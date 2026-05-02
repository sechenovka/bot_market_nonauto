import aiohttp
import re
from services.deepseek import analyze_raw_text
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
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(YANDEX_SEARCH_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
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
            print(f"Яндекс.Поиск ошибка: {e}")
            return []

async def process_avito_items(query: str, channel_id: int, bot) -> None:
    listings = await search_avito_via_yandex(query)
    for item in listings:
        analysis = await analyze_raw_text(f"Продаю: {item['title']}.")
        if analysis.get('type') and analysis['type'] != 'none':
            probs = '\n'.join(f'• {p}' for p in analysis.get('problems', []))
            text = (
                f"🛍 <b>Avito: {item['title']}</b>\n"
                f"🔗 <a href='{item['url']}'>Смотреть объявление</a>\n\n"
                f"<b>Возможные проблемы:</b>\n{probs}\n"
                f"<i>Источник: Avito (легальный поиск)</i>"
            )
        else:
            text = f"🔍 Найден популярный товар на Avito:\n<a href='{item['url']}'>{item['title']}</a>"
        try:
            await bot.send_message(channel_id, text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки Avito-сообщения: {e}")