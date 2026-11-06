"""Unit tests for database models and schema relationships."""

from datetime import datetime, timezone
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    COLLECTION_STATUS_DRAFT,
    COLLECTION_STATUS_PUBLISHED,
    UPLOAD_JOB_PENDING,
    VIDEO_STATUS_DRAFT,
    VIDEO_STATUS_PUBLISHED,
    AdminUser,
    AuditLog,
    Category,
    Collection,
    CollectionVideo,
    UploadJob,
    Video,
    VideoCategory,
)


async def test_admin_user_model(db_session: AsyncSession) -> None:
    """Test AdminUser creation, defaults, and uniqueness constraints."""
    admin = AdminUser(
        username="superadmin",
        password_hash="argon2_hashed_secret",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    assert admin.id is not None
    assert admin.username == "superadmin"
    assert admin.password_hash == "argon2_hashed_secret"
    assert admin.is_active is True
    assert admin.created_at is not None
    assert admin.last_login_at is None

    # Uniqueness constraint test
    duplicate_admin = AdminUser(
        username="superadmin",
        password_hash="another_hash",
    )
    db_session.add(duplicate_admin)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_category_model(db_session: AsyncSession) -> None:
    """Test Category creation and unique slug/name constraints."""
    cat = Category(
        name="Action",
        slug="action",
        description="Action-packed videos",
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    assert cat.id is not None
    assert cat.name == "Action"
    assert cat.slug == "action"
    assert cat.description == "Action-packed videos"
    assert cat.created_at is not None

    # Duplicate slug test
    dup = Category(name="Action 2", slug="action")
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_video_model(db_session: AsyncSession) -> None:
    """Test Video creation, default status, and published state."""
    video = Video(
        title="Sample Video",
        description="A test video sample",
        telegram_file_id="BAACAgIAAxkBAAE...",
        telegram_file_unique_id="unique_file_123",
        duration=120,
        file_size=10485760,
        mime_type="video/mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    assert video.id is not None
    assert video.title == "Sample Video"
    assert video.status == VIDEO_STATUS_DRAFT
    assert video.is_published is False
    assert video.duration == 120
    assert video.file_size == 10485760
    assert video.mime_type == "video/mp4"
    assert video.created_at is not None
    assert video.updated_at is not None
    assert video.published_at is None

    # Test status change to published
    video.status = VIDEO_STATUS_PUBLISHED
    video.published_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(video)

    assert video.is_published is True
    assert video.published_at is not None


async def test_video_category_many_to_many(db_session: AsyncSession) -> None:
    """Test bidirectional many-to-many relationship between Video and Category."""
    cat1 = Category(name="Thriller", slug="thriller")
    cat2 = Category(name="Drama", slug="drama")
    video = Video(title="Suspense Story", categories=[cat1, cat2])

    db_session.add(video)
    await db_session.commit()

    # Query from video side using eager loading
    result = await db_session.execute(
        select(Video).options(selectinload(Video.categories)).where(Video.id == video.id)
    )
    loaded_video = result.scalar_one()
    assert len(loaded_video.categories) == 2
    category_slugs = {c.slug for c in loaded_video.categories}
    assert category_slugs == {"thriller", "drama"}

    # Query from category side using eager loading
    cat_result = await db_session.execute(
        select(Category).options(selectinload(Category.videos)).where(Category.slug == "thriller")
    )
    loaded_cat = cat_result.scalar_one()
    assert len(loaded_cat.videos) == 1
    assert loaded_cat.videos[0].id == video.id


async def test_collection_model_and_ordering(db_session: AsyncSession) -> None:
    """Test Collection, Cover Video, and CollectionVideo position ordering."""
    v1 = Video(title="Episode 1")
    v2 = Video(title="Episode 2")
    db_session.add_all([v1, v2])
    await db_session.commit()

    cv1 = CollectionVideo(video_id=v1.id, position=1)
    cv2 = CollectionVideo(video_id=v2.id, position=2)

    coll = Collection(
        title="Web Series Season 1",
        description="First season of series",
        status=COLLECTION_STATUS_DRAFT,
        cover_video_id=v1.id,
        collection_videos=[cv1, cv2],
    )
    db_session.add(coll)
    await db_session.commit()

    # Query collection with eager loading
    result = await db_session.execute(
        select(Collection)
        .options(
            selectinload(Collection.collection_videos),
            selectinload(Collection.cover_video),
        )
        .where(Collection.id == coll.id)
    )
    loaded_coll = result.scalar_one()

    assert loaded_coll.cover_video is not None
    assert loaded_coll.cover_video.id == v1.id
    assert len(loaded_coll.collection_videos) == 2
    assert loaded_coll.collection_videos[0].video_id == v1.id
    assert loaded_coll.collection_videos[0].position == 1
    assert loaded_coll.collection_videos[1].video_id == v2.id
    assert loaded_coll.collection_videos[1].position == 2


async def test_upload_job_model(db_session: AsyncSession) -> None:
    """Test UploadJob creation and linkage to Video."""
    video = Video(title="Video from Upload")
    db_session.add(video)
    await db_session.commit()

    job = UploadJob(
        original_filename="holiday_clip.mp4",
        status=UPLOAD_JOB_PENDING,
        progress=0,
        video_id=video.id,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    assert job.id is not None
    assert job.original_filename == "holiday_clip.mp4"
    assert job.status == UPLOAD_JOB_PENDING
    assert job.progress == 0
    assert job.video_id == video.id
    assert job.created_at is not None

    # Update progress
    job.progress = 50
    job.status = "uploading"
    await db_session.commit()
    await db_session.refresh(job)

    assert job.progress == 50
    assert job.status == "uploading"


async def test_audit_log_model(db_session: AsyncSession) -> None:
    """Test AuditLog record with metadata JSON and admin linkage."""
    admin = AdminUser(username="auditor", password_hash="dummy_hash")
    db_session.add(admin)
    await db_session.commit()

    audit = AuditLog(
        admin_id=admin.id,
        action="video.publish",
        entity_type="video",
        entity_id=str(uuid.uuid4()),
        extra_metadata={"ip": "127.0.0.1", "browser": "Chrome", "reason": "approved"},
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.id is not None
    assert audit.admin_id == admin.id
    assert audit.action == "video.publish"
    assert audit.entity_type == "video"
    assert audit.extra_metadata == {"ip": "127.0.0.1", "browser": "Chrome", "reason": "approved"}
    assert audit.created_at is not None
