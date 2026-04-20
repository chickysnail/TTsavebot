from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite

from video_bot.core.entities import User, UserRole
from video_bot.core.interfaces import IAccessRepository
from video_bot.infrastructure.database.sqlite import SQLiteDatabase


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _parse_user(row: aiosqlite.Row) -> User:
    return User(
        telegram_id=row["telegram_id"],
        role=UserRole(row["role"]),
        is_active=bool(row["is_active"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class SQLiteAccessRepository(IAccessRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def get_user(self, telegram_id: int) -> User | None:
        async with self._database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT telegram_id, role, is_active, created_at, updated_at
                FROM users
                WHERE telegram_id = ?
                """,
                (telegram_id,),
            )
            row = await cursor.fetchone()
            return _parse_user(row) if row else None

    async def upsert_user(self, telegram_id: int, role: UserRole) -> User:
        now = _now_iso()
        async with self._database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO users (telegram_id, role, is_active, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    role = excluded.role,
                    is_active = 1,
                    updated_at = excluded.updated_at
                """,
                (telegram_id, role.value, now, now),
            )
            await connection.commit()
        user = await self.get_user(telegram_id)
        if user is None:
            raise RuntimeError("User upsert failed")
        return user

    async def deactivate_user(self, telegram_id: int) -> None:
        async with self._database.connect() as connection:
            await connection.execute(
                """
                UPDATE users
                SET is_active = 0, updated_at = ?
                WHERE telegram_id = ?
                """,
                (_now_iso(), telegram_id),
            )
            await connection.commit()

    async def list_active_users(self) -> list[User]:
        async with self._database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT telegram_id, role, is_active, created_at, updated_at
                FROM users
                WHERE is_active = 1
                ORDER BY CASE WHEN role = 'superadmin' THEN 0 ELSE 1 END, telegram_id ASC
                """
            )
            rows = await cursor.fetchall()
            return [_parse_user(row) for row in rows]

    async def list_inactive_users(self) -> list[User]:
        async with self._database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT telegram_id, role, is_active, created_at, updated_at
                FROM users
                WHERE is_active = 0
                ORDER BY telegram_id ASC
                """
            )
            rows = await cursor.fetchall()
            return [_parse_user(row) for row in rows]
