from __future__ import annotations

from video_bot.core.entities import User, UserRole
from video_bot.core.interfaces import IAccessRepository


class AdminAllowUserUseCase:
    def __init__(self, access_repository: IAccessRepository) -> None:
        self._access_repository = access_repository

    async def execute(self, telegram_id: int) -> User:
        return await self._access_repository.upsert_user(telegram_id=telegram_id, role=UserRole.USER)

