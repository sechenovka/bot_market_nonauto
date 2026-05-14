import sqlite3
import asyncio
from config import DATABASE_URL

DB_PATH = DATABASE_URL.replace("file:", "")  # убираем префикс file:

# Глобальное синхронное соединение (будем использовать через asyncio.to_thread)
conn: sqlite3.Connection = None

def _init_db_sync():
    """Синхронная инициализация БД (вызывается в отдельном потоке)."""
    global conn
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS business (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            inn TEXT,
            type TEXT,
            registration TEXT DEFAULT 'registered',
            description TEXT,
            routineProblems TEXT,
            contacts TEXT,
            source TEXT,
            sourceUrl TEXT,
            isDevelopedTech INTEGER DEFAULT 0,
            isPosted INTEGER DEFAULT 0,
            createdAt TEXT DEFAULT (datetime('now')),
            updatedAt TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_name_type ON business(name, type)
    """)
    conn.commit()

async def init_db():
    """Асинхронная инициализация БД при запуске."""
    await asyncio.to_thread(_init_db_sync)

async def close_db():
    """Закрытие соединения (опционально)."""
    global conn
    if conn:
        await asyncio.to_thread(conn.close)

async def execute_db(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Выполняет SQL-запрос в отдельном потоке и возвращает курсор."""
    def _execute():
        return conn.execute(sql, params)
    return await asyncio.to_thread(_execute)

async def fetch_one(sql: str, params: tuple = ()):
    """Получает одну строку из БД."""
    cursor = await execute_db(sql, params)
    row = cursor.fetchone()
    return row

async def commit_db():
    """Коммит изменений."""
    await asyncio.to_thread(conn.commit)