"""Abstract base repository for common CRUD operations."""

from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Type variable for SQLAlchemy model
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Abstract base repository providing common CRUD operations.  """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
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
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get a record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """Get all records with optional pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, id: Any, **kwargs: Any) -> Optional[ModelType]:
        """Update a record by ID.
        
        Args:
            id: Primary key value
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None if not found
        """
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
        )
        await self.session.flush()
        return await self.get_by_id(id)

    async def delete(self, id: Any) -> bool:
        """Delete a record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, id: Any) -> bool:
        """Check if a record exists.
        
        Args:
            id: Primary key value
            
        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """Count total records.
        
        Returns:
            Total number of records
        """
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()
