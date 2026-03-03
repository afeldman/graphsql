"""SSO/OAuth Authentication for MCP Server.

This module provides OAuth/OIDC authentication support for multiple
identity providers including Azure AD, Okta, Keycloak, Auth0, Google, and GitHub.

Example:
    >>> from graphsql.mcp_server.auth.sso import SSOAuthenticator, SSOConfig, SSOProvider
    >>> config = SSOConfig(
    ...     provider=SSOProvider.AZURE_AD,
    ...     client_id="your-client-id",
    ...     client_secret="your-client-secret",
    ...     tenant_id="your-tenant-id",
    ... )
    >>> async with SSOAuthenticator(config) as auth:
    ...     user_session = await auth.authenticate(authorization_code)
"""

from __future__ import annotations

import time
import urllib.parse
from enum import Enum
from typing import Any, Self

# Python 3.11+ has StrEnum, Python 3.10 needs a fallback
try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):  # type: ignore[no-redef]
        """String Enum for Python 3.10 compatibility."""

        pass

import httpx
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, computed_field


class SSOProvider(StrEnum):
    """Supported SSO/OAuth providers.

    Each provider has specific endpoints and configuration requirements.
    Use CUSTOM for providers not in this list.
    """

    AZURE_AD = "azure_ad"
    OKTA = "okta"
    KEYCLOAK = "keycloak"
    AUTH0 = "auth0"
    GOOGLE = "google"
    GITHUB = "github"
    CUSTOM = "custom"


class SSOConfig(BaseModel):
    """SSO Provider Configuration.

    This model holds all necessary configuration for OAuth/OIDC authentication.
    Different providers require different fields - see the documentation for
    each provider's requirements.

    Attributes:
        provider: The SSO provider type.
        client_id: OAuth client ID from the provider.
        client_secret: OAuth client secret from the provider.
        tenant_id: Azure AD tenant ID (Azure AD only).
        domain: Provider domain (Okta, Auth0, Keycloak).
        authorization_url: Custom authorization endpoint URL.
        token_url: Custom token endpoint URL.
        userinfo_url: Custom userinfo endpoint URL.
        scopes: OAuth scopes to request.
        redirect_uri: OAuth redirect URI (must match provider config).
    """

    provider: SSOProvider = Field(description="SSO provider type")
    client_id: str = Field(description="OAuth client ID")
    client_secret: str = Field(description="OAuth client secret")
    tenant_id: str | None = Field(default=None, description="Tenant ID (Azure AD)")
    domain: str | None = Field(default=None, description="Domain (Okta, Auth0)")
    authorization_url: str | None = Field(default=None, description="Custom auth URL")
    token_url: str | None = Field(default=None, description="Custom token URL")
    userinfo_url: str | None = Field(default=None, description="Custom userinfo URL")
    scopes: list[str] = Field(
        default_factory=lambda: ["openid", "profile", "email"],
        description="OAuth scopes",
    )
    redirect_uri: str = Field(
        default="http://localhost:8080/callback",
        description="OAuth redirect URI",
    )

    def get_authorization_url(self) -> str:
        """Get the authorization URL for the provider.

        Returns:
            Authorization endpoint URL.

        Raises:
            ValueError: If required provider configuration is missing.
        """
        if self.authorization_url:
            return self.authorization_url

        urls = {
            SSOProvider.AZURE_AD: f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize",
            SSOProvider.OKTA: f"https://{self.domain}/oauth2/default/v1/authorize",
            SSOProvider.KEYCLOAK: f"https://{self.domain}/realms/master/protocol/openid-connect/auth",
            SSOProvider.AUTH0: f"https://{self.domain}/authorize",
            SSOProvider.GOOGLE: "https://accounts.google.com/o/oauth2/v2/auth",
            SSOProvider.GITHUB: "https://github.com/login/oauth/authorize",
        }

        url = urls.get(self.provider)
        if not url:
            raise ValueError(f"No authorization URL configured for provider: {self.provider}")
        return url

    def get_token_url(self) -> str:
        """Get the token URL for the provider.

        Returns:
            Token endpoint URL.

        Raises:
            ValueError: If required provider configuration is missing.
        """
        if self.token_url:
            return self.token_url

        urls = {
            SSOProvider.AZURE_AD: f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
            SSOProvider.OKTA: f"https://{self.domain}/oauth2/default/v1/token",
            SSOProvider.KEYCLOAK: f"https://{self.domain}/realms/master/protocol/openid-connect/token",
            SSOProvider.AUTH0: f"https://{self.domain}/oauth/token",
            SSOProvider.GOOGLE: "https://oauth2.googleapis.com/token",
            SSOProvider.GITHUB: "https://github.com/login/oauth/access_token",
        }

        url = urls.get(self.provider)
        if not url:
            raise ValueError(f"No token URL configured for provider: {self.provider}")
        return url

    def get_userinfo_url(self) -> str:
        """Get the userinfo URL for the provider.

        Returns:
            Userinfo endpoint URL.

        Raises:
            ValueError: If required provider configuration is missing.
        """
        if self.userinfo_url:
            return self.userinfo_url

        urls = {
            SSOProvider.AZURE_AD: "https://graph.microsoft.com/oidc/userinfo",
            SSOProvider.OKTA: f"https://{self.domain}/oauth2/default/v1/userinfo",
            SSOProvider.KEYCLOAK: f"https://{self.domain}/realms/master/protocol/openid-connect/userinfo",
            SSOProvider.AUTH0: f"https://{self.domain}/userinfo",
            SSOProvider.GOOGLE: "https://openidconnect.googleapis.com/v1/userinfo",
            SSOProvider.GITHUB: "https://api.github.com/user",
        }

        url = urls.get(self.provider)
        if not url:
            raise ValueError(f"No userinfo URL configured for provider: {self.provider}")
        return url


class OAuthToken(BaseModel):
    """OAuth token container.

    Holds the access token and related metadata from OAuth token response.

    Attributes:
        access_token: The OAuth access token.
        token_type: Token type (usually "Bearer").
        expires_in: Token lifetime in seconds.
        refresh_token: Optional refresh token for token renewal.
        scope: Granted scopes as space-separated string.
        id_token: Optional OIDC ID token.
        created_at: Unix timestamp when token was created.
    """

    model_config = ConfigDict(frozen=False)

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str | None = None
    scope: str = ""
    id_token: str | None = None
    created_at: float = Field(default_factory=time.time)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 60s buffer).

        Returns:
            True if token is expired or about to expire.
        """
        return time.time() > (self.created_at + self.expires_in - 60)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def expires_at(self) -> float:
        """Get token expiration timestamp.

        Returns:
            Unix timestamp when token expires.
        """
        return self.created_at + self.expires_in

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> Self:
        """Create token from OAuth response.

        Args:
            data: Token response from OAuth provider.

        Returns:
            OAuthToken instance.
        """
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope", ""),
            id_token=data.get("id_token"),
        )


class UserSession(BaseModel):
    """User session with identity information.

    Contains the authenticated user's identity information and OAuth token.

    Attributes:
        user_id: Unique user identifier from the provider.
        email: User's email address.
        name: User's display name.
        token: OAuth token for API access.
        groups: List of groups the user belongs to.
        roles: List of roles assigned to the user.
        attributes: Additional user attributes from the provider.
        created_at: Unix timestamp when session was created.
    """

    model_config = ConfigDict(frozen=False)

    user_id: str
    email: str
    name: str
    token: OAuthToken
    groups: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_valid(self) -> bool:
        """Check if session is still valid.

        Returns:
            True if token is not expired.
        """
        return not self.token.is_expired

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role.

        Args:
            role: Role name to check.

        Returns:
            True if user has the role.
        """
        return role in self.roles

    def has_group(self, group: str) -> bool:
        """Check if user is in a specific group.

        Args:
            group: Group name to check.

        Returns:
            True if user is in the group.
        """
        return group in self.groups


class SSOAuthenticator:
    """SSO Authentication handler.

    Handles the OAuth/OIDC authentication flow including authorization,
    token exchange, and user info retrieval.

    Example:
        >>> config = SSOConfig(provider=SSOProvider.GOOGLE, ...)
        >>> async with SSOAuthenticator(config) as auth:
        ...     login_url = auth.get_login_url(state="random-state")
        ...     # ... redirect user to login_url ...
        ...     user = await auth.authenticate(code="authorization-code")
    """

    def __init__(self, config: SSOConfig) -> None:
        """Initialize authenticator with SSO config.

        Args:
            config: SSO provider configuration.
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None
        logger.debug(
            "Initialized SSO authenticator",
            provider=config.provider.value,
            client_id=config.client_id[:8] + "...",
            redirect_uri=config.redirect_uri,
            scopes=config.scopes,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Async HTTP client.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
            logger.trace("Created new HTTP client for SSO requests")
        return self._client

    async def __aenter__(self) -> SSOAuthenticator:
        """Async context manager entry.

        Returns:
            Self for context manager usage.
        """
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.trace(
            "Entered SSO authenticator context",
            provider=self.config.provider.value,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.trace(
                "Exited SSO authenticator context and closed HTTP client",
                provider=self.config.provider.value,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_login_url(self, state: str) -> str:
        """Generate login URL with state parameter.

        Args:
            state: Random state parameter for CSRF protection.

        Returns:
            Complete login URL to redirect user to.
        """
        params: dict[str, str] = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "state": state,
        }

        # Provider-specific parameters
        if self.config.provider == SSOProvider.AZURE_AD:
            params["response_mode"] = "query"
        elif self.config.provider == SSOProvider.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        base_url = self.config.get_authorization_url()
        return f"{base_url}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback.

        Returns:
            OAuth token containing access token and refresh token.

        Raises:
            httpx.HTTPStatusError: If token exchange fails.
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }

        headers = {"Accept": "application/json"}

        logger.debug(
            "Exchanging authorization code for token",
            token_url=self.config.get_token_url(),
            provider=self.config.provider.value,
        )

        response = await self.client.post(
            self.config.get_token_url(),
            data=data,
            headers=headers,
        )
        response.raise_for_status()

        token_data = response.json()
        logger.info(
            "Successfully exchanged authorization code for tokens",
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            has_refresh_token=bool(token_data.get("refresh_token")),
        )

        return OAuthToken.from_response(token_data)

    async def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh an expired token.

        Args:
            refresh_token: Refresh token from previous authentication.

        Returns:
            New OAuth token.

        Raises:
            httpx.HTTPStatusError: If token refresh fails.
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        response = await self.client.post(
            self.config.get_token_url(),
            data=data,
        )
        response.raise_for_status()

        logger.info(
            "Successfully refreshed OAuth token",
            provider=self.config.provider.value,
        )
        return OAuthToken.from_response(response.json())

    async def get_user_info(self, token: OAuthToken) -> dict[str, Any]:
        """Get user information from SSO provider.

        Args:
            token: OAuth token with access token.

        Returns:
            User info dictionary from provider.

        Raises:
            httpx.HTTPStatusError: If userinfo request fails.
        """
        headers = {"Authorization": f"{token.token_type} {token.access_token}"}

        response = await self.client.get(
            self.config.get_userinfo_url(),
            headers=headers,
        )
        response.raise_for_status()

        user_info = response.json()
        logger.debug(
            "Retrieved user info from SSO provider",
            email=user_info.get("email", "unknown"),
            provider=self.config.provider.value,
            fields=list(user_info.keys()),
        )

        result: dict[str, Any] = user_info
        return result

    async def authenticate(self, code: str) -> UserSession:
        """Complete authentication flow and create user session.

        Exchanges the authorization code for tokens and retrieves user info.

        Args:
            code: Authorization code from OAuth callback.

        Returns:
            UserSession with user info and token.

        Raises:
            httpx.HTTPStatusError: If any OAuth request fails.
        """
        start_time = time.time()
        logger.debug(
            "Starting SSO authentication flow",
            provider=self.config.provider.value,
            code_prefix=code[:8] + "...",
        )

        token = await self.exchange_code(code)
        token_time = time.time()
        logger.trace(
            "Token exchange completed",
            duration_ms=int((token_time - start_time) * 1000),
        )

        user_info = await self.get_user_info(token)
        userinfo_time = time.time()
        logger.trace(
            "User info retrieval completed",
            duration_ms=int((userinfo_time - token_time) * 1000),
        )

        # Extract user details based on provider
        user_id = self._extract_user_id(user_info)
        email = self._extract_email(user_info)
        name = self._extract_name(user_info)
        groups = self._extract_groups(user_info)
        roles = self._extract_roles(user_info)

        session = UserSession(
            user_id=user_id,
            email=email,
            name=name,
            token=token,
            groups=groups,
            roles=roles,
            attributes=user_info,
        )

        logger.info(
            "Created user session from SSO authentication",
            user_id=user_id,
            email=email,
            name=name,
            groups_count=len(groups),
            roles_count=len(roles),
            provider=self.config.provider.value,
        )
        return session

    def _extract_user_id(self, user_info: dict[str, Any]) -> str:
        """Extract user ID from provider response.

        Args:
            user_info: User info from provider.

        Returns:
            User identifier string.
        """
        # Check common user ID fields
        keys = ["sub", "id", "user_id", "oid"]
        for key in keys:
            if key in user_info:
                return str(user_info[key])
        email: str = str(user_info.get("email", "unknown"))
        return email

    def _extract_email(self, user_info: dict[str, Any]) -> str:
        """Extract email from provider response.

        Args:
            user_info: User info from provider.

        Returns:
            User email address.
        """
        return str(user_info.get("email", user_info.get("preferred_username", "")))

    def _extract_name(self, user_info: dict[str, Any]) -> str:
        """Extract name from provider response.

        Args:
            user_info: User info from provider.

        Returns:
            User display name.
        """
        if "name" in user_info:
            return str(user_info["name"])
        given = user_info.get("given_name", "")
        family = user_info.get("family_name", "")
        full_name = f"{given} {family}".strip()
        return full_name or self._extract_email(user_info)

    def _extract_groups(self, user_info: dict[str, Any]) -> list[str]:
        """Extract groups from provider response.

        Args:
            user_info: User info from provider.

        Returns:
            List of group names.
        """
        groups = user_info.get("groups", [])
        if isinstance(groups, list):
            return [str(g) for g in groups]
        return []

    def _extract_roles(self, user_info: dict[str, Any]) -> list[str]:
        """Extract roles from provider response.

        Args:
            user_info: User info from provider.

        Returns:
            List of role names.
        """
        # Check multiple possible role locations
        roles = user_info.get("roles", [])
        if not roles:
            # Keycloak stores roles differently
            realm_access = user_info.get("realm_access", {})
            roles = realm_access.get("roles", [])
        if isinstance(roles, list):
            return [str(r) for r in roles]
        return []
