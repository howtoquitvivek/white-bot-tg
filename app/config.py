"""Application configuration and environment settings."""

from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str = Field(
        ...,
        description="Telegram bot token obtained from @BotFather",
    )
    DATABASE_URL: str = Field(
        ...,
        description="Async PostgreSQL connection string (postgresql+asyncpg://user:pass@host:port/dbname)",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    SECRET_KEY: str = Field(
        default="super-secret-key-change-in-production-min32chars",
        description="Secret key for signing sessions and cryptographic tokens",
    )
    SECURE_COOKIES: bool = Field(
        default=False,
        description="Whether to mark session cookies as Secure (HTTPS only)",
    )
    SESSION_COOKIE_NAME: str = Field(
        default="admin_session",
        description="Cookie name for admin session token",
    )
    CSRF_COOKIE_NAME: str = Field(
        default="csrf_token",
        description="Cookie name for CSRF token",
    )
    CSRF_HEADER_NAME: str = Field(
        default="X-CSRF-Token",
        description="Header name for CSRF token verification",
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins for the frontend dashboard",
    )
    AUTH_REQUIRED: bool = Field(
        default=False,
        description="Whether authentication and CSRF are required. Defaults to False for local development.",
    )
    TELEGRAM_STORAGE_CHANNEL_ID: Optional[str] = Field(
        default=None,
        description="Telegram private channel/chat ID for video storage (e.g. -1001234567890)",
    )
    BOT_ABOUT_TEXT: Optional[str] = Field(
        default=None,
        description="Custom About text for the Telegram bot",
    )
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=50 * 1024 * 1024,
        description="Maximum video upload size in bytes (50 MB standard Bot API limit)",
    )

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        token = v.strip()
        if not token:
            raise ValueError(
                "BOT_TOKEN is missing or empty. Please set a valid Telegram bot token from @BotFather in your environment or .env file."
            )
        if "YOUR_TELEGRAM_BOT_TOKEN" in token or token.lower() in {"token", "your_token", "xxx"}:
            raise ValueError(
                "BOT_TOKEN is set to a placeholder value ('YOUR_TELEGRAM_BOT_TOKEN'). "
                "Please replace it with your actual Telegram bot token from @BotFather in .env."
            )
        parts = token.split(":")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
            raise ValueError(
                "Invalid BOT_TOKEN format. Expected format: '<bot_id>:<token_secret>' "
                "(e.g. 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ)."
            )
        return token

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        url = v.strip()
        if not url:
            raise ValueError(
                "DATABASE_URL is missing or empty. Please configure DATABASE_URL in your environment or .env file."
            )
        if "YOUR_PASSWORD" in url:
            raise ValueError(
                "DATABASE_URL contains the placeholder 'YOUR_PASSWORD'. "
                "Please update it with your actual PostgreSQL credentials in .env."
            )
        if not (url.startswith("postgresql+asyncpg://") or url.startswith("sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL must use an async driver scheme such as 'postgresql+asyncpg://...' or 'sqlite+aiosqlite://...'. "
                f"Got scheme: '{url.split('://')[0] if '://' in url else url}'"
            )
        return url

    @property
    def masked_bot_token(self) -> str:
        """Return masked bot token safe for logging."""
        if not self.BOT_TOKEN or ":" not in self.BOT_TOKEN:
            return "***"
        bot_id, _ = self.BOT_TOKEN.split(":", 1)
        return f"{bot_id}:***"

    @property
    def masked_database_url(self) -> str:
        """Return database URL with password masked, safe for logging."""
        try:
            parsed = urlparse(self.DATABASE_URL)
            if parsed.password:
                netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
                return urlunparse(parsed._replace(netloc=netloc))
            return self.DATABASE_URL
        except Exception:
            return "postgresql+asyncpg://***"

    def __repr__(self) -> str:
        return (
            f"Settings(BOT_TOKEN='{self.masked_bot_token}', "
            f"DATABASE_URL='{self.masked_database_url}', "
            f"LOG_LEVEL='{self.LOG_LEVEL}')"
        )

    def __str__(self) -> str:
        return self.__repr__()


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
