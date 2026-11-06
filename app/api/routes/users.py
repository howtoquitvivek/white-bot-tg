"""User management routes for administrators."""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db
from app.api.schemas.user import UserListResponse, UserResponse
from app.models.admin_user import AdminUser
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    search: Optional[str] = Query(None, description="Search by username or first/last name"),
    verified_only: Optional[bool] = Query(None, description="Filter by age verification status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """List bot users with pagination and filtering."""
    base_query = select(User)
    count_query = select(func.count(User.id))

    if verified_only is True:
        base_query = base_query.where(User.age_verified_at.is_not(None))
        count_query = count_query.where(User.age_verified_at.is_not(None))
    elif verified_only is False:
        base_query = base_query.where(User.age_verified_at.is_(None))
        count_query = count_query.where(User.age_verified_at.is_(None))

    if search:
        search_term = f"%{search.strip()}%"
        filter_clause = or_(
            User.username.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
        )
        base_query = base_query.where(filter_clause)
        count_query = count_query.where(filter_clause)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    base_query = base_query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(base_query)
    users = list(result.scalars().all())

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_detail(
    user_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve details for a specific user."""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)

