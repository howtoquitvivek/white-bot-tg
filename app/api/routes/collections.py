"""Collection administration routes."""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db, verify_csrf
from app.api.schemas.auth import MessageResponse
from app.api.schemas.collection import (
    CollectionCreate,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
)
from app.api.schemas.video import VideoResponse
from app.models.admin_user import AdminUser
from app.models.collection import Collection
from app.services.audit_service import create_audit_log
from app.services.collection_service import (
    create_collection,
    delete_collection,
    get_collection_by_id,
    list_collections,
    update_collection,
)

router = APIRouter(prefix="/collections", tags=["Collections"])


def serialize_collection(collection: Collection) -> CollectionResponse:
    """Helper to convert Collection entity into CollectionResponse schema."""
    videos = [
        VideoResponse.model_validate(cv.video)
        for cv in sorted(collection.collection_videos, key=lambda x: x.position)
        if cv.video is not None
    ]
    return CollectionResponse(
        id=collection.id,
        title=collection.title,
        description=collection.description,
        cover_video_id=collection.cover_video_id,
        status=collection.status,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        videos=videos,
    )


@router.get("", response_model=CollectionListResponse)
async def get_collections(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """List all collections with pagination."""
    collections, total = await list_collections(
        session=session,
        status=status_filter,
        limit=limit,
        offset=offset,
        public_only=False,
    )
    return CollectionListResponse(
        items=[serialize_collection(c) for c in collections],
        total=total,
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Retrieve details and videos for a specific collection."""
    collection = await get_collection_by_id(session, collection_id, public_only=False)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return serialize_collection(collection)


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_collection(
    payload: CollectionCreate,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Create a new collection with deduplicated ordered videos."""
    collection = await create_collection(
        session=session,
        title=payload.title,
        description=payload.description,
        cover_video_id=payload.cover_video_id,
        status=payload.status or "draft",
        video_ids=payload.video_ids,
    )

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="collection.create",
        entity_type="collection",
        entity_id=str(collection.id),
        metadata={"title": collection.title},
    )

    # Re-fetch with loaded relationships
    refreshed = await get_collection_by_id(session, collection.id, public_only=False)
    return serialize_collection(refreshed or collection)


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection_details(
    collection_id: uuid.UUID,
    payload: CollectionUpdate,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Update collection metadata and video order."""
    collection = await update_collection(
        session=session,
        collection_id=collection_id,
        title=payload.title,
        description=payload.description,
        cover_video_id=payload.cover_video_id,
        status=payload.status,
        video_ids=payload.video_ids,
    )
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="collection.update",
        entity_type="collection",
        entity_id=str(collection.id),
        metadata={"title": collection.title},
    )

    refreshed = await get_collection_by_id(session, collection.id, public_only=False)
    return serialize_collection(refreshed or collection)


@router.delete("/{collection_id}", response_model=MessageResponse)
async def remove_collection(
    collection_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete a collection record."""
    deleted = await delete_collection(session, collection_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="collection.delete",
        entity_type="collection",
        entity_id=str(collection_id),
    )

    return MessageResponse(message="Collection deleted successfully")

