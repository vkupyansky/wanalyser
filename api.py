import asyncio
from aiohttp import ClientSession

semaphore = asyncio.Semaphore(1)

async def fetch(url, headers):
    async with semaphore:
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                await asyncio.sleep(0.4)
                return await response.json()

async def get_info():
    url = "https://api.warframe.market/v2/items"
    headers = {"User-Agent": "WAnalyser (https://github.com/vkupyansky/wanalyser)", "Language": "ru"}
    return await fetch(url, headers)

async def get_tag(url_name):
    url = f"https://api.warframe.market/v2/items/{url_name}"
    headers = {"User-Agent": "WAnalyser (https://github.com/vkupyansky/wanalyser)"}
    return await fetch(url, headers)

async def get_price(url_name):
    url = f"https://api.warframe.market/v2/orders/item/{url_name}"
    headers = {"User-Agent": "WAnalyser (https://github.com/vkupyansky/wanalyser)"}
    return await fetch(url, headers)
