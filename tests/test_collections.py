"""Unit tests for Collections browsing, pagination, and video access in the Telegram bot."""

from typing import Optional
from unittest.mock import AsyncMock, MagicMock
import uuid

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, User as TgUser
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.catalog import (
    handle_collection_list_callback,
    handle_collection_video_page_callback,
    handle_collection_view_callback,
    handle_collections,
)
from app.handlers.constants import AGE_GATE_TEXT
from app.handlers.start import handle_start
from app.keyboards.catalog import (
    CB_COLLECTION_LIST,
    CB_COLLECTION_PAGE,
    CB_COLLECTION_VIEW,
    CB_MAIN_MENU,
    CB_VIDEO_VIEW,
)
from app.keyboards.main_menu import BTN_COLLECTIONS
from app.models.collection import (
    COLLECTION_STATUS_DRAFT,
    COLLECTION_STATUS_PUBLISHED,
    Collection,
    CollectionVideo,
)
from app.models.video import (
    VIDEO_STATUS_ARCHIVED,
    VIDEO_STATUS_DRAFT,
    VIDEO_STATUS_PUBLISHED,
    Video,
)
from app.services.user_service import confirm_age


def make_mock_message(user_id: int, username: str = "testuser", text: str = BTN_COLLECTIONS) -> Message:
    """Helper to create a mocked aiogram Message."""
    msg = MagicMock(spec=Message)
    user = MagicMock(spec=TgUser)
    user.id = user_id
    user.username = username
    user.first_name = "Test"
    user.last_name = "User"
    msg.from_user = user
    msg.text = text
    msg.answer = AsyncMock()
    return msg


def make_mock_callback(user_id: int, data: str) -> CallbackQuery:
    """Helper to create a mocked aiogram CallbackQuery."""
    cb = MagicMock(spec=CallbackQuery)
    user = MagicMock(spec=TgUser)
    user.id = user_id
    cb.from_user = user
    cb.data = data
    cb.answer = AsyncMock()

    inner_msg = MagicMock(spec=Message)
    chat = MagicMock()
    chat.id = user_id
    inner_msg.chat = chat
    inner_msg.edit_text = AsyncMock()
    inner_msg.answer = AsyncMock()
    cb.message = inner_msg
    return cb


async def setup_verified_user(db_session: AsyncSession, user_id: int) -> None:
    """Helper to register and age-verify a test user."""
    msg = make_mock_message(user_id=user_id)
    await handle_start(msg, db_session)
    await confirm_age(db_session, user_id)


async def test_browse_collections_empty(db_session: AsyncSession) -> None:
    """Test Browse Collections when no collections exist displays empty prompt."""
    user_id = 4001
    await setup_verified_user(db_session, user_id)

    msg = make_mock_message(user_id=user_id, text=BTN_COLLECTIONS)
    await handle_collections(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert "no collections available" in args[0]
    reply_markup = kwargs.get("reply_markup")
    assert isinstance(reply_markup, InlineKeyboardMarkup)
    assert any(btn.callback_data == CB_MAIN_MENU for row in reply_markup.inline_keyboard for btn in row)


async def test_browse_collections_shows_published_with_counts(db_session: AsyncSession) -> None:
    """Test Browse Collections displays published collections with published video counts."""
    user_id = 4002
    await setup_verified_user(db_session, user_id)

    # Create published collection 1
    c1 = Collection(
        id=uuid.uuid4(),
        title="Best of 2026",
        description="Top highlights of the year",
        status=COLLECTION_STATUS_PUBLISHED,
    )
    # Create draft collection 2 (should not appear in public bot)
    c2 = Collection(
        id=uuid.uuid4(),
        title="Hidden Drafts",
        status=COLLECTION_STATUS_DRAFT,
    )
    db_session.add_all([c1, c2])
    await db_session.flush()

    # Create 2 published videos and 1 draft video in collection 1
    v1 = Video(
        id=uuid.uuid4(),
        title="Highlight One",
        status=VIDEO_STATUS_PUBLISHED,
        telegram_file_id="tg_v1",
        telegram_file_unique_id="uniq_v1",
    )
    v2 = Video(
        id=uuid.uuid4(),
        title="Highlight Two",
        status=VIDEO_STATUS_PUBLISHED,
        telegram_file_id="tg_v2",
        telegram_file_unique_id="uniq_v2",
    )
    v3 = Video(
        id=uuid.uuid4(),
        title="Highlight Draft",
        status=VIDEO_STATUS_DRAFT,
        telegram_file_id="tg_v3",
        telegram_file_unique_id="uniq_v3",
    )
    db_session.add_all([v1, v2, v3])
    await db_session.flush()

    cv1 = CollectionVideo(collection_id=c1.id, video_id=v1.id, position=0)
    cv2 = CollectionVideo(collection_id=c1.id, video_id=v2.id, position=1)
    cv3 = CollectionVideo(collection_id=c1.id, video_id=v3.id, position=2)
    db_session.add_all([cv1, cv2, cv3])
    await db_session.commit()

    msg = make_mock_message(user_id=user_id, text=BTN_COLLECTIONS)
    await handle_collections(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert "Collections" in args[0]
    assert "Showing 1–1 of 1" in args[0]

    reply_markup = kwargs.get("reply_markup")
    assert isinstance(reply_markup, InlineKeyboardMarkup)

    # Collection button must show title and count of published videos only (2, not 3)
    coll_btn = reply_markup.inline_keyboard[0][0]
    assert "Best of 2026" in coll_btn.text
    assert "(2)" in coll_btn.text
    assert coll_btn.callback_data == f"{CB_COLLECTION_VIEW}:{c1.id}"


async def test_select_collection_shows_only_published_videos(db_session: AsyncSession) -> None:
    """Test clicking a collection displays its published videos in correct order."""
    user_id = 4003
    await setup_verified_user(db_session, user_id)

    coll = Collection(
        id=uuid.uuid4(),
        title="Action Classics",
        description="Iconic action scenes",
        status=COLLECTION_STATUS_PUBLISHED,
    )
    db_session.add(coll)
    await db_session.flush()

    v_pub1 = Video(
        id=uuid.uuid4(),
        title="Chase Scene",
        status=VIDEO_STATUS_PUBLISHED,
        telegram_file_id="tg_chase",
        telegram_file_unique_id="u_chase",
    )
    v_draft = Video(
        id=uuid.uuid4(),
        title="Secret Cut",
        status=VIDEO_STATUS_DRAFT,
        telegram_file_id="tg_cut",
        telegram_file_unique_id="u_cut",
    )
    v_pub2 = Video(
        id=uuid.uuid4(),
        title="Final Showdown",
        status=VIDEO_STATUS_PUBLISHED,
        telegram_file_id="tg_final",
        telegram_file_unique_id="u_final",
    )
    db_session.add_all([v_pub1, v_draft, v_pub2])
    await db_session.flush()

    # Ordered: Chase Scene (0), Secret Cut (1), Final Showdown (2)
    db_session.add(CollectionVideo(collection_id=coll.id, video_id=v_pub1.id, position=0))
    db_session.add(CollectionVideo(collection_id=coll.id, video_id=v_draft.id, position=1))
    db_session.add(CollectionVideo(collection_id=coll.id, video_id=v_pub2.id, position=2))
    await db_session.commit()

    cb = make_mock_callback(user_id=user_id, data=f"{CB_COLLECTION_VIEW}:{coll.id}")
    await handle_collection_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    assert cb.message is not None
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args

    # Check header and description
    assert "Action Classics" in args[0]
    assert "Iconic action scenes" in args[0]
    assert "Showing 1–2 of 2" in args[0]

    reply_markup = kwargs.get("reply_markup")
    assert isinstance(reply_markup, InlineKeyboardMarkup)

    # First row is Chase Scene, second row is Final Showdown (Secret Cut excluded!)
    btn1 = reply_markup.inline_keyboard[0][0]
    btn2 = reply_markup.inline_keyboard[1][0]
    assert "Chase Scene" in btn1.text
    assert btn1.callback_data == f"{CB_VIDEO_VIEW}:{v_pub1.id}"
    assert "Final Showdown" in btn2.text
    assert btn2.callback_data == f"{CB_VIDEO_VIEW}:{v_pub2.id}"

    # Bottom navigation
    bottom_row = reply_markup.inline_keyboard[-1]
    assert any("Back to Collections" in b.text for b in bottom_row)
    assert any("Main Menu" in b.text for b in bottom_row)


async def test_select_empty_collection_graceful(db_session: AsyncSession) -> None:
    """Test viewing a published collection with 0 published videos shows graceful empty message."""
    user_id = 4004
    await setup_verified_user(db_session, user_id)

    coll = Collection(
        id=uuid.uuid4(),
        title="Empty Collection",
        description="Nothing here yet",
        status=COLLECTION_STATUS_PUBLISHED,
    )
    db_session.add(coll)
    await db_session.commit()

    cb = make_mock_callback(user_id=user_id, data=f"{CB_COLLECTION_VIEW}:{coll.id}")
    await handle_collection_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    assert cb.message is not None
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args
    assert "Empty Collection" in args[0]
    assert "no published videos in this collection" in args[0]

    reply_markup = kwargs.get("reply_markup")
    assert isinstance(reply_markup, InlineKeyboardMarkup)
    assert any(b.callback_data == CB_COLLECTION_LIST for row in reply_markup.inline_keyboard for b in row)


async def test_deleted_or_invalid_collection_safe(db_session: AsyncSession) -> None:
    """Test viewing a deleted or invalid collection safely triggers alert."""
    user_id = 4005
    await setup_verified_user(db_session, user_id)

    # Non-existent UUID
    random_id = uuid.uuid4()
    cb = make_mock_callback(user_id=user_id, data=f"{CB_COLLECTION_VIEW}:{random_id}")
    await handle_collection_view_callback(cb, db_session)

    cb.answer.assert_called_once_with("⚠️ This collection is no longer available.", show_alert=True)

    # Malformed UUID
    cb2 = make_mock_callback(user_id=user_id, data=f"{CB_COLLECTION_VIEW}:not-a-uuid")
    await handle_collection_view_callback(cb2, db_session)
    cb2.answer.assert_called_once_with("⚠️ Invalid collection request.", show_alert=True)


async def test_collection_navigation_back_and_main_menu(db_session: AsyncSession) -> None:
    """Test collection list callback navigation and refreshing."""
    user_id = 4006
    await setup_verified_user(db_session, user_id)

    coll = Collection(
        id=uuid.uuid4(),
        title="Series One",
        status=COLLECTION_STATUS_PUBLISHED,
    )
    db_session.add(coll)
    await db_session.commit()

    cb = make_mock_callback(user_id=user_id, data=CB_COLLECTION_LIST)
    await handle_collection_list_callback(cb, db_session)

    cb.answer.assert_called_once()
    assert cb.message is not None
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args
    assert "Collections" in args[0]
    assert "Series One" in args[0] or any(
        "Series One" in btn.text
        for row in kwargs.get("reply_markup").inline_keyboard
        for btn in row
    )


async def test_collection_video_pagination(db_session: AsyncSession) -> None:
    """Test pagination for collections with more than 10 published videos."""
    user_id = 4007
    await setup_verified_user(db_session, user_id)

    coll = Collection(
        id=uuid.uuid4(),
        title="Mega Series",
        status=COLLECTION_STATUS_PUBLISHED,
    )
    db_session.add(coll)
    await db_session.flush()

    videos = []
    for i in range(15):
        v = Video(
            id=uuid.uuid4(),
            title=f"Episode {i + 1:02d}",
            status=VIDEO_STATUS_PUBLISHED,
            telegram_file_id=f"tg_{i}",
            telegram_file_unique_id=f"uniq_{i}",
        )
        videos.append(v)
    db_session.add_all(videos)
    await db_session.flush()

    for idx, v in enumerate(videos):
        db_session.add(CollectionVideo(collection_id=coll.id, video_id=v.id, position=idx))
    await db_session.commit()

    # Page 0 (items 1-10)
    cb0 = make_mock_callback(user_id=user_id, data=f"{CB_COLLECTION_VIEW}:{coll.id}")
    await handle_collection_view_callback(cb0, db_session)
    args0, kwargs0 = cb0.message.edit_text.call_args
    assert "Showing 1–10 of 15" in args0[0]
    kb0 = kwargs0.get("reply_markup")
    assert any(f"{CB_COLLECTION_PAGE}:{coll.id}:1" in btn.callback_data for row in kb0.inline_keyboard for btn in row)

    # Page 1 (items 11-15)
    cb1 = make_mock_callback(user_id=user_id, data=f"{CB_COLLECTION_PAGE}:{coll.id}:1")
    await handle_collection_video_page_callback(cb1, db_session)
    args1, kwargs1 = cb1.message.edit_text.call_args
    assert "Showing 11–15 of 15" in args1[0]
    kb1 = kwargs1.get("reply_markup")
    assert any(f"{CB_COLLECTION_PAGE}:{coll.id}:0" in btn.callback_data for row in kb1.inline_keyboard for btn in row)


async def test_collection_unverified_user_blocked(db_session: AsyncSession) -> None:
    """Test that unverified users cannot access collections."""
    unverified_id = 4008
    # User exists but not age-verified
    msg_start = make_mock_message(user_id=unverified_id)
    await handle_start(msg_start, db_session)

    msg = make_mock_message(user_id=unverified_id, text=BTN_COLLECTIONS)
    await handle_collections(msg, db_session)

    msg.answer.assert_called_once()
    assert AGE_GATE_TEXT in msg.answer.call_args[0][0]

    cb = make_mock_callback(user_id=unverified_id, data=CB_COLLECTION_LIST)
    await handle_collection_list_callback(cb, db_session)
    cb.answer.assert_called_once_with("⚠️ Age verification required.", show_alert=True)
