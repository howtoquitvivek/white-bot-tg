"""UploadJob model definition tracking asynchronous video uploads to Telegram."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TZDateTime

if TYPE_CHECKING:
    from app.models.video import Video

UPLOAD_JOB_PENDING = "pending"
UPLOAD_JOB_UPLOADING = "uploading"
UPLOAD_JOB_COMPLETED = "completed"
UPLOAD_JOB_FAILED = "failed"

VALID_UPLOAD_JOB_STATUSES = {
    UPLOAD_JOB_PENDING,
    UPLOAD_JOB_UPLOADING,
    UPLOAD_JOB_COMPLETED,
    UPLOAD_JOB_FAILED,
}


class UploadJob(Base):
    """Tracks background/streaming video upload jobs and progress."""

    __tablename__ = "upload_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UPLOAD_JOB_PENDING,
        server_default=UPLOAD_JOB_PENDING,
        index=True,
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    video_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
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
    video: Mapped[Optional["Video"]] = relationship(
        "Video",
        back_populates="upload_jobs",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UploadJob(id={self.id}, filename={self.original_filename!r}, status={self.status!r}, progress={self.progress})>"

