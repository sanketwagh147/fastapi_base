"""Centralized logging configuration with structured logging.

Provides:
- Pretty console logs for development (colored, key-value pairs)
- JSON logs for production (machine-parseable)
- Request ID correlation across all logs
- Configurable log levels for different libraries

Usage:
    from app.core.logging_config import setup_logging
    setup_logging()  # Call once at app startup
"""

import importlib.util
import logging
import sys
from typing import Any

import structlog
from asgi_correlation_id import correlation_id

from app.main_config import logging_config


def get_request_id(_logger: Any, _method_name: str, event_dict: dict) -> dict:
    """Add request_id from asgi-correlation-id contextvar to log events."""
    request_id = correlation_id.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the entire application.

    Behavior:
    - Reads LOG_FORMAT, LOG_LEVEL from environment (via main_config)
    - JSON format for production (LOG_FORMAT=json)
    - Pretty console for local/dev (LOG_FORMAT=console)
    - Request ID automatically added to all logs
    - Uvicorn logs also go through structlog processors

    Call this once before creating the FastAPI app.
    """
    log_level = logging_config.log_level.upper()

    # Shared processors for both stdlib and structlog
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        get_request_id,  # Inject request_id from contextvar
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    # Choose renderer based on environment
    if logging_config.log_format == "json":
        # Production: JSON to stdout
        renderer = structlog.processors.JSONRenderer()
    else:
        # Local/dev: Pretty console output with colors
        try:
            # Use rich for pretty colors if available (dev dependency)
            if importlib.util.find_spec("rich") is not None:
                renderer = structlog.dev.ConsoleRenderer(colors=True)
            else:
                renderer = structlog.dev.ConsoleRenderer(colors=False)
        except (ImportError, ValueError):
            # Fallback if rich not installed
            renderer = structlog.dev.ConsoleRenderer(colors=False)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatting
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    # Console handler with structlog formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Configure uvicorn loggers to use the same handler/formatter
    for uvicorn_logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.propagate = False

    # Set levels for noisy third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging_config.log_level_sqlalchemy.upper())
    logging.getLogger("httpx").setLevel(logging_config.log_level_httpx.upper())
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(logging_config.log_level_uvicorn_access.upper())
    logging.getLogger("uvicorn.error").setLevel(log_level)

    # Log startup message
    logger = structlog.get_logger(__name__)
    logger.info(
        "logging_configured",
        log_format=logging_config.log_format,
        log_level=log_level,
    )
