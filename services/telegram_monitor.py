from telethon import TelegramClient
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH

async def fetch_channel_messages(channel_username: str, limit: int = 10) -> list[dict]:
    client = TelegramClient('session_monitor', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    try:
        await client.start()
        messages = []
        async for message in client.iter_messages(channel_username, limit=limit):
            if message.text:
                messages.append({
                    'id': message.id,
                    'text': message.text,
                    'link': f"https://t.me/{channel_username}/{message.id}"
                })
        return messages
    except Exception as e:
        print(f"Telegram monitor error: {e}")
        return []
    finally:
        await client.disconnect()