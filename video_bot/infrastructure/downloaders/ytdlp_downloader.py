from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from video_bot.core.entities import DownloadedVideo, detect_platform
from video_bot.core.errors import DownloadTimeoutError, DownloaderError, PrivateContentError, ValidationError
from video_bot.core.interfaces import IVideoDownloaderService


class YtDlpDownloader(IVideoDownloaderService):
    def __init__(
        self,
        ytdlp_bin: str,
        downloads_dir: Path,
        timeout_seconds: int,
        cookies_path: Path | None = None,
    ) -> None:
        self._ytdlp_bin = ytdlp_bin
        self._downloads_dir = downloads_dir
        self._timeout_seconds = timeout_seconds
        self._cookies_path = cookies_path

    async def download(self, url: str) -> DownloadedVideo:
        request_dir = self._downloads_dir / str(uuid4())
        request_dir.mkdir(parents=True, exist_ok=True)
        output_template = request_dir / "%(id)s.%(ext)s"

        command = [
            self._ytdlp_bin,
            "--no-playlist",
            "--restrict-filenames",
            "--merge-output-format",
            "mp4",
            "--output",
            str(output_template),
            "--print",
            "title",
            "--print",
            "id",
            url,
        ]

        if self._cookies_path and self._cookies_path.exists():
            command[1:1] = ["--cookies", str(self._cookies_path)]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self._timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise DownloadTimeoutError("Время ожидания скачивания истекло.") from exc

        if process.returncode != 0:
            message = stderr.decode("utf-8", errors="ignore").strip() or stdout.decode("utf-8", errors="ignore").strip()
            lowered = message.lower()
            if "login required" in lowered or "private" in lowered:
                raise PrivateContentError("Видео недоступно без авторизации или аккаунт приватный.")
            if "unsupported url" in lowered or "invalid url" in lowered:
                raise ValidationError("Ссылка не поддерживается или повреждена.")
            raise DownloaderError(message or "Не удалось скачать видео.")

        output_lines = [line.strip() for line in stdout.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        title = output_lines[0] if output_lines else None
        extractor_id = output_lines[1] if len(output_lines) > 1 else None

        video_files = [path for path in request_dir.iterdir() if path.is_file() and not path.name.endswith((".part", ".ytdl"))]
        if not video_files:
            raise DownloaderError("Файл не был сохранен на диск.")

        file_path = max(video_files, key=lambda candidate: candidate.stat().st_mtime)
        return DownloadedVideo(
            source_url=url,
            platform=detect_platform(url),
            file_path=file_path,
            file_size_bytes=file_path.stat().st_size,
            title=title,
            extractor_id=extractor_id,
        )

