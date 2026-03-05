from __future__ import annotations

from abc import ABC, abstractmethod

from video_bot.core.entities import DownloadedVideo


class IVideoDownloaderService(ABC):
    @abstractmethod
    async def download(self, url: str) -> DownloadedVideo:
        raise NotImplementedError

