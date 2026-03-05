from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from video_bot.core.entities.enums import UserRole


@dataclass(slots=True, frozen=True)
class User:
    telegram_id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def is_superadmin(self) -> bool:
        return self.role == UserRole.SUPERADMIN

