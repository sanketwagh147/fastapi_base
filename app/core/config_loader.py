"""Environment detection and .env file selection utilities."""

import os
from pathlib import Path

from app.core.enums import Environment

__all__ = ["Environment", "get_current_environment", "get_env_file", "get_env_files"]

# Get the directory where this file is located (app/core/)
_CURRENT_DIR = Path(__file__).parent
# Navigate to app/env_files/ directory
_ENV_FILES_DIR = _CURRENT_DIR.parent / "env_files"


def get_current_environment() -> Environment:
    """Get current environment from ENV variable (defaults to LOCAL)."""
    env_value = os.getenv("ENV", Environment.LOCAL.value)
    try:
        return Environment(env_value)
    except ValueError:
        return Environment.LOCAL


def get_env_file(override: Environment | None = None) -> str:
    """GAbsolute path to .env file (e.g., "/path/to/app/env_files/.env_local")"""
    env = os.getenv("ENV", Environment.LOCAL.value)

    # Allow override only in local environment for testing
    if env == Environment.LOCAL.value and override:
        env = override.value

    return str(_ENV_FILES_DIR / f".env_{env}")


def get_env_files(override: Environment | None = None) -> list[str]:
    """Get .env files to load (base + environment-specific).

    Args:
        override: Override environment (local mode only)

    Returns:
        List of absolute .env file paths in load order (base first, then environment-specific)
    """
    env_specific = get_env_file(override)
    base_file = str(_ENV_FILES_DIR / ".env_base")
    return [base_file, env_specific]
