"""Inline keyboards for video catalog and category browsing and pagination."""

import math
from typing import List, Optional, Tuple
import uuid

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.category import Category
from app.models.collection import Collection
from app.models.video import Video

PAGE_SIZE = 10

# Callback prefixes and actions
CB_CATEGORY_LIST = "cat:list"
CB_CATEGORY_VIEW = "cat:view"
CB_CATEGORY_PAGE = "cat:page"
CB_COLLECTION_LIST = "col:list"
CB_COLLECTION_VIEW = "col:view"
CB_COLLECTION_PAGE = "col:page"
CB_VIDEO_VIEW = "vid:view"
CB_VIDEO_PAGE = "vid:page"
CB_MAIN_MENU = "vid:main_menu"
CB_NOOP = "vid:noop"
CB_HELP = "nav:help"
CB_ABOUT = "nav:about"


def build_category_list_keyboard(
    categories_with_counts: List[Tuple[Category, int]],
    page: int = 0,
    total_count: int = 0,
    page_size: int = PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Build an inline keyboard listing available categories with published video counts."""
    buttons: List[List[InlineKeyboardButton]] = []

    # 1. Category buttons (one per row for clear mobile interaction)
    for cat, count in categories_with_counts:
        cat_name = cat.name.strip()
        display_name = (cat_name[:32] + "…") if len(cat_name) > 32 else cat_name
        btn_text = f"📁 {display_name} ({count})"

        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"{CB_CATEGORY_VIEW}:{cat.id}",
            )
        ])

    # 2. Pagination controls for categories if total_count > page_size
    total_pages = max(1, math.ceil(total_count / page_size)) if total_count else 1
    if total_pages > 1:
        nav_row: List[InlineKeyboardButton] = []

        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ Prev",
                    callback_data=f"{CB_CATEGORY_LIST}:{page - 1}",
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data=CB_NOOP,
            )
        )

        if page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"{CB_CATEGORY_LIST}:{page + 1}",
                )
            )

        buttons.append(nav_row)

    # 3. Middle cross-section navigation: Collections & Help
    buttons.append([
        InlineKeyboardButton(
            text="📚 Collections",
            callback_data=CB_COLLECTION_LIST,
        ),
        InlineKeyboardButton(
            text="❓ Help",
            callback_data=CB_HELP,
        ),
    ])

    # 4. Bottom navigation row: Refresh & Main Menu
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data=f"{CB_CATEGORY_LIST}:{page}",
        ),
        InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data=CB_MAIN_MENU,
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_empty_categories_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard when no categories exist."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Check Again",
                    callback_data=f"{CB_CATEGORY_LIST}:0",
                ),
                InlineKeyboardButton(
                    text="📚 Collections",
                    callback_data=CB_COLLECTION_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Help",
                    callback_data=CB_HELP,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )


def build_collection_list_keyboard(
    collections_with_counts: List[Tuple[Collection, int]],
    page: int = 0,
    total_count: int = 0,
    page_size: int = PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Build an inline keyboard listing available collections with published video counts."""
    buttons: List[List[InlineKeyboardButton]] = []

    # 1. Collection buttons (one per row for readability)
    for coll, count in collections_with_counts:
        title = coll.title.strip()
        display_title = (title[:30] + "…") if len(title) > 30 else title
        btn_text = f"📚 {display_title} ({count})"

        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"{CB_COLLECTION_VIEW}:{coll.id}",
            )
        ])

    # 2. Pagination controls if total_count > page_size
    total_pages = max(1, math.ceil(total_count / page_size)) if total_count else 1
    if total_pages > 1:
        nav_row: List[InlineKeyboardButton] = []

        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ Prev",
                    callback_data=f"{CB_COLLECTION_LIST}:{page - 1}",
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data=CB_NOOP,
            )
        )

        if page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"{CB_COLLECTION_LIST}:{page + 1}",
                )
            )

        buttons.append(nav_row)

    # 3. Middle cross-section navigation: Categories & Help
    buttons.append([
        InlineKeyboardButton(
            text="📁 Categories",
            callback_data=CB_CATEGORY_LIST,
        ),
        InlineKeyboardButton(
            text="❓ Help",
            callback_data=CB_HELP,
        ),
    ])

    # 4. Bottom navigation row: Refresh & Main Menu
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data=f"{CB_COLLECTION_LIST}:{page}",
        ),
        InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data=CB_MAIN_MENU,
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_empty_collections_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard when no collections exist."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Check Again",
                    callback_data=f"{CB_COLLECTION_LIST}:0",
                ),
                InlineKeyboardButton(
                    text="📁 Categories",
                    callback_data=CB_CATEGORY_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Help",
                    callback_data=CB_HELP,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )


def build_empty_collection_videos_keyboard(collection_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Build inline keyboard when a selected collection has zero published videos."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Refresh",
                    callback_data=f"{CB_COLLECTION_VIEW}:{collection_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📚 Back to Collections",
                    callback_data=CB_COLLECTION_LIST,
                ),
                InlineKeyboardButton(
                    text="📁 Categories",
                    callback_data=CB_CATEGORY_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Help",
                    callback_data=CB_HELP,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )


def build_video_catalog_keyboard(
    videos: List[Video],
    page: int,
    total_count: int,
    category_id: Optional[uuid.UUID] = None,
    collection_id: Optional[uuid.UUID] = None,
    page_size: int = PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Build an inline keyboard listing video buttons and category/collection-aware pagination controls."""
    buttons: List[List[InlineKeyboardButton]] = []

    # 1. Video item buttons (one per row for readability)
    for video in videos:
        duration_str = ""
        if video.duration:
            mins, secs = divmod(video.duration, 60)
            duration_str = f" [{mins}:{secs:02d}]"

        # Truncate title if necessary so button label remains readable
        title = video.title.strip()
        max_len = 35 - len(duration_str)
        display_title = (title[:max_len] + "…") if len(title) > max_len else title
        btn_text = f"🎬 {display_title}{duration_str}"

        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"{CB_VIDEO_VIEW}:{video.id}",
            )
        ])

    # 2. Pagination controls (if total_count > page_size)
    total_pages = max(1, math.ceil(total_count / page_size))
    if total_pages > 1:
        nav_row: List[InlineKeyboardButton] = []

        # Target callback prefix depends on whether browsing a collection, category, or general list
        if collection_id:
            page_cb_prefix = f"{CB_COLLECTION_PAGE}:{collection_id}"
        elif category_id:
            page_cb_prefix = f"{CB_CATEGORY_PAGE}:{category_id}"
        else:
            page_cb_prefix = CB_VIDEO_PAGE

        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ Prev",
                    callback_data=f"{page_cb_prefix}:{page - 1}",
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data=CB_NOOP,
            )
        )

        if page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"{page_cb_prefix}:{page + 1}",
                )
            )

        buttons.append(nav_row)

    # 3. Cross-navigation: link to alternate discovery mode and help
    if collection_id:
        buttons.append([
            InlineKeyboardButton(text="📁 Categories", callback_data=CB_CATEGORY_LIST),
            InlineKeyboardButton(text="❓ Help", callback_data=CB_HELP),
        ])
    elif category_id:
        buttons.append([
            InlineKeyboardButton(text="📚 Collections", callback_data=CB_COLLECTION_LIST),
            InlineKeyboardButton(text="❓ Help", callback_data=CB_HELP),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="📁 Categories", callback_data=CB_CATEGORY_LIST),
            InlineKeyboardButton(text="❓ Help", callback_data=CB_HELP),
        ])

    # 4. Bottom navigation row: Back navigation and Main Menu
    back_button = (
        InlineKeyboardButton(text="📚 Back to Collections", callback_data=CB_COLLECTION_LIST)
        if collection_id
        else InlineKeyboardButton(text="📁 Back to Categories", callback_data=CB_CATEGORY_LIST)
    )

    buttons.append([
        back_button,
        InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data=CB_MAIN_MENU,
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_empty_category_videos_keyboard(category_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Build inline keyboard when a selected category has zero published videos."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Refresh",
                    callback_data=f"{CB_CATEGORY_VIEW}:{category_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📁 Back to Categories",
                    callback_data=CB_CATEGORY_LIST,
                ),
                InlineKeyboardButton(
                    text="📚 Collections",
                    callback_data=CB_COLLECTION_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Help",
                    callback_data=CB_HELP,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )


def build_empty_catalog_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard when no published videos exist."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 Back to Categories",
                    callback_data=CB_CATEGORY_LIST,
                ),
                InlineKeyboardButton(
                    text="📚 Collections",
                    callback_data=CB_COLLECTION_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Help",
                    callback_data=CB_HELP,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )


def build_video_detail_keyboard(
    category_id: Optional[uuid.UUID] = None,
    collection_id: Optional[uuid.UUID] = None,
) -> InlineKeyboardMarkup:
    """Build inline keyboard attached to delivered video message."""
    buttons: List[List[InlineKeyboardButton]] = []

    if collection_id:
        buttons.append([
            InlineKeyboardButton(
                text="◀️ Back to Collection",
                callback_data=f"{CB_COLLECTION_VIEW}:{collection_id}",
            )
        ])
    elif category_id:
        buttons.append([
            InlineKeyboardButton(
                text="◀️ Back to Category",
                callback_data=f"{CB_CATEGORY_VIEW}:{category_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="📚 Collections",
            callback_data=CB_COLLECTION_LIST,
        ),
        InlineKeyboardButton(
            text="📁 Categories",
            callback_data=CB_CATEGORY_LIST,
        ),
    ])

    buttons.append([
        InlineKeyboardButton(
            text="❓ Help",
            callback_data=CB_HELP,
        ),
        InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data=CB_MAIN_MENU,
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_help_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for the Help Guide screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 Browse Categories",
                    callback_data=CB_CATEGORY_LIST,
                ),
                InlineKeyboardButton(
                    text="📚 Collections",
                    callback_data=CB_COLLECTION_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ About Platform",
                    callback_data=CB_ABOUT,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )


def build_about_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for the About screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📁 Browse Categories",
                    callback_data=CB_CATEGORY_LIST,
                ),
                InlineKeyboardButton(
                    text="📚 Collections",
                    callback_data=CB_COLLECTION_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Help Guide",
                    callback_data=CB_HELP,
                ),
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ]
    )
