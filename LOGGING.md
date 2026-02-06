# Structured Logging Guide

This project uses **structured logging** with automatic request correlation IDs for production-ready observability.

## Quick Start

```python
import logging

logger = logging.getLogger(__name__)
logger.info("User created", user_id=123, email="test@example.com")
```

## Features

✅ **JSON logs in production** - Queryable in Loki/CloudWatch/Datadog
✅ **Pretty console logs locally** - Color-coded, human-readable
✅ **Automatic request IDs** - Trace requests across services
✅ **Uvicorn logs integrated** - Access logs include request_id
✅ **Library noise reduction** - Pre-configured SQLAlchemy/httpx levels
✅ **Future-proof** - Ready for Sentry/OpenTelemetry integration

## Configuration

Set in `.env` files:

```bash
# .env_local (development)
LOG_LEVEL=DEBUG
LOG_FORMAT=console
LOG_LEVEL_SQLALCHEMY=INFO
LOG_LEVEL_HTTPX=INFO
LOG_LEVEL_UVICORN_ACCESS=INFO

# .env_prod (production)
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_LEVEL_SQLALCHEMY=WARNING
LOG_LEVEL_HTTPX=WARNING
LOG_LEVEL_UVICORN_ACCESS=INFO
```

### Configuration Options

| Variable | Values | Description |
|----------|--------|-------------|
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR | Root log level |
| `LOG_FORMAT` | `json`, `console` | Output format (json=prod, console=dev) |
| `LOG_LEVEL_SQLALCHEMY` | DEBUG, INFO, WARNING, ERROR | SQLAlchemy engine logs |
| `LOG_LEVEL_HTTPX` | DEBUG, INFO, WARNING, ERROR | HTTP client logs |
| `LOG_LEVEL_UVICORN_ACCESS` | DEBUG, INFO, WARNING, ERROR | Uvicorn access logs |

## Usage Examples

### Basic Logging

```python
import logging

logger = logging.getLogger(__name__)

# Simple message
logger.info("Application started")

# With context (structured)
logger.info("User login", user_id=123, ip="192.168.1.1")

# Error with exception
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", error=str(e), user_id=456)
```

### In Route Handlers

```python
from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users")
async def create_user(user_data: UserCreate):
    logger.info("Creating user", email=user_data.email)

    # All logs in this request automatically get the same request_id
    user = await user_repo.create(user_data)

    logger.info("User created", user_id=user.id)
    return user
```

### Specialized Loggers

Create domain-specific loggers:

```python
# Audit logger for compliance
audit_logger = logging.getLogger("myapp.audit")
audit_logger.info("payment_processed", user_id=99, amount=100.50, currency="USD")

# Performance logger
metrics_logger = logging.getLogger("myapp.metrics")
metrics_logger.info("api_latency", endpoint="/users", duration_ms=45)

# Security events
security_logger = logging.getLogger("myapp.security")
security_logger.warning("failed_login_attempt", ip="1.2.3.4", username="admin")
```

## Output Formats

### Console (Local Development)

When `LOG_FORMAT=console`:

```
2024-02-05 10:30:45 [info     ] User created               user_id=123 email=test@example.com request_id=abc123
2024-02-05 10:30:46 [warning  ] Slow query detected        duration_ms=1500 query=SELECT * request_id=abc123
```

### JSON (Production)

When `LOG_FORMAT=json`:

```json
{
  "event": "User created",
  "level": "info",
  "timestamp": "2024-02-05T10:30:45.123Z",
  "logger": "app.routes.users",
  "user_id": 123,
  "email": "test@example.com",
  "request_id": "abc123def456"
}
```

## Request Correlation

Every HTTP request gets a unique `request_id` that appears in all logs during that request:

- **Auto-generated**: UUID-based (16 chars)
- **Header**: `X-Request-ID` (can be set by client for distributed tracing)
- **Scope**: All logs in request context get the same ID
- **Uvicorn logs**: Access logs also include `request_id`

Example flow:

```
[Request starts] → request_id=abc123
  ↓
[Route handler] logger.info("Fetching user") → includes request_id=abc123
  ↓
[Database query] logger.debug("Executing query") → includes request_id=abc123
  ↓
[Response sent] uvicorn.access log → includes request_id=abc123
```

## Library Log Levels

Pre-configured to reduce noise:

- **SQLAlchemy**: `WARNING` (prod), `INFO` (local)
- **httpx**: `WARNING` (prod), `INFO` (local)
- **uvicorn.access**: `INFO` (always enabled)
- **uvicorn.error**: Follows root `LOG_LEVEL`

## Best Practices

### ✅ Do

```python
# Use structured context
logger.info("Order placed", order_id=123, user_id=456, total=99.99)

# Use appropriate log levels
logger.debug("Cache hit", key="user:123")  # Verbose, dev only
logger.info("User action", action="login")  # Important events
logger.warning("Retry attempt", retry=3)    # Potential issues
logger.error("Failed", error=str(e))        # Actual errors

# Use module-level loggers
logger = logging.getLogger(__name__)
```

### ❌ Don't

```python
# Don't use string formatting (wastes CPU)
logger.info(f"User {user_id} created")  # Bad
logger.info("User created", user_id=user_id)  # Good

# Don't log sensitive data in production
logger.info("Login", password=pwd)  # Bad
logger.info("Login", user_id=user.id)  # Good

# Don't use print() statements
print("Debug info")  # Bad - not captured in logs
logger.debug("Debug info")  # Good
```

## Adding Custom Loggers

Create module-specific loggers for different concerns:

```python
# app/core/audit.py
import logging

audit_logger = logging.getLogger("myapp.audit")

def log_sensitive_action(user_id: int, action: str, resource: str):
    audit_logger.info(
        "audit_event",
        user_id=user_id,
        action=action,
        resource=resource,
        event_type="AUDIT"
    )
```

All loggers automatically inherit:
- Request ID context
- Timestamp formatting
- JSON/console rendering
- Log level filtering

## Querying Logs (Production)

With JSON logs, you can query in log aggregators:

**Loki/Grafana**:
```logql
{service="eventually-api"} | json | request_id="abc123"
```

**CloudWatch Insights**:
```sql
fields @timestamp, event, user_id, request_id
| filter request_id = "abc123"
| sort @timestamp desc
```

**Datadog**:
```
service:eventually-api request_id:abc123
```

## Future: Sentry Integration

Ready to add error tracking:

```python
# app/core/logging_config.py - add to setup_logging()
import sentry_sdk

if logging_config.sentry_dsn:
    sentry_sdk.init(
        dsn=logging_config.sentry_dsn,
        environment=settings.env.value,
        traces_sample_rate=0.1,
    )
```

## Future: OpenTelemetry

Ready for distributed tracing:

```python
# Add trace_id/span_id to logs
from opentelemetry import trace

def add_trace_context(_logger, _method_name, event_dict):
    span = trace.get_current_span()
    if span:
        event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")
        event_dict["span_id"] = format(span.get_span_context().span_id, "016x")
    return event_dict

# Add to shared_processors in setup_logging()
```

## Troubleshooting

**Logs not appearing?**
- Check `LOG_LEVEL` in your `.env` file
- Ensure `setup_logging()` is called before app creation

**No request_id in logs?**
- Check that `CorrelationIdMiddleware` is added to app
- Logs outside HTTP request context won't have request_id

**Want file logs instead of stdout?**
- Add a `FileHandler` to `logging_config.py`
- Or use container log collection (recommended for K8s)

**SQLAlchemy logs too noisy?**
- Set `LOG_LEVEL_SQLALCHEMY=WARNING` in `.env`
