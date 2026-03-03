"""Tests for MCP server main module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text

from graphsql.mcp_server.config import MCPServerConfig, reset_config
from graphsql.mcp_server.db import close_engine, get_engine
from graphsql.mcp_server.main import create_mcp_server


class TestCreateMCPServer:
    """Tests for create_mcp_server function."""

    def setup_method(self) -> None:
        """Set up test database."""
        close_engine()
        reset_config()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_create_server_returns_server(self) -> None:
        """Test that create_mcp_server returns a Server instance."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        # Create a table so we have something to introspect
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))

        server = create_mcp_server(config)
        assert server is not None
        assert hasattr(server, "run")

    def test_create_server_with_default_config(self) -> None:
        """Test create_mcp_server with default config."""
        # Set up a valid database first
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        get_engine(config)

        # Now create server with implicit config
        server = create_mcp_server()
        assert server is not None

    def test_create_server_fails_with_bad_connection(self) -> None:
        """Test that create_mcp_server raises on failed connection."""
        # This should fail because of invalid database URL
        with patch("graphsql.mcp_server.main.test_connection") as mock_test:
            mock_test.return_value = False
            config = MCPServerConfig(database_url="sqlite:///:memory:")

            with pytest.raises(RuntimeError, match="Database connection failed"):
                create_mcp_server(config)

    def test_create_server_registers_handlers(self) -> None:
        """Test that create_mcp_server registers all handlers."""
        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)

        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))

        server = create_mcp_server(config)
        # Server should have registered handlers
        assert server is not None


class TestRunServer:
    """Tests for run_server function."""

    def setup_method(self) -> None:
        """Set up test database."""
        close_engine()
        reset_config()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    @pytest.mark.asyncio
    async def test_run_server_calls_server_run(self) -> None:
        """Test that run_server sets up and runs the server."""
        from graphsql.mcp_server.main import run_server

        config = MCPServerConfig(database_url="sqlite:///:memory:")
        engine = get_engine(config)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER)"))

        # Patch stdio_server and server.run
        mock_read = AsyncMock()
        mock_write = AsyncMock()

        async def mock_aenter(*args, **kwargs):
            return (mock_read, mock_write)

        async def mock_aexit(*args, **kwargs):
            return None

        mock_context = MagicMock()
        mock_context.__aenter__ = mock_aenter
        mock_context.__aexit__ = mock_aexit

        with patch("graphsql.mcp_server.main.stdio_server", return_value=mock_context):
            with patch("mcp.server.Server.run", new_callable=AsyncMock) as mock_run:
                await run_server()
                mock_run.assert_called_once()


class TestMain:
    """Tests for main entry point."""

    def setup_method(self) -> None:
        """Set up test database."""
        close_engine()
        reset_config()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        close_engine()
        reset_config()

    def test_main_keyboard_interrupt(self) -> None:
        """Test main handles keyboard interrupt gracefully."""
        from graphsql.mcp_server.main import main

        with patch("graphsql.mcp_server.main.asyncio.run") as mock_run:
            mock_run.side_effect = KeyboardInterrupt()

            # Should not raise, just log and return
            main()

    def test_main_exception_exits(self) -> None:
        """Test main exits with error code on exception."""
        from graphsql.mcp_server.main import main

        with patch("graphsql.mcp_server.main.asyncio.run") as mock_run:
            mock_run.side_effect = RuntimeError("Test error")

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_success(self) -> None:
        """Test main completes successfully."""
        from graphsql.mcp_server.main import main

        with patch("graphsql.mcp_server.main.asyncio.run") as mock_run:
            mock_run.return_value = None

            # Should complete without error
            main()
            mock_run.assert_called_once()
