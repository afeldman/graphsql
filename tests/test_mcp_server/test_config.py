"""Tests for MCP server configuration."""

import os
from unittest.mock import patch

import pytest

from graphsql.mcp_server.config import MCPServerConfig, get_config, reset_config


class TestMCPServerConfig:
    """Tests for MCPServerConfig dataclass."""

    def setup_method(self) -> None:
        """Reset config before each test."""
        reset_config()

    def teardown_method(self) -> None:
        """Reset config after each test."""
        reset_config()

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MCPServerConfig()
        assert config.database_url == "sqlite:///./database.db"
        assert config.server_name == "graphsql"
        assert config.server_version == "0.1.0"
        assert config.max_rows == 1000
        assert config.query_timeout == 30
        assert config.read_only is False
        assert config.log_level == "INFO"
        assert config.enable_auth is False
        assert config.auth_method == "none"
        assert config.api_key == ""
        assert config.pool_size == 5
        assert config.pool_max_overflow == 10

    def test_from_env_defaults(self) -> None:
        """Test loading config from environment with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPServerConfig.from_env()
            assert config.database_url == "sqlite:///./database.db"
            assert config.server_name == "graphsql"
            assert config.max_rows == 1000

    def test_from_env_custom_values(self) -> None:
        """Test loading config from environment with custom values."""
        env_vars = {
            "DATABASE_URL": "postgresql://user:pass@localhost/testdb",
            "MCP_SERVER_NAME": "custom-server",
            "MCP_SERVER_VERSION": "1.0.0",
            "MAX_ROWS": "500",
            "QUERY_TIMEOUT": "60",
            "READ_ONLY": "true",
            "LOG_LEVEL": "DEBUG",
            "ENABLE_AUTH": "true",
            "AUTH_METHOD": "api_key",
            "API_KEY": "secret-key-123",
            "POOL_SIZE": "10",
            "POOL_MAX_OVERFLOW": "20",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = MCPServerConfig.from_env()
            assert config.database_url == "postgresql://user:pass@localhost/testdb"
            assert config.server_name == "custom-server"
            assert config.server_version == "1.0.0"
            assert config.max_rows == 500
            assert config.query_timeout == 60
            assert config.read_only is True
            assert config.log_level == "DEBUG"
            assert config.enable_auth is True
            assert config.auth_method == "api_key"
            assert config.api_key == "secret-key-123"
            assert config.pool_size == 10
            assert config.pool_max_overflow == 20

    def test_from_env_allowed_tables(self) -> None:
        """Test loading allowed tables from environment."""
        env_vars = {
            "ALLOWED_TABLES": "users,orders,products",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = MCPServerConfig.from_env()
            assert config.allowed_tables == ("users", "orders", "products")

    def test_from_env_denied_tables(self) -> None:
        """Test loading denied tables from environment."""
        env_vars = {
            "DENIED_TABLES": "secrets,passwords",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = MCPServerConfig.from_env()
            assert config.denied_tables == ("secrets", "passwords")

    def test_from_env_empty_tables(self) -> None:
        """Test empty allowed/denied tables."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPServerConfig.from_env()
            assert config.allowed_tables == ()
            assert config.denied_tables == ()

    def test_is_table_allowed_no_restrictions(self) -> None:
        """Test table access with no restrictions."""
        config = MCPServerConfig()
        assert config.is_table_allowed("users") is True
        assert config.is_table_allowed("any_table") is True

    def test_is_table_allowed_with_allowlist(self) -> None:
        """Test table access with allowlist."""
        config = MCPServerConfig(allowed_tables=("users", "orders"))
        assert config.is_table_allowed("users") is True
        assert config.is_table_allowed("orders") is True
        assert config.is_table_allowed("secrets") is False

    def test_is_table_allowed_with_denylist(self) -> None:
        """Test table access with denylist."""
        config = MCPServerConfig(denied_tables=("secrets", "passwords"))
        assert config.is_table_allowed("users") is True
        assert config.is_table_allowed("secrets") is False
        assert config.is_table_allowed("passwords") is False

    def test_is_table_allowed_denylist_takes_precedence(self) -> None:
        """Test that denylist takes precedence over allowlist."""
        config = MCPServerConfig(
            allowed_tables=("users", "secrets"),
            denied_tables=("secrets",),
        )
        assert config.is_table_allowed("users") is True
        assert config.is_table_allowed("secrets") is False

    def test_is_sqlite(self) -> None:
        """Test SQLite detection."""
        sqlite_config = MCPServerConfig(database_url="sqlite:///./test.db")
        assert sqlite_config.is_sqlite is True

        pg_config = MCPServerConfig(database_url="postgresql://localhost/db")
        assert pg_config.is_sqlite is False


class TestGetConfig:
    """Tests for get_config singleton."""

    def setup_method(self) -> None:
        """Reset config before each test."""
        reset_config()

    def teardown_method(self) -> None:
        """Reset config after each test."""
        reset_config()

    def test_get_config_singleton(self) -> None:
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self) -> None:
        """Test that reset_config clears the singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # After reset, new instance is created (but may have same values)
        assert config1 is not config2
