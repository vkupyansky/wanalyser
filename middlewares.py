from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.storage.redis import RedisStorage
from database import *
from config import BOT, REDIS_URL

class Manage(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if event.chat.type != 'private':
            return
        start = event.text

        referrer_id = str(start[7:]) if start is not None and start.startswith('/start ') else None

        if referrer_id is not None and (not referrer_id.isdigit() or int(referrer_id) <= 0):
            referrer_id = None

        if referrer_id == str(event.from_user.id):
            return await event.answer("<b>Нельзя зарегистрироваться по собственной реферальной ссылке</b>")

        is_user_exists = await add_or_update_user(event.from_user.id, event.from_user.username, event.from_user.first_name, event.from_user.last_name, referrer_id)

        if not is_user_exists and referrer_id:
            await increment_balance(referrer_id, 5)
            try:
                await BOT.send_message(referrer_id, "<b>По твоей реферальной ссылке зарегистрировался новый пользователь, получено вознаграждение в размере 5 💎</b>")
            except:
                pass

        is_blocked = await is_user_blocked(event.from_user.id)
        if is_blocked:
            return await event.answer("<b>Профиль заблокирован в боте</b>")


        return await handler(event, data)

class Throttling(BaseMiddleware):
    def __init__(self):
        self.storage = RedisStorage.from_url(REDIS_URL)

    async def __call__(self, handler, event: Message, data: dict):
        long_user_key = f"long_user_{event.from_user.id}"

        current_count_long = await self.storage.redis.incr(long_user_key)
        if current_count_long == 1:
            await self.storage.redis.expire(long_user_key, 5)

        if current_count_long > 10:
            await block_user(event.from_user.id, 'СПАМ. Количество запросов более 10 в 5 секунд.')
            return await event.answer(f"<b>Ты заблокирован за чрезмерное количество запросов</b>")

        if current_count_long > 3:
            return await event.answer(f"<b>Слишком много запросов. Попробуй позже</b>")

        return await handler(event, data)
