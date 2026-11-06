"""Unit tests for environment configuration validation and error handling."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_valid_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test valid configuration with proper token and database URL."""
    settings = Settings(
        BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
        DATABASE_URL="postgresql+asyncpg://postgres:secret123@localhost:5432/video_bot",
        LOG_LEVEL="DEBUG",
    )
    assert settings.BOT_TOKEN == "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
    assert settings.masked_bot_token == "123456789:***"
    assert "secret123" not in settings.masked_database_url
    assert "postgres:***@localhost:5432/video_bot" in settings.masked_database_url
    assert "secret123" not in repr(settings)
    assert "123456789:***" in repr(settings)
    assert "secret123" not in str(settings)
    assert "123456789:***" in str(settings)



def test_missing_bot_token() -> None:
    """Test that empty or missing bot token raises a descriptive ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            BOT_TOKEN="",
            DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/video_bot",
        )
    errors = str(exc_info.value)
    assert "BOT_TOKEN is missing or empty" in errors


def test_placeholder_bot_token() -> None:
    """Test that leaving the default placeholder bot token raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN",
            DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/video_bot",
        )
    errors = str(exc_info.value)
    assert "placeholder" in errors.lower()


def test_malformed_bot_token() -> None:
    """Test that malformed bot token format is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            BOT_TOKEN="invalid_token_without_colon",
            DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/video_bot",
        )
    errors = str(exc_info.value)
    assert "Invalid BOT_TOKEN format" in errors


def test_placeholder_database_password() -> None:
    """Test that leaving YOUR_PASSWORD placeholder raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
            DATABASE_URL="postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/video_bot",
        )
    errors = str(exc_info.value)
    assert "YOUR_PASSWORD" in errors


def test_invalid_database_url_scheme() -> None:
    """Test that non-async database drivers (e.g., synchronous psycopg2) are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
            DATABASE_URL="postgresql://postgres:password@localhost:5432/video_bot",
        )
    errors = str(exc_info.value)
    assert "must use an async driver scheme" in errors
