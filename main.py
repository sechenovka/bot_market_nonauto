import asyncio
import bot_handlers
import database

async def main():
    await database.init_db()
    print("База данных готова")
    try:
        await bot_handlers.dp.start_polling(bot_handlers.bot)
    finally:
        await database.close_db()

if __name__ == "__main__":
    asyncio.run(main())