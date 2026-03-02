"""GraphSQL engine wrapper for MCP integration.

This module provides a wrapper around the GraphSQL library that can be
used by the MCP server to execute queries. It integrates with the main
graphsql.database module for database operations.

Example:
    >>> from graphsql.mcp_server.engine import GraphSQLEngine
    >>> from graphsql.mcp_server.db import get_engine
    >>> engine = GraphSQLEngine(get_engine())
    >>> result = engine.sql_query("SELECT * FROM users LIMIT 10")
"""

from __future__ import annotations

import logging
import signal
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

from sqlalchemy import MetaData, inspect, text
from sqlalchemy.engine import Engine

from graphsql.mcp_server.config import MCPServerConfig, get_config
from graphsql.mcp_server.db import get_session, reflect_metadata
from graphsql.mcp_server.security import SecurityValidator, get_validator

logger = logging.getLogger(__name__)


class QueryTimeoutError(Exception):
    """Raised when a query exceeds the configured timeout."""

    pass


class QueryExecutionError(Exception):
    """Raised when query execution fails."""

    pass


@dataclass
class QueryResult:
    """Container for query execution results.

    Attributes:
        success: Whether the query executed successfully.
        data: Query result data (rows for SELECT, affected count for DML).
        columns: List of column names (for SELECT queries).
        row_count: Number of rows returned or affected.
        execution_time_ms: Query execution time in milliseconds.
        error: Error message if query failed.
        warnings: List of warning messages.
        query_type: Type of query executed.
    """

    success: bool
    data: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    query_type: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "success": self.success,
            "data": self.data,
            "columns": self.columns,
            "row_count": self.row_count,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "warnings": self.warnings,
            "query_type": self.query_type,
        }


@dataclass
class SchemaInfo:
    """Container for database schema information.

    Attributes:
        tables: List of table metadata.
        total_tables: Total number of tables.
        database_type: Type of database (postgresql, mysql, sqlite).
    """

    tables: list[dict[str, Any]] = field(default_factory=list)
    total_tables: int = 0
    database_type: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the schema.
        """
        return {
            "tables": self.tables,
            "total_tables": self.total_tables,
            "database_type": self.database_type,
        }


class GraphSQLEngine:
    """Wrapper around GraphSQL for MCP tool integration.

    This class provides a unified interface for executing SQL and GraphQL
    queries against the database, with security validation and timeout handling.
    It integrates with the main graphsql package for schema generation.

    Attributes:
        engine: SQLAlchemy database engine.
        config: Server configuration.
        validator: Security validator instance.
        metadata: Reflected database metadata.

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = GraphSQLEngine(create_engine("sqlite:///test.db"))
        >>> result = engine.sql_query("SELECT 1 as value")
        >>> result.data
        [{'value': 1}]
    """

    def __init__(
        self,
        db_engine: Engine,
        config: MCPServerConfig | None = None,
        validator: SecurityValidator | None = None,
    ) -> None:
        """Initialize the GraphSQL engine.

        Args:
            db_engine: SQLAlchemy database engine.
            config: Server configuration. Uses global config if None.
            validator: Security validator. Uses global validator if None.
        """
        self.engine = db_engine
        self.config = config or get_config()
        self.validator = validator or get_validator()
        self._metadata: MetaData | None = None

        logger.info("GraphSQLEngine initialized")

    @property
    def metadata(self) -> MetaData:
        """Get reflected database metadata (lazy-loaded).

        Returns:
            SQLAlchemy MetaData with reflected tables.
        """
        if self._metadata is None:
            self._metadata = reflect_metadata(self.engine)
        return self._metadata

    def refresh_metadata(self) -> None:
        """Refresh the database metadata.

        Call this after schema changes to update the cached metadata.
        """
        self._metadata = reflect_metadata(self.engine)
        logger.info("Database metadata refreshed")

    def sql_query(self, query: str) -> QueryResult:
        """Execute an SQL query and return results.

        The query is validated for security before execution.
        SELECT queries will have LIMIT added if missing.
        Read-only mode restricts to SELECT queries only.

        Args:
            query: SQL query string to execute.

        Returns:
            QueryResult with execution status and data.

        Example:
            >>> result = engine.sql_query("SELECT * FROM users")
            >>> for row in result.data:
            ...     print(row['name'])
        """
        start_time = datetime.now()

        # Validate query
        validation = self.validator.validate_sql(query)
        if not validation.is_valid:
            return QueryResult(
                success=False,
                error=validation.error,
                query_type=validation.query_type.value,
            )

        # Use modified query (with LIMIT added if needed)
        exec_query = validation.modified_query or query

        try:
            with self._timeout_context():
                with get_session(self.engine) as session:
                    result = session.execute(text(exec_query))

                    # Handle SELECT queries
                    if validation.query_type.value == "SELECT":
                        rows = result.fetchall()
                        columns = list(result.keys())

                        # Convert rows to dictionaries
                        data = [dict(zip(columns, row, strict=True)) for row in rows]

                        # Serialize special types
                        data = [self._serialize_row(row) for row in data]

                        execution_time = (datetime.now() - start_time).total_seconds() * 1000

                        return QueryResult(
                            success=True,
                            data=data,
                            columns=columns,
                            row_count=len(data),
                            execution_time_ms=execution_time,
                            warnings=validation.warnings,
                            query_type=validation.query_type.value,
                        )
                    else:
                        # DML queries - return affected row count
                        row_count = result.rowcount if result.rowcount >= 0 else 0
                        execution_time = (datetime.now() - start_time).total_seconds() * 1000

                        return QueryResult(
                            success=True,
                            row_count=row_count,
                            execution_time_ms=execution_time,
                            warnings=validation.warnings,
                            query_type=validation.query_type.value,
                        )

        except QueryTimeoutError:
            return QueryResult(
                success=False,
                error=f"Query timed out after {self.config.query_timeout} seconds",
                query_type=validation.query_type.value,
            )
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                query_type=validation.query_type.value,
            )

    def graphql_query(self, query: str, variables: dict[str, Any] | None = None) -> QueryResult:
        """Execute a GraphQL query using the GraphSQL library.

        This method integrates with the GraphSQL schema generator to execute
        GraphQL queries against the database.

        Args:
            query: GraphQL query string.
            variables: Optional GraphQL variables.

        Returns:
            QueryResult with execution status and data.

        Example:
            >>> result = engine.graphql_query('''
            ...     query {
            ...         all_users(limit: 10) {
            ...             id
            ...             name
            ...         }
            ...     }
            ... ''')
        """
        start_time = datetime.now()

        # Validate GraphQL query
        validation = self.validator.validate_graphql(query)
        if not validation.is_valid:
            return QueryResult(
                success=False,
                error=validation.error,
                query_type="GRAPHQL",
            )

        try:
            # Execute GraphQL query using SQL conversion
            # TODO: Integrate with graphsql.graphql_schema when available
            result = self._execute_graphql_as_sql(query, variables)
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            return result
        except Exception as e:
            logger.error(f"GraphQL execution failed: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                query_type="GRAPHQL",
            )

    def _execute_graphql_as_sql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> QueryResult:
        """Fallback GraphQL execution by converting to SQL.

        This is a simplified implementation that handles basic GraphQL queries.

        Args:
            query: GraphQL query string.
            variables: Optional GraphQL variables.

        Returns:
            QueryResult with execution status and data.
        """
        import re

        # Extract the query operation
        # Simple pattern matching for basic queries
        # Format: query { all_tablename(limit: N) { field1 field2 } }

        # Find table queries
        table_pattern = r"all_(\w+)\s*(?:\(([^)]*)\))?\s*\{([^}]+)\}"
        matches = re.findall(table_pattern, query, re.IGNORECASE)

        if not matches:
            # Try single record query pattern: tablename(id: N) { fields }
            single_pattern = r"(\w+)\s*\(\s*id\s*:\s*(\d+)\s*\)\s*\{([^}]+)\}"
            single_matches = re.findall(single_pattern, query, re.IGNORECASE)

            if single_matches:
                table_name, record_id, fields_str = single_matches[0]
                fields = [f.strip() for f in fields_str.split() if f.strip()]

                # Build SQL query
                fields_sql = ", ".join(fields) if fields else "*"
                sql = f"SELECT {fields_sql} FROM {table_name} WHERE id = {record_id}"

                return self.sql_query(sql)
            else:
                return QueryResult(
                    success=False,
                    error="Unable to parse GraphQL query. Supported formats: all_table { fields } or table(id: N) { fields }",
                    query_type="GRAPHQL",
                )

        # Handle all_tablename query
        table_name, params_str, fields_str = matches[0]

        # Parse fields
        fields = [f.strip() for f in fields_str.split() if f.strip()]
        fields_sql = ", ".join(fields) if fields else "*"

        # Parse parameters
        limit = self.config.max_rows
        offset = 0

        if params_str:
            limit_match = re.search(r"limit\s*:\s*(\d+)", params_str, re.IGNORECASE)
            if limit_match:
                limit = min(int(limit_match.group(1)), self.config.max_rows)

            offset_match = re.search(r"offset\s*:\s*(\d+)", params_str, re.IGNORECASE)
            if offset_match:
                offset = int(offset_match.group(1))

        # Build SQL query
        sql = f"SELECT {fields_sql} FROM {table_name} LIMIT {limit} OFFSET {offset}"

        result = self.sql_query(sql)
        result.query_type = "GRAPHQL"
        return result

    def introspect_schema(self) -> SchemaInfo:
        """Introspect the database schema and return metadata.

        Returns detailed information about all tables, columns, indexes,
        and relationships in the database.

        Returns:
            SchemaInfo with complete schema metadata.

        Example:
            >>> schema = engine.introspect_schema()
            >>> for table in schema.tables:
            ...     print(f"Table: {table['name']}")
        """
        try:
            inspector = inspect(self.engine)

            # Detect database type
            dialect_name = self.engine.dialect.name

            tables = []
            for table_name in inspector.get_table_names():
                # Check table access permissions
                if not self.config.is_table_allowed(table_name):
                    continue

                # Get column information
                columns = []
                for column in inspector.get_columns(table_name):
                    columns.append(
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": column.get("nullable", True),
                            "default": str(column.get("default"))
                            if column.get("default")
                            else None,
                            "autoincrement": column.get("autoincrement", False),
                        }
                    )

                # Get primary keys
                pk_constraint = inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint.get("constrained_columns", []) if pk_constraint else []

                # Get foreign keys
                foreign_keys = []
                for fk in inspector.get_foreign_keys(table_name):
                    foreign_keys.append(
                        {
                            "constrained_columns": fk.get("constrained_columns", []),
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns", []),
                        }
                    )

                # Get indexes
                indexes = []
                for idx in inspector.get_indexes(table_name):
                    indexes.append(
                        {
                            "name": idx.get("name"),
                            "columns": idx.get("column_names", []),
                            "unique": idx.get("unique", False),
                        }
                    )

                # Get row count (approximate)
                row_count = self._get_row_count(table_name)

                tables.append(
                    {
                        "name": table_name,
                        "columns": columns,
                        "primary_keys": primary_keys,
                        "foreign_keys": foreign_keys,
                        "indexes": indexes,
                        "row_count": row_count,
                    }
                )

            return SchemaInfo(
                tables=tables,
                total_tables=len(tables),
                database_type=dialect_name,
            )

        except Exception as e:
            logger.error(f"Schema introspection failed: {e}")
            return SchemaInfo(tables=[], total_tables=0, database_type="unknown")

    def health_check(self) -> dict[str, Any]:
        """Perform a health check on the database connection.

        Returns:
            Dictionary with health status information.

        Example:
            >>> health = engine.health_check()
            >>> health['status']
            'healthy'
        """
        try:
            start_time = datetime.now()

            with get_session(self.engine) as session:
                session.execute(text("SELECT 1"))

            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Get table count
            inspector = inspect(self.engine)
            table_count = len(inspector.get_table_names())

            return {
                "status": "healthy",
                "database_connected": True,
                "database_type": self.engine.dialect.name,
                "latency_ms": round(latency_ms, 2),
                "table_count": table_count,
                "read_only_mode": self.config.read_only,
                "max_rows": self.config.max_rows,
                "query_timeout": self.config.query_timeout,
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_connected": False,
                "error": str(e),
            }

    def _get_row_count(self, table_name: str) -> int | None:
        """Get approximate row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Row count or None if unable to determine.
        """
        try:
            with get_session(self.engine) as session:
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
                )
                scalar_result = result.scalar()
                return cast(int | None, scalar_result)
        except Exception:
            return None

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Serialize a row dictionary for JSON output.

        Handles special types like datetime, bytes, Decimal, etc.

        Args:
            row: Row dictionary to serialize.

        Returns:
            Serialized row dictionary.
        """
        from datetime import date, datetime
        from decimal import Decimal

        result: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, bytes):
                result[key] = value.decode("utf-8", errors="ignore")
            elif hasattr(value, "__dict__"):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    @contextmanager
    def _timeout_context(self) -> Generator[None, None, None]:
        """Context manager for query timeout.

        Implements timeout using signal alarm (Unix only).
        On Windows, timeout is not enforced.

        Yields:
            None

        Raises:
            QueryTimeoutError: If query exceeds timeout.
        """
        if self.config.query_timeout <= 0:
            yield
            return

        try:
            # Try to use signal-based timeout (Unix only)
            def timeout_handler(signum: int, frame: Any) -> None:
                raise QueryTimeoutError(f"Query timed out after {self.config.query_timeout}s")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.config.query_timeout)

            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        except (AttributeError, ValueError):
            # Signal not available (Windows) - just yield without timeout
            yield


# Singleton engine instance
_engine_instance: GraphSQLEngine | None = None


def get_graphsql_engine(db_engine: Engine | None = None) -> GraphSQLEngine:
    """Get or create the global GraphSQL engine instance.

    Args:
        db_engine: SQLAlchemy engine. Creates new if None.

    Returns:
        GraphSQLEngine singleton.
    """
    global _engine_instance
    if _engine_instance is None:
        if db_engine is None:
            from graphsql.mcp_server.db import get_engine

            db_engine = get_engine()
        _engine_instance = GraphSQLEngine(db_engine)
    return _engine_instance


def reset_graphsql_engine() -> None:
    """Reset the global GraphSQL engine instance."""
    global _engine_instance
    _engine_instance = None
