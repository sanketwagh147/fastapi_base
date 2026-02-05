# Architecture Documentation

## Overview

This is an **opinionated FastAPI base template** designed for building production-ready REST APIs with a focus on:

- **Async-first**: 100% async/await operations for optimal concurrency
- **Type safety**: Heavy use of Pydantic for runtime validation
- **Clean architecture**: Clear separation of concerns
- **Connection pooling**: Efficient resource management for databases and HTTP clients
- **Production-ready**: Environment-aware configuration and Kubernetes integration

## Technology Stack

### Core Framework
- **FastAPI** - Modern async web framework with automatic OpenAPI documentation
- **Uvicorn** - ASGI server with auto-reload and performance optimizations
- **Python 3.11+** - Latest Python features including improved async performance

### Database Layer
- **SQLAlchemy 2.0** - Async ORM with powerful query building
- **asyncpg** - Fast PostgreSQL async driver (recommended for production)
- **aiosqlite** - SQLite async driver (development/testing)

### Data Validation
- **Pydantic V2** - Runtime validation, serialization, and parsing
- **Pydantic Settings** - Environment-based configuration management

### HTTP Client
- **httpx** - Async HTTP client with connection pooling, HTTP/2, and retry logic

## Architectural Patterns

### 1. Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer (Routes)          │
│  - HTTP endpoints                   │
│  - Request/response validation      │
│  - Error handling                   │
├─────────────────────────────────────┤
│    Service Layer (Optional)         │
│  - Business logic                   │
│  - Orchestration                    │
│  - Transaction management           │
├─────────────────────────────────────┤
│  Repository Layer (Data Access)     │
│  - CRUD operations                  │
│  - Query building                   │
│  - Database abstractions            │
├─────────────────────────────────────┤
│    Models Layer (ORM Models)        │
│  - SQLAlchemy models                │
│  - Database schema                  │
│  - Relationships                    │
├─────────────────────────────────────┤
│   Core Layer (Infrastructure)       │
│  - Database connection pool         │
│  - HTTP client pool                 │
│  - Configuration management         │
│  - Dependency injection             │
└─────────────────────────────────────┘
```

**Benefits:**
- Clear separation of concerns
- Easy to test each layer independently
- Scalable from monolith to microservices
- Replaceable components

### 2. Repository Pattern

The Repository Pattern abstracts data access logic from business logic.

**Why Repository Pattern?**
- **Testability**: Easy to mock database operations
- **Maintainability**: Centralized data access logic
- **Flexibility**: Easy to swap database implementations
- **Reusability**: Common CRUD operations in base repository

**Structure:**

```python
# Base repository with generic CRUD
class BaseRepository[ModelType, IDType]:
    async def create(self, **kwargs) -> ModelType
    async def get_by_id(self, id: IDType) -> ModelType | None
    async def update(self, id: IDType, **kwargs) -> ModelType | None
    async def delete(self, id: IDType) -> bool
    async def get_all(self, limit, offset) -> list[ModelType]

# Specialized repository for domain-specific queries
class UserRepository(BaseRepository[User, int]):
    async def find_by_email(self, email: str) -> User | None
    async def find_active_users(self) -> list[User]
```

### 3. Dependency Injection

FastAPI's built-in dependency injection system provides:

- **Automatic resource management**: Sessions, connections cleaned up automatically
- **Type safety**: IDE autocomplete and type checking
- **Testability**: Easy to override dependencies in tests
- **Reusability**: Share dependencies across endpoints

**Example:**

```python
# Define dependency
async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncDBPool.get_session() as session:
        yield session

# Use in endpoint
@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    # db is automatically injected and cleaned up
    return await UserRepository(User, db).get_all()
```

### 4. Configuration Management

**Pydantic Settings** provides type-safe, environment-aware configuration:

**Features:**
- Environment variable loading
- `.env` file support with environment-specific files
- Type validation at startup (fail-fast)
- Kubernetes secrets integration
- SecretStr for sensitive data

**Configuration Hierarchy:**

```
1. Environment variables (highest priority)
2. Kubernetes secrets (/mnt/secrets/*)
3. .env.{environment} (.env.prod, .env.local)
4. .env (base configuration)
5. Default values in code (lowest priority)
```

**Example:**

```python
class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local"],
        env_prefix="DATABASE_"
    )

    host: str = "localhost"
    port: int = 5432
    user: str
    password: SecretStr
    pool_size: int = 5

# Usage
config = DatabaseConfig()  # Auto-loads and validates
db_url = config.get_database_url()
```

## Design Decisions

### Why Async-First?

**Traditional Sync I/O:**
- Threads block while waiting for database/network
- High memory usage (each thread needs stack space)
- Context switching overhead
- Limited scalability (typically 100s of concurrent requests)

**Async I/O:**
- Non-blocking operations
- Single thread handles thousands of connections
- Lower memory footprint
- Better resource utilization
- Perfect for I/O-bound applications (most web services)

**Performance Comparison:**
```
Sync (threading):    ~100-500 concurrent connections
Async (single core): ~10,000+ concurrent connections
```

### Why SQLAlchemy 2.0?

SQLAlchemy 2.0 represents a major evolution with first-class async support:

**Key Features:**
- Native async/await support
- Connection pooling with health checks
- Powerful query building with type hints
- Lazy loading in async context
- ORM and Core APIs
- Database migration support (Alembic)

**Performance Optimizations:**
- Connection pooling reduces handshake overhead
- Pre-ping validates connections before use
- Lazy loading minimizes database queries
- Compiled query caching

### Why httpx?

**Advantages over aiohttp:**
- More requests-like API (easier for developers)
- Built-in HTTP/2 support
- Better connection pooling defaults
- Excellent type hints
- Synchronous API available for testing

**Features:**
- Connection pooling and reuse
- Automatic retries on transient failures
- Configurable timeouts (connect, read, write, pool)
- SSL verification
- Redirect following
- HTTP/2 multiplexing

### Why Pydantic V2?

Pydantic V2 brings significant improvements:

**Performance:**
- ~5-50x faster validation (Rust core)
- Lower memory usage
- Faster JSON serialization

**Features:**
- Runtime type validation
- Automatic data coercion
- Custom validators
- JSON Schema generation
- Settings management
- Serialization modes (exclude, include, by_alias)

**Use Cases:**
- API request/response validation
- Configuration management
- Database model serialization
- DTO (Data Transfer Objects)

## Connection Pooling Strategy

### Database Connection Pool

**Configuration:**
- **Pool size**: 5-20 connections (configurable per environment)
- **Max overflow**: 10 additional connections under load
- **Pool timeout**: 30 seconds waiting for available connection
- **Pool recycle**: 3600 seconds (1 hour) - recycle stale connections
- **Pre-ping**: Health check before using connection

**Why Connection Pooling?**
- Reduces TCP handshake overhead
- Reuses authenticated connections
- Limits total connections to database
- Handles connection failures gracefully

**Sizing Guide:**
```
pool_size = (number_of_workers * concurrent_requests_per_worker) / average_request_duration

Example:
4 workers * 50 concurrent requests * 0.1s duration = 20 connections
```

### HTTP Connection Pool

**Configuration:**
- **Max connections**: 100 total connections
- **Max keepalive**: 20 idle connections
- **Keepalive expiry**: 30 seconds
- **Max retries**: 3 attempts on failure
- **HTTP/2**: Enabled for multiplexing

**Benefits:**
- Connection reuse across requests
- Automatic retry on transient failures
- HTTP/2 multiplexing (multiple requests on one connection)
- SSL session reuse

## Environment Strategy

### Supported Environments

1. **LOCAL** - Local development
   - Debug enabled
   - Verbose logging
   - SQLite or local PostgreSQL
   - CORS fully open
   - Auto-reload enabled

2. **DEV** - Shared development server
   - Debug enabled
   - Shared database
   - Relaxed security
   - API docs enabled

3. **UAT** - User Acceptance Testing
   - Production-like configuration
   - Test database
   - API docs enabled
   - Monitoring enabled

4. **PROD** - Production
   - Debug disabled
   - Strict security
   - API docs disabled
   - Full monitoring
   - Kubernetes secrets

### Configuration Files

```
env_files/
├── .env              # Base configuration (defaults)
├── .env.local        # Local overrides (gitignored)
├── .env.dev          # Development environment
├── .env.uat          # UAT environment
└── .env.prod         # Production configuration
```

### Kubernetes Integration

Production deployments use Kubernetes secrets:

```yaml
# Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded>
  SECRET_KEY: <base64-encoded>
```

Mounted at `/mnt/secrets/` and loaded automatically.

## Auto-Discovery System

Routes are automatically discovered from the `app/routes/` directory.

**How it works:**

1. Scans all Python files in `app/routes/`
2. Imports modules and looks for `router` variable
3. Registers routers with FastAPI application
4. Uses `APIRouter(...)` config first; `ROUTER_CONFIG` can provide extra `include_router(...)` kwargs
5. If `prefix`/`tags` aren't set on the router, defaults are generated from the file path

**Benefits:**

- No manual route registration
- Convention over configuration
- Reduced boilerplate
- Easy to add new endpoints

**Example:**

```python
# app/routes/users.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)

@router.get("/")
async def list_users():
    return {"users": []}
```

Routes automatically registered at startup!

## Performance Considerations

### Async Performance

- **Concurrency**: Single Python process handles 10,000+ concurrent connections
- **Memory**: Low memory footprint (no thread stack overhead)
- **CPU**: Efficient for I/O-bound workloads

### Database Performance

- **Connection Pooling**: Reduces connection overhead by 90%+
- **Compiled Queries**: SQLAlchemy caches compiled queries
- **Lazy Loading**: Only loads related data when accessed
- **Indexing**: Ensure proper indexes on frequently queried columns

### HTTP Client Performance

- **Connection Reuse**: 5-10x faster than creating new connections
- **HTTP/2 Multiplexing**: Multiple requests on single connection
- **Keep-Alive**: Reduces TCP handshake and SSL negotiation

### Recommended Optimizations

1. **Use SELECT specific columns** instead of SELECT *
2. **Implement pagination** for large result sets
3. **Add database indexes** on foreign keys and query filters
4. **Use response_model_exclude_none** to reduce payload size
5. **Enable Gzip compression** in Uvicorn for large responses
6. **Cache frequently accessed data** with Redis

## Testing Strategy

### Unit Testing

Test each layer independently:

```python
# Test repository with in-memory database
async def test_user_repository():
    # Setup in-memory SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Test repository
    async with AsyncSession(engine) as session:
        repo = UserRepository(User, session)
        user = await repo.create(email="test@example.com")
        assert user.id is not None
```

### Integration Testing

Test with FastAPI TestClient:

```python
from httpx import AsyncClient

async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/users", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert response.status_code == 201
```

### Dependency Overrides

Override dependencies in tests:

```python
async def override_get_db():
    async with test_session_maker() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
```

## Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **SecretStr**: Use for passwords and API keys
3. **SQL Injection**: Use parameterized queries (SQLAlchemy ORM)
4. **CORS**: Configure allowed origins explicitly
5. **HTTPS**: Enforce SSL in production
6. **Rate Limiting**: Add rate limiting middleware (not included)
7. **Input Validation**: Pydantic validates all input
8. **Dependencies**: Keep dependencies updated

## Scalability

### Vertical Scaling
- Increase Uvicorn workers (`--workers 4`)
- Increase database pool size
- Add more CPU/RAM to server

### Horizontal Scaling
- Run multiple FastAPI instances behind load balancer
- Use shared PostgreSQL database
- Use Redis for shared session/cache
- Stateless design enables easy scaling

### Database Scaling
- Read replicas for read-heavy workloads
- Connection pooling at application level
- Database connection pooler (PgBouncer)
- Sharding for very large datasets

## Monitoring & Observability

### Recommended Additions

1. **Logging**: Structured logging with contextvars
2. **Metrics**: Prometheus metrics for requests, latency, errors
3. **Tracing**: OpenTelemetry for distributed tracing
4. **Health Checks**: Database connectivity, external API health
5. **Alerts**: Error rate, response time, database connections

### Example Health Check

```python
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    # Check database
    await db.execute(text("SELECT 1"))

    # Check external API
    async with HttpxRestClientPool.get_client() as client:
        await client.get("https://api.example.com/health")

    return {"status": "healthy"}
```

## Migration Path

### From This Template to Production

1. **Remove Example Code**: Delete event/image models and repositories
2. **Add Authentication**: Implement JWT or OAuth2
3. **Add Authorization**: Role-based access control
4. **Add Logging**: Structured logging with correlation IDs
5. **Add Monitoring**: Prometheus metrics and health checks
6. **Configure Secrets**: Use Kubernetes secrets or AWS Secrets Manager
7. **Add Rate Limiting**: Protect against abuse
8. **Add Caching**: Redis for frequently accessed data
9. **Add Background Tasks**: Celery or FastAPI background tasks
10. **Add CI/CD**: GitHub Actions, GitLab CI, or Jenkins

## Summary

This template provides a **production-ready foundation** for FastAPI applications with:

✅ **Async-first architecture** for high concurrency
✅ **Type-safe configuration** with Pydantic Settings
✅ **Repository pattern** for clean data access
✅ **Connection pooling** for databases and HTTP
✅ **Environment-aware** configuration management
✅ **Auto-discovery** of routes
✅ **Clean architecture** with clear separation of concerns

The opinionated choices eliminate common pitfalls and provide best practices out of the box, allowing you to focus on business logic rather than infrastructure.
