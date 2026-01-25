"""Test cases for exception handling system."""

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ErrorResponse,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    UnauthorizedError,
    register_exception_handlers,
)


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI application."""
    test_app = FastAPI()
    register_exception_handlers(test_app)
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


# =============================================================================
# Test ErrorResponse Model
# =============================================================================


def test_error_response_model():
    """Test ErrorResponse model creation and validation."""
    error = ErrorResponse(
        error_code="TEST_ERROR",
        message="Test error message",
        detail={"key": "value"},
        path="/test/path",
    )

    assert error.success is False
    assert error.error_code == "TEST_ERROR"
    assert error.message == "Test error message"
    assert error.detail == {"key": "value"}
    assert error.path == "/test/path"


def test_error_response_model_defaults() -> None:
    """Test ErrorResponse model with defaults."""
    error = ErrorResponse(error_code="TEST", message="Test")

    assert error.success is False
    assert error.detail is None
    assert error.path is None


def test_error_response_validation_error() -> None:
    """Test ErrorResponse validation for invalid detail type."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        ErrorResponse(
            error_code="TEST",
            message="Test",
            detail="invalid_string",  # Should be dict
        )


# =============================================================================
# Test Exception Classes with Individual Parameters
# =============================================================================


def test_not_found_error_with_params(app: FastAPI, client: TestClient) -> None:
    """Test NotFoundError with individual parameters."""

    @app.get("/test-not-found")
    async def route():
        raise NotFoundError(
            message="Resource not found", error_code="RESOURCE_NOT_FOUND", detail={"id": 123}
        )

    response = client.get("/test-not-found")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "RESOURCE_NOT_FOUND"
    assert data["message"] == "Resource not found"
    assert data["detail"] == {"id": 123}
    assert data["path"] == "/test-not-found"


def test_bad_request_error(app: FastAPI, client: TestClient) -> None:
    """Test BadRequestError."""

    @app.get("/test-bad-request")
    async def route():
        raise BadRequestError(message="Invalid input", detail={"field": "email"})

    response = client.get("/test-bad-request")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error_code"] == "BadRequestError"
    assert data["message"] == "Invalid input"
    assert data["detail"] == {"field": "email"}


def test_unauthorized_error(app: FastAPI, client: TestClient) -> None:
    """Test UnauthorizedError."""

    @app.get("/test-unauthorized")
    async def route():
        raise UnauthorizedError(message="Authentication required")

    response = client.get("/test-unauthorized")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["error_code"] == "UnauthorizedError"
    assert data["message"] == "Authentication required"


def test_forbidden_error(app: FastAPI, client: TestClient) -> None:
    """Test ForbiddenError."""

    @app.get("/test-forbidden")
    async def route():
        raise ForbiddenError(message="Insufficient permissions")

    response = client.get("/test-forbidden")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["error_code"] == "ForbiddenError"


def test_conflict_error(app: FastAPI, client: TestClient) -> None:
    """Test ConflictError."""

    @app.get("/test-conflict")
    async def route():
        raise ConflictError(message="Resource already exists", detail={"email": "test@example.com"})

    response = client.get("/test-conflict")

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["error_code"] == "ConflictError"
    assert data["detail"] == {"email": "test@example.com"}


def test_internal_server_error(app: FastAPI, client: TestClient) -> None:
    """Test InternalServerError."""

    @app.get("/test-server-error")
    async def route():
        raise InternalServerError(message="Database error", detail={"db": "primary"})

    response = client.get("/test-server-error")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["error_code"] == "InternalServerError"
    assert data["message"] == "Database error"


# =============================================================================
# Test Exception Classes with ErrorResponse Object
# =============================================================================


def test_not_found_error_with_error_response(app: FastAPI, client: TestClient) -> None:
    """Test NotFoundError with ErrorResponse object."""

    @app.get("/test-error-response")
    async def route():
        error = ErrorResponse(
            error_code="USER_NOT_FOUND",
            message="User does not exist",
            detail={"user_id": 456},
        )
        raise NotFoundError(error)

    response = client.get("/test-error-response")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["error_code"] == "USER_NOT_FOUND"
    assert data["message"] == "User does not exist"
    assert data["detail"] == {"user_id": 456}


def test_bad_request_with_error_response(app: FastAPI, client: TestClient) -> None:
    """Test BadRequestError with ErrorResponse object."""

    @app.get("/test-bad-request-obj")
    async def route():
        error = ErrorResponse(
            error_code="INVALID_EMAIL",
            message="Email format is invalid",
            detail={"email": "invalid@email"},
        )
        raise BadRequestError(error)

    response = client.get("/test-bad-request-obj")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error_code"] == "INVALID_EMAIL"
    assert data["message"] == "Email format is invalid"


# =============================================================================
# Test Default Error Messages
# =============================================================================


def test_not_found_error_default_message(app: FastAPI, client: TestClient) -> None:
    """Test NotFoundError with default message."""

    @app.get("/test-default")
    async def route():
        raise NotFoundError()

    response = client.get("/test-default")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["message"] == "Not found"
    assert data["error_code"] == "NotFoundError"


# =============================================================================
# Test Generic Exception Handler
# =============================================================================


def test_generic_exception_handler(app: FastAPI, client: TestClient) -> None:
    """Test generic exception handler for unexpected errors."""

    @app.get("/test-unexpected")
    async def route():
        msg = "Unexpected error"
        raise ValueError(msg)

    response = client.get("/test-unexpected")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["error_code"] == "InternalServerError"
    assert data["message"] == "An unexpected error occurred"
    assert "path" in data


def test_zero_division_error_handling(app: FastAPI, client: TestClient) -> None:
    """Test handling of ZeroDivisionError."""

    @app.get("/test-zero-division")
    async def route():
        return 1 / 0

    response = client.get("/test-zero-division")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["error_code"] == "InternalServerError"


# =============================================================================
# Test Pydantic Validation Error Handler
# =============================================================================


def test_validation_error_handler(app: FastAPI, client: TestClient) -> None:
    """Test Pydantic validation error handling."""

    class TestModel(BaseModel):
        name: str
        age: int

    @app.post("/test-validation")
    async def route(data: TestModel):
        return data

    response = client.post("/test-validation", json={"name": "John", "age": "invalid"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["error_code"] == "ValidationError"
    assert data["message"] == "Request validation failed"
    assert "errors" in data["detail"]


# =============================================================================
# Test to_error_response Method
# =============================================================================


def test_exception_to_error_response_conversion() -> None:
    """Test converting exception to ErrorResponse."""
    exc = NotFoundError(
        message="User not found", error_code="USER_NOT_FOUND", detail={"user_id": 789}
    )

    error_response = exc.to_error_response(path="/users/789")

    assert isinstance(error_response, ErrorResponse)
    assert error_response.error_code == "USER_NOT_FOUND"
    assert error_response.message == "User not found"
    assert error_response.detail == {"user_id": 789}
    assert error_response.path == "/users/789"


# =============================================================================
# Test Error Response Serialization
# =============================================================================


def test_error_response_excludes_none_values(app: FastAPI, client: TestClient) -> None:
    """Test that None values are excluded from response."""

    @app.get("/test-no-detail")
    async def route():
        raise NotFoundError(message="Not found")

    response = client.get("/test-no-detail")

    data = response.json()
    assert "detail" not in data  # Should be excluded when None


def test_error_response_includes_all_fields(app: FastAPI, client: TestClient) -> None:
    """Test that all fields are included when provided."""

    @app.get("/test-all-fields")
    async def route():
        raise NotFoundError(message="Not found", detail={"id": 1})

    response = client.get("/test-all-fields")

    data = response.json()
    assert "success" in data
    assert "error_code" in data
    assert "message" in data
    assert "detail" in data
    assert "path" in data
