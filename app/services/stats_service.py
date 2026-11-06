"""Dashboard statistics and analytics service."""

from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.collection import COLLECTION_STATUS_PUBLISHED, Collection
from app.models.user import User
from app.models.video import (
    VIDEO_STATUS_ARCHIVED,
    VIDEO_STATUS_DRAFT,
    VIDEO_STATUS_PUBLISHED,
    Video,
)


async def get_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
    """Calculate and return platform overview metrics."""
    # Video counts
    total_videos = (await session.execute(select(func.count(Video.id)))).scalar_one()
    published_videos = (
        await session.execute(select(func.count(Video.id)).where(Video.status == VIDEO_STATUS_PUBLISHED))
    ).scalar_one()
    draft_videos = (
        await session.execute(select(func.count(Video.id)).where(Video.status == VIDEO_STATUS_DRAFT))
    ).scalar_one()
    archived_videos = (
        await session.execute(select(func.count(Video.id)).where(Video.status == VIDEO_STATUS_ARCHIVED))
    ).scalar_one()

    # Category count
    total_categories = (await session.execute(select(func.count(Category.id)))).scalar_one()

    # Collection counts
    total_collections = (await session.execute(select(func.count(Collection.id)))).scalar_one()
    published_collections = (
        await session.execute(select(func.count(Collection.id)).where(Collection.status == COLLECTION_STATUS_PUBLISHED))
    ).scalar_one()

    # User counts
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    verified_users = (
        await session.execute(select(func.count(User.id)).where(User.age_verified_at.is_not(None)))
    ).scalar_one()

    # Recent activity
    recent_audits_stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.admin))
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_audits_result = await session.execute(recent_audits_stmt)
    recent_audits = [
        {
            "id": str(log.id),
            "admin_username": log.admin.username if log.admin else "System",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "created_at": log.created_at.isoformat(),
            "metadata": log.extra_metadata or {},
        }
        for log in recent_audits_result.scalars().all()
    ]

    # Recent videos / uploads for dashboard
    recent_videos_stmt = (
        select(Video)
        .options(selectinload(Video.categories))
        .order_by(Video.created_at.desc())
        .limit(10)
    )
    recent_videos_result = await session.execute(recent_videos_stmt)
    recent_videos = [
        {
            "id": str(v.id),
            "title": v.title,
            "status": v.status,
            "duration": v.duration,
            "file_size": v.file_size,
            "created_at": v.created_at.isoformat(),
            "categories": [{"id": str(c.id), "name": c.name} for c in v.categories],
        }
        for v in recent_videos_result.scalars().all()
    ]

    return {
        "videos": {
            "total": total_videos,
            "published": published_videos,
            "draft": draft_videos,
            "archived": archived_videos,
        },
        "categories": {
            "total": total_categories,
        },
        "collections": {
            "total": total_collections,
            "published": published_collections,
        },
        "users": {
            "total": total_users,
            "verified": verified_users,
        },
        "recent_activity": recent_audits,
        "recent_videos": recent_videos,
    }

