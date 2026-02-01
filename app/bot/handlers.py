from aiogram import Router
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import Command
import asyncio

from aiogram.exceptions import TelegramRetryAfter, TelegramNetworkError

from app.api.client import get_lots
from app.services.lot_filter import filter_lots
from app.services.sent_lots import (
    load_user_seen,
    save_user_seen,
)
from app.services.chats import load_chats, save_chats

router = Router()

PAGE_SIZE = 10
SEND_DELAY = 1.2  # защита от Flood


# ───────────────────────── SAFE SEND ─────────────────────────

async def safe_send(message: Message, text: str, reply_markup=None):
    bot = message.bot
    chat_id = message.chat.id

    while True:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
            await asyncio.sleep(SEND_DELAY)
            return

        except TelegramRetryAfter as e:
            wait_s = int(getattr(e, "retry_after", 5))
            await asyncio.sleep(wait_s + 1)

        except TelegramNetworkError:
            await asyncio.sleep(3)


# ───────────────────────── START ─────────────────────────

@router.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Показать лоты", callback_data="show_lots:0")],
            [InlineKeyboardButton(text="🔔 Включить авто-поиск", callback_data="subscribe")],
        ]
    )

    await safe_send(
        message,
        "👋 Привет!\n\n"
        "Я тендер-бот 🤖\n"
        "Показываю подходящие и актуальные лоты.",
        reply_markup=keyboard,
    )


# ───────────────────────── SUBSCRIBE ─────────────────────────

@router.callback_query(lambda c: c.data == "subscribe")
async def subscribe_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    chats = load_chats()
    chats.add(chat_id)
    save_chats(chats)

    await callback.answer()
    await safe_send(callback.message, "🔔 Авто-поиск включён для этого чата")


# ───────────────────────── LOTS ─────────────────────────

@router.callback_query(lambda c: c.data.startswith("show_lots"))
async def show_lots_callback(callback: CallbackQuery):
    _, offset = callback.data.split(":")
    await callback.answer()
    await send_lots(callback.message, int(offset))


# ───────────────────────── CORE LOGIC ─────────────────────────

async def send_lots(message: Message, offset: int):
    chat_id = str(message.chat.id)

    lots = await get_lots()
    if not lots:
        await safe_send(message, "❌ Лоты не найдены.")
        return

    filtered = filter_lots(lots)

    user_seen = load_user_seen()
    seen = user_seen.get(chat_id, set())

    available = [
        lot for lot in filtered
        if lot.get("url") and lot["url"] not in seen
    ]

    if not available:
        await safe_send(message, "❌ Новых подходящих лотов нет.")
        return

    page = available[offset: offset + PAGE_SIZE]

    for lot in page:
        url = lot["url"]
        text = (
            f"📦 <b>{lot.get('lot_number', '—')}</b>\n"
            f"<b>{lot.get('name_ru', 'Без названия')}</b>\n\n"
            f"💰 <b>{lot.get('amount', '—')}</b>\n"
            f"📌 Статус: <b>{lot.get('status_ru', '—')}</b>"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="🔗 Открыть лот на портале",
                url=url
            )]]
        )

        await safe_send(message, text, reply_markup=keyboard)
        seen.add(url)

    user_seen[chat_id] = seen
    save_user_seen(user_seen)

    if offset + PAGE_SIZE < len(available):
        more_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="➡️ Показать ещё",
                callback_data=f"show_lots:{offset + PAGE_SIZE}"
            )]]
        )
        await safe_send(message, "Показать ещё лоты?", reply_markup=more_keyboard)
