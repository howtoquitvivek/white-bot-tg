"""AdminUser model definition."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Boolean, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TZDateTime


class AdminUser(Base):
    """Administrator user entity with credentials for dashboard access."""

    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime,
        nullable=True,
        default=None,
    )

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username={self.username!r}, is_active={self.is_active})>"

