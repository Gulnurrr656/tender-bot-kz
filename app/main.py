import asyncio

from aiogram import Bot, Dispatcher
from app.config.settings import TG_TOKEN
from app.bot import router
from app.services.auto_checker import auto_check_lots


async def main():
    bot = Bot(token=TG_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    # 🔔 ЗАПУСК АВТОПРОВЕРКИ
    asyncio.create_task(auto_check_lots(bot))

    print("🤖 Бот запущен и авто-поиск работает")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
