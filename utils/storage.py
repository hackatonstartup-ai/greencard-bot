"""SQLite asosidagi FSM storage: bot qayta ishga tushsa ham anketa holati yo'qolmaydi."""
import json
from typing import Any, Dict, Optional

import aiosqlite
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

from config import DB_PATH


def _k(key: StorageKey) -> str:
    return f"{key.bot_id}:{key.chat_id}:{key.user_id}:{key.thread_id}:{key.business_connection_id}:{key.destiny}"


class SQLiteStorage(BaseStorage):
    def __init__(self, path=DB_PATH):
        self.path = str(path)
        self._ready = False

    async def _db(self) -> aiosqlite.Connection:
        db = await aiosqlite.connect(self.path)
        if not self._ready:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS fsm (key TEXT PRIMARY KEY, state TEXT, data TEXT NOT NULL DEFAULT '{}')"
            )
            await db.commit()
            self._ready = True
        return db

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        value = state.state if isinstance(state, State) else state
        db = await self._db()
        try:
            await db.execute(
                "INSERT INTO fsm (key, state) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET state = excluded.state",
                (_k(key), value),
            )
            await db.commit()
        finally:
            await db.close()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        db = await self._db()
        try:
            async with db.execute("SELECT state FROM fsm WHERE key = ?", (_k(key),)) as cur:
                row = await cur.fetchone()
            return row[0] if row else None
        finally:
            await db.close()

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        db = await self._db()
        try:
            await db.execute(
                "INSERT INTO fsm (key, data) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET data = excluded.data",
                (_k(key), json.dumps(data, ensure_ascii=False, default=str)),
            )
            await db.commit()
        finally:
            await db.close()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        db = await self._db()
        try:
            async with db.execute("SELECT data FROM fsm WHERE key = ?", (_k(key),)) as cur:
                row = await cur.fetchone()
            return json.loads(row[0]) if row and row[0] else {}
        finally:
            await db.close()

    async def close(self) -> None:
        return None
