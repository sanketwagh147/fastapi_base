"""
Generic repository base class for SQLAlchemy models with async CRUD operations.

Features:
    - Type-safe operations: BaseRepository[ModelType, IDType]
    - CRUD operations: create, read, update, delete
    - Bulk operations: create_many, update_many, delete_many
    - Filtering, pagination, and counting
    - Soft delete support (requires 'deleted_at' field)
    - Automatic error handling with rollback

Usage:
    class UserRepository(BaseRepository[User, int]):
        async def find_by_email(self, email: str) -> User | None:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    async with AsyncDBPool.get_session() as session:
        repo = UserRepository(User, session)
        user = await repo.create(email="user@example.com", name="John")
        await session.commit()
"""

from abc import ABC
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["BaseRepository"]

# Type variables for SQLAlchemy model and ID type
ModelType = TypeVar("ModelType")
IDType = TypeVar("IDType", int, str)


class BaseRepository(Generic[ModelType, IDType], ABC):
    """Base repository with async CRUD operations for SQLAlchemy models."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Field values

        Returns:
            Created instance
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return instance

    async def create_many(self, items: Sequence[dict[str, Any]]) -> Sequence[ModelType]:
        """Create multiple records.

        Args:
            items: List of field value dicts

        Returns:
            Created instances
        """
        try:
            instances = [self.model(**item) for item in items]
            self.session.add_all(instances)
            await self.session.flush()
            for instance in instances:
                await self.session.refresh(instance)
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return instances

    async def get_by_id(self, id: IDType) -> ModelType | None:
        """Get record by ID.

        Args:
            id: Primary key

        Returns:
            Instance or None
        """
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_by(self, **filters: Any) -> ModelType | None:
        """Get single record by filters.

        Args:
            **filters: Field-value pairs

        Returns:
            Instance or None
        """
        query = select(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: int | None = None, offset: int | None = None
    ) -> Sequence[ModelType]:
        """Get all records.

        Args:
            limit: Max records
            offset: Records to skip

        Returns:
            List of instances
        """
        query = select(self.model)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def filter(
        self, limit: int | None = None, offset: int | None = None, **filters: Any
    ) -> Sequence[ModelType]:
        """Get records by filters.

        Args:
            limit: Max records
            offset: Records to skip
            **filters: Field-value pairs

        Returns:
            List of instances
        """
        query = select(self.model)

        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, id: IDType, refresh: bool = True, **kwargs: Any) -> ModelType | None:
        """Update record by ID.

        Args:
            id: Primary key
            refresh: Return updated instance
            **kwargs: Fields to update

        Returns:
            Updated instance or None
        """
        try:
            result = await self.session.execute(
                update(self.model).where(self.model.id == id).values(**kwargs)
            )
            await self.session.flush()

            if refresh and result.rowcount > 0:
                return await self.get_by_id(id)

        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return None

    async def update_many(self, ids: Sequence[IDType], **kwargs: Any) -> int:
        """Update multiple records.

        Args:
            ids: Primary keys
            **kwargs: Fields to update

        Returns:
            Number updated
        """
        try:
            result = await self.session.execute(
                update(self.model).where(self.model.id.in_(ids)).values(**kwargs)
            )
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return result.rowcount

    async def delete(self, id: IDType) -> bool:
        """Delete record by ID.

        Args:
            id: Primary key

        Returns:
            True if deleted
        """
        try:
            result = await self.session.execute(delete(self.model).where(self.model.id == id))
            await self.session.flush()

        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return result.rowcount > 0

    async def delete_many(self, ids: Sequence[IDType]) -> int:
        """Delete multiple records.

        Args:
            ids: Primary keys

        Returns:
            Number deleted
        """
        try:
            result = await self.session.execute(delete(self.model).where(self.model.id.in_(ids)))
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return result.rowcount

    async def soft_delete(self, id: IDType) -> bool:
        """Soft delete by setting deleted_at timestamp.

        Args:
            id: Primary key

        Returns:
            True if deleted

        Note:
            Requires 'deleted_at' field on model
        """

        try:
            if not hasattr(self.model, "deleted_at"):
                msg = f"{self.model.__name__} does not support soft delete (missing 'deleted_at' field)"
                raise AttributeError(msg)

            result = await self.session.execute(
                update(self.model).where(self.model.id == id).values(deleted_at=datetime.now(UTC))
            )
            await self.session.flush()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        else:
            return result.rowcount > 0

    async def exists(self, id_: IDType) -> bool:
        """Check if record exists.

        Args:
            id: Primary key

        Returns:
            True if exists
        """
        result = await self.session.execute(select(self.model.id).where(self.model.id == id_))
        return result.scalar_one_or_none() is not None

    async def count(self, **filters: Any) -> int:
        """Count records.

        Args:
            **filters: Optional filters

        Returns:
            Total count
        """
        query = select(func.count()).select_from(self.model)

        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def commit(self) -> None:
        """Commit current transaction."""
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def rollback(self) -> None:
        """Rollback current transaction."""
        await self.session.rollback()
