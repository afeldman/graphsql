"""SSO Auth Proxy - HTTP server that handles SSO and spawns MCP sessions.

This module provides a FastAPI-based HTTP server that handles SSO authentication
and manages MCP sessions for authenticated users.

Example:
    >>> from graphsql.mcp_server.auth.proxy import create_auth_proxy, AuthProxyConfig
    >>> config = AuthProxyConfig(sso=sso_config, encryption_key="...")
    >>> app = create_auth_proxy(config)
    >>> # Run with uvicorn: uvicorn app:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import asyncio
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger
from pydantic import BaseModel, Field

from graphsql.mcp_server.auth.session_manager import (
    MCPSessionFactory,
    SessionManager,
    start_cleanup_task,
)
from graphsql.mcp_server.auth.sso import SSOAuthenticator, SSOConfig, UserSession
from graphsql.mcp_server.auth.user_config import (
    EncryptionKey,
    FileConfigStore,
    InMemoryConfigStore,
    UserConfigStore,
    UserDatabaseConfig,
)


class AuthProxyConfig(BaseModel):
    """Configuration for the auth proxy server.

    Attributes:
        sso: SSO provider configuration.
        encryption_key: Key for encrypting stored configurations.
        config_store_path: Path for file-based config storage.
        config_store_type: Type of config store ("file", "memory", "redis").
        redis_url: Redis URL for redis config store.
        session_timeout: Session timeout in seconds.
        cleanup_interval: Cleanup task interval in seconds.
        host: Host to bind to.
        port: Port to bind to.
        cors_origins: Allowed CORS origins.
    """

    sso: SSOConfig
    encryption_key: str = Field(description="Encryption key for stored configs")
    config_store_path: str = Field(default="./user_configs")
    config_store_type: str = Field(default="file")
    redis_url: str | None = Field(default=None)
    session_timeout: int = Field(default=3600)
    cleanup_interval: int = Field(default=300)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class AuthState:
    """Global authentication state container.

    Manages pending OAuth states and active user sessions.

    Attributes:
        pending_states: Mapping of state tokens to creation times.
        user_sessions: Mapping of session IDs to user sessions.
        state_timeout: State expiration time in seconds.
    """

    def __init__(self, state_timeout: int = 600) -> None:
        """Initialize auth state.

        Args:
            state_timeout: State expiration time in seconds.
        """
        self.pending_states: dict[str, float] = {}
        self.user_sessions: dict[str, UserSession] = {}
        self.state_timeout = state_timeout
        self._lock = asyncio.Lock()

    async def create_state(self) -> str:
        """Create new OAuth state parameter.

        Returns:
            Random state token.
        """
        async with self._lock:
            state = secrets.token_urlsafe(32)
            self.pending_states[state] = time.time()
            return state

    async def validate_state(self, state: str) -> bool:
        """Validate and consume OAuth state.

        Args:
            state: State token from OAuth callback.

        Returns:
            True if state is valid and not expired.
        """
        async with self._lock:
            if state not in self.pending_states:
                return False

            created_at = self.pending_states.pop(state)
            return time.time() - created_at < self.state_timeout

    async def create_session(self, user: UserSession) -> str:
        """Create session for authenticated user.

        Args:
            user: Authenticated user session.

        Returns:
            Session ID for cookie.
        """
        async with self._lock:
            session_id = secrets.token_urlsafe(32)
            self.user_sessions[session_id] = user
            return session_id

    async def get_user(self, session_id: str) -> UserSession | None:
        """Get user from session ID.

        Args:
            session_id: Session ID from cookie.

        Returns:
            User session if valid, None otherwise.
        """
        async with self._lock:
            user = self.user_sessions.get(session_id)
            if user and user.is_valid:
                return user
            return None

    async def destroy_session(self, session_id: str) -> None:
        """Destroy user session.

        Args:
            session_id: Session ID to destroy.
        """
        async with self._lock:
            self.user_sessions.pop(session_id, None)

    async def cleanup_expired(self) -> int:
        """Clean up expired states and sessions.

        Returns:
            Number of items cleaned up.
        """
        async with self._lock:
            now = time.time()
            count = 0

            # Clean expired states
            expired_states = [
                s
                for s, t in self.pending_states.items()
                if now - t > self.state_timeout
            ]
            for state in expired_states:
                del self.pending_states[state]
                count += 1

            # Clean expired sessions
            expired_sessions = [
                sid for sid, user in self.user_sessions.items() if not user.is_valid
            ]
            for sid in expired_sessions:
                del self.user_sessions[sid]
                count += 1

            return count


def create_config_store(config: AuthProxyConfig) -> UserConfigStore:
    """Create config store based on configuration.

    Args:
        config: Auth proxy configuration.

    Returns:
        Configured UserConfigStore instance.
    """
    encryption_key = EncryptionKey.from_string(config.encryption_key)

    if config.config_store_type == "memory":
        return InMemoryConfigStore()

    if config.config_store_type == "redis" and config.redis_url:
        from graphsql.mcp_server.auth.user_config import RedisConfigStore

        return RedisConfigStore(
            redis_url=config.redis_url,
            encryption_key=encryption_key,
        )

    # Default to file store
    return FileConfigStore(
        base_path=Path(config.config_store_path),
        encryption_key=encryption_key,
    )


def create_auth_proxy(config: AuthProxyConfig) -> FastAPI:
    """Create FastAPI auth proxy application.

    Args:
        config: Auth proxy configuration.

    Returns:
        Configured FastAPI application.
    """
    # Initialize components
    config_store = create_config_store(config)
    session_manager = SessionManager(
        config_store=config_store,
        session_timeout=config.session_timeout,
    )
    mcp_factory = MCPSessionFactory(session_manager)
    auth_state = AuthState()
    cleanup_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        """Application lifespan handler."""
        nonlocal cleanup_task
        logger.info(
            "Starting GraphSQL Auth Proxy server",
            sso_provider=config.sso.provider.value,
            config_store_type=config.config_store_type,
            session_timeout=config.session_timeout,
            cleanup_interval=config.cleanup_interval,
        )

        # Start cleanup task
        cleanup_task = await start_cleanup_task(
            session_manager, config.cleanup_interval
        )

        yield

        # Shutdown
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        await session_manager.close_all()
        logger.info(
            "Auth Proxy shutdown complete",
            final_session_count=session_manager.active_count,
        )

    app = FastAPI(
        title="GraphSQL MCP Auth Proxy",
        description="SSO-authenticated MCP server access for GraphSQL",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware if needed
    if config.cors_origins:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        """Log all incoming requests."""
        start_time = time.time()

        # Log request
        logger.debug(
            "Incoming HTTP request",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")[:50],
        )

        response = await call_next(request)

        # Log response
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "HTTP request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response

    # Dependency for SSO authenticator
    async def get_authenticator() -> SSOAuthenticator:
        """Get SSO authenticator."""
        auth = SSOAuthenticator(config.sso)
        return auth

    # Dependency for current user
    async def get_current_user(request: Request) -> UserSession:
        """Get current authenticated user from session."""
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        user = await auth_state.get_user(session_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired",
            )

        return user

    # Optional user dependency
    async def get_optional_user(request: Request) -> UserSession | None:
        """Get current user if authenticated."""
        session_id = request.cookies.get("session_id")
        if session_id:
            return await auth_state.get_user(session_id)
        return None

    # Routes
    @app.get("/")
    async def root(user: UserSession | None = Depends(get_optional_user)) -> dict:
        """Root endpoint with service info."""
        return {
            "service": "GraphSQL MCP Auth Proxy",
            "version": "1.0.0",
            "status": "running",
            "authenticated": user is not None,
            "endpoints": {
                "login": "/login",
                "callback": "/callback",
                "dashboard": "/dashboard",
                "config": "/config",
                "connect": "/mcp/connect",
                "health": "/health",
            },
        }

    @app.get("/login")
    async def login(
        auth: SSOAuthenticator = Depends(get_authenticator),
    ) -> RedirectResponse:
        """Initiate SSO login flow.

        Redirects user to SSO provider's login page.
        """
        state = await auth_state.create_state()
        login_url = auth.get_login_url(state)
        logger.info(
            "Initiating SSO login flow",
            state_prefix=state[:8],
            provider=config.sso.provider.value,
            redirect_uri=config.sso.redirect_uri,
        )
        return RedirectResponse(url=login_url)

    @app.get("/callback")
    async def callback(
        code: str,
        state: str,
        auth: SSOAuthenticator = Depends(get_authenticator),
    ) -> RedirectResponse:
        """Handle SSO callback.

        Exchanges authorization code for tokens and creates user session.
        """
        # Validate state
        if not await auth_state.validate_state(state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter",
            )

        # Exchange code for user session
        try:
            async with auth:
                user_session = await auth.authenticate(code)
        except Exception as e:
            logger.error(
                "SSO authentication failed during code exchange",
                error=str(e),
                state_prefix=state[:8],
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {e}",
            ) from e

        # Create session ID
        session_id = await auth_state.create_session(user_session)
        logger.info(
            "User successfully authenticated via SSO",
            user_id=user_session.user_id,
            email=user_session.email,
            name=user_session.name,
            groups_count=len(user_session.groups),
            roles_count=len(user_session.roles),
        )

        # Redirect to dashboard with session cookie
        response = RedirectResponse(url="/dashboard")
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=config.session_timeout,
        )
        return response

    @app.get("/dashboard")
    async def dashboard(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, Any]:
        """User dashboard after login.

        Shows user info and database configuration status.
        """
        db_config = await config_store.get_config(user.user_id)
        return {
            "user": {
                "id": user.user_id,
                "email": user.email,
                "name": user.name,
                "groups": user.groups,
                "roles": user.roles,
            },
            "database_configured": db_config is not None,
            "database_url": db_config.get_masked_url() if db_config else None,
            "mcp_endpoint": "/mcp/connect",
        }

    @app.post("/config")
    async def save_database_config(
        db_config: UserDatabaseConfig,
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, str]:
        """Save user's database configuration.

        The user_id in the config is automatically set to the authenticated user.
        """
        # Ensure user_id matches authenticated user
        db_config.user_id = user.user_id
        await config_store.save_config(user.user_id, db_config)
        logger.info(
            "Saved user database configuration",
            user_id=user.user_id,
            email=user.email,
            database_url=db_config.get_masked_url(),
            read_only=db_config.read_only,
            max_rows=db_config.max_rows,
        )
        return {"status": "saved", "user_id": user.user_id}

    @app.get("/config")
    async def get_database_config(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Get user's database configuration."""
        db_config = await config_store.get_config(user.user_id)
        if db_config is None:
            return {"status": "not_configured", "message": "Please configure your database connection"}

        # Return config with masked URL
        return {
            "status": "configured",
            "database_url": db_config.get_masked_url(),
            "database_name": db_config.database_name,
            "schema_name": db_config.schema_name,
            "read_only": db_config.read_only,
            "max_rows": db_config.max_rows,
            "query_timeout": db_config.query_timeout,
            "allowed_tables": db_config.allowed_tables,
            "blocked_tables": db_config.blocked_tables,
        }

    @app.delete("/config")
    async def delete_database_config(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, str]:
        """Delete user's database configuration."""
        await config_store.delete_config(user.user_id)
        await session_manager.close_session(user.user_id)
        logger.info(
            "Deleted user database configuration and closed session",
            user_id=user.user_id,
            email=user.email,
        )
        return {"status": "deleted", "user_id": user.user_id}

    @app.post("/mcp/connect")
    async def connect_mcp(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Create MCP connection for authenticated user.

        Returns connection details and available tools.
        """
        try:
            mcp = await mcp_factory.create_mcp_for_user(user)
            tools = mcp._tool_manager.list_tools() if hasattr(mcp, "_tool_manager") else []
            return {
                "status": "connected",
                "user": user.email,
                "mcp_name": mcp.name,
                "tools": [tool.name for tool in tools] if tools else ["sql_query", "graphql_query", "schema_introspect", "health_check"],
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except Exception as e:
            logger.error(
                "MCP connection failed unexpectedly",
                user_id=user.user_id,
                email=user.email,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create MCP connection: {e}",
            ) from e

    @app.get("/mcp/session")
    async def get_mcp_session(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Get current MCP session status."""
        session = await session_manager.get_session(user.user_id)
        if session:
            return {
                "status": "active",
                "user": user.email,
                "age_seconds": session.age_seconds,
                "database_url": session.db_config.get_masked_url(),
            }
        return {"status": "not_connected", "message": "No active MCP session"}

    @app.delete("/mcp/session")
    async def close_mcp_session(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, str]:
        """Close current MCP session."""
        closed = await session_manager.close_session(user.user_id)
        if closed:
            return {"status": "closed", "user_id": user.user_id}
        return {"status": "not_found", "message": "No active session"}

    @app.post("/logout")
    async def logout(
        request: Request,
        user: UserSession = Depends(get_current_user),
    ) -> JSONResponse:
        """Logout and cleanup session."""
        session_id = request.cookies.get("session_id")
        if session_id:
            await auth_state.destroy_session(session_id)

        await session_manager.close_session(user.user_id)
        logger.info(
            "User logged out successfully",
            user_id=user.user_id,
            email=user.email,
        )

        response = JSONResponse({"status": "logged_out"})
        response.delete_cookie("session_id")
        return response

    @app.get("/health")
    async def health() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "active_sessions": session_manager.active_count,
            "pending_states": len(auth_state.pending_states),
            "sso_provider": config.sso.provider.value,
        }

    @app.get("/stats")
    async def stats(
        user: UserSession = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Get proxy statistics (requires authentication)."""
        return {
            "session_stats": session_manager.get_stats(),
            "config_users": await config_store.list_users(),
        }

    return app


def run_auth_proxy(config: AuthProxyConfig) -> None:
    """Run the auth proxy server.

    Args:
        config: Auth proxy configuration.
    """
    import uvicorn

    app = create_auth_proxy(config)
    uvicorn.run(app, host=config.host, port=config.port)
