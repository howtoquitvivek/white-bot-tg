"""Unit tests for Milestone 6: Help section, About section, navigation consistency, and callback error handling."""

from unittest.mock import AsyncMock, MagicMock
import uuid

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, User as TgUser
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.handlers.catalog import (
    handle_about_callback,
    handle_help_callback,
    handle_unknown_or_outdated_callback,
    handle_video_view_callback,
)
from app.handlers.constants import (
    DEFAULT_ABOUT_TEXT,
    HELP_TEXT,
    get_about_text,
)
from app.handlers.start import (
    handle_about,
    handle_help,
    handle_start,
)
from app.keyboards.catalog import (
    CB_ABOUT,
    CB_CATEGORY_LIST,
    CB_COLLECTION_LIST,
    CB_HELP,
    CB_MAIN_MENU,
    CB_VIDEO_VIEW,
    build_about_keyboard,
    build_category_list_keyboard,
    build_collection_list_keyboard,
    build_empty_catalog_keyboard,
    build_empty_categories_keyboard,
    build_empty_category_videos_keyboard,
    build_empty_collection_videos_keyboard,
    build_empty_collections_keyboard,
    build_help_keyboard,
    build_video_catalog_keyboard,
    build_video_detail_keyboard,
)
from app.keyboards.main_menu import get_main_menu_keyboard
from app.models.category import Category
from app.models.video import VIDEO_STATUS_PUBLISHED, Video
from app.services.user_service import confirm_age


def make_mock_message(user_id: int, username: str = "testuser", text: str = "/help") -> Message:
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


def make_mock_callback(user_id: int, data: str, bot=None) -> CallbackQuery:
    """Helper to create a mocked aiogram CallbackQuery."""
    cb = MagicMock(spec=CallbackQuery)
    user = MagicMock(spec=TgUser)
    user.id = user_id
    cb.from_user = user
    cb.data = data
    cb.answer = AsyncMock()
    cb.bot = bot or MagicMock()

    inner_msg = MagicMock(spec=Message)
    inner_msg.edit_text = AsyncMock()
    inner_msg.answer = AsyncMock()
    cb.message = inner_msg
    return cb


async def setup_verified_user(session: AsyncSession, user_id: int) -> None:
    """Helper to register and verify user."""
    msg = make_mock_message(user_id=user_id)
    await handle_start(msg, session)
    await confirm_age(session, user_id)


# -----------------------------------------------------------------------------
# 1. Help Section Tests
# -----------------------------------------------------------------------------

async def test_help_section_content_and_explanations(db_session: AsyncSession) -> None:
    """Verify that the Help section explains all required interactions."""
    user_id = 5001
    await setup_verified_user(db_session, user_id)

    msg = make_mock_message(user_id=user_id, text="/help")
    await handle_help(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    help_content = args[0].lower()

    # Requirement 1: Explaining all required items
    assert "how to browse categories" in help_content or "browse categories" in help_content
    assert "categories" in help_content
    assert "collections" in help_content
    assert "select" in help_content and "receive" in help_content
    assert "main menu" in help_content

    # Verified users get the persistent reply keyboard
    assert kwargs.get("reply_markup") == get_main_menu_keyboard()


async def test_help_inline_callback_navigation(db_session: AsyncSession) -> None:
    """Verify that clicking the inline Help button updates the view to the Help guide."""
    user_id = 5002
    await setup_verified_user(db_session, user_id)

    cb = make_mock_callback(user_id=user_id, data=CB_HELP)
    await handle_help_callback(cb, db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args

    assert "About & Help Guide" in args[0]
    keyboard = kwargs.get("reply_markup")
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Check that Help keyboard has cross-navigation
    callbacks = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert CB_CATEGORY_LIST in callbacks
    assert CB_COLLECTION_LIST in callbacks
    assert CB_ABOUT in callbacks
    assert CB_MAIN_MENU in callbacks


# -----------------------------------------------------------------------------
# 2. About Section Tests
# -----------------------------------------------------------------------------

async def test_about_section_default_content(db_session: AsyncSession) -> None:
    """Verify /about command displays the default factual platform information."""
    user_id = 5003
    await setup_verified_user(db_session, user_id)

    msg = make_mock_message(user_id=user_id, text="/about")
    await handle_about(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    about_content = args[0]

    assert "About Video Platform" in about_content
    assert "18+" in about_content
    assert "authorized" in about_content.lower()

    keyboard = kwargs.get("reply_markup")
    assert isinstance(keyboard, InlineKeyboardMarkup)
    callbacks = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert CB_CATEGORY_LIST in callbacks
    assert CB_COLLECTION_LIST in callbacks
    assert CB_HELP in callbacks
    assert CB_MAIN_MENU in callbacks


async def test_about_section_custom_content_configurable(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that custom about text can be configured via environment settings."""
    user_id = 5004
    await setup_verified_user(db_session, user_id)

    custom_text = "Custom Studio Platform — Authorized original content."
    monkeypatch.setenv("BOT_ABOUT_TEXT", custom_text)
    get_settings.cache_clear()

    msg = make_mock_message(user_id=user_id, text="/about")
    await handle_about(msg, db_session)

    args, _ = msg.answer.call_args
    assert custom_text in args[0]

    get_settings.cache_clear()


async def test_about_inline_callback_navigation(db_session: AsyncSession) -> None:
    """Verify clicking the inline About button updates the view to the About screen."""
    user_id = 5005
    await setup_verified_user(db_session, user_id)

    cb = make_mock_callback(user_id=user_id, data=CB_ABOUT)
    await handle_about_callback(cb, db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args
    assert "About Video Platform" in args[0]

    keyboard = kwargs.get("reply_markup")
    callbacks = [b.callback_data for row in keyboard.inline_keyboard for b in row]
    assert CB_HELP in callbacks
    assert CB_MAIN_MENU in callbacks


# -----------------------------------------------------------------------------
# 3. Age Verification Gating for Help and About Callbacks
# -----------------------------------------------------------------------------

async def test_help_and_about_callbacks_blocked_for_unverified_user(db_session: AsyncSession) -> None:
    """Verify unverified users attempting callback access are blocked with the age gate."""
    unverified_id = 5006
    # Not verified!

    for cb_data, handler in [(CB_HELP, handle_help_callback), (CB_ABOUT, handle_about_callback)]:
        cb = make_mock_callback(user_id=unverified_id, data=cb_data)
        await handler(cb, db_session)

        cb.answer.assert_called_once_with("⚠️ Age verification required.", show_alert=True)
        cb.message.edit_text.assert_not_called()


# -----------------------------------------------------------------------------
# 4. Consistent Navigation Across All Major Keyboards
# -----------------------------------------------------------------------------

def test_consistent_navigation_across_all_keyboards() -> None:
    """Test that all major section keyboards offer consistent cross-navigation."""
    fake_cat_id = uuid.uuid4()
    fake_col_id = uuid.uuid4()

    keyboards_to_test = [
        ("Help", build_help_keyboard()),
        ("About", build_about_keyboard()),
        ("Category List", build_category_list_keyboard([], 0, 0)),
        ("Collection List", build_collection_list_keyboard([], 0, 0)),
        ("Empty Categories", build_empty_categories_keyboard()),
        ("Empty Collections", build_empty_collections_keyboard()),
        ("Empty Category Videos", build_empty_category_videos_keyboard(fake_cat_id)),
        ("Empty Collection Videos", build_empty_collection_videos_keyboard(fake_col_id)),
        ("Video Catalog (in category)", build_video_catalog_keyboard([], 0, 0, category_id=fake_cat_id)),
        ("Video Catalog (in collection)", build_video_catalog_keyboard([], 0, 0, collection_id=fake_col_id)),
        ("Video Detail (category)", build_video_detail_keyboard(category_id=fake_cat_id)),
        ("Video Detail (collection)", build_video_detail_keyboard(collection_id=fake_col_id)),
    ]

    for name, kb in keyboards_to_test:
        all_callbacks = [b.callback_data for row in kb.inline_keyboard for b in row]

        # Every keyboard must have Main Menu navigation
        assert CB_MAIN_MENU in all_callbacks, f"{name} keyboard missing Main Menu button"

        # Keyboards must have category, collection, or help cross-links
        has_cross_nav = any(
            cb in all_callbacks
            for cb in [CB_CATEGORY_LIST, CB_COLLECTION_LIST, CB_HELP, CB_ABOUT]
        )
        assert has_cross_nav, f"{name} keyboard missing cross-navigation buttons"


# -----------------------------------------------------------------------------
# 5. Outdated and Invalid Callback Handling
# -----------------------------------------------------------------------------

async def test_unknown_or_outdated_callback_graceful_handling() -> None:
    """Test that an outdated, malformed, or unrecognized callback query is answered with an alert."""
    cb = make_mock_callback(user_id=5007, data="outdated_callback_from_old_version:123")
    await handle_unknown_or_outdated_callback(cb)

    cb.answer.assert_called_once()
    args, kwargs = cb.answer.call_args
    assert kwargs.get("show_alert") is True
    assert "expired" in args[0].lower() or "no longer valid" in args[0].lower()


async def test_missing_video_media_file_handled_gracefully(db_session: AsyncSession) -> None:
    """Test that a video with missing telegram_file_id shows an alert and friendly message."""
    user_id = 5008
    await setup_verified_user(db_session, user_id)

    # Video without telegram_file_id
    vid = Video(title="Corrupt Video", telegram_file_id=None, status=VIDEO_STATUS_PUBLISHED)
    db_session.add(vid)
    await db_session.commit()
    await db_session.refresh(vid)

    cb = make_mock_callback(user_id=user_id, data=f"{CB_VIDEO_VIEW}:{vid.id}")
    await handle_video_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    assert cb.answer.call_args[1].get("show_alert") is True
    assert "unavailable" in cb.answer.call_args[0][0].lower()

