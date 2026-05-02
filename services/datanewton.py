import aiohttp
from config import DATANEWTON_API_KEY

DATANEWTON_BASE = "https://api.datanewton.ru/v1"
HEADERS = {
    "Authorization": f"Bearer {DATANEWTON_API_KEY}",
    "Content-Type": "application/json"
}

async def search_companies(query: str, count: int = 5) -> list[dict]:
    endpoint = f"{DATANEWTON_BASE}/search"
    params = {
        "q": query,
        "per_page": count,
        "type": "company"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(endpoint, params=params, headers=HEADERS) as resp:
                if resp.status != 200:
                    print(f"DataNewton error: {resp.status}")
                    return []
                data = await resp.json()
                items = data.get("items", [])
                results = []
                for item in items:
                    name = item.get("name", {}).get("short_with_opf") or item.get("name", {}).get("full")
                    inn = item.get("inn")
                    ogrn = item.get("ogrn")
                    address = item.get("address", {}).get("value") if item.get("address") else None
                    okved = item.get("okved", {}).get("name") if item.get("okved") else None
                    phones = item.get("phones", [])
                    emails = item.get("emails", [])
                    contacts = {
                        "phone": phones[0] if phones else None,
                        "email": emails[0] if emails else None,
                        "site": item.get("site") or None
                    }
                    results.append({
                        "name": name,
                        "inn": inn,
                        "ogrn": ogrn,
                        "type": "ИП" if item.get("type") == "individual" else "ООО",
                        "registration": "registered",
                        "description": okved or "",
                        "contacts": contacts,
                        "source": "datanewton"
                    })
                return results
        except Exception as e:
            print(f"DataNewton exception: {e}")
            return []