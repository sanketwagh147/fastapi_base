"""
Simple secrets management with pluggable loading strategies.

File Structure:
    env_files/
    ├── .env_local           # URLs, non-sensitive config (committed)
    ├── .env_prod            # URLs, non-sensitive config (committed)
    ├── .secrets_local       # Passwords, keys (gitignored)
    └── .secrets_prod        # Passwords, keys (gitignored)

Modes:
    - file: Read from {base_path}/.{env}_secrets (default)
    - env: Read from environment variables {PROJECT}_{SECRET_NAME}
    - custom: Override `load_secret()` method for Vault, AWS, etc.

Usage:
    # Default file mode
    secrets = SecretsLoader()
    db_password = secrets.get("DATABASE_PASSWORD")

    # Environment variable mode
    secrets = SecretsLoader(mode="env")
    db_password = secrets.get("DATABASE_PASSWORD")  # reads EVENTUALLY_DATABASE_PASSWORD

    # Custom mode - subclass and override
    class VaultLoader(SecretsLoader):
        def load_secret(self, name: str) -> str | None:
            return vault_client.read(f"secret/{name}")
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

__all__ = [
    "SecretsLoader",
    "SecretsMode",
    "configure_secrets",
    "get_secret",
    "get_secrets_loader",
    "secret_field",
]

# Default secrets directory (app/env_files relative to this file)
_DEFAULT_SECRETS_DIR = Path(__file__).parent.parent / "env_files"


class SecretsMode(str, Enum):
    """Secret loading modes."""

    FILE = "file"  # Load from secrets file (default)
    ENV = "env"  # Load from environment variables
    CUSTOM = "custom"  # User-provided loader


class SecretsLoader:
    """
    Flexible secrets loader with pluggable strategies.

    Override `load_secret()` for custom implementations (Vault, AWS, etc.)
    """

    def __init__(
        self,
        mode: SecretsMode | str = SecretsMode.FILE,
        project_name: str = "eventually",
        env: str | None = None,
        base_path: str | Path | None = None,
    ) -> None:
        """
        Initialize secrets loader.

        Args:
            mode: "file", "env", or "custom"
            project_name: Project name for env var prefix
            env: Environment (local, dev, prod). Auto-detected from ENV var if None.
            base_path: Secrets directory. Default: app/env_files (local) or /etc/{project_name} (prod)
        """
        self.mode = SecretsMode(mode) if isinstance(mode, str) else mode
        self.project_name = project_name
        self.env = env or os.getenv("ENV", "local")

        # Default: app/env_files for local, /etc/{project_name} for production
        if base_path:
            self.base_path = Path(base_path)
        elif self.env in ("local", "dev"):
            self.base_path = _DEFAULT_SECRETS_DIR
        else:
            self.base_path = Path(f"/etc/{project_name}")

    @property
    def secrets_file(self) -> Path:
        """Path to secrets file: {base_path}/.secrets_{env}"""
        return Path(self.base_path) / f".secrets_{self.env}"

    def get(self, name: str, default: str | None = None) -> str:
        """
        Get a secret value.

        Args:
            name: Secret name (e.g., "DATABASE_PASSWORD")
            default: Default value if not found

        Returns:
            Secret value or default (plain string - let caller wrap if needed)

        Raises:
            ValueError: If secret not found and no default provided
        """
        value = self._load(name)

        if value is not None:
            return value

        if default is not None:
            return default

        # Always raise if secret not found - fail fast on missing configuration
        raise ValueError(self._error_message(name))

    def _load(self, name: str) -> str | None:
        """Load secret based on current mode."""
        if self.mode == SecretsMode.FILE:
            return self._load_from_file(name)
        if self.mode == SecretsMode.ENV:
            return self._load_from_env(name)
        return self.load_secret(name)

    def _load_from_file(self, name: str) -> str | None:
        """Load secret from .{env}_secrets file (KEY=VALUE format)."""
        if not self.secrets_file.exists():
            return None

        try:
            for line in self.secrets_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() == name:
                        return value.strip().strip("'\"")
        except Exception:
            return None

        return None

    def _load_from_env(self, name: str) -> str | None:
        """Load from environment variable: {PROJECT}_{SECRET_NAME}"""
        env_var = f"{self.project_name.upper()}_{name}"
        return os.getenv(env_var)

    def load_secret(self, name: str) -> str | None:
        """
        Override this for custom secret loading (Vault, AWS, etc.)

        Example:
            class VaultLoader(SecretsLoader):
                def load_secret(self, name: str) -> str | None:
                    return vault_client.read(f"secret/{name}")
        """
        msg = (
            "Custom mode requires overriding load_secret() method.\n"
            "Create a subclass and implement load_secret()."
        )
        raise NotImplementedError(msg)

    def _error_message(self, name: str) -> str:
        """Generate helpful error message based on mode."""
        if self.mode == SecretsMode.FILE:
            return (
                f"Required secret '{name}' not found.\n"
                f"  Mode: file\n"
                f"  File: {self.secrets_file}\n"
                f"  Add: {name}=your_value"
            )
        if self.mode == SecretsMode.ENV:
            env_var = f"{self.project_name.upper()}_{name}"
            return (
                f"Required secret '{name}' not found.\n"
                f"  Mode: env\n"
                f"  Expected: {env_var}\n"
                f"  Set: export {env_var}=your_value"
            )
        return f"Required secret '{name}' not found in custom loader."


# =============================================================================
# Global Instance (using container pattern to avoid 'global' statement)
# =============================================================================

_state: dict[str, SecretsLoader | None] = {"loader": None}


def configure_secrets(
    mode: SecretsMode | str = SecretsMode.FILE,
    project_name: str = "eventually",
    base_path: str | None = None,
    loader: SecretsLoader | None = None,
) -> None:
    """
    Configure global secrets loader. Call once at app startup.

    Args:
        mode: "file", "env", or "custom"
        project_name: Project name
        base_path: Override secrets directory
        loader: Custom SecretsLoader instance (for custom mode)
    """
    if loader:
        _state["loader"] = loader
    else:
        _state["loader"] = SecretsLoader(
            mode=mode,
            project_name=project_name,
            base_path=base_path,
        )


def get_secrets_loader() -> SecretsLoader:
    """Get global secrets loader. Auto-configures from env vars if not set."""
    if _state["loader"] is None:
        # Auto-configure from environment
        mode = os.getenv("SECRETS_MODE", "file")
        project_name = os.getenv("SECRETS_PROJECT_NAME", "eventually")
        base_path = os.getenv("SECRETS_BASE_PATH")

        _state["loader"] = SecretsLoader(
            mode=mode,
            project_name=project_name,
            base_path=base_path,
        )

    return _state["loader"]


def get_secret(name: str, default: str | None = None) -> str:
    """Get a secret using the global loader. Raises if not found and no default."""
    return get_secrets_loader().get(name, default)


def secret_field(name: str, default: str | None = None) -> Any:
    """
    Create a Pydantic Field that loads value from secrets.

    Usage in Pydantic models:
        class DatabaseCredentials(BaseSettings):
            password: SecretStr | None = secret_field("DATABASE_PASSWORD")
            user: str = secret_field("DATABASE_USER", default="postgres")

    Args:
        name: Secret name (e.g., "DATABASE_PASSWORD")
        default: Default value if secret not found

    Returns:
        Pydantic Field with default_factory that loads from secrets
    """

    return Field(default_factory=lambda: get_secret(name, default))
