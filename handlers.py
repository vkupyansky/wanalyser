import json
from datetime import datetime, timedelta
from aiogram import types, F, Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from utils import *
from database import *
from keyboards import *
from middlewares import *
from config import BOT_NAME, BOT
from html import escape

router = Router()

router.message.middleware(Manage())
throttling = Throttling()
router.message.middleware(throttling)

def load_dictionary():
    with open('dictionary.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def get_item_key(ru):
    dictionary = load_dictionary()
    ru_lower = ru.lower()
    for key, value in dictionary["DICTIONARY"].items():
        if isinstance(value.get("ru"), str) and value["ru"].lower() == ru_lower:
            return key
    return None

def find_english_name(item_name):
    dictionary = load_dictionary()
    return dictionary["DICTIONARY"].get(item_name, {}).get("en", None)

class States(StatesGroup):
    waiting_for_global_message = State()
    waiting_for_block = State()
    waiting_for_price = State()
    waiting_for_rank = State()
    waiting_for_count = State()

@router.message(Command("start"))
async def start_handler(msg: Message):
    is_admin = await is_user_admin(msg.from_user.id)
    if is_admin:
        kb = [
            [
                KeyboardButton(text="🔎 Живой поиск"),
                KeyboardButton(text="🏆 Топы")
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="💬 Помощь")
            ],
            [KeyboardButton(text="💳 Поддержать проект")],
            [KeyboardButton(text="⚙️ Администрирование")]
        ]
    else:
        kb = [
            [
                KeyboardButton(text="🔎 Живой поиск"),
                KeyboardButton(text="🏆 Топы")
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="💬 Помощь")
            ],
            [KeyboardButton(text="💳 Поддержать проект")]
        ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Введи название предмета"
    )
    await msg.answer(
        f"Привет, {escape(msg.from_user.first_name)}",
        reply_markup=keyboard
    )

@router.message(Command("search"))
@router.message(F.text.lower() == "🔎 живой поиск")
async def live_search_handler(msg: Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔎 Начать поиск",
        switch_inline_query_current_chat="")
    )
    await msg.answer(
        "<b>Живой поиск предметов</b>\n\n"
        "<b>1.</b> Начни печатать название предмета (не менее 3-х символов).\n"
        "<b>2.</b> Выбери нужный предмет из списка.\n\n"
        "<b>Пример:</b> <code>@warframe_marketbot защита</code>",
        reply_markup=builder.as_markup()
    )


@router.message(Command("top"))
@router.message(F.text.lower() == "🏆 топы")
async def top_items(msg: Message):
    await msg.answer(
        "<b>Топы временно не работают из-за неполадок на стороне API провайдера</b>"
    )

@router.message(Command("profile"))
@router.message(F.text.lower() == "👤 профиль")
async def profile_handler(msg: Message):
    registration_date = await get_registration_date(msg.from_user.id)
    balance = await get_user_balance(msg.from_user.id)
    premium = await is_user_premium(msg.from_user.id)
    premium_text = 'активен' if premium else 'отсутствует'
    premium_days_left = await expiration_date(msg.from_user.id)
    if premium_days_left is None:
        premium_days_left_text = "вечный"
    else:
        premium_days_left_text = premium_days_left
    if premium:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="📦 Подписки на предметы",
            callback_data="show_subscriptions")
        )
        builder.row(InlineKeyboardButton(
            text="🤝 Пригласить друзей",
            callback_data="invite_friends")
        )
        await msg.answer(
            "👤 <b>Профиль</b>\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
            f"ID: <code>{msg.from_user.id}</code>\n"
            f"Никнейм: @{msg.from_user.username}\n"
            f"Баланс: {balance} 💎\n"
            f"Премиум: {premium_text}\n"
            f"Дата окончания: {premium_days_left_text}\n"
            f"Дата регистрации: {registration_date}\n"
            "➖➖➖➖➖➖➖➖➖➖",
            reply_markup=builder.as_markup()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⭐️ Оформить Премиум",
            callback_data="make_subscription")
        )
        builder.row(InlineKeyboardButton(
            text="📦 Подписки на предметы",
            callback_data="show_subscriptions")
        )
        builder.row(InlineKeyboardButton(
            text="🤝 Пригласить друзей",
            callback_data="invite_friends")
        )
        await msg.answer(
            "👤 <b>Профиль</b>\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
            f"ID: <code>{msg.from_user.id}</code>\n"
            f"Никнейм: @{msg.from_user.username}\n"
            f"Баланс: {balance} 💎\n"
            f"Премиум: {premium_text}\n"
            f"Дата регистрации: {registration_date}\n"
            "➖➖➖➖➖➖➖➖➖➖",
            reply_markup=builder.as_markup()
        )

@router.message(Command("help"))
@router.message(F.text.lower() == "💬 помощь")
async def help_handler(msg: Message):
    await msg.answer(
        "<b>В боте представлен следующий основной функционал:</b>\n\n"
        "<b>1. Поиск предметов</b>\n"
        "Поиск осуществляется путём ввода и отправки полного названия предмета на русском языке или с помощью живого поиска (команда <code>/search</code>, Кнопка - <b>🔎 Живой поиск</b>). Также можно скопировать выделенный текст <code>@warframe_marketbot</code>, начать печатать название предмета на русском языке и выбрать его из предложенного списка. Например, <code>@warframe_marketbot Поток прайм</code>. В ответ бот отправляет информацию о минимальной стоимости предмета за минимальный и максимальный ранг.\n"
        "Если у предмета отсутствует ранг, бот сообщает минимальную цену без ранга, а также указывает тип предмета, продавца, стоимость в дукатах и количество продаваемых предметов у одного пользователя, если это предусмотрено. Поиск предназначен для быстрого просмотра цены на предмет при торговле через игровой чат <b>Торговля</b>, без необходимости заходить на Варфрейм Маркет.\n\n"
        "<b>2. Топы</b>\n"
        "Кнопка позволяет узнать топ дорогих предметов из определённых категорий за последние 3-4 дня. Топы предназначены для быстрого ориентира о том, что лучше фармить для продажи на данный момент или что можно продать дороже.\n"
        "Важно: топы обновляются каждую среду и воскресенье в 20:00 (мск).\n\n"
        "<b>3. Подписка на предмет (Премиум)</b>\n"
        "Можно отслеживать цену интересующего предмета. Для этого введи полное название предмета или воспользуйся командой <code>/search</code>, Кнопка - <b>🔎 Живой поиск</b>, после чего нажми на кнопку <b>👁‍🗨 Подписаться на предмет</b>, введи ранг, стоимость и количество предметов. После этого начнут приходить уведомления, если на маркете появится предмет по указанным параметрам.\n"
        "Важно: по истечении Премиум, все подписки на предметы автоматически удалятся. На данный момент можно подписаться максимум на 4 предмета, в будущем возможно расширение лимита.\n\n"
        "<b>4. Оплата Премиума</b>\n"
        "Оплата осуществляется через сервис <a href='https://boosty.to/creatonwf'><b>Boosty</b></a>, <b>Уровень БОТ ТГ</b>. При оплате в чате нужно указать свой ID или никнейм с профиля в боте, и в течение суток будет выдана подписка. В будущем планируется подключение платёжной системы для быстрого и комфортного оформления Премиум.\n"
        "Важно: оплата должна производиться строго через <b>Уровень БОТ ТГ</b>. Оплату нельзя разбить на части или добавить обычные донаты к стоимости подписки. Если ты оплатил не тот уровень на Boosty, возврат средств не предусмотрен, будь внимательнее.\n\n"
        "<b>5. Профиль</b>\n"
        "В профиле можно увидеть основную информацию: ID, никнейм, баланс, статус Премиум подписки и дату регистрации, а также управление подписками на предметы.\n\n"
        "<b>6. Управление подписками на предметы</b>\n"
        "Нажав кнопку <b>📦 Подписки на предметы</b>, можно просмотреть активные подписки, а также удалить подписку на любой предмет из списка, просто нажав на кнопку с его названием.\n\n"
        "<b>7. Реферальная программа</b>\n"
        "Реферальная программа предусмотрена в кнопке <b>🤝 Пригласить друзей</b> в профиле. По нажатию на эту кнопку будет показана индивидуальная ссылка для приглашения друга. За каждого активного друга ты получишь 5 💎, которые можно использовать для оформления Премиума на 30 дней (149 💎 = Премиум, стоимость 1 к 1).\n\n"
        "<b>8. Поддержка проекта</b>\n"
        "Кнопка <b>💳 Поддержать проект</b> позволяет пожертвовать любую сумму через сервис <a href='https://boosty.to/creatonwf'><b>Boosty</b></a>. Это не относится к оформлению Премиум подписки, но является мотивацией для дальнейшего развития проекта."
    )

@router.message(Command("pay"))
@router.message(F.text.lower() == "💳 поддержать проект")
async def pay_handler(msg: Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="💰 Boosty",
        url="https://boosty.to/creatonwf")
    )
    await msg.answer(
        "<b>Доступные методы пожертвования:</b>",
        reply_markup=builder.as_markup()
    )

@router.message(Command("admin"))
@router.message(F.text.lower() == "⚙️ администрирование")
async def admin_handler(msg: Message):
    is_admin = await is_user_admin(msg.from_user.id)
    if is_admin:
        await msg.answer(
            "<b>Выбери нужное действие:</b>",
            reply_markup=keyboard_admin()
        )

async def safe_edit_text(callback_message, text, reply_markup=None):
    try:
        return await callback_message.edit_text(text, reply_markup=reply_markup)
    except:
        pass

async def safe_delete_message(bot, chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

@router.callback_query()
async def callbacks(callback: CallbackQuery, state: FSMContext):
    if (
        callback.message is None
        or callback.message.chat.type != "private"
        or callback.message.chat.id != callback.from_user.id
    ):
        await callback.answer("Откройте личный чат с ботом.", show_alert=True)
        return
    if await is_user_blocked(callback.from_user.id):
        await callback.answer("Профиль заблокирован.", show_alert=True)
        return
    action = (callback.data or "").split(":", 1)[0]
    admin_actions = {
        "admin_statistic", "global_message", "create_db_archive", "collate",
        "make_dict", "back_to_admin", "block_user", "unblock_user", "add_admin",
        "remove_admin", "delete_from_database_user", "add_access", "remove_access",
        "give_premium",
    }
    if action in admin_actions and not await is_user_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    if callback.data is None:
        await callback.answer()
        return
    if callback.data == "top_all":
        top_all = await get_top_all()
        message_text = ""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tops")
        )
        for result in top_all:
            ru_name, min_rank, platinum_min_rank, max_rank, platinum_max_rank, not_rank = result
            ranks_info = ""
            if min_rank is not None and platinum_min_rank is not None:
                ranks_info += f"{min_rank} ранг - {platinum_min_rank} 💎"
            if max_rank is not None and platinum_max_rank is not None:
                if max_rank == min_rank and platinum_max_rank == platinum_min_rank:
                    ranks_info = f"{min_rank} ранг - {platinum_min_rank} 💎"
                else:
                    ranks_info += f" | {max_rank} ранг - {platinum_max_rank} 💎" if ranks_info else f"{max_rank} ранг - {platinum_max_rank} 💎"
            if not_rank is not None and not ranks_info:
                ranks_info = f"Без ранга - {not_rank} 💎"
            message_text += f"{ru_name}\n{ranks_info}\n\n"
        await safe_edit_text(callback.message, f"<b>Общий топ:</b>\n\n{message_text.strip()}", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "top_mods":
        top_mods = await get_top_mod()
        message_text = ""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tops")
        )
        for result in top_mods:
            ru_name, min_rank, platinum_min_rank, max_rank, platinum_max_rank, not_rank = result
            ranks_info = ""
            if min_rank is not None and platinum_min_rank is not None:
                ranks_info += f"{min_rank} ранг - {platinum_min_rank} 💎"
            if max_rank is not None and platinum_max_rank is not None:
                if max_rank == min_rank and platinum_max_rank == platinum_min_rank:
                    ranks_info = f"{min_rank} ранг - {platinum_min_rank} 💎"
                else:
                    ranks_info += f" | {max_rank} ранг - {platinum_max_rank} 💎" if ranks_info else f"{max_rank} ранг - {platinum_max_rank} 💎"
            if not_rank is not None and not ranks_info:
                ranks_info = f"Без ранга - {not_rank} 💎"
            message_text += f"{ru_name}\n{ranks_info}\n\n"
        await safe_edit_text(callback.message, f"<b>Топ моды</b>:\n\n{message_text.strip()}", reply_markup=builder.as_markup())
    if callback.data == "back_to_tops":
        new_text = "<b>Топы обновляются каждую среду и воскресенье в 20:00 (мск)</b>\n\n<b>Выбери нужный топ:</b>"
        await safe_edit_text(callback.message, new_text, reply_markup=keyboard_top())
        await callback.answer()
    if callback.data == "top_primes":
        top_primes = await get_top_prime()
        message_text = ""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tops")
        )
        for result in top_primes:
            ru_name, not_rank = result
            message_text += f"{ru_name}\n{not_rank} 💎\n\n"

        new_text = f"<b>Топ праймы:</b>\n\n{message_text.strip()}"
        new_markup = builder.as_markup()
        await safe_edit_text(callback.message, new_text, reply_markup=new_markup)

        await callback.answer()
    if callback.data == "top_mist":
        top_mist = await get_top_mist()
        message_text = ""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tops")
        )
        for result in top_mist:
            ru_name, min_rank, platinum_min_rank, max_rank, platinum_max_rank = result
            message_text += f"{ru_name}\n{min_rank} ранг - {platinum_min_rank} 💎 | {max_rank} ранг - {platinum_max_rank} 💎\n\n"
        await safe_edit_text(callback.message, f"<b>Топ мистификаторы:</b>\n\n{message_text.strip()}", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "top_collections":
        top_collect = await get_top_collection()
        message_text = ""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tops")
        )
        for result in top_collect:
            ru_name, min_rank, platinum_min_rank, max_rank, platinum_max_rank, not_rank = result
            ranks_info = ""
            if min_rank is not None and platinum_min_rank is not None:
                ranks_info += f"{min_rank} ранг - {platinum_min_rank} 💎"
            if max_rank is not None and platinum_max_rank is not None:
                if max_rank == min_rank and platinum_max_rank == platinum_min_rank:
                    ranks_info = f"{min_rank} ранг - {platinum_min_rank} 💎"
                else:
                    ranks_info += f" | {max_rank} ранг - {platinum_max_rank} 💎" if ranks_info else f"{max_rank} ранг - {platinum_max_rank} 💎"
            if not_rank is not None and not ranks_info:
                ranks_info = f"Без ранга - {not_rank} 💎"
            message_text += f"{ru_name}\n{ranks_info}\n\n"
        await safe_edit_text(callback.message, f"<b>Топ коллекционные:</b>\n\n{message_text.strip()}", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "admin_statistic":
        total_users, total_premium_users, total_blocked_users, active_24h, active_7d, active_30d = await get_stats()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_admin")
        )
        await safe_edit_text(callback.message,
            f"<b>Всего пользователей: {total_users}</b>\n\n"
            f"<b>Всего Премиум пользователей: {total_premium_users}</b>\n\n"
            f"<b>Всего заблокированных пользователей: {total_blocked_users}</b>\n\n"
            "<b>Активных пользователей:</b>\n"
            f"<b>За 24 часа: {active_24h}</b>\n"
            f"<b>За 7 дней: {active_7d}</b>\n"
            f"<b>За 30 дней: {active_30d}</b>", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "global_message":
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_admin")
        )
        response_message = await safe_edit_text(callback.message,
            "<b>Введи сообщение для всех пользователей</b>\n\n"
            "Поддерживается HTML форматирование:\n"
            "<b>жирный</b>\n"
            "<i>курсив</i>\n"
            "<code>код</code>\n"
            "<s>перечеркнутый</s>\n"
            "<u>подчеркнутый</u>\n"
            "<pre language='c++'>код</pre>\n"
            "<a href='smth.ru'>сайт</a>\n\n"
            "Переносы строк вводятся клавишей Enter", reply_markup=builder.as_markup())
        await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
        await state.set_state(States.waiting_for_global_message)
        await callback.answer()
    if callback.data == "create_db_archive":
        dump_filename = await create_dump_database()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_admin")
        )
        await safe_edit_text(callback.message,
            "<b>Копия базы данных сохранена</b>\n\n"
            f"Название: {dump_filename}\n\n"
            "Команда для восстановления:\n"
            "psql --file dump.sql (подключение через PG* env)", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "collate":
        items, dictionary_items = await collate()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_admin")
        )
        await safe_edit_text(callback.message,
            f"<b>Всего предметов на маркете: {len(items)}</b>\n"
            f"<b>Всего предметов в словаре: {len(dictionary_items.keys())}</b>", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "make_dict":
        await make_dictionary()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_admin")
        )
        await safe_edit_text(callback.message, "<b>Словарь обновлен</b>", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "back_to_admin":
        await safe_edit_text(callback.message, "<b>Выбери нужное действие:</b>", reply_markup=keyboard_admin())
        await callback.answer()
    if callback.data == 'invite_friends':
        total_balance = await get_total_balance(callback.from_user.id)
        number_of_invited_users = await get_number_of_invited_users(callback.from_user.id)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_profile")
        )
        await safe_edit_text(callback.message,
            "<b>Приглашай друзей и получай бонусы!</b>\n\n"
            "<b>В качестве вознаграждения ты будешь получать 5 💎 в боте за каждого приглашенного пользователя.</b>\n\n"
            "<b>За 💎 можно оформить Премиум на 30 дней.\n\n</b>"
            "<b>🤝 Реферальная программа</b>\n"
            f"├ Приглашено пользователей: {number_of_invited_users}\n"
            f"├ Всего заработано: {total_balance} 💎\n\n"
            "Ссылка для приглашения —\n"
            f"<b>http://t.me/{BOT_NAME}?start={callback.from_user.id}</b>", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "back_to_profile":
        balance = await get_user_balance(callback.from_user.id)
        registration_date = await get_registration_date(callback.from_user.id)
        premium = await is_user_premium(callback.from_user.id)
        premium_text = 'активен' if premium else 'отсутствует'
        premium_days_left = await expiration_date(callback.from_user.id)
        if premium_days_left is None:
            premium_days_left_text = "вечный"
        else:
            premium_days_left_text = premium_days_left
        if premium:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="📦 Подписки на предметы",
                callback_data="show_subscriptions")
            )
            builder.row(InlineKeyboardButton(
                text="🤝 Пригласить друзей",
                callback_data="invite_friends")
            )
            await safe_edit_text(callback.message,
                "👤 <b>Профиль</b>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"ID: <code>{callback.from_user.id}</code>\n"
                f"Никнейм: @{callback.from_user.username}\n"
                f"Баланс: {balance} 💎\n"
                f"Премиум: {premium_text}\n"
                f"Дата окончания: {premium_days_left_text}\n"
                f"Дата регистрации: {registration_date}\n"
                "➖➖➖➖➖➖➖➖➖➖", reply_markup=builder.as_markup())
        else:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="⭐️ Оформить Премиум",
                callback_data="make_subscription")
            )
            builder.row(InlineKeyboardButton(
                text="📦 Подписки на предметы",
                callback_data="show_subscriptions")
            )
            builder.row(InlineKeyboardButton(
                text="🤝 Пригласить друзей",
                callback_data="invite_friends")
            )
            await safe_edit_text(callback.message,
                "👤 <b>Профиль</b>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"ID: <code>{callback.from_user.id}</code>\n"
                f"Никнейм: @{callback.from_user.username}\n"
                f"Баланс: {balance} 💎\n"
                f"Премиум: {premium_text}\n"
                f"Дата регистрации: {registration_date}\n"
                "➖➖➖➖➖➖➖➖➖➖", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "show_subscriptions":
        subscriptions_results = await get_subscriptions(callback.from_user.id)
        if subscriptions_results:
            builder = InlineKeyboardBuilder()
            for user_id, ru_name, rank, price, more_less in subscriptions_results:
                if rank == -1:
                    sub_id = await get_subscription_id(user_id, ru_name, rank, price, more_less)
                    action_text = "больше или" if more_less else "меньше или"
                    builder.row(InlineKeyboardButton(
                        text=f"{ru_name} {action_text} {price} 💎",
                        callback_data=f"subscription:{sub_id}")
                    )
                else:
                    sub_id = await get_subscription_id(user_id, ru_name, rank, price, more_less)
                    action_text = "больше или" if more_less else "меньше или"
                    builder.row(InlineKeyboardButton(
                        text=f"{ru_name} {rank} ранга {action_text} {price} 💎",
                        callback_data=f"subscription:{sub_id}")
                    )
            builder.row(InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back_to_profile")
                )
            await safe_edit_text(callback.message,
                "Для отписки нажми на предмет.\n\n"
                "<b>Твои подписки:</b>", reply_markup=builder.as_markup())
        else:
            await callback.message.answer("<b>У тебя пока нет подписок.</b>")
        await callback.answer()
    if callback.data == 'make_subscription':
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="30 дней за 149 💎",
            callback_data="make_subscription_platinum")
        )
        builder.row(InlineKeyboardButton(
            text="30 дней за 149 ₽",
            url="https://boosty.to/creatonwf")
        )
        await safe_edit_text(callback.message, "<b>Выбери нужный вариант:</b>", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == 'make_subscription_platinum':
        balance = await get_user_balance(callback.from_user.id)
        if balance < 149:
            await safe_edit_text(callback.message, "<b>Недостаточно средств</b>")
        else:
            current_date = datetime.now()
            future_date = current_date + timedelta(days=30)
            formatted_date = future_date.strftime("%d.%m.%Y")
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="Да ✅",
                callback_data="pay_for_subscription_platinum")
            )
            builder.row(InlineKeyboardButton(
                text="Нет ❌",
                callback_data="back_to_profile")
            )
            await safe_edit_text(callback.message,
                "<b>Списать 149 💎 с баланса?</b>\n\n"
                f"Премиум будет активен 30 дней, до {formatted_date}", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == 'pay_for_subscription_platinum':
        balance = await get_user_balance(callback.from_user.id)
        if balance < 149:
            await safe_edit_text(callback.message, "<b>Недостаточно средств</b>")
        else:
            current_date = datetime.now()
            future_date = current_date + timedelta(days=30)
            paid = await remove_balance_for_sub_and_send_premium(149, future_date, callback.from_user.id)
            if not paid:
                await callback.answer("Баланс изменился или Премиум уже активен.", show_alert=True)
                return
            await safe_delete_message(callback.bot, callback.from_user.id, callback.message.message_id)
        await callback.answer()
    if callback.data == "hidden":
        await safe_delete_message(callback.bot, callback.from_user.id, callback.message.message_id)
        await state.clear()
        await callback.answer()
    if callback.data.startswith("block_user:"):
        user_id = callback.data.split(':')[1]
        await state.update_data(user_id=user_id)
        await safe_edit_text(callback.message, "<b>Введи причину блокировки</b>")
        await state.set_state(States.waiting_for_block)
        await callback.answer()
    if callback.data.startswith("unblock_user:"):
        user_id = callback.data.split(':')[1]
        await unblock_user(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} разблокирован.</b>")
        await callback.answer()
    if callback.data.startswith("add_admin:"):
        user_id = callback.data.split(':')[1]
        await add_admin(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} назначен администратором.</b>")
        await callback.answer()
    if callback.data.startswith("remove_admin:"):
        user_id = callback.data.split(':')[1]
        await remove_admin(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} удален из администраторов.</b>")
        await callback.answer()
    if callback.data.startswith("delete_from_database_user:"):
        user_id = callback.data.split(':')[1]
        await delete_from_database_user(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} удален.</b>")
        await callback.answer()
    if callback.data.startswith("add_access:"):
        user_id = callback.data.split(':')[1]
        await add_access_bot(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} теперь имеет доступ к боту.</b>")
        await callback.answer()
    if callback.data.startswith("remove_access:"):
        user_id = callback.data.split(':')[1]
        await remove_access_bot(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} теперь не имеет доступа к боту.</b>")
        await callback.answer()
    if callback.data.startswith("give_premium:"):
        user_id = callback.data.split(':')[1]
        await give_premium(user_id)
        await safe_edit_text(callback.message, f"<b>Пользователь {user_id} получил Премиум на +30 дней.</b>")
        await callback.answer()
    if callback.data == 'subscribe_to_item':
        isPremium = await is_user_premium(callback.from_user.id)
        if isPremium:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="Понижение цены 🔽",
                callback_data="low_price")
            )
            builder.row(InlineKeyboardButton(
                text="Повышение цены 🔼",
                callback_data="high_price")
            )
            builder.row(InlineKeyboardButton(
                text="✖️ Отмена",
                callback_data="cancel_subscription")
            )
            await safe_edit_text(callback.message, "<b>Выбери подходящий вариант:</b>", reply_markup=builder.as_markup())
        else:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="⭐️ Оформить Премиум",
                callback_data="make_subscription")
            )
            await callback.message.answer(
                "<b>Доступно только пользователем Премиума</b>",
                reply_markup=builder.as_markup()
            )
        await callback.answer()
    if callback.data.startswith("subscription:"):
        try:
            subscription_id_str = callback.data.split(':')[1]
            cleaned_subscription_id_str = subscription_id_str.strip("()").replace(",", "")
            subscription_id = int(cleaned_subscription_id_str)
            details = await get_subscription_details(subscription_id, callback.from_user.id)
            if details is None:
                await callback.answer("Подписка недоступна.", show_alert=True)
                return
            user_id, ru_name, rank, price, more_less = details
            await remove_subscriptions(user_id, ru_name, rank, price, more_less)
        except:
            await safe_edit_text(callback.message, "<b>Подписка уже отменена.</b>")
        registration_date = await get_registration_date(callback.from_user.id)
        balance = await get_user_balance(callback.from_user.id)
        premium = await is_user_premium(callback.from_user.id)
        premium_text = 'активен' if premium else 'отсутствует'
        premium_days_left = await expiration_date(callback.from_user.id)
        if premium_days_left is None:
            premium_days_left_text = "вечный"
        else:
            premium_days_left_text = premium_days_left
        if premium:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="📦 Подписки на предметы",
                callback_data="show_subscriptions")
            )
            builder.row(InlineKeyboardButton(
                text="🤝 Пригласить друзей",
                callback_data="invite_friends")
            )
            await safe_edit_text(callback.message,
                "👤 <b>Профиль</b>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"ID: <code>{callback.from_user.id}</code>\n"
                f"Никнейм: @{callback.from_user.username}\n"
                f"Баланс: {balance} 💎\n"
                f"Премиум: {premium_text}\n"
                f"Дата окончания: {premium_days_left_text}\n"
                f"Дата регистрации: {registration_date}\n"
                "➖➖➖➖➖➖➖➖➖➖", reply_markup=builder.as_markup())
        else:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="⭐️ Оформить Премиум",
                callback_data="make_subscription")
            )
            builder.row(InlineKeyboardButton(
                text="📦 Подписки на предметы",
                callback_data="show_subscriptions")
            )
            builder.row(InlineKeyboardButton(
                text="🤝 Пригласить друзей",
                callback_data="invite_friends")
            )
            await safe_edit_text(callback.message,
                "👤 <b>Профиль</b>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"ID: <code>{callback.from_user.id}</code>\n"
                f"Никнейм: @{callback.from_user.username}\n"
                f"Баланс: {balance} 💎\n"
                f"Премиум: {premium_text}\n"
                f"Дата регистрации: {registration_date}\n"
                "➖➖➖➖➖➖➖➖➖➖", reply_markup=builder.as_markup())
        await callback.answer()
    if callback.data == "low_price":
        data = await state.get_data()
        rank = data.get('has_rank', 'Нет ранга')
        more_less = False
        if not rank:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="✖️ Назад",
                callback_data="subscribe_to_item")
            )
            response_message = await safe_edit_text(callback.message, "<b>Введи минимальную стоимость предмета, при которой нужно оповестить</b>", reply_markup=builder.as_markup())
            await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
            await state.set_state(States.waiting_for_price)
        else:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="✖️ Назад",
                callback_data="subscribe_to_item")
            )
            response_message = await safe_edit_text(callback.message, "<b>Введи ранг предмета</b>", reply_markup=builder.as_markup())
            await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
            await state.set_state(States.waiting_for_rank)
        await state.update_data(more_less=more_less)
        await callback.answer()
    if callback.data == "high_price":
        data = await state.get_data()
        rank = data.get('has_rank', 'Нет ранга')
        more_less = True
        if not rank:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="✖️ Назад",
                callback_data="subscribe_to_item")
            )
            response_message = await safe_edit_text(callback.message, "<b>Введи максимальную стоимость предмета, при которой нужно оповестить</b>",  reply_markup=builder.as_markup())
            await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
            await state.set_state(States.waiting_for_price)
        else:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="✖️ Назад",
                callback_data="subscribe_to_item")
            )
            response_message = await safe_edit_text(callback.message, "<b>Введи ранг предмета</b>", reply_markup=builder.as_markup())
            await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
            await state.set_state(States.waiting_for_rank)
        await state.update_data(more_less=more_less)
        await callback.answer()
    if callback.data == "cancel_subscription":
        await safe_delete_message(callback.bot, callback.from_user.id, callback.message.message_id)
        await state.clear()
        await callback.answer()
    if callback.data == "change_rank":
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="✖️ Отмена",
            callback_data="subscribe_to_item")
        )
        response_message = await safe_edit_text(callback.message, "<b>Введи ранг предмета</b>", reply_markup=builder.as_markup())
        await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
        await state.set_state(States.waiting_for_rank)
        await callback.answer()

@router.message(States.waiting_for_block)
async def rank_input_handler(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return
    reason = message.text
    data = await state.get_data()
    user_id = data.get('user_id', 'без причины')
    await block_user(user_id, reason)
    await message.answer(f"<b>Пользователь {user_id} заблокирован.</b>")
    await state.clear()

@router.message(States.waiting_for_global_message)
async def global_message(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return
    if message.text is None:
        await message.answer("Отправьте текст сообщения.")
        return
    global_message = message.text
    if len(global_message) > 3000:
        await message.answer("<b>Сообщение не должно превышать 3000 символов</b>")
        await state.clear()
        return
    data = await state.get_data()
    message_to_delete = data.get('message_to_delete')
    await safe_delete_message(BOT, message_to_delete['chat_id'], message_to_delete['message_id'])


    result = await get_all_users()
    for data in result:
        user_id = data[0]
        await BOT.send_message(user_id, global_message)

    await state.clear()

@router.message(States.waiting_for_rank)
async def rank_input_handler(message: Message, state: FSMContext):
    try:
        rank = int(message.text)
        if rank < 0:
            await message.answer("<b>Ранг не может быть отрицательный.</b>")
            return
        elif rank > 50:
            await message.answer("<b>Ранг не может быть больше 50.</b>")
            return
    except ValueError:
        await message.answer("<b>Используй числовое значение.</b>")
        return
    await state.update_data(rank2=rank)
    data = await state.get_data()
    rank = data.get('rank2', -1)
    message_to_delete = data.get('message_to_delete')
    await safe_delete_message(BOT, message_to_delete['chat_id'], message_to_delete['message_id'])
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить ранг",
        callback_data="change_rank")
    )
    builder.row(InlineKeyboardButton(
        text="✖️ Отмена",
        callback_data="subscribe_to_item")
    )
    response_message = await message.answer(f"<b>Выбранный ранг: {rank}</b>\n<b>Введи минимальную стоимость предмета, при которой нужно оповестить</b>" if rank != -1 else "<b>Введи минимальную стоимость предмета, при которой нужно оповестить</b>", reply_markup=builder.as_markup())
    await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
    await state.set_state(States.waiting_for_price)

@router.message(States.waiting_for_price)
async def price_input_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    more_less = data.get('more_less', False)
    message_to_delete = data.get('message_to_delete')
    await safe_delete_message(BOT, message_to_delete['chat_id'], message_to_delete['message_id'])
    try:
        price = int(message.text)
        if price < 0:
            await message.answer("<b>Цена не может быть отрицательной.</b>")
            return
    except ValueError:
        await message.answer("<b>Используй числовое значение.</b>")
        return

    await state.update_data(price=price)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✖️ Отмена",
        callback_data="subscribe_to_item")
    )
    response_message = await message.answer("<b>Введи минимальное количество предметов, которое должно быть у продавца:</b>", reply_markup=builder.as_markup())
    await state.update_data(message_to_delete={'chat_id': response_message.chat.id, 'message_id': response_message.message_id})
    await state.set_state(States.waiting_for_count)

@router.message(States.waiting_for_count)
async def count_input_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    more_less = data.get('more_less', False)

    try:
        count = int(message.text)
        if count < 1:
            await message.answer("<b>Количество должно быть хотя бы один</b>")
            return
    except ValueError:
        await message.answer("<b>Используй числовое значение.</b>")
        return

    item_name = data.get('item_name', 'Неизвестный предмет')
    ru_name = data.get('ru_name', 'Неизвестный предмет')
    rank = data.get('rank2', -1)
    price = data.get('price', 0)
    message_to_delete = data.get('message_to_delete')

    result = await new_subscription(message.from_user.id, item_name, ru_name, rank, price, count, more_less)
    if result:
        await safe_delete_message(BOT, message_to_delete['chat_id'], message_to_delete['message_id'])
        action_text = "повышении" if more_less else "снижении"
        if rank == -1:
            await message.answer(f"Ты подписался на уведомления о {action_text} цены для предмета <b>{ru_name}</b> {'от' if more_less else 'до'} <b>{price}</b> 💎 или {'выше' if more_less else 'ниже'} с количеством {count} и больше.")
        else:
            await message.answer(f"Ты подписался на уведомления о {action_text} цены для предмета <b>{ru_name} {rank} ранга</b> {'от' if more_less else 'до'} <b>{price}</b> 💎 или {'выше' if more_less else 'ниже'} с количеством {count} и больше.")
    else:
        await message.answer("<b>Нельзя подписаться более чем на 4 предмета одновременно, отпишись от какого-либо предмета в профиле.</b>")
    await state.clear()

async def fetch(session, url, msg):
    for attempt in range(int(20)):
        try:
            async with session.get(url, timeout=2) as response:
                return await response.json()
        except TimeoutError:
            if attempt == int(20) - 1:
                if msg:
                    await msg.answer("<b>Кажется, API warframe.market в настоящий момент недоступен. Пожалуйста, попробуй выполнить запрос повторно через несколько минут.</b>")
                return {}

@router.message()
async def message_handler(msg: Message, state: FSMContext):
    if msg.text is None:
        await msg.reply("<b>Сообщение не должно быть пустым.</b>")
        return

    item = msg.text.lower()

    if item.startswith("user:"):
        is_admin = await is_user_admin(msg.from_user.id)
        if is_admin:
            query = item[5:].strip()
            if not query:
                await msg.reply("<b>ID или username пользователя обязателен.</b>")
                return

            user_records = await search_users_by_query(item[5:])
            if not user_records:
                await msg.reply("<b>Пользователь не найден.</b>")
                return
            for record in user_records:
                builder = InlineKeyboardBuilder()

                builder.row(InlineKeyboardButton(text="Разблокировать" if record[14] else "Заблокировать", callback_data=f"unblock_user:{record[3]}" if record[14] else f"block_user:{record[3]}"))
                builder.row(InlineKeyboardButton(text="Забрать админку" if record[13] else "Выдать админку", callback_data=f"remove_admin:{record[3]}" if record[13] else f"add_admin:{record[3]}"))
                builder.row(InlineKeyboardButton(text="Забрать доступ к боту" if record[12] else "Дать доступ к боту", callback_data=f"remove_access:{record[3]}" if record[12] else f"add_access:{record[3]}"))
                builder.row(InlineKeyboardButton(text="Выдать Премиум на +30 дней", callback_data=f"give_premium:{record[3]}"))
                builder.row(InlineKeyboardButton(text="Удалить из БД", callback_data=f"delete_from_database_user:{record[3]}"))
                builder.row(InlineKeyboardButton(text="✖️ Скрыть", callback_data="hidden"))

                await msg.reply(
                    f"<b>Уникальный ID: {record[0]}</b>\n"
                    f"<b>Дата регистрации: {record[1].strftime('%d.%m.%Y %H:%M')}</b>\n"
                    f"<b>Последняя активность: {'отсутствует' if record[2] is None else record[2].strftime('%d.%m.%Y %H:%M')}</b>\n"
                    f"<b>ID: <code>{record[3]}</code></b>\n"
                    f"<b>Никнейм: {'-' if record[4] is None else record[4]}</b>\n"
                    f"<b>Имя: {'-' if record[5] is None else record[5]}</b>\n"
                    f"<b>Фамилия: {'-' if record[6] is None else record[6]}</b>\n"
                    f"<b>Кто пригласил: {'никто' if record[7] is None else '<code>' + str(record[7]) + '</code>'}</b>\n"
                    f"<b>Баланс: {record[8]} 💎</b>\n"
                    f"<b>Общий заработанный баланс: {record[9]} 💎</b>\n"
                    f"<b>Премиум: {'активен' if record[10] else 'отсутсвует'}</b>\n"
                    f"<b>Дата окончания: {'вечный' if record[11] is None else record[11].strftime('%d.%m.%Y %H:%M')}</b>\n"
                    f"<b>Доступ к боту: {'да' if record[12] else 'нет'}</b>\n"
                    f"<b>Админ: {'да' if record[13] else 'нет'}</b>\n"
                    f"<b>Заблокирован: {'да' if record[14] else 'нет'}</b>\n"
                    f"<b>Прична блокировки: {'-' if record[15] is None else record[15]}</b>",
                    reply_markup=builder.as_markup()
                )
        return

    item_name = get_item_key(item)
    item_name_en = find_english_name(item_name)

    api_url = f"https://api.warframe.market/v1/items/{item_name}/orders?include=item"
    TAG_TRANSLATION = {
        'arcane_enhancement': 'Мистификатор',
        'prime': 'Прайм',
        'mod': 'Мод'
    }

    async with ClientSession() as session:
        response = await fetch(session, api_url, msg)

        orders = response.get('payload', {}).get('orders', {})

        processed_orders = [order for order in orders if order['user']['status'] == 'ingame' and order['order_type'] == 'sell']

        items_in_set = response.get('include', {}).get('item', {}).get('items_in_set', [])
        item_in_set = next((item for item in items_in_set if item.get('url_name') == item_name), None)

        if item_in_set is None:
            try:
                await msg.reply("<b>Предмет не найден</b>")
            except:
                pass
            return

        ru_name = translations.get(item_name, item_in_set.get('ru', {}).get('item_name', item))
        ducats = item_in_set.get('ducats', None)
        tags = item_in_set.get('tags', [])

        relevant_tags = ['arcane_enhancement', 'prime', 'mod']
        found_tags = [TAG_TRANSLATION[tag] for tag in tags if tag in relevant_tags]

        if processed_orders:
            orders_with_rank = [order for order in processed_orders if 'mod_rank' in order]
            if orders_with_rank:
                has_rank = True
                min_mod_rank_offer = min(processed_orders, key=lambda x: (x['mod_rank'], x['platinum']))
                max_mod_rank_offer = min(processed_orders, key=lambda x: (-x['mod_rank'], x['platinum']))

                answer_lines = [
                    f"<b>Предмет:</b> <code>{ru_name}</code> <b>| {', '.join(found_tags) if found_tags else 'Прочее'} </b>\n\n"
                    f"<b>Минимальная цена за {min_mod_rank_offer['mod_rank']} ранг - {min_mod_rank_offer['platinum']} </b>💎\n"
                    f"<b>Продавец:</b> <code>{min_mod_rank_offer['user']['ingame_name']}</code>\n\n"
                    f"<code>/w {min_mod_rank_offer['user']['ingame_name']} Hi! I want to buy: {item_name_en}{' (rank '+ str(min_mod_rank_offer['mod_rank']) +')'} for {min_mod_rank_offer['platinum']} platinum. (WAnalyser)</code>\n\n"
                    f"<b>Минимальная цена за {max_mod_rank_offer['mod_rank']} ранг - {max_mod_rank_offer['platinum']} </b>💎\n"
                    f"<b>Продавец:</b> <code>{max_mod_rank_offer['user']['ingame_name']}</code>\n\n"
                    f"<code>/w {max_mod_rank_offer['user']['ingame_name']} Hi! I want to buy: {item_name_en}{' (rank '+ str(max_mod_rank_offer['mod_rank']) +')'} for {max_mod_rank_offer['platinum']} platinum. (WAnalyser)</code>"
                ]
            else:
                has_rank = False
                min_price_offer = min(processed_orders, key=lambda x: x['platinum'])
                if ducats is None:
                    answer_lines = [
                        f"<b>Предмет:</b> <code>{ru_name}</code> <b>| {', '.join(found_tags) if found_tags else 'Прочее'} </b>\n\n"
                        "<b>У предмета отсутствует ранг</b>\n\n"
                        f"<b>Минимальная цена - {min_price_offer['platinum']} </b>💎\n"
                        f"<b>Продавец:</b> <code>{min_price_offer['user']['ingame_name']}</code>\n\n"
                        f"<code>/w {min_price_offer['user']['ingame_name']} Hi! I want to buy: {item_name_en} for {min_price_offer['platinum']} platinum. (WAnalyser)</code>"
                    ]
                else:
                    answer_lines = [
                        f"<b>Предмет:</b> <code>{ru_name}</code> <b>| {', '.join(found_tags) if found_tags else 'Прочее'} </b>\n\n"
                        f"<b>Цена в дукатах - {ducats}</b>\n\n"
                        "<b>У предмета отсутствует ранг</b>\n\n"
                        f"<b>Минимальная цена - {min_price_offer['platinum']} </b>💎\n"
                        f"<b>Продавец:</b> <code>{min_price_offer['user']['ingame_name']}</code>\n\n"
                        f"<code>/w {min_price_offer['user']['ingame_name']} Hi! I want to buy: {item_name_en} for {min_price_offer['platinum']} platinum. (WAnalyser)</code>",
                    ]
            await state.update_data(item_name=item_name, ru_name=ru_name, has_rank=has_rank)
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="👁‍🗨 Подписаться на предмет",
                callback_data="subscribe_to_item")
            )

            await msg.reply("\n".join(answer_lines),
            reply_markup=builder.as_markup())

notifications_sent = {}

async def check_prices_and_notify():
    async with ClientSession() as session:
        subscriptions = await get_all_subscriptions()
        for subscription in subscriptions:
            unique_id, created_at, user_id, item_name, ru_name, rank, price, count, more_less = subscription
            sub_id = await get_subscription_id(user_id, ru_name, rank, price, more_less)

            response = await fetch(session, f"https://api.warframe.market/v1/items/{item_name}/orders?include=item", None)
            orders = response.get('payload', {}).get('orders', {})
            items_in_set = response.get('include', {}).get('item', {}).get('items_in_set', [])
            item_in_set = next((item for item in items_in_set if item.get('url_name') == item_name), None)

            filtered_orders = [
                order for order in orders
                if order['user']['status'] == 'ingame'
                and order['order_type'] == 'sell'
                and ((more_less and order['platinum'] >= price) or (not more_less and order['platinum'] <= price))
                and (order.get('mod_rank') == rank or rank == -1)
                and order['quantity'] >= count
            ]

            if not filtered_orders:
                continue

            sorted_orders = sorted(filtered_orders, key=lambda x: x['platinum'])
            grouped_orders = {}
            for order in sorted_orders:
                if order['platinum'] in grouped_orders:
                    grouped_orders[order['platinum']].append(order)
                else:
                    grouped_orders[order['platinum']] = [order]

            prices_notified = 0
            for price, orders in grouped_orders.items():
                for order in orders:
                    if prices_notified >= 3:
                        break

                    ingame_name = order['user']['ingame_name']
                    mod_rank = order.get('mod_rank', None)
                    platinum = order['platinum']
                    quantity = order['quantity']
                    en_name = item_in_set.get('en', {}).get('item_name', item_name)

                    notification_key = f"{sub_id}:{ingame_name}:{platinum}"
                    if notifications_sent.get(notification_key, 0) < 1:
                        notifications_sent[notification_key] = notifications_sent.get(notification_key, 0) + 1
                        builder = InlineKeyboardBuilder()
                        builder.row(InlineKeyboardButton(
                            text="✖️ Скрыть",
                            callback_data="hidden")
                        )
                        try:
                            await BOT.send_message(user_id,
                                f"<b>Уведомление подписки:</b>\n\n"
                                f"Предмет <b>{ru_name} {'с рангом ' + str(mod_rank) if mod_rank is not None and rank != -1 else ''}</b> появился по цене <b>{platinum}</b> 💎 у продавца <b>{ingame_name}</b>, кол-во: <b>{quantity}</b>\n\n"
                                f"<code>/w {ingame_name} Hi! I want to buy: {en_name}{' (rank '+ str(mod_rank) +')' if mod_rank is not None and rank != -1 else ''} for {platinum} platinum. (WAnalyser)</code>",
                                reply_markup=builder.as_markup()
                            )
                        except:
                            pass

                    prices_notified += 1

                if prices_notified >= 3:
                    break

@router.inline_query()
async def live_search(inline_query: InlineQuery):
    DICTIONARY = load_dictionary()
    query = inline_query.query

    if not query.strip() or len(query) <= 2:
        await inline_query.answer(results=[], cache_time=1, is_personal=True)
        return

    offset = int(inline_query.offset) if inline_query.offset else 0
    filtered_messages = [item['ru'] for item in DICTIONARY["DICTIONARY"].values() if isinstance(item.get('ru'), str) and query.lower() in item['ru'].lower()]

    chunk = filtered_messages[offset:offset + 50]

    results = [
        InlineQueryResultArticle(
            id=str(index + offset),
            title=message,
            input_message_content=InputTextMessageContent(message_text=message)
        ) for index, message in enumerate(chunk)
    ]

    next_offset = str(offset + 50) if len(filtered_messages) > offset + 50 else None

    await inline_query.answer(results, cache_time=1, is_personal=True, next_offset=next_offset)

async def check_expiration_subscribe_premium():
    result = await expiration_date2()
    for data in result:
        user_id, expiration_date, notification, premium_expired, premium_start = data
        if expiration_date is not None:
            if datetime.now() > expiration_date and not premium_expired:
                try:
                    await BOT.send_message(user_id, "<b>Премиум закончился.</b>")
                except:
                    pass
                await update_premium_status(user_id)
            elif not notification and timedelta(days=0) < (expiration_date - datetime.now()) <= timedelta(days=1):
                try:
                    await BOT.send_message(user_id, "<b>До окончания Премиума осталось менее 24 часов.</b>")
                except:
                    pass
                await update_notification_sent2(user_id)
            elif premium_start:
                try:
                    await BOT.send_message(user_id, f"<b>Премиум активирован до {expiration_date.strftime('%d.%m.%Y %H:%M')}</b>")
                except:
                    pass
                await update_notification_sent3(user_id)
