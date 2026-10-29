import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from utils.storage import SQLiteStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_IDS, PHOTO_RETENTION_DAYS
from utils.export import cleanup_old_photos
from database import init_db
from handlers import start, application, admin
from handlers.application import verify_and_settle
from database import get_payment_by_provider_id, mark_payment_cancelled_if_pending
from utils import hamyon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def handle_ping(request):
    return web.Response(text="Green Card Telegram Bot is running on Render 24/7! 🇺🇸")

async def hamyon_prepare(request):
    return web.json_response({"status": "ok"})


async def hamyon_complete(request):
    """hamyon-api.uz 'paid' / 'cancel' callbacki. Ishonch uchun holat API orqali qayta tekshiriladi."""
    try:
        try:
            body = await request.json()
        except Exception:
            body = dict(await request.post()) or dict(request.query)
        pid = hamyon.find(body, ("payment_id", "id"))
        if pid is None:
            return web.json_response({"status": "ignored"})

        sign = hamyon.find(body, ("sign", "signature", "hash"))
        if sign:
            shop_id = str(hamyon.find(body, ("shop_id",)) or "")
            amount = str(hamyon.find(body, ("amount",)) or "")
            if not hamyon.verify_sign(shop_id, str(pid), amount, sign):
                logger.warning("Hamyon callback imzosi mos kelmadi (payment %s)", pid)
                return web.json_response({"status": "bad sign"}, status=403)

        payment = await get_payment_by_provider_id(str(pid))
        if payment and payment["status"] == "pending":
            await verify_and_settle(request.app["bot"], request.app["storage"], payment)
    except Exception as e:
        logger.exception("Hamyon callback xatosi: %s", e)
    return web.json_response({"status": "ok"})


async def start_web_server(bot=None, storage=None):
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app["bot"] = bot
    app["storage"] = storage
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_post("/hamyon/prepare", hamyon_prepare)
    app.router.add_post("/hamyon/complete", hamyon_complete)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check web server muvaffaqiyatli ishga tushdi (port: {port})")

async def photo_cleanup_loop():
    """Har 24 soatda eski rasmlarni o'chiradi."""
    while True:
        try:
            n = await asyncio.to_thread(cleanup_old_photos, PHOTO_RETENTION_DAYS)
            if n:
                logger.info("%s kundan eski %s ta rasm o'chirildi", PHOTO_RETENTION_DAYS, n)
        except Exception as e:
            logger.exception("Rasm tozalashda xato: %s", e)
        await asyncio.sleep(24 * 3600)


async def main():
    if not BOT_TOKEN:
        logger.error("DIQQAT: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, .env faylga bot tokenini kiriting.")
        return

    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=SQLiteStorage())

    # Render uchun web server (health check + to'lov callbacklari)
    await start_web_server(bot, dp.storage)

    # Routers ro'yxatdan o'tkaziladi
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(application.router)

    cleanup_task = asyncio.create_task(photo_cleanup_loop())
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
