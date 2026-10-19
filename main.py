import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db
from handlers import start, application, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.error("DIQQAT: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, .env faylga bot tokenini kiriting.")
        print("\n" + "="*60)
        print("XATOLIK: BOT_TOKEN topilmadi!")
        print("Iltimos, .env faylini oching va Telegram @BotFather dan olgan")
        print("Bot Tokeningizni quyidagicha kiriting:")
        print("BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz")
        print("="*60 + "\n")
        return

    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routers ro'yxatdan o'tkaziladi
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(application.router)

    logger.info("Bot muvaffaqiyatli ishga tushdi!")
    if ADMIN_IDS:
        logger.info(f"Adminlar ID lari: {ADMIN_IDS}")
    else:
        logger.warning(".env da ADMIN_IDS kiritilmagan! Admin paneldan foydalanish uchun o'z Telegram ID ingizni yozing.")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
