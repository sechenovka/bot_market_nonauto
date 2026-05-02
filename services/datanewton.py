import aiohttp
from config import DATANEWTON_API_KEY

DATANEWTON_URL = "https://api.datanewton.ru/v1/search/company"  # уточни URL в документации

async def search_companies(query: str, count: int = 5) -> list[dict]:
    headers = {"Authorization": f"Bearer {DATANEWTON_API_KEY}"}
    params = {"q": query, "limit": count}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(DATANEWTON_URL, headers=headers, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                items = data.get("items", [])
                result = []
                for item in items:
                    inn = item.get("inn")
                    name = item.get("name") or item.get("short_name")
                    if not name:
                        continue
                    phones = [p.get("value") for p in item.get("phones", [])]
                    emails = [e.get("value") for e in item.get("emails", [])]
                    result.append({
                        "name": name,
                        "inn": inn,
                        "type": None,
                        "registration": "registered",
                        "description": item.get("okved") or "",
                        "contacts": {
                            "phone": phones[0] if phones else None,
                            "email": emails[0] if emails else None,
                            "site": item.get("site") or None
                        },
                        "source": "datanewton"
                    })
                return result
        except Exception as e:
            print(f"DataNewton error: {e}")
            return []