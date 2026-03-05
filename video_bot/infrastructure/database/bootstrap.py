from __future__ import annotations

from video_bot.core.entities import UserRole
from video_bot.core.interfaces import IAccessRepository, IDownloadLogRepository
from video_bot.infrastructure.database.sqlite import SQLiteDatabase


async def initialize_database(database: SQLiteDatabase) -> None:
    async with database.connect() as connection:
        await connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS download_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                platform TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                file_size_bytes INTEGER,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            """
        )
        await connection.commit()


async def sync_superadmins(access_repository: IAccessRepository, superadmins: tuple[int, ...]) -> None:
    for telegram_id in superadmins:
        await access_repository.upsert_user(telegram_id=telegram_id, role=UserRole.SUPERADMIN)


async def trim_logs(log_repository: IDownloadLogRepository, limit: int) -> None:
    await log_repository.trim_to_limit(limit)
