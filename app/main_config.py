"""FastAPI configuration with environment variables and K8s secrets support."""
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# LOCAL DEBUG OVERRIDE - Change this to test other environments locally
# =============================================================================
LOCAL_ENV_OVERRIDE: "Environment | None" = None  # e.g., Environment.UATBIZ


# =============================================================================
# K8s Secrets Config
# =============================================================================
# Secret path: /etc/{SECRETS_FOLDER_NAME}/{PROJECT_KEY}_{secret_name}
# e.g., /etc/secrets/eventually_db_password
SECRETS_FOLDER_NAME: str = os.getenv("SECRETS_FOLDER_NAME", "secrets")
PROJECT_KEY: str = os.getenv("PROJECT_KEY", "eventually")
SECRETS_BASE_PATH: str = f"/etc/{SECRETS_FOLDER_NAME}" if SECRETS_FOLDER_NAME else ""


class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    UAT = "uat"
    UATBIZ = "uatbiz"
    PREPROD = "preprod"
    SANITY = "sanity"
    PROD = "prod"


def read_secret_from_file(secret_name: str, base_path: str | None) -> str | None:
    """Read secret from K8s mounted file."""
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
    """Get K8s secret filename: {PROJECT_KEY}_{secret_name}"""
    return f"{PROJECT_KEY}_{secret_name}"


def get_secret(env_var: str, secret_file_name: str | None = None, default: str | None = None) -> str | None:
    """Get secret: K8s file > env var > {env_var}_FILE > default."""
    if secret_file_name and SECRETS_BASE_PATH:
        k8s_name = get_k8s_secret_name(secret_file_name)
        if value := read_secret_from_file(k8s_name, SECRETS_BASE_PATH):
            return value
    if value := os.getenv(env_var):
        return value
    if file_path := os.getenv(f"{env_var}_FILE"):
        if value := read_secret_from_file(Path(file_path).name, str(Path(file_path).parent)):
            return value
    return default


def get_env_file(override: Environment | None = None) -> str:
    """Get .env file path. Override only works when ENV=local."""
    env = os.getenv("ENV", Environment.LOCAL.value)
    if env == Environment.LOCAL.value and override:
        env = override.value
    return f".env_{env}"


ENV_FILE = get_env_file(LOCAL_ENV_OVERRIDE)


# =============================================================================
# Config Classes
# =============================================================================

class DatabaseCredentials(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="DATABASE_", extra="ignore")

    host: str
    port: int = 5432
    user: str | None = Field(default=None)
    password: SecretStr | None = Field(default=None)
    db_name: str

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
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="DATABASE_", extra="ignore")

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


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="REDIS_", extra="ignore")

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


class APIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="API_", extra="ignore")

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


class CORSConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="CORS_", extra="ignore")

    allow_origins: str = "http://localhost:5173,http://localhost:3000"
    allow_credentials: bool = True
    allow_methods: str = "*"
    allow_headers: str = "*"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allow_origins.split(",")]

    @property
    def methods_list(self) -> list[str]:
        return ["*"] if self.allow_methods == "*" else [m.strip() for m in self.allow_methods.split(",")]

    @property
    def headers_list(self) -> list[str]:
        return ["*"] if self.allow_headers == "*" else [h.strip() for h in self.allow_headers.split(",")]


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="LOG_", extra="ignore")

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False
    file_path: str | None = None


class FastAPIConfig(BaseSettings):
    """FastAPI application configuration."""
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="FASTAPI_", extra="ignore")

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


class JWTConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="JWT_", extra="ignore")

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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    env: Environment = Field(default=Environment.LOCAL)
    app_name: str = Field(default="Eventually API")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    secret_key: SecretStr | None = Field(default=None)
    host: str = Field(default="0.0.0.0")
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
            raise ValueError(f"{info.field_name} cannot be True in production")
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


# =============================================================================
# Lazy Loaders (cached)
# =============================================================================

@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_database_config() -> DatabaseConfig:
    return DatabaseConfig()

@lru_cache
def get_cors_config() -> CORSConfig:
    return CORSConfig()

@lru_cache
def get_logging_config() -> LoggingConfig:
    return LoggingConfig()

@lru_cache
def get_fastapi_config() -> FastAPIConfig:
    return FastAPIConfig()

@lru_cache
def get_redis_config() -> RedisConfig:
    return RedisConfig()

@lru_cache
def get_api_config() -> APIConfig:
    return APIConfig()

@lru_cache
def get_jwt_config() -> JWTConfig:
    return JWTConfig()


# =============================================================================
# Global Instances (core configs only)
# =============================================================================

settings = get_settings()
database_config = get_database_config()
cors_config = get_cors_config()
logging_config = get_logging_config()
fastapi_config = get_fastapi_config()

# Optional - uncomment if needed:
# redis_config = get_redis_config()
# api_config = get_api_config()
# jwt_config = get_jwt_config()
