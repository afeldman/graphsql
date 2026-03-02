"""MCP Tools for database access.

This module defines the MCP tools that are exposed to LLM agents:
- graphql_query: Execute GraphQL queries
- sql_query: Execute SQL queries
- schema_introspect: Get database schema information
- health_check: Check database connectivity

Example:
    Tools are registered with the MCP server and invoked by agents::

        result = await sql_query(query="SELECT * FROM users LIMIT 10")
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from graphsql.mcp_server.engine import (
    GraphSQLEngine,
    get_graphsql_engine,
)

logger = logging.getLogger(__name__)


# Pydantic models for tool inputs/outputs
class SQLQueryInput(BaseModel):
    """Input schema for sql_query tool."""

    query: str = Field(
        ...,
        description="SQL query to execute. SELECT queries are limited to MAX_ROWS. "
        "In read-only mode, only SELECT/SHOW/DESCRIBE queries are allowed.",
        examples=[
            "SELECT * FROM users LIMIT 10",
            "SELECT name, email FROM customers WHERE active = true",
        ],
    )


class GraphQLQueryInput(BaseModel):
    """Input schema for graphql_query tool."""

    query: str = Field(
        ...,
        description="GraphQL query to execute. Supports queries against any table in the database.",
        examples=[
            "query { all_users(limit: 10) { id name email } }",
            "query { users(id: 1) { id name created_at } }",
        ],
    )
    variables: dict[str, Any] | None = Field(
        default=None,
        description="Optional GraphQL variables as a JSON object.",
    )


class SchemaIntrospectInput(BaseModel):
    """Input schema for schema_introspect tool."""

    table_name: str | None = Field(
        default=None,
        description="Optional table name to get schema for. If not provided, returns all tables.",
    )


class HealthCheckInput(BaseModel):
    """Input schema for health_check tool."""

    pass  # No inputs needed


class QueryResponse(BaseModel):
    """Response schema for query tools."""

    success: bool = Field(description="Whether the query executed successfully")
    data: list[dict[str, Any]] = Field(
        default_factory=list, description="Query result data as list of row objects"
    )
    columns: list[str] = Field(default_factory=list, description="Column names in the result")
    row_count: int = Field(default=0, description="Number of rows returned or affected")
    execution_time_ms: float = Field(
        default=0.0, description="Query execution time in milliseconds"
    )
    error: str | None = Field(default=None, description="Error message if query failed")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    query_type: str = Field(default="UNKNOWN", description="Type of query executed")


class SchemaResponse(BaseModel):
    """Response schema for schema_introspect tool."""

    tables: list[dict[str, Any]] = Field(default_factory=list, description="List of table metadata")
    total_tables: int = Field(default=0, description="Total number of tables")
    database_type: str = Field(default="unknown", description="Database type")


class HealthResponse(BaseModel):
    """Response schema for health_check tool."""

    status: str = Field(description="Health status: 'healthy' or 'unhealthy'")
    database_connected: bool = Field(description="Whether database connection is active")
    database_type: str = Field(default="unknown", description="Database dialect")
    latency_ms: float = Field(default=0.0, description="Connection latency in milliseconds")
    table_count: int = Field(default=0, description="Number of tables in database")
    read_only_mode: bool = Field(default=False, description="Whether read-only mode is enabled")
    max_rows: int = Field(default=1000, description="Maximum rows per query")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    error: str | None = Field(default=None, description="Error message if unhealthy")


class MCPTools:
    """Container for MCP tools.

    This class provides methods that are registered as MCP tools.
    Each method corresponds to a tool that LLM agents can invoke.

    Attributes:
        engine: GraphSQL engine instance for query execution.

    Example:
        >>> tools = MCPTools()
        >>> result = tools.sql_query("SELECT * FROM users LIMIT 5")
        >>> print(result.success)
        True
    """

    def __init__(self, engine: GraphSQLEngine | None = None) -> None:
        """Initialize MCP tools.

        Args:
            engine: GraphSQL engine. Uses global instance if None.
        """
        self.engine = engine or get_graphsql_engine()
        logger.info("MCPTools initialized")

    def sql_query(self, query: str) -> QueryResponse:
        """Execute an SQL query against the database.

        This tool allows LLM agents to run SQL queries. Security measures
        are applied automatically:
        - Read-only mode restricts to SELECT queries
        - Row limits are enforced
        - Dangerous patterns are detected and blocked
        - Query timeouts prevent long-running queries

        Args:
            query: SQL query string to execute.

        Returns:
            QueryResponse with results or error information.

        Example:
            >>> result = tools.sql_query("SELECT id, name FROM users WHERE active = true")
            >>> for row in result.data:
            ...     print(f"{row['id']}: {row['name']}")
        """
        logger.info(f"Executing SQL query: {query[:100]}...")

        result = self.engine.sql_query(query)

        return QueryResponse(
            success=result.success,
            data=result.data,
            columns=result.columns,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
            error=result.error,
            warnings=result.warnings,
            query_type=result.query_type,
        )

    def graphql_query(self, query: str, variables: dict[str, Any] | None = None) -> QueryResponse:
        """Execute a GraphQL query against the database.

        This tool allows LLM agents to run GraphQL queries. The GraphQL
        schema is automatically generated from the database structure.

        Supported query formats:
        - all_tablename(limit: N, offset: M) { field1 field2 }
        - tablename(id: N) { field1 field2 }

        Args:
            query: GraphQL query string.
            variables: Optional GraphQL variables.

        Returns:
            QueryResponse with results or error information.

        Example:
            >>> result = tools.graphql_query('''
            ...     query {
            ...         all_users(limit: 10) {
            ...             id
            ...             name
            ...             email
            ...         }
            ...     }
            ... ''')
        """
        logger.info(f"Executing GraphQL query: {query[:100]}...")

        result = self.engine.graphql_query(query, variables)

        return QueryResponse(
            success=result.success,
            data=result.data,
            columns=result.columns,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
            error=result.error,
            warnings=result.warnings,
            query_type=result.query_type,
        )

    def schema_introspect(self, table_name: str | None = None) -> SchemaResponse:
        """Introspect the database schema.

        Returns detailed information about database tables including:
        - Column names and types
        - Primary keys
        - Foreign key relationships
        - Indexes
        - Approximate row counts

        Args:
            table_name: Optional table name to filter results.

        Returns:
            SchemaResponse with schema information.

        Example:
            >>> schema = tools.schema_introspect()
            >>> for table in schema.tables:
            ...     print(f"Table {table['name']} has {len(table['columns'])} columns")
        """
        logger.info(f"Introspecting schema (table: {table_name or 'all'})")

        schema_info = self.engine.introspect_schema()

        # Filter by table name if provided
        if table_name:
            schema_info.tables = [t for t in schema_info.tables if t["name"] == table_name]
            schema_info.total_tables = len(schema_info.tables)

        return SchemaResponse(
            tables=schema_info.tables,
            total_tables=schema_info.total_tables,
            database_type=schema_info.database_type,
        )

    def health_check(self) -> HealthResponse:
        """Check the health of the database connection.

        Performs a lightweight connectivity test and returns status
        information about the MCP server configuration.

        Returns:
            HealthResponse with health status.

        Example:
            >>> health = tools.health_check()
            >>> if health.status == "healthy":
            ...     print(f"Connected to {health.database_type}")
        """
        logger.info("Performing health check")

        health_info = self.engine.health_check()

        return HealthResponse(
            status=health_info.get("status", "unknown"),
            database_connected=health_info.get("database_connected", False),
            database_type=health_info.get("database_type", "unknown"),
            latency_ms=health_info.get("latency_ms", 0.0),
            table_count=health_info.get("table_count", 0),
            read_only_mode=health_info.get("read_only_mode", False),
            max_rows=health_info.get("max_rows", 1000),
            query_timeout=health_info.get("query_timeout", 30),
            error=health_info.get("error"),
        )


# Tool definitions for MCP registration
TOOL_DEFINITIONS = [
    {
        "name": "sql_query",
        "description": (
            "Execute an SQL query against the database. "
            "Returns results as a list of row objects. "
            "SELECT queries are automatically limited to prevent large result sets. "
            "In read-only mode, only SELECT/SHOW/DESCRIBE queries are allowed. "
            "Dangerous patterns (DROP, ALTER, etc.) are blocked."
        ),
        "inputSchema": SQLQueryInput.model_json_schema(),
    },
    {
        "name": "graphql_query",
        "description": (
            "Execute a GraphQL query against the database. "
            "The schema is automatically generated from database tables. "
            "Supports queries like: all_tablename(limit: N) { fields } "
            "or tablename(id: N) { fields }"
        ),
        "inputSchema": GraphQLQueryInput.model_json_schema(),
    },
    {
        "name": "schema_introspect",
        "description": (
            "Get database schema information including tables, columns, "
            "primary keys, foreign keys, indexes, and approximate row counts. "
            "Optionally filter by table name."
        ),
        "inputSchema": SchemaIntrospectInput.model_json_schema(),
    },
    {
        "name": "health_check",
        "description": (
            "Check the health of the database connection and MCP server. "
            "Returns connectivity status, latency, and configuration information."
        ),
        "inputSchema": HealthCheckInput.model_json_schema(),
    },
]


# Singleton tools instance
_tools: MCPTools | None = None


def get_tools() -> MCPTools:
    """Get the global MCPTools instance.

    Returns:
        MCPTools singleton.
    """
    global _tools
    if _tools is None:
        _tools = MCPTools()
    return _tools


def reset_tools() -> None:
    """Reset the global tools instance."""
    global _tools
    _tools = None
