from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from config import BOT_TOKEN, CHANNEL_ID, PROXY_URL
from searcher import SearchController

search_ctrl = SearchController()
dp = Dispatcher()

# Создаём сессию с прокси, если он задан
if PROXY_URL:
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
else:
    bot = Bot(token=BOT_TOKEN)

@dp.message(Command("start_search"))
async def start_search_cmd(message: types.Message):
    if not search_ctrl.is_running:
        await search_ctrl.start(bot)
        await message.answer("🔍 Поиск бизнесов запущен. Результаты будут публиковаться в канале.")
    else:
        await message.answer("Уже работает.")

@dp.message(Command("stop_search"))
async def stop_search_cmd(message: types.Message):
    if search_ctrl.is_running:
        await search_ctrl.stop()
        await message.answer("⏹ Поиск остановлен.")
    else:
        await message.answer("Поиск не активен.")

@dp.message(Command("test_post"))
async def test_post(message: types.Message):
    try:
        await bot.send_message(CHANNEL_ID, "🧪 Тестовое сообщение от бота")
        await message.answer("✅ Сообщение в канал отправлено успешно!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
        # Выведем полный трейсбек в консоль
        import traceback
        traceback.print_exc()