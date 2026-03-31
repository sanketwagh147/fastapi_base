# FastAPI Backend Template

Opinionated FastAPI starter focused on async I/O, structured configuration, connection pooling, standardized errors, and route auto-discovery.
The repository is intended to be a base backend template rather than a finished product. It gives you the application shell, environment loading, HTTP/database plumbing, logging, auth dependency stubs, and testing scaffolding needed to start a service quickly.

## What is included
- FastAPI application bootstrapping with lifespan-based startup and shutdown
- Async SQLAlchemy engine and session management
- Shared httpx async client pool
- Route auto-discovery from `app/routes`
- Centralized exception hierarchy and JSON error responses
- Pydantic settings for environment-driven configuration
- Structured logging with correlation IDs
- Base repository and response schema helpers
- Docker, docker compose, Makefile, Ruff, MyPy, and pytest setup

## Current project layout
fastapi-backend/
├── app/
│   ├── main.py
│   ├── main_config.py
│   ├── core/
│   │   ├── auth.py
│   │   ├── base_repository.py
│   │   ├── config_loader.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── http_calls.py
│   │   ├── lifespan.py
│   │   ├── logging_config.py
│   │   ├── route_discovery.py
│   │   ├── secrets.py
│   │   └── exceptions/
│   ├── env_files/
│   │   ├── .env_base
│   │   ├── .env_local
│   │   ├── .env.example
│   │   └── .secrets_local.example
│   ├── models/
│   │   └── base.py
│   ├── repository/
│   ├── routes/
│   │   ├── auth_examples.py
│   │   └── health.py
│   └── schemas/
│       └── base.py
├── tests/
│   ├── conftest.py
│   └── test_exceptions.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── pyproject.toml
## Quick start

### Requirements
- Python 3.11+
- `uv`

### Install dependencies
```bash
uv sync --extra dev
```
If you prefer editable install style tooling instead of `uv sync`, the repository also supports:

```bash
make dev
```

### Local configuration
This template loads configuration from `app/env_files/.env_base` and then `app/env_files/.env_<ENV>`.

For local development, the committed defaults already point to:
- `ENV=local`
- host `0.0.0.0`
- port `8000`
- PostgreSQL via `postgresql+asyncpg`

Create your local secrets file from the example template:
```bash
cp app/env_files/.secrets_local.example app/env_files/.secrets_local
```
Then update the credentials in `app/env_files/.secrets_local`.

### Start dependencies
If you want a local PostgreSQL instance via Docker:

```bash
docker compose up -d postgres
```

### Run the API
```bash
make run
```

This uses the Python module entrypoint so the app keeps the repository's structured logging configuration.

### Available endpoints
- `GET /api/`
- `GET /api/health`
- `GET /api/health/ready`
- `GET /api/auth-examples/me`
- `GET /api/auth-examples/me/active`
- `GET /api/auth-examples/admin-only`
- `GET /api/auth-examples/editor-or-admin`

OpenAPI docs are available by default at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Configuration model
Configuration is defined in `app/main_config.py` and loaded through Pydantic settings.

Load order:
1. Environment variables
2. `app/env_files/.env_base`
3. `app/env_files/.env_<ENV>`
4. Secret lookups for fields configured through `secret_field(...)`

The environment value is normalized, so both lowercase and uppercase forms like `local` and `LOCAL` work.
### Important config groups

- `Settings`: host, port, reload, workers, debug, environment
- `FastAPIConfig`: title, docs URLs, root path, debug
- `DatabaseConfig`: async SQLAlchemy URL and pool settings
- `CORSConfig`: origins, methods, headers, credentials
- `LoggingConfig`: log format and log levels
- `JWTConfig`: JWT settings placeholder for future auth implementation

## Architecture notes
### Application startup

- Logging is configured before the app instance is created
- FastAPI lifespan initializes the shared database pool and shared HTTP client
- Routers are auto-discovered from `app/routes`
- Exception handlers are registered centrally

### Database layer
- `app/core/database.py` manages a singleton async engine and sessionmaker
- `app/core/base_repository.py` provides generic CRUD, filtering, paging, and count helpers
- `app/models/base.py` contains the shared SQLAlchemy base and timestamp mixins

### HTTP client layer
- `app/core/http_calls.py` exposes a shared `httpx.AsyncClient`
- Timeout, retry, and pool settings are configurable through Pydantic models

### Auth layer
- `app/core/auth.py` currently provides dependency stubs and role checks
- The token validation path is intentionally a placeholder and must be replaced with real JWT verification before production use

## Validation commands
These commands are currently passing in the repository:

```bash
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/pytest -q
```

There is also a convenience target for most day-to-day checks:

```bash
make check
```

## Docker usage
Run the whole local stack:

```bash
docker compose up --build
```

The Docker image starts the app through `python -m app.main`, which preserves the app's logging setup and runtime configuration.

## How to extend this template
Typical next steps for a real service:

1. Add domain models under `app/models`
2. Add repositories under `app/repository`
3. Add route modules under `app/routes`
4. Replace the auth placeholder with real JWT verification
5. Add domain-specific tests beyond the shipped exception coverage

## What this template does not include yet
The project is usable as a starting point, but a few production-grade pieces are still intentionally left for the service owner to add:

- Alembic migrations
- Real authentication and token issuance
- Service layer examples for domain orchestration
- Background job or queue integration
- CI workflow files
- Pre-commit hooks
- Metrics and tracing exporters

If your goal is a "ready to go" backend template for multiple services, those are the next highest-value additions.

**Not included** (by design):
- ❌ Authentication/authorization (project-specific)
- ❌ Caching layer (use Redis separately)
- ❌ Message queues (use Celery/RabbitMQ separately)
- ❌ File storage (use S3/MinIO separately)

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [httpx Documentation](https://www.python-httpx.org/)

## 📄 License

MIT
