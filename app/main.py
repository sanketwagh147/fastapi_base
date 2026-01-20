"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import AsyncDBPool, DBConfig, register_routers
from app.main_config import fastapi_config, cors_config, database_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup: Initialize database pool
    db_cfg = database_config
    config = DBConfig(
        url=db_cfg.url,
        pool_size=db_cfg.pool_size,
        max_overflow=db_cfg.max_overflow,
        pool_timeout=db_cfg.pool_timeout,
        pool_recycle=db_cfg.pool_recycle,
        pool_pre_ping=db_cfg.pool_pre_ping,
        echo=db_cfg.echo
    )
    await AsyncDBPool.init(config)
    
    yield
    
    # Shutdown: Cleanup database pool
    await AsyncDBPool.dispose()


app = FastAPI(
    routes=[],
    title=fastapi_config.title,
    description=fastapi_config.description,
    version=fastapi_config.version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.allow_origins,
    allow_credentials=cors_config.allow_credentials,
    allow_methods=cors_config.allow_methods,
    allow_headers=cors_config.allow_headers,
)


# =============================================================================
# Auto-register all routes
# =============================================================================
register_routers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
