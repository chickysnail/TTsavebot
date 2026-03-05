from __future__ import annotations

from video_bot.core.interfaces import DownloadStats, IDownloadLogRepository


class AdminGetStatsUseCase:
    def __init__(self, log_repository: IDownloadLogRepository) -> None:
        self._log_repository = log_repository

    async def execute(self) -> DownloadStats:
        return await self._log_repository.get_stats()

