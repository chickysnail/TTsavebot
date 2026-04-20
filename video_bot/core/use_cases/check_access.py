from __future__ import annotations

from video_bot.core.entities import User, UserRole
from video_bot.core.interfaces import IAccessRepository


class CheckAccessUseCase:
    def __init__(self, access_repository: IAccessRepository) -> None:
        self._access_repository = access_repository

    async def execute(self, telegram_id: int) -> User | None:
        user = await self._access_repository.get_user(telegram_id)
        if user is None:
            return await self._access_repository.upsert_user(telegram_id=telegram_id, role=UserRole.USER)
        if not user.is_active:
            return None
        return user

