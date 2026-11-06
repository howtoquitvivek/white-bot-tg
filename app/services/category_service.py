"""Category management service."""

import re
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category


def slugify(text: str) -> str:
    """Generate a clean URL/identifier slug from a string."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


async def get_category_by_id(session: AsyncSession, category_id: uuid.UUID) -> Optional[Category]:
    """Retrieve category by UUID."""
    stmt = select(Category).where(Category.id == category_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_category_by_slug(session: AsyncSession, slug: str) -> Optional[Category]:
    """Retrieve category by unique slug."""
    stmt = select(Category).where(Category.slug == slug)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_categories(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Category], int]:
    """List categories with total count and pagination."""
    count_stmt = select(func.count()).select_from(Category)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = select(Category).order_by(Category.name.asc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    categories = list(result.scalars().all())

    return categories, total


async def list_categories_with_published_counts(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Tuple[Category, int]], int]:
    """List categories along with the count of published videos in each."""
    from app.models.video import Video, VideoCategory, VIDEO_STATUS_PUBLISHED

    # Count total categories
    count_stmt = select(func.count(Category.id))
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Query categories with count of published videos
    published_case = case(
        (Video.status == VIDEO_STATUS_PUBLISHED, Video.id),
        else_=None,
    )
    stmt = (
        select(
            Category,
            func.count(func.distinct(published_case)).label("published_count"),
        )
        .outerjoin(VideoCategory, Category.id == VideoCategory.category_id)
        .outerjoin(Video, VideoCategory.video_id == Video.id)
        .group_by(Category.id)
        .order_by(Category.name.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()
    categories_with_counts = [(row[0], int(row[1])) for row in rows]
    return categories_with_counts, total


async def create_category(
    session: AsyncSession,
    name: str,
    slug: Optional[str] = None,
    description: Optional[str] = None,
) -> Category:
    """Create a new category."""
    final_slug = slugify(slug or name)
    category = Category(
        name=name.strip(),
        slug=final_slug,
        description=description.strip() if description else None,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def update_category(
    session: AsyncSession,
    category_id: uuid.UUID,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Category]:
    """Update existing category metadata."""
    category = await get_category_by_id(session, category_id)
    if not category:
        return None

    if name is not None:
        category.name = name.strip()
    if slug is not None:
        category.slug = slugify(slug)
    if description is not None:
        category.description = description.strip() if description else None

    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: uuid.UUID) -> bool:
    """Delete a category by ID."""
    category = await get_category_by_id(session, category_id)
    if not category:
        return False

    await session.delete(category)
    await session.commit()
    return True

