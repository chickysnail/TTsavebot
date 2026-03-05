from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from video_bot.core.entities import User


class SuperadminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        current_user: User | None = data.get("current_user")
        if current_user is None or not current_user.is_superadmin:
            answer = getattr(event, "answer", None)
            if answer is not None and getattr(event, "data", None) is not None:
                await answer("Недостаточно прав.", show_alert=True)
            elif answer is not None:
                await answer("Команда доступна только супер-админам.")
            return None

        return await handler(event, data)
