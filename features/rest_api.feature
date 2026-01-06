Feature: REST API CRUD Operations
  As an API consumer
  I want to perform CRUD operations via REST endpoints
  So that I can manage database records through HTTP requests

  Scenario: List all tables
    Given a database with multiple tables
    When I send a GET request to /api/tables
    Then the response status should be 200
    And the response should contain a list of table names

  Scenario: Get table schema information
    Given a database with a "users" table containing id, name, email columns
    When I send a GET request to /api/tables/users/info
    Then the response status should be 200
    And the response should contain column information
    And the response should include primary key information

  Scenario: List records with pagination
    Given a database with "users" table containing 100 records
    When I send a GET request to /api/users?limit=10&offset=0
    Then the response status should be 200
    And the response should contain 10 users
    And pagination should work correctly for different offsets

  Scenario: Create a new record via REST
    Given a database with "users" table
    When I send a POST request to /api/users with user data
    Then the response status should be 201
    And the response should contain the created user with an id
    And the record should be stored in database

  Scenario: Get single record by id
    Given a database with "users" table containing sample data
    When I send a GET request to /api/users/1
    Then the response status should be 200
    And the response should contain user data for id 1

  Scenario: Update record via REST
    Given a database with "users" table containing sample data
    When I send a PUT request to /api/users/1 with updated data
    Then the response status should be 200
    And the database should contain the updated record

  Scenario: Partial update record via PATCH
    Given a database with "users" table containing sample data
    When I send a PATCH request to /api/users/1 with partial data
    Then the response status should be 200
    And only the specified fields should be updated

  Scenario: Delete record via REST
    Given a database with "users" table containing sample data
    When I send a DELETE request to /api/users/1
    Then the response status should be 204
    And the record should no longer exist in database
