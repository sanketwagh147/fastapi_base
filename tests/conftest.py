"""Pytest configuration and fixtures.

Provides:
    - Sync TestClient for unit tests (client)
    - Async httpx client for integration tests (async_client)
    - Database session override for isolated tests (override_get_db)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client for unit tests.

    Usage:
        def test_health(client):
            response = client.get("/api/health")
            assert response.status_code == 200
    """
    return TestClient(app)
