from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from video_bot.core.entities import DownloadStatus, PlatformType


@dataclass(slots=True, frozen=True)
class DownloadLogRecord:
    id: int
    telegram_id: int
    url: str
    platform: PlatformType | None
    status: DownloadStatus
    error_message: str | None
    file_size_bytes: int | None
    created_at: datetime
    completed_at: datetime | None


@dataclass(slots=True, frozen=True)
class DownloadStats:
    total: int
    success: int
    failed: int
    rejected: int
    oversize: int
    tiktok: int
    instagram: int


class IDownloadLogRepository(ABC):
    @abstractmethod
    async def create_log(self, telegram_id: int, url: str, platform: PlatformType | None) -> int:
        raise NotImplementedError

    @abstractmethod
    async def mark_success(self, log_id: int, file_size_bytes: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_failure(self, log_id: int, error_message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_rejected(self, log_id: int, error_message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_oversize(self, log_id: int, file_size_bytes: int, error_message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_recent(self, limit: int) -> list[DownloadLogRecord]:
        raise NotImplementedError

    @abstractmethod
    async def get_stats(self) -> DownloadStats:
        raise NotImplementedError

    @abstractmethod
    async def trim_to_limit(self, limit: int) -> None:
        raise NotImplementedError

