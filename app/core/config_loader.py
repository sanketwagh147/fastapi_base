"""Environment detection and .env file selection utilities."""

import os

from app.core.enums import Environment

__all__ = ["Environment", "get_current_environment", "get_env_file", "get_env_files"]


def get_current_environment() -> Environment:
    """Get current environment from ENV variable (defaults to LOCAL)."""
    env_value = os.getenv("ENV", Environment.LOCAL.value)
    try:
        return Environment(env_value)
    except ValueError:
        return Environment.LOCAL


def get_env_file(override: Environment | None = None) -> str:
    """Get .env file path for current environment.

    Args:
        override: Override environment (local mode only)

    Returns:
        Path to .env file (e.g., "env_files/.env_local")
    """
    env = os.getenv("ENV", Environment.LOCAL.value)

    # Allow override only in local environment for testing
    if env == Environment.LOCAL.value and override:
        env = override.value

    return f"env_files/.env_{env}"


def get_env_files(override: Environment | None = None) -> list[str]:
    """Get .env files to load (base + environment-specific).

    Args:
        override: Override environment (local mode only)

    Returns:
        List of .env file paths in load order
    """
    env_specific = get_env_file(override)
    return ["env_files/.env_base", env_specific]
