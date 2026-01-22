"""
Application lifespan management for FastAPI.

This module provides the lifespan context manager that handles:
- Database connection pool initialization and cleanup
- HTTP client pool initialization and cleanup
- Any other startup/shutdown tasks

The lifespan context manager ensures proper resource management
and graceful shutdown of all application services.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import AsyncDBPool
from app.core.rest_api import HttpxRestClientPool
from app.main_config import database_config


@asynccontextmanager
async def app_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle events.

    Startup:
        - Initialize database connection pool
        - Initialize HTTP client connection pool

    Shutdown:
        - Cleanup database pool
        - Cleanup HTTP client pool
    """
    # Startup: Initialize pools
    await AsyncDBPool.init(database_config)
    await HttpxRestClientPool.get_client()

    yield

    # Shutdown: Cleanup pools
    await AsyncDBPool.dispose()
    await HttpxRestClientPool.dispose()
