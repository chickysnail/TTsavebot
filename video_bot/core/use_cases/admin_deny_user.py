from __future__ import annotations

from video_bot.core.errors import ValidationError
from video_bot.core.interfaces import IAccessRepository


class AdminDenyUserUseCase:
    def __init__(self, access_repository: IAccessRepository) -> None:
        self._access_repository = access_repository

    async def execute(self, telegram_id: int) -> None:
        user = await self._access_repository.get_user(telegram_id)
        if user and user.is_superadmin:
            raise ValidationError("Супер-админа можно управлять только через SUPERADMINS в .env.")
        await self._access_repository.deactivate_user(telegram_id)

