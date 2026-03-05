from __future__ import annotations

from enum import StrEnum


class PlatformType(StrEnum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


class UserRole(StrEnum):
    SUPERADMIN = "superadmin"
    USER = "user"


class DownloadStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"
    OVERSIZE = "oversize"

