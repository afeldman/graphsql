"""Tests for MCP server database module."""

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from graphsql.mcp_server.config import MCPServerConfig, reset_config
from graphsql.mcp_server.db import (
    close_engine,
    create_db_engine,
    get_engine,
    get_session,
    get_table_names,
    reflect_metadata,
    test_connection,
)


class TestCreateDbEngine:
    """Tests for create_db_engine function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_create_sqlite_engine(self) -> None:
        """Test creating SQLite engine."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = create_db_engine(config)
        assert engine is not None
        assert isinstance(engine, Engine)
        assert engine.url.database == ":memory:"
        engine.dispose()

    def test_create_engine_default_config(self) -> None:
        """Test creating engine with default config."""
        engine = create_db_engine()
        assert engine is not None
        engine.dispose()


class TestGetEngine:
    """Tests for get_engine singleton."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_get_engine_singleton(self) -> None:
        """Test that get_engine returns same instance."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine1 = get_engine(config)
        engine2 = get_engine(config)
        assert engine1 is engine2

    def test_close_engine(self) -> None:
        """Test closing the engine."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine1 = get_engine(config)
        close_engine()
        engine2 = get_engine(config)
        # After close, new engine should be created
        assert engine1 is not engine2


class TestGetSession:
    """Tests for get_session context manager."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_get_session_basic(self) -> None:
        """Test basic session usage."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        with get_session(engine) as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_get_session_commit(self) -> None:
        """Test session commits on success."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        # Create a table using begin() for auto-commit
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"))

        # Insert with session
        with get_session(engine) as session:
            session.execute(text("INSERT INTO test (id, name) VALUES (1, 'test')"))

        # Verify committed
        with get_session(engine) as session:
            result = session.execute(text("SELECT name FROM test WHERE id = 1"))
            assert result.scalar() == "test"

    def test_get_session_rollback_on_error(self) -> None:
        """Test session rolls back on error."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        # Create a table using begin() for auto-commit
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"))

        # Try to insert with error
        try:
            with get_session(engine) as session:
                session.execute(text("INSERT INTO test (id, name) VALUES (1, 'test')"))
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify rolled back
        with get_session(engine) as session:
            result = session.execute(text("SELECT COUNT(*) FROM test"))
            assert result.scalar() == 0


class TestReflectMetadata:
    """Tests for reflect_metadata function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_reflect_empty_database(self) -> None:
        """Test reflecting empty database."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)
        metadata = reflect_metadata(engine)
        assert len(metadata.tables) == 0

    def test_reflect_with_tables(self) -> None:
        """Test reflecting database with tables."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        # Create tables using begin() for auto-commit
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
            conn.execute(text("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT)"))

        metadata = reflect_metadata(engine)
        assert "users" in metadata.tables
        assert "posts" in metadata.tables


class TestGetTableNames:
    """Tests for get_table_names function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_get_table_names_empty(self) -> None:
        """Test getting table names from empty database."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)
        names = get_table_names(engine)
        assert names == []

    def test_get_table_names_with_tables(self) -> None:
        """Test getting table names."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        # Create tables using begin() for auto-commit
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE alpha (id INTEGER)"))
            conn.execute(text("CREATE TABLE beta (id INTEGER)"))

        names = get_table_names(engine)
        assert "alpha" in names
        assert "beta" in names


class TestTestConnection:
    """Tests for test_connection function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_connection_success(self) -> None:
        """Test successful connection."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)
        assert test_connection(engine) is True

    def test_connection_with_default_engine(self) -> None:
        """Test connection with default engine."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        get_engine(config)  # Initialize global engine
        assert test_connection() is True
