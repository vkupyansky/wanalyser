from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def keyboard_top():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🥇 Общий топ", callback_data="top_all"))
    builder.row(InlineKeyboardButton(text="🥇 Топ моды", callback_data="top_mods"))
    builder.add(InlineKeyboardButton(text="🥇 Топ праймы", callback_data="top_primes"))
    builder.row(InlineKeyboardButton(text="🥇 Топ мистификаторы", callback_data="top_mist"))
    builder.row(InlineKeyboardButton(text="🥇 Топ коллекционные", callback_data="top_collections"))
    builder.row(InlineKeyboardButton(text="✖️ Скрыть", callback_data="hidden"))
    return builder.as_markup()

def keyboard_admin():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏆 Статистика", callback_data="admin_statistic"))
    builder.row(InlineKeyboardButton(text="📢 Глобальное оповещение", callback_data="global_message"))
    builder.row(InlineKeyboardButton(text="🗄 Создать копию БД", callback_data="create_db_archive"))
    builder.row(InlineKeyboardButton(text="📚 Сравнить маркет и словарь", callback_data="collate"))
    builder.row(InlineKeyboardButton(text="🆕 Обновить словарь", callback_data="make_dict"))
    builder.row(InlineKeyboardButton(text="✖️ Скрыть", callback_data="hidden"))
    return builder.as_markup()
