"""Image repository for database operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.image import Image


class ImageRepository(BaseRepository[Image]):
    """Repository for Image entity operations.
    
    Provides database access methods specific to Image entities.
    """

    def __init__(self, session: AsyncSession):
        """Initialize ImageRepository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        super().__init__(Image, session)

    async def find_by_path(self, path: str) -> Optional[Image]:
        """Find image by path.
        
        Args:
            path: Image path/filename
            
        Returns:
            Image instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.path == path)
        )
        return result.scalar_one_or_none()

    async def path_exists(self, path: str) -> bool:
        """Check if an image with the given path exists.
        
        Args:
            path: Image path/filename
            
        Returns:
            True if image exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.path == path)
        )
        return result.scalar_one_or_none() is not None
