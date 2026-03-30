"""Pydantic schemas for API request/response contracts.

Organize schemas by domain:
    schemas/
    ├── __init__.py      # Common schemas (pagination, responses)
    ├── user.py          # UserCreate, UserRead, UserUpdate
    └── auth.py          # LoginRequest, TokenResponse
"""

from .base import PaginatedResponse, SortOrder, SuccessResponse

__all__ = [
    "PaginatedResponse",
    "SortOrder",
    "SuccessResponse",
]
