"""Exception handling package for FastAPI application.

Provides custom exception hierarchy and handlers for standardized error responses.
"""

from .handlers import register_exception_handlers
from .http_exceptions import (
    AppError,
    BadRequestError,
    ClientError,
    ConflictError,
    ErrorResponse,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    NotImplementedAppError,
    ServerError,
    ServiceUnavailableError,
    UnauthorizedError,
    UnprocessableEntityError,
)

__all__ = [
    # Base exceptions
    "AppError",
    # Client exceptions (4xx)
    "BadRequestError",
    "ClientError",
    "ConflictError",
    # Models
    "ErrorResponse",
    "ForbiddenError",
    # Server Error (5xx)
    "InternalServerError",
    "NotFoundError",
    "NotImplementedAppError",
    "ServerError",
    "ServiceUnavailableError",
    "UnauthorizedError",
    "UnprocessableEntityError",
    # Handlers
    "register_exception_handlers",
]
