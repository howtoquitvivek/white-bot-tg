"""API routes package."""

from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.collections import router as collections_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.users import router as users_router
from app.api.routes.videos import router as videos_router

__all__ = [
    "auth_router",
    "categories_router",
    "collections_router",
    "dashboard_router",
    "uploads_router",
    "users_router",
    "videos_router",
]

