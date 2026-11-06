"""Handlers for browsing categories, collections, category/collection video lists, pagination, and video delivery."""

import html
import logging
from typing import Optional, Union
import uuid

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.handlers.constants import (
    AGE_GATE_TEXT,
    HELP_TEXT,
    WELCOME_VERIFIED_TEXT,
    get_about_text,
)
from app.keyboards.catalog import (
    CB_ABOUT,
    CB_CATEGORY_LIST,
    CB_CATEGORY_PAGE,
    CB_CATEGORY_VIEW,
    CB_COLLECTION_LIST,
    CB_COLLECTION_PAGE,
    CB_COLLECTION_VIEW,
    CB_HELP,
    CB_MAIN_MENU,
    CB_NOOP,
    CB_VIDEO_PAGE,
    CB_VIDEO_VIEW,
    PAGE_SIZE,
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
from app.keyboards.main_menu import (
    BTN_BROWSE_VIDEOS,
    BTN_COLLECTIONS,
    get_age_gate_keyboard,
    get_main_menu_keyboard,
)
from app.models.video import VIDEO_STATUS_PUBLISHED
from app.services.category_service import (
    get_category_by_id,
    list_categories_with_published_counts,
)
from app.services.collection_service import (
    get_collection_by_id,
    list_collections_with_published_counts,
)
from app.services.user_service import get_user_by_telegram_id
from app.services.video_service import get_video_by_id, list_videos

logger = logging.getLogger(__name__)

router = Router(name="catalog_router")


async def check_user_age_verified(
    event: Union[Message, CallbackQuery],
    session: AsyncSession,
) -> bool:
    """Verify that the user exists and has confirmed their age (18+)."""
    from_user = event.from_user
    if not from_user:
        return False

    user = await get_user_by_telegram_id(session, from_user.id)
    if user is None or not user.is_age_verified:
        if isinstance(event, CallbackQuery):
            await event.answer("⚠️ Age verification required.", show_alert=True)
            if event.message and isinstance(event.message, Message):
                await event.message.answer(
                    AGE_GATE_TEXT,
                    reply_markup=get_age_gate_keyboard(),
                    parse_mode="HTML",
                )
        elif isinstance(event, Message):
            await event.answer(
                AGE_GATE_TEXT,
                reply_markup=get_age_gate_keyboard(),
                parse_mode="HTML",
            )
        return False
    return True


def format_video_caption(video) -> str:
    """Build a rich HTML caption for video delivery, capped at 1024 characters."""
    title = html.escape(video.title)
    caption_parts = [f"🎬 <b>{title}</b>"]

    if video.description:
        desc = html.escape(video.description.strip())
        caption_parts.append(f"\n{desc}")

    meta_parts = []
    if video.duration:
        mins, secs = divmod(video.duration, 60)
        meta_parts.append(f"⏱ <i>Duration: {mins}:{secs:02d}</i>")

    if video.categories:
        cat_names = ", ".join(html.escape(c.name) for c in video.categories)
        meta_parts.append(f"📁 <i>Category: {cat_names}</i>")

    if meta_parts:
        caption_parts.append("\n" + "\n".join(meta_parts))

    full_caption = "\n".join(caption_parts)
    if len(full_caption) > 1024:
        return full_caption[:1020] + "..."
    return full_caption


@router.message(F.text.in_({BTN_BROWSE_VIDEOS, "🎬 Browse Videos", "/browse", "/categories", "/videos"}))
async def handle_browse_videos(message: Message, session: AsyncSession) -> None:
    """Display available categories with published video counts in an inline keyboard."""
    if not await check_user_age_verified(message, session):
        return

    categories_with_counts, total = await list_categories_with_published_counts(
        session=session,
        limit=PAGE_SIZE,
        offset=0,
    )

    if total == 0:
        await message.answer(
            "📁 <b>Browse Videos — Categories</b>\n\n"
            "There are currently no video categories available. "
            "Please check back soon for new releases!",
            reply_markup=build_empty_categories_keyboard(),
            parse_mode="HTML",
        )
        return

    shown_count = min(len(categories_with_counts), total)
    header_text = (
        f"📁 <b>Browse Videos — Categories</b> (Showing 1–{shown_count} of {total})\n\n"
        "Select a category below to explore available videos:"
    )

    await message.answer(
        header_text,
        reply_markup=build_category_list_keyboard(
            categories_with_counts=categories_with_counts,
            page=0,
            total_count=total,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CATEGORY_LIST)
@router.callback_query(F.data.startswith(f"{CB_CATEGORY_LIST}:"))
async def handle_category_list_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle category list navigation and pagination."""
    if not await check_user_age_verified(callback, session):
        return

    page = 0
    if ":" in callback.data:
        try:
            page = int(callback.data.split(":")[2])
        except (IndexError, ValueError):
            page = 0

    categories_with_counts, total = await list_categories_with_published_counts(
        session=session,
        limit=PAGE_SIZE,
        offset=page * PAGE_SIZE,
    )

    if total == 0:
        text = (
            "📁 <b>Browse Videos — Categories</b>\n\n"
            "There are currently no video categories available."
        )
        keyboard = build_empty_categories_keyboard()
    else:
        start_idx = page * PAGE_SIZE + 1
        end_idx = min(start_idx + len(categories_with_counts) - 1, total)
        text = (
            f"📁 <b>Browse Videos — Categories</b> (Showing {start_idx}–{end_idx} of {total})\n\n"
            "Select a category below to explore available videos:"
        )
        keyboard = build_category_list_keyboard(
            categories_with_counts=categories_with_counts,
            page=page,
            total_count=total,
        )

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit category list message: %s", exc)

    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_CATEGORY_VIEW}:"))
async def handle_category_view_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Display published videos for a selected category."""
    if not await check_user_age_verified(callback, session):
        return

    try:
        category_id_str = callback.data.split(":")[2]
        category_id = uuid.UUID(category_id_str)
    except (IndexError, ValueError):
        await callback.answer("⚠️ Invalid category request.", show_alert=True)
        return

    category = await get_category_by_id(session, category_id)
    if not category:
        await callback.answer("⚠️ This category is no longer available.", show_alert=True)
        return

    videos, total = await list_videos(
        session=session,
        category_id=category_id,
        public_only=True,
        limit=PAGE_SIZE,
        offset=0,
    )

    cat_name = html.escape(category.name)

    if total == 0:
        text = (
            f"📁 <b>{cat_name}</b>\n\n"
            "There are currently no published videos in this category. "
            "Please check back soon or explore other categories!"
        )
        keyboard = build_empty_category_videos_keyboard(category_id)
    else:
        shown_count = min(len(videos), total)
        desc_line = f"\n<i>{html.escape(category.description.strip())}</i>\n" if category.description else "\n"
        text = (
            f"📁 <b>{cat_name}</b> (Showing 1–{shown_count} of {total}){desc_line}\n"
            "Tap a video below to watch:"
        )
        keyboard = build_video_catalog_keyboard(
            videos=videos,
            page=0,
            total_count=total,
            category_id=category_id,
        )

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit category video list: %s", exc)

    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_CATEGORY_PAGE}:"))
async def handle_category_video_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle pagination for videos within a specific category."""
    if not await check_user_age_verified(callback, session):
        return

    parts = callback.data.split(":")
    try:
        category_id = uuid.UUID(parts[2])
        page = int(parts[3])
    except (IndexError, ValueError):
        await callback.answer("⚠️ Invalid navigation request.", show_alert=True)
        return

    category = await get_category_by_id(session, category_id)
    if not category:
        await callback.answer("⚠️ This category is no longer available.", show_alert=True)
        return

    videos, total = await list_videos(
        session=session,
        category_id=category_id,
        public_only=True,
        limit=PAGE_SIZE,
        offset=page * PAGE_SIZE,
    )

    cat_name = html.escape(category.name)
    start_idx = page * PAGE_SIZE + 1
    end_idx = min(start_idx + len(videos) - 1, total)

    text = (
        f"📁 <b>{cat_name}</b> (Showing {start_idx}–{end_idx} of {total})\n\n"
        "Tap a video below to watch:"
    )
    keyboard = build_video_catalog_keyboard(
        videos=videos,
        page=page,
        total_count=total,
        category_id=category_id,
    )

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit paginated category video list: %s", exc)

    await callback.answer()


@router.message(F.text.in_({BTN_COLLECTIONS, "📁 Collections", "📚 Collections", "/collections"}))
async def handle_collections(message: Message, session: AsyncSession) -> None:
    """Display available collections with published video counts in an inline keyboard."""
    if not await check_user_age_verified(message, session):
        return

    collections_with_counts, total = await list_collections_with_published_counts(
        session=session,
        public_only=True,
        limit=PAGE_SIZE,
        offset=0,
    )

    if total == 0:
        await message.answer(
            "📚 <b>Collections</b>\n\n"
            "There are currently no collections available. "
            "Please check back soon for new releases!",
            reply_markup=build_empty_collections_keyboard(),
            parse_mode="HTML",
        )
        return

    shown_count = min(len(collections_with_counts), total)
    header_text = (
        f"📚 <b>Collections</b> (Showing 1–{shown_count} of {total})\n\n"
        "Select a collection below to view curated videos:"
    )

    await message.answer(
        header_text,
        reply_markup=build_collection_list_keyboard(
            collections_with_counts=collections_with_counts,
            page=0,
            total_count=total,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_COLLECTION_LIST)
@router.callback_query(F.data.startswith(f"{CB_COLLECTION_LIST}:"))
async def handle_collection_list_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle collection list navigation and pagination."""
    if not await check_user_age_verified(callback, session):
        return

    page = 0
    if ":" in callback.data:
        try:
            page = int(callback.data.split(":")[2])
        except (IndexError, ValueError):
            page = 0

    collections_with_counts, total = await list_collections_with_published_counts(
        session=session,
        public_only=True,
        limit=PAGE_SIZE,
        offset=page * PAGE_SIZE,
    )

    if total == 0:
        text = (
            "📚 <b>Collections</b>\n\n"
            "There are currently no collections available."
        )
        keyboard = build_empty_collections_keyboard()
    else:
        start_idx = page * PAGE_SIZE + 1
        end_idx = min(start_idx + len(collections_with_counts) - 1, total)
        text = (
            f"📚 <b>Collections</b> (Showing {start_idx}–{end_idx} of {total})\n\n"
            "Select a collection below to view curated videos:"
        )
        keyboard = build_collection_list_keyboard(
            collections_with_counts=collections_with_counts,
            page=page,
            total_count=total,
        )

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit collection list message: %s", exc)

    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_COLLECTION_VIEW}:"))
async def handle_collection_view_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Display published videos for a selected collection."""
    if not await check_user_age_verified(callback, session):
        return

    try:
        collection_id_str = callback.data.split(":")[2]
        collection_id = uuid.UUID(collection_id_str)
    except (IndexError, ValueError):
        await callback.answer("⚠️ Invalid collection request.", show_alert=True)
        return

    collection = await get_collection_by_id(session, collection_id, public_only=True)
    if not collection:
        await callback.answer("⚠️ This collection is no longer available.", show_alert=True)
        return

    # Extract published videos ordered by CollectionVideo.position
    sorted_cvs = sorted(collection.collection_videos, key=lambda cv: cv.position)
    published_videos = [
        cv.video for cv in sorted_cvs
        if cv.video and cv.video.status == VIDEO_STATUS_PUBLISHED
    ]
    total = len(published_videos)

    coll_title = html.escape(collection.title)
    desc_line = f"\n<i>{html.escape(collection.description.strip())}</i>\n" if collection.description else "\n"

    if total == 0:
        text = (
            f"📚 <b>{coll_title}</b>{desc_line}\n"
            "There are currently no published videos in this collection. "
            "Please check back soon or explore other collections!"
        )
        keyboard = build_empty_collection_videos_keyboard(collection_id)
    else:
        page_videos = published_videos[:PAGE_SIZE]
        shown_count = min(len(page_videos), total)
        text = (
            f"📚 <b>{coll_title}</b> (Showing 1–{shown_count} of {total}){desc_line}\n"
            "Tap a video below to watch:"
        )
        keyboard = build_video_catalog_keyboard(
            videos=page_videos,
            page=0,
            total_count=total,
            collection_id=collection_id,
        )

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit collection video list: %s", exc)

    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_COLLECTION_PAGE}:"))
async def handle_collection_video_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle pagination for videos within a specific collection."""
    if not await check_user_age_verified(callback, session):
        return

    parts = callback.data.split(":")
    try:
        collection_id = uuid.UUID(parts[2])
        page = int(parts[3])
    except (IndexError, ValueError):
        await callback.answer("⚠️ Invalid navigation request.", show_alert=True)
        return

    collection = await get_collection_by_id(session, collection_id, public_only=True)
    if not collection:
        await callback.answer("⚠️ This collection is no longer available.", show_alert=True)
        return

    sorted_cvs = sorted(collection.collection_videos, key=lambda cv: cv.position)
    published_videos = [
        cv.video for cv in sorted_cvs
        if cv.video and cv.video.status == VIDEO_STATUS_PUBLISHED
    ]
    total = len(published_videos)

    coll_title = html.escape(collection.title)
    start_idx = page * PAGE_SIZE
    page_videos = published_videos[start_idx : start_idx + PAGE_SIZE]
    shown_start = start_idx + 1 if total > 0 else 0
    shown_end = min(start_idx + len(page_videos), total)

    text = (
        f"📚 <b>{coll_title}</b> (Showing {shown_start}–{shown_end} of {total})\n\n"
        "Tap a video below to watch:"
    )
    keyboard = build_video_catalog_keyboard(
        videos=page_videos,
        page=page,
        total_count=total,
        collection_id=collection_id,
    )

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit paginated collection video list: %s", exc)

    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_VIDEO_PAGE}:"))
async def handle_catalog_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle general video catalog pagination navigation."""
    if not await check_user_age_verified(callback, session):
        return

    try:
        page = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        page = 0

    videos, total = await list_videos(
        session=session,
        public_only=True,
        limit=PAGE_SIZE,
        offset=page * PAGE_SIZE,
    )

    if total == 0:
        text = (
            "🎬 <b>Browse Videos</b>\n\n"
            "There are currently no videos available in the catalog."
        )
        keyboard = build_empty_catalog_keyboard()
    else:
        start_idx = page * PAGE_SIZE + 1
        end_idx = min(start_idx + len(videos) - 1, total)
        text = (
            f"🎬 <b>Browse Videos</b> (Showing {start_idx}–{end_idx} of {total})\n\n"
            "Tap a video below to watch:"
        )
        keyboard = build_video_catalog_keyboard(videos, page=page, total_count=total)

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Failed to edit catalog message: %s", exc)

    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_VIDEO_VIEW}:"))
async def handle_video_view_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Retrieve video by ID and send via Telegram using bot.send_video()."""
    if not await check_user_age_verified(callback, session):
        return

    try:
        video_id_str = callback.data.split(":")[2]
        video_id = uuid.UUID(video_id_str)
    except (IndexError, ValueError):
        await callback.answer("⚠️ Invalid video request.", show_alert=True)
        return

    video = await get_video_by_id(session, video_id, public_only=True)
    if not video:
        await callback.answer("⚠️ This video is no longer available in the catalog.", show_alert=True)
        return

    if not video.telegram_file_id:
        logger.error("Video %s is marked published but has no telegram_file_id", video.id)
        await callback.answer("⚠️ Video media file is currently unavailable.", show_alert=True)
        return

    # Acknowledge callback immediately to dismiss the client loading spinner
    await callback.answer("Sending video...", show_alert=False)

    caption = format_video_caption(video)
    target_chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    primary_cat_id = video.categories[0].id if video.categories else None

    try:
        if callback.bot:
            await callback.bot.send_video(
                chat_id=target_chat_id,
                video=video.telegram_file_id,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True,
                reply_markup=build_video_detail_keyboard(category_id=primary_cat_id),
            )
    except TelegramAPIError as exc:
        logger.error("Telegram API error sending video %s (file_id=%s): %s", video.id, video.telegram_file_id, exc)
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(
                "⚠️ <b>Delivery Error</b>\n\n"
                "Could not send this video right now. The media file may be temporarily unavailable or expired.",
                parse_mode="HTML",
            )
    except Exception as exc:
        logger.error("Unexpected error delivering video %s: %s", video.id, exc)
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(
                "⚠️ An unexpected error occurred while delivering the video. Please try again later.",
                parse_mode="HTML",
            )


@router.callback_query(F.data == CB_MAIN_MENU)
async def handle_main_menu_callback(callback: CallbackQuery) -> None:
    """Handle Main Menu inline button click."""
    await callback.answer()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer(
            WELCOME_VERIFIED_TEXT,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_NOOP)
async def handle_noop_callback(callback: CallbackQuery) -> None:
    """Acknowledge no-op pagination indicator click."""
    await callback.answer()


@router.callback_query(F.data == CB_HELP)
async def handle_help_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Display Help section via inline button navigation."""
    if not await check_user_age_verified(callback, session):
        return

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                HELP_TEXT,
                reply_markup=build_help_keyboard(),
                parse_mode="HTML",
            )
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                logger.debug("Help content unchanged on refresh")
            else:
                logger.warning("TelegramBadRequest in handle_help_callback: %s", exc)
        except Exception as exc:
            logger.debug("Failed to edit message to Help: %s", exc)

    await callback.answer()


@router.callback_query(F.data == CB_ABOUT)
async def handle_about_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Display About section via inline button navigation."""
    if not await check_user_age_verified(callback, session):
        return

    settings = get_settings()
    about_text = get_about_text(settings.BOT_ABOUT_TEXT)

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                about_text,
                reply_markup=build_about_keyboard(),
                parse_mode="HTML",
            )
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                logger.debug("About content unchanged on refresh")
            else:
                logger.warning("TelegramBadRequest in handle_about_callback: %s", exc)
        except Exception as exc:
            logger.debug("Failed to edit message to About: %s", exc)

    await callback.answer()


@router.callback_query()
async def handle_unknown_or_outdated_callback(callback: CallbackQuery) -> None:
    """Fallback handler for expired, invalid, or unrecognized callback queries."""
    logger.info(
        "Received unrecognized or expired callback query: data=%r, user_id=%s",
        callback.data,
        callback.from_user.id if callback.from_user else None,
    )
    await callback.answer(
        "⚠️ This menu option has expired or is no longer valid. Please choose an option from the menu.",
        show_alert=True,
    )
