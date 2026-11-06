"""Audit log service for recording administrative operations."""

from typing import Any, Dict, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_audit_log(
    session: AsyncSession,
    admin_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Record an administrative action into the audit_logs table."""
    # Ensure foreign key validity for admin_id
    valid_admin_id = None
    if admin_id:
        from app.models.admin_user import AdminUser
        admin_record = await session.get(AdminUser, admin_id)
        if admin_record:
            valid_admin_id = admin_record.id

    audit = AuditLog(
        admin_id=valid_admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        extra_metadata=metadata,
    )
    session.add(audit)
    await session.commit()
    await session.refresh(audit)
    return audit

