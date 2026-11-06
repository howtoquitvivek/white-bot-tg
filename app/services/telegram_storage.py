"""Service for uploading and delivering video files via Telegram Bot API."""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Optional, Union

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TelegramVideoResult:
    """Metadata extracted from a successful Telegram video upload."""

    file_id: str
    file_unique_id: str
    chat_id: int
    message_id: int
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class TelegramStorageService:
    """Manages video uploads to the private Telegram storage channel."""

    def __init__(self, bot: Optional[Bot] = None) -> None:
        self._bot = bot

    def get_bot(self) -> Bot:
        """Retrieve existing bot instance or create one from settings."""
        if self._bot is None:
            settings = get_settings()
            self._bot = Bot(token=settings.BOT_TOKEN)
        return self._bot

    async def upload_video(
        self,
        file_path: Union[str, Path],
        caption: Optional[str] = None,
        channel_id: Optional[Union[int, str]] = None,
    ) -> TelegramVideoResult:
        """Upload a video file to the Telegram private storage channel.

        Args:
            file_path: Local filesystem path to the video file.
            caption: Optional caption or title for the video message.
            channel_id: Target channel ID. Defaults to settings.TELEGRAM_STORAGE_CHANNEL_ID.

        Returns:
            TelegramVideoResult with file_id, message_id, and media properties.

        Raises:
            ValueError: If target channel ID is missing or invalid.
            FileNotFoundError: If the local file does not exist.
            RuntimeError: If Telegram upload fails or returned message lacks video metadata.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Video file not found at {path}")

        settings = get_settings()
        target_channel = channel_id or settings.TELEGRAM_STORAGE_CHANNEL_ID
        if not target_channel:
            raise ValueError(
                "Telegram storage channel ID is not configured. "
                "Set TELEGRAM_STORAGE_CHANNEL_ID in .env or provide channel_id."
            )

        # Parse numeric channel IDs if given as strings (e.g. "-1001234567890")
        target_chat_id: Union[int, str]
        if isinstance(target_channel, str) and (
            target_channel.startswith("-") or target_channel.isdigit()
        ):
            try:
                target_chat_id = int(target_channel)
            except ValueError:
                target_chat_id = target_channel
        else:
            target_chat_id = target_channel

        bot = self.get_bot()
        input_file = FSInputFile(path=str(path), filename=path.name)

        try:
            message = await bot.send_video(
                chat_id=target_chat_id,
                video=input_file,
                caption=caption[:1024] if caption else None,
                supports_streaming=True,
            )
        except TelegramAPIError as exc:
            logger.error("Telegram API upload failed for %s: %s", path.name, exc)
            raise RuntimeError(f"Telegram upload failed: {exc.message}") from exc
        except Exception as exc:
            logger.error("Unexpected error during Telegram video upload: %s", exc)
            raise RuntimeError(f"Video upload failed: {str(exc)}") from exc

        # Extract file info from video or document payload
        if message.video:
            video_meta = message.video
            return TelegramVideoResult(
                file_id=video_meta.file_id,
                file_unique_id=video_meta.file_unique_id,
                chat_id=message.chat.id,
                message_id=message.message_id,
                duration=video_meta.duration,
                file_size=video_meta.file_size,
                mime_type=video_meta.mime_type or "video/mp4",
                width=video_meta.width,
                height=video_meta.height,
            )
        elif message.document:
            doc_meta = message.document
            return TelegramVideoResult(
                file_id=doc_meta.file_id,
                file_unique_id=doc_meta.file_unique_id,
                chat_id=message.chat.id,
                message_id=message.message_id,
                duration=None,
                file_size=doc_meta.file_size,
                mime_type=doc_meta.mime_type or "video/mp4",
            )
        else:
            raise RuntimeError("Telegram response did not contain a video or document attachment.")


# Shared default singleton
telegram_storage = TelegramStorageService()

