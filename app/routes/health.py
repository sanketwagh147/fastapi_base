"""Health check and readiness endpoints."""

import logging

from fastapi import APIRouter

from app.main_config import fastapi_config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["health"],
)


@router.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": fastapi_config.title,
        "version": fastapi_config.version,
        "docs": fastapi_config.docs_url,
    }


@router.get("/health")
async def health_check():
    """Liveness probe — confirms the process is running."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe — confirms the app can serve traffic.

    Checks database connectivity. Add more checks (Redis, external APIs)
    as your application grows.
    """
    checks: dict[str, str] = {}

    # Database check
    try:
        from sqlalchemy import text

        from app.core.database import AsyncDBPool

        async with AsyncDBPool.get_session() as session:
            await session.execute(text(\"SELECT 1\"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.warning("Readiness: database check failed: %s", exc)
        checks["database"] = "unavailable"

    overall = "ready" if all(v == "ok" for v in checks.values()) else "not_ready"
    status_code = 200 if overall == "ready" else 503

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "checks": checks},
    )
