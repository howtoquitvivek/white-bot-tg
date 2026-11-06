"""Collection and CollectionVideo association model definitions."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TZDateTime

if TYPE_CHECKING:
    from app.models.video import Video

COLLECTION_STATUS_DRAFT = "draft"
COLLECTION_STATUS_PUBLISHED = "published"
COLLECTION_STATUS_ARCHIVED = "archived"

VALID_COLLECTION_STATUSES = {
    COLLECTION_STATUS_DRAFT,
    COLLECTION_STATUS_PUBLISHED,
    COLLECTION_STATUS_ARCHIVED,
}


class CollectionVideo(Base):
    """Association model linking Videos to Collections with ordering."""

    __tablename__ = "collection_videos"

    collection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="collection_videos",
        lazy="selectin",
    )
    video: Mapped["Video"] = relationship(
        "Video",
        back_populates="collection_items",
        lazy="selectin",
    )


class Collection(Base):
    """Collection entity representing a curated group of videos."""

    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    cover_video_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=COLLECTION_STATUS_DRAFT,
        server_default=COLLECTION_STATUS_DRAFT,
        index=True,
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

    # Relationships
    collection_videos: Mapped[List[CollectionVideo]] = relationship(
        "CollectionVideo",
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionVideo.position",
        lazy="selectin",
    )
    cover_video: Mapped[Optional["Video"]] = relationship(
        "Video",
        foreign_keys=[cover_video_id],
        lazy="selectin",
    )

    @property
    def is_published(self) -> bool:
        """Check whether the collection is published."""
        return self.status == COLLECTION_STATUS_PUBLISHED

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, title={self.title!r}, status={self.status!r})>"

