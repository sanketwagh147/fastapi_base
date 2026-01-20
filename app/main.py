"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import AsyncDBPool, register_routers
from app.main_config import fastapi_config, cors_config, database_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup: Initialize database pool
    await AsyncDBPool.init(database_config)
    
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
