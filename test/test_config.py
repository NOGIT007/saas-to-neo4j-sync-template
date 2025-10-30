"""
Configuration Tests

Tests for configuration loading, validation, and environment variable handling.

Run:
    pytest test/test_config.py -v

TODO: Customize for your specific API configuration requirements
"""

import pytest
import os
from unittest.mock import patch

# TODO: Update import paths to match your project
from {project}_sync.config import {API}Config, Neo4jConfig, SyncConfig


class TestAPIConfig:
    """Tests for {API_NAME} API configuration"""

    def test_api_config_from_env(self, monkeypatch):
        """Test loading API config from environment variables"""
        # TODO: Adjust for your API authentication method
        monkeypatch.setenv("{API_NAME}_URL", "https://test.api.com")
        monkeypatch.setenv("{API_NAME}_CLIENT_ID", "test_client")
        monkeypatch.setenv("{API_NAME}_CLIENT_SECRET", "test_secret")

        config = {API}Config()

        assert config.api_url == "https://test.api.com"
        assert config.client_id == "test_client"
        assert config.client_secret == "test_secret"

    def test_api_config_defaults(self):
        """Test default values when environment variables not set"""
        config = {API}Config()

        assert config.max_retries == 3
        assert config.batch_size == 100
        assert config.request_timeout == 60

    def test_api_config_validation_success(self, api_config):
        """Test validation passes with valid config"""
        assert api_config.validate() is True

    def test_api_config_validation_missing_url(self):
        """Test validation fails without API URL"""
        config = {API}Config(
            api_url="",
            client_id="test",
            client_secret="test"
        )

        with pytest.raises(ValueError, match="{API_NAME}_URL is required"):
            config.validate()

    def test_api_config_validation_missing_auth(self):
        """Test validation fails without authentication credentials"""
        config = {API}Config(
            api_url="https://api.example.com",
            client_id="",
            client_secret="",
            api_key=None
        )

        with pytest.raises(ValueError, match="OAuth credentials.*or API key.*is required"):
            config.validate()

    def test_api_config_oauth_auth(self):
        """Test config with OAuth authentication"""
        config = {API}Config(
            api_url="https://api.example.com",
            client_id="test_client",
            client_secret="test_secret"
        )

        assert config.validate() is True

    def test_api_config_api_key_auth(self):
        """Test config with API key authentication"""
        config = {API}Config(
            api_url="https://api.example.com",
            client_id="",
            client_secret="",
            api_key="test_api_key"
        )

        assert config.validate() is True

    def test_api_config_custom_timeouts(self, monkeypatch):
        """Test custom timeout and retry settings"""
        monkeypatch.setenv("SYNC_MAX_RETRIES", "5")
        monkeypatch.setenv("SYNC_REQUEST_TIMEOUT", "120")

        config = {API}Config()

        assert config.max_retries == 5
        assert config.request_timeout == 120


class TestNeo4jConfig:
    """Tests for Neo4j configuration"""

    def test_neo4j_config_from_env(self, monkeypatch):
        """Test loading Neo4j config from environment variables"""
        monkeypatch.setenv("NEO4J_URI", "bolt://test:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "test_user")
        monkeypatch.setenv("NEO4J_PASSWORD", "test_pass")
        monkeypatch.setenv("NEO4J_DATABASE", "test_db")

        config = Neo4jConfig()

        assert config.uri == "bolt://test:7687"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.database == "test_db"

    def test_neo4j_config_defaults(self):
        """Test default values"""
        config = Neo4jConfig()

        assert config.database == "neo4j"

    def test_neo4j_config_validation_success(self, neo4j_config):
        """Test validation passes with valid config"""
        assert neo4j_config.validate() is True

    def test_neo4j_config_validation_missing_uri(self):
        """Test validation fails without URI"""
        config = Neo4jConfig(
            uri="",
            username="test",
            password="test"
        )

        with pytest.raises(ValueError, match="NEO4J_URI is required"):
            config.validate()

    def test_neo4j_config_validation_missing_username(self):
        """Test validation fails without username"""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="",
            password="test"
        )

        with pytest.raises(ValueError, match="NEO4J_USERNAME is required"):
            config.validate()

    def test_neo4j_config_validation_missing_password(self):
        """Test validation fails without password"""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="test",
            password=""
        )

        with pytest.raises(ValueError, match="NEO4J_PASSWORD is required"):
            config.validate()


class TestSyncConfig:
    """Tests for sync configuration"""

    def test_sync_config_defaults(self):
        """Test default sync configuration values"""
        config = SyncConfig()

        assert config.default_days_back == 365
        assert config.enable_metrics is True
        assert config.enable_analytics is True
        assert config.create_indexes is True

    def test_sync_config_from_env(self, monkeypatch):
        """Test loading sync config from environment variables"""
        monkeypatch.setenv("SYNC_DEFAULT_DAYS_BACK", "730")
        monkeypatch.setenv("SYNC_ENABLE_METRICS", "false")
        monkeypatch.setenv("SYNC_ENABLE_ANALYTICS", "false")
        monkeypatch.setenv("SYNC_CREATE_INDEXES", "false")

        config = SyncConfig()

        assert config.default_days_back == 730
        assert config.enable_metrics is False
        assert config.enable_analytics is False
        assert config.create_indexes is False

    def test_get_entity_days_back_default(self):
        """Test getting days back for entity uses default"""
        config = SyncConfig(default_days_back=365)

        days_back = config.get_entity_days_back("transactions")

        assert days_back == 365

    def test_get_entity_days_back_custom(self, monkeypatch):
        """Test getting custom days back for specific entity"""
        # TODO: Adjust entity name for your transactional data types
        monkeypatch.setenv("SYNC_TRANSACTIONS_DAYS_BACK", "90")

        config = SyncConfig()

        days_back = config.get_entity_days_back("transactions")

        assert days_back == 90

    def test_get_entity_start_date_none(self):
        """Test getting start date returns None when not set"""
        config = SyncConfig()

        start_date = config.get_entity_start_date("transactions")

        assert start_date is None

    def test_get_entity_start_date_custom(self, monkeypatch):
        """Test getting custom start date for specific entity"""
        # TODO: Adjust entity name for your transactional data types
        monkeypatch.setenv("SYNC_TRANSACTIONS_START_DATE", "2020-01-01")

        config = SyncConfig()

        start_date = config.get_entity_start_date("transactions")

        assert start_date == "2020-01-01"

    def test_sync_config_boolean_parsing(self, monkeypatch):
        """Test boolean environment variable parsing"""
        # Test various boolean string formats
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("anything_else", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("SYNC_ENABLE_METRICS", env_value)
            config = SyncConfig()
            assert config.enable_metrics is expected


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for configuration with real environment"""

    def test_all_configs_validate_together(self, api_config, neo4j_config, sync_config):
        """Test all configurations validate successfully together"""
        # This would typically be done in orchestrator initialization

        assert api_config.validate() is True
        assert neo4j_config.validate() is True
        # SyncConfig has no validate method - just check it exists
        assert sync_config.default_days_back > 0

    def test_config_from_dotenv(self):
        """
        Test loading configuration from .env file

        TODO: This test requires a .env file in your project root
        Run this manually to verify .env loading works correctly
        """
        from dotenv import load_dotenv
        load_dotenv()

        # Try to create configs from environment
        api_config = {API}Config()
        neo4j_config = Neo4jConfig()

        # Basic sanity checks
        assert api_config.api_url
        assert neo4j_config.uri

        # Note: Don't validate here - might not have all credentials in CI/CD
