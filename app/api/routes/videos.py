"""Video administration routes."""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db, verify_csrf
from app.api.schemas.auth import MessageResponse
from app.api.schemas.video import VideoCreate, VideoListResponse, VideoResponse, VideoUpdate
from app.models.admin_user import AdminUser
from app.services.audit_service import create_audit_log
from app.services.video_service import (
    archive_video,
    create_video,
    delete_video,
    get_video_by_id,
    list_videos,
    publish_video,
    unpublish_video,
    update_video,
)

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.get("", response_model=VideoListResponse)
async def get_videos(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> VideoListResponse:
    """List all videos with filtering and pagination for administrators."""
    videos, total = await list_videos(
        session=session,
        status=status_filter,
        category_id=category_id,
        search=search,
        limit=limit,
        offset=offset,
        public_only=False,
    )
    return VideoListResponse(
        items=[VideoResponse.model_validate(v) for v in videos],
        total=total,
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Retrieve details for a specific video."""
    video = await get_video_by_id(session, video_id, public_only=False)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return VideoResponse.model_validate(video)


@router.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_video(
    payload: VideoCreate,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Create a new video catalog record."""
    video = await create_video(
        session=session,
        title=payload.title,
        description=payload.description,
        category_ids=payload.category_ids,
        telegram_file_id=payload.telegram_file_id,
        telegram_file_unique_id=payload.telegram_file_unique_id,
        telegram_chat_id=payload.telegram_chat_id,
        telegram_message_id=payload.telegram_message_id,
        duration=payload.duration,
        file_size=payload.file_size,
        mime_type=payload.mime_type,
        status=payload.status or "draft",
    )

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="video.create",
        entity_type="video",
        entity_id=str(video.id),
        metadata={"title": video.title, "status": video.status},
    )

    return VideoResponse.model_validate(video)


@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video_details(
    video_id: uuid.UUID,
    payload: VideoUpdate,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Update metadata or category assignments for a video."""
    video = await update_video(
        session=session,
        video_id=video_id,
        title=payload.title,
        description=payload.description,
        category_ids=payload.category_ids,
        telegram_file_id=payload.telegram_file_id,
        telegram_file_unique_id=payload.telegram_file_unique_id,
        duration=payload.duration,
        file_size=payload.file_size,
        mime_type=payload.mime_type,
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="video.update",
        entity_type="video",
        entity_id=str(video.id),
        metadata={"title": video.title},
    )

    return VideoResponse.model_validate(video)


@router.post("/{video_id}/publish", response_model=VideoResponse)
async def publish(
    video_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Publish a video making it accessible to verified users in the catalog."""
    video = await publish_video(session, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="video.publish",
        entity_type="video",
        entity_id=str(video.id),
    )

    return VideoResponse.model_validate(video)


@router.post("/{video_id}/unpublish", response_model=VideoResponse)
async def unpublish(
    video_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Unpublish a video, reverting its status to draft."""
    video = await unpublish_video(session, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="video.unpublish",
        entity_type="video",
        entity_id=str(video.id),
    )

    return VideoResponse.model_validate(video)


@router.post("/{video_id}/archive", response_model=VideoResponse)
async def archive(
    video_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Archive a video without deleting Telegram assets."""
    video = await archive_video(session, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="video.archive",
        entity_type="video",
        entity_id=str(video.id),
    )

    return VideoResponse.model_validate(video)


@router.delete("/{video_id}", response_model=MessageResponse)
async def remove_video(
    video_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete a video record from the database."""
    deleted = await delete_video(session, video_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="video.delete",
        entity_type="video",
        entity_id=str(video_id),
    )

    return MessageResponse(message="Video deleted successfully")

