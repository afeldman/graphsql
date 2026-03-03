"""Tests for SSO authentication module."""

from __future__ import annotations

import pytest

from graphsql.mcp_server.auth.sso import (
    OAuthToken,
    SSOAuthenticator,
    SSOConfig,
    SSOProvider,
    UserSession,
)


class TestSSOProvider:
    """Tests for SSOProvider enum."""

    def test_all_providers_exist(self) -> None:
        """Test all expected providers are defined."""
        providers = [
            SSOProvider.AZURE_AD,
            SSOProvider.OKTA,
            SSOProvider.KEYCLOAK,
            SSOProvider.AUTH0,
            SSOProvider.GOOGLE,
            SSOProvider.GITHUB,
            SSOProvider.CUSTOM,
        ]
        assert len(providers) == 7

    def test_provider_values(self) -> None:
        """Test provider enum values."""
        assert SSOProvider.AZURE_AD.value == "azure_ad"
        assert SSOProvider.OKTA.value == "okta"
        assert SSOProvider.GITHUB.value == "github"


class TestSSOConfig:
    """Tests for SSOConfig dataclass."""

    def test_azure_ad_config(self) -> None:
        """Test Azure AD configuration."""
        config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8080/callback",
        )
        assert config.provider == SSOProvider.AZURE_AD
        assert config.client_id == "test-client-id"
        assert config.tenant_id == "test-tenant-id"

    def test_azure_ad_urls(self) -> None:
        """Test Azure AD URL generation."""
        config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8080/callback",
        )
        auth_url = config.get_authorization_url()
        assert "login.microsoftonline.com" in auth_url
        assert "test-tenant-id" in auth_url
        assert "/authorize" in auth_url

        token_url = config.get_token_url()
        assert "login.microsoftonline.com" in token_url
        assert "/token" in token_url

    def test_okta_config(self) -> None:
        """Test Okta configuration."""
        config = SSOConfig(
            provider=SSOProvider.OKTA,
            client_id="test-client-id",
            client_secret="test-client-secret",
            domain="test.okta.com",
            redirect_uri="http://localhost:8080/callback",
        )
        assert config.provider == SSOProvider.OKTA
        assert config.domain == "test.okta.com"

    def test_okta_urls(self) -> None:
        """Test Okta URL generation."""
        config = SSOConfig(
            provider=SSOProvider.OKTA,
            client_id="test-client-id",
            client_secret="test-client-secret",
            domain="test.okta.com",
            redirect_uri="http://localhost:8080/callback",
        )
        auth_url = config.get_authorization_url()
        assert "test.okta.com" in auth_url

    def test_google_urls(self) -> None:
        """Test Google URL generation."""
        config = SSOConfig(
            provider=SSOProvider.GOOGLE,
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8080/callback",
        )
        auth_url = config.get_authorization_url()
        assert "accounts.google.com" in auth_url

    def test_github_urls(self) -> None:
        """Test GitHub URL generation."""
        config = SSOConfig(
            provider=SSOProvider.GITHUB,
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8080/callback",
        )
        auth_url = config.get_authorization_url()
        assert "github.com" in auth_url

    def test_custom_urls(self) -> None:
        """Test custom provider URL configuration."""
        config = SSOConfig(
            provider=SSOProvider.CUSTOM,
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8080/callback",
            authorization_url="https://custom.example.com/auth",
            token_url="https://custom.example.com/token",
            userinfo_url="https://custom.example.com/userinfo",
        )
        assert config.get_authorization_url() == "https://custom.example.com/auth"
        assert config.get_token_url() == "https://custom.example.com/token"
        assert config.get_userinfo_url() == "https://custom.example.com/userinfo"


class TestOAuthToken:
    """Tests for OAuthToken dataclass."""

    def test_create_token(self) -> None:
        """Test creating an OAuth token."""
        token = OAuthToken(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="test-refresh-token",
            scope="openid profile email",
        )
        assert token.access_token == "test-access-token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600

    def test_token_is_expired_property(self) -> None:
        """Test token expiration check (property)."""
        # Token with expired time
        token = OAuthToken(
            access_token="test",
            token_type="Bearer",
            expires_in=0,  # Expired immediately
        )
        # Force created_at to be in the past
        token.created_at = 0
        assert token.is_expired is True

    def test_token_not_expired_property(self) -> None:
        """Test token is not expired (property)."""
        token = OAuthToken(
            access_token="test",
            token_type="Bearer",
            expires_in=3600,  # 1 hour
        )
        assert token.is_expired is False


class TestUserSession:
    """Tests for UserSession dataclass."""

    def test_create_session(self) -> None:
        """Test creating a user session."""
        token = OAuthToken(
            access_token="test",
            token_type="Bearer",
            expires_in=3600,
        )
        session = UserSession(
            user_id="user123",
            email="user@example.com",
            name="Test User",
            token=token,
        )
        assert session.user_id == "user123"
        assert session.email == "user@example.com"
        assert session.name == "Test User"
        assert session.token.access_token == "test"

    def test_session_is_valid_property(self) -> None:
        """Test session validity check (property)."""
        token = OAuthToken(
            access_token="test",
            token_type="Bearer",
            expires_in=3600,
        )
        session = UserSession(
            user_id="user123",
            email="user@example.com",
            name="Test User",
            token=token,
        )
        assert session.is_valid is True

    def test_session_invalid_when_token_expired(self) -> None:
        """Test session is invalid when token expired."""
        token = OAuthToken(
            access_token="test",
            token_type="Bearer",
            expires_in=0,
        )
        token.created_at = 0  # Force expiration
        session = UserSession(
            user_id="user123",
            email="user@example.com",
            name="Test User",
            token=token,
        )
        assert session.is_valid is False


class TestSSOAuthenticator:
    """Tests for SSOAuthenticator class."""

    @pytest.fixture
    def azure_config(self) -> SSOConfig:
        """Create Azure AD config fixture."""
        return SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8080/callback",
        )

    @pytest.fixture
    def authenticator(self, azure_config: SSOConfig) -> SSOAuthenticator:
        """Create authenticator fixture."""
        return SSOAuthenticator(azure_config)

    def test_get_login_url(
        self, authenticator: SSOAuthenticator
    ) -> None:
        """Test generating login URL."""
        url = authenticator.get_login_url(state="test-state")
        assert "login.microsoftonline.com" in url
        assert "state=test-state" in url
        assert "client_id=" in url
        assert "redirect_uri=" in url

    def test_login_url_contains_scopes(
        self, authenticator: SSOAuthenticator
    ) -> None:
        """Test login URL contains correct scopes."""
        url = authenticator.get_login_url(state="test")
        assert "scope=" in url

    def test_different_states_produce_different_urls(
        self, authenticator: SSOAuthenticator
    ) -> None:
        """Test that different states produce different URLs."""
        url1 = authenticator.get_login_url(state="state1")
        url2 = authenticator.get_login_url(state="state2")
        assert url1 != url2
        assert "state1" in url1
        assert "state2" in url2

    @pytest.mark.asyncio
    async def test_context_manager(self, azure_config: SSOConfig) -> None:
        """Test authenticator as async context manager."""
        async with SSOAuthenticator(azure_config) as auth:
            assert auth._client is not None
        # Client should be closed after exiting
        assert auth._client is None

    @pytest.mark.asyncio
    async def test_close(self, authenticator: SSOAuthenticator) -> None:
        """Test closing authenticator."""
        # Access client to create it
        _ = authenticator.client
        await authenticator.close()
        assert authenticator._client is None
