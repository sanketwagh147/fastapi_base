"""Async SQLAlchemy connection pool and session management.

Features:
    - Singleton connection pool manager
    - Async-only operations
    - Connection pooling with health checks
    - Automatic session cleanup and rollback

Usage:
    # Initialize at startup
    await AsyncDBPool.init(config)

    # Use in routes
    async with AsyncDBPool.get_session() as session:
        result = await session.execute(select(Event))
        await session.commit()

    # Cleanup at shutdown
    await AsyncDBPool.dispose()
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
    """Async SQLAlchemy connection pool manager.

    Usage:
        await AsyncDBPool.init(config)
        async with AsyncDBPool.get_session() as session:
            await session.execute(select(Event))
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
            config: Database configuration
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
        """Close all database connections and cleanup."""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._maker = None

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncIterator[AsyncSession]:
        """Get database session with automatic rollback on errors.

        Usage:
            async with AsyncDBPool.get_session() as session:
                await session.execute(...)
                await session.commit()
        """
        if cls._maker is None:
            msg = "AsyncDBPool not initialized. Call await AsyncDBPool.init() first."
            raise RuntimeError(msg)

        async with cls._maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for database session.

    Usage:
        @app.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Event))
            return result.scalars().all()
    """
    async with AsyncDBPool.get_session() as session:
        yield session
