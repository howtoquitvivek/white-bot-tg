"""Comprehensive unit tests for Category-based video browsing, pagination, and video delivery."""

from typing import Optional
from unittest.mock import AsyncMock, MagicMock
import uuid

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, User as TgUser
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.catalog import (
    handle_browse_videos,
    handle_catalog_page_callback,
    handle_category_list_callback,
    handle_category_video_page_callback,
    handle_category_view_callback,
    handle_main_menu_callback,
    handle_noop_callback,
    handle_video_view_callback,
)
from app.handlers.start import handle_start
from app.keyboards.catalog import (
    CB_CATEGORY_LIST,
    CB_CATEGORY_PAGE,
    CB_CATEGORY_VIEW,
    CB_MAIN_MENU,
    CB_NOOP,
    CB_VIDEO_VIEW,
    build_category_list_keyboard,
    build_empty_categories_keyboard,
    build_empty_category_videos_keyboard,
    build_video_catalog_keyboard,
    build_video_detail_keyboard,
)
from app.keyboards.main_menu import BTN_BROWSE_VIDEOS, get_main_menu_keyboard
from app.models.category import Category
from app.models.video import (
    VIDEO_STATUS_ARCHIVED,
    VIDEO_STATUS_DRAFT,
    VIDEO_STATUS_PUBLISHED,
    Video,
    VideoCategory,
)
from app.services.user_service import confirm_age


def make_mock_message(user_id: int, username: str = "testuser", text: str = BTN_BROWSE_VIDEOS) -> Message:
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


def make_mock_callback(user_id: int, data: str, bot: Optional[MagicMock] = None) -> CallbackQuery:
    """Helper to create a mocked aiogram CallbackQuery with attached Bot."""
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

    cb.bot = bot or MagicMock()
    if bot is None:
        cb.bot.send_video = AsyncMock()
    return cb


async def setup_verified_user(db_session: AsyncSession, user_id: int) -> None:
    """Helper to register and age-verify a test user."""
    msg = make_mock_message(user_id=user_id)
    await handle_start(msg, db_session)
    await confirm_age(db_session, user_id)


async def test_browse_videos_empty_categories(db_session: AsyncSession) -> None:
    """Test Browse Videos when no categories exist displays empty prompt."""
    user_id = 3001
    await setup_verified_user(db_session, user_id)

    msg = make_mock_message(user_id=user_id, text=BTN_BROWSE_VIDEOS)
    await handle_browse_videos(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert "no video categories available" in args[0].lower()
    assert kwargs.get("reply_markup") == build_empty_categories_keyboard()


async def test_browse_videos_shows_categories_with_published_counts(db_session: AsyncSession) -> None:
    """Test that categories are listed with correct published video counts."""
    user_id = 3002
    await setup_verified_user(db_session, user_id)

    # 1. Category Action with 2 published videos and 1 draft
    cat_action = Category(name="Action", slug="action")
    # 2. Category Comedy with 1 published video
    cat_comedy = Category(name="Comedy", slug="comedy")
    # 3. Category Drama with 0 videos
    cat_drama = Category(name="Drama", slug="drama")
    db_session.add_all([cat_action, cat_comedy, cat_drama])
    await db_session.flush()

    v_act1 = Video(title="Action 1", telegram_file_id="tg_act1", status=VIDEO_STATUS_PUBLISHED)
    v_act2 = Video(title="Action 2", telegram_file_id="tg_act2", status=VIDEO_STATUS_PUBLISHED)
    v_act_draft = Video(title="Action Draft", telegram_file_id="tg_act_draft", status=VIDEO_STATUS_DRAFT)
    v_com1 = Video(title="Comedy 1", telegram_file_id="tg_com1", status=VIDEO_STATUS_PUBLISHED)
    db_session.add_all([v_act1, v_act2, v_act_draft, v_com1])
    await db_session.flush()

    db_session.add_all([
        VideoCategory(video_id=v_act1.id, category_id=cat_action.id),
        VideoCategory(video_id=v_act2.id, category_id=cat_action.id),
        VideoCategory(video_id=v_act_draft.id, category_id=cat_action.id),
        VideoCategory(video_id=v_com1.id, category_id=cat_comedy.id),
    ])
    await db_session.commit()

    # User triggers Browse Videos
    msg = make_mock_message(user_id=user_id, text=BTN_BROWSE_VIDEOS)
    await handle_browse_videos(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert "Browse Videos — Categories" in args[0]
    keyboard = kwargs.get("reply_markup")
    assert isinstance(keyboard, InlineKeyboardMarkup)

    all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    btn_dict = {btn.callback_data: btn.text for btn in all_buttons}

    # Verify category buttons and counts
    assert f"{CB_CATEGORY_VIEW}:{cat_action.id}" in btn_dict
    assert "Action (2)" in btn_dict[f"{CB_CATEGORY_VIEW}:{cat_action.id}"]

    assert f"{CB_CATEGORY_VIEW}:{cat_comedy.id}" in btn_dict
    assert "Comedy (1)" in btn_dict[f"{CB_CATEGORY_VIEW}:{cat_comedy.id}"]

    assert f"{CB_CATEGORY_VIEW}:{cat_drama.id}" in btn_dict
    assert "Drama (0)" in btn_dict[f"{CB_CATEGORY_VIEW}:{cat_drama.id}"]

    # Verify Main Menu button is present
    assert CB_MAIN_MENU in btn_dict


async def test_category_selection_displays_published_videos(db_session: AsyncSession) -> None:
    """Test clicking a category displays its published videos only."""
    user_id = 3003
    await setup_verified_user(db_session, user_id)

    cat = Category(name="Sci-Fi", slug="sci-fi", description="Futuristic and science fiction movies")
    db_session.add(cat)
    await db_session.flush()

    v_pub = Video(title="Interstellar", telegram_file_id="tg_pub", status=VIDEO_STATUS_PUBLISHED, duration=150)
    v_draft = Video(title="Draft SciFi", telegram_file_id="tg_draft", status=VIDEO_STATUS_DRAFT)
    v_arch = Video(title="Archived SciFi", telegram_file_id="tg_arch", status=VIDEO_STATUS_ARCHIVED)
    db_session.add_all([v_pub, v_draft, v_arch])
    await db_session.flush()

    db_session.add_all([
        VideoCategory(video_id=v_pub.id, category_id=cat.id),
        VideoCategory(video_id=v_draft.id, category_id=cat.id),
        VideoCategory(video_id=v_arch.id, category_id=cat.id),
    ])
    await db_session.commit()

    cb = make_mock_callback(user_id=user_id, data=f"{CB_CATEGORY_VIEW}:{cat.id}")
    await handle_category_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args
    assert "Sci-Fi" in args[0]
    assert "Showing 1–1 of 1" in args[0]

    keyboard = kwargs.get("reply_markup")
    assert isinstance(keyboard, InlineKeyboardMarkup)
    all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    btn_dict = {btn.callback_data: btn.text for btn in all_buttons}

    # Published video must be visible
    assert f"{CB_VIDEO_VIEW}:{v_pub.id}" in btn_dict
    assert "Interstellar" in btn_dict[f"{CB_VIDEO_VIEW}:{v_pub.id}"]

    # Draft & Archived must NOT be visible
    assert not any("Draft SciFi" in t for t in btn_dict.values())
    assert not any("Archived SciFi" in t for t in btn_dict.values())

    # Back to Categories and Main Menu navigation buttons must be present
    assert CB_CATEGORY_LIST in btn_dict
    assert CB_MAIN_MENU in btn_dict


async def test_empty_category_handled_gracefully(db_session: AsyncSession) -> None:
    """Test clicking a category with zero published videos shows friendly empty state."""
    user_id = 3004
    await setup_verified_user(db_session, user_id)

    cat = Category(name="Documentaries", slug="documentaries")
    db_session.add(cat)
    await db_session.commit()

    cb = make_mock_callback(user_id=user_id, data=f"{CB_CATEGORY_VIEW}:{cat.id}")
    await handle_category_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args
    assert "no published videos in this category" in args[0].lower()

    keyboard = kwargs.get("reply_markup")
    all_callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
    assert CB_CATEGORY_LIST in all_callbacks
    assert CB_MAIN_MENU in all_callbacks


async def test_deleted_or_invalid_category_handled_safely(db_session: AsyncSession) -> None:
    """Test that selecting a nonexistent or deleted category displays alert safely."""
    user_id = 3005
    await setup_verified_user(db_session, user_id)

    nonexistent_id = uuid.uuid4()
    cb = make_mock_callback(user_id=user_id, data=f"{CB_CATEGORY_VIEW}:{nonexistent_id}")
    await handle_category_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    assert cb.answer.call_args[1].get("show_alert") is True
    assert "no longer available" in cb.answer.call_args[0][0]
    cb.message.edit_text.assert_not_called()


async def test_category_video_pagination_over_10_videos(db_session: AsyncSession) -> None:
    """Test pagination when a category has > 10 published videos."""
    user_id = 3006
    await setup_verified_user(db_session, user_id)

    cat = Category(name="Thrillers", slug="thrillers")
    db_session.add(cat)
    await db_session.flush()

    # Create 14 published videos in Thrillers
    videos = []
    video_cats = []
    for i in range(14):
        v = Video(title=f"Thriller #{i + 1:02d}", telegram_file_id=f"tg_th_{i}", status=VIDEO_STATUS_PUBLISHED)
        videos.append(v)
    db_session.add_all(videos)
    await db_session.flush()

    for v in videos:
        video_cats.append(VideoCategory(video_id=v.id, category_id=cat.id))
    db_session.add_all(video_cats)
    await db_session.commit()

    # 1. View Category Page 0
    cb_p0 = make_mock_callback(user_id=user_id, data=f"{CB_CATEGORY_VIEW}:{cat.id}")
    await handle_category_view_callback(cb_p0, db_session)

    cb_p0.message.edit_text.assert_called_once()
    args_p0, kwargs_p0 = cb_p0.message.edit_text.call_args
    assert "Showing 1–10 of 14" in args_p0[0]

    kb_p0 = kwargs_p0.get("reply_markup")
    callbacks_p0 = [btn.callback_data for row in kb_p0.inline_keyboard for btn in row]
    # Should have "Next ➡️" pointing to cat:page:<cat.id>:1
    assert f"{CB_CATEGORY_PAGE}:{cat.id}:1" in callbacks_p0

    # 2. View Category Page 1 via pagination callback
    cb_p1 = make_mock_callback(user_id=user_id, data=f"{CB_CATEGORY_PAGE}:{cat.id}:1")
    await handle_category_video_page_callback(cb_p1, db_session)

    cb_p1.message.edit_text.assert_called_once()
    args_p1, kwargs_p1 = cb_p1.message.edit_text.call_args
    assert "Showing 11–14 of 14" in args_p1[0]

    kb_p1 = kwargs_p1.get("reply_markup")
    callbacks_p1 = [btn.callback_data for row in kb_p1.inline_keyboard for btn in row]
    # Should have "⬅️ Prev" pointing to cat:page:<cat.id>:0
    assert f"{CB_CATEGORY_PAGE}:{cat.id}:0" in callbacks_p1
    # Navigation controls maintained
    assert CB_CATEGORY_LIST in callbacks_p1
    assert CB_MAIN_MENU in callbacks_p1


async def test_category_listing_pagination_over_10_categories(db_session: AsyncSession) -> None:
    """Test pagination when there are > 10 categories."""
    user_id = 3007
    await setup_verified_user(db_session, user_id)

    # Create 13 categories
    cats = [Category(name=f"Category {i:02d}", slug=f"cat-{i:02d}") for i in range(13)]
    db_session.add_all(cats)
    await db_session.commit()

    # 1. Page 0 of categories
    msg = make_mock_message(user_id=user_id, text=BTN_BROWSE_VIDEOS)
    await handle_browse_videos(msg, db_session)

    kb_p0 = msg.answer.call_args[1].get("reply_markup")
    cbs_p0 = [btn.callback_data for row in kb_p0.inline_keyboard for btn in row]
    assert f"{CB_CATEGORY_LIST}:1" in cbs_p0

    # 2. Navigate to Page 1 of categories
    cb_p1 = make_mock_callback(user_id=user_id, data=f"{CB_CATEGORY_LIST}:1")
    await handle_category_list_callback(cb_p1, db_session)

    cb_p1.message.edit_text.assert_called_once()
    kb_p1 = cb_p1.message.edit_text.call_args[1].get("reply_markup")
    cbs_p1 = [btn.callback_data for row in kb_p1.inline_keyboard for btn in row]
    assert f"{CB_CATEGORY_LIST}:0" in cbs_p1


async def test_navigation_back_to_categories_callback(db_session: AsyncSession) -> None:
    """Test clicking 'Back to Categories' from video list returns to category overview."""
    user_id = 3008
    await setup_verified_user(db_session, user_id)

    cat = Category(name="Animation", slug="animation")
    db_session.add(cat)
    await db_session.commit()

    cb = make_mock_callback(user_id=user_id, data=CB_CATEGORY_LIST)
    await handle_category_list_callback(cb, db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    args, kwargs = cb.message.edit_text.call_args
    assert "Browse Videos — Categories" in args[0]
    keyboard = kwargs.get("reply_markup")
    assert any("Animation" in btn.text for row in keyboard.inline_keyboard for btn in row)


async def test_video_selection_and_delivery_from_category(db_session: AsyncSession) -> None:
    """Test selecting a video from category triggers send_video and provides return navigation."""
    user_id = 3009
    await setup_verified_user(db_session, user_id)

    cat = Category(name="Adventures", slug="adventures")
    db_session.add(cat)
    await db_session.flush()

    vid = Video(
        title="Jungle Trek",
        description="Deep exploration of the Amazon rainforest.",
        telegram_file_id="BAACAgIAAxkBAAI_ADVENTURE_FILE_ID",
        duration=1820,
        status=VIDEO_STATUS_PUBLISHED,
    )
    db_session.add(vid)
    await db_session.flush()
    db_session.add(VideoCategory(video_id=vid.id, category_id=cat.id))
    await db_session.commit()
    await db_session.refresh(vid)

    cb = make_mock_callback(user_id=user_id, data=f"{CB_VIDEO_VIEW}:{vid.id}")
    await handle_video_view_callback(cb, db_session)

    # Callback answered
    cb.answer.assert_called_once()

    # send_video was called with caption and detail keyboard
    cb.bot.send_video.assert_called_once()
    call_kwargs = cb.bot.send_video.call_args.kwargs
    assert call_kwargs["chat_id"] == user_id
    assert call_kwargs["video"] == "BAACAgIAAxkBAAI_ADVENTURE_FILE_ID"
    assert "Jungle Trek" in call_kwargs["caption"]
    assert "Adventures" in call_kwargs["caption"]

    detail_kb = call_kwargs["reply_markup"]
    detail_callbacks = [btn.callback_data for row in detail_kb.inline_keyboard for btn in row]
    assert f"{CB_CATEGORY_VIEW}:{cat.id}" in detail_callbacks
    assert CB_CATEGORY_LIST in detail_callbacks
    assert CB_MAIN_MENU in detail_callbacks


async def test_video_view_missing_or_unpublished_rejected(db_session: AsyncSession) -> None:
    """Test requesting a draft or non-existent video is rejected with an alert."""
    user_id = 3010
    await setup_verified_user(db_session, user_id)

    draft_vid = Video(title="Draft Only", telegram_file_id="tg_draft", status=VIDEO_STATUS_DRAFT)
    db_session.add(draft_vid)
    await db_session.commit()
    await db_session.refresh(draft_vid)

    cb = make_mock_callback(user_id=user_id, data=f"{CB_VIDEO_VIEW}:{draft_vid.id}")
    await handle_video_view_callback(cb, db_session)

    cb.answer.assert_called_once()
    assert cb.answer.call_args[1].get("show_alert") is True
    assert "no longer available" in cb.answer.call_args[0][0]
    cb.bot.send_video.assert_not_called()


async def test_video_view_telegram_api_error_handling(db_session: AsyncSession) -> None:
    """Test Telegram API errors during video send are handled with a graceful notification."""
    user_id = 3011
    await setup_verified_user(db_session, user_id)

    vid = Video(title="Error Vid", telegram_file_id="bad_id", status=VIDEO_STATUS_PUBLISHED)
    db_session.add(vid)
    await db_session.commit()
    await db_session.refresh(vid)

    mock_bot = MagicMock()
    mock_bot.send_video = AsyncMock(
        side_effect=TelegramBadRequest(method="sendVideo", message="Wrong remote file identifier")
    )

    cb = make_mock_callback(user_id=user_id, data=f"{CB_VIDEO_VIEW}:{vid.id}", bot=mock_bot)
    await handle_video_view_callback(cb, db_session)

    cb.message.answer.assert_called_once()
    assert "Delivery Error" in cb.message.answer.call_args[0][0]


async def test_catalog_main_menu_and_noop_callbacks() -> None:
    """Test Main Menu and No-op callbacks."""
    cb_menu = make_mock_callback(user_id=3012, data=CB_MAIN_MENU)
    await handle_main_menu_callback(cb_menu)
    cb_menu.answer.assert_called_once()
    cb_menu.message.answer.assert_called_once()
    assert cb_menu.message.answer.call_args[1].get("reply_markup") == get_main_menu_keyboard()

    cb_noop = make_mock_callback(user_id=3012, data=CB_NOOP)
    await handle_noop_callback(cb_noop)
    cb_noop.answer.assert_called_once()
