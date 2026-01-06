Feature: Health Check and Status
  As a monitoring system
  I want to check the health status of the GraphSQL API
  So that I can verify the application is running and database is accessible

  Scenario: Health check endpoint returns healthy status
    Given the GraphSQL API is running
    When I request the /health endpoint
    Then the response status should be 200
    And the response should contain status "healthy"
    And database_connected should be true
    And the response should contain a timestamp

  Scenario: Health check includes table count
    Given the GraphSQL API is running with multiple tables
    When I request the /health endpoint
    Then the response should include tables_count
    And tables_count should be greater than or equal to 0

  Scenario: API root endpoint provides information
    Given the GraphSQL API is running
    When I request the root / endpoint
    Then the response status should be 200
    And the response should describe available API endpoints
