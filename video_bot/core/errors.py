class TTSaveBotError(Exception):
    """Base application error."""


class AccessDeniedError(TTSaveBotError):
    """Raised when a user is not allowed to use the bot."""


class ValidationError(TTSaveBotError):
    """Raised when the user input is invalid."""


class DownloaderError(TTSaveBotError):
    """Raised when a video cannot be downloaded."""


class PrivateContentError(DownloaderError):
    """Raised for private or protected content."""


class DownloadTimeoutError(DownloaderError):
    """Raised when the downloader exceeds the configured timeout."""


class FileTooLargeError(TTSaveBotError):
    """Raised when a downloaded file exceeds the Telegram limit."""

