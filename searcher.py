import asyncio
import random
import json
from database import prisma
from services.dadata import search_organizations
from services.datanewton import search_companies
from services.deepseek import analyze_business, analyze_raw_text, is_it_or_tech_company
from services.telegram_monitor import fetch_channel_messages
from services.marketplace import process_avito_items
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

                # --- 1. Dadata ---
                orgs_dadata = await search_organizations(keyword, count=3)
                for biz in orgs_dadata:
                    await self._process_official_business(biz)

                # --- 2. DataNewton ---
                orgs_newton = await search_companies(keyword, count=3)
                for biz in orgs_newton:
                    if not biz["inn"]:
                        continue
                    existing = await prisma.business.find_first(where={"inn": biz["inn"]})
                    if existing:
                        continue
                    await self._process_official_business(biz)

                # --- 3. Avito ---
                avito_queries = ["айфон", "мебель ручной работы", "вязаные вещи"]
                for q in avito_queries:
                    await process_avito_items(q, CHANNEL_ID, self.bot)

                # Пауза 15–30 минут
                await asyncio.sleep(random.randint(900, 1800))

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Ошибка в поисковом цикле: {e}")
                await asyncio.sleep(60)

    async def _process_official_business(self, biz: dict):
        # Фильтр IT и технологически развитых
        if await is_it_or_tech_company(biz["name"], biz.get("description", "")):
            return

        analysis = await analyze_business(biz["name"], biz.get("description", ""), "")
        # Дополнительно проверяем тип на случай ошибки
        if analysis.get("type") and "IT" in analysis["type"].upper():
            return

        record = await prisma.business.create(
            data={
                "name": biz["name"],
                "inn": biz.get("inn"),
                "type": analysis.get("type"),
                "registration": "registered",
                "description": biz.get("description"),
                "routineProblems": json.dumps(analysis.get("problems", [])),
                "contacts": json.dumps(biz.get("contacts", {})),
                "source": biz.get("source"),
                "isDevelopedTech": False,
            }
        )
        await self._post_to_channel(record)

    async def _post_to_channel(self, record):
        problems = record.routineProblems or "[]"
        contacts = record.contacts or "{}"
        source_url = record.sourceUrl
        try:
            prob_list = json.loads(problems)
            problems_str = "\n".join(f"• {p}" for p in prob_list) if prob_list else "Неизвестны"
            if record.source in ("dadata", "datanewton"):
                cont_dict = json.loads(contacts)
                parts = []
                if cont_dict.get("phone"): parts.append(f"📞 {cont_dict['phone']}")
                if cont_dict.get("email"): parts.append(f"📧 {cont_dict['email']}")
                if cont_dict.get("site"): parts.append(f"🌐 {cont_dict['site']}")
                contact_str = "\n".join(parts) or "Нет"
            else:
                contact_str = f"🔗 {source_url}" if source_url else "Нет"
        except:
            problems_str = problems
            contact_str = "Нет"

        text = (
            f"🆕 <b>{record.name}</b>\n"
            f"ИНН: {record.inn or '—'}\n"
            f"Тип: {record.type or 'не определён'}\n\n"
            f"<b>Описание:</b> {record.description or 'нет'}\n\n"
            f"<b>Рутинные проблемы:</b>\n{problems_str}\n\n"
            f"<b>Контакты:</b>\n{contact_str}\n"
            f"<i>ID: {record.id}</i>"
        )
        try:
            await self.bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки в канал: {e}")