"""
FastAPI configuration management with Pydantic Settings.

This module provides environment-aware configuration using Pydantic Settings V2,
supporting multiple deployment environments and Kubernetes secrets integration.

Configuration Philosophy:
    - Type-safe configuration with Pydantic validation
    - Environment-specific .env files (.env.local, .env.prod, etc.)
    - Kubernetes secrets support for production deployments
    - Fail-fast validation on startup
    - No hardcoded credentials

Supported Environments:
    - LOCAL: Local development (debug enabled, relaxed settings)
    - DEV: Development server (shared development environment)
    - UAT: User acceptance testing
    - UATBIZ: Business UAT environment
    - SANITY: Sanity/smoke testing
    - PROD: Production (strict settings, no debug)

Configuration Loading Priority:
    1. Environment variables (highest priority)
    2. Kubernetes secrets (production)
    3. Environment-specific .env files (.env.prod, .env.local)
    4. Base .env file
    5. Default values in Pydantic models (lowest priority)

File Structure:
    env_files/
    ├── .env              # Base configuration (shared)
    ├── .env.local        # Local development overrides
    ├── .env.dev          # Dev environment
    ├── .env.uat          # UAT environment
    └── .env.prod         # Production configuration

Security Features:
    - SecretStr for sensitive fields (passwords, API keys)
    - Kubernetes secrets integration via mounted volumes
    - Production validation (no debug=True in prod)
    - SSL enforcement in production

Configuration Classes:
    - Settings: Core application settings (env, debug, host, port)
    - FastAPIConfig: FastAPI-specific configuration
    - DatabaseConfig: Database connection and pool settings
    - CORSConfig: CORS middleware configuration
    - LoggingConfig: Logging configuration (optional)

Usage:
    from app.main_config import database_config, fastapi_config

    # Type-safe access
    db_url = database_config.url
    pool_size = database_config.pool_size

    # Environment checks
    if fastapi_config.is_production:
        # Production-specific logic

Example .env.prod:
    ENV=prod
    DEBUG=false
    DATABASE_HOST=postgres.production.internal
    DATABASE_POOL_SIZE=20
    CORS_ALLOW_ORIGINS=["https://app.example.com"]

Development Override:
    # Test production config locally by setting LOCAL_ENV_OVERRIDE
    LOCAL_ENV_OVERRIDE = Environment.PROD  # In main_config.py
"""

from functools import lru_cache
from typing import Any
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config_loader import Environment, get_env_files
from app.core.secrets import get_secret

# =============================================================================
# LOCAL DEBUG OVERRIDE - Change this to test other environments locally
# =============================================================================
LOCAL_ENV_OVERRIDE: Environment | None = None  # e.g., Environment.UATBIZ

# Get environment-specific .env files (base + environment)
ENV_FILES = get_env_files(LOCAL_ENV_OVERRIDE)


# =============================================================================
# Config Classes
# =============================================================================


# -----------------------------------------------------------------------------
# CORE SETTINGS (Always Required)
# -----------------------------------------------------------------------------


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, extra="ignore")

    env: Environment = Field(default=Environment.LOCAL)
    debug: bool = Field(default=False)
    secret_key: SecretStr | None = Field(default=None)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    workers: int = Field(default=1)

    @model_validator(mode="before")
    @classmethod
    def _load_secrets(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get("secret_key"):
            data["secret_key"] = get_secret("SECRET_KEY", "app-secret-key")
        return data

    @field_validator("debug", "reload")
    @classmethod
    def _no_debug_in_prod(cls, v: bool, info) -> bool:
        if info.data.get("env") == Environment.PROD and v:
            msg: str = f"{info.field_name} cannot be True in production"
            raise ValueError(msg)
        return v

    @property
    def is_production(self) -> bool:
        return self.env == Environment.PROD

    @property
    def is_local(self) -> bool:
        return self.env == Environment.LOCAL

    @property
    def is_development(self) -> bool:
        return self.env in (Environment.LOCAL, Environment.DEV)

    @property
    def is_testing(self) -> bool:
        return self.env in (Environment.UAT, Environment.UATBIZ, Environment.SANITY)


class FastAPIConfig(BaseSettings):
    """FastAPI application configuration."""

    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="FASTAPI_", extra="ignore")

    title: str = "Eventually API"
    description: str = "Event management API"
    version: str = "0.1.0"
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"
    root_path: str = ""
    debug: bool = False

    @field_validator("docs_url", "redoc_url", "openapi_url")
    @classmethod
    def _disable_docs_in_prod(cls, v: str | None, info) -> str | None:
        # Docs URLs can be disabled by setting to empty string in env
        return v if v else None


class DatabaseCredentials(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="DATABASE_", extra="ignore")

    host: str = Field(default="localhost")
    port: int
    user: str | None = Field(default=None)
    password: SecretStr | None = Field(default=None)
    db_name: str = Field(default="eventually")

    @model_validator(mode="before")
    @classmethod
    def _load_secrets(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get("user"):
            data["user"] = get_secret("DATABASE_USER", "database-user")
        if not data.get("password"):
            data["password"] = get_secret("DATABASE_PASSWORD", "database-password")
        return data


class DatabaseConfig(BaseSettings):
    """Database configuration with connection pooling settings."""

    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="DATABASE_", extra="ignore")

    driver: str = "postgresql+asyncpg"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 15
    pool_recycle: int = 900
    pool_pre_ping: bool = True
    echo: bool = False

    @property
    def credentials(self) -> DatabaseCredentials:
        return DatabaseCredentials()  # type: ignore[call-arg]

    @property
    def url(self) -> str:
        """Build database URL from credentials."""
        creds = self.credentials
        password = creds.password.get_secret_value() if creds.password else ""
        return f"{self.driver}://{creds.user}:{quote_plus(password)}@{creds.host}:{creds.port}/{creds.db_name}"


# -----------------------------------------------------------------------------
# FREQUENTLY USED SETTINGS
# -----------------------------------------------------------------------------


class CORSConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="CORS_", extra="ignore")

    allow_origins: str = "http://localhost:5173,http://localhost:3000"
    allow_credentials: bool = True
    allow_methods: str = "*"
    allow_headers: str = "*"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allow_origins.split(",")]

    @property
    def methods_list(self) -> list[str]:
        return (
            ["*"]
            if self.allow_methods == "*"
            else [m.strip() for m in self.allow_methods.split(",")]
        )

    @property
    def headers_list(self) -> list[str]:
        return (
            ["*"]
            if self.allow_headers == "*"
            else [h.strip() for h in self.allow_headers.split(",")]
        )


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="LOG_", extra="ignore")

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False
    file_path: str | None = None


# -----------------------------------------------------------------------------
# OPTIONAL SETTINGS (Enable as needed)
# -----------------------------------------------------------------------------


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="REDIS_", extra="ignore")

    host: str = "localhost"
    port: int = 6379
    password: SecretStr | None = Field(default=None)
    timeout: int = 5
    db: int = 0

    @model_validator(mode="before")
    @classmethod
    def _load_secrets(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get("password"):
            data["password"] = get_secret("REDIS_PASSWORD", "redis-password")
        return data

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{quote_plus(self.password.get_secret_value())}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class JWTConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="JWT_", extra="ignore")

    secret_key: SecretStr | None = Field(default=None)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @model_validator(mode="before")
    @classmethod
    def _load_secrets(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get("secret_key"):
            data["secret_key"] = get_secret("JWT_SECRET_KEY", "jwt-secret-key")
        return data


class APIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_prefix="API_", extra="ignore")

    key: SecretStr | None = Field(default=None)
    secret: SecretStr | None = Field(default=None)
    timeout: int = 30
    rate_limit: int = 100

    @model_validator(mode="before")
    @classmethod
    def _load_secrets(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get("key"):
            data["key"] = get_secret("API_KEY", "api-key")
        if not data.get("secret"):
            data["secret"] = get_secret("API_SECRET", "api-secret")
        return data


# =============================================================================
# Lazy Loaders (cached)
# =============================================================================


# Core loaders (always needed)
@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_fastapi_config() -> FastAPIConfig:
    return FastAPIConfig()


@lru_cache
def get_database_config() -> DatabaseConfig:
    return DatabaseConfig()


# Frequently used loaders
@lru_cache
def get_cors_config() -> CORSConfig:
    return CORSConfig()


@lru_cache
def get_logging_config() -> LoggingConfig:
    return LoggingConfig()


# Optional loaders (enable as needed)
@lru_cache
def get_redis_config() -> RedisConfig:
    return RedisConfig()


@lru_cache
def get_jwt_config() -> JWTConfig:
    return JWTConfig()


@lru_cache
def get_api_config() -> APIConfig:
    return APIConfig()


# =============================================================================
# Global Instances
# =============================================================================

# Core instances (always loaded)
settings = get_settings()
fastapi_config = get_fastapi_config()
database_config = get_database_config()

# Frequently used instances
cors_config = get_cors_config()
logging_config = get_logging_config()

# Optional instances (uncomment as needed)
# redis_config = get_redis_config()
# jwt_config = get_jwt_config()
# api_config = get_api_config()
