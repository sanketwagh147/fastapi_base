"""
Core infrastructure components for the application.

This module contains database configuration, base classes,
dependency injection components, and route discovery.
"""

from .base_repository import BaseRepository
from .database import AsyncDBPool
from .dependencies import get_db
from .lifespan import app_lifespan
from .logging_config import setup_logging
from .route_discovery import RouterDiscoveryError, discover_routers, register_routers

__all__ = [
    # Core
    "AsyncDBPool",
    "BaseRepository",
    "RouterDiscoveryError",
    "app_lifespan",
    "discover_routers",
    "get_db",
    "register_routers",
    "setup_logging",
]
