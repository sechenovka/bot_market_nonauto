import json
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

async def analyze_business(name: str, description: str, okved: str) -> dict:
    prompt = (
        f"Ты эксперт по малому бизнесу в России. Проанализируй следующее ИП:\n"
        f"Название: {name}\n"
        f"Описание/ОКВЭД: {description} {okved}\n\n"
        "1. Определи сферу деятельности (например, детский сад, продуктовый магазин, интернет-магазин одежды).\n"
        "2. Является ли бизнес сильно развитым технологически? "
        "(Признаки: есть сайт с веб-приложением, CRM, мобильное приложение, высокотехнологичное производство). "
        "Ответь true/false.\n"
        "3. Перечисли 3-5 типичных РУТИННЫХ проблем, с которыми сталкивается такой бизнес (например, "
        "низкая посещаемость сайта, кассовые разрывы, сложности с персоналом, документооборот, "
        "учёт товаров, логистика).\n\n"
        "Ответ дай строго в JSON формате:\n"
        '{"type": "...", "isDevelopedTech": false, "problems": ["...", "..."]}'
    )
    return await _request(prompt)

async def analyze_raw_text(text: str) -> dict:
    prompt = (
        "Ты анализируешь русскоязычный пост/объявление. "
        "Если это похоже на малый бизнес или частного продавца, который регулярно что‑то продаёт/предлагает услуги, определи:\n"
        "1. Тип деятельности (одна фраза).\n"
        "2. Является ли он технологически продвинутым? (true/false) — если упоминаются сложные ИТ‑системы.\n"
        "3. 2-3 типичные рутинные проблемы, с которыми сталкивается такой продавец.\n"
        "Если это не бизнес, ответь type='none'.\n\n"
        f"Текст: \"{text}\"\n\n"
        "Ответ строго JSON: {\"type\": \"...\", \"isDevelopedTech\": false, \"problems\": [...]}"
    )
    return await _request(prompt)

async def is_it_or_tech_company(name: str, description: str) -> bool:
    prompt = (
        f"Определи, является ли компания IT-компанией или сильно технологически развитой.\n"
        f"Название: {name}\n"
        f"Описание: {description}\n"
        "Ответь строго 'yes' или 'no'."
    )
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role":"user","content":prompt}],
            temperature=0.0,
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"
    except:
        return False

async def _request(prompt: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role":"user","content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        content = response.choices[0].message.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
    except Exception as e:
        print(f"DeepSeek error: {e}")
    return {"type": None, "isDevelopedTech": False, "problems": []}