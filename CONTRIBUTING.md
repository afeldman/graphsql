# Contributing to GraphSQL

We welcome contributions to GraphSQL! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [License](#license)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We're building a welcoming community.

---

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/afeldman/graphsql.git
cd graphsql
```

### 2. Set Up Development Environment

```bash
# Use UV for virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dev dependencies (including cloud dialects if needed)
uv pip install -e ".[dev]"

# Optional: Install cloud database dialects
uv pip install -e ".[dev,cloud]"
```

### 3. Install Pre-commit Hooks

```bash
# Auto-run linting/formatting before commits
pre-commit install
```

---

## Development Workflow

### Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use clear, descriptive branch names:
- `feature/add-graphql-mutations` — New feature
- `fix/handle-missing-pk` — Bug fix
- `docs/update-hana-guide` — Documentation
- `test/add-snowflake-tests` — Test additions

### Make Changes

- Keep changes **focused** on a single feature or fix
- Write code that follows the existing style
- Add or update tests as you go
- Update documentation if needed

### Run Checks Locally

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/

# Run all checks at once
make format && make lint && make type-check

# Or manually
black src/ && ruff check --fix src/ && mypy src/
```

---

## Code Quality

### Style Guide

- **Line length:** 100 characters (enforced by black & ruff)
- **Python version:** Target 3.8+ (tested on 3.8–3.12)
- **Imports:** `isort`-style, enforce with ruff
- **Docstrings:** Google-style, every function/class

### Example

```python
def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
    """Return column metadata for a table.

    Args:
        table_name: Table name to inspect.

    Returns:
        Dictionary with column definitions and primary keys, or ``None`` if
        the table does not exist.

    Examples:
        >>> db_manager.get_table_info("users")  # doctest: +SKIP
        {'name': 'users', 'columns': [...], 'primary_keys': ['id']}
    """
    ...
```

### Type Hints

- Use type hints for all function signatures
- Prefer `Optional[X]` over `X | None` for Python 3.8 compatibility
- Use `list[str]` for modern syntax (3.9+), or `List[str]` for 3.8

---

## Testing

### Unit Tests (pytest)

```bash
# Run all unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_config.py

# Run specific test
uv run pytest tests/test_config.py::TestSettingsLoading::test_load_defaults
```

### BDD Tests (behave)

```bash
# Run all BDD scenarios
uv run behave

# Run specific feature
uv run behave features/health_check.feature

# Generate HTML report
uv run behave --format=html -o reports/behave.html
```

### Test Coverage

Aim for **80%+ coverage**; use `--cov-report=html` to see gaps:

```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Writing Tests

- **Unit tests:** Focus on isolated logic in `tests/test_*.py`
- **BDD tests:** Business-focused scenarios in `features/*.feature`
- **Fixtures:** Centralize setup in `tests/conftest.py`
- **Mocking:** Use `unittest.mock` for external dependencies

Example unit test:

```python
def test_list_tables(client):
    """Verify REST endpoint returns table names."""
    response = client.get("/api/tables")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

Example BDD scenario:

```gherkin
Scenario: Health check endpoint returns healthy status
  Given the GraphSQL API is running
  When I request the /health endpoint
  Then the response status should be 200
  And the response should contain status "healthy"
```

---

## Documentation

### Update README

If adding features (especially cloud databases), update [README.md](README.md):
- Add section in appropriate category (e.g., [Additional Databases](#additional-databases-hana-redshift-snowflake))
- Include example `DATABASE_URL`
- Note any special requirements or caveats
- Link from [Table of Contents](#-table-of-contents)

### Code Comments

- Write clear, intent-driven comments
- Avoid redundant comments ("increment i by 1" is unnecessary)
- Explain *why*, not *what*

### Docstrings

- Every public module, class, function has a docstring
- Google-style format
- Include Examples section with doctests where helpful

---

## Commit Messages

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

### Format Rules

- **type:** `feat` (feature), `fix` (bug), `docs` (documentation), `test` (tests), `chore` (maintenance), `refactor` (code restructuring)
- **scope:** Optional; module or area affected (e.g., `config`, `graphql`, `rest`)
- **description:** Lowercase, imperative mood, no period; 50 char limit
- **body:** Wrap at 72 chars; explain *why*, not *what*
- **footer:** Reference issues: `Fixes #123`, `Closes #456`

### Examples

```
feat(cloud): add SAP HANA dialect support

Install sqlalchemy-hana and hdbcli to enable HANA connections.
Update DATABASE_URL format and document reflection caveats.

Fixes #42
```

```
fix(graphql): handle missing primary key in Redshift tables

Redshift doesn't enforce PKs; gracefully skip ID generation
for tables without explicit primary keys.

Closes #58
```

```
docs(readme): cloud database setup guide
```

---

## Pull Requests

### Before Opening

- Ensure **all tests pass**: `uv run pytest && uv run behave`
- Run **linting/formatting**: `black src/ && ruff check --fix src/ && mypy src/`
- Rebase on `main` or `master`
- Force-push if needed: `git push -f origin feature/...`

### PR Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Breaking change

## Testing
- [ ] Unit tests pass
- [ ] BDD tests pass
- [ ] Coverage maintained (80%+)

## Checklist
- [ ] Code follows style guide (black, ruff, mypy)
- [ ] Comments/docstrings updated
- [ ] README/docs updated if needed
- [ ] Tests added/updated
```

### Review Process

- Respond promptly to feedback
- Keep commits logical; rebase if history is messy
- Merge only after approval and CI passes

---

## Development Tips

### Watch Mode

```bash
# Requires pytest-watch
pip install pytest-watch
ptw
```

### Parallel Tests

```bash
# Requires pytest-xdist
pip install pytest-xdist
uv run pytest -n auto
```

### Debug Failing Tests

```bash
# Print statements
uv run pytest -s tests/test_file.py

# Drop into debugger on failure
uv run pytest --pdb tests/test_file.py

# Stop at first failure
uv run pytest -x tests/test_file.py
```

### Makefile Shortcuts

```bash
make format        # Black formatting
make lint          # Ruff linting
make type-check    # MyPy type checking
make test          # Run pytest
make test-bdd      # Run behave
make test-coverage # Coverage report
make clean         # Remove build artifacts
```

---

## Areas for Contribution

We welcome help in these areas:

### Code
- **Dialect support:** Oracle, CockroachDB, MariaDB, etc.
- **GraphQL features:** Subscriptions, directives, custom resolvers
- **REST enhancements:** Filtering, sorting, field selection
- **Performance:** Caching, query optimization, connection pooling

### Docs
- **Guides:** Integration tutorials, deployment patterns
- **Examples:** Docker, Kubernetes, cloud providers (AWS, GCP, Azure)
- **Troubleshooting:** FAQ, common errors

### Testing
- **E2E tests:** Real database connections (PostgreSQL, MySQL, HANA, Redshift, Snowflake)
- **Load tests:** Stress testing with large result sets
- **Security:** Injection attack prevention, auth flows

### DevOps
- **CI/CD:** GitHub Actions, testing matrix
- **Deployment:** Helm improvements, Terraform modules

---

## Questions?

- Check [README.md](README.md) and docs/ for existing answers
- Open a GitHub issue to discuss ideas before large contributions
- Use GitHub Discussions for questions

---

## License

By contributing to GraphSQL, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).

---

**Thank you for contributing! 🚀**
