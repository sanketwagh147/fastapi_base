"""
Core infrastructure components for the application.

This module contains database configuration, base classes,
dependency injection components, and route discovery.
"""
from .database import AsyncDBPool, DBConfig
from .dependencies import get_db
from .base_repository import BaseRepository
from .route_discovery import register_routers, discover_routers, RouterDiscoveryError

__all__ = [
    'AsyncDBPool', 
    'DBConfig', 
    'get_db', 
    'BaseRepository',
    'register_routers',
    'discover_routers',
    'RouterDiscoveryError',
]
