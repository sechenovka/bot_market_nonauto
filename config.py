import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DADATA_API_KEY = os.getenv("DADATA_API_KEY")
DADATA_SECRET_KEY = os.getenv("DADATA_SECRET_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

DATANEWTON_API_KEY = os.getenv("DATANEWTON_API_KEY")

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

DATABASE_URL = os.getenv("DATABASE_URL", "file:./market.db")