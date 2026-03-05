from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from video_bot.core.entities.enums import PlatformType
from video_bot.core.errors import ValidationError

_TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "vm.tiktok.com"}
_INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}


def detect_platform(raw_url: str) -> PlatformType:
    url = raw_url.strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    if parsed.scheme not in {"http", "https"} or not host:
        raise ValidationError("Отправьте корректную ссылку на TikTok или Instagram.")

    if host in _TIKTOK_HOSTS:
        return PlatformType.TIKTOK

    if host in _INSTAGRAM_HOSTS and (path.startswith("/reel/") or path.startswith("/p/")):
        return PlatformType.INSTAGRAM

    raise ValidationError("Поддерживаются только TikTok и Instagram Reels/Post ссылки.")


@dataclass(slots=True, frozen=True)
class VideoRequest:
    telegram_id: int
    url: str
    platform: PlatformType
    requested_at: datetime

    @classmethod
    def from_url(cls, telegram_id: int, url: str) -> "VideoRequest":
        return cls(
            telegram_id=telegram_id,
            url=url.strip(),
            platform=detect_platform(url),
            requested_at=datetime.utcnow(),
        )

