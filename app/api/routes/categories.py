"""Category administration routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db, verify_csrf
from app.api.schemas.auth import MessageResponse
from app.api.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from app.models.admin_user import AdminUser
from app.services.audit_service import create_audit_log
from app.services.category_service import (
    create_category,
    delete_category,
    get_category_by_id,
    list_categories,
    update_category,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=CategoryListResponse)
async def get_all_categories(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> CategoryListResponse:
    """List all categories with pagination."""
    categories, total = await list_categories(session, limit=limit, offset=offset)
    return CategoryListResponse(
        items=[CategoryResponse.model_validate(c) for c in categories],
        total=total,
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_new_category(
    payload: CategoryCreate,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """Create a new category."""
    try:
        category = await create_category(
            session=session,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create category: {exc}",
        )

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="category.create",
        entity_type="category",
        entity_id=str(category.id),
        metadata={"name": category.name, "slug": category.slug},
    )

    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category_details(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """Update category name, slug, or description."""
    category = await update_category(
        session=session,
        category_id=category_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
    )
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="category.update",
        entity_type="category",
        entity_id=str(category.id),
        metadata={"name": category.name},
    )

    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", response_model=MessageResponse)
async def remove_category(
    category_id: uuid.UUID,
    admin: AdminUser = Depends(get_current_admin),
    _csrf: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete a category."""
    deleted = await delete_category(session, category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="category.delete",
        entity_type="category",
        entity_id=str(category_id),
    )

    return MessageResponse(message="Category deleted successfully")

