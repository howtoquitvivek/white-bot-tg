"""Declarative base class and common custom types for SQLAlchemy models."""

from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in the application."""

    pass


class TZDateTime(TypeDecorator):
    """DateTime type that guarantees timezone-aware UTC datetime values across all dialects."""

    impl = sa.DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect: sa.Dialect) -> Optional[datetime]:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value: Optional[datetime], dialect: sa.Dialect) -> Optional[datetime]:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
