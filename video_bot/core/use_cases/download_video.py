from __future__ import annotations

from video_bot.core.entities import DownloadedVideo, VideoRequest
from video_bot.core.errors import FileTooLargeError
from video_bot.core.interfaces import IDownloadLogRepository, IFileStorage, IVideoDownloaderService


class DownloadVideoUseCase:
    def __init__(
        self,
        downloader: IVideoDownloaderService,
        file_storage: IFileStorage,
        log_repository: IDownloadLogRepository,
        max_file_size_bytes: int,
        log_retention_limit: int,
    ) -> None:
        self._downloader = downloader
        self._file_storage = file_storage
        self._log_repository = log_repository
        self._max_file_size_bytes = max_file_size_bytes
        self._log_retention_limit = log_retention_limit

    async def execute(self, url: str, telegram_id: int) -> tuple[int, DownloadedVideo]:
        request = VideoRequest.from_url(telegram_id=telegram_id, url=url)
        log_id = await self._log_repository.create_log(telegram_id=telegram_id, url=request.url, platform=request.platform)

        try:
            video = await self._downloader.download(request.url)
            file_size = await self._file_storage.file_size(video.file_path)
            if file_size > self._max_file_size_bytes:
                await self._log_repository.mark_oversize(
                    log_id,
                    file_size_bytes=file_size,
                    error_message="Размер файла превышает лимит Telegram Bot API.",
                )
                raise FileTooLargeError("Видео превышает лимит Telegram и не может быть отправлено.")

            await self._log_repository.mark_success(log_id, file_size_bytes=file_size)
            await self._log_repository.trim_to_limit(self._log_retention_limit)
            return log_id, DownloadedVideo(
                source_url=video.source_url,
                platform=video.platform,
                file_path=video.file_path,
                file_size_bytes=file_size,
                title=video.title,
                extractor_id=video.extractor_id,
            )
        except Exception as exc:
            if not isinstance(exc, FileTooLargeError):
                await self._log_repository.mark_failure(log_id, error_message=str(exc))
            await self._log_repository.trim_to_limit(self._log_retention_limit)
            raise

