from aiogram import Router
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import Command

from app.api.client import get_lots
from app.services.lot_filter import filter_lots
from app.services.sent_lots import load_sent_lots, save_sent_lots
from app.services.chats import load_chats, save_chats

router = Router()


# ───────────────────────── START ─────────────────────────

@router.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Показать лоты", callback_data="show_lots")],
            [InlineKeyboardButton(text="🔔 Включить авто-поиск", callback_data="subscribe")],
        ]
    )

    await message.answer(
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

    await message.answer("🔔 Авто-поиск включён для этого чата")


@router.callback_query(lambda c: c.data == "subscribe")
async def subscribe_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    chats = load_chats()
    chats.add(chat_id)
    save_chats(chats)

    await callback.message.answer("🔔 Авто-поиск включён для этого чата")
    await callback.answer()


# ───────────────────────── LOTS ─────────────────────────

@router.message(Command("lots"))
async def lots_handler(message: Message):
    await send_lots(message)


@router.callback_query(lambda c: c.data == "show_lots")
async def show_lots_callback(callback: CallbackQuery):
    await callback.answer("🔎 Ищу лоты...")
    await send_lots(callback.message)


# ───────────────────────── CORE LOGIC ─────────────────────────

async def send_lots(message: Message):
    lots = await get_lots()

    # ❗ НЕ ПИШЕМ ОШИБКУ ПОЛЬЗОВАТЕЛЮ
    if not lots:
        return

    filtered = filter_lots(lots)

    sent_ids = load_sent_lots()
    new_sent_ids = set(sent_ids)

    # 🔑 используем URL как уникальный ключ
    filtered = [
        lot for lot in filtered
        if lot.get("url") and lot["url"] not in sent_ids
    ]

    if not filtered:
        await message.answer("❌ Новых подходящих лотов нет.")
        return

    await message.answer(f"🔎 Найдено новых лотов: {len(filtered)}")

    for lot in filtered:
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

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

        new_sent_ids.add(lot_url)

    save_sent_lots(new_sent_ids)
