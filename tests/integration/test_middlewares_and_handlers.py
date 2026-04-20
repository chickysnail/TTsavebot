import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from aiogram.types import TelegramObject

from video_bot.core.entities import DownloadedVideo, PlatformType, User, UserRole
from video_bot.core.errors import FileTooLargeError
from video_bot.core.interfaces import DownloadLogRecord, DownloadStats, IDownloadLogRepository
from video_bot.containers import AppContainer
from video_bot.presentation.handlers.admin import panel_stats_handler
from video_bot.presentation.handlers.downloads import download_handler
from video_bot.presentation.middlewares.auth import AuthMiddleware


@dataclass
class FakeFromUser:
    id: int


@dataclass
class FakeMessage:
    from_user: FakeFromUser
    text: str | None = None
    caption: str | None = None
    answers: list[str] = field(default_factory=list)
    videos: list[tuple[object, str | None]] = field(default_factory=list)
    edited_texts: list[str] = field(default_factory=list)
    deleted: bool = False

    async def answer(self, text: str, **_: object) -> "FakeMessage":
        self.answers.append(text)
        return self

    async def answer_video(self, video: object, caption: str | None = None, **_: object) -> None:
        self.videos.append((video, caption))

    async def edit_text(self, text: str, **_: object) -> None:
        self.edited_texts.append(text)

    async def delete(self) -> None:
        self.deleted = True


@dataclass
class FakeLogRepository(IDownloadLogRepository):
    created: list[tuple[int, str, PlatformType | None]] = field(default_factory=list)
    rejected: list[tuple[int, str]] = field(default_factory=list)
    trimmed: list[int] = field(default_factory=list)

    async def create_log(self, telegram_id: int, url: str, platform: PlatformType | None) -> int:
        self.created.append((telegram_id, url, platform))
        return 1

    async def mark_success(self, log_id: int, file_size_bytes: int) -> None:
        return None

    async def mark_failure(self, log_id: int, error_message: str) -> None:
        return None

    async def mark_rejected(self, log_id: int, error_message: str) -> None:
        self.rejected.append((log_id, error_message))

    async def mark_oversize(self, log_id: int, file_size_bytes: int, error_message: str) -> None:
        return None

    async def get_recent(self, limit: int) -> list[DownloadLogRecord]:
        return []

    async def get_stats(self) -> DownloadStats:
        return DownloadStats(total=0, success=0, failed=0, rejected=0, oversize=0, tiktok=0, instagram=0)

    async def trim_to_limit(self, limit: int) -> None:
        self.trimmed.append(limit)


@pytest.mark.asyncio
async def test_auth_middleware_denies_unknown_user() -> None:
    event = FakeMessage(from_user=FakeFromUser(id=999), text="/start")
    log_repository = FakeLogRepository()
    container = SimpleNamespace(
        check_access_use_case=SimpleNamespace(execute=None),
        download_log_repository=log_repository,
        settings=SimpleNamespace(log_retention_limit=10),
    )
    middleware = AuthMiddleware(cast(AppContainer, container))
    handler_called = False

    async def fake_execute(_: int):
        return None

    container.check_access_use_case.execute = fake_execute

    async def handler(_event: object, _data: dict[str, object]) -> None:
        nonlocal handler_called
        handler_called = True

    await middleware(handler, cast(TelegramObject, event), {})

    assert handler_called is False
    assert event.answers == ["Доступ запрещён."]
    assert log_repository.rejected == [(1, "Пользователь в blacklist.")]


@pytest.mark.asyncio
async def test_download_handler_sends_video_and_cleans_up(tmp_path: Path) -> None:
    user = User(
        telegram_id=1,
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"video")
    message = FakeMessage(from_user=FakeFromUser(id=1), text="https://www.tiktok.com/@creator/video/1")

    class DownloadUseCase:
        async def execute(self, url: str, telegram_id: int):
            return 1, DownloadedVideo(url, PlatformType.TIKTOK, path, path.stat().st_size, "clip", "1")

    class FileStorage:
        def __init__(self) -> None:
            self.removed: list[Path] = []

        async def remove_file(self, file_path: Path) -> None:
            self.removed.append(file_path)

    file_storage = FileStorage()
    container = SimpleNamespace(
        download_video_use_case=DownloadUseCase(),
        file_storage=file_storage,
        get_user_lock=lambda telegram_id: asyncio.Lock(),
    )

    await download_handler(message=message, current_user=user, app_container=container)

    assert message.videos
    assert file_storage.removed == [path]


@pytest.mark.asyncio
async def test_download_handler_maps_error_to_progress_message() -> None:
    user = User(
        telegram_id=1,
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    message = FakeMessage(from_user=FakeFromUser(id=1), text="https://www.tiktok.com/@creator/video/1")

    class DownloadUseCase:
        async def execute(self, url: str, telegram_id: int):
            raise FileTooLargeError("too large")

    class FileStorage:
        async def remove_file(self, file_path: Path) -> None:
            return None

    container = SimpleNamespace(
        download_video_use_case=DownloadUseCase(),
        file_storage=FileStorage(),
        get_user_lock=lambda telegram_id: asyncio.Lock(),
    )

    await download_handler(message=message, current_user=user, app_container=container)

    assert message.edited_texts == ["Файл слишком большой для отправки через Telegram."]


@pytest.mark.asyncio
async def test_panel_stats_handler_uses_stats_use_case() -> None:
    edited: list[str] = []
    answered: list[bool] = []

    async def edit_text(text: str, **_: object) -> None:
        edited.append(text)

    async def answer(**_: object) -> None:
        answered.append(True)

    callback = SimpleNamespace(
        data="panel:stats",
        message=SimpleNamespace(edit_text=edit_text),
        answer=answer,
    )
    stats = DownloadStats(total=5, success=4, failed=1, rejected=0, oversize=0, tiktok=3, instagram=2)

    async def execute():
        return stats

    container = SimpleNamespace(admin_get_stats_use_case=SimpleNamespace(execute=execute))

    await panel_stats_handler(callback=callback, app_container=container)

    assert edited
    assert answered == [True]
