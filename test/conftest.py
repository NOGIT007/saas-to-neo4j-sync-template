"""
Pytest fixtures for SaaS to Neo4j sync testing

Provides reusable test fixtures for:
- Configuration objects (API, Neo4j, Sync)
- Client instances (API client, Neo4j driver)
- Test data generators
- Database cleanup utilities

Usage:
    def test_example(api_config, neo4j_driver):
        # Fixtures automatically injected
        assert api_config.api_url
        result = neo4j_driver.execute_query("MATCH (n) RETURN count(n)")
"""

import pytest
import os
from unittest.mock import Mock, MagicMock
from neo4j import GraphDatabase

# TODO: Update import paths to match your project structure
from {project}_sync.config import {API}Config, Neo4jConfig, SyncConfig
from {project}_sync.{api}_client import {API}Client


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def api_config():
    """
    Fixture providing API configuration

    TODO: Customize for your API authentication method

    Returns:
        {API}Config: Configured API settings
    """
    return {API}Config(
        api_url=os.getenv("{API_NAME}_URL", "https://api.example.com/v1"),
        client_id=os.getenv("{API_NAME}_CLIENT_ID", "test_client_id"),
        client_secret=os.getenv("{API_NAME}_CLIENT_SECRET", "test_client_secret"),
        max_retries=3,
        batch_size=100,
        request_timeout=60
    )


@pytest.fixture
def neo4j_config():
    """
    Fixture providing Neo4j configuration

    Returns:
        Neo4jConfig: Configured Neo4j settings
    """
    return Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j")
    )


@pytest.fixture
def sync_config():
    """
    Fixture providing sync configuration

    Returns:
        SyncConfig: Configured sync settings
    """
    return SyncConfig(
        default_days_back=365,
        enable_metrics=True,
        enable_analytics=True,
        create_indexes=True
    )


# =============================================================================
# Client Fixtures
# =============================================================================

@pytest.fixture
def mock_api_client(api_config):
    """
    Fixture providing mocked API client

    Use for structural tests that don't need real API calls.

    TODO: Add mock responses for your specific API endpoints

    Returns:
        Mock: Mocked {API}Client with common responses
    """
    client = Mock(spec={API}Client)
    client.config = api_config

    # Mock authentication
    client.authenticate.return_value = True

    # TODO: Mock your entity fetch methods
    # Example:
    # client.get_customers.return_value = [
    #     {"guid": "customer-1", "name": "Test Customer 1"},
    #     {"guid": "customer-2", "name": "Test Customer 2"}
    # ]
    # client.get_users.return_value = [
    #     {"guid": "user-1", "email": "user1@example.com"},
    #     {"guid": "user-2", "email": "user2@example.com"}
    # ]

    return client


@pytest.fixture
def api_client(api_config):
    """
    Fixture providing real API client

    Use for integration tests that need actual API connectivity.

    Returns:
        {API}Client: Real API client instance
    """
    client = {API}Client(api_config)
    # Note: Don't auto-authenticate here - let tests control authentication
    return client


@pytest.fixture
def neo4j_driver(neo4j_config):
    """
    Fixture providing Neo4j driver connection

    Automatically closes connection after test.

    Returns:
        neo4j.Driver: Connected Neo4j driver
    """
    driver = GraphDatabase.driver(
        neo4j_config.uri,
        auth=(neo4j_config.username, neo4j_config.password)
    )

    yield driver

    # Cleanup
    driver.close()


@pytest.fixture
def neo4j_session(neo4j_driver, neo4j_config):
    """
    Fixture providing Neo4j session

    Automatically closes session after test.

    Returns:
        neo4j.Session: Active Neo4j session
    """
    session = neo4j_driver.session(database=neo4j_config.database)

    yield session

    # Cleanup
    session.close()


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_customer_data():
    """
    Fixture providing sample customer data

    TODO: Customize for your API's customer structure

    Returns:
        dict: Sample customer API response
    """
    return {
        "guid": "customer-test-123",
        "name": "Test Customer Corp",
        "number": "CUST-001",
        "isActive": True,
        "createdDateTime": "2024-01-01T00:00:00Z",
        # TODO: Add nested objects if your API uses them
        # "address": {
        #     "street": "123 Test St",
        #     "city": "Test City"
        # },
        # "owner": {
        #     "guid": "user-test-456"
        # }
    }


@pytest.fixture
def sample_user_data():
    """
    Fixture providing sample user data

    TODO: Customize for your API's user structure

    Returns:
        dict: Sample user API response
    """
    return {
        "guid": "user-test-456",
        "email": "test.user@example.com",
        "firstName": "Test",
        "lastName": "User",
        "isActive": True,
        # TODO: Add nested objects if your API uses them
    }


@pytest.fixture
def sample_project_data():
    """
    Fixture providing sample project data

    TODO: Customize for your API's project structure

    Returns:
        dict: Sample project API response
    """
    return {
        "guid": "project-test-789",
        "name": "Test Project",
        "number": "PROJ-001",
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "isClosed": False,
        # TODO: Add foreign key references
        # "customer": {
        #     "guid": "customer-test-123"
        # },
        # "owner": {
        #     "guid": "user-test-456"
        # }
    }


# =============================================================================
# Database Cleanup Fixtures
# =============================================================================

@pytest.fixture
def cleanup_test_nodes(neo4j_session):
    """
    Fixture to cleanup test nodes after test

    Deletes all nodes with 'test' in their guid.
    Use when creating test data that needs cleanup.

    Usage:
        def test_example(neo4j_session, cleanup_test_nodes):
            # Create test nodes
            neo4j_session.run("CREATE (n:Customer {guid: 'customer-test-123'})")
            # Test logic here
            # Cleanup happens automatically after test
    """
    yield

    # Cleanup after test
    neo4j_session.run("""
        MATCH (n)
        WHERE n.guid CONTAINS 'test'
        DETACH DELETE n
    """)


@pytest.fixture
def empty_database(neo4j_session):
    """
    Fixture to ensure empty database for test

    WARNING: Deletes ALL data! Use carefully.
    Only for isolated integration tests.

    Usage:
        @pytest.mark.integration
        def test_full_sync(empty_database):
            # Database is empty at start
            # Run full sync
            # Verify results
    """
    # Delete all data before test
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    yield

    # Note: Not cleaning up after - might want to inspect results


# =============================================================================
# Parametrization Helpers
# =============================================================================

def generate_nested_object_test_cases():
    """
    Generate test cases for nested object extraction

    TODO: Add test cases for your API's nested object patterns

    Returns:
        list: Test cases with (api_response, expected_guid, description)
    """
    return [
        # Present nested object
        (
            {"customer": {"guid": "customer-123"}},
            "customer-123",
            "nested object present"
        ),
        # Missing nested object
        (
            {},
            None,
            "nested object missing"
        ),
        # Null nested object
        (
            {"customer": None},
            None,
            "nested object null"
        ),
        # Nested object without guid
        (
            {"customer": {"name": "Test"}},
            None,
            "nested object missing guid"
        ),
    ]


# =============================================================================
# Marks and Markers
# =============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "live: tests requiring live data from database"
    )
    config.addinivalue_line(
        "markers", "structural: tests for code structure and orchestration"
    )
    config.addinivalue_line(
        "markers", "integration: end-to-end integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take significant time to run"
    )
