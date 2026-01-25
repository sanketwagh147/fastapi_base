# Exception Handling Tests

Comprehensive test suite for the exception handling system.

## Test Coverage

### Exception Classes

- NotFoundError (404)
- BadRequestError (400)
- UnauthorizedError (401)
- ForbiddenError (403)
- ConflictError (409)
- InternalServerError (500)

### Test Scenarios

1. **Individual Parameters Pattern**: Tests exceptions created with separate parameters
2. **ErrorResponse Object Pattern**: Tests exceptions created with ErrorResponse objects
3. **Default Messages**: Tests exceptions with default error messages
4. **Generic Exception Handler**: Tests handling of unexpected Python exceptions
5. **Validation Errors**: Tests Pydantic validation error handling
6. **Error Response Serialization**: Tests JSON response format and field exclusion

## Running Tests

### Install Dependencies

```bash
# Install test dependencies
uv pip install pytest pytest-asyncio

# Or using pip
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
# Run all exception tests with verbose output
pytest tests/test_exceptions.py -v

# Run with coverage
pytest tests/test_exceptions.py --cov=app.core.exceptions --cov-report=term-missing

# Run specific test
pytest tests/test_exceptions.py::test_not_found_error_with_params -v
```

### Run Tests by Category

```bash
# Test only exception classes
pytest tests/test_exceptions.py -k "test_not_found or test_bad_request" -v

# Test only error response model
pytest tests/test_exceptions.py -k "test_error_response_model" -v

# Test only handlers
pytest tests/test_exceptions.py -k "handler" -v
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_exceptions.py       # Exception handling tests
└── README.md               # This file
```

## Key Test Cases

### 1. Testing Custom Exceptions with Parameters

```python
def test_not_found_error_with_params():
    raise NotFoundError(
        message="Resource not found",
        error_code="RESOURCE_NOT_FOUND",
        detail={"id": 123}
    )
```

### 2. Testing with ErrorResponse Object

```python
def test_not_found_error_with_error_response():
    error = ErrorResponse(
        error_code="USER_NOT_FOUND",
        message="User does not exist",
        detail={"user_id": 456}
    )
    raise NotFoundError(error)
```

### 3. Testing Generic Exception Handler

```python
def test_generic_exception_handler():
    raise ValueError("Unexpected error")
    # Should return 500 with standardized response
```

## Expected Response Format

All exceptions return responses in this format:

```json
{
	"success": false,
	"error_code": "ERROR_CODE",
	"message": "Error message",
	"detail": { "key": "value" }, // Optional
	"path": "/api/endpoint"
}
```

## Adding New Tests

To add tests for new exception types:

1. Import the new exception class
2. Create test function following naming convention: `test_<exception_name>_<scenario>`
3. Use the `app` and `client` fixtures
4. Assert status code and response structure
5. Verify error_code, message, and detail fields

Example:

```python
def test_new_exception(app: FastAPI, client: TestClient):
    @app.get("/test-new")
    async def route():
        raise NewException(message="Test message")

    response = client.get("/test-new")

    assert response.status_code == status.HTTP_XXX
    assert response.json()["error_code"] == "NewException"
```
