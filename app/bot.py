"""Bot and Dispatcher initialization and middleware configuration."""

from collections.abc import Awaitable, Callable
import logging
from typing import Any

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.handlers.catalog import router as catalog_router
from app.handlers.start import router as start_router

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """Aiogram middleware that injects an active AsyncSession into handler parameters."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_maker() as session:
            data["session"] = session
            return await handler(event, data)


def create_bot(token: str) -> Bot:
    """Create and configure the aiogram Bot instance."""
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(session_maker: async_sessionmaker[AsyncSession]) -> Dispatcher:
    """Create and configure the Dispatcher with routers and middlewares."""
    dp = Dispatcher()

    # Register DB session middleware for messages and callbacks
    db_middleware = DbSessionMiddleware(session_maker)
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)

    # Register routers
    dp.include_router(start_router)
    dp.include_router(catalog_router)

    return dp

