"""Authentication module for GraphSQL MCP Server.

This module provides SSO-based authentication for the MCP server,
allowing users to authenticate via OAuth providers and automatically
load their database configurations.

Example:
    Start the auth proxy server::

        graphsql-auth --mode proxy --port 8080

    Or run standalone without SSO::

        graphsql-auth --mode standalone
"""

from graphsql.mcp_server.auth.logging_config import (
    add_context,
    configure_logging,
    log_exception,
    log_timing,
)
from graphsql.mcp_server.auth.session_manager import (
    MCPSessionFactory,
    MCPUserSession,
    SessionManager,
)
from graphsql.mcp_server.auth.sso import (
    OAuthToken,
    SSOAuthenticator,
    SSOConfig,
    SSOProvider,
    UserSession,
)
from graphsql.mcp_server.auth.user_config import (
    EncryptionKey,
    FileConfigStore,
    InMemoryConfigStore,
    UserConfigStore,
    UserDatabaseConfig,
)

__all__ = [
    # SSO
    "SSOConfig",
    "SSOProvider",
    "OAuthToken",
    "UserSession",
    "SSOAuthenticator",
    # User Config
    "UserDatabaseConfig",
    "UserConfigStore",
    "FileConfigStore",
    "InMemoryConfigStore",
    "EncryptionKey",
    # Session Management
    "SessionManager",
    "MCPUserSession",
    "MCPSessionFactory",
    # Logging
    "configure_logging",
    "add_context",
    "log_exception",
    "log_timing",
]
