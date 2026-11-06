"""Authentication routes: login, logout, and current admin profile."""

from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_current_admin_session, get_db
from app.api.schemas.auth import AdminResponse, LoginRequest, LoginResponse, MessageResponse
from app.config import get_settings
from app.models.admin_user import AdminUser
from app.security.password import verify_password
from app.security.rate_limiter import login_rate_limiter
from app.security.session import AdminSession, session_store
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate administrator, establish server-side session and issue secure cookies."""
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"{client_ip}:{payload.username.lower()}"

    # Rate limiting check
    if login_rate_limiter.is_rate_limited(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again in a few minutes.",
        )

    # Fetch admin
    stmt = select(AdminUser).where(AdminUser.username == payload.username.strip())
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(payload.password, admin.password_hash):
        login_rate_limiter.record_failure(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not admin.is_active:
        login_rate_limiter.record_failure(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is deactivated",
        )

    # Success: reset rate limiter
    login_rate_limiter.reset(rate_limit_key)

    # Create server-side session
    admin_session = session_store.create_session(admin.id)

    # Update last login timestamp
    admin.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(admin)

    # Audit logging
    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="admin.login",
        entity_type="admin_user",
        entity_id=str(admin.id),
        metadata={"ip": client_ip, "user_agent": request.headers.get("user-agent")},
    )

    # Set secure cookies
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=admin_session.session_id,
        httponly=True,
        samesite="lax",
        secure=settings.SECURE_COOKIES,
        path="/",
        max_age=86400 * 7,
    )
    # CSRF cookie is non-httponly so browser frontend JS can read and send in header
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=admin_session.csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.SECURE_COOKIES,
        path="/",
        max_age=86400 * 7,
    )

    return LoginResponse(
        admin=AdminResponse.model_validate(admin),
        csrf_token=admin_session.csrf_token,
        message="Login successful",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    admin_session: AdminSession = Depends(get_current_admin_session),
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Invalidate current administrator session and clear cookies."""
    settings = get_settings()

    # Invalidate session in store
    session_store.invalidate_session(admin_session.session_id)

    # Audit log
    await create_audit_log(
        session=session,
        admin_id=admin.id,
        action="admin.logout",
        entity_type="admin_user",
        entity_id=str(admin.id),
    )

    # Clear cookies
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")

    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=AdminResponse)
async def get_me(admin: AdminUser = Depends(get_current_admin)) -> AdminResponse:
    """Retrieve profile of the currently authenticated administrator."""
    return AdminResponse.model_validate(admin)

