"""Health check endpoints for monitoring."""
from fastapi import APIRouter
from datetime import datetime

# Everything in one place - clean and simple!
router = APIRouter(
    prefix="/api",
    tags=["health",],
)


@router.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Eventually API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}