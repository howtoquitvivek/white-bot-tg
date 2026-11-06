"""Pydantic schemas for authentication and admin user representation."""

from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Payload for administrator login."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class AdminResponse(BaseModel):
    """Admin profile representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Generic status/acknowledgment message."""

    message: str


class LoginResponse(BaseModel):
    """Response returned upon successful administrator authentication."""

    admin: AdminResponse
    csrf_token: str
    message: str

