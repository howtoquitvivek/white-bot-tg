"""AuditLog model definition tracking administrative operations."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid

from sqlalchemy import ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TZDateTime

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser


class AuditLog(Base):
    """Audit log entity recording administrative operations for compliance and security."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    # Stored as column "metadata" in the database while avoiding collision with Base.metadata
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        default=None,
    )

    # Relationships
    admin: Mapped[Optional["AdminUser"]] = relationship(
        "AdminUser",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action!r}, entity={self.entity_type}:{self.entity_id})>"

