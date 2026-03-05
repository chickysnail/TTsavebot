from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from video_bot.core.interfaces import IFileStorage


class LocalFileStorage(IFileStorage):
    def __init__(self, base_dir: Path, stale_file_max_age_hours: int) -> None:
        self._base_dir = base_dir
        self._stale_delta = timedelta(hours=stale_file_max_age_hours)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    async def ensure_dirs(self) -> None:
        await asyncio.to_thread(self._base_dir.mkdir, parents=True, exist_ok=True)

    async def remove_file(self, path: Path) -> None:
        def _remove() -> None:
            if path.exists():
                path.unlink()
            parent = path.parent
            if parent != self._base_dir and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()

        await asyncio.to_thread(_remove)

    async def cleanup_stale_files(self) -> int:
        cutoff = datetime.now(tz=timezone.utc) - self._stale_delta

        def _cleanup() -> int:
            removed = 0
            if not self._base_dir.exists():
                return removed

            for item in self._base_dir.rglob("*"):
                if not item.is_file():
                    continue
                modified = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                if modified < cutoff:
                    item.unlink(missing_ok=True)
                    removed += 1

            for directory in sorted((path for path in self._base_dir.rglob("*") if path.is_dir()), reverse=True):
                if directory.exists() and not any(directory.iterdir()):
                    directory.rmdir()

            return removed

        return await asyncio.to_thread(_cleanup)

    async def file_size(self, path: Path) -> int:
        return await asyncio.to_thread(lambda: path.stat().st_size)
