"""SQLAlchemy models package.

Define domain models here, inheriting from Base and optional mixins:

    from app.models.base import Base, TimestampMixin

    class User(Base, TimestampMixin):
        __tablename__ = "users"
        ...
"""

from .base import Base, SoftDeleteMixin, TimestampMixin

__all__ = ["Base", "SoftDeleteMixin", "TimestampMixin"]
