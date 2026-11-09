import asyncio
import logging
from contextlib import suppress

from aiohttp import ClientError, web
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from psycopg import Error as DatabaseError

from handlers import router, check_expiration_subscribe_premium, check_prices_and_notify, throttling
from config import BOT, WEB_SERVER_HOST, WEB_SERVER_PORT, WEBHOOK_PATH, WEBHOOK_SECRET, BASE_WEBHOOK_URL


async def check():
    while True:
        try:
            await check_expiration_subscribe_premium()
            await check_prices_and_notify()
        except (ClientError, TimeoutError, DatabaseError, TelegramAPIError) as error:
            logging.error("Периодическая проверка не выполнена: %s", type(error).__name__)
        await asyncio.sleep(60)


async def periodic_checks(app):
    task = asyncio.create_task(check())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await throttling.storage.close()


async def on_startup(bot: Bot):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)


def main():
    dp = Dispatcher()
    dp.include_router(router)
    dp.startup.register(on_startup)
    app = web.Application()
    app.cleanup_ctx.append(periodic_checks)
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp, bot=BOT, secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=BOT)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
