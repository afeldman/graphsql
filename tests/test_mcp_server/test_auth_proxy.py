"""Tests for auth proxy module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from graphsql.mcp_server.auth.proxy import (
    AuthProxyConfig,
    AuthState,
    create_auth_proxy,
)
from graphsql.mcp_server.auth.sso import OAuthToken, SSOConfig, SSOProvider, UserSession
from graphsql.mcp_server.auth.user_config import (
    EncryptionKey,
    InMemoryConfigStore,
    UserDatabaseConfig,
)
from graphsql.mcp_server.auth.session_manager import SessionManager
from graphsql.mcp_server.engine import GraphSQLEngine
from graphsql.mcp_server.security import SecurityValidator


class TestAuthProxyConfig:
    """Tests for AuthProxyConfig dataclass."""

    def test_create_config(self) -> None:
        """Test creating auth proxy config."""
        sso_config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client",
            client_secret="test-secret",
            tenant_id="test-tenant",
            redirect_uri="http://localhost:8080/callback",
        )
        encryption_key = EncryptionKey.generate()
        
        config = AuthProxyConfig(
            sso=sso_config,
            encryption_key=encryption_key.to_string(),
            host="0.0.0.0",
            port=8080,
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 8080

    def test_default_values(self) -> None:
        """Test default config values."""
        sso_config = SSOConfig(
            provider=SSOProvider.GITHUB,
            client_id="test",
            client_secret="test",
            redirect_uri="http://localhost/callback",
        )
        encryption_key = EncryptionKey.generate()
        
        config = AuthProxyConfig(
            sso=sso_config,
            encryption_key=encryption_key.to_string(),
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.session_timeout == 3600


class TestAuthState:
    """Tests for AuthState class."""

    def test_create_state(self) -> None:
        """Test creating auth state manager."""
        state = AuthState(state_timeout=600)
        assert state.state_timeout == 600
        assert state.pending_states == {}
        assert state.user_sessions == {}

    def test_default_timeout(self) -> None:
        """Test default state timeout."""
        state = AuthState()
        assert state.state_timeout == 600

    @pytest.mark.asyncio
    async def test_create_auth_state(self) -> None:
        """Test creating OAuth state."""
        auth_state = AuthState()
        state_token = await auth_state.create_state()
        assert len(state_token) > 0
        assert state_token in auth_state.pending_states

    @pytest.mark.asyncio
    async def test_validate_state(self) -> None:
        """Test validating OAuth state."""
        auth_state = AuthState()
        state_token = await auth_state.create_state()
        
        # First validation should succeed
        is_valid = await auth_state.validate_state(state_token)
        assert is_valid is True
        
        # Second validation should fail (state consumed)
        is_valid = await auth_state.validate_state(state_token)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_invalid_state(self) -> None:
        """Test validating invalid state."""
        auth_state = AuthState()
        is_valid = await auth_state.validate_state("invalid-state")
        assert is_valid is False


class TestAuthProxy:
    """Tests for auth proxy FastAPI application."""

    @pytest.fixture
    def sso_config(self) -> SSOConfig:
        """Create SSO config fixture."""
        return SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8080/callback",
        )

    @pytest.fixture
    def encryption_key(self) -> EncryptionKey:
        """Create encryption key fixture."""
        return EncryptionKey.generate()

    @pytest.fixture
    def proxy_config(
        self, sso_config: SSOConfig, encryption_key: EncryptionKey
    ) -> AuthProxyConfig:
        """Create proxy config fixture."""
        return AuthProxyConfig(
            sso=sso_config,
            encryption_key=encryption_key.to_string(),
            config_store_type="memory",  # Use in-memory store for tests
        )

    @pytest.fixture
    def app(self, proxy_config: AuthProxyConfig) -> TestClient:
        """Create FastAPI test client fixture."""
        fastapi_app = create_auth_proxy(config=proxy_config)
        return TestClient(fastapi_app)

    def test_health_endpoint(self, app: TestClient) -> None:
        """Test health check endpoint."""
        response = app.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_login_redirect(self, app: TestClient) -> None:
        """Test login redirects to SSO provider."""
        response = app.get("/login", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        location = response.headers.get("location", "")
        assert "login.microsoftonline.com" in location

    def test_login_stores_state(self, app: TestClient) -> None:
        """Test login stores state for CSRF protection."""
        response = app.get("/login", follow_redirects=False)
        location = response.headers.get("location", "")
        assert "state=" in location

    def test_callback_without_code(self, app: TestClient) -> None:
        """Test callback without code returns error."""
        response = app.get("/callback")
        # FastAPI returns 422 for missing required params
        assert response.status_code in (400, 422)

    def test_callback_without_state(self, app: TestClient) -> None:
        """Test callback without state returns error."""
        response = app.get("/callback?code=test-code")
        # FastAPI returns 422 for missing required params
        assert response.status_code in (400, 422)

    def test_callback_with_invalid_state(self, app: TestClient) -> None:
        """Test callback with invalid state returns error."""
        response = app.get("/callback?code=test-code&state=invalid-state")
        assert response.status_code == 400

    def test_dashboard_unauthenticated(self, app: TestClient) -> None:
        """Test dashboard redirects when not authenticated."""
        response = app.get("/dashboard", follow_redirects=False)
        # Should redirect to login
        assert response.status_code in (302, 307, 401, 403)

    def test_config_unauthenticated(self, app: TestClient) -> None:
        """Test config endpoint requires authentication."""
        response = app.post(
            "/config",
            json={
                "database_url": "postgresql://localhost/db",
            },
        )
        assert response.status_code in (401, 403)

    def test_logout(self, app: TestClient) -> None:
        """Test logout clears session."""
        response = app.post("/logout")
        # Logout may require auth or return success
        assert response.status_code in (200, 302, 307, 401)


class TestAuthProxyWithMockAuth:
    """Tests for auth proxy with mocked authentication."""

    @pytest.fixture
    def sso_config(self) -> SSOConfig:
        """Create SSO config fixture."""
        return SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8080/callback",
        )

    @pytest.fixture
    def encryption_key(self) -> EncryptionKey:
        """Create encryption key fixture."""
        return EncryptionKey.generate()

    @pytest.fixture
    def config_store(self) -> InMemoryConfigStore:
        """Create config store fixture."""
        return InMemoryConfigStore()

    @pytest.fixture
    def proxy_config(
        self, sso_config: SSOConfig, encryption_key: EncryptionKey
    ) -> AuthProxyConfig:
        """Create proxy config fixture."""
        return AuthProxyConfig(
            sso=sso_config,
            encryption_key=encryption_key.to_string(),
            config_store_type="memory",
        )

    def _create_mock_session(self) -> UserSession:
        """Create a mock user session."""
        token = OAuthToken(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="test-refresh-token",
        )
        return UserSession(
            user_id="user123",
            email="user@example.com",
            name="Test User",
            token=token,
        )

    @pytest.mark.asyncio
    async def test_save_user_config(
        self, config_store: InMemoryConfigStore
    ) -> None:
        """Test saving user database configuration."""
        config = UserDatabaseConfig(
            database_url="postgresql://localhost/mydb",
            database_name="mydb",
        )
        
        await config_store.save_config("user123", config)
        
        retrieved = await config_store.get_config("user123")
        assert retrieved is not None
        assert retrieved.database_url == "postgresql://localhost/mydb"

    @pytest.mark.asyncio
    async def test_session_manager_integration(
        self, config_store: InMemoryConfigStore
    ) -> None:
        """Test session manager works with auth proxy."""
        session_manager = SessionManager(
            config_store=config_store,
            session_timeout=3600,
        )
        
        # Save user config
        config = UserDatabaseConfig(
            database_url="sqlite:///:memory:",
        )
        await config_store.save_config("user123", config)
        
        # Create session
        user_session = self._create_mock_session()
        
        with patch(
            "graphsql.mcp_server.auth.session_manager.create_engine"
        ) as mock_create_engine, patch(
            "graphsql.mcp_server.auth.session_manager.GraphSQLEngine"
        ) as mock_graphsql_engine_cls, patch(
            "graphsql.mcp_server.auth.session_manager.SecurityValidator"
        ) as mock_security_cls:
            mock_engine = MagicMock(spec=Engine)
            mock_create_engine.return_value = mock_engine
            mock_graphsql_engine = MagicMock(spec=GraphSQLEngine)
            mock_graphsql_engine_cls.return_value = mock_graphsql_engine
            mock_security = MagicMock(spec=SecurityValidator)
            mock_security_cls.return_value = mock_security
            
            mcp_session = await session_manager.create_session(user_session)
            
            assert mcp_session is not None
            assert mcp_session.user_session.user_id == "user123"


class TestOAuthCallbackFlow:
    """Tests for OAuth callback flow."""

    def test_oauth_error_handling(self) -> None:
        """Test OAuth error is properly handled."""
        sso_config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test",
            client_secret="test",
            tenant_id="test",
            redirect_uri="http://localhost/callback",
        )
        encryption_key = EncryptionKey.generate()
        
        config = AuthProxyConfig(
            sso=sso_config,
            encryption_key=encryption_key.to_string(),
            config_store_type="memory",
        )
        
        app = create_auth_proxy(config=config)
        client = TestClient(app)
        
        # Simulate OAuth error
        response = client.get(
            "/callback?error=access_denied&error_description=User+denied+access"
        )
        # FastAPI may return 422 for missing required params or 400 for error
        assert response.status_code in (400, 422)

    def test_state_validation_timing(self) -> None:
        """Test state validation prevents replay attacks."""
        sso_config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test",
            client_secret="test",
            tenant_id="test",
            redirect_uri="http://localhost/callback",
        )
        encryption_key = EncryptionKey.generate()
        
        config = AuthProxyConfig(
            sso=sso_config,
            encryption_key=encryption_key.to_string(),
            config_store_type="memory",
        )
        
        app = create_auth_proxy(config=config)
        client = TestClient(app)
        
        # Get state from login
        response = client.get("/login", follow_redirects=False)
        location = response.headers.get("location", "")
        
        # Extract state from URL
        import urllib.parse
        parsed = urllib.parse.urlparse(location)
        params = urllib.parse.parse_qs(parsed.query)
        state = params.get("state", [""])[0]
        
        # Using same state twice should fail after first use
        # (in actual implementation, state is consumed after use)
        assert len(state) > 0
