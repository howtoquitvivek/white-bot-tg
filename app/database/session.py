"""Asynchronous database engine and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when the database connection check fails."""

    pass


def init_db_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """Initialize and configure the asynchronous SQLAlchemy engine."""
    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
    )


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a configured async session factory bound to the engine."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def check_database_connection(engine: AsyncEngine, timeout_seconds: float = 5.0) -> bool:
    """Verify that PostgreSQL is reachable and accepting queries.

    Raises DatabaseConnectionError if connection cannot be established.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity check succeeded.")
        return True
    except (SQLAlchemyError, OSError) as exc:
        err_msg = (
            f"Failed to connect to the database. Ensure PostgreSQL is running and accessible. "
            f"Details: {exc}"
        )
        logger.error(err_msg)
        raise DatabaseConnectionError(err_msg) from exc


async def close_database(engine: Optional[AsyncEngine]) -> None:
    """Gracefully dispose of the engine and close active connection pools."""
    if engine is not None:
        logger.info("Disposing database connection pool...")
        await engine.dispose()
        logger.info("Database connection pool disposed.")


@asynccontextmanager
async def get_db_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous transactional database session scope."""
    session = session_maker()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

