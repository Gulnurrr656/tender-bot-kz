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


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Показать лоты", callback_data="show_lots")],
            [InlineKeyboardButton(text="🔔 Включить авто-поиск", callback_data="subscribe")],
            [InlineKeyboardButton(text="♻️ Сбросить просмотр", callback_data="reset_seen")],
        ]
    )


# ───────────────────────── START ─────────────────────────

@router.message(Command("start"))
async def start_handler(message: Message):
    await safe_send(
        message,
        "👋 Привет!\n\n"
        "Я тендер-бот 🤖\n"
        "Показываю подходящие и актуальные лоты.\n\n"
        "Нажми «📦 Показать лоты» — пришлю по 10 штук, без повторов.",
        reply_markup=main_keyboard(),
    )


# ───────────────────────── SUBSCRIBE ─────────────────────────

@router.callback_query(lambda c: c.data == "subscribe")
async def subscribe_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    chats = load_chats()
    chats.add(chat_id)
    save_chats(chats)

    await callback.answer("✅ Включено")
    await safe_send(callback.message, "🔔 Авто-поиск включён для этого чата", reply_markup=main_keyboard())


# ───────────────────────── RESET SEEN ─────────────────────────

@router.callback_query(lambda c: c.data == "reset_seen")
async def reset_seen_callback(callback: CallbackQuery):
    chat_id = str(callback.message.chat.id)

    user_seen = load_user_seen()
    user_seen[chat_id] = set()
    save_user_seen(user_seen)

    await callback.answer("Сброшено")
    await safe_send(callback.message, "♻️ История просмотренных лотов сброшена. Теперь снова покажу лоты.", reply_markup=main_keyboard())


# ───────────────────────── LOTS ─────────────────────────

@router.callback_query(lambda c: c.data == "show_lots")
async def show_lots_callback(callback: CallbackQuery):
    # чтобы было видно что бот “думает”
    await callback.answer("🔎 Ищу лоты...")
    await send_lots(callback.message)


# ───────────────────────── CORE LOGIC ─────────────────────────

async def send_lots(message: Message):
    chat_id = str(message.chat.id)

    # 1) Забираем лоты (и показываем реальную ошибку, если Playwright упал)
    try:
        lots = await get_lots()
    except Exception as e:
        await safe_send(
            message,
            "❌ Ошибка при получении лотов.\n\n"
            f"<b>Причина:</b> {type(e).__name__}: {e}",
            reply_markup=main_keyboard(),
        )
        return

    if not lots:
        await safe_send(
            message,
            "❌ Лоты не найдены (get_lots вернул пусто).",
            reply_markup=main_keyboard(),
        )
        return

    # 2) Фильтруем
    filtered = filter_lots(lots)

    # 3) Не повторяем для конкретного пользователя
    user_seen = load_user_seen()
    seen = user_seen.get(chat_id, set())

    available = [
        lot for lot in filtered
        if lot.get("url") and lot["url"] not in seen
    ]

    if not available:
        await safe_send(
            message,
            "❌ Новых подходящих лотов нет.",
            reply_markup=main_keyboard(),
        )
        return

    # ✅ ВАЖНО: pagination без offset.
    # Каждый раз выдаём следующие 10 НЕВИДЕННЫХ, потом помечаем их seen.
    page = available[:PAGE_SIZE]

    # можно показать сколько осталось
    await safe_send(
        message,
        f"🔎 Найдено новых лотов: <b>{len(available)}</b>\n"
        f"Показываю <b>{len(page)}</b> шт.",
        reply_markup=None,
    )

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

    # 4) Кнопка “Показать ещё” — опять show_lots (без offset), чтобы НЕ ПУТАЛОСЬ
    if len(available) > PAGE_SIZE:
        more_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➡️ Показать ещё 10", callback_data="show_lots")],
                [InlineKeyboardButton(text="♻️ Сбросить просмотр", callback_data="reset_seen")],
            ]
        )
        await safe_send(message, "Продолжить?", reply_markup=more_keyboard)
    else:
        await safe_send(message, "✅ Это все новые лоты на сейчас.", reply_markup=main_keyboard())