"""Video management service for administrative and public catalog operations."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.video import (
    VIDEO_STATUS_ARCHIVED,
    VIDEO_STATUS_DRAFT,
    VIDEO_STATUS_PUBLISHED,
    Video,
    VideoCategory,
)


async def get_video_by_id(
    session: AsyncSession,
    video_id: uuid.UUID,
    public_only: bool = False,
) -> Optional[Video]:
    """Retrieve a single video by ID, optionally enforcing published status."""
    stmt = (
        select(Video)
        .options(selectinload(Video.categories))
        .where(Video.id == video_id)
    )
    if public_only:
        stmt = stmt.where(Video.status == VIDEO_STATUS_PUBLISHED)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_videos(
    session: AsyncSession,
    status: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    public_only: bool = False,
) -> Tuple[List[Video], int]:
    """List videos with optional filtering, search, pagination, and public access gating.

    When public_only=True, only published videos are returned.
    """
    base_query = select(Video).options(selectinload(Video.categories))
    count_query = select(func.count(func.distinct(Video.id))).select_from(Video)

    # 1. Enforce public access restriction
    if public_only:
        base_query = base_query.where(Video.status == VIDEO_STATUS_PUBLISHED)
        count_query = count_query.where(Video.status == VIDEO_STATUS_PUBLISHED)
    elif status:
        base_query = base_query.where(Video.status == status)
        count_query = count_query.where(Video.status == status)

    # 2. Filter by category
    if category_id:
        base_query = base_query.join(VideoCategory, Video.id == VideoCategory.video_id).where(
            VideoCategory.category_id == category_id
        )
        count_query = count_query.join(VideoCategory, Video.id == VideoCategory.video_id).where(
            VideoCategory.category_id == category_id
        )

    # 3. Filter by search query
    if search:
        search_term = f"%{search.strip()}%"
        base_query = base_query.where(Video.title.ilike(search_term))
        count_query = count_query.where(Video.title.ilike(search_term))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    base_query = base_query.order_by(Video.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(base_query)
    videos = list(result.scalars().all())

    return videos, total


async def create_video(
    session: AsyncSession,
    title: str,
    description: Optional[str] = None,
    category_ids: Optional[List[uuid.UUID]] = None,
    telegram_file_id: Optional[str] = None,
    telegram_file_unique_id: Optional[str] = None,
    telegram_chat_id: Optional[int] = None,
    telegram_message_id: Optional[int] = None,
    duration: Optional[int] = None,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = "video/mp4",
    status: str = VIDEO_STATUS_DRAFT,
) -> Video:
    """Create and persist a new Video record."""
    video = Video(
        title=title.strip(),
        description=description.strip() if description else None,
        telegram_file_id=telegram_file_id,
        telegram_file_unique_id=telegram_file_unique_id,
        telegram_chat_id=telegram_chat_id,
        telegram_message_id=telegram_message_id,
        duration=duration,
        file_size=file_size,
        mime_type=mime_type or "video/mp4",
        status=status,
    )

    if category_ids:
        cat_stmt = select(Category).where(Category.id.in_(category_ids))
        categories = (await session.execute(cat_stmt)).scalars().all()
        video.categories = list(categories)

    session.add(video)
    await session.commit()
    await session.refresh(video)
    return video


async def update_video(
    session: AsyncSession,
    video_id: uuid.UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    category_ids: Optional[List[uuid.UUID]] = None,
    telegram_file_id: Optional[str] = None,
    telegram_file_unique_id: Optional[str] = None,
    duration: Optional[int] = None,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = None,
) -> Optional[Video]:
    """Update metadata and category associations for an existing video."""
    video = await get_video_by_id(session, video_id, public_only=False)
    if not video:
        return None

    if title is not None:
        video.title = title.strip()
    if description is not None:
        video.description = description.strip() if description else None
    if telegram_file_id is not None:
        video.telegram_file_id = telegram_file_id
    if telegram_file_unique_id is not None:
        video.telegram_file_unique_id = telegram_file_unique_id
    if duration is not None:
        video.duration = duration
    if file_size is not None:
        video.file_size = file_size
    if mime_type is not None:
        video.mime_type = mime_type

    if category_ids is not None:
        if category_ids:
            cat_stmt = select(Category).where(Category.id.in_(category_ids))
            categories = (await session.execute(cat_stmt)).scalars().all()
            video.categories = list(categories)
        else:
            video.categories = []

    await session.commit()
    await session.refresh(video)
    return video


async def publish_video(session: AsyncSession, video_id: uuid.UUID) -> Optional[Video]:
    """Publish a video making it accessible in the catalog."""
    video = await get_video_by_id(session, video_id, public_only=False)
    if not video:
        return None

    video.status = VIDEO_STATUS_PUBLISHED
    video.published_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(video)
    return video


async def unpublish_video(session: AsyncSession, video_id: uuid.UUID) -> Optional[Video]:
    """Unpublish a video moving it back to draft status."""
    video = await get_video_by_id(session, video_id, public_only=False)
    if not video:
        return None

    video.status = VIDEO_STATUS_DRAFT
    video.published_at = None
    await session.commit()
    await session.refresh(video)
    return video


async def archive_video(session: AsyncSession, video_id: uuid.UUID) -> Optional[Video]:
    """Archive a video without deleting Telegram media assets."""
    video = await get_video_by_id(session, video_id, public_only=False)
    if not video:
        return None

    video.status = VIDEO_STATUS_ARCHIVED
    await session.commit()
    await session.refresh(video)
    return video


async def delete_video(session: AsyncSession, video_id: uuid.UUID) -> bool:
    """Delete a video record from the database."""
    video = await get_video_by_id(session, video_id, public_only=False)
    if not video:
        return False

    await session.delete(video)
    await session.commit()
    return True

