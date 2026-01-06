Feature: Health Check and Status
  As a monitoring system
  I want to check the health status of the GraphSQL API
  So that I can verify the application is running

  Scenario: Health check endpoint returns healthy status
    Given the GraphSQL API is running
    When I request the /health endpoint
    Then the response status should be 200
    And the response should contain status "healthy"

  Scenario: API root endpoint provides information
    Given the GraphSQL API is running
    When I request the / endpoint
    Then the response status should be 200
