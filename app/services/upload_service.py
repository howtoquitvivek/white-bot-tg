"""Video upload workflow service managing streaming, temporary storage, and Telegram synchronization."""

import logging
import os
from pathlib import Path
import tempfile
from typing import List, Optional, Tuple, Union
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.category import Category
from app.models.upload_job import (
    UPLOAD_JOB_COMPLETED,
    UPLOAD_JOB_FAILED,
    UPLOAD_JOB_UPLOADING,
    UploadJob,
)
from app.models.video import (
    VIDEO_STATUS_DRAFT,
    Video,
    VideoCategory,
)
from app.services.telegram_storage import TelegramStorageService, telegram_storage

logger = logging.getLogger(__name__)

# Allowed video extensions
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

# 64 KB chunk size for streaming
CHUNK_SIZE = 64 * 1024


def validate_video_file_header(first_bytes: bytes, filename: str) -> None:
    """Validate video file signatures (magic bytes) when available."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    if len(first_bytes) >= 12:
        # MP4 / MOV standard box signatures
        is_mp4_box = first_bytes[4:8] in {b"ftyp", b"moov", b"mdat", b"wide"}
        # Matroska / WebM EBML header
        is_ebml = first_bytes[:4] == b"\x1a\x45\xdf\xa3"
        # AVI header (RIFF....AVI )
        is_avi = first_bytes[:4] == b"RIFF" and first_bytes[8:12] == b"AVI "

        if not (is_mp4_box or is_ebml or is_avi):
            logger.warning("Unrecognized magic bytes for file %s, proceeding based on extension %s", filename, ext)


async def save_upload_to_temp_file(upload_file: UploadFile, max_size_bytes: int) -> Tuple[Path, int]:
    """Stream uploaded file to a temporary file while enforcing max size limit."""
    filename = upload_file.filename or "uploaded_video.mp4"
    suffix = Path(filename).suffix or ".mp4"

    # Create temporary file
    temp_dir = Path(tempfile.gettempdir()) / "tg_bot_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_path = None
    total_bytes = 0

    try:
        with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=suffix, delete=False) as tmp:
            temp_path = Path(tmp.name)
            first_chunk = True

            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break

                if first_chunk:
                    validate_video_file_header(chunk, filename)
                    first_chunk = False

                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File exceeds maximum upload limit of {max_size_bytes // (1024 * 1024)} MB for Telegram Bot API.",
                    )

                tmp.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        return temp_path, total_bytes

    except Exception:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


async def process_video_upload(
    session: AsyncSession,
    upload_file: UploadFile,
    title: str,
    description: Optional[str] = None,
    category_ids: Optional[List[uuid.UUID]] = None,
    channel_id: Optional[Union[int, str]] = None,
    storage_service: Optional[TelegramStorageService] = None,
) -> Tuple[Video, UploadJob]:
    """Execute complete video upload workflow: stream to disk, send to Telegram, save to DB."""
    settings = get_settings()
    uploader = storage_service or telegram_storage
    filename = upload_file.filename or "video.mp4"

    # 1. Create UploadJob in pending/uploading state
    job = UploadJob(
        original_filename=filename,
        status=UPLOAD_JOB_UPLOADING,
        progress=10,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    temp_path: Optional[Path] = None

    try:
        # 2. Stream to temporary disk storage with size checks
        temp_path, total_bytes = await save_upload_to_temp_file(
            upload_file=upload_file,
            max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
        )

        job.progress = 50
        await session.commit()

        # 3. Upload to Telegram storage channel
        tg_result = await uploader.upload_video(
            file_path=temp_path,
            caption=title,
            channel_id=channel_id,
        )

        job.progress = 80
        await session.commit()

        # 4. Create Video record in draft status
        video = Video(
            title=title.strip(),
            description=description.strip() if description else None,
            telegram_file_id=tg_result.file_id,
            telegram_file_unique_id=tg_result.file_unique_id,
            telegram_chat_id=tg_result.chat_id,
            telegram_message_id=tg_result.message_id,
            duration=tg_result.duration,
            file_size=tg_result.file_size or total_bytes,
            mime_type=tg_result.mime_type or "video/mp4",
            status=VIDEO_STATUS_DRAFT,
        )
        session.add(video)
        await session.flush()

        # 5. Associate Categories if provided
        if category_ids:
            for cat_id in category_ids:
                cat_exists = await session.get(Category, cat_id)
                if cat_exists:
                    session.add(VideoCategory(video_id=video.id, category_id=cat_id))

        # 6. Mark UploadJob as completed
        job.video_id = video.id
        job.status = UPLOAD_JOB_COMPLETED
        job.progress = 100
        await session.commit()

        # Reload video with categories
        stmt = select(Video).options(selectinload(Video.categories)).where(Video.id == video.id)
        video_res = await session.execute(stmt)
        refreshed_video = video_res.scalar_one()

        return refreshed_video, job

    except Exception as exc:
        logger.error("Video upload processing failed: %s", exc)
        job.status = UPLOAD_JOB_FAILED
        job.error_message = str(exc)
        await session.commit()
        raise

    finally:
        # 7. Always delete temporary file from disk
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError as cleanup_err:
                logger.warning("Failed to remove temp upload file %s: %s", temp_path, cleanup_err)


async def get_upload_job(session: AsyncSession, job_id: uuid.UUID) -> Optional[UploadJob]:
    """Retrieve an upload job by ID."""
    return await session.get(UploadJob, job_id)


async def list_upload_jobs(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[UploadJob], int]:
    """List upload jobs with pagination."""
    count_stmt = select(UploadJob)
    total_result = await session.execute(count_stmt)
    total = len(total_result.scalars().all())

    stmt = (
        select(UploadJob)
        .options(selectinload(UploadJob.video))
        .order_by(UploadJob.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all()), total
