import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config import settings
from app.database import init_db
from app.handlers.admin import router as admin_router
from app.handlers.common import router as common_router
from app.handlers.modes import router as modes_router

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(common_router)
    dp.include_router(modes_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
