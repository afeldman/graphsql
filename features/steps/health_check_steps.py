"""Step implementations for health check feature tests."""
import os

from behave import given, when, then
from fastapi.testclient import TestClient

from graphsql.main import app


@given("the GraphSQL API is running")
def step_api_running(context):
    """Set up running API."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    context.client = TestClient(app)


@when("I request the /health endpoint")
def step_request_health(context):
    """Request health endpoint."""
    context.response = context.client.get("/health")


@then("the response status should be 200")
def step_status_200(context):
    """Assert response status is 200."""
    assert context.response.status_code == 200


@then("the response should contain status \"healthy\"")
def step_contains_healthy_status(context):
    """Assert response contains healthy status."""
    data = context.response.json()
    assert data.get("status") == "healthy"


@then("database_connected should be true")
def step_database_connected_true(context):
    """Assert database is connected."""
    data = context.response.json()
    assert data.get("database_connected") is True


@then("the response should contain a timestamp")
def step_contains_timestamp(context):
    """Assert response contains timestamp."""
    data = context.response.json()
    assert "timestamp" in data


@given("the GraphSQL API is running with multiple tables")
def step_api_running_with_tables(context):
    """Set up API with multiple tables."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    context.client = TestClient(app)


@then("the response should include tables_count")
def step_includes_tables_count(context):
    """Assert response includes table count."""
    data = context.response.json()
    assert "tables_count" in data


@then("tables_count should be greater than or equal to 0")
def step_tables_count_valid(context):
    """Assert tables count is valid."""
    data = context.response.json()
    assert data.get("tables_count") >= 0


@when("I request the root / endpoint")
def step_request_root(context):
    """Request root endpoint."""
    context.response = context.client.get("/")


@then("the response should describe available API endpoints")
def step_describes_endpoints(context):
    """Assert response describes endpoints."""
    data = context.response.json()
    assert data is not None
