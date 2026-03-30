# =============================================================================
# Multi-stage Dockerfile for FastAPI application
# Uses uv for fast dependency installation
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build dependencies
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency files first (better layer caching)
COPY pyproject.toml ./

# Install production dependencies only
RUN uv pip install --system --no-cache -r pyproject.toml

# ---------------------------------------------------------------------------
# Stage 2: Production image
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS production

# Security: run as non-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/

# Switch to non-root user
USER appuser

# Expose default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run with uvicorn — configure workers/host/port via env vars
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-config", "None"]
