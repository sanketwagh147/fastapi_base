"""Exception handlers for FastAPI application.

Provides centralized exception handling with standardized error responses.
"""

import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .http_exceptions import AppError, ErrorResponse, InternalServerError

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom AppException and its subclasses.

    Args:
        request: FastAPI request
        exc: Application exception

    Returns:
        JSON response with standardized error format
    """
    error_response = exc.to_error_response(path=request.url.path)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors (422).

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON response with validation error details
    """
    error_response = ErrorResponse(
        error_code="ValidationError",
        message="Request validation failed",
        detail={"errors": exc.errors()},
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(exclude_none=True),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle SQLAlchemy IntegrityError (database constraints).

    Args:
        request: FastAPI request
        exc: Integrity error

    Returns:
        JSON response with constraint violation details
    """
    logger.error(f"Database integrity error: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error_code="IntegrityError",
        message="Database constraint violation",
        detail={"database_error": str(exc.orig) if hasattr(exc, "orig") else str(exc)},
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response.model_dump(exclude_none=True),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions (500).

    Args:
        request: FastAPI request
        exc: Unexpected exception

    Returns:
        JSON response with generic error message
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    # Convert to internal server exception
    internal_exc = InternalServerError(
        message="An unexpected error occurred",
        detail={"error": str(exc)} if logger.level == logging.DEBUG else None,
    )

    error_response = internal_exc.to_error_response(path=request.url.path)

    return JSONResponse(
        status_code=internal_exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


def register_exception_handlers(app: Any) -> None:
    """Register all exception handlers with FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
