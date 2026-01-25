import logging
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/cache",
    tags=["timed_cache"],
)

logger = logging.getLogger(__name__)


logging.basicConfig(
    format="%(asctime)s [%(threadName)s] %(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class CacheStatusInput(BaseModel):
    nums: list[int]


class CacheStatusResponse(BaseModel):
    """Schema for timed cache status response."""

    status: str
    cached_sum: int | None = None


def cache_me_auto_expire(ttl: int = 10, cleanup_interval: int = 5) -> Callable:
    """Decorator Factory that returns caching decorator with auto expiry"""

    def decorator_factory(fn: Callable) -> Callable:
        _cache: dict[Any, tuple[Any, float]] = {}
        _lock = threading.Lock()
        _cleanup_thread = None

        _stop_cleanup = threading.Event()

        def cleanup_expired() -> None:
            while not _stop_cleanup.is_set():
                time.sleep(cleanup_interval)
                # logger.debug("Running auto cleanup...")
                current_time = time.time()

                with _lock:
                    expired_keys = [
                        key
                        for key, (_, cached_time) in _cache.items()
                        if current_time - cached_time >= ttl
                    ]

                    for key in expired_keys:
                        del _cache[key]
                        logger.debug(f"Auto-Cleared expired cache for args: {key}")

        def start_cleanup_thread() -> None:
            nonlocal _cleanup_thread
            if _cleanup_thread is None or not _cleanup_thread.is_alive():
                _stop_cleanup.clear()

                _cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
                _cleanup_thread.start()

        @wraps(fn)
        def wrapper(*args: Any) -> Any:
            start_cleanup_thread()

            current_time = time.time()

            with _lock:
                if args in _cache:
                    result, cached_time = _cache[args]
                    if current_time - cached_time < ttl:
                        logger.debug(f"Cache hit for args: {args}")
                        return result
                    logger.debug(f"Cache expired for {args}. recalculating")

            result = fn(*args)

            with _lock:
                _cache[args] = (result, current_time)

            return result

        wrapper.cache = _cache  # type: ignore[attr-defined]
        wrapper.stop_cleanup = lambda: _stop_cleanup.set()  # type: ignore[attr-defined]

        return wrapper

    return decorator_factory


@cache_me_auto_expire(10, 5)
def calculate_sum(*args) -> int:
    return sum(args)


@cache_me_auto_expire(10, 5)
def calculate_sum_1(*args) -> int:
    return sum(args)


@cache_me_auto_expire(10, 5)
def calculate_sum_2(*args) -> int:
    return sum(args)


@cache_me_auto_expire(10, 5)
def calculate_sum_3(*args) -> int:
    return sum(args)


@cache_me_auto_expire(10, 5)
def calculate_sum_4(*args) -> int:
    return sum(args)


@cache_me_auto_expire(10, 5)
def calculate_sum_5(*args) -> int:
    return sum(args)


@router.post("/status")
async def cache_status(nums: CacheStatusInput) -> CacheStatusResponse:
    """Endpoint to check the status of the timed cache with cached sum."""
    cached_sum = calculate_sum(*nums.nums)
    cached_sum = calculate_sum_1(*nums.nums)
    cached_sum = calculate_sum_2(*nums.nums)
    cached_sum = calculate_sum_3(*nums.nums)
    cached_sum = calculate_sum_4(*nums.nums)
    cached_sum = calculate_sum_5(*nums.nums)
    return CacheStatusResponse(status="Timed cache is operational", cached_sum=cached_sum)
