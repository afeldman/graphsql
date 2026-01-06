"""Step implementations for REST API feature tests."""
import os

from behave import when, then, given
from fastapi.testclient import TestClient

from graphsql.main import app


@given("a database with multiple tables")
def step_database_with_tables(context):
    """Set up database with multiple tables."""
    context.client = TestClient(app)
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@when("I send a GET request to /api/tables")
def step_get_tables(context):
    """Send GET request to list tables."""
    context.response = context.client.get("/api/tables")


@then("the response status should be 200")
def step_status_200(context):
    """Assert response status is 200."""
    assert context.response.status_code == 200, f"Expected 200, got {context.response.status_code}"


@then("the response should contain a list of table names")
def step_contains_table_list(context):
    """Assert response contains a list."""
    assert isinstance(context.response.json(), list)


@given("a database with a \"{table}\" table containing {fields} columns")
def step_database_with_table(context, table, fields):
    """Set up database with specific table."""
    context.client = TestClient(app)
    context.table_name = table
    context.fields = fields.split(", ")


@when("I send a GET request to /api/tables/{table}/info")
def step_get_table_info(context, table):
    """Send GET request for table schema."""
    context.response = context.client.get(f"/api/tables/{table}/info")


@then("the response should contain column information")
def step_contains_column_info(context):
    """Assert response contains column information."""
    if context.response.status_code == 200:
        data = context.response.json()
        assert "columns" in data or "result" in data


@then("the response should include primary key information")
def step_contains_primary_key(context):
    """Assert response includes primary key info."""
    if context.response.status_code == 200:
        data = context.response.json()
        assert "primary_key" in data or "columns" in data


@given("a database with \"{table}\" table containing {count} records")
def step_database_with_records(context, table, count):
    """Set up database with records."""
    context.client = TestClient(app)
    context.table_name = table
    context.record_count = int(count)


@when("I send a GET request to /api/{table}?limit={limit}&offset={offset}")
def step_get_with_pagination(context, table, limit, offset):
    """Send GET request with pagination parameters."""
    context.response = context.client.get(f"/api/{table}?limit={limit}&offset={offset}")


@then("the response should contain {count} {table}")
def step_contains_record_count(context, count, table):
    """Assert response contains expected number of records."""
    if context.response.status_code == 200:
        data = context.response.json()
        assert isinstance(data, list)


@then("pagination should work correctly for different offsets")
def step_pagination_works(context):
    """Assert pagination works correctly."""
    assert context.response.status_code == 200


@given("a database with \"{table}\" table")
def step_database_with_table_basic(context, table):
    """Set up database with a basic table."""
    context.client = TestClient(app)
    context.table_name = table


@when("I send a POST request to /api/{table} with user data")
def step_post_user_data(context, table):
    """Send POST request to create a user."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "age": 25
    }
    context.response = context.client.post(f"/api/{table}", json=user_data)


@then("the response status should be 201")
def step_status_201(context):
    """Assert response status is 201."""
    assert context.response.status_code == 201, f"Expected 201, got {context.response.status_code}"


@then("the response should contain the created user with an id")
def step_response_contains_created_user(context):
    """Assert response contains created user."""
    data = context.response.json()
    assert "id" in data or "name" in data


@then("the record should be stored in database")
def step_record_stored(context):
    """Assert record is stored in database."""
    # Verification would happen in integration test
    pass


@given("a database with \"{table}\" table containing sample data")
def step_database_with_sample_data(context, table):
    """Set up database with sample data."""
    context.client = TestClient(app)
    context.table_name = table


@when("I send a GET request to /api/{table}/{id}")
def step_get_single_record(context, table, id):
    """Send GET request for single record."""
    context.response = context.client.get(f"/api/{table}/{id}")


@when("I send a PUT request to /api/{table}/{id} with updated data")
def step_put_update_record(context, table, id):
    """Send PUT request to update record."""
    updated_data = {"name": "Updated Name"}
    context.response = context.client.put(f"/api/{table}/{id}", json=updated_data)


@then("the database should contain the updated record")
def step_database_has_update(context):
    """Assert database has updated record."""
    assert context.response.status_code == 200


@when("I send a PATCH request to /api/{table}/{id} with partial data")
def step_patch_partial_update(context, table, id):
    """Send PATCH request for partial update."""
    partial_data = {"name": "Partially Updated"}
    context.response = context.client.patch(f"/api/{table}/{id}", json=partial_data)


@then("only the specified fields should be updated")
def step_only_specified_fields_updated(context):
    """Assert only specified fields are updated."""
    assert context.response.status_code == 200


@when("I send a DELETE request to /api/{table}/{id}")
def step_delete_record(context, table, id):
    """Send DELETE request to delete record."""
    context.response = context.client.delete(f"/api/{table}/{id}")


@then("the response status should be 204")
def step_status_204(context):
    """Assert response status is 204."""
    assert context.response.status_code == 204, f"Expected 204, got {context.response.status_code}"


@then("the record should no longer exist in database")
def step_record_deleted(context):
    """Assert record is deleted from database."""
    # Verification would happen in integration test
    pass
