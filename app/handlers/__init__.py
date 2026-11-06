"""Handlers package."""

from app.handlers.catalog import router as catalog_router
from app.handlers.start import router as start_router

__all__ = ["start_router", "catalog_router"]

