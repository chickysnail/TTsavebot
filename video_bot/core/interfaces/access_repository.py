from __future__ import annotations

from abc import ABC, abstractmethod

from video_bot.core.entities import User, UserRole


class IAccessRepository(ABC):
    @abstractmethod
    async def get_user(self, telegram_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_user(self, telegram_id: int, role: UserRole) -> User:
        raise NotImplementedError

    @abstractmethod
    async def deactivate_user(self, telegram_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_active_users(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def list_inactive_users(self) -> list[User]:
        raise NotImplementedError

