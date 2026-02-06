"""Example: Using structured logging in your application.

This file demonstrates how to use the centralized logging system
with request correlation IDs and structured output.
"""

import logging

# =============================================================================
# Basic Usage - Works everywhere in your app
# =============================================================================

# Get a logger for this module
logger = logging.getLogger(__name__)


def example_basic_logging():
    """Basic logging with structured context."""
    # Simple log message
    logger.info("User logged in")

    # Add structured context (key-value pairs)
    logger.info("User created", user_id=123, email="test@example.com")

    # Different log levels
    logger.debug("Debug information", step="validation")
    logger.warning("Slow query detected", duration_ms=1500, query="SELECT *")
    logger.error("Failed to connect", service="postgres", retry_count=3)


# =============================================================================
# In Route Handlers - Request ID automatically included
# =============================================================================

from fastapi import APIRouter

router = APIRouter()


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """Example route handler with automatic request_id in logs."""
    logger.info("Fetching user", user_id=user_id)

    # All logs in this request context will have the same request_id
    logger.debug("Checking cache", cache_key=f"user:{user_id}")

    # Simulate some work
    logger.info("User found", user_id=user_id, cached=False)

    return {"id": user_id}


# =============================================================================
# Creating Specialized Loggers
# =============================================================================

# Audit logger for security/compliance
audit_logger = logging.getLogger("myapp.audit")


def log_payment(user_id: int, amount: float):
    """Log payment events to audit trail."""
    audit_logger.info(
        "payment_processed",
        user_id=user_id,
        amount=amount,
        currency="USD",
        event_type="PAYMENT",
    )


# Performance/metrics logger
metrics_logger = logging.getLogger("myapp.metrics")


def log_api_latency(endpoint: str, duration_ms: float):
    """Log API performance metrics."""
    metrics_logger.info(
        "api_latency",
        endpoint=endpoint,
        duration_ms=duration_ms,
        threshold_exceeded=duration_ms > 1000,
    )


# =============================================================================
# Expected Output
# =============================================================================

# LOCAL (LOG_FORMAT=console):
# 2024-02-05 10:30:45 [info     ] User created               user_id=123 email=test@example.com
# 2024-02-05 10:30:46 [info     ] Fetching user              user_id=456 request_id=abc123def456

# PRODUCTION (LOG_FORMAT=json):
# {"event": "User created", "level": "info", "timestamp": "2024-02-05T10:30:45Z", "logger": "app.routes.users", "user_id": 123, "email": "test@example.com"}
# {"event": "Fetching user", "level": "info", "timestamp": "2024-02-05T10:30:46Z", "logger": "app.routes.users", "user_id": 456, "request_id": "abc123def456"}
