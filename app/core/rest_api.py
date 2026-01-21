"""
HTTP client connection pool with httpx for FastAPI applications.

This module provides a singleton HTTP client pool for making external API calls
with connection reuse, retry logic, and comprehensive timeout management.

Key Features:
    - Connection pooling for efficient resource usage
    - HTTP/2 support for multiplexing requests
    - Configurable timeouts (connect, read, write, pool)
    - Automatic retry on transient failures
    - Keep-alive connection management
    - SSL certificate verification
    - Redirect following

Design Philosophy:
    - Singleton pattern to share connections across the application
    - Async-only operations for optimal concurrency
    - Pydantic models for type-safe configuration
    - Automatic cleanup via lifespan management
    - Thread-safe with asyncio locks

Why httpx over aiohttp?
    - More requests-like API (easier migration)
    - Built-in HTTP/2 support
    - Better connection pooling defaults
    - Excellent type hints and async support
    - Synchronous client available for testing

Configuration Example:
    config = ClientConfig(
        timeout=TimeoutConfig(connect=5.0, read=30.0),
        pool=PoolConfig(max_connections=100, max_keepalive=20),
        retry=RetryConfig(max_retries=3),
        http2=True,
        verify_ssl=True
    )
    HttpxRestClientPool.configure(config)

Usage in FastAPI:
    # In startup event
    @app.on_event("startup")
    async def startup():
        HttpxRestClientPool.configure(custom_config)

    # In endpoints
    async with HttpxRestClientPool.get_client() as client:
        response = await client.get("https://api.example.com/data")
        data = response.json()

    # Or use the convenience function
    data = await fetch_url("https://api.example.com/data")

Performance Considerations:
    - Connection pooling reduces TCP handshake overhead
    - Keep-alive reuses connections for multiple requests
    - HTTP/2 allows request multiplexing
    - Configurable limits prevent resource exhaustion

Best Practices:
    - Configure pool size based on expected concurrent requests
    - Set appropriate timeouts to avoid hanging requests
    - Use retry logic for transient network errors
    - Enable SSL verification in production
    - Monitor connection pool metrics
"""

import asyncio
import warnings
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

__all__ = [
    "ClientConfig",
    "fetch_url",
    "http_pool_lifespan",
]


class TimeoutConfig(BaseModel):
    """HTTP client timeout settings."""

    connect: float = Field(default=5.0, description="Connection timeout (seconds)")
    read: float = Field(default=30.0, description="Read timeout (seconds)")
    write: float = Field(default=30.0, description="Write timeout (seconds)")
    pool: float = Field(default=30.0, description="Pool timeout (seconds)")

    def to_httpx_timeout(self) -> httpx.Timeout:
        """Convert to httpx.Timeout."""
        return httpx.Timeout(**self.model_dump())


class PoolConfig(BaseModel):
    """Connection pool settings."""

    max_connections: int = Field(default=100, description="Max total connections")
    max_keepalive: int = Field(default=20, description="Max idle connections")
    keepalive_expiry: float = Field(default=30.0, description="Idle connection TTL (seconds)")


class RetryConfig(BaseModel):
    """Retry settings for failed requests."""

    max_retries: int = Field(default=3, description="Max retry attempts")


class ClientConfig(BaseModel):
    """HTTP client configuration."""

    timeout: TimeoutConfig = Field(default_factory=TimeoutConfig)
    pool: PoolConfig = Field(default_factory=PoolConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    http2: bool = Field(default=True, description="Enable HTTP/2")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    follow_redirects: bool = Field(default=True, description="Follow redirects")


class HttpxRestClientPool:
    """Singleton HTTP client pool for FastAPI with connection reuse."""

    _client: httpx.AsyncClient | None = None
    _config: ClientConfig = ClientConfig()
    _lock: asyncio.Lock | None = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create lock for current event loop."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    def configure(cls, config: ClientConfig | None = None) -> None:
        """Set custom client configuration."""
        if config is not None:
            cls._config = config

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get shared HTTP client (async-safe)."""
        if cls._client is None:
            async with cls._get_lock():
                if cls._client is None:
                    limits = httpx.Limits(
                        max_connections=cls._config.pool.max_connections,
                        max_keepalive_connections=cls._config.pool.max_keepalive,
                        keepalive_expiry=cls._config.pool.keepalive_expiry,
                    )

                    transport = httpx.AsyncHTTPTransport(
                        retries=cls._config.retry.max_retries,
                        http2=cls._config.http2,
                    )

                    cls._client = httpx.AsyncClient(
                        transport=transport,
                        limits=limits,
                        timeout=cls._config.timeout.to_httpx_timeout(),
                        verify=cls._config.verify_ssl,
                        follow_redirects=cls._config.follow_redirects,
                    )
        return cls._client

    @classmethod
    async def dispose(cls) -> None:
        """Close client and release resources."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
            cls._lock = None


@asynccontextmanager
async def http_pool_lifespan(
    _app: FastAPI, config: ClientConfig | None = None
) -> AsyncIterator[None]:
    """FastAPI lifespan for HTTP pool management.

    Example:
        app = FastAPI(lifespan=http_pool_lifespan)

        # With custom config:
        from functools import partial
        app = FastAPI(lifespan=partial(http_pool_lifespan, config=my_config))
    """
    if config is not None:
        HttpxRestClientPool.configure(config)

    await HttpxRestClientPool.get_client()
    try:
        yield
    finally:
        await HttpxRestClientPool.dispose()


def setup_http_pool(app: FastAPI, config: ClientConfig | None = None) -> None:
    """Configure HTTP pool lifecycle hooks.

    Deprecated:
        Use http_pool_lifespan() instead. This uses deprecated @app.on_event().
    """
    warnings.warn(
        "setup_http_pool is deprecated, use http_pool_lifespan instead",
        DeprecationWarning,
        stacklevel=2,
    )
    if config is not None:
        HttpxRestClientPool.configure(config)

    @app.on_event("startup")
    async def initialize_http_pool() -> None:
        await HttpxRestClientPool.get_client()

    @app.on_event("shutdown")
    async def cleanup_http_pool() -> None:
        await HttpxRestClientPool.dispose()


async def fetch_url(
    url: str,
    method: str = "GET",
    raise_for_status: bool = True,
    return_json: bool = True,
    **kwargs: Any,
) -> Any:
    """Make HTTP request using the shared connection pool.

    Args:
        url: Request URL.
        method: HTTP method (default: GET).
        raise_for_status: Raise on 4xx/5xx (default: True).
        return_json: Parse response as JSON (default: True).
        **kwargs: Passed to httpx.request().

    Returns:
        JSON dict if return_json=True, else httpx.Response.

    Raises:
        httpx.HTTPStatusError: On 4xx/5xx if raise_for_status=True.
        httpx.RequestError: On network errors.
    """
    client = await HttpxRestClientPool.get_client()
    response = await client.request(method, url, **kwargs)

    if raise_for_status:
        response.raise_for_status()

    if return_json:
        return response.json()

    return response
