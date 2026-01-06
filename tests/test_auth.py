"""Tests for JWT authentication module."""

import pytest
from datetime import timedelta
from fastapi import HTTPException, status

from graphsql.auth import (
    TokenData,
    create_access_token,
    verify_token,
)


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token_default(self) -> None:
        """Test creating token with default expiration."""
        response = create_access_token(user_id="test_user")

        assert response.access_token
        assert response.token_type == "bearer"
        assert response.expires_in > 0

    def test_create_access_token_with_scope(self) -> None:
        """Test creating token with custom scope."""
        response = create_access_token(user_id="test_user", scope="admin")

        assert response.access_token
        token_data = verify_token(response.access_token)
        assert token_data.user_id == "test_user"
        assert token_data.scope == "admin"

    def test_create_access_token_custom_expiration(self) -> None:
        """Test creating token with custom expiration."""
        expires_delta = timedelta(minutes=30)
        response = create_access_token(
            user_id="test_user",
            expires_delta=expires_delta,
        )

        assert response.access_token
        assert response.expires_in == 30 * 60  # 30 minutes in seconds


class TestTokenVerification:
    """Test JWT token verification."""

    def test_verify_valid_token(self) -> None:
        """Test verifying valid token."""
        response = create_access_token(user_id="test_user", scope="default")
        token_data = verify_token(response.access_token)

        assert token_data.user_id == "test_user"
        assert token_data.scope == "default"

    def test_verify_invalid_token(self) -> None:
        """Test verifying invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_malformed_token(self) -> None:
        """Test verifying malformed token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not_a_token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_empty_token(self) -> None:
        """Test verifying empty token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenData:
    """Test TokenData model."""

    def test_token_data_default_scope(self) -> None:
        """Test TokenData with default scope."""
        token_data = TokenData(user_id="test_user")

        assert token_data.user_id == "test_user"
        assert token_data.scope == "default"

    def test_token_data_custom_scope(self) -> None:
        """Test TokenData with custom scope."""
        token_data = TokenData(user_id="test_user", scope="admin")

        assert token_data.user_id == "test_user"
        assert token_data.scope == "admin"
