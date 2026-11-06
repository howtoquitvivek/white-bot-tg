"""Shared text constants for Telegram bot interactions."""

from typing import Optional

AGE_GATE_TEXT = (
    "⚠️ <b>Age Confirmation Required (18+)</b>\n\n"
    "This bot provides access to adult media content intended strictly for users "
    "aged 18 or older.\n\n"
    "All distributed content is lawful, consensually produced, and authorized for distribution.\n\n"
    "Please confirm that you are at least 18 years of age to proceed.\n\n"
    "<i>Notice: This confirmation acts as an access gate and does not constitute "
    "formal legal age or identity verification.</i>"
)

WELCOME_VERIFIED_TEXT = (
    "🎬 <b>Welcome to the Video Bot!</b>\n\n"
    "Your 18+ confirmation is active. Choose an option below to get started:"
)

ACCESS_DENIED_TEXT = (
    "🚫 <b>Access Denied</b>\n\n"
    "You must be 18 or older to access this bot. If you chose this by mistake, "
    "send /start when you are eligible."
)

HELP_TEXT = (
    "ℹ️ <b>About & Help Guide</b>\n\n"
    "Welcome to the Video Bot! Here is how to discover and watch videos:\n\n"
    "📁 <b>1. How to Browse Categories:</b>\n"
    "• Tap <b>Browse Videos</b> on the menu to view all available video categories.\n"
    "• Each category shows the number of available videos in parentheses.\n"
    "• Use <b>⬅️ Prev</b> and <b>Next ➡️</b> to page through categories if there are more than 10.\n\n"
    "📚 <b>2. How to Access Collections:</b>\n"
    "• Tap <b>Collections</b> on the menu to explore curated playlists and series.\n"
    "• Select any collection to see its full video tracklist in order.\n\n"
    "🎬 <b>3. How to Select & Receive Videos:</b>\n"
    "• Tap any video title button inside a category or collection.\n"
    "• The bot instantly sends the full video directly to this chat.\n"
    "• Videos include duration, description, and streaming support.\n\n"
    "🏠 <b>4. How to Navigate Back to Main Menu:</b>\n"
    "• Tap the <b>🏠 Main Menu</b> inline button under any list or video.\n"
    "• Or use the persistent reply menu buttons at the bottom of your screen anytime.\n"
    "• You can also send /start to re-open the main menu.\n\n"
    "<b>Commands:</b>\n"
    "• /start — Restart bot or open main menu\n"
    "• /browse — Browse video categories\n"
    "• /collections — View curated collections\n"
    "• /help — View this help guide\n"
    "• /about — Platform overview & compliance"
)

DEFAULT_ABOUT_TEXT = (
    "ℹ️ <b>About Video Platform</b>\n\n"
    "This Telegram bot is a private video platform distributing authorized media "
    "content strictly to verified adult users (18+).\n\n"
    "• <b>Compliance & Authorization:</b> All distributed media is consensual, lawful, "
    "and authorized for distribution.\n"
    "• <b>Age Restriction:</b> Strict 18+ age verification gate is required before accessing any content.\n"
    "• <b>Direct Streaming:</b> Videos are streamed and distributed securely via Telegram cloud storage.\n"
    "• <b>Organization:</b> Content is organized into thematic categories and curated collections."
)


def get_about_text(custom_text: Optional[str] = None) -> str:
    """Return configured about text or default factual platform information."""
    if custom_text and custom_text.strip():
        return custom_text.strip()
    return DEFAULT_ABOUT_TEXT
