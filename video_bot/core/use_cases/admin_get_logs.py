from __future__ import annotations

from video_bot.core.interfaces import DownloadLogRecord, IDownloadLogRepository


class AdminGetLogsUseCase:
    def __init__(self, log_repository: IDownloadLogRepository) -> None:
        self._log_repository = log_repository

    async def execute(self, limit: int = 10) -> list[DownloadLogRecord]:
        return await self._log_repository.get_recent(limit=limit)
