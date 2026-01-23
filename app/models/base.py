"""
Base declarative class and mixins for SQLAlchemy models.

This module contains only the domain model base class and common mixins.
Database connection logic has been moved to app.core.database
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


def utc_now():
    """Returns current UTC time with timezone awareness.

    Replaces deprecated datetime.utcnow()
    """
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All domain models (Event, Image, etc.) should inherit from this class.
    """


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns to models.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = 'my_model'
            id = Column(Integer, primary_key=True)
    """

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
