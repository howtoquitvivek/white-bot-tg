"""Unit tests for Telegram bot handlers (/start, callbacks, and menu navigation)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import (
    ACCESS_DENIED_TEXT,
    AGE_GATE_TEXT,
    WELCOME_VERIFIED_TEXT,
    handle_age_confirm_exit,
    handle_age_confirm_yes,
    handle_browse_videos,
    handle_collections,
    handle_help,
    handle_start,
)
from app.keyboards.main_menu import (
    AGE_CONFIRM_EXIT_CALLBACK,
    AGE_CONFIRM_YES_CALLBACK,
    BTN_BROWSE_VIDEOS,
    BTN_COLLECTIONS,
    BTN_HELP,
    get_age_gate_keyboard,
    get_main_menu_keyboard,
)
from app.services.user_service import confirm_age, get_user_by_telegram_id


def make_mock_message(user_id: int, username: str = "testuser", text: str = "/start") -> Message:
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
    inner_msg.edit_text = AsyncMock()
    inner_msg.answer = AsyncMock()
    cb.message = inner_msg
    return cb


def test_main_menu_keyboard_structure_and_persistence() -> None:
    """Test that main reply keyboard is persistent, resized, and contains all expected buttons."""
    kb = get_main_menu_keyboard()
    assert isinstance(kb, ReplyKeyboardMarkup)
    assert kb.resize_keyboard is True
    assert kb.is_persistent is True
    assert kb.input_field_placeholder == "Choose an option..."

    # Extract all button texts from keyboard matrix
    button_texts = [
        btn.text
        for row in kb.keyboard
        for btn in row
        if isinstance(btn, KeyboardButton)
    ]

    expected_buttons = ["Browse Videos", "Collections", "Help"]
    assert button_texts == expected_buttons
    assert BTN_BROWSE_VIDEOS in button_texts
    assert BTN_COLLECTIONS in button_texts
    assert BTN_HELP in button_texts


async def test_start_unverified_user_shows_age_gate(db_session: AsyncSession) -> None:
    """Test /start for a brand new user registers them and shows age gate prompt without main menu."""
    msg = make_mock_message(user_id=1001, username="newbie")

    await handle_start(msg, db_session)

    # Verify user was saved in DB
    db_user = await get_user_by_telegram_id(db_session, 1001)
    assert db_user is not None
    assert db_user.telegram_id == 1001
    assert db_user.is_age_verified is False

    # Verify response contains inline age gate, NOT the main reply keyboard
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert AGE_GATE_TEXT in args[0]
    assert kwargs.get("reply_markup") == get_age_gate_keyboard()


async def test_start_verified_user_shows_main_menu(db_session: AsyncSession) -> None:
    """Test /start for an already verified user displays welcome back and main reply keyboard immediately."""
    msg = make_mock_message(user_id=1002, username="verified_user")

    # Initial start to register
    await handle_start(msg, db_session)
    # Confirm age
    await confirm_age(db_session, 1002)

    # Second start
    msg.answer.reset_mock()
    await handle_start(msg, db_session)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert WELCOME_VERIFIED_TEXT in args[0]
    reply_markup = kwargs.get("reply_markup")
    assert reply_markup == get_main_menu_keyboard()
    assert reply_markup.is_persistent is True
    assert reply_markup.resize_keyboard is True


async def test_age_confirm_yes_callback_attaches_reply_keyboard(db_session: AsyncSession) -> None:
    """Test clicking 'I am 18 or older' records timestamp and delivers persistent main menu reply keyboard."""
    # Register user first
    msg = make_mock_message(user_id=1003, username="age_tester")
    await handle_start(msg, db_session)

    cb = make_mock_callback(user_id=1003, data=AGE_CONFIRM_YES_CALLBACK)
    await handle_age_confirm_yes(cb, db_session)

    # Verify DB update
    db_user = await get_user_by_telegram_id(db_session, 1003)
    assert db_user is not None
    assert db_user.is_age_verified is True
    assert db_user.age_verified_at is not None

    # Verify callback answered and message sent with persistent keyboard
    cb.answer.assert_called_once()
    assert cb.message is not None
    assert isinstance(cb.message, Message)
    cb.message.edit_text.assert_called_once()
    cb.message.answer.assert_called_once()
    answer_args, answer_kwargs = cb.message.answer.call_args
    assert WELCOME_VERIFIED_TEXT in answer_args[0]
    reply_markup = answer_kwargs.get("reply_markup")
    assert reply_markup == get_main_menu_keyboard()
    assert reply_markup.is_persistent is True


async def test_age_confirm_exit_callback() -> None:
    """Test clicking 'Exit' rejects access and edits prompt message without showing reply keyboard."""
    cb = make_mock_callback(user_id=1004, data=AGE_CONFIRM_EXIT_CALLBACK)
    await handle_age_confirm_exit(cb)

    cb.answer.assert_called_once()
    assert cb.message is not None
    assert isinstance(cb.message, Message)
    cb.message.edit_text.assert_called_once()
    assert ACCESS_DENIED_TEXT in cb.message.edit_text.call_args[0][0]


async def test_menu_buttons_unverified_blocked(db_session: AsyncSession) -> None:
    """Test that an unverified user cannot bypass age verification via button texts."""
    for btn_text in [BTN_BROWSE_VIDEOS, BTN_COLLECTIONS]:
        msg = make_mock_message(user_id=1005, text=btn_text)
        await handle_start(msg, db_session)
        msg.answer.reset_mock()

        if btn_text == BTN_BROWSE_VIDEOS:
            await handle_browse_videos(msg, db_session)
        elif btn_text == BTN_COLLECTIONS:
            await handle_collections(msg, db_session)

        msg.answer.assert_called_once()
        assert AGE_GATE_TEXT in msg.answer.call_args[0][0]


async def test_all_menu_buttons_verified_allowed_with_keyboard_preserved(db_session: AsyncSession) -> None:
    """Test that all three menu buttons respond and preserve the persistent main menu keyboard."""
    user_id = 1006
    msg_init = make_mock_message(user_id=user_id)
    await handle_start(msg_init, db_session)
    await confirm_age(db_session, user_id)

    handlers = [
        (BTN_BROWSE_VIDEOS, handle_browse_videos, "Browse Videos"),
        (BTN_COLLECTIONS, handle_collections, "Collections"),
        (BTN_HELP, handle_help, "About & Help"),
    ]

    for btn_text, handler_fn, expected_phrase in handlers:
        msg = make_mock_message(user_id=user_id, text=btn_text)
        await handler_fn(msg, db_session)

        msg.answer.assert_called_once()
        args, kwargs = msg.answer.call_args
        assert expected_phrase in args[0]
        # Ensure keyboard is attached (inline keyboard for browse catalog & collections, reply keyboard for placeholders)
        if btn_text in {BTN_BROWSE_VIDEOS, BTN_COLLECTIONS}:
            from aiogram.types import InlineKeyboardMarkup
            assert isinstance(kwargs.get("reply_markup"), InlineKeyboardMarkup)
        else:
            assert kwargs.get("reply_markup") == get_main_menu_keyboard()
