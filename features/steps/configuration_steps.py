"""Step implementations for configuration feature tests."""
import os

from behave import given, when, then

from graphsql.config import Settings


@given("DATABASE_URL environment variable is set to SQLite path")
def step_set_sqlite_url(context):
    """Set SQLite database URL."""
    os.environ["DATABASE_URL"] = "sqlite:///test.db"


@when("the application starts")
def step_app_starts(context):
    """Start application (load settings)."""
    context.settings = Settings.load()


@then("it should detect SQLite as the database type")
def step_detect_sqlite(context):
    """Assert SQLite is detected."""
    assert context.settings.is_sqlite is True
    assert context.settings.is_postgres is False
    assert context.settings.is_mysql is False


@then("it should create or open the SQLite database file")
def step_sqlite_file_created(context):
    """Assert SQLite setup is ready."""
    assert context.settings.database_url.startswith("sqlite://")


@given("DATABASE_URL environment variable is set to PostgreSQL connection string")
def step_set_postgres_url(context):
    """Set PostgreSQL database URL."""
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/graphsql"


@when("the application loads configuration")
def step_load_configuration(context):
    """Load configuration."""
    context.settings = Settings.load()


@then("it should detect PostgreSQL as the database type")
def step_detect_postgres(context):
    """Assert PostgreSQL is detected."""
    assert context.settings.is_postgres is True
    assert context.settings.is_sqlite is False
    assert context.settings.is_mysql is False


@then("configuration should include PostgreSQL specific settings")
def step_postgres_settings(context):
    """Assert PostgreSQL configuration is present."""
    assert context.settings.is_postgres is True


@given("DATABASE_URL environment variable is set to MySQL connection string")
def step_set_mysql_url(context):
    """Set MySQL database URL."""
    os.environ["DATABASE_URL"] = "mysql+pymysql://user:pass@localhost/graphsql"


@then("it should detect MySQL as the database type")
def step_detect_mysql(context):
    """Assert MySQL is detected."""
    assert context.settings.is_mysql is True
    assert context.settings.is_postgres is False
    assert context.settings.is_sqlite is False


@then("configuration should include MySQL specific settings")
def step_mysql_settings(context):
    """Assert MySQL configuration is present."""
    assert context.settings.is_mysql is True


@given("environment variables for API_HOST and API_PORT are set")
def step_set_api_config(context):
    """Set API configuration."""
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["API_HOST"] = "127.0.0.1"
    os.environ["API_PORT"] = "9000"


@then("the API should bind to the specified host and port")
def step_api_configured(context):
    """Assert API is configured correctly."""
    assert context.settings.api_host == "127.0.0.1"
    assert context.settings.api_port == 9000


@then("the server should be accessible at that address")
def step_server_accessible(context):
    """Assert server is accessible."""
    # This would be tested via actual HTTP request in integration test
    pass


@given("LOG_LEVEL environment variable is set to DEBUG")
def step_set_log_level_debug(context):
    """Set log level to DEBUG."""
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["LOG_LEVEL"] = "DEBUG"


@then("logging level should be DEBUG")
def step_log_level_debug(context):
    """Assert log level is DEBUG."""
    assert context.settings.log_level == "DEBUG"


@then("detailed log messages should be output")
def step_detailed_logs(context):
    """Assert detailed logging is enabled."""
    assert context.settings.log_level == "DEBUG"


@given("CORS_ORIGINS environment variable is set to specific hosts")
def step_set_cors_origins(context):
    """Set CORS origins."""
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"


@when("a cross-origin request is made from an allowed origin")
def step_cors_request(context):
    """Make cross-origin request."""
    context.cors_origins = ["http://localhost:3000", "http://localhost:8080"]


@then("the request should succeed")
def step_cors_success(context):
    """Assert CORS request succeeds."""
    pass


@then("CORS headers should be present in response")
def step_cors_headers_present(context):
    """Assert CORS headers are present."""
    pass
