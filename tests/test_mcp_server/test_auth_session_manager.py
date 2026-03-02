"""Tests for session manager module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from graphsql.mcp_server.auth.session_manager import (
    MCPSessionFactory,
    MCPUserSession,
    SessionManager,
)
from graphsql.mcp_server.auth.sso import OAuthToken, UserSession
from graphsql.mcp_server.auth.user_config import (
    InMemoryConfigStore,
    UserDatabaseConfig,
)


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.fixture
    def config_store(self) -> InMemoryConfigStore:
        """Create config store fixture."""
        return InMemoryConfigStore()

    @pytest.fixture
    def session_manager(
        self, config_store: InMemoryConfigStore
    ) -> SessionManager:
        """Create session manager fixture."""
        return SessionManager(
            config_store=config_store,
            session_timeout=3600,
        )

    def _create_user_session(
        self, user_id: str = "user123", expires_in: int = 3600
    ) -> UserSession:
        """Helper to create a user session."""
        token = OAuthToken(
            access_token="test-token",
            token_type="Bearer",
            expires_in=expires_in,
        )
        return UserSession(
            user_id=user_id,
            email=f"{user_id}@example.com",
            name=f"User {user_id}",
            token=token,
        )

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(
        self, session_manager: SessionManager
    ) -> None:
        """Test retrieving a session that doesn't exist."""
        result = await session_manager.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(
        self, session_manager: SessionManager
    ) -> None:
        """Test closing a session that doesn't exist."""
        result = await session_manager.close_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_active_count_empty(
        self, session_manager: SessionManager
    ) -> None:
        """Test active count with no sessions."""
        assert session_manager.active_count == 0

    @pytest.mark.asyncio
    async def test_get_stats(
        self, session_manager: SessionManager
    ) -> None:
        """Test getting stats."""
        stats = session_manager.get_stats()
        assert "active_sessions" in stats
        assert "session_timeout" in stats
        assert stats["active_sessions"] == 0

    @pytest.mark.asyncio
    async def test_create_session_without_config(
        self, session_manager: SessionManager
    ) -> None:
        """Test creating session without existing config fails."""
        user_session = self._create_user_session("no-config-user")
        
        with pytest.raises(ValueError, match="No database configuration found"):
            await session_manager.create_session(user_session)

    @pytest.mark.asyncio
    async def test_close_all_empty(
        self, session_manager: SessionManager
    ) -> None:
        """Test closing all sessions when empty."""
        await session_manager.close_all()
        assert session_manager.active_count == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_empty(
        self, session_manager: SessionManager
    ) -> None:
        """Test cleanup with no sessions."""
        count = await session_manager.cleanup_expired()
        assert count == 0


class TestMCPSessionFactory:
    """Tests for MCPSessionFactory class."""

    @pytest.fixture
    def config_store(self) -> InMemoryConfigStore:
        """Create config store fixture."""
        return InMemoryConfigStore()

    @pytest.fixture
    def session_manager(
        self, config_store: InMemoryConfigStore
    ) -> SessionManager:
        """Create session manager fixture."""
        return SessionManager(config_store=config_store)

    @pytest.fixture
    def factory(self, session_manager: SessionManager) -> MCPSessionFactory:
        """Create factory fixture."""
        return MCPSessionFactory(session_manager)

    def test_factory_creation(self, factory: MCPSessionFactory) -> None:
        """Test factory is created correctly."""
        assert factory.session_manager is not None
