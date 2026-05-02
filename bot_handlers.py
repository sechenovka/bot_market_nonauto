from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, CHANNEL_ID
from searcher import SearchController

search_ctrl = SearchController()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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