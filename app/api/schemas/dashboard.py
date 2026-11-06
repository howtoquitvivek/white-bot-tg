"""Pydantic schemas for dashboard metrics."""

from typing import Any, Dict, List
from pydantic import BaseModel


class VideoStats(BaseModel):
    total: int
    published: int
    draft: int
    archived: int


class CategoryStats(BaseModel):
    total: int


class CollectionStats(BaseModel):
    total: int
    published: int


class UserStats(BaseModel):
    total: int
    verified: int


class ActivityLogItem(BaseModel):
    id: str
    admin_username: str
    action: str
    entity_type: str
    entity_id: str | None = None
    created_at: str
    metadata: Dict[str, Any] = {}


class DashboardStatsResponse(BaseModel):
    videos: VideoStats
    categories: CategoryStats
    collections: CollectionStats
    users: UserStats
    recent_activity: List[ActivityLogItem]
    recent_videos: List[Dict[str, Any]] = []

