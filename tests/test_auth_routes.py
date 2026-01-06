"""Integration tests for authentication endpoints."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from graphsql.auth_routes import users_db, LoginRequest
from graphsql.main import app

client = TestClient(app)


class TestLoginEndpoint:
    """Test /auth/login endpoint."""

    def test_login_success_admin(self) -> None:
        """Test successful login as admin."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_success_demo(self) -> None:
        """Test successful login as demo user."""
        response = client.post(
            "/auth/login",
            json={"username": "demo", "password": "demo123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self) -> None:
        """Test login with invalid username."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_invalid_password(self) -> None:
        """Test login with invalid password."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_missing_username(self) -> None:
        """Test login with missing username."""
        response = client.post(
            "/auth/login",
            json={"password": "admin123"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_password(self) -> None:
        """Test login with missing password."""
        response = client.post(
            "/auth/login",
            json={"username": "admin"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_credentials(self) -> None:
        """Test login with empty credentials."""
        response = client.post(
            "/auth/login",
            json={"username": "", "password": ""},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProtectedEndpoints:
    """Test protected endpoints with JWT authentication."""

    def test_health_without_auth(self) -> None:
        """Test health endpoint without authentication."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_root_without_auth(self) -> None:
        """Test root endpoint without authentication."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_auth_endpoint_exists(self) -> None:
        """Test that auth endpoint is available."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == status.HTTP_200_OK
