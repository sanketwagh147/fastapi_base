"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(
    prefix="/api",
    tags=["health"],
)


@router.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Eventually API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint (public)."""
    return {"status": "healthy"}
