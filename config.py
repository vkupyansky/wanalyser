import os
import re
from urllib.parse import urlsplit

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


def required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise ValueError(f"Не задан обязательный параметр {name}")
    return value


BOT_TOKEN = required("BOT_TOKEN")
BOT_NAME = required("BOT_NAME")
if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", BOT_NAME):
    raise ValueError("BOT_NAME должен содержать имя бота без @")

PG_DSN = required("PG_DSN")
REDIS_URL = required("REDIS_URL")
WEBHOOK_SECRET = required("WEBHOOK_SECRET")
if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", WEBHOOK_SECRET):
    raise ValueError("WEBHOOK_SECRET должен содержать 32-256 символов A-Z, a-z, 0-9, _ или -")

BASE_WEBHOOK_URL = required("BASE_WEBHOOK_URL")
origin = urlsplit(BASE_WEBHOOK_URL)
if (
    origin.scheme != "https"
    or not origin.hostname
    or origin.username
    or origin.password
    or origin.path
    or origin.query
    or origin.fragment
):
    raise ValueError("BASE_WEBHOOK_URL должен быть HTTPS origin без завершающего /")

WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 8080
WEBHOOK_PATH = "/webhook"
BOT = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
