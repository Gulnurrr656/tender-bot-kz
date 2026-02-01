import asyncio

from aiogram.exceptions import TelegramRetryAfter, TelegramNetworkError

from app.api.client import get_lots
from app.services.lot_filter import filter_lots
from app.services.sent_lots import load_sent_lots, save_sent_lots
from app.services.chats import load_chats

CHECK_INTERVAL = 300   # 5 минут
SEND_DELAY = 1.2       # пауза между сообщениями
MAX_PER_RUN = 10       # максимум лотов за один цикл (безопасно)


async def safe_send(bot, chat_id: int, text: str):
    """
    Безопасная отправка сообщения с учётом Flood control.
    """
    while True:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            await asyncio.sleep(SEND_DELAY)
            return

        except TelegramRetryAfter as e:
            wait_s = int(getattr(e, "retry_after", 5))
            print(f"⚠️ Flood control: жду {wait_s} сек")
            await asyncio.sleep(wait_s + 1)

        except TelegramNetworkError as e:
            print("⚠️ TelegramNetworkError:", e)
            await asyncio.sleep(3)


async def auto_check_lots(bot):
    """
    Фоновый авто-поиск новых лотов.
    Работает тихо и безопасно.
    """
    while True:
        try:
            chats = load_chats()
            if not chats:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            lots = await get_lots()
            if not lots:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            filtered = filter_lots(lots)

            sent_ids = load_sent_lots()
            new_sent_ids = set(sent_ids)

            new_lots = []
            for lot in filtered:
                lot_key = lot.get("url") or lot.get("lot_number")
                if not lot_key:
                    continue
                if lot_key not in sent_ids:
                    new_lots.append(lot)

            # ограничиваем объём
            new_lots = new_lots[:MAX_PER_RUN]

            for lot in new_lots:
                lot_key = lot.get("url") or lot.get("lot_number")

                text = (
                    f"🆕 <b>Новый лот</b>\n\n"
                    f"<b>{lot.get('name_ru', 'Без названия')}</b>\n"
                    f"💰 <b>{lot.get('amount', '—')}</b>\n"
                    f"📌 Статус: <b>{lot.get('status_ru', '—')}</b>\n\n"
                    f"🔗 {lot.get('url', '')}"
                )

                for chat_id in chats:
                    await safe_send(bot, chat_id, text)

                new_sent_ids.add(lot_key)

            if new_lots:
                save_sent_lots(new_sent_ids)

        except Exception as e:
            print("❌ Ошибка авто-поиска:", e)

        await asyncio.sleep(CHECK_INTERVAL)
