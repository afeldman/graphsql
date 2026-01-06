# GraphSQL Test Suite

Comprehensive testing with Unit Tests and BDD Tests using Behave.

## Overview

The test suite consists of:
- **Unit Tests** — Test individual modules with pytest
- **BDD Tests** — Business-Driven Development scenarios with behave
- **Configuration** — Fixtures and test environment setup

## Unit Tests

Unit tests are located in `tests/` directory and test individual components.

### Running Unit Tests

```bash
# Run all unit tests
pytest

# Run with verbose output
pytest -vv

# Run specific test file
pytest tests/test_config.py

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test class
pytest tests/test_config.py::TestSettingsLoading

# Run specific test
pytest tests/test_config.py::TestSettingsLoading::test_load_defaults
```

### Test Files

#### `test_config.py`
Tests the configuration module and environment variable loading.

**Test Classes:**
- `TestSettingsLoading` — Settings initialization and environment parsing
  - `test_load_defaults` — Default configuration values
  - `test_load_with_custom_values` — Custom environment variables
  - `test_load_cors_origins` — CORS origin parsing
  - `test_database_type_detection_*` — Database type detection (SQLite, PostgreSQL, MySQL)
  - `test_auth_settings` — Authentication configuration
  - `test_pagination_settings` — Pagination configuration

```bash
pytest tests/test_config.py -v
```

#### `test_utils.py`
Tests utility functions for data serialization.

**Test Classes:**
- `TestCleanDict` — Data cleaning and type conversion
  - `test_remove_none_values` — Remove None values
  - `test_convert_datetime_to_iso` — DateTime conversion
  - `test_convert_decimal_to_float` — Decimal conversion
  - `test_decode_bytes` — Bytes decoding
  - `test_nested_dict_with_none_values` — Nested dictionaries
  - `test_mixed_types` — Mixed data types

```bash
pytest tests/test_utils.py -v
```

#### `test_rest_routes.py`
Tests REST API endpoints.

**Test Classes:**
- `TestHealthCheck` — Health check endpoint
  - `test_health_check_success` — Health check returns 200
  - `test_health_check_response_structure` — Response format validation

- `TestRootEndpoint` — Root endpoint
  - `test_root_returns_available_endpoints` — Root endpoint returns info

- `TestTableListing` — Table listing endpoint
  - `test_list_tables_empty` — Empty table list
  - `test_list_tables_endpoint_exists` — Endpoint exists

- `TestSwaggerDocumentation` — API documentation
  - `test_swagger_ui_accessible` — Swagger UI at /docs
  - `test_redoc_accessible` — ReDoc at /redoc
  - `test_openapi_schema_accessible` — OpenAPI schema at /openapi.json

```bash
pytest tests/test_rest_routes.py -v
```

### Test Fixtures

Available fixtures in `conftest.py`:

- `test_db` — In-memory SQLite database URL
- `db_session` — SQLAlchemy session connected to test database
- `client` — FastAPI TestClient with test database
- `sample_db` — Database with sample users and posts tables

Usage example:

```python
def test_something(client):
    """Test using FastAPI client."""
    response = client.get("/health")
    assert response.status_code == 200
```

## BDD Tests with Behave

BDD test scenarios are located in `features/` directory.

### Running BDD Tests

```bash
# Run all BDD scenarios
behave

# Run with verbose output
behave -v

# Run specific feature file
behave features/rest_api.feature

# Run specific scenario
behave features/rest_api.feature -n "List all tables"

# Run with tags
behave --tags=@important

# Pretty print results
behave --format=pretty

# Generate HTML report
behave --format=html -o reports/behave_report.html

# Generate JSON report
behave --format=json -o reports/behave_report.json
```

### Feature Files

#### `rest_api.feature`
REST API CRUD operations scenarios.

**Scenarios:**
- `List all tables` — GET /api/tables returns list of tables
- `Get table schema information` — GET /api/tables/{table}/info returns schema
- `List records with pagination` — Pagination works correctly
- `Create a new record via REST` — POST creates record with 201 status
- `Get single record by id` — GET /api/{table}/{id} returns record
- `Update record via REST` — PUT updates entire record
- `Partial update record via PATCH` — PATCH updates specific fields
- `Delete record via REST` — DELETE removes record

#### `graphql.feature`
GraphQL schema generation and queries.

**Scenarios:**
- `Dynamic schema generation for database tables` — Schema auto-generated
- `GraphQL query returns data` — Query returns user data
- `GraphQL mutation creates record` — Mutation creates and stores record

#### `configuration.feature`
Database and application configuration.

**Scenarios:**
- `SQLite database connection` — SQLite configuration
- `PostgreSQL database connection` — PostgreSQL configuration
- `MySQL database connection` — MySQL configuration
- `API configuration from environment` — API host/port configuration
- `Logging configuration from environment` — Log level configuration
- `CORS configuration` — CORS headers in responses

#### `health_check.feature`
API health and status checks.

**Scenarios:**
- `Health check endpoint returns healthy status` — /health returns 200 with healthy status
- `Health check includes table count` — Health check includes tables_count
- `API root endpoint provides information` — / endpoint returns info

### Step Implementations

Step implementations are in `features/steps/`:

#### `rest_api_steps.py`
Implements REST API steps (Given/When/Then).

Key steps:
- `Given a database with multiple tables`
- `When I send a GET/POST/PUT/PATCH/DELETE request to /api/...`
- `Then the response status should be ...`
- `And the response should contain ...`

#### `configuration_steps.py`
Implements configuration steps.

Key steps:
- `Given DATABASE_URL environment variable is set to ...`
- `When the application starts`
- `Then it should detect ... as the database type`

#### `health_check_steps.py`
Implements health check steps.

Key steps:
- `Given the GraphSQL API is running`
- `When I request the /health endpoint`
- `Then the response should contain status "healthy"`

#### `graphql_steps.py`
Implements GraphQL steps.

Key steps:
- `Given a database with ... tables`
- `When I execute a GraphQL query/mutation`
- `Then I should receive ...`

### Environment Setup

`features/environment.py` provides:

- `before_all(context)` — Global test setup
- `before_scenario(context, scenario)` — Setup for each scenario
- `after_scenario(context, scenario)` — Cleanup after scenario
- `after_all(context)` — Global cleanup

## Test Coverage

Generate coverage reports:

```bash
# Generate coverage
pytest --cov=src --cov-report=html

# Open HTML report
open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing
```

## Continuous Integration

Run tests in CI/CD pipeline:

```bash
# Run all tests
pytest && behave

# With coverage
pytest --cov=src --cov-report=xml && behave --format=json -o reports/behave.json

# With strict mode
pytest --strict-markers --strict-config && behave --strict
```

## Best Practices

### Unit Tests

1. **Arrange-Act-Assert pattern**
   ```python
   def test_something(client):
       # Arrange
       data = {"name": "test"}
       
       # Act
       response = client.post("/api/endpoint", json=data)
       
       # Assert
       assert response.status_code == 201
   ```

2. **Use fixtures for setup**
   ```python
   def test_with_fixture(client, sample_db):
       # client and sample_db are set up
       pass
   ```

3. **Test one thing per test**
   ```python
   # Good - focused test
   def test_health_check_returns_200(client):
       response = client.get("/health")
       assert response.status_code == 200
   ```

### BDD Tests

1. **Business-focused scenarios**
   ```gherkin
   Scenario: Create a user
     Given a database with users table
     When I send a POST request to /api/users with user data
     Then the response status should be 201
   ```

2. **Reusable steps**
   - Keep steps generic and reusable
   - Use table parameters for multiple values

3. **Clear given-when-then structure**
   - **Given** — Initial state
   - **When** — Action
   - **Then** — Expected result

## Common Issues

### Import errors in tests

**Problem:** `ModuleNotFoundError: No module named 'graphsql'`

**Solution:**
```bash
# Install package in development mode
pip install -e .
```

### Database locked error

**Problem:** SQLite database is locked during testing

**Solution:**
```python
# Use in-memory database
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
```

### Behave not finding features

**Problem:** `No steps in 'features' directory`

**Solution:**
```bash
# Ensure structure:
features/
  ├── steps/
  │   ├── __init__.py
  │   └── *_steps.py
  ├── *.feature
  └── environment.py
```

## Integration with Development Workflow

### Pre-commit hook

```bash
# Run tests before commit
echo "pytest && behave" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Watch mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw
```

### Parallel execution

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Advanced Testing Topics

### Mocking external services

```python
from unittest.mock import patch

def test_with_mock(client):
    with patch("graphsql.database.create_engine") as mock_engine:
        mock_engine.return_value = MagicMock()
        response = client.get("/health")
```

### Database fixtures

```python
@pytest.fixture
def populated_db(db_session):
    """Database with pre-loaded data."""
    db_session.execute("INSERT INTO users ...")
    db_session.commit()
    return db_session
```

### Performance testing

```python
import time

def test_performance(client):
    start = time.time()
    response = client.get("/api/users?limit=1000")
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Should complete in under 1 second
```

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Behave Documentation](https://behave.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
