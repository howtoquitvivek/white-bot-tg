"""Telegram inline and reply keyboards."""

from typing import Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

AGE_CONFIRM_YES_CALLBACK = "age_confirm:yes"
AGE_CONFIRM_EXIT_CALLBACK = "age_confirm:exit"

# Menu button labels (exact text matching requirements)
BTN_BROWSE_VIDEOS = "Browse Videos"
BTN_COLLECTIONS = "Collections"
BTN_HELP = "Help"


def get_age_gate_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for 18+ age confirmation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔞 I am 18 or older",
                    callback_data=AGE_CONFIRM_YES_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Exit",
                    callback_data=AGE_CONFIRM_EXIT_CALLBACK,
                )
            ],
        ]
    )


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build persistent reply keyboard for the main menu.

    Configured with resize_keyboard=True, is_persistent=True (if supported),
    and a placeholder for the input field.
    """
    keyboard_layout = [
        [
            KeyboardButton(text=BTN_BROWSE_VIDEOS),
            KeyboardButton(text=BTN_COLLECTIONS),
        ],
        [
            KeyboardButton(text=BTN_HELP),
        ],
    ]

    kwargs: dict[str, Any] = {
        "keyboard": keyboard_layout,
        "resize_keyboard": True,
        "input_field_placeholder": "Choose an option...",
    }

    # Set is_persistent=True if supported by the installed aiogram version
    if "is_persistent" in ReplyKeyboardMarkup.model_fields:
        kwargs["is_persistent"] = True

    return ReplyKeyboardMarkup(**kwargs)
