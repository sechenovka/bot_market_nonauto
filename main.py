import asyncio
from bot_handlers import dp, bot
from database import init_db, close_db

async def main():
    await init_db()
    print("База данных готова")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())