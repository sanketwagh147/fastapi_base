"""Example routes demonstrating exception handling.

Run the application and test:
    curl http://localhost:8000/api/test/success
    curl http://localhost:8000/api/test/not-found
    curl http://localhost:8000/api/test/server-error
"""

from fastapi import APIRouter

from app.core.exceptions import InternalServerError, NotFoundError

router = APIRouter(prefix="/test", tags=["Testing"])


@router.get("/success")
async def test_success() -> dict:
    """Test successful response."""
    return {"message": "Success!"}


@router.get("/not-found")
async def test_not_found() -> dict:
    """Test 404 exception."""
    raise NotFoundError(
        message="User not found",
        detail={"user_id": 123, "reason": "User does not exist in database"},
    )


@router.get("/server-error")
async def test_server_error() -> dict:
    """Test 500 exception."""
    raise InternalServerError(message="Database connection failed", detail={"server": "db-primary"})


@router.get("/unexpected-error")
async def test_unexpected_error() -> dict:
    """Test unexpected exception handling."""
    # This will be caught by generic exception handler
    raise ValueError("Unexpected error occurred!")
