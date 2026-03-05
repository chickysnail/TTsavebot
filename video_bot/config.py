from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _csv_to_ints(raw_value: str) -> tuple[int, ...]:
    values = []
    for chunk in raw_value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(int(chunk))
    return tuple(values)


@dataclass(slots=True, frozen=True)
class Settings:
    bot_token: str
    superadmins: tuple[int, ...]
    db_path: Path = Path("data/bot.sqlite3")
    downloads_dir: Path = Path("downloads")
    ytdlp_bin: str = "yt-dlp"
    ytdlp_timeout_seconds: int = 60
    max_file_size_mb: int = 50
    instagram_cookies_path: Path | None = None
    log_retention_limit: int = 10_000
    stale_file_max_age_hours: int = 24

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    raw_superadmins = os.getenv("SUPERADMINS", "")
    if not raw_superadmins.strip():
        raise ValueError("SUPERADMINS must contain at least one Telegram ID")

    cookies = os.getenv("INSTAGRAM_COOKIES_PATH", "").strip()

    return Settings(
        bot_token=bot_token,
        superadmins=_csv_to_ints(raw_superadmins),
        db_path=Path(os.getenv("DB_PATH", "data/bot.sqlite3")),
        downloads_dir=Path(os.getenv("DOWNLOADS_DIR", "downloads")),
        ytdlp_bin=os.getenv("YTDLP_BIN", "yt-dlp").strip() or "yt-dlp",
        ytdlp_timeout_seconds=int(os.getenv("YTDLP_TIMEOUT_SECONDS", "60")),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        instagram_cookies_path=Path(cookies) if cookies else None,
        log_retention_limit=int(os.getenv("LOG_RETENTION_LIMIT", "10000")),
        stale_file_max_age_hours=int(os.getenv("STALE_FILE_MAX_AGE_HOURS", "24")),
    )

