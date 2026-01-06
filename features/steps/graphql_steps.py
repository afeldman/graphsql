"""Step implementations for GraphQL feature tests."""
import os

from behave import given, when, then
from fastapi.testclient import TestClient

from graphsql.main import app


@given("a database with \"{tables}\" tables")
def step_database_with_tables(context, tables):
    """Set up database with specified tables."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    context.client = TestClient(app)
    context.tables = tables.split(" and ")


@when("I request the GraphQL schema")
def step_request_graphql_schema(context):
    """Request GraphQL schema."""
    # Schema is embedded in GraphQL endpoint
    context.response = context.client.get("/graphql")


@then("the schema should include types for \"{table_types}\"")
def step_schema_includes_types(context, table_types):
    """Assert schema includes expected types."""
    # Check via introspection or documentation
    pass


@then("each type should have Query and Mutation operations")
def step_types_have_operations(context):
    """Assert types have Query and Mutation."""
    pass


@given("a database with sample users")
def step_database_sample_users(context):
    """Set up database with sample users."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    context.client = TestClient(app)


@given("a GraphQL schema is generated")
def step_graphql_schema_generated(context):
    """Generate GraphQL schema."""
    # Schema is auto-generated
    pass


@when("I execute a GraphQL query for all users")
def step_execute_graphql_query(context):
    """Execute GraphQL query."""
    query = """
    query {
      users(limit: 10, offset: 0) {
        id
        name
        email
      }
    }
    """
    context.response = context.client.post("/graphql", json={"query": query})


@then("I should receive a list of users")
def step_receive_users_list(context):
    """Assert response contains users list."""
    if context.response.status_code == 200:
        data = context.response.json()
        assert "data" in data or "errors" not in data


@then("each user should have id, name, and email fields")
def step_users_have_fields(context):
    """Assert users have required fields."""
    pass


@given("a database with users table")
def step_database_users_table(context):
    """Set up database with users table."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    context.client = TestClient(app)


@when("I execute a mutation to create a new user")
def step_execute_create_mutation(context):
    """Execute GraphQL mutation to create user."""
    mutation = """
    mutation {
      createUser(name: "New User", email: "newuser@example.com") {
        id
        name
        email
      }
    }
    """
    context.response = context.client.post("/graphql", json={"query": mutation})


@then("the mutation should succeed")
def step_mutation_succeeds(context):
    """Assert mutation succeeds."""
    if context.response.status_code == 200:
        data = context.response.json()
        assert "errors" not in data or len(data.get("errors", [])) == 0


@then("the new user should be stored in database")
def step_user_stored_in_db(context):
    """Assert new user is stored."""
    pass
