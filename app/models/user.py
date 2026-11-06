"""User database model definition."""

from datetime import datetime, timezone
from typing import Optional
import uuid

import sqlalchemy as sa
from sqlalchemy import BigInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.database.base import Base, TZDateTime

USER_STATUS_ACTIVE = "active"
USER_STATUS_BLOCKED = "blocked"



class User(Base):
    """User account entity storing Telegram identity and access gating status."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    age_verified_at: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime,
        nullable=True,
        default=None,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=USER_STATUS_ACTIVE,
        server_default=USER_STATUS_ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def is_age_verified(self) -> bool:
        """Check whether the user has confirmed they are 18 or older."""
        return self.age_verified_at is not None

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"username={self.username!r}, status={self.status!r}, "
            f"verified={self.is_age_verified})>"
        )
