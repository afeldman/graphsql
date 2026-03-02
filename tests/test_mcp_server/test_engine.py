"""Tests for MCP server engine module."""

import pytest
from sqlalchemy import text

from graphsql.mcp_server.config import MCPServerConfig, reset_config
from graphsql.mcp_server.db import close_engine, get_engine
from graphsql.mcp_server.engine import (
    GraphSQLEngine,
    QueryResult,
    QueryTimeoutError,
    SchemaInfo,
    get_graphsql_engine,
    reset_graphsql_engine,
)


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_default_values(self) -> None:
        """Test default QueryResult values."""
        result = QueryResult(success=True)
        assert result.success is True
        assert result.data == []
        assert result.columns == []
        assert result.row_count == 0
        assert result.execution_time_ms == 0.0
        assert result.error is None
        assert result.warnings == []
        assert result.query_type == "UNKNOWN"

    def test_success_result(self) -> None:
        """Test successful QueryResult."""
        result = QueryResult(
            success=True,
            data=[{"id": 1, "name": "test"}],
            columns=["id", "name"],
            row_count=1,
            execution_time_ms=10.5,
            query_type="SELECT",
        )
        assert result.success is True
        assert len(result.data) == 1
        assert result.row_count == 1

    def test_error_result(self) -> None:
        """Test error QueryResult."""
        result = QueryResult(
            success=False,
            error="Query failed",
            query_type="SELECT",
        )
        assert result.success is False
        assert result.error == "Query failed"

    def test_to_dict(self) -> None:
        """Test QueryResult.to_dict()."""
        result = QueryResult(
            success=True,
            data=[{"id": 1}],
            columns=["id"],
            row_count=1,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["data"] == [{"id": 1}]
        assert d["columns"] == ["id"]


class TestSchemaInfo:
    """Tests for SchemaInfo dataclass."""

    def test_default_values(self) -> None:
        """Test default SchemaInfo values."""
        info = SchemaInfo()
        assert info.tables == []
        assert info.total_tables == 0
        assert info.database_type == "unknown"

    def test_to_dict(self) -> None:
        """Test SchemaInfo.to_dict()."""
        info = SchemaInfo(
            tables=[{"name": "users"}],
            total_tables=1,
            database_type="sqlite",
        )
        d = info.to_dict()
        assert d["total_tables"] == 1
        assert d["database_type"] == "sqlite"


class TestGraphSQLEngine:
    """Tests for GraphSQLEngine class."""

    def setup_method(self) -> None:
        """Set up test database."""
        close_engine()
        reset_config()
        reset_graphsql_engine()

        self.config = MCPServerConfig(database_url="sqlite:///:memory:")
        self.db_engine = get_engine(self.config)

        # Create test tables using begin() for auto-commit
        with self.db_engine.begin() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            """
                )
            )
            conn.execute(
                text(
                    """
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    title TEXT NOT NULL,
                    content TEXT
                )
            """
                )
            )
            conn.execute(
                text("INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@test.com')")
            )
            conn.execute(
                text("INSERT INTO users (id, name, email) VALUES (2, 'Bob', 'bob@test.com')")
            )
            conn.execute(
                text("INSERT INTO posts (id, user_id, title) VALUES (1, 1, 'First Post')")
            )

        self.engine = GraphSQLEngine(self.db_engine, self.config)

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()
        reset_graphsql_engine()

    def test_sql_query_select(self) -> None:
        """Test basic SELECT query."""
        result = self.engine.sql_query("SELECT * FROM users")
        assert result.success is True
        assert result.query_type == "SELECT"
        assert len(result.data) == 2
        assert result.row_count == 2

    def test_sql_query_select_with_where(self) -> None:
        """Test SELECT with WHERE clause."""
        result = self.engine.sql_query("SELECT * FROM users WHERE id = 1")
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["name"] == "Alice"

    def test_sql_query_select_columns(self) -> None:
        """Test SELECT specific columns."""
        result = self.engine.sql_query("SELECT name, email FROM users")
        assert result.success is True
        assert "name" in result.columns
        assert "email" in result.columns

    def test_sql_query_invalid_syntax(self) -> None:
        """Test query with invalid syntax."""
        result = self.engine.sql_query("SELEC * FROM users")
        assert result.success is False
        assert result.error is not None

    def test_sql_query_nonexistent_table(self) -> None:
        """Test query against nonexistent table."""
        result = self.engine.sql_query("SELECT * FROM nonexistent")
        assert result.success is False
        assert result.error is not None

    def test_sql_query_empty(self) -> None:
        """Test empty query."""
        result = self.engine.sql_query("")
        assert result.success is False
        assert "Empty" in result.error

    def test_sql_query_readonly_blocks_insert(self) -> None:
        """Test that read-only mode blocks INSERT."""
        from graphsql.mcp_server.security import SecurityValidator
        
        readonly_config = MCPServerConfig(
            database_url="sqlite:///:memory:",
            read_only=True,
        )
        readonly_validator = SecurityValidator(readonly_config)
        readonly_engine = GraphSQLEngine(self.db_engine, readonly_config, readonly_validator)
        result = readonly_engine.sql_query("INSERT INTO users VALUES (3, 'Test', 'test@test.com')")
        assert result.success is False
        assert "read-only" in result.error.lower()

    def test_sql_query_readonly_blocks_update(self) -> None:
        """Test that read-only mode blocks UPDATE."""
        from graphsql.mcp_server.security import SecurityValidator
        
        readonly_config = MCPServerConfig(
            database_url="sqlite:///:memory:",
            read_only=True,
        )
        readonly_validator = SecurityValidator(readonly_config)
        readonly_engine = GraphSQLEngine(self.db_engine, readonly_config, readonly_validator)
        result = readonly_engine.sql_query("UPDATE users SET name = 'Changed' WHERE id = 1")
        assert result.success is False
        assert "read-only" in result.error.lower()

    def test_sql_query_readonly_blocks_delete(self) -> None:
        """Test that read-only mode blocks DELETE."""
        from graphsql.mcp_server.security import SecurityValidator
        
        readonly_config = MCPServerConfig(
            database_url="sqlite:///:memory:",
            read_only=True,
        )
        readonly_validator = SecurityValidator(readonly_config)
        readonly_engine = GraphSQLEngine(self.db_engine, readonly_config, readonly_validator)
        result = readonly_engine.sql_query("DELETE FROM users WHERE id = 1")
        assert result.success is False
        assert "read-only" in result.error.lower()

    def test_introspect_schema(self) -> None:
        """Test schema introspection."""
        schema = self.engine.introspect_schema()
        assert schema.total_tables == 2
        assert schema.database_type == "sqlite"

        table_names = [t["name"] for t in schema.tables]
        assert "users" in table_names
        assert "posts" in table_names

    def test_introspect_schema_table_details(self) -> None:
        """Test schema introspection returns table details."""
        schema = self.engine.introspect_schema()
        users_table = next(t for t in schema.tables if t["name"] == "users")

        assert "columns" in users_table
        column_names = [c["name"] for c in users_table["columns"]]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names

    def test_health_check_healthy(self) -> None:
        """Test health check when healthy."""
        health = self.engine.health_check()
        assert health["status"] == "healthy"
        assert health["database_connected"] is True
        assert health["database_type"] == "sqlite"
        assert health["table_count"] == 2

    def test_metadata_lazy_load(self) -> None:
        """Test that metadata is lazy-loaded."""
        # Access metadata property
        metadata = self.engine.metadata
        assert metadata is not None
        assert "users" in metadata.tables

    def test_refresh_metadata(self) -> None:
        """Test metadata refresh."""
        # Initial metadata
        metadata1 = self.engine.metadata

        # Add a table using begin() for auto-commit
        with self.db_engine.begin() as conn:
            conn.execute(text("CREATE TABLE new_table (id INTEGER)"))

        # Refresh
        self.engine.refresh_metadata()
        metadata2 = self.engine.metadata

        assert "new_table" in metadata2.tables

    def test_graphql_query_all_users(self) -> None:
        """Test GraphQL query for all users."""
        result = self.engine.graphql_query("query { all_users { id name } }")
        assert result.success is True
        assert result.query_type == "GRAPHQL"

    def test_graphql_query_single_user(self) -> None:
        """Test GraphQL query for single user by ID."""
        result = self.engine.graphql_query("query { users(id: 1) { id name } }")
        assert result.success is True

    def test_graphql_query_with_limit(self) -> None:
        """Test GraphQL query with limit."""
        result = self.engine.graphql_query("query { all_users(limit: 1) { id name } }")
        assert result.success is True

    def test_graphql_query_empty(self) -> None:
        """Test empty GraphQL query."""
        result = self.engine.graphql_query("")
        assert result.success is False

    def test_graphql_query_invalid(self) -> None:
        """Test invalid GraphQL query format."""
        result = self.engine.graphql_query("not a valid query")
        assert result.success is False


class TestGetGraphSQLEngine:
    """Tests for get_graphsql_engine singleton."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()
        reset_graphsql_engine()

    def test_singleton(self) -> None:
        """Test that get_graphsql_engine returns same instance."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        db_engine = get_engine(config)

        engine1 = get_graphsql_engine(db_engine)
        engine2 = get_graphsql_engine(db_engine)
        assert engine1 is engine2

    def test_reset(self) -> None:
        """Test resetting the singleton."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        db_engine = get_engine(config)

        engine1 = get_graphsql_engine(db_engine)
        reset_graphsql_engine()
        engine2 = get_graphsql_engine(db_engine)
        assert engine1 is not engine2
