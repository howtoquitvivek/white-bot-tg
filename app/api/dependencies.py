"""FastAPI dependencies for database sessions, authentication, and CSRF protection."""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.database.session import create_session_maker, init_db_engine
from app.models.admin_user import AdminUser
from app.security.session import AdminSession, session_store

# Shared engine and session maker instances for the API process
_engine = None
_session_maker = None
DEV_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _get_dev_session() -> AdminSession:
    now = datetime.now(timezone.utc)
    return AdminSession(
        session_id="dev-session-id",
        admin_id=DEV_ADMIN_ID,
        csrf_token="dev-csrf-token",
        created_at=now,
        expires_at=now + timedelta(days=365),
    )


def get_api_session_maker() -> async_sessionmaker[AsyncSession]:
    """Retrieve or initialize the async session maker for FastAPI."""
    global _engine, _session_maker
    if _session_maker is None:
        settings = get_settings()
        _engine = init_db_engine(settings.DATABASE_URL)
        _session_maker = create_session_maker(_engine)
    return _session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active database session for an API request."""
    session_factory = get_api_session_maker()
    async with session_factory() as session:
        yield session


async def get_current_admin_session(request: Request) -> AdminSession:
    """Validate session cookie and return the active AdminSession."""
    settings = get_settings()
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not session_id:
        if not settings.AUTH_REQUIRED:
            return _get_dev_session()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    admin_session = session_store.get_session(session_id)
    if admin_session is None:
        if not settings.AUTH_REQUIRED:
            return _get_dev_session()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    return admin_session


async def get_current_admin(
    admin_session: AdminSession = Depends(get_current_admin_session),
    session: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Validate that the authenticated administrator exists and is active."""
    settings = get_settings()
    admin = await session.get(AdminUser, admin_session.admin_id)

    if not admin:
        if not settings.AUTH_REQUIRED:
            # Check if any active admin exists in DB, or return a dev placeholder
            first_admin_stmt = select(AdminUser).where(AdminUser.is_active == True).limit(1)  # noqa: E712
            res = await session.execute(first_admin_stmt)
            existing = res.scalars().first()
            if existing:
                return existing
            return AdminUser(id=None, username="dev_admin", is_active=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account not found",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is deactivated",
        )

    return admin


async def verify_csrf(
    request: Request,
    admin_session: AdminSession = Depends(get_current_admin_session),
) -> None:
    """Enforce CSRF token verification for state-changing HTTP methods."""
    settings = get_settings()
    if not settings.AUTH_REQUIRED:
        return

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)

        if not csrf_header or not secrets.compare_digest(csrf_header, admin_session.csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid",
            )

