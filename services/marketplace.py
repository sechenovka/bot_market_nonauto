import aiohttp
import re
from services.http_client import get_session
from config import YANDEX_FOLDER_ID, YANDEX_API_KEY

YANDEX_SEARCH_URL = "https://yandex.ru/search/xml"

async def search_avito_via_yandex(query: str, limit: int = 5) -> list[dict]:
    params = {
        'folderid': YANDEX_FOLDER_ID,
        'apikey': YANDEX_API_KEY,
        'query': f'site:avito.ru {query}',
        'lr': '213',
        'l10n': 'ru',
        'sortby': 'rlv',
        'filter': 'moderate',
        'maxpassages': '0',
        'groupby': 'attr=d.mode=flat.groups-on-page=5.docs-in-group=1',
        'page': '0',
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with get_session() as session:
        try:
            async with session.get(YANDEX_SEARCH_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    print(f"[Avito] Статус: {resp.status}")
                    return []
                data = await resp.text()
                urls = re.findall(r'<url>(https://www\.avito\.ru[^<]+)</url>', data)
                titles = re.findall(r'<title>(.*?)</title>', data)
                items = []
                for i in range(min(len(urls), len(titles), limit)):
                    items.append({
                        'id': str(hash(urls[i])),
                        'title': titles[i],
                        'url': urls[i],
                        'reviews': 0
                    })
                return items
        except Exception as e:
            print(f"[Avito] Ошибка: {e}")
            return []

async def process_avito_items(query: str, channel_id: int, bot) -> None:
    listings = await search_avito_via_yandex(query)
    for item in listings:
        text = f"🛍 <b>Avito: {item['title']}</b>\n🔗 <a href='{item['url']}'>Смотреть объявление</a>"
        try:
            await bot.send_message(channel_id, text, parse_mode="HTML")
        except Exception as e:
            print(f"[Avito] Ошибка отправки: {e}")