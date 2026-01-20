"""FastAPI dependency injection functions."""

from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncDBPool


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for async database session.
    
    Provides a database session that automatically handles cleanup
    and rollback on errors.
    
    Usage:
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.core.dependencies import get_db
        
        @app.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Event))
            return result.scalars().all()
    """
    async with AsyncDBPool.get_session() as session:
        yield session
