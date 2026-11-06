"""Handlers for /start command, age gating callbacks, and main menu interactions."""

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.main_menu import (
    AGE_CONFIRM_EXIT_CALLBACK,
    AGE_CONFIRM_YES_CALLBACK,
    BTN_BROWSE_VIDEOS,
    BTN_COLLECTIONS,
    BTN_HELP,
    get_age_gate_keyboard,
    get_main_menu_keyboard,
)
from app.services.user_service import (
    confirm_age,
    get_user_by_telegram_id,
    register_or_update_user,
)

logger = logging.getLogger(__name__)

router = Router(name="start_router")

from app.config import get_settings
from app.handlers.constants import (
    ACCESS_DENIED_TEXT,
    AGE_GATE_TEXT,
    HELP_TEXT,
    WELCOME_VERIFIED_TEXT,
    get_about_text,
)
from app.keyboards.catalog import build_about_keyboard, build_help_keyboard


@router.message(CommandStart())
async def handle_start(message: Message, session: AsyncSession) -> None:
    """Handle /start command.

    Registers user idempotently, checks age gating, and shows the appropriate screen.
    """
    from_user = message.from_user
    if not from_user:
        logger.warning("Received /start from message without from_user")
        return

    telegram_id = from_user.id
    logger.info("Handling /start for user_id=%d", telegram_id)

    user = await register_or_update_user(
        session=session,
        telegram_id=telegram_id,
        username=from_user.username,
        first_name=from_user.first_name,
        last_name=from_user.last_name,
    )

    if user.is_age_verified:
        await message.answer(
            WELCOME_VERIFIED_TEXT,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            AGE_GATE_TEXT,
            reply_markup=get_age_gate_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == AGE_CONFIRM_YES_CALLBACK)
async def handle_age_confirm_yes(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle positive age confirmation button click."""
    if not callback.from_user:
        return

    telegram_id = callback.from_user.id
    logger.info("Processing age confirmation for user_id=%d", telegram_id)

    # Server-side persistent confirmation
    await confirm_age(session, telegram_id)
    await callback.answer("Age confirmed! Welcome.", show_alert=False)

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                "✅ <b>Age Verified (18+)</b>\n\nThank you for confirming your age.",
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Could not edit callback message: %s", exc)

        await callback.message.answer(
            WELCOME_VERIFIED_TEXT,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    elif callback.bot and callback.from_user:
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=WELCOME_VERIFIED_TEXT,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == AGE_CONFIRM_EXIT_CALLBACK)
async def handle_age_confirm_exit(callback: CallbackQuery) -> None:
    """Handle exit button click from age confirmation."""
    logger.info("User declined age confirmation: user_id=%s", callback.from_user.id if callback.from_user else None)
    await callback.answer("Access declined.", show_alert=False)

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                ACCESS_DENIED_TEXT,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Could not edit callback message: %s", exc)


# Import browse videos and collections handlers from catalog module for backwards compatibility
from app.handlers.catalog import handle_browse_videos, handle_collections


@router.message(F.text.in_({BTN_HELP, "ℹ️ Help", "/help"}))
async def handle_help(message: Message, session: AsyncSession) -> None:
    """Handle help menu button or command."""
    user = None
    if message.from_user:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    reply_markup = get_main_menu_keyboard() if (user and user.is_age_verified) else None

    await message.answer(
        HELP_TEXT,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


@router.message(F.text.in_({"About", "ℹ️ About", "/about"}))
async def handle_about(message: Message, session: AsyncSession) -> None:
    """Handle about command/text."""
    user = None
    if message.from_user:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    reply_markup = build_about_keyboard() if (user and user.is_age_verified) else None

    settings = get_settings()
    about_text = get_about_text(settings.BOT_ABOUT_TEXT)

    await message.answer(
        about_text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


async def _ensure_verified(message: Message, session: AsyncSession) -> bool:
    """Helper to verify that user is age-verified before serving content."""
    if not message.from_user:
        return False

    user = await get_user_by_telegram_id(session, message.from_user.id)
    if user is None or not user.is_age_verified:
        await message.answer(
            AGE_GATE_TEXT,
            reply_markup=get_age_gate_keyboard(),
            parse_mode="HTML",
        )
        return False
    return True
