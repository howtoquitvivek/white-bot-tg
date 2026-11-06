"""Video and VideoCategory association model definitions."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TZDateTime

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.collection import CollectionVideo
    from app.models.upload_job import UploadJob

VIDEO_STATUS_DRAFT = "draft"
VIDEO_STATUS_PUBLISHED = "published"
VIDEO_STATUS_ARCHIVED = "archived"

VALID_VIDEO_STATUSES = {VIDEO_STATUS_DRAFT, VIDEO_STATUS_PUBLISHED, VIDEO_STATUS_ARCHIVED}


class VideoCategory(Base):
    """Many-to-many association between Videos and Categories."""

    __tablename__ = "video_categories"

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
    )


class Video(Base):
    """Video catalog entity storing metadata and Telegram storage references."""

    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    telegram_file_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    telegram_file_unique_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    telegram_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        default=None,
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="video/mp4",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=VIDEO_STATUS_DRAFT,
        server_default=VIDEO_STATUS_DRAFT,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime,
        nullable=True,
        default=None,
    )

    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary="video_categories",
        back_populates="videos",
        lazy="selectin",
    )
    collection_items: Mapped[List["CollectionVideo"]] = relationship(
        "CollectionVideo",
        back_populates="video",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    upload_jobs: Mapped[List["UploadJob"]] = relationship(
        "UploadJob",
        back_populates="video",
        lazy="selectin",
    )

    @property
    def is_published(self) -> bool:
        """Check whether the video is in published status."""
        return self.status == VIDEO_STATUS_PUBLISHED

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title={self.title!r}, status={self.status!r})>"

