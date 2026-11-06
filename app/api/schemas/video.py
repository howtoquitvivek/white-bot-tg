"""Pydantic schemas for video endpoints."""

from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.category import CategoryResponse


class VideoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_ids: Optional[List[uuid.UUID]] = None
    telegram_file_id: Optional[str] = None
    telegram_file_unique_id: Optional[str] = None
    telegram_chat_id: Optional[int] = None
    telegram_message_id: Optional[int] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = "video/mp4"
    status: Optional[str] = "draft"


class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_ids: Optional[List[uuid.UUID]] = None
    telegram_file_id: Optional[str] = None
    telegram_file_unique_id: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    telegram_file_id: Optional[str] = None
    telegram_file_unique_id: Optional[str] = None
    telegram_chat_id: Optional[int] = None
    telegram_message_id: Optional[int] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    categories: List[CategoryResponse] = []


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int

