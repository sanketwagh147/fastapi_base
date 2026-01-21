"""
FastAPI dependency injection functions for database sessions and services.

This module provides reusable FastAPI dependencies following dependency injection
patterns for clean, testable code.

Dependency Injection Benefits:
    - Decouples components for easier testing
    - Automatic resource cleanup (sessions, connections)
    - Type hints provide IDE autocomplete
    - Consistent session management across endpoints
    - Easy to override in tests with dependency_overrides

Usage in FastAPI Routes:
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.dependencies import get_db

    @app.get("/events")
    async def list_events(db: AsyncSession = Depends(get_db)):
        # Session is automatically provided and cleaned up
        result = await db.execute(select(Event))
        return result.scalars().all()

Testing with Dependency Override:
    # In tests, override with a test database session
    async def override_get_db():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

Design Notes:
    - Uses AsyncIterator for proper async context management
    - Automatic rollback on exceptions
    - Session cleanup guaranteed via context manager
    - Compatible with FastAPI's dependency injection system
"""

from collections.abc import AsyncIterator

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
