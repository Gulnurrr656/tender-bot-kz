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
from app.services.sent_lots import load_sent_lots, save_sent_lots
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
            print(f"⚠️ Flood control: жду {wait_s} сек...")
            await asyncio.sleep(wait_s + 1)

        except TelegramNetworkError as e:
            print("⚠️ TelegramNetworkError:", e)
            await asyncio.sleep(3)


# ───────────────────────── START ─────────────────────────

@router.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Показать лоты", callback_data="show_lots")],
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

@router.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    chat_id = message.chat.id
    chats = load_chats()
    chats.add(chat_id)
    save_chats(chats)

    await safe_send(message, "🔔 Авто-поиск включён для этого чата")


@router.callback_query(lambda c: c.data == "subscribe")
async def subscribe_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    chats = load_chats()
    chats.add(chat_id)
    save_chats(chats)

    await callback.answer()
    await safe_send(callback.message, "🔔 Авто-поиск включён для этого чата")


# ───────────────────────── LOTS ─────────────────────────

@router.message(Command("lots"))
async def lots_handler(message: Message):
    await send_lots(message, offset=0)


@router.callback_query(lambda c: c.data == "show_lots")
async def show_lots_callback(callback: CallbackQuery):
    await callback.answer("🔎 Ищу лоты...")
    await send_lots(callback.message, offset=0)


@router.callback_query(lambda c: c.data.startswith("more:"))
async def more_lots_callback(callback: CallbackQuery):
    offset = int(callback.data.split(":")[1])
    await callback.answer()
    await send_lots(callback.message, offset=offset)


# ───────────────────────── CORE LOGIC ─────────────────────────

async def send_lots(message: Message, offset: int = 0):
    lots = await get_lots()
    if not lots:
        return

    filtered = filter_lots(lots)

    sent_ids = load_sent_lots()
    new_sent_ids = set(sent_ids)

    filtered = [
        lot for lot in filtered
        if lot.get("url") and lot["url"] not in sent_ids
    ]

    if not filtered:
        await safe_send(message, "❌ Новых подходящих лотов нет.")
        return

    page = filtered[offset: offset + PAGE_SIZE]

    for lot in page:
        lot_url = lot.get("url")
        if not lot_url:
            continue

        text = (
            f"📦 <b>{lot.get('lot_number', '—')}</b>\n"
            f"<b>{lot.get('name_ru', 'Без названия')}</b>\n\n"
            f"💰 <b>{lot.get('amount', '—')}</b>\n"
            f"📌 Статус: <b>{lot.get('status_ru', '—')}</b>"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="🔗 Открыть лот на портале",
                url=lot_url
            )]]
        )

        await safe_send(message, text, reply_markup=keyboard)
        new_sent_ids.add(lot_url)

    save_sent_lots(new_sent_ids)

    if offset + PAGE_SIZE < len(filtered):
        more_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="➡️ Показать ещё",
                callback_data=f"more:{offset + PAGE_SIZE}"
            )]]
        )
        await safe_send(message, "Показать ещё лоты?", reply_markup=more_keyboard)
