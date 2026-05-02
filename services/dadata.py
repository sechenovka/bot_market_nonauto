import aiohttp
from config import DADATA_API_KEY, DADATA_SECRET_KEY

DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"

async def search_organizations(query: str, count: int = 5) -> list[dict]:
    headers = {"Authorization": f"Token {DADATA_API_KEY}"}
    if DADATA_SECRET_KEY:
        headers["X-Secret"] = DADATA_SECRET_KEY
    payload = {"query": query, "count": count, "status": ["ACTIVE"]}
    async with aiohttp.ClientSession() as session:
        async with session.post(DADATA_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            suggestions = data.get("suggestions", [])
            result = []
            for s in suggestions:
                party = s["data"]
                if party.get("type") != "INDIVIDUAL":
                    continue
                inn = party.get("inn")
                name = party.get("value") or party.get("name", {}).get("short_with_opf")
                if not name:
                    continue
                phones = [p["value"] for p in party.get("phones", [])]
                emails = [e["value"] for e in party.get("emails", [])]
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