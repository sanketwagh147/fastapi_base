"""
Async SQLAlchemy connection pool and database session management.

This module provides a singleton connection pool manager for async SQLAlchemy operations.
It handles database connections efficiently with connection pooling, health checks,
and automatic cleanup.

Key Features:
    - Singleton pattern for global connection pool management
    - Async-only operations (no blocking database calls)
    - Connection pool with configurable size and overflow
    - Pre-ping health checks to avoid stale connections
    - Automatic rollback on exceptions
    - Graceful shutdown with connection cleanup

Design Decisions:
    - Class-based singleton (AsyncDBPool) for lifecycle management
    - Context manager pattern for automatic session cleanup
    - expire_on_commit=False for better async performance
    - Pool pre-ping enabled by default for reliability

Usage:
    # Initialize once at application startup (in lifespan)
    config = DatabaseConfig(...)
    await AsyncDBPool.init(config)

    # Use in route handlers or services
    async with AsyncDBPool.get_session() as session:
        result = await session.execute(select(Event))
        events = result.scalars().all()
        await session.commit()

    # Cleanup at shutdown (in lifespan)
    await AsyncDBPool.dispose()

Thread Safety:
    All methods are async and should be called from async context.
    The pool itself is thread-safe through SQLAlchemy's engine.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Import DatabaseConfig from main_config
from app.main_config import DatabaseConfig


class AsyncDBPool:
    """Async-only SQLAlchemy engine + session manager.

    This class manages database connection pooling and session lifecycle
    for async SQLAlchemy operations.

    Usage:
        # Initialize once at app startup
        config = DatabaseConfig()
        await AsyncDBPool.init(config)

        # Use in your code
        async with AsyncDBPool.get_session() as session:
            result = await session.execute(select(Event))
            events = result.scalars().all()

        # Cleanup at shutdown
        await AsyncDBPool.dispose()
    """

    _engine: AsyncEngine | None = None
    _maker: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    async def init(
        cls,
        config: DatabaseConfig,
    ) -> None:
        """Initialize async engine and sessionmaker.

        Args:
            config: DatabaseConfig instance with credentials and pool settings
        """
        if cls._engine is not None:
            return  # already initialized

        # Only pass valid SQLAlchemy engine parameters
        cls._engine = create_async_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
        )
        cls._maker = async_sessionmaker(cls._engine, expire_on_commit=False, class_=AsyncSession)

    @classmethod
    async def dispose(cls) -> None:
        """Dispose engine and clear session maker.

        Should be called during application shutdown to cleanly close
        all database connections.
        """
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._maker = None

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncIterator[AsyncSession]:
        """Yield a session; rollback on exceptions.

        Usage:
            async with AsyncDBPool.get_session() as session:
                await session.execute(...)
                await session.commit()

        Raises:
            RuntimeError: If pool not initialized
        """
        if cls._maker is None:
            raise RuntimeError("AsyncDBPool not initialized. Call await AsyncDBPool.init() first.")

        async with cls._maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for async DB session.

    Usage:
        @app.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Event))
            return result.scalars().all()
    """
    async with AsyncDBPool.get_session() as session:
        yield session
