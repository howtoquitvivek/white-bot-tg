"""Test configuration, fixtures, and in-memory test database."""

from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies import get_db
from app.api.main import app as fastapi_app
from app.database.base import Base
import app.models as app_models  # noqa: F401
from app.security.password import hash_password
from app.security.rate_limiter import login_rate_limiter
from app.security.session import session_store


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an isolated in-memory SQLite async engine with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test database session."""
    session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
def reset_security_stores(monkeypatch) -> None:
    """Clear session store, rate limiter, and ensure AUTH_REQUIRED is True for tests."""
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    from app.config import get_settings
    get_settings.cache_clear()
    session_store.clear()
    login_rate_limiter.clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an HTTP test client with database dependency overridden."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> app_models.AdminUser:
    """Create a default active administrator for testing."""
    admin = app_models.AdminUser(
        username="admin_test",
        password_hash=hash_password("SuperSecret123!"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin
