"""Tests for MCP server tools module."""

from sqlalchemy import text

from graphsql.mcp_server.config import MCPServerConfig, reset_config
from graphsql.mcp_server.db import close_engine, get_engine
from graphsql.mcp_server.engine import GraphSQLEngine, reset_graphsql_engine
from graphsql.mcp_server.tools import (
    TOOL_DEFINITIONS,
    GraphQLQueryInput,
    HealthResponse,
    MCPTools,
    QueryResponse,
    SchemaIntrospectInput,
    SchemaResponse,
    SQLQueryInput,
    get_tools,
    reset_tools,
)


class TestPydanticModels:
    """Tests for Pydantic input/output models."""

    def test_sql_query_input(self) -> None:
        """Test SQLQueryInput model."""
        input_model = SQLQueryInput(query="SELECT * FROM users")
        assert input_model.query == "SELECT * FROM users"

    def test_graphql_query_input(self) -> None:
        """Test GraphQLQueryInput model."""
        input_model = GraphQLQueryInput(query="{ users { id } }")
        assert input_model.query == "{ users { id } }"
        assert input_model.variables is None

    def test_graphql_query_input_with_variables(self) -> None:
        """Test GraphQLQueryInput with variables."""
        input_model = GraphQLQueryInput(
            query="{ user(id: $id) { name } }",
            variables={"id": 1},
        )
        assert input_model.variables == {"id": 1}

    def test_schema_introspect_input(self) -> None:
        """Test SchemaIntrospectInput model."""
        input_model = SchemaIntrospectInput()
        assert input_model.table_name is None

        input_model_with_table = SchemaIntrospectInput(table_name="users")
        assert input_model_with_table.table_name == "users"

    def test_query_response(self) -> None:
        """Test QueryResponse model."""
        response = QueryResponse(
            success=True,
            data=[{"id": 1}],
            columns=["id"],
            row_count=1,
            execution_time_ms=5.0,
            query_type="SELECT",
        )
        assert response.success is True
        assert response.row_count == 1

    def test_schema_response(self) -> None:
        """Test SchemaResponse model."""
        response = SchemaResponse(
            tables=[{"name": "users"}],
            total_tables=1,
            database_type="sqlite",
        )
        assert response.total_tables == 1

    def test_health_response(self) -> None:
        """Test HealthResponse model."""
        response = HealthResponse(
            status="healthy",
            database_connected=True,
            database_type="sqlite",
            latency_ms=1.5,
            table_count=5,
            read_only_mode=False,
            max_rows=1000,
            query_timeout=30,
        )
        assert response.status == "healthy"
        assert response.database_connected is True


class TestToolDefinitions:
    """Tests for TOOL_DEFINITIONS."""

    def test_tool_definitions_exist(self) -> None:
        """Test that tool definitions are present."""
        assert len(TOOL_DEFINITIONS) == 4

    def test_sql_query_tool_definition(self) -> None:
        """Test sql_query tool definition."""
        sql_tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "sql_query")
        assert "description" in sql_tool
        assert "inputSchema" in sql_tool

    def test_graphql_query_tool_definition(self) -> None:
        """Test graphql_query tool definition."""
        gql_tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "graphql_query")
        assert "description" in gql_tool
        assert "inputSchema" in gql_tool

    def test_schema_introspect_tool_definition(self) -> None:
        """Test schema_introspect tool definition."""
        schema_tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "schema_introspect")
        assert "description" in schema_tool

    def test_health_check_tool_definition(self) -> None:
        """Test health_check tool definition."""
        health_tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "health_check")
        assert "description" in health_tool


class TestMCPTools:
    """Tests for MCPTools class."""

    def setup_method(self) -> None:
        """Set up test database."""
        close_engine()
        reset_config()
        reset_graphsql_engine()
        reset_tools()

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
                    email TEXT
                )
            """
                )
            )
            conn.execute(text("INSERT INTO users VALUES (1, 'Alice', 'alice@test.com')"))
            conn.execute(text("INSERT INTO users VALUES (2, 'Bob', 'bob@test.com')"))

        graphsql_engine = GraphSQLEngine(self.db_engine, self.config)
        self.tools = MCPTools(graphsql_engine)

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()
        reset_graphsql_engine()
        reset_tools()

    def test_sql_query_success(self) -> None:
        """Test successful SQL query."""
        response = self.tools.sql_query("SELECT * FROM users")
        assert response.success is True
        assert len(response.data) == 2
        assert response.query_type == "SELECT"

    def test_sql_query_with_where(self) -> None:
        """Test SQL query with WHERE clause."""
        response = self.tools.sql_query("SELECT * FROM users WHERE id = 1")
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Alice"

    def test_sql_query_error(self) -> None:
        """Test SQL query with error."""
        response = self.tools.sql_query("SELECT * FROM nonexistent")
        assert response.success is False
        assert response.error is not None

    def test_graphql_query_success(self) -> None:
        """Test successful GraphQL query."""
        response = self.tools.graphql_query("query { all_users { id name } }")
        assert response.success is True
        assert response.query_type == "GRAPHQL"

    def test_graphql_query_with_variables(self) -> None:
        """Test GraphQL query with variables."""
        response = self.tools.graphql_query(
            "query { all_users(limit: 1) { id name } }",
            variables=None,
        )
        assert response.success is True

    def test_schema_introspect_all_tables(self) -> None:
        """Test schema introspection for all tables."""
        response = self.tools.schema_introspect()
        assert response.total_tables >= 1
        assert response.database_type == "sqlite"

        table_names = [t["name"] for t in response.tables]
        assert "users" in table_names

    def test_schema_introspect_single_table(self) -> None:
        """Test schema introspection for single table."""
        response = self.tools.schema_introspect(table_name="users")
        assert response.total_tables == 1
        assert response.tables[0]["name"] == "users"

    def test_schema_introspect_nonexistent_table(self) -> None:
        """Test schema introspection for nonexistent table."""
        response = self.tools.schema_introspect(table_name="nonexistent")
        assert response.total_tables == 0

    def test_health_check(self) -> None:
        """Test health check."""
        response = self.tools.health_check()
        assert response.status == "healthy"
        assert response.database_connected is True
        assert response.database_type == "sqlite"
        assert response.table_count >= 1


class TestGetTools:
    """Tests for get_tools singleton."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()
        reset_graphsql_engine()
        reset_tools()

    def test_singleton(self) -> None:
        """Test that get_tools returns same instance."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        get_engine(config)

        tools1 = get_tools()
        tools2 = get_tools()
        assert tools1 is tools2

    def test_reset(self) -> None:
        """Test resetting the singleton."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        get_engine(config)

        tools1 = get_tools()
        reset_tools()
        tools2 = get_tools()
        assert tools1 is not tools2
