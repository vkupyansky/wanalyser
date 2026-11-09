import asyncio
import os
import tempfile
from pathlib import Path

from psycopg.conninfo import conninfo_to_dict
from config import PG_DSN
import json
from datetime import datetime
from api import *
from database import insert_newtop

translations = {
    'hexis_armor_set': 'Набор Брони Гексис',
    'lokan_armor_set': 'Набор Брони Локан',
    'melee_animosity': 'Враждебность Ближнего Боя',
    'melee_crescendo': 'Крещендо Ближнего Боя',
    'melee_duplicate': 'Двойной Удар',
    'melee_exposure': 'Обнаружение Ближнего Боя',
    'melee_fortification': 'Укрепление Ближнего Боя',
    'melee_influence': 'Влияние Ближнего Боя',
    'melee_retaliation': 'Возмездие Ближнего Боя',
    'melee_vortex': 'Вихрь Ближнего Боя',
    'meridian_armor_set': 'Набор Брони Меридиан',
    'ostron_armor_set': 'Набор Брони  Острон',
    'perrin_armor_set': ' Набор Брони Перрин',
    'red_veil_armor_set': 'Набор Брони Красная Вуаль',
    'solaris_armor_set': 'Набор Брони Солярис',
    'suda_armor_set': 'Набор Брони Суда',
}

async def collate():
    data = await get_info()
    items = data.get("data", [])
    try:
        with open('dictionary.json', 'r') as file:
            data = json.load(file)
            dictionary_items = data["DICTIONARY"]
    except FileNotFoundError:
        print("Словарь не найден")
    return items, dictionary_items

async def make_dictionary():
    data = await get_info()
    items = sorted(data.get("data", []), key=lambda x: x.get("urlName"))

    content = {
        "DICTIONARY": {
            item.get("urlName"): {
                'ducats': item.get("ducats"),
                'en': item.get("i18n", {}).get("en", {}).get("name"),
                'ru': translations.get(item.get("urlName"), item.get("i18n", {}).get("ru", {}).get("name"))
            } for item in items
        }
    }

    with open("dictionary.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)

async def make_top():
    data = await get_info()
    items = [{"url_name": item["urlName"], "ru_name": item["i18n"]["ru"]["name"]} for item in data.get("data", [])]
    collection = {"corpus_void_key", "ancient_fusion_core", "equilibrium_(steam_pinnacle_pack)"}

    for item in items:
        url_name = item["url_name"]
        data = await get_tag(url_name)
        tags = data.get("data", {}).get("tags", [])

        if url_name in collection:
            tag = "Коллекция"
        elif "mod" in tags:
            tag = "Мод"
        elif "prime" in tags:
            tag = "Прайм" + next((f" {item}" for item in ["Warframe", "Weapon"] if item.lower() in tags), "")
        elif "arcane_enhancement" in tags:
            tag = "Мистификатор"
        else:
            tag = "Прочее"

        orders = await get_price(url_name)
        filtered_orders = [order for order in orders.get("data", []) if order["type"] == "sell" and order["user"]["status"] == "ingame"]

        if filtered_orders:
            if not any("rank" in order for order in filtered_orders):
                min_price_no_rank = min(order["platinum"] for order in filtered_orders)
                await insert_newtop(translations.get(url_name, item['ru_name']), tag, None, None, None, None, min_price_no_rank)
            else:
                rank_prices = {order["rank"]: [] for order in filtered_orders if "rank" in order}
                for order in filtered_orders:
                    if "rank" in order:
                        rank_prices[order["rank"]].append(order["platinum"])

                min_rank = min(rank_prices.keys())
                max_rank = max(rank_prices.keys())
                min_price_min_rank = min(rank_prices[min_rank])
                min_price_max_rank = min(rank_prices[max_rank])
                await insert_newtop(translations.get(url_name, item['ru_name']), tag, min_rank, min_price_min_rank, max_rank, min_price_max_rank, None)

async def create_dump_database():
    directory = Path("database_dumps")
    directory.mkdir(mode=0o700, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    descriptor, path = tempfile.mkstemp(prefix=f"dump_{timestamp}_", suffix=".sql", dir=directory)
    connection_options = conninfo_to_dict(PG_DSN)
    environment = os.environ.copy()
    for key, value in connection_options.items():
        variable = "PGDATABASE" if key == "dbname" else "PG" + key.upper()
        environment[variable] = value
    try:
        with os.fdopen(descriptor, "wb") as output:
            process = await asyncio.create_subprocess_exec(
                "pg_dump", "--no-password", "--schema=public",
                stdout=output, stderr=asyncio.subprocess.PIPE, env=environment,
            )
            await process.communicate()
        if process.returncode:
            raise RuntimeError("pg_dump завершился с ошибкой; проверьте настройки PostgreSQL")
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise
    return Path(path).name
