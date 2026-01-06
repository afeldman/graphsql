"""Tests for rate limiting functionality."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from graphsql.main import app
from graphsql.rate_limit import limiter

client = TestClient(app)


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_rate_limiter_initialized(self) -> None:
        """Test that rate limiter is initialized."""
        assert app.state.limiter is not None
        assert limiter is not None

    def test_health_endpoint_accessible(self) -> None:
        """Test that health endpoint is accessible."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_root_endpoint_accessible(self) -> None:
        """Test that root endpoint is accessible."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_auth_login_endpoint_accessible(self) -> None:
        """Test that auth endpoint is accessible."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_docs_endpoint_accessible(self) -> None:
        """Test that API docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_swagger_json_accessible(self) -> None:
        """Test that Swagger schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
