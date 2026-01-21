# FastAPI Backend Template

> **Opinionated, production-ready FastAPI base project with async SQLAlchemy, httpx, and Pydantic**

A modern, async-first FastAPI template designed for building scalable REST APIs with strong typing, database connection pooling, and clean architecture patterns. This template provides a solid foundation for microservices and monolithic applications alike.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- UV (fast Python package manager)

### Installation

```bash
# Install UV
brew install uv

# Install dependencies
uv sync

# For PostgreSQL support
uv sync --extra postgres

# For SQLite support
uv sync --extra sqlite
```

### Run the Application

```bash
# Development server with auto-reload
uv run uvicorn main:app --reload --port 8000

# Or use the main.py directly
uv run python main.py
```

Visit:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ✨ Key Features

### Opinionated Architecture
- **Async-First**: 100% async/await throughout - from database to HTTP clients
- **Type-Safe**: Heavy use of Pydantic for request/response validation and settings
- **Repository Pattern**: Clean separation between business logic and data access
- **Connection Pooling**: Built-in async connection pools for databases and HTTP clients

### Technology Stack
- **FastAPI** - Modern, high-performance web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** - Async ORM with connection pooling and optimized queries
- **Pydantic V2** - Runtime validation, serialization, and settings management
- **httpx** - Async HTTP client with connection pooling and HTTP/2 support
- **Uvicorn** - Lightning-fast ASGI server with auto-reload

### Production-Ready Features
- ✅ Environment-based configuration (local/dev/uat/prod)
- ✅ Kubernetes secrets integration
- ✅ Database connection pooling with health checks
- ✅ HTTP client connection pooling and retry logic
- ✅ Auto-discovery of API routes
- ✅ CORS middleware pre-configured
- ✅ Structured logging ready
- ✅ Clean shutdown with lifespan management

## 📁 Project Structure

```
fastapi-backend/
├── app/
│   ├── main.py                    # Application entry point with lifespan management
│   ├── main_config.py            # Environment-aware configuration with Pydantic
│   │
│   ├── core/                     # Infrastructure & framework code
│   │   ├── database.py           # Async SQLAlchemy connection pool
│   │   ├── base_repository.py    # Generic CRUD repository pattern
│   │   ├── rest_api.py           # httpx client pool for external APIs
│   │   ├── route_discovery.py    # Auto-register routes from modules
│   │   ├── config_loader.py      # Environment file loading logic
│   │   ├── secrets.py            # Kubernetes secrets integration
│   │   ├── dependencies.py       # FastAPI dependency injection
│   │   └── enums.py              # Shared enums and constants
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── base.py               # Base model with common fields (id, timestamps)
│   │   ├── event.py              # Example: Event model
│   │   └── image.py              # Example: Image model
│   │
│   ├── repository/               # Data access layer (repository pattern)
│   │   ├── event_repository.py   # Event-specific queries
│   │   └── image_repository.py   # Image-specific queries
│   │
│   ├── routes/                   # API endpoints (auto-discovered)
│   │   └── health.py             # Health check endpoint
│   │
│   └── utils/                    # Shared utilities
│       └── client_pool.py        # Alternative httpx pool implementation
│
├── scripts/                      # Utility scripts
│   └── migrate_data.py          # Data migration example
│
├── pyproject.toml               # Dependencies & project metadata (UV/pip)
└── README.md                    # This file
```

### Architecture Patterns

**Repository Pattern**: Abstracts database operations with a generic base repository
```python
class EventRepository(BaseRepository[Event, int]):
    async def find_by_location(self, location: str) -> list[Event]:
        # Custom query logic
```

**Dependency Injection**: FastAPI dependencies for session management
```python
async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncDBPool.get_session() as session:
        yield session
```

**Configuration Management**: Pydantic settings with environment-aware loading
```python
# Supports .env files: .env, .env.local, .env.production
config = DatabaseConfig()  # Auto-loads from environment
```

## 🔧 Configuration

### Environment-Based Configuration

This template uses **Pydantic Settings** for type-safe, environment-aware configuration:

```python
# Automatically loads from .env, .env.local, .env.production, etc.
from app.main_config import database_config, fastapi_config, cors_config

# Type-safe access with validation
db_url = database_config.url  # Validated at startup
pool_size = database_config.pool_size  # Default: 5
```

**Supported Environments**: `LOCAL`, `DEV`, `UAT`, `UATBIZ`, `SANITY`, `PROD`

Configuration files are loaded in order:
1. `.env` (base configuration)
2. `.env.{environment}` (environment-specific overrides)

### Database Configuration

**PostgreSQL** (Recommended for production):
```python
# .env.production
DATABASE_HOST=postgres.example.com
DATABASE_PORT=5432
DATABASE_USER=app_user
DATABASE_PASSWORD=secure_password
DATABASE_NAME=production_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**SQLite** (Development):
```python
# .env.local
DATABASE_URL=sqlite+aiosqlite:///./local.db
DATABASE_ECHO=true
```

**Connection Pooling** (automatic):
- Pool size: 5-20 connections (configurable)
- Pool pre-ping: Health checks before use
- Pool recycling: Auto-recycle stale connections
- Async engine with asyncpg/aiosqlite

### HTTP Client Configuration

Built-in **httpx** connection pool with retry logic:

```python
from app.core import HttpxRestClientPool, ClientConfig, TimeoutConfig

# Configure global client
config = ClientConfig(
    timeout=TimeoutConfig(connect=5.0, read=30.0),
    pool=PoolConfig(max_connections=100, max_keepalive=20),
    retry=RetryConfig(max_retries=3),
    http2=True
)
HttpxRestClientPool.configure(config)

# Use in your code
async with HttpxRestClientPool.get_client() as client:
    response = await client.get("https://api.example.com/data")
```

### CORS Configuration

```python
# .env
CORS_ALLOW_ORIGINS=["http://localhost:3000", "https://app.example.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE"]
CORS_ALLOW_HEADERS=["*"]
```

## 📊 Database Operations

### Using the Base Repository

The `BaseRepository` provides common CRUD operations:

```python
from app.repository.event_repository import EventRepository

async with AsyncDBPool.get_session() as session:
    repo = EventRepository(Event, session)

    # Create
    event = await repo.create(name="Conference", location="NYC")

    # Read
    event = await repo.get_by_id(1)
    events = await repo.get_all(limit=10, offset=0)

    # Update
    event = await repo.update(1, name="Updated Conference")

    # Delete
    await repo.delete(1)

    # Custom queries
    events = await repo.find_by_location("NYC")

    await session.commit()
```

### Transaction Management

```python
async with AsyncDBPool.get_session() as session:
    try:
        # Multiple operations in one transaction
        user = await user_repo.create(email="user@example.com")
        profile = await profile_repo.create(user_id=user.id)

        await session.commit()
    except Exception:
        await session.rollback()  # Auto-rollback on exception
        raise
```

## 📊 Database Migration

Migrate data from JSON files:

```bash
uv run python scripts/migrate_data.py
```

## 🧪 Development

### Code Formatting & Linting

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Type Checking

```bash
uv run mypy app/
```

### Run Tests

```bash
uv run pytest
```

## 📦 Dependencies

### Core Stack

- **FastAPI** (>=0.109.0) - Modern, fast web framework with automatic OpenAPI documentation
- **SQLAlchemy** (>=2.0.25) - Async ORM with powerful query building and connection pooling
- **Pydantic** (>=2.5.0) - Runtime type validation and serialization
- **Pydantic Settings** (>=2.1.0) - Environment-based configuration management
- **httpx** (>=0.26.0) - Async HTTP client with HTTP/2, connection pooling, and retries
- **Uvicorn** (>=0.27.0) - ASGI server with auto-reload and performance optimizations

### Database Drivers (Optional Extras)

Install based on your database:

```bash
# PostgreSQL (recommended for production)
uv sync --extra postgres
# Includes: asyncpg>=0.31.0

# SQLite (development/testing)
uv sync --extra sqlite
# Includes: aiosqlite>=0.19.0

# MySQL
uv sync --extra mysql
# Includes: aiomysql>=0.2.0
```

### Development Tools (Optional)

```bash
uv sync --extra dev
# Includes: ruff, mypy, pytest, pytest-asyncio, httpx-mock
```

## 🏗️ Architecture & Design Principles

## 🏗️ Architecture & Design Principles

### Opinionated Choices

This template makes deliberate architectural decisions to maximize productivity:

**1. Async-First Philosophy**
- All I/O operations use `async/await` - no blocking calls
- Async SQLAlchemy sessions with connection pooling
- Async httpx client for external API calls
- Enables high concurrency with low resource usage

**2. Repository Pattern**
- Abstract data access logic from business logic
- Generic base repository with common CRUD operations
- Specialized repositories for complex queries
- Easy to test and mock

**3. Pydantic Everywhere**
- Request/response validation (FastAPI)
- Configuration management (Pydantic Settings)
- Database model serialization
- Type safety across the application

**4. Dependency Injection**
- FastAPI's DI system for session management
- Singleton patterns for connection pools
- Easy to override in tests

**5. Environment-Aware Configuration**
- Separate configs for local/dev/staging/production
- Kubernetes secrets integration
- No hardcoded credentials

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer (Routes)          │  FastAPI endpoints
├─────────────────────────────────────┤
│      Service Layer (Optional)       │  Business logic
├─────────────────────────────────────┤
│    Repository Layer (Data Access)   │  Database queries
├─────────────────────────────────────┤
│      Models Layer (ORM Models)      │  SQLAlchemy models
├─────────────────────────────────────┤
│     Core Layer (Infrastructure)     │  DB pools, HTTP clients
└─────────────────────────────────────┘
```

**Benefits**:
- Clear separation of concerns
- Easy to test each layer independently
- Scalable from monolith to microservices
- Follows clean architecture principles

### Code Organization Conventions

1. **Models** (`app/models/`) - SQLAlchemy ORM models only
2. **Repositories** (`app/repository/`) - Database access patterns
3. **Routes** (`app/routes/`) - API endpoints (auto-discovered)
4. **Core** (`app/core/`) - Framework and infrastructure code
5. **Utils** (`app/utils/`) - Shared utilities without business logic

## 🚀 Usage Examples

### Creating a New Model

```python
# app/models/user.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
```

### Creating a Repository

```python
# app/repository/user_repository.py
from app.core import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User, int]):
    async def find_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_active_users(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())
```

### Creating an API Endpoint

```python
# app/routes/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_db_session
from app.repository.user_repository import UserRepository
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    repo = UserRepository(User, session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

Routes are **auto-discovered** - no manual registration needed!

### Making External API Calls

```python
from app.core import fetch_url

# Simple GET request
data = await fetch_url("https://api.example.com/data")

# With custom options
response = await fetch_url(
    "https://api.example.com/users",
    method="POST",
    json={"name": "John"},
    headers={"Authorization": "Bearer token"}
)
```

## 📊 Database Operations

## 🤝 Contributing

### Development Guidelines

1. **Maintain async consistency** - All I/O should use async/await
2. **Use type hints** - Leverage Pydantic and typing module
3. **Follow repository pattern** - Keep data access in repository layer
4. **Validate with Pydantic** - Use Pydantic models for all DTOs
5. **Add docstrings** - Document public methods and classes
6. **Keep it testable** - Use dependency injection

### Code Style

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Type checking
uv run mypy app/
```

## 🎯 Design Philosophy

This template is **opinionated** to promote consistency and best practices:

- ✅ **Async everywhere** - No sync database or HTTP calls
- ✅ **Type safety** - Pydantic models validate at runtime
- ✅ **Dependency injection** - Easy testing and modularity
- ✅ **Connection pooling** - Efficient resource management
- ✅ **Environment configuration** - Production-ready from day one
- ✅ **Clean architecture** - Separation of concerns

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
