"""FastAPI application entrypoint for the admin backend."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import get_api_session_maker
from app.api.routes import (
    auth_router,
    categories_router,
    collections_router,
    dashboard_router,
    uploads_router,
    users_router,
    videos_router,
)
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing database engine initialization and disposal."""
    settings = get_settings()
    logger.info("Starting FastAPI Admin Backend on port 8000...")
    # Initialize the session maker on startup
    get_api_session_maker()
    yield
    logger.info("Shutting down FastAPI Admin Backend...")


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title="Telegram Video Platform Admin API",
        version="0.2.0",
        description="REST backend for the Web Admin Dashboard",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS for the frontend dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register API routers under /api
    app.include_router(auth_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(uploads_router, prefix="/api")
    app.include_router(videos_router, prefix="/api")
    app.include_router(categories_router, prefix="/api")
    app.include_router(collections_router, prefix="/api")
    app.include_router(users_router, prefix="/api")

    @app.get("/api/health")
    async def health_check() -> dict:
        return {"status": "ok", "version": "0.2.0"}

    return app


app = create_app()

