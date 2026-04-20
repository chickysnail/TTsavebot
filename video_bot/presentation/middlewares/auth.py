from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from video_bot.containers import AppContainer


class AuthMiddleware(BaseMiddleware):
    def __init__(self, container: AppContainer) -> None:
        self._container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_id = getattr(getattr(event, "from_user", None), "id", None)
        if telegram_id is None:
            return await handler(event, data)

        user = await self._container.check_access_use_case.execute(telegram_id)
        if user is None:
            await self._log_rejection(telegram_id, event)
            await self._deny(event)
            return None

        data["current_user"] = user
        return await handler(event, data)

    async def _log_rejection(self, telegram_id: int, event: TelegramObject) -> None:
        payload = "<empty>"
        platform = None
        if getattr(event, "text", None) or getattr(event, "caption", None):
            payload = getattr(event, "text", None) or getattr(event, "caption", None) or "<empty>"
        elif getattr(event, "data", None):
            payload = f"callback:{getattr(event, 'data')}"

        log_id = await self._container.download_log_repository.create_log(
            telegram_id=telegram_id,
            url=payload,
            platform=platform,
        )
        await self._container.download_log_repository.mark_rejected(log_id, "Пользователь в blacklist.")
        await self._container.download_log_repository.trim_to_limit(self._container.settings.log_retention_limit)

    @staticmethod
    async def _deny(event: TelegramObject) -> None:
        answer = getattr(event, "answer", None)
        if answer is None:
            return

        if getattr(event, "data", None) is not None:
            await answer("Доступ запрещён.", show_alert=True)
            return

        await answer("Доступ запрещён.")
