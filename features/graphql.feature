Feature: GraphQL Schema Generation
  As a developer
  I want GraphQL schema to be automatically generated from database tables
  So that I can query data using GraphQL without manual schema definition

  Scenario: Dynamic schema generation for database tables
    Given a database with "users" and "posts" tables
    When I request the GraphQL schema
    Then the schema should include types for "users" and "posts"
    And each type should have Query and Mutation operations

  Scenario: GraphQL query returns data
    Given a database with sample users
    And a GraphQL schema is generated
    When I execute a GraphQL query for all users
    Then I should receive a list of users
    And each user should have id, name, and email fields

  Scenario: GraphQL mutation creates record
    Given a database with users table
    And a GraphQL schema is generated
    When I execute a mutation to create a new user
    Then the mutation should succeed
    And the new user should be stored in database
