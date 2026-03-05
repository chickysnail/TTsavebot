import pytest

from video_bot.core.entities import PlatformType, VideoRequest, detect_platform
from video_bot.core.errors import ValidationError


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.tiktok.com/@creator/video/123", PlatformType.TIKTOK),
        ("https://vm.tiktok.com/ZM123456/", PlatformType.TIKTOK),
        ("https://vt.tiktok.com/ZSudP646K/", PlatformType.TIKTOK),
        ("https://www.instagram.com/reel/ABC123/", PlatformType.INSTAGRAM),
        ("https://instagram.com/p/ABC123/", PlatformType.INSTAGRAM),
    ],
)
def test_detect_platform_accepts_supported_urls(url: str, platform: PlatformType) -> None:
    assert detect_platform(url) == platform


@pytest.mark.parametrize(
    "url",
    [
        "notaurl",
        "https://example.com/video/123",
        "https://instagram.com/stories/abc",
    ],
)
def test_detect_platform_rejects_unsupported_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        detect_platform(url)


def test_video_request_uses_detected_platform() -> None:
    request = VideoRequest.from_url(telegram_id=1, url="https://www.tiktok.com/@creator/video/123")
    assert request.platform == PlatformType.TIKTOK
    assert request.telegram_id == 1
