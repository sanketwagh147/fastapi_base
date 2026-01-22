"""
FastAPI application entry point with async lifespan management.

This module initializes the FastAPI application with:
- Async database connection pooling (AsyncDBPool)
- CORS middleware configuration
- Automatic route discovery and registration
- Graceful startup/shutdown handling

Architecture:
    - Lifespan context manager handles database pool initialization/cleanup
    - Routes are auto-discovered from app/routes/ directory
    - Configuration is loaded from environment-specific .env files
    - All I/O operations use async/await for optimal concurrency
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import app_lifespan, register_routers
from app.main_config import cors_config, fastapi_config

app = FastAPI(
    title=fastapi_config.title,
    description=fastapi_config.description,
    version=fastapi_config.version,
    lifespan=app_lifespan,
    debug=fastapi_config.debug,
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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
