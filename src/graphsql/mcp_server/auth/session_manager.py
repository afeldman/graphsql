"""Session management for SSO-authenticated MCP connections.

This module manages user sessions and creates MCP server instances
with user-specific database configurations.

Example:
    >>> from graphsql.mcp_server.auth.session_manager import SessionManager
    >>> manager = SessionManager(config_store)
    >>> mcp_session = await manager.create_session(user_session)
    >>> # Use mcp_session.graphsql_engine for queries
    >>> await manager.close_session(user_session.user_id)
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, computed_field
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from graphsql.mcp_server.auth.sso import UserSession
from graphsql.mcp_server.auth.user_config import UserConfigStore, UserDatabaseConfig
from graphsql.mcp_server.config import MCPServerConfig
from graphsql.mcp_server.engine import GraphSQLEngine
from graphsql.mcp_server.security import SecurityValidator

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class MCPUserSession(BaseModel):
    """MCP session bound to an authenticated user.

    Contains all resources needed to execute queries for a specific user,
    including database connection and GraphSQL engine.

    Attributes:
        user_session: The authenticated user's session info.
        db_config: User's database configuration.
        engine: SQLAlchemy database engine.
        graphsql_engine: GraphSQL query engine.
        security: Security validator instance.
        created_at: Unix timestamp when session was created.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_session: UserSession
    db_config: UserDatabaseConfig
    engine: Engine
    graphsql_engine: GraphSQLEngine
    security: SecurityValidator
    created_at: float = Field(default_factory=time.time)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def age_seconds(self) -> float:
        """Get session age in seconds.

        Returns:
            Number of seconds since session creation.
        """
        return time.time() - self.created_at

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_valid(self) -> bool:
        """Check if session is still valid.

        Returns:
            True if user's OAuth token is still valid.
        """
        return self.user_session.is_valid

    async def close(self) -> None:
        """Close session resources.

        Disposes the database engine and releases connections.
        """
        try:
            self.engine.dispose()
            logger.debug(
                "Closed MCP user session and disposed database engine",
                user_id=self.user_session.user_id,
                email=self.user_session.email,
                session_age_seconds=int(time.time() - self.created_at),
            )
        except Exception as e:
            logger.error(
                "Error closing MCP user session",
                user_id=self.user_session.user_id,
                error=str(e),
            )


class SessionManager:
    """Manages user sessions and their MCP instances.

    Handles creation, retrieval, and cleanup of user-specific MCP sessions.
    Ensures each user has at most one active session.

    Attributes:
        config_store: Storage backend for user configurations.
        session_timeout: Maximum session lifetime in seconds.
        _sessions: Internal session storage.
        _lock: Async lock for thread-safe operations.
    """

    def __init__(
        self,
        config_store: UserConfigStore,
        session_timeout: int = 3600,
    ) -> None:
        """Initialize session manager.

        Args:
            config_store: Storage backend for user configurations.
            session_timeout: Maximum session lifetime in seconds.
        """
        self.config_store = config_store
        self.session_timeout = session_timeout
        self._sessions: dict[str, MCPUserSession] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def create_session(
        self,
        user_session: UserSession,
    ) -> MCPUserSession:
        """Create MCP session for authenticated user.

        If a valid session already exists, it is returned.
        If an expired session exists, it is closed and replaced.

        Args:
            user_session: Authenticated user session from SSO.

        Returns:
            MCPUserSession with user-specific configuration.

        Raises:
            ValueError: If no database configuration found for user.
            Exception: If database connection fails.
        """
        async with self._lock:
            # Check if session already exists
            if user_session.user_id in self._sessions:
                existing = self._sessions[user_session.user_id]
                if existing.is_valid:
                    logger.debug(
                        "Reusing existing valid session",
                        user_id=user_session.user_id,
                        email=user_session.email,
                        session_age_seconds=int(time.time() - existing.created_at),
                    )
                    return existing
                # Close expired session
                await existing.close()
                del self._sessions[user_session.user_id]

            # Get user's database config
            db_config = await self.config_store.get_config(user_session.user_id)
            if db_config is None:
                raise ValueError(
                    f"No database configuration found for user: {user_session.user_id}. "
                    "Please configure your database connection first."
                )

            logger.info(
                "Creating new MCP session for authenticated user",
                user_id=user_session.user_id,
                email=user_session.email,
                database_url=db_config.get_masked_url(),
                read_only=db_config.read_only,
                max_rows=db_config.max_rows,
                query_timeout=db_config.query_timeout,
            )

            # Create database engine with user's config
            logger.debug(
                "Creating SQLAlchemy database engine",
                user_id=user_session.user_id,
                pool_size=db_config.connection_pool_size,
                pool_pre_ping=True,
            )
            engine = create_engine(
                db_config.to_connection_string(),
                pool_size=db_config.connection_pool_size,
                pool_pre_ping=True,
                **db_config.extra_options,
            )

            # Test connection
            logger.debug(
                "Testing database connection",
                user_id=user_session.user_id,
                database_url=db_config.get_masked_url(),
            )
            try:
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                logger.debug(
                    "Database connection test successful",
                    user_id=user_session.user_id,
                )
            except Exception as e:
                logger.error(
                    "Database connection test failed",
                    user_id=user_session.user_id,
                    error=str(e),
                    database_url=db_config.get_masked_url(),
                )
                engine.dispose()
                raise ValueError(f"Failed to connect to database: {e}") from e

            # Create MCP config from user settings
            mcp_config = MCPServerConfig(
                database_url=db_config.database_url,
                read_only=db_config.read_only,
                max_rows=db_config.max_rows,
                query_timeout=db_config.query_timeout,
                allowed_tables=tuple(db_config.allowed_tables),
                denied_tables=tuple(db_config.blocked_tables),
            )

            # Create security validator
            security = SecurityValidator(mcp_config)

            # Create GraphSQL engine
            graphsql_engine = GraphSQLEngine(engine, mcp_config, security)

            # Create session
            session = MCPUserSession(
                user_session=user_session,
                db_config=db_config,
                engine=engine,
                graphsql_engine=graphsql_engine,
                security=security,
            )

            self._sessions[user_session.user_id] = session
            logger.info(
                "Successfully created MCP session with database connection",
                user_id=user_session.user_id,
                email=user_session.email,
                table_count=len(graphsql_engine.introspect_schema().tables),
                pool_size=db_config.connection_pool_size,
                session_timeout=self.session_timeout,
            )

            return session

    async def get_session(self, user_id: str) -> MCPUserSession | None:
        """Get existing session for user.

        Args:
            user_id: User identifier from SSO.

        Returns:
            MCPUserSession if exists and valid, None otherwise.
        """
        async with self._lock:
            session = self._sessions.get(user_id)
            if session and session.is_valid:
                return session
            return None

    async def close_session(self, user_id: str) -> bool:
        """Close and remove user session.

        Args:
            user_id: User identifier from SSO.

        Returns:
            True if session was closed, False if not found.
        """
        async with self._lock:
            session = self._sessions.pop(user_id, None)
            if session:
                await session.close()
                logger.info(
                    "Closed and removed MCP session",
                    user_id=user_id,
                    email=session.user_session.email,
                    session_duration_seconds=int(time.time() - session.created_at),
                )
                return True
            return False

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions.

        Removes sessions where the OAuth token has expired or
        the session has exceeded the timeout.

        Returns:
            Number of sessions cleaned up.
        """
        async with self._lock:
            expired = []
            now = time.time()

            for user_id, session in self._sessions.items():
                if not session.is_valid:
                    expired.append(user_id)
                elif now - session.created_at > self.session_timeout:
                    expired.append(user_id)

            for user_id in expired:
                session = self._sessions.pop(user_id)
                await session.close()

            if expired:
                logger.info(
                    "Cleaned up expired sessions",
                    expired_count=len(expired),
                    remaining_sessions=len(self._sessions),
                    session_timeout=self.session_timeout,
                )

            return len(expired)

    async def close_all(self) -> None:
        """Close all sessions.

        Should be called during shutdown.
        """
        async with self._lock:
            for session in self._sessions.values():
                await session.close()
            count = len(self._sessions)
            self._sessions.clear()
            logger.info(
                "Closed all MCP sessions during shutdown",
                closed_count=count,
            )

    @property
    def active_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of active sessions.
        """
        return len(self._sessions)

    def get_stats(self) -> dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with session statistics.
        """
        return {
            "active_sessions": self.active_count,
            "session_timeout": self.session_timeout,
            "users": list(self._sessions.keys()),
        }


class MCPSessionFactory:
    """Factory for creating user-scoped MCP servers.

    Creates FastMCP instances pre-configured with user-specific
    database connections and tools.

    Attributes:
        session_manager: Session manager for user sessions.
        base_config: Base configuration for all MCP instances.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        base_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize factory.

        Args:
            session_manager: Session manager for user sessions.
            base_config: Base configuration for all MCP instances.
        """
        self.session_manager = session_manager
        self.base_config = base_config or {}

    async def create_mcp_for_user(
        self,
        user_session: UserSession,
    ) -> FastMCP:
        """Create MCP server instance for authenticated user.

        Args:
            user_session: Authenticated user session from SSO.

        Returns:
            FastMCP instance configured for the user.

        Raises:
            ValueError: If user has no database configuration.
        """
        from mcp.server.fastmcp import FastMCP

        from graphsql.mcp_server.tools import MCPTools

        # Get or create user's MCP session
        mcp_session = await self.session_manager.create_session(user_session)

        # Create FastMCP instance with user context
        mcp = FastMCP(
            name=f"graphsql-{user_session.user_id[:8]}",
            **self.base_config,
        )

        # Create tools instance with user's engine
        _tools = MCPTools(mcp_session.graphsql_engine)

        return mcp

    def get_user_context(self, user_session: UserSession) -> dict[str, Any]:
        """Get context information for user.

        Useful for logging and auditing.

        Args:
            user_session: Authenticated user session.

        Returns:
            Dictionary with user context information.
        """
        return {
            "user_id": user_session.user_id,
            "email": user_session.email,
            "name": user_session.name,
            "groups": user_session.groups,
            "roles": user_session.roles,
        }


async def start_cleanup_task(
    session_manager: SessionManager,
    interval: int = 300,
) -> asyncio.Task:
    """Start background task to clean up expired sessions.

    Args:
        session_manager: Session manager to clean up.
        interval: Cleanup interval in seconds (default: 5 minutes).

    Returns:
        Background task that can be cancelled.
    """

    async def cleanup_loop() -> None:
        while True:
            await asyncio.sleep(interval)
            try:
                await session_manager.cleanup_expired()
            except Exception as e:
                logger.error(
                    "Error in session cleanup task",
                    error=str(e),
                )

    task = asyncio.create_task(cleanup_loop())
    logger.info(
        "Started background session cleanup task",
        interval_seconds=interval,
    )
    return task
