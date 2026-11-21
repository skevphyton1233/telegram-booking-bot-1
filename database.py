import logging
from datetime import datetime

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = "requests.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT,
    service TEXT NOT NULL,
    client_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    datetime_comment TEXT,
    created_at TEXT NOT NULL
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()
    logger.info("База данных готова: %s", DB_PATH)


async def save_request(
    user_id: int,
    username: str | None,
    full_name: str,
    service: str,
    client_name: str,
    phone: str,
    datetime_comment: str,
) -> int:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO requests
                (user_id, username, full_name, service, client_name, phone, datetime_comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, full_name, service, client_name, phone, datetime_comment, created_at),
        )
        await db.commit()
        return cursor.lastrowid


async def get_last_requests(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM requests ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return await cursor.fetchall()
