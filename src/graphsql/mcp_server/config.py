"""Configuration management for the MCP server.

This module provides environment-based configuration using python-dotenv
and pydantic for validation. All settings can be overridden via environment
variables or a .env file.

Environment Variables:
    DATABASE_URL: SQLAlchemy database connection string
    MCP_SERVER_NAME: Name of the MCP server (default: graphsql)
    MAX_ROWS: Maximum number of rows returned per query (default: 1000)
    QUERY_TIMEOUT: Query execution timeout in seconds (default: 30)
    READ_ONLY: Enable read-only mode (default: false)
    LOG_LEVEL: Logging level (default: INFO)
    ENABLE_AUTH: Enable authentication (default: false)
    AUTH_METHOD: Authentication method (none, api_key, oauth)
    API_KEY: API key for authentication
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load .env file from current directory or parent directories
_env_path = Path.cwd() / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Try to find .env in parent directory
    load_dotenv()


def _get_bool(key: str, default: bool = False) -> bool:
    """Parse boolean environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Parsed boolean value.
    """
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_int(key: str, default: int) -> int:
    """Parse integer environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Parsed integer value.
    """
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_list(key: str, default: list[str] | None = None) -> list[str]:
    """Parse comma-separated list environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Parsed list of strings.
    """
    if default is None:
        default = []
    value = os.getenv(key, "")
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True, slots=True)
class MCPServerConfig:
    """Configuration container for the MCP server.

    This dataclass holds all configuration settings and provides
    validation and type safety. Configuration is loaded from environment
    variables at instantiation time.

    Attributes:
        database_url: SQLAlchemy database connection string.
        server_name: Name of the MCP server.
        max_rows: Maximum number of rows returned per query.
        query_timeout: Query execution timeout in seconds.
        read_only: Enable read-only mode.
        log_level: Logging level.
        enable_auth: Enable authentication.
        auth_method: Authentication method (none, api_key, oauth).
        api_key: API key for authentication.
        oauth_issuer: OAuth issuer URL.
        oauth_audience: OAuth audience.
        allowed_tables: Whitelist of allowed tables (empty = all).
        denied_tables: Blacklist of denied tables.
        pool_size: Database connection pool size.
        pool_max_overflow: Maximum pool overflow connections.
        pool_timeout: Pool connection timeout.
        pool_recycle: Pool connection recycle time.

    Example:
        >>> config = MCPServerConfig.from_env()
        >>> config.database_url
        'sqlite:///./database.db'
        >>> config.max_rows
        1000
    """

    # Database settings
    database_url: str = "sqlite:///./database.db"

    # MCP server settings
    server_name: str = "graphsql"
    server_version: str = "0.1.0"

    # Query limits
    max_rows: int = 1000
    query_timeout: int = 30
    read_only: bool = False

    # Logging
    log_level: str = "INFO"

    # Authentication (future extension)
    enable_auth: bool = False
    auth_method: Literal["none", "api_key", "oauth"] = "none"
    api_key: str = ""
    oauth_issuer: str = ""
    oauth_audience: str = ""

    # Table access control
    allowed_tables: tuple[str, ...] = field(default_factory=tuple)
    denied_tables: tuple[str, ...] = field(default_factory=tuple)

    # Connection pool settings
    pool_size: int = 5
    pool_max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

    @classmethod
    def from_env(cls) -> MCPServerConfig:
        """Create configuration from environment variables.

        Returns:
            MCPServerConfig instance populated from environment.

        Example:
            >>> import os
            >>> os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
            >>> config = MCPServerConfig.from_env()
            >>> config.database_url
            'postgresql://user:pass@localhost/db'
        """
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./database.db"),
            server_name=os.getenv("MCP_SERVER_NAME", "graphsql"),
            server_version=os.getenv("MCP_SERVER_VERSION", "0.1.0"),
            max_rows=_get_int("MAX_ROWS", 1000),
            query_timeout=_get_int("QUERY_TIMEOUT", 30),
            read_only=_get_bool("READ_ONLY", False),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            enable_auth=_get_bool("ENABLE_AUTH", False),
            auth_method=os.getenv("AUTH_METHOD", "none"),  # type: ignore[arg-type]
            api_key=os.getenv("API_KEY", ""),
            oauth_issuer=os.getenv("OAUTH_ISSUER", ""),
            oauth_audience=os.getenv("OAUTH_AUDIENCE", ""),
            allowed_tables=tuple(_get_list("ALLOWED_TABLES")),
            denied_tables=tuple(_get_list("DENIED_TABLES")),
            pool_size=_get_int("POOL_SIZE", 5),
            pool_max_overflow=_get_int("POOL_MAX_OVERFLOW", 10),
            pool_timeout=_get_int("POOL_TIMEOUT", 30),
            pool_recycle=_get_int("POOL_RECYCLE", 3600),
        )

    def is_table_allowed(self, table_name: str) -> bool:
        """Check if a table is allowed according to access control settings.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if table access is allowed, False otherwise.

        Example:
            >>> config = MCPServerConfig(allowed_tables=("users", "orders"))
            >>> config.is_table_allowed("users")
            True
            >>> config.is_table_allowed("secrets")
            False
        """
        # Check deny list first
        if self.denied_tables and table_name in self.denied_tables:
            return False

        # If allow list is set, table must be in it
        if self.allowed_tables:
            return table_name in self.allowed_tables

        # Default: allow all
        return True

    @property
    def is_sqlite(self) -> bool:
        """Check if the database is SQLite.

        Returns:
            True if using SQLite, False otherwise.
        """
        return self.database_url.startswith("sqlite")


# Global configuration instance (lazy-loaded)
_config: MCPServerConfig | None = None


def get_config() -> MCPServerConfig:
    """Get the global configuration instance.

    Returns:
        MCPServerConfig instance (singleton).

    Example:
        >>> config = get_config()
        >>> config.server_name
        'graphsql'
    """
    global _config
    if _config is None:
        _config = MCPServerConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance.

    Useful for testing or reloading configuration.
    """
    global _config
    _config = None
