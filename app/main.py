"""Application entry point and graceful execution lifecycle."""

import asyncio
import logging
import sys

from pydantic import ValidationError

from app.bot import create_bot, create_dispatcher
from app.config import get_settings
from app.database.session import (
    DatabaseConnectionError,
    check_database_connection,
    close_database,
    create_session_maker,
    init_db_engine,
)

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("telegram_video_bot")


async def main() -> None:
    """Initialize application components, verify connectivity, and start polling."""
    # 1. Load and validate configuration
    try:
        settings = get_settings()
        logging.getLogger().setLevel(settings.LOG_LEVEL.upper())
    except ValidationError as err:
        logger.critical("Configuration validation failed:")
        for error in err.errors():
            field_name = " -> ".join(str(loc) for loc in error["loc"])
            logger.critical(" - Field '%s': %s", field_name, error["msg"])
        sys.exit(1)
    except Exception as exc:
        logger.critical("Failed to load application configuration: %s", exc)
        sys.exit(1)

    logger.info(
        "Starting Telegram Video Bot (Bot: %s, DB: %s, LogLevel: %s)",
        settings.masked_bot_token,
        settings.masked_database_url,
        settings.LOG_LEVEL,
    )

    # 2. Initialize database engine and session maker
    engine = init_db_engine(settings.DATABASE_URL)
    session_maker = create_session_maker(engine)

    # 3. Verify PostgreSQL database availability (fail fast)
    try:
        await check_database_connection(engine)
    except DatabaseConnectionError:
        logger.critical(
            "Database connectivity check failed. The bot cannot start without a working database connection.\n"
            "Please ensure PostgreSQL is running and your DATABASE_URL in .env is correct."
        )
        await close_database(engine)
        sys.exit(1)

    # 4. Initialize Bot and Dispatcher
    bot = create_bot(settings.BOT_TOKEN)
    dp = create_dispatcher(session_maker)

    # 5. Start polling with graceful shutdown guarantees
    try:
        logger.info("Telegram Bot is running and polling for updates...")
        # Drop pending updates on startup to avoid processing stale messages
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received.")
    except Exception as exc:
        logger.error("Unexpected error in polling loop: %s", exc, exc_info=True)
    finally:
        logger.info("Executing graceful application shutdown...")
        try:
            await bot.session.close()
            logger.info("Bot HTTP session closed.")
        except Exception as exc:
            logger.warning("Error closing bot session: %s", exc)

        await close_database(engine)
        logger.info("Graceful shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except SystemExit as e:
        sys.exit(e.code)

