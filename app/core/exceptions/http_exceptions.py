"""Custom HTTP exception hierarchy and standardized error responses.

Exception Hierarchy:
    AppError (HTTPException)
    ├── ClientError (4xx errors)
    │   ├── BadRequestError (400)
    │   ├── UnauthorizedError (401)
    │   ├── ForbiddenError (403)
    │   ├── NotFoundError (404)
    │   └── ConflictError (409)
    └── ServerError (5xx errors)
        ├── InternalServerError (500)
        ├── NotImplementedError (501)
        └── ServiceUnavailableError (503)

Usage:
    # Option 1: Pass individual parameters
    raise NotFoundError(
        message="User not found",
        detail={"user_id": 123}
    )

    # Option 2: Pass ErrorResponse object directly
    error = ErrorResponse(
        error_code="USER_NOT_FOUND",
        message="User not found",
        detail={"user_id": 123}
    )
    raise NotFoundError(error)
"""

from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    success: bool = Field(default=False, description="Always False for errors")
    error_code: str = Field(description="Error code identifier")
    message: str = Field(description="Human-readable error message")
    detail: dict[str, Any] | None = Field(default=None, description="Additional error details")
    path: str | None = Field(default=None, description="Request path where error occurred")


class AppError(HTTPException):
    """Base exception for all application HTTP errors."""

    def __init__(
        self,
        message: str | ErrorResponse = "An error occurred",
        error_code: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: dict[str, Any] | None = None,
    ) -> None:
        # Handle ErrorResponse object
        if isinstance(message, ErrorResponse):
            error_response = message
            self.message = error_response.message
            self.error_code = error_response.error_code
            self.detail = error_response.detail
            # Use provided status_code or default
            actual_status_code = status_code
        else:
            # Handle individual parameters
            self.message = message
            self.error_code = error_code or self.__class__.__name__
            self.detail = detail
            actual_status_code = status_code

        super().__init__(status_code=actual_status_code, detail=self.message)

    def to_error_response(self, path: str | None = None) -> ErrorResponse:
        """Convert exception to ErrorResponse object.

        Args:
            path: Request path where error occurred

        Returns:
            ErrorResponse object
        """
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            detail=self.detail,
            path=path,
        )


# ============================================================================
# Client Exceptions (4xx)
# ============================================================================


class ClientError(AppError):
    """Base exception for client errors (4xx)."""

    def __init__(
        self,
        message: str | ErrorResponse = "Client error",
        error_code: str | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status_code, detail)


class BadRequestError(ClientError):
    """400 Bad Request - Invalid request parameters."""

    def __init__(
        self,
        message: str | ErrorResponse = "Bad request",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_400_BAD_REQUEST, detail)


class UnauthorizedError(ClientError):
    """401 Unauthorized - Authentication required."""

    def __init__(
        self,
        message: str | ErrorResponse = "Unauthorized",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_401_UNAUTHORIZED, detail)


class ForbiddenError(ClientError):
    """403 Forbidden - Insufficient permissions."""

    def __init__(
        self,
        message: str | ErrorResponse = "Forbidden",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_403_FORBIDDEN, detail)


class NotFoundError(ClientError):
    """404 Not Found - Resource does not exist."""

    def __init__(
        self,
        message: str | ErrorResponse = "Not found",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_404_NOT_FOUND, detail)


class ConflictError(ClientError):
    """409 Conflict - Resource already exists or state conflict."""

    def __init__(
        self,
        message: str | ErrorResponse = "Conflict",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_409_CONFLICT, detail)


class UnprocessableEntityError(ClientError):
    """422 Unprocessable Entity - Validation error."""

    def __init__(
        self,
        message: str | ErrorResponse = "Unprocessable entity",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


# ============================================================================
# Server Exceptions (5xx)
# ============================================================================


class ServerError(AppError):
    """Base exception for server errors (5xx)."""

    def __init__(
        self,
        message: str | ErrorResponse = "Server error",
        error_code: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status_code, detail)


class InternalServerError(ServerError):
    """500 Internal Server Error - Unexpected server error."""

    def __init__(
        self,
        message: str | ErrorResponse = "Internal server error",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class NotImplementedAppError(ServerError):
    """501 Not Implemented - Feature not yet implemented."""

    def __init__(
        self,
        message: str | ErrorResponse = "Not implemented",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_501_NOT_IMPLEMENTED, detail)


class ServiceUnavailableError(ServerError):
    """503 Service Unavailable - Service temporarily unavailable."""

    def __init__(
        self,
        message: str | ErrorResponse = "Service unavailable",
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code, status.HTTP_503_SERVICE_UNAVAILABLE, detail)
