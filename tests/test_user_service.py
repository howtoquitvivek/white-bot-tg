"""Unit tests for user service operations and age gating logic."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import USER_STATUS_ACTIVE, User
from app.services.user_service import (
    UserNotFoundError,
    confirm_age,
    create_user,
    get_user_by_telegram_id,
    register_or_update_user,
)


async def test_create_user(db_session: AsyncSession) -> None:
    """Test creating a new user record."""
    user = await create_user(
        session=db_session,
        telegram_id=123456789,
        username="alice",
        first_name="Alice",
        last_name="Doe",
    )

    assert user.id is not None
    assert user.telegram_id == 123456789
    assert user.username == "alice"
    assert user.first_name == "Alice"
    assert user.last_name == "Doe"
    assert user.status == USER_STATUS_ACTIVE
    assert user.age_verified_at is None
    assert user.is_age_verified is False
    assert user.created_at is not None


async def test_get_user_by_telegram_id(db_session: AsyncSession) -> None:
    """Test looking up a user by Telegram ID."""
    non_existent = await get_user_by_telegram_id(db_session, 999999999)
    assert non_existent is None

    created = await create_user(db_session, telegram_id=555555555, username="bob")
    fetched = await get_user_by_telegram_id(db_session, 555555555)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.username == "bob"


async def test_register_or_update_user_creates_new(db_session: AsyncSession) -> None:
    """Test that register_or_update_user creates a new user when not existing."""
    user = await register_or_update_user(
        session=db_session,
        telegram_id=111222333,
        username="charlie",
        first_name="Charlie",
    )
    assert user.telegram_id == 111222333
    assert user.username == "charlie"


async def test_duplicate_telegram_user_registration_is_idempotent(db_session: AsyncSession) -> None:
    """Test that duplicate registration does not crash and updates user details."""
    # First registration
    user1 = await register_or_update_user(
        session=db_session,
        telegram_id=987654321,
        username="old_username",
        first_name="John",
        last_name="Old",
    )
    user1_id = user1.id

    # Confirm age on user1
    await confirm_age(db_session, 987654321)

    # Second registration with changed profile name
    user2 = await register_or_update_user(
        session=db_session,
        telegram_id=987654321,
        username="new_username",
        first_name="Johnathan",
        last_name="New",
    )

    assert user2.id == user1_id
    assert user2.username == "new_username"
    assert user2.first_name == "Johnathan"
    assert user2.last_name == "New"
    # Age confirmation must be preserved
    assert user2.is_age_verified is True
    assert user2.age_verified_at is not None


async def test_age_confirmation_state(db_session: AsyncSession) -> None:
    """Test that confirm_age records timezone-aware UTC timestamp persistently."""
    user = await create_user(db_session, telegram_id=888777666, username="david")
    assert user.age_verified_at is None
    assert user.is_age_verified is False

    before = datetime.now(timezone.utc)
    verified_user = await confirm_age(db_session, 888777666)
    after = datetime.now(timezone.utc)

    assert verified_user.is_age_verified is True
    assert verified_user.age_verified_at is not None
    assert verified_user.age_verified_at.tzinfo is not None
    assert before <= verified_user.age_verified_at <= after

    # Calling confirm_age again should be idempotent and not change the original timestamp
    original_timestamp = verified_user.age_verified_at
    second_call_user = await confirm_age(db_session, 888777666)
    assert second_call_user.age_verified_at == original_timestamp


async def test_confirm_age_nonexistent_user(db_session: AsyncSession) -> None:
    """Test that confirm_age on nonexistent telegram_id raises UserNotFoundError."""
    with pytest.raises(UserNotFoundError):
        await confirm_age(db_session, 404404404)

