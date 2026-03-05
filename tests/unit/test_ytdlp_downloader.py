from pathlib import Path

import pytest

from video_bot.core.errors import DownloaderError
from video_bot.infrastructure.downloaders.ytdlp_downloader import YtDlpDownloader


def test_resolve_command_prefers_installed_module(monkeypatch, tmp_path: Path) -> None:
    downloader = YtDlpDownloader(
        ytdlp_bin="yt-dlp",
        downloads_dir=tmp_path,
        timeout_seconds=60,
    )

    monkeypatch.setattr("video_bot.infrastructure.downloaders.ytdlp_downloader.shutil.which", lambda _: None)
    monkeypatch.setattr("video_bot.infrastructure.downloaders.ytdlp_downloader.importlib.util.find_spec", lambda _: object())

    command = downloader._resolve_command()

    assert command[0]
    assert command[1:] == ["-m", "yt_dlp"]


def test_resolve_command_raises_clear_error_when_not_available(monkeypatch, tmp_path: Path) -> None:
    downloader = YtDlpDownloader(
        ytdlp_bin="yt-dlp",
        downloads_dir=tmp_path,
        timeout_seconds=60,
    )

    monkeypatch.setattr("video_bot.infrastructure.downloaders.ytdlp_downloader.shutil.which", lambda _: None)
    monkeypatch.setattr("video_bot.infrastructure.downloaders.ytdlp_downloader.importlib.util.find_spec", lambda _: None)

    with pytest.raises(DownloaderError, match="не найден"):
        downloader._resolve_command()


def test_build_command_disables_simulation(monkeypatch, tmp_path: Path) -> None:
    downloader = YtDlpDownloader(
        ytdlp_bin="yt-dlp",
        downloads_dir=tmp_path,
        timeout_seconds=60,
    )

    monkeypatch.setattr(downloader, "_resolve_command", lambda: ["python", "-m", "yt_dlp"])

    command = downloader._build_command("https://example.com/video", tmp_path / "%(id)s.%(ext)s")

    assert "--no-simulate" in command
    assert command[-1] == "https://example.com/video"
