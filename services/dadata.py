import aiohttp
from services.http_client import get_session
from config import DADATA_API_KEY, DADATA_SECRET_KEY

DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"

async def search_organizations(query: str, count: int = 5) -> list[dict]:
    headers = {"Authorization": f"Token {DADATA_API_KEY}"}
    if DADATA_SECRET_KEY:
        headers["X-Secret"] = DADATA_SECRET_KEY
    payload = {"query": query, "count": count, "status": ["ACTIVE"]}
    async with get_session() as session:
        async with session.post(DADATA_URL, json=payload, headers=headers) as resp:
            print(f"[Dadata] Статус ответа: {resp.status}")
            if resp.status != 200:
                return []
            try:
                data = await resp.json()
            except Exception as e:
                print(f"[Dadata] Ошибка парсинга JSON: {e}")
                return []
            suggestions = data.get("suggestions", [])
            result = []
            for s in suggestions:
                party = s["data"]
                # убрали фильтр по типу, берём и ИП, и юрлиц
                inn = party.get("inn")
                name = party.get("value") or party.get("name", {}).get("short_with_opf")
                if not name:
                    continue
                # безопасное извлечение телефонов
                phones_list = party.get("phones")
                if phones_list is None:
                    phones_list = []
                phones = [p["value"] for p in phones_list]

                emails_list = party.get("emails")
                if emails_list is None:
                    emails_list = []
                emails = [e["value"] for e in emails_list]

                contacts = {
                    "phone": phones[0] if phones else None,
                    "email": emails[0] if emails else None,
                    "site": party.get("site") or None,
                }
                result.append({
                    "name": name,
                    "inn": inn,
                    "type": None,
                    "registration": "registered",
                    "description": party.get("okved") or "",
                    "contacts": contacts,
                    "source": "dadata"
                })
            return result