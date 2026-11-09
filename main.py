import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import start_router, media_router, video_router, youtube_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def start_web_server():
    """Starts a lightweight web server for cloud platforms (Render, Railway, etc.)"""
    port_str = os.getenv("PORT")
    if not port_str:
        return None
    port = int(port_str)
    app = web.Application()

    async def handle_ping(request):
        return web.Response(text="Bot is running! 🚀")

    app.router.add_get("/", handle_ping)
    app.router.add_get("/healthz", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Cloud platforma uchun web-server {port}-portda ishga tushirildi.")
    return runner


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error(
            "\n" + "=" * 60 + "\n"
            "❌ XATOLIK: BOT_TOKEN ko'rsatilmagan!\n"
            "Iltimos, .env faylini oching va BOT_TOKEN o'rniga @BotFather dan olingan tokenni yozing.\n"
            "Misol: BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ\n"
            + "=" * 60
        )
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_router)
    dp.include_router(youtube_router)
    dp.include_router(video_router)
    dp.include_router(media_router)

    logger.info("🤖 Bot muvaffaqiyatli ishga tushirildi! Rasmlardan video yaratishga tayyor...")

    web_runner = await start_web_server()

    try:
        # Delete pending updates to start fresh
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")

