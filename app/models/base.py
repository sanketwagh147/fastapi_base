"""Base declarative class and mixins for SQLAlchemy models.

This module contains only the domain model base class and common mixins.
Database connection logic lives in app.core.database.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return current UTC time with timezone awareness."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


class TimestampMixin:
    """Adds created_at / updated_at columns.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class SoftDeleteMixin:
    """Adds deleted_at column for soft-delete support.

    Use with BaseRepository.soft_delete() to mark records as deleted
    without removing them from the database.

    Usage:
        class MyModel(Base, TimestampMixin, SoftDeleteMixin):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
