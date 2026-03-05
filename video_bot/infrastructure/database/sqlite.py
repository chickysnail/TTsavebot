from __future__ import annotations

from pathlib import Path

import aiosqlite


class SQLiteDatabase:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    async def connect(self) -> aiosqlite.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = await aiosqlite.connect(self._db_path)
        connection.row_factory = aiosqlite.Row
        return connection

