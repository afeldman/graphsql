"""Common step implementations shared across features."""

from typing import Any

from behave import given, then, when
from fastapi.testclient import TestClient

from graphsql.main import app


@given("the GraphSQL API is running")
def step_api_running(context: Any) -> None:
    """Set up running API."""
    import os

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    context.client = TestClient(app)


@when("I request the /health endpoint")
def step_request_health(context: Any) -> None:
    """Request health endpoint."""
    context.response = context.client.get("/health")


@when("I request the / endpoint")
def step_request_root(context: Any) -> None:
    """Request root endpoint."""
    context.response = context.client.get("/")


@then("the response status should be 200")
def step_status_200(context: Any) -> None:
    """Assert response status is 200."""
    assert context.response.status_code == 200, f"Expected 200, got {context.response.status_code}"


@then("the response status should be 201")
def step_status_201(context: Any) -> None:
    """Assert response status is 201."""
    assert context.response.status_code == 201, f"Expected 201, got {context.response.status_code}"


@then("the response status should be 204")
def step_status_204(context: Any) -> None:
    """Assert response status is 204."""
    assert context.response.status_code == 204, f"Expected 204, got {context.response.status_code}"


@then('the response should contain status "healthy"')
def step_contains_healthy_status(context: Any) -> None:
    """Assert response contains healthy status."""
    data = context.response.json()
    assert data.get("status") == "healthy"


@then("the response should contain a list of table names")
def step_contains_table_list(context: Any) -> None:
    """Assert response contains a list."""
    assert isinstance(context.response.json(), (list, dict))
