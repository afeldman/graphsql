"""Unit tests for REST API routes."""
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_success(self, client: TestClient):
        """Test health check returns 200 with valid response."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "tables_count" in data

    def test_health_check_response_structure(self, client: TestClient):
        """Test health check response contains required fields."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["status"], str)
        assert isinstance(data["tables_count"], int)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_available_endpoints(self, client: TestClient):
        """Test root endpoint returns available endpoints."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data or "message" in data


class TestTableListing:
    """Test table listing endpoint."""

    def test_list_tables_empty(self, client: TestClient):
        """Test listing tables when database is empty."""
        response = client.get("/api/tables")

        assert response.status_code == 200
        tables = response.json()
        assert isinstance(tables, (list, dict))

    def test_list_tables_endpoint_exists(self, client: TestClient):
        """Test that tables endpoint is accessible."""
        response = client.get("/api/tables")
        assert response.status_code == 200


class TestSwaggerDocumentation:
    """Test Swagger/OpenAPI documentation."""

    def test_swagger_ui_accessible(self, client: TestClient):
        """Test Swagger UI is accessible at /docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, client: TestClient):
        """Test ReDoc is accessible at /redoc."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_accessible(self, client: TestClient):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema or "swagger" in schema
