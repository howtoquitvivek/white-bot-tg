"""Collection management service for administrative and public catalog operations."""

from typing import List, Optional, Tuple
import uuid

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collection import (
    COLLECTION_STATUS_ARCHIVED,
    COLLECTION_STATUS_DRAFT,
    COLLECTION_STATUS_PUBLISHED,
    Collection,
    CollectionVideo,
)
from app.models.video import VIDEO_STATUS_PUBLISHED, Video


async def get_collection_by_id(
    session: AsyncSession,
    collection_id: uuid.UUID,
    public_only: bool = False,
) -> Optional[Collection]:
    """Retrieve collection by ID with loaded items and cover video.

    If public_only=True, unpublished collections are not returned, and only published
    videos within the collection are exposed.
    """
    stmt = (
        select(Collection)
        .options(
            selectinload(Collection.collection_videos).selectinload(CollectionVideo.video),
            selectinload(Collection.cover_video),
        )
        .where(Collection.id == collection_id)
    )

    if public_only:
        stmt = stmt.where(Collection.status == COLLECTION_STATUS_PUBLISHED)

    result = await session.execute(stmt)
    collection = result.scalar_one_or_none()

    if collection and public_only:
        # Filter collection_videos in-memory for public view to exclude non-published videos
        collection.collection_videos = [
            cv for cv in collection.collection_videos
            if cv.video and cv.video.status == VIDEO_STATUS_PUBLISHED
        ]

    return collection


async def list_collections(
    session: AsyncSession,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    public_only: bool = False,
) -> Tuple[List[Collection], int]:
    """List collections with count and pagination."""
    base_query = select(Collection).options(
        selectinload(Collection.collection_videos).selectinload(CollectionVideo.video),
        selectinload(Collection.cover_video),
    )
    count_query = select(func.count(Collection.id))

    if public_only:
        base_query = base_query.where(Collection.status == COLLECTION_STATUS_PUBLISHED)
        count_query = count_query.where(Collection.status == COLLECTION_STATUS_PUBLISHED)
    elif status:
        base_query = base_query.where(Collection.status == status)
        count_query = count_query.where(Collection.status == status)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    base_query = base_query.order_by(Collection.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(base_query)
    collections = list(result.scalars().all())

    if public_only:
        for coll in collections:
            coll.collection_videos = [
                cv for cv in coll.collection_videos
                if cv.video and cv.video.status == VIDEO_STATUS_PUBLISHED
            ]

    return collections, total


async def list_collections_with_published_counts(
    session: AsyncSession,
    public_only: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Tuple[Collection, int]], int]:
    """List collections along with the count of published videos in each."""
    count_case = case(
        (Video.status == VIDEO_STATUS_PUBLISHED, Video.id),
        else_=None,
    )
    stmt = (
        select(
            Collection,
            func.count(func.distinct(count_case)).label("published_count"),
        )
        .outerjoin(CollectionVideo, Collection.id == CollectionVideo.collection_id)
        .outerjoin(Video, CollectionVideo.video_id == Video.id)
    )
    count_stmt = select(func.count(Collection.id))

    if public_only:
        stmt = stmt.where(Collection.status == COLLECTION_STATUS_PUBLISHED)
        count_stmt = count_stmt.where(Collection.status == COLLECTION_STATUS_PUBLISHED)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = (
        stmt.group_by(Collection.id)
        .order_by(Collection.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()
    collections_with_counts = [(row[0], int(row[1])) for row in rows]
    return collections_with_counts, total


async def create_collection(
    session: AsyncSession,
    title: str,
    description: Optional[str] = None,
    cover_video_id: Optional[uuid.UUID] = None,
    status: str = COLLECTION_STATUS_DRAFT,
    video_ids: Optional[List[uuid.UUID]] = None,
) -> Collection:
    """Create a new collection, preventing duplicate videos and establishing initial ordering."""
    collection = Collection(
        title=title.strip(),
        description=description.strip() if description else None,
        cover_video_id=cover_video_id,
        status=status,
    )

    if video_ids:
        # Deduplicate while preserving order
        unique_video_ids = list(dict.fromkeys(video_ids))
        items = [
            CollectionVideo(video_id=vid, position=idx)
            for idx, vid in enumerate(unique_video_ids)
        ]
        collection.collection_videos = items

    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection


async def update_collection(
    session: AsyncSession,
    collection_id: uuid.UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    cover_video_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    video_ids: Optional[List[uuid.UUID]] = None,
) -> Optional[Collection]:
    """Update collection metadata and video composition."""
    collection = await get_collection_by_id(session, collection_id, public_only=False)
    if not collection:
        return None

    if title is not None:
        collection.title = title.strip()
    if description is not None:
        collection.description = description.strip() if description else None
    if cover_video_id is not None:
        collection.cover_video_id = cover_video_id
    if status is not None:
        collection.status = status

    if video_ids is not None:
        # Delete existing items and replace with new deduplicated ordered list
        await session.execute(
            delete(CollectionVideo).where(CollectionVideo.collection_id == collection_id)
        )
        unique_video_ids = list(dict.fromkeys(video_ids))
        collection.collection_videos = [
            CollectionVideo(collection_id=collection_id, video_id=vid, position=idx)
            for idx, vid in enumerate(unique_video_ids)
        ]

    await session.commit()
    await session.refresh(collection)
    return collection


async def reorder_collection_videos(
    session: AsyncSession,
    collection_id: uuid.UUID,
    video_order: List[uuid.UUID],
) -> Optional[Collection]:
    """Reorder videos inside a collection according to the provided list of IDs."""
    collection = await get_collection_by_id(session, collection_id, public_only=False)
    if not collection:
        return None

    # Deduplicate video_order
    unique_order = list(dict.fromkeys(video_order))
    order_map = {vid: idx for idx, vid in enumerate(unique_order)}

    for item in collection.collection_videos:
        if item.video_id in order_map:
            item.position = order_map[item.video_id]

    # Sort in memory to reflect new positions
    collection.collection_videos.sort(key=lambda x: x.position)
    await session.commit()
    await session.refresh(collection)
    return collection


async def delete_collection(session: AsyncSession, collection_id: uuid.UUID) -> bool:
    """Delete a collection record from the database."""
    collection = await get_collection_by_id(session, collection_id, public_only=False)
    if not collection:
        return False

    await session.delete(collection)
    await session.commit()
    return True

