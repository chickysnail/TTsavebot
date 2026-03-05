from __future__ import annotations

import asyncio
import importlib.util
import os
import shlex
import shutil
import sys
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

    def _resolve_command(self) -> list[str]:
        configured = self._ytdlp_bin.strip()
        if configured:
            parts = shlex.split(configured, posix=os.name != "nt")
            if parts and shutil.which(parts[0]):
                return parts

        if importlib.util.find_spec("yt_dlp") is not None:
            return [sys.executable, "-m", "yt_dlp"]

        if configured:
            raise DownloaderError(
                f"Downloader '{configured}' не найден. Установите yt-dlp или укажите корректный YTDLP_BIN."
            )

        raise DownloaderError("yt-dlp не установлен. Выполните `uv sync` или укажите путь в YTDLP_BIN.")

    def _build_command(self, url: str, output_template: Path) -> list[str]:
        command = [
            *self._resolve_command(),
            "--no-simulate",
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

        return command

    async def download(self, url: str) -> DownloadedVideo:
        request_dir = self._downloads_dir / str(uuid4())
        request_dir.mkdir(parents=True, exist_ok=True)
        output_template = request_dir / "%(id)s.%(ext)s"
        command = self._build_command(url, output_template)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self._timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise DownloadTimeoutError("Время ожидания скачивания истекло.") from exc
        except FileNotFoundError as exc:
            raise DownloaderError("yt-dlp не найден. Выполните `uv sync` или укажите корректный YTDLP_BIN.") from exc

        if process.returncode != 0:
            message = stderr.decode("utf-8", errors="ignore").strip() or stdout.decode("utf-8", errors="ignore").strip()
            lowered = message.lower()
            if "no module named yt_dlp" in lowered:
                raise DownloaderError("yt-dlp не установлен в окружении. Выполните `uv sync`.")
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
