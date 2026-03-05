from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from video_bot.core.entities.enums import PlatformType


@dataclass(slots=True, frozen=True)
class DownloadedVideo:
    source_url: str
    platform: PlatformType
    file_path: Path
    file_size_bytes: int
    title: str | None
    extractor_id: str | None

