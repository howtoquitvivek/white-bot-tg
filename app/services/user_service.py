"""User management service containing database queries and lifecycle logic."""

from datetime import datetime, timezone
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when an operation is requested on a non-existent user."""

    pass


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Retrieve a user record by Telegram ID."""
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """Create and persist a new user record."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("Created new user with telegram_id=%d", telegram_id)
    return user


async def register_or_update_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """Idempotently register a new user or update an existing user's profile info."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        return await create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

    # Update metadata if changed
    updated = False
    if user.username != username:
        user.username = username
        updated = True
    if user.first_name != first_name:
        user.first_name = first_name
        updated = True
    if user.last_name != last_name:
        user.last_name = last_name
        updated = True

    if updated:
        await session.commit()
        await session.refresh(user)
        logger.info("Updated profile for telegram_id=%d", telegram_id)

    return user


async def confirm_age(session: AsyncSession, telegram_id: int) -> User:
    """Record that the user has confirmed they are 18 or older with a UTC timestamp."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        raise UserNotFoundError(f"User with telegram_id={telegram_id} not found.")

    if user.age_verified_at is None:
        user.age_verified_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)
        logger.info("Age confirmed for telegram_id=%d at %s", telegram_id, user.age_verified_at)

    return user

