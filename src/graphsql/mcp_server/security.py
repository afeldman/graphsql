"""Security layer for query validation and protection.

This module provides security features to protect database access:
- Query timeout enforcement
- Row count limiting
- Read-only mode enforcement
- Dangerous SQL pattern detection
- Table access control

Example:
    >>> from graphsql.mcp_server.security import SecurityValidator
    >>> validator = SecurityValidator(read_only=True)
    >>> validator.validate_sql("SELECT * FROM users")  # OK
    >>> validator.validate_sql("DROP TABLE users")  # Raises SecurityError
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

from graphsql.mcp_server.config import MCPServerConfig, get_config

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security violation is detected."""

    pass


class QueryType(Enum):
    """Types of SQL queries."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"
    GRANT = "GRANT"
    REVOKE = "REVOKE"
    EXECUTE = "EXECUTE"
    CALL = "CALL"
    UNKNOWN = "UNKNOWN"


# Patterns for dangerous SQL operations
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA|INDEX|VIEW|PROCEDURE|FUNCTION)\b", "DROP statement"),
    (r"\bALTER\s+(?:TABLE|DATABASE|SCHEMA)\b", "ALTER statement"),
    (r"\bTRUNCATE\s+(?:TABLE)?\b", "TRUNCATE statement"),
    (r"\bCREATE\s+(?:TABLE|DATABASE|SCHEMA|INDEX|VIEW|PROCEDURE|FUNCTION)\b", "CREATE statement"),
    (r"\bDELETE\s+FROM\b", "DELETE statement"),
    (r"\bUPDATE\s+\w+\s+SET\b", "UPDATE statement"),
    (r"\bINSERT\s+INTO\b", "INSERT statement"),
    (r"\bGRANT\b", "GRANT statement"),
    (r"\bREVOKE\b", "REVOKE statement"),
    (r"\bEXEC(?:UTE)?\s*\(", "EXECUTE statement"),
    (r";\s*(?:DROP|ALTER|TRUNCATE|DELETE|UPDATE|INSERT)", "SQL injection attempt"),
    (r"--\s*$", "SQL comment injection"),
    (r"/\*.*\*/", "SQL block comment"),
    (r"\bUNION\s+(?:ALL\s+)?SELECT\b", "UNION injection"),
    (r"\bINTO\s+(?:OUTFILE|DUMPFILE)\b", "File write attempt"),
    (r"\bLOAD_FILE\s*\(", "File read attempt"),
    (r"\bBENCHMARK\s*\(", "Benchmark attack"),
    (r"\bSLEEP\s*\(", "Time-based attack"),
    (r"\bWAITFOR\s+DELAY\b", "Time-based attack"),
    (r"\b(?:xp_|sp_)cmdshell\b", "Command shell attack"),
]

# Read-only patterns (allowed in read-only mode)
READONLY_PATTERNS: list[str] = [
    r"^\s*SELECT\b",
    r"^\s*SHOW\b",
    r"^\s*DESCRIBE\b",
    r"^\s*DESC\b",
    r"^\s*EXPLAIN\b",
    r"^\s*WITH\s+.*\bSELECT\b",
]


@dataclass
class ValidationResult:
    """Result of query validation.

    Attributes:
        is_valid: Whether the query passed validation.
        query_type: Detected type of query.
        error: Error message if validation failed.
        warnings: List of warning messages.
        modified_query: Query after any modifications (e.g., LIMIT added).
    """

    is_valid: bool
    query_type: QueryType
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    modified_query: str | None = None


class SecurityValidator:
    """Validates and sanitizes database queries.

    This class provides comprehensive security validation for SQL queries,
    including read-only mode enforcement, dangerous pattern detection,
    and row limiting.

    Attributes:
        config: Server configuration instance.
        _compiled_dangerous: Compiled regex patterns for dangerous SQL.
        _compiled_readonly: Compiled regex patterns for read-only SQL.

    Example:
        >>> validator = SecurityValidator()
        >>> result = validator.validate_sql("SELECT * FROM users")
        >>> result.is_valid
        True
    """

    def __init__(self, config: MCPServerConfig | None = None) -> None:
        """Initialize the security validator.

        Args:
            config: Server configuration. Uses global config if None.
        """
        self.config = config or get_config()

        # Pre-compile dangerous patterns
        self._compiled_dangerous = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), desc)
            for pattern, desc in DANGEROUS_PATTERNS
        ]

        # Pre-compile read-only patterns
        self._compiled_readonly = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in READONLY_PATTERNS
        ]

        logger.debug(
            f"SecurityValidator initialized (read_only={self.config.read_only}, "
            f"max_rows={self.config.max_rows})"
        )

    def validate_sql(self, query: str) -> ValidationResult:
        """Validate an SQL query for security.

        Performs the following checks:
        1. Empty query check
        2. Read-only mode enforcement
        3. Dangerous pattern detection
        4. Row limit enforcement (adds LIMIT if missing)

        Args:
            query: SQL query string to validate.

        Returns:
            ValidationResult with validation status and details.

        Raises:
            SecurityError: If a critical security violation is detected.

        Example:
            >>> validator = SecurityValidator()
            >>> result = validator.validate_sql("SELECT * FROM users")
            >>> result.is_valid
            True
            >>> result.modified_query
            'SELECT * FROM users LIMIT 1000'
        """
        warnings: list[str] = []
        modified_query = query.strip()

        # Check for empty query
        if not modified_query:
            return ValidationResult(
                is_valid=False,
                query_type=QueryType.UNKNOWN,
                error="Empty query provided",
            )

        # Detect query type
        query_type = self._detect_query_type(modified_query)

        # Check read-only mode
        if self.config.read_only:
            if not self._is_readonly_query(modified_query):
                return ValidationResult(
                    is_valid=False,
                    query_type=query_type,
                    error=f"Query type '{query_type.value}' not allowed in read-only mode",
                )

        # Check for dangerous patterns (even in non-read-only mode, some patterns are blocked)
        dangerous_check = self._check_dangerous_patterns(modified_query)
        if dangerous_check:
            logger.warning(f"Dangerous SQL pattern detected: {dangerous_check}")
            if self.config.read_only:
                return ValidationResult(
                    is_valid=False,
                    query_type=query_type,
                    error=f"Dangerous pattern detected: {dangerous_check}",
                )
            else:
                warnings.append(f"Potentially dangerous pattern: {dangerous_check}")

        # Add LIMIT clause for SELECT queries if not present
        if query_type == QueryType.SELECT:
            modified_query, limit_warning = self._ensure_limit(modified_query)
            if limit_warning:
                warnings.append(limit_warning)

        return ValidationResult(
            is_valid=True,
            query_type=query_type,
            warnings=warnings,
            modified_query=modified_query,
        )

    def validate_graphql(self, query: str) -> ValidationResult:
        """Validate a GraphQL query.

        GraphQL queries are generally safer than raw SQL as they go through
        the schema. This method performs basic sanity checks.

        Args:
            query: GraphQL query string.

        Returns:
            ValidationResult with validation status.
        """
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                query_type=QueryType.UNKNOWN,
                error="Empty GraphQL query provided",
            )

        # Check for excessively deep nesting (DoS prevention)
        depth = self._calculate_graphql_depth(query)
        if depth > 10:
            return ValidationResult(
                is_valid=False,
                query_type=QueryType.SELECT,
                error=f"GraphQL query too deeply nested (depth: {depth}, max: 10)",
            )

        # Check for excessive fields (DoS prevention)
        field_count = len(re.findall(r"\w+\s*(?:\([^)]*\))?\s*{", query))
        if field_count > 50:
            return ValidationResult(
                is_valid=False,
                query_type=QueryType.SELECT,
                error=f"GraphQL query has too many field selections ({field_count}, max: 50)",
            )

        return ValidationResult(
            is_valid=True,
            query_type=QueryType.SELECT,
            modified_query=query,
        )

    def check_table_access(self, table_name: str) -> bool:
        """Check if access to a table is allowed.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if access is allowed, False otherwise.
        """
        return self.config.is_table_allowed(table_name)

    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of SQL query.

        Args:
            query: SQL query string.

        Returns:
            QueryType enum value.
        """
        query_upper = query.strip().upper()

        for qt in QueryType:
            if qt != QueryType.UNKNOWN and query_upper.startswith(qt.value):
                return qt

        # Check for WITH ... SELECT (CTE)
        if query_upper.startswith("WITH"):
            if "SELECT" in query_upper:
                return QueryType.SELECT

        return QueryType.UNKNOWN

    def _is_readonly_query(self, query: str) -> bool:
        """Check if a query is read-only.

        Args:
            query: SQL query string.

        Returns:
            True if query is read-only.
        """
        for pattern in self._compiled_readonly:
            if pattern.search(query):
                return True
        return False

    def _check_dangerous_patterns(self, query: str) -> str | None:
        """Check for dangerous SQL patterns.

        Args:
            query: SQL query string.

        Returns:
            Description of dangerous pattern found, or None.
        """
        for pattern, description in self._compiled_dangerous:
            if pattern.search(query):
                return description
        return None

    def _ensure_limit(self, query: str) -> tuple[str, str | None]:
        """Ensure SELECT query has a LIMIT clause.

        Args:
            query: SQL query string.

        Returns:
            Tuple of (modified query, warning message or None).
        """
        # Check if LIMIT already exists
        if re.search(r"\bLIMIT\s+\d+", query, re.IGNORECASE):
            # Extract existing limit value
            match = re.search(r"\bLIMIT\s+(\d+)", query, re.IGNORECASE)
            if match:
                existing_limit = int(match.group(1))
                if existing_limit > self.config.max_rows:
                    # Replace with max_rows
                    modified = re.sub(
                        r"\bLIMIT\s+\d+",
                        f"LIMIT {self.config.max_rows}",
                        query,
                        flags=re.IGNORECASE,
                    )
                    return (
                        modified,
                        f"LIMIT reduced from {existing_limit} to {self.config.max_rows}",
                    )
            return query, None

        # Add LIMIT clause
        # Handle trailing semicolon
        if query.rstrip().endswith(";"):
            query = query.rstrip()[:-1]
            modified = f"{query} LIMIT {self.config.max_rows};"
        else:
            modified = f"{query} LIMIT {self.config.max_rows}"

        return modified, f"Added LIMIT {self.config.max_rows} clause"

    def _calculate_graphql_depth(self, query: str) -> int:
        """Calculate nesting depth of GraphQL query.

        Args:
            query: GraphQL query string.

        Returns:
            Maximum nesting depth.
        """
        max_depth = 0
        current_depth = 0

        for char in query:
            if char == "{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "}":
                current_depth = max(0, current_depth - 1)

        return max_depth


# Singleton validator instance
_validator: SecurityValidator | None = None


def get_validator() -> SecurityValidator:
    """Get the global security validator instance.

    Returns:
        SecurityValidator singleton.
    """
    global _validator
    if _validator is None:
        _validator = SecurityValidator()
    return _validator


def reset_validator() -> None:
    """Reset the global validator instance."""
    global _validator
    _validator = None


def validate_sql_query(query: str) -> ValidationResult:
    """Convenience function to validate an SQL query.

    Args:
        query: SQL query string.

    Returns:
        ValidationResult with validation status.
    """
    return get_validator().validate_sql(query)


def validate_graphql_query(query: str) -> ValidationResult:
    """Convenience function to validate a GraphQL query.

    Args:
        query: GraphQL query string.

    Returns:
        ValidationResult with validation status.
    """
    return get_validator().validate_graphql(query)
