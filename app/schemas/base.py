"""Base schemas shared across the application."""

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SortOrder(str, Enum):
    """Sort direction for paginated queries."""

    ASC = "asc"
    DESC = "desc"


class SuccessResponse(BaseModel):
    """Standard success envelope."""

    success: bool = True
    message: str = "OK"
    data: Any = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper.

    Usage in routes:
        @router.get("/users", response_model=PaginatedResponse[UserRead])
        async def list_users(page: int = 1, size: int = 20, db = Depends(get_db)):
            repo = UserRepository(User, db)
            items, total = await repo.get_page(page=page, size=size)
            return PaginatedResponse.build(items=items, total=total, page=page, size=size)
    """

    items: list[T]
    total: int = Field(description="Total number of records matching the query")
    page: int = Field(description="Current page number (1-based)")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")

    @classmethod
    def build(cls, *, items: list[T], total: int, page: int, size: int) -> "PaginatedResponse[T]":
        """Construct a paginated response from query results."""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)
