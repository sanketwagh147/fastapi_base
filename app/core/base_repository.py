"""
Abstract base repository implementing the Repository Pattern for SQLAlchemy models.

This module provides a generic, reusable repository base class that abstracts
common CRUD (Create, Read, Update, Delete) operations for SQLAlchemy ORM models.

Design Pattern: Repository Pattern
    - Separates data access logic from business logic
    - Provides a collection-like interface for domain objects
    - Encapsulates query logic in specialized repository classes
    - Makes testing easier through mockable interfaces

Key Features:
    - Generic type support for type-safe operations
    - Common CRUD operations out of the box
    - Bulk operations (create_many, update_many, delete_many)
    - Filtering, pagination, and counting
    - Soft delete support (if model has is_deleted field)
    - Automatic error handling with rollback
    - Async-first design for optimal performance

Type Safety:
    BaseRepository[ModelType, IDType] ensures:
    - ModelType: Your SQLAlchemy model class
    - IDType: Type of the primary key (int, str, UUID, etc.)

Usage:
    # Create a specialized repository
    class UserRepository(BaseRepository[User, int]):
        async def find_by_email(self, email: str) -> User | None:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    # Use in your application
    async with AsyncDBPool.get_session() as session:
        repo = UserRepository(User, session)
        user = await repo.create(email="user@example.com", name="John")
        users = await repo.get_all(limit=10)
        await session.commit()

Benefits:
    - Reduces boilerplate code
    - Consistent API across all repositories
    - Easy to extend with domain-specific queries
    - Testable through dependency injection
    - Type-safe operations with proper IDE support
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
    """Abstract base repository providing common CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """Initialize repository with model type and session.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance

        Raises:
            IntegrityError: If unique constraint or foreign key violation occurs
            SQLAlchemyError: For other database errors
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def create_many(self, items: Sequence[dict[str, Any]]) -> Sequence[ModelType]:
        """Create multiple records in bulk.

        Args:
            items: List of dictionaries containing field values

        Returns:
            List of created model instances

        Raises:
            IntegrityError: If unique constraint or foreign key violation occurs
            SQLAlchemyError: For other database errors
        """
        try:
            instances = [self.model(**item) for item in items]
            self.session.add_all(instances)
            await self.session.flush()
            for instance in instances:
                await self.session.refresh(instance)
            return instances
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, id: IDType) -> ModelType | None:
        """Get a record by ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_by(self, **filters: Any) -> ModelType | None:
        """Get a single record matching the given filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            Model instance or None if not found
        """
        query = select(self.model)
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, limit: int | None = None, offset: int | None = None
    ) -> Sequence[ModelType]:
        """Get all records with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Sequence of model instances
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
        """Get records matching the given filters with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            **filters: Field-value pairs to filter by

        Returns:
            Sequence of model instances
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
        """Update a record by ID.

        Args:
            id: Primary key value
            refresh: Whether to refresh and return the updated instance
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found (when refresh=True)
            None if refresh=False

        Raises:
            IntegrityError: If unique constraint or foreign key violation occurs
            SQLAlchemyError: For other database errors
        """
        try:
            result = await self.session.execute(
                update(self.model).where(self.model.id == id).values(**kwargs)
            )
            await self.session.flush()

            if refresh and result.rowcount > 0:
                return await self.get_by_id(id)
            return None
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update_many(self, ids: Sequence[IDType], **kwargs: Any) -> int:
        """Update multiple records by IDs.

        Args:
            ids: Sequence of primary key values
            **kwargs: Fields to update

        Returns:
            Number of records updated

        Raises:
            IntegrityError: If unique constraint or foreign key violation occurs
            SQLAlchemyError: For other database errors
        """
        try:
            result = await self.session.execute(
                update(self.model).where(self.model.id.in_(ids)).values(**kwargs)
            )
            await self.session.flush()
            return result.rowcount
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete(self, id: IDType) -> bool:
        """Delete a record by ID.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found

        Raises:
            IntegrityError: If foreign key constraint prevents deletion
            SQLAlchemyError: For other database errors
        """
        try:
            result = await self.session.execute(delete(self.model).where(self.model.id == id))
            await self.session.flush()
            return result.rowcount > 0
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_many(self, ids: Sequence[IDType]) -> int:
        """Delete multiple records by IDs.

        Args:
            ids: Sequence of primary key values

        Returns:
            Number of records deleted

        Raises:
            IntegrityError: If foreign key constraint prevents deletion
            SQLAlchemyError: For other database errors
        """
        try:
            result = await self.session.execute(delete(self.model).where(self.model.id.in_(ids)))
            await self.session.flush()
            return result.rowcount
        except IntegrityError:
            await self.session.rollback()
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def soft_delete(self, id: IDType) -> bool:
        """Soft delete a record by setting deleted_at timestamp.

        Note: Requires model to have 'deleted_at' field.

        Args:
            id: Primary key value

        Returns:
            True if soft deleted, False if not found

        Raises:
            AttributeError: If model doesn't have deleted_at field
            SQLAlchemyError: For database errors
        """

        try:
            if not hasattr(self.model, "deleted_at"):
                raise AttributeError(
                    f"{self.model.__name__} does not support soft delete (missing 'deleted_at' field)"
                )

            result = await self.session.execute(
                update(self.model).where(self.model.id == id).values(deleted_at=datetime.now(UTC))
            )
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def exists(self, id: IDType) -> bool:
        """Check if a record exists.

        Args:
            id: Primary key value

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(select(self.model.id).where(self.model.id == id))
        return result.scalar_one_or_none() is not None

    async def count(self, **filters: Any) -> int:
        """Count records matching optional filters.

        Args:
            **filters: Optional field-value pairs to filter by

        Returns:
            Total number of records matching filters
        """
        query = select(func.count()).select_from(self.model)

        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def commit(self) -> None:
        """Commit the current transaction.

        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def rollback(self) -> None:
        """Rollback the current transaction.

        Raises:
            SQLAlchemyError: For database errors
        """
        await self.session.rollback()
