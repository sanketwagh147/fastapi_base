"""Secret management utilities for K8s, environment variables, and file-based secrets."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config_loader import get_env_files

__all__ = [
    "SecretsConfig",
    "get_k8s_secret_name",
    "get_secret",
    "read_secret_from_file",
]


class SecretsConfig(BaseSettings):
    """Configuration for K8s secrets paths and naming."""

    model_config = SettingsConfigDict(env_file=get_env_files(), extra="ignore")

    secrets_folder_name: str = Field(default="secrets")
    project_key: str = Field(default="eventually")

    @property
    def secrets_base_path(self) -> str:
        """Compute secrets base path from folder name."""
        return f"/etc/{self.secrets_folder_name}" if self.secrets_folder_name else ""


@lru_cache
def get_secrets_config() -> SecretsConfig:
    """Get cached secrets configuration."""
    return SecretsConfig()


def read_secret_from_file(secret_name: str, base_path: str | None) -> str | None:
    """Read secret from mounted file (K8s secret or Docker secret).

    Args:
        secret_name: Name of the secret file
        base_path: Directory path where secret is mounted

    Returns:
        Secret value as string, or None if not found or error occurred
    """
    if not base_path:
        return None

    secret_path = Path(base_path) / secret_name
    if not secret_path.exists():
        return None

    try:
        return secret_path.read_text().strip()
    except Exception:
        return None


def get_k8s_secret_name(secret_name: str) -> str:
    """Get K8s-style secret filename with project prefix.

    Args:
        secret_name: Base secret name (e.g., "database-password")

    Returns:
        Prefixed secret name (e.g., "eventually_database-password")
    """
    config = get_secrets_config()
    return f"{config.project_key}_{secret_name}"


def get_secret(
    env_var: str, secret_file_name: str | None = None, default: str | None = None
) -> str | None:
    """Get secret value from multiple sources in priority order.

    Priority order:
    1. K8s mounted file: /etc/secrets/{PROJECT_KEY}_{secret_file_name}
    2. Environment variable: {env_var}
    3. File path from env variable: {env_var}_FILE
    4. Default value

    Args:
        env_var: Environment variable name to check
        secret_file_name: K8s secret file name (without project prefix)
        default: Default value if secret not found

    Returns:
        Secret value or None

    Example:
        >>> get_secret("DATABASE_PASSWORD", "database-password", "default_pass")
        # Checks: /etc/secrets/eventually_database-password
        # Then: $DATABASE_PASSWORD
        # Then: file at $DATABASE_PASSWORD_FILE
        # Finally: returns "default_pass"
    """

    # 1. Try K8s mounted secret file
    if secret_file_name:
        config = get_secrets_config()
        if config.secrets_base_path:
            k8s_name = get_k8s_secret_name(secret_file_name)
            if value := read_secret_from_file(k8s_name, config.secrets_base_path):
                return value

    # 2. Try environment variable
    if value := os.getenv(env_var):
        return value

    # 3. Try file path from {ENV_VAR}_FILE pattern
    if file_path := os.getenv(f"{env_var}_FILE"):
        path = Path(file_path)
        if value := read_secret_from_file(path.name, str(path.parent)):
            return value

    # 4. Return default
    return default
