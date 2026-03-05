from __future__ import annotations

from datetime import datetime, timezone

from video_bot.core.entities import DownloadStatus, PlatformType
from video_bot.core.interfaces import DownloadLogRecord, DownloadStats, IDownloadLogRepository
from video_bot.infrastructure.database.sqlite import SQLiteDatabase


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _parse_record(row: dict) -> DownloadLogRecord:
    platform = PlatformType(row["platform"]) if row["platform"] else None
    return DownloadLogRecord(
        id=row["id"],
        telegram_id=row["telegram_id"],
        url=row["url"],
        platform=platform,
        status=DownloadStatus(row["status"]),
        error_message=row["error_message"],
        file_size_bytes=row["file_size_bytes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
    )


class SQLiteDownloadLogRepository(IDownloadLogRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    async def create_log(self, telegram_id: int, url: str, platform: PlatformType | None) -> int:
        async with await self._database.connect() as connection:
            cursor = await connection.execute(
                """
                INSERT INTO download_logs (telegram_id, url, platform, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (telegram_id, url, platform.value if platform else None, DownloadStatus.PENDING.value, _now_iso()),
            )
            await connection.commit()
            return int(cursor.lastrowid)

    async def mark_success(self, log_id: int, file_size_bytes: int) -> None:
        await self._mark(log_id, DownloadStatus.SUCCESS, file_size_bytes=file_size_bytes)

    async def mark_failure(self, log_id: int, error_message: str) -> None:
        await self._mark(log_id, DownloadStatus.FAILED, error_message=error_message)

    async def mark_rejected(self, log_id: int, error_message: str) -> None:
        await self._mark(log_id, DownloadStatus.REJECTED, error_message=error_message)

    async def mark_oversize(self, log_id: int, file_size_bytes: int, error_message: str) -> None:
        await self._mark(log_id, DownloadStatus.OVERSIZE, file_size_bytes=file_size_bytes, error_message=error_message)

    async def get_recent(self, limit: int) -> list[DownloadLogRecord]:
        async with await self._database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT id, telegram_id, url, platform, status, error_message, file_size_bytes, created_at, completed_at
                FROM download_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            return [_parse_record(row) for row in rows]

    async def get_stats(self) -> DownloadStats:
        async with await self._database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected,
                    SUM(CASE WHEN status = 'oversize' THEN 1 ELSE 0 END) AS oversize,
                    SUM(CASE WHEN platform = 'tiktok' THEN 1 ELSE 0 END) AS tiktok,
                    SUM(CASE WHEN platform = 'instagram' THEN 1 ELSE 0 END) AS instagram
                FROM download_logs
                """
            )
            row = await cursor.fetchone()
            return DownloadStats(
                total=row["total"] or 0,
                success=row["success"] or 0,
                failed=row["failed"] or 0,
                rejected=row["rejected"] or 0,
                oversize=row["oversize"] or 0,
                tiktok=row["tiktok"] or 0,
                instagram=row["instagram"] or 0,
            )

    async def trim_to_limit(self, limit: int) -> None:
        async with await self._database.connect() as connection:
            await connection.execute(
                """
                DELETE FROM download_logs
                WHERE id NOT IN (
                    SELECT id
                    FROM download_logs
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (limit,),
            )
            await connection.commit()

    async def _mark(
        self,
        log_id: int,
        status: DownloadStatus,
        *,
        file_size_bytes: int | None = None,
        error_message: str | None = None,
    ) -> None:
        async with await self._database.connect() as connection:
            await connection.execute(
                """
                UPDATE download_logs
                SET status = ?, error_message = ?, file_size_bytes = ?, completed_at = ?
                WHERE id = ?
                """,
                (status.value, error_message, file_size_bytes, _now_iso(), log_id),
            )
            await connection.commit()

