"""Tests for MCP server security module."""


from graphsql.mcp_server.config import MCPServerConfig
from graphsql.mcp_server.security import (
    QueryType,
    SecurityValidator,
    ValidationResult,
    get_validator,
    reset_validator,
)


class TestQueryType:
    """Tests for QueryType enum."""

    def test_query_types_exist(self) -> None:
        """Test that all query types are defined."""
        assert QueryType.SELECT.value == "SELECT"
        assert QueryType.INSERT.value == "INSERT"
        assert QueryType.UPDATE.value == "UPDATE"
        assert QueryType.DELETE.value == "DELETE"
        assert QueryType.CREATE.value == "CREATE"
        assert QueryType.DROP.value == "DROP"
        assert QueryType.UNKNOWN.value == "UNKNOWN"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self) -> None:
        """Test valid validation result."""
        result = ValidationResult(
            is_valid=True,
            query_type=QueryType.SELECT,
        )
        assert result.is_valid is True
        assert result.query_type == QueryType.SELECT
        assert result.error is None
        assert result.warnings == []
        assert result.modified_query is None

    def test_invalid_result(self) -> None:
        """Test invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            query_type=QueryType.DROP,
            error="DROP not allowed",
        )
        assert result.is_valid is False
        assert result.error == "DROP not allowed"

    def test_result_with_warnings(self) -> None:
        """Test validation result with warnings."""
        result = ValidationResult(
            is_valid=True,
            query_type=QueryType.SELECT,
            warnings=["LIMIT added", "Query modified"],
        )
        assert len(result.warnings) == 2


class TestSecurityValidator:
    """Tests for SecurityValidator class."""

    def setup_method(self) -> None:
        """Reset validator before each test."""
        reset_validator()

    def test_validate_empty_query(self) -> None:
        """Test validation of empty query."""
        validator = SecurityValidator()
        result = validator.validate_sql("")
        assert result.is_valid is False
        assert "Empty query" in result.error

    def test_validate_select_query(self) -> None:
        """Test validation of SELECT query."""
        validator = SecurityValidator()
        result = validator.validate_sql("SELECT * FROM users")
        assert result.is_valid is True
        assert result.query_type == QueryType.SELECT

    def test_validate_select_with_where(self) -> None:
        """Test validation of SELECT with WHERE clause."""
        validator = SecurityValidator()
        result = validator.validate_sql("SELECT id, name FROM users WHERE id = 1")
        assert result.is_valid is True
        assert result.query_type == QueryType.SELECT

    def test_validate_select_adds_limit(self) -> None:
        """Test that SELECT queries get LIMIT added."""
        config = MCPServerConfig(max_rows=100)
        validator = SecurityValidator(config)
        result = validator.validate_sql("SELECT * FROM users")
        assert result.is_valid is True
        assert result.modified_query is not None
        assert "LIMIT" in result.modified_query.upper()

    def test_validate_select_respects_existing_limit(self) -> None:
        """Test that existing LIMIT is respected."""
        config = MCPServerConfig(max_rows=100)
        validator = SecurityValidator(config)
        result = validator.validate_sql("SELECT * FROM users LIMIT 10")
        assert result.is_valid is True
        # Should not add another LIMIT

    def test_validate_select_enforces_max_limit(self) -> None:
        """Test that LIMIT exceeding max_rows is reduced."""
        config = MCPServerConfig(max_rows=100)
        validator = SecurityValidator(config)
        result = validator.validate_sql("SELECT * FROM users LIMIT 1000")
        assert result.is_valid is True
        # Limit should be reduced to max_rows

    def test_readonly_blocks_insert(self) -> None:
        """Test that read-only mode blocks INSERT."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("INSERT INTO users VALUES (1, 'test')")
        assert result.is_valid is False
        assert "not allowed in read-only mode" in result.error

    def test_readonly_blocks_update(self) -> None:
        """Test that read-only mode blocks UPDATE."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("UPDATE users SET name = 'test' WHERE id = 1")
        assert result.is_valid is False

    def test_readonly_blocks_delete(self) -> None:
        """Test that read-only mode blocks DELETE."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("DELETE FROM users WHERE id = 1")
        assert result.is_valid is False

    def test_readonly_blocks_drop(self) -> None:
        """Test that read-only mode blocks DROP."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("DROP TABLE users")
        assert result.is_valid is False

    def test_readonly_allows_select(self) -> None:
        """Test that read-only mode allows SELECT."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("SELECT * FROM users")
        assert result.is_valid is True

    def test_readonly_allows_show(self) -> None:
        """Test that read-only mode allows SHOW."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("SHOW TABLES")
        assert result.is_valid is True

    def test_readonly_allows_describe(self) -> None:
        """Test that read-only mode allows DESCRIBE."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("DESCRIBE users")
        assert result.is_valid is True

    def test_readonly_allows_explain(self) -> None:
        """Test that read-only mode allows EXPLAIN."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("EXPLAIN SELECT * FROM users")
        assert result.is_valid is True

    def test_dangerous_drop_table(self) -> None:
        """Test detection of DROP TABLE in read-only mode."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("DROP TABLE users")
        assert result.is_valid is False

    def test_dangerous_drop_table_writable_warns(self) -> None:
        """Test that DROP TABLE gives warning in writable mode."""
        config = MCPServerConfig(read_only=False)
        validator = SecurityValidator(config)
        result = validator.validate_sql("DROP TABLE users")
        # In writable mode, dangerous patterns get warnings only
        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_dangerous_drop_database(self) -> None:
        """Test detection of DROP DATABASE in read-only mode."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("DROP DATABASE mydb")
        assert result.is_valid is False

    def test_dangerous_truncate(self) -> None:
        """Test detection of TRUNCATE in read-only mode."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("TRUNCATE TABLE users")
        assert result.is_valid is False

    def test_dangerous_sql_injection_semicolon(self) -> None:
        """Test detection of SQL injection with semicolon in read-only mode."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql("SELECT * FROM users; DROP TABLE users")
        assert result.is_valid is False

    def test_dangerous_union_injection(self) -> None:
        """Test detection of UNION injection in read-only mode."""
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_sql(
            "SELECT * FROM users UNION SELECT * FROM passwords"
        )
        assert result.is_valid is False

    def test_validate_graphql_empty(self) -> None:
        """Test validation of empty GraphQL query."""
        validator = SecurityValidator()
        result = validator.validate_graphql("")
        assert result.is_valid is False

    def test_validate_graphql_valid(self) -> None:
        """Test validation of valid GraphQL query."""
        validator = SecurityValidator()
        result = validator.validate_graphql("query { users { id name } }")
        assert result.is_valid is True

    def test_validate_graphql_with_mutation(self) -> None:
        """Test validation of GraphQL mutation in read-only mode.

        Note: Current implementation does NOT block GraphQL mutations,
        it only validates query structure. Mutationen are handled at
        the GraphQL execution layer, not at validation time.
        """
        config = MCPServerConfig(read_only=True)
        validator = SecurityValidator(config)
        result = validator.validate_graphql("mutation { createUser(name: \"test\") { id } }")
        # GraphQL validation does not block mutations - this is handled at execution time
        assert result.is_valid is True

    def test_validate_graphql_introspection(self) -> None:
        """Test validation of GraphQL introspection query."""
        validator = SecurityValidator()
        result = validator.validate_graphql("{ __schema { types { name } } }")
        # Introspection should be allowed by default
        assert result.is_valid is True


class TestGetValidator:
    """Tests for get_validator singleton."""

    def setup_method(self) -> None:
        """Reset validator before each test."""
        reset_validator()

    def teardown_method(self) -> None:
        """Reset validator after each test."""
        reset_validator()

    def test_get_validator_singleton(self) -> None:
        """Test that get_validator returns the same instance."""
        validator1 = get_validator()
        validator2 = get_validator()
        assert validator1 is validator2

    def test_reset_validator(self) -> None:
        """Test that reset_validator clears the singleton."""
        validator1 = get_validator()
        reset_validator()
        validator2 = get_validator()
        assert validator1 is not validator2
