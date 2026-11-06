"""Pydantic schemas for user endpoints."""

from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age_verified_at: Optional[datetime] = None
    is_age_verified: bool
    status: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int

