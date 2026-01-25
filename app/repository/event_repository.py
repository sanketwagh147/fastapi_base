"""Event repository for database operations."""

from typing import Optional, List
from datetime import date
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.event import Event


class EventRepository(BaseRepository[Event]):
    """Repository for Event entity operations.
    
    Provides database access methods specific to Event entities,
    including search and filtering capabilities.
    """

    def __init__(self, session: AsyncSession):
        """Initialize EventRepository with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        super().__init__(Event, session)

    async def search(
        self, 
        search_term: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Event]:
        """Search events by title, description, or location.
        
        Args:
            search_term: Text to search for in title, description, and location
            limit: Maximum number of results to return
            offset: Number of records to skip
            
        Returns:
            List of matching Event instances
        """
        query = select(self.model).order_by(self.model.date.desc())
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    self.model.title.ilike(search_pattern),
                    self.model.description.ilike(search_pattern),
                    self.model.location.ilike(search_pattern),
                )
            )
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Event]:
        """Find events within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of Event instances within the date range
        """
        result = await self.session.execute(
            select(self.model)
            .where(self.model.date >= start_date)
            .where(self.model.date <= end_date)
            .order_by(self.model.date)
        )
        return list(result.scalars().all())

    async def find_upcoming(self, limit: Optional[int] = None) -> List[Event]:
        """Find upcoming events (from today onwards).
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of upcoming Event instances
        """
        from datetime import date as date_func
        
        query = (
            select(self.model)
            .where(self.model.date >= date_func.today())
            .order_by(self.model.date)
        )
        
        if limit:
            query = query.limit(limit)
            
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_location(self, location: str) -> List[Event]:
        """Find events by location (case-insensitive partial match).
        
        Args:
            location: Location search term
            
        Returns:
            List of Event instances matching the location
        """
        result = await self.session.execute(
            select(self.model)
            .where(self.model.location.ilike(f"%{location}%"))
            .order_by(self.model.date.desc())
        )
        return list(result.scalars().all())
