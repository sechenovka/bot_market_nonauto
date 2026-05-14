import asyncio
import random
import json
import uuid
from datetime import datetime
from database import fetch_one, execute_db
from services.dadata import search_organizations
from services.datanewton import search_companies
from services.marketplace import process_avito_items
from services.problems_by_okved import get_problems_by_okved
from config import CHANNEL_ID

KEYWORDS = [
    "детский сад", "школа", "продуктовый магазин", "интернет-магазин одежды",
    "автосервис", "парикмахерская", "ремонт обуви", "аптека", "турфирма",
    "доставка еды", "цветочный магазин", "ювелирная мастерская",
    "продажа автозапчастей", "сервис по ремонту телефонов",
    "столярная мастерская", "типография", "агентство недвижимости"
]

class SearchController:
    def __init__(self):
        self.is_running = False
        self.task = None
        self.bot = None

    async def start(self, bot):
        self.bot = bot
        self.is_running = True
        self.task = asyncio.create_task(self._search_loop())

    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()

    async def _search_loop(self):
        await asyncio.sleep(2)
        while self.is_running:
            try:
                keyword = random.choice(KEYWORDS)
                print(f"🔍 Ищу: {keyword}")

                # 1. Dadata
                print("→ Запрашиваю Dadata...")
                orgs_dadata = await search_organizations(keyword, count=3)
                print(f"   Dadata вернула: {len(orgs_dadata)} записей")
                for biz in orgs_dadata:
                    await self._process_official_business(biz)

                # 2. DataNewton
                print("→ Запрашиваю DataNewton...")
                orgs_newton = await search_companies(keyword, count=3)
                print(f"   DataNewton вернул: {len(orgs_newton)} записей")
                for biz in orgs_newton:
                    if not biz["inn"]:
                        continue
                    # Проверка на дубликат
                    row = await fetch_one("SELECT id FROM business WHERE inn = ?", (biz["inn"],))
                    if row:
                        continue
                    await self._process_official_business(biz)

                # 3. Avito
                avito_queries = ["айфон", "мебель ручной работы", "вязаные вещи"]
                for q in avito_queries:
                    print(f"→ Avito запрос: {q}")
                    await process_avito_items(q, CHANNEL_ID, self.bot)

                print("✅ Цикл завершён, жду 15 минут")
                await asyncio.sleep(random.randint(900, 1800))

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)

    async def _process_official_business(self, biz: dict):
        okved_code = biz.get("description")
        problems = get_problems_by_okved(okved_code)

        biz_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await execute_db("""
            INSERT OR IGNORE INTO business (id, name, inn, type, registration, description, routineProblems, contacts, source, sourceUrl, isDevelopedTech, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            biz_id,
            biz["name"],
            biz.get("inn"),
            None,
            "registered",
            okved_code,
            json.dumps(problems, ensure_ascii=False),
            json.dumps(biz.get("contacts", {}), ensure_ascii=False),
            biz.get("source", "dadata"),
            None,
            0,
            now,
            now
        ))

        record = {
            "id": biz_id,
            "name": biz["name"],
            "inn": biz.get("inn"),
            "type": "не определён",
            "registration": "registered",
            "description": okved_code,
            "routineProblems": json.dumps(problems, ensure_ascii=False),
            "contacts": json.dumps(biz.get("contacts", {}), ensure_ascii=False),
            "source": biz.get("source", "dadata"),
            "sourceUrl": None
        }
        await self._post_to_channel(record)

    async def _post_to_channel(self, record):
        problems = record.get("routineProblems", "[]")
        contacts = record.get("contacts", "{}")
        text = ""
        try:
            prob_list = json.loads(problems) if isinstance(problems, str) else problems
            problems_str = "\n".join(f"• {p}" for p in prob_list) if prob_list else "Неизвестны"
            if record["source"] in ("dadata", "datanewton"):
                cont_dict = json.loads(contacts) if isinstance(contacts, str) else contacts
                parts = []
                if cont_dict.get("phone"): parts.append(f"📞 {cont_dict['phone']}")
                if cont_dict.get("email"): parts.append(f"📧 {cont_dict['email']}")
                if cont_dict.get("site"): parts.append(f"🌐 {cont_dict['site']}")
                contact_str = "\n".join(parts) or "Нет"
            else:
                contact_str = "Нет"
            text = (
                f"🆕 <b>{record['name']}</b>\n"
                f"ИНН: {record.get('inn') or '—'}\n"
                f"Тип: {record.get('type') or 'не определён'}\n\n"
                f"<b>Описание (ОКВЭД):</b> {record.get('description') or 'нет'}\n\n"
                f"<b>Рутинные проблемы:</b>\n{problems_str}\n\n"
                f"<b>Контакты:</b>\n{contact_str}\n"
                f"<i>ID: {record['id']}</i>"
            )
        except Exception as e:
            print(f"Ошибка формирования сообщения: {e}")
            text = f"🆕 {record.get('name', 'Бизнес')}\n(ошибка анализа)"
        if text:
            try:
                await self.bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
                print(f"✅ Сообщение отправлено в канал: {record.get('name')}")
            except Exception as e:
                print(f"❌ Ошибка отправки в канал: {e}")
                import traceback
                traceback.print_exc()