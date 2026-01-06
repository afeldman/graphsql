# GraphSQL

Automatic REST and GraphQL API for any relational database using FastAPI, SQLAlchemy, and Strawberry GraphQL.

## Features

- ✅ Automatic REST API for all database tables
- ✅ Automatic GraphQL API
- ✅ Supports PostgreSQL, MySQL, and SQLite
- ✅ CRUD operations
- ✅ Pagination
- ✅ Automatic API documentation (Swagger/ReDoc)
- ✅ GraphQL Playground
- ✅ Configuration via .env
- ✅ Modern stack with UV and Hatchling

## Installation

### With UV (recommended)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Project setup
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -e .

# For development
uv pip install -e ".[dev]"
```

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
