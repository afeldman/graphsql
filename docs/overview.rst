Overview
========

GraphSQL reflects existing relational schemas and exposes both REST and GraphQL APIs
without manual model definitions.

Key features
------------

- Automatic REST endpoints with pagination
- Automatic GraphQL schema and mutations
- PostgreSQL, MySQL, and SQLite support
- Environment-based configuration via ``.env``
- Built with FastAPI, SQLAlchemy, and Strawberry GraphQL

Getting started
---------------

1. Install dependencies and the package in editable mode::

      uv pip install -e "[dev]"

2. Provide a ``DATABASE_URL`` in ``.env`` or via environment variable.

3. Run the application::

      graphsql-start

4. Explore the REST API at ``/docs`` and GraphQL at ``/graphql``.
