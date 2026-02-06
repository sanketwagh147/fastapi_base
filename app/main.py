"""
FastAPI application entry point with async lifespan management.

This module initializes the FastAPI application with:
- Structured logging with request correlation IDs
- Async database connection pooling (AsyncDBPool)
- CORS middleware configuration
- Automatic route discovery and registration
- Graceful startup/shutdown handling

Architecture:
    - Logging configured before app creation (JSON/console)
    - Lifespan context manager handles database pool initialization/cleanup
    - Routes are auto-discovered from app/routes/ directory
    - Configuration is loaded from environment-specific .env files
    - All I/O operations use async/await for optimal concurrency
"""

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import app_lifespan, register_routers, setup_logging
from app.core.exceptions.handlers import register_exception_handlers
from app.main_config import cors_config, fastapi_config

# =============================================================================
# Setup Logging (before app creation)
# =============================================================================
setup_logging()

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

# Add correlation ID middleware (adds request_id to context)
app.add_middleware(
    CorrelationIdMiddleware,
    header_name="X-Request-ID",
    generator=lambda: __import__("uuid").uuid4().hex[:16],
    validator=None,
    transformer=lambda x: x,
)

# Register exception handlers
register_exception_handlers(app)

# =============================================================================
# Auto-register all routes
# =============================================================================
register_routers(app)

# TODO: Integrate pytest tests and documentation generation

if __name__ == "__main__":
    import uvicorn

    # Use our structured logging config, disable uvicorn's default logging
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Disable uvicorn's logging config to use our structlog setup
    )
