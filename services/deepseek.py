import json
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

async def is_it_or_tech_company(name: str, description: str) -> bool:
    prompt = (
        f"Ты эксперт по классификации бизнеса в России. Определи, относится ли следующая компания "
        f"к IT-сфере (разработка ПО, веб-студия, системная интеграция, интернет-провайдер, "
        f"производство компьютеров, телекоммуникации и т.п.) ИЛИ является ли она сильно "
        f"технологически развитой в своей отрасли (имеет собственные CRM, мобильные приложения, "
        f"высокотехнологичное оборудование, автоматизированные линии, интернет-магазин с "
        f"интегрированной ERP-системой и т.д.).\n\n"
        f"Название: {name}\n"
        f"Описание / ОКВЭД: {description}\n\n"
        f"Ответь строго одним словом: true или false."
    )
    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == "true"
    except Exception as e:
        print(f"IT/tech check error: {e}")
        return False

async def analyze_business(name: str, description: str, okved: str) -> dict:
    prompt = (
        f"Ты эксперт по малому бизнесу в России. Проанализируй следующую компанию:\n"
        f"Название: {name}\n"
        f"Описание/ОКВЭД: {description} {okved}\n\n"
        "1. Определи сферу деятельности (например, детский сад, продуктовый магазин, интернет-магазин одежды, "
        "автосервис, аптека, парикмахерская и т.д.).\n"
        "2. Перечисли 3-5 типичных РУТИННЫХ проблем, с которыми сталкивается такой бизнес (например, "
        "низкая посещаемость сайта, кассовые разрывы, сложности с персоналом, документооборот, учёт товаров, "
        "логистика, нехватка клиентов).\n\n"
        "Ответ дай строго в JSON формате:\n"
        '{"type": "...", "problems": ["...", "..."]}'
    )
    return await _request(prompt)

async def analyze_raw_text(text: str) -> dict:
    prompt = (
        "Ты анализируешь русскоязычный пост/объявление. Если это похоже на малый бизнес или частного продавца, "
        "который регулярно что‑то продаёт/предлагает услуги, определи:\n"
        "1. Тип деятельности (одна фраза).\n"
        "2. 2-3 типичные рутинные проблемы, с которыми сталкивается такой продавец.\n"
        "Если это не бизнес, ответь type='none'.\n\n"
        f"Текст: \"{text}\"\n\n"
        "Ответ строго JSON: {\"type\": \"...\", \"problems\": [...]}"
    )
    return await _request(prompt)

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
    return {"type": None, "problems": []}