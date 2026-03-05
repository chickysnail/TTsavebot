from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IFileStorage(ABC):
    @abstractmethod
    async def ensure_dirs(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_file(self, path: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    async def cleanup_stale_files(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def file_size(self, path: Path) -> int:
        raise NotImplementedError

