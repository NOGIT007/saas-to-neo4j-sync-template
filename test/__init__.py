"""
Test Package
============
Comprehensive test suite for {PROJECT_NAME} sync framework.

Test organization:
- test_config.py: Configuration validation
- test_api_client.py: API client functionality
- test_entity_sync.py: Entity sync modules
- test_relationships.py: Relationship creation
- test_orchestrator.py: Orchestration coverage
- test_integration.py: End-to-end tests (requires live data)

Test markers:
- @pytest.mark.live: Requires live database connection
- @pytest.mark.integration: Integration tests
- @pytest.mark.unit: Unit tests (isolated)

Run tests:
    pytest -v -m "not live"  # Structural tests only
    pytest -v                # All tests (requires synced data)
"""
