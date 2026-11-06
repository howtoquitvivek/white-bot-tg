"""Pydantic schemas for collection endpoints."""

from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.video import VideoResponse


class CollectionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cover_video_id: Optional[uuid.UUID] = None
    status: Optional[str] = "draft"
    video_ids: Optional[List[uuid.UUID]] = None


class CollectionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cover_video_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    video_ids: Optional[List[uuid.UUID]] = None


class CollectionReorderRequest(BaseModel):
    video_order: List[uuid.UUID] = Field(..., min_length=1)


class CollectionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    video: VideoResponse
    position: int


class CollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    cover_video_id: Optional[uuid.UUID] = None
    status: str
    created_at: datetime
    updated_at: datetime
    videos: List[VideoResponse] = []


class CollectionListResponse(BaseModel):
    items: List[CollectionResponse]
    total: int

