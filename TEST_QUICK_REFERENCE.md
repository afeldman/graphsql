# Test Quick Reference

## Quick Start

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
make test

# Or manually:
pytest && behave
```

## Unit Tests with pytest

```bash
# Run all unit tests
make test-unit

# Run specific test file
pytest tests/test_config.py

# Run with coverage
make test-coverage

# Run in watch mode
make test-watch

# Run specific test
pytest tests/test_config.py::TestSettingsLoading::test_load_defaults

# Run with markers
pytest -m unit
```

## BDD Tests with behave

```bash
# Run all BDD scenarios
make test-bdd

# Run specific feature file
behave features/rest_api.feature

# Run specific scenario
behave features/rest_api.feature -n "List all tables"

# Pretty output
behave --format=pretty

# Generate HTML report
behave --format=html -o reports/behave.html
```

## Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# All checks
make format && make lint && make type-check
```

## Test Structure

```
tests/                              # Unit tests
├── __init__.py
├── conftest.py                     # Fixtures
├── test_config.py                  # Configuration tests
├── test_rest_routes.py             # REST API tests
└── test_utils.py                   # Utility tests

features/                           # BDD tests
├── environment.py                  # Setup/teardown
├── rest_api.feature                # REST API scenarios
├── graphql.feature                 # GraphQL scenarios
├── configuration.feature           # Configuration scenarios
├── health_check.feature            # Health check scenarios
└── steps/                          # Step implementations
    ├── rest_api_steps.py
    ├── graphql_steps.py
    ├── configuration_steps.py
    └── health_check_steps.py
```

## Key Test Files

### Unit Tests
- **test_config.py** — 8 tests for Settings loading and database type detection
- **test_utils.py** — 8 tests for data serialization
- **test_rest_routes.py** — 7 tests for API endpoints

### BDD Tests
- **rest_api.feature** — 8 scenarios for CRUD operations
- **graphql.feature** — 3 scenarios for GraphQL schema and queries
- **configuration.feature** — 6 scenarios for configuration
- **health_check.feature** — 3 scenarios for health checks

## Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing
```

## Common Commands

```bash
# Test everything
make test

# Test and generate coverage
make test-coverage

# Watch tests
make test-watch

# Full development workflow
make install-dev && make test && make lint && make type-check

# CI/CD pipeline
pytest --cov=src && behave
```

## Debugging Tests

```bash
# Print debug statements
pytest -s tests/test_config.py

# Drop into debugger on failure
pytest --pdb tests/test_config.py

# Stop at first failure
pytest -x tests/test_config.py

# Verbose output
pytest -vv tests/test_config.py
```

## Environment Setup

Test database automatically set to SQLite in-memory (`sqlite:///:memory:`) for isolation.

Override via environment:
```bash
DATABASE_URL=postgresql://localhost/test pytest
```

## Test Examples

### Unit Test
```python
def test_load_defaults(monkeypatch):
    """Test loading settings with defaults."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    
    settings = Settings.load()
    
    assert settings.api_port == 8000
```

### BDD Scenario
```gherkin
Scenario: Create a new record
  Given a database with "users" table
  When I send a POST request to /api/users with user data
  Then the response status should be 201
```

## Fixtures Available

- `test_db` — In-memory SQLite URL
- `db_session` — SQLAlchemy session
- `client` — FastAPI TestClient
- `sample_db` — Pre-populated database

Usage:
```python
def test_api(client):
    response = client.get("/health")
    assert response.status_code == 200
```
