"""Pydantic schemas package."""

from app.api.schemas.auth import AdminResponse, LoginRequest, LoginResponse, MessageResponse
from app.api.schemas.category import CategoryCreate, CategoryListResponse, CategoryResponse, CategoryUpdate
from app.api.schemas.collection import (
    CollectionCreate,
    CollectionItemResponse,
    CollectionListResponse,
    CollectionReorderRequest,
    CollectionResponse,
    CollectionUpdate,
)
from app.api.schemas.dashboard import DashboardStatsResponse
from app.api.schemas.user import UserListResponse, UserResponse
from app.api.schemas.video import VideoCreate, VideoListResponse, VideoResponse, VideoUpdate

__all__ = [
    "AdminResponse",
    "CategoryCreate",
    "CategoryListResponse",
    "CategoryResponse",
    "CategoryUpdate",
    "CollectionCreate",
    "CollectionItemResponse",
    "CollectionListResponse",
    "CollectionReorderRequest",
    "CollectionResponse",
    "CollectionUpdate",
    "DashboardStatsResponse",
    "LoginRequest",
    "LoginResponse",
    "MessageResponse",
    "UserListResponse",
    "UserResponse",
    "VideoCreate",
    "VideoListResponse",
    "VideoResponse",
    "VideoUpdate",
]

