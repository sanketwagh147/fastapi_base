"""FastAPI dependency injection for database sessions.

Usage:
    @app.get("/events")
    async def list_events(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Event))
        return result.scalars().all()

Testing:
    app.dependency_overrides[get_db] = override_get_db
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncDBPool


async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide database session with automatic cleanup.

    Usage:
        @app.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Event))
            return result.scalars().all()
    """
    async with AsyncDBPool.get_session() as session:
        yield session
