import sqlite3
import asyncio
from config import DATABASE_URL

DB_PATH = DATABASE_URL.replace("file:", "")

def _init_db_sync():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
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
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_name_type ON business(name, type)
    """)
    conn.commit()
    conn.close()

async def init_db():
    await asyncio.to_thread(_init_db_sync)

async def execute_db(sql: str, params: tuple = ()):
    def _execute():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(sql, params)
        conn.commit()
        conn.close()
        return cursor
    return await asyncio.to_thread(_execute)

async def fetch_one(sql: str, params: tuple = ()):
    def _fetch():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row
    return await asyncio.to_thread(_fetch)