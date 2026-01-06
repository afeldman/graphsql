Feature: Database Configuration
  As an administrator
  I want to configure database connections via environment variables
  So that the application can connect to different databases

  Scenario: SQLite database connection
    Given DATABASE_URL environment variable is set to SQLite path
    When the application starts
    Then it should detect SQLite as the database type
    And it should create or open the SQLite database file

  Scenario: PostgreSQL database connection
    Given DATABASE_URL environment variable is set to PostgreSQL connection string
    When the application loads configuration
    Then it should detect PostgreSQL as the database type
    And configuration should include PostgreSQL specific settings

  Scenario: MySQL database connection
    Given DATABASE_URL environment variable is set to MySQL connection string
    When the application loads configuration
    Then it should detect MySQL as the database type
    And configuration should include MySQL specific settings

  Scenario: API configuration from environment
    Given environment variables for API_HOST and API_PORT are set
    When the application starts
    Then the API should bind to the specified host and port
    And the server should be accessible at that address

  Scenario: Logging configuration from environment
    Given LOG_LEVEL environment variable is set to DEBUG
    When the application starts
    Then logging level should be DEBUG
    And detailed log messages should be output

  Scenario: CORS configuration
    Given CORS_ORIGINS environment variable is set to specific hosts
    When a cross-origin request is made from an allowed origin
    Then the request should succeed
    And CORS headers should be present in response
