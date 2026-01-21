"""Environment detection and .env file selection utilities."""

import os

from app.core.enums import Environment

__all__ = ["Environment", "get_current_environment", "get_env_file", "get_env_files"]


def get_current_environment() -> Environment:
    """Get current environment from ENV variable.

    Returns:
        Current Environment enum value, defaults to LOCAL
    """
    env_value = os.getenv("ENV", Environment.LOCAL.value)
    try:
        return Environment(env_value)
    except ValueError:
        return Environment.LOCAL


def get_env_file(override: Environment | None = None) -> str:
    """Get .env file path based on current environment.

    The override parameter only works when ENV=local to allow local testing
    of other environment configurations.

    Args:
        override: Optional environment to override (only works in local mode)

    Returns:
        Path to .env file (e.g., "env_files/.env_local", "env_files/.env_prod")

    Example:
        >>> get_env_file()
        "env_files/.env_local"
        >>> get_env_file(Environment.PROD)  # Only works if ENV=local
        "env_files/.env_prod"
    """
    env = os.getenv("ENV", Environment.LOCAL.value)

    # Allow override only in local environment for testing
    if env == Environment.LOCAL.value and override:
        env = override.value

    return f"env_files/.env_{env}"


def get_env_files(override: Environment | None = None) -> list[str]:
    """Get list of .env files to load (base + environment-specific).

    Loads env_files/.env_base first, then environment-specific file.
    Environment-specific values override base values.

    Args:
        override: Optional environment to override (only works in local mode)

    Returns:
        List of .env file paths in load order

    Example:
        >>> get_env_files()
        ["env_files/.env_base", "env_files/.env_local"]
    """
    env_specific = get_env_file(override)
    return ["env_files/.env_base", env_specific]
