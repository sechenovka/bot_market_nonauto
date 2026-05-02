import aiohttp
from services.deepseek import analyze_raw_text

AVITO_URL = "https://www.avito.ru/web/1/main/items"

async def fetch_avito_with_reviews(query: str, location_id: int = 637640, limit: int = 5) -> list[dict]:
    params = {
        'query': query,
        'locationId': location_id,
        'limit': limit,
        'sort': 'date'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(AVITO_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                items = []
                for item in data.get('items', []):
                    reviews = item.get('seller', {}).get('reviewsCount', 0)
                    if reviews > 0:
                        items.append({
                            'id': item['id'],
                            'title': item.get('title'),
                            'url': f"https://www.avito.ru{item.get('urlPath', '')}",
                            'reviews': reviews
                        })
                return items
        except Exception as e:
            print(f"Avito error: {e}")
            return []

async def process_avito_items(query: str, channel_id: int, bot) -> None:
    listings = await fetch_avito_with_reviews(query)
    for item in listings:
        analysis = await analyze_raw_text(f"Продаю: {item['title']}. Много отзывов.")
        if analysis.get('type') and analysis['type'] != 'none':
            probs = '\n'.join(f'• {p}' for p in analysis.get('problems', []))
            text = (
                f"🛍 <b>Avito: {item['title']}</b>\n"
                f"🔗 <a href='{item['url']}'>Смотреть товар</a>\n"
                f"⭐ Отзывов: {item['reviews']}\n\n"
                f"<b>Возможные проблемы:</b>\n{probs}\n"
                f"<i>Источник: Avito (незарегистрированный продавец)</i>"
            )
            try:
                await bot.send_message(channel_id, text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки Avito-сообщения: {e}")
        else:
            await bot.send_message(channel_id,
                f"🔍 Найден популярный товар на Avito:\n<a href='{item['url']}'>{item['title']}</a> (отзывов: {item['reviews']})",
                parse_mode="HTML")