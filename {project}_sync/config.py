"""
Configuration Management
========================
Dataclasses for managing configuration from environment variables.

TODO: Customize for your specific API
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class {API}Config:
    """
    {API_NAME} API configuration

    Loaded from environment variables with sensible defaults.

    Required environment variables:
    - {API_NAME}_URL: API base URL
    - {API_NAME}_CLIENT_ID: OAuth client ID
    - {API_NAME}_CLIENT_SECRET: OAuth client secret

    Optional environment variables:
    - {API_NAME}_API_KEY: API key (if using key-based auth instead of OAuth)
    - SYNC_MAX_RETRIES: Maximum retry attempts (default: 3)
    - SYNC_BATCH_SIZE: Batch size for bulk operations (default: 100)
    - SYNC_REQUEST_TIMEOUT: Request timeout in seconds (default: 60)

    TODO: Customize fields for your API authentication method
    """

    # API connection
    api_url: str = os.getenv("{API_NAME}_URL", "https://api.example.com/v1")

    # OAuth credentials (TODO: adjust for your auth method)
    client_id: str = os.getenv("{API_NAME}_CLIENT_ID", "")
    client_secret: str = os.getenv("{API_NAME}_CLIENT_SECRET", "")

    # Alternative: API key authentication
    api_key: Optional[str] = os.getenv("{API_NAME}_API_KEY")

    # Runtime state
    token: Optional[str] = None  # OAuth token set after authentication

    # Request configuration
    max_retries: int = int(os.getenv("SYNC_MAX_RETRIES", "3"))
    batch_size: int = int(os.getenv("SYNC_BATCH_SIZE", "100"))
    request_timeout: int = int(os.getenv("SYNC_REQUEST_TIMEOUT", "60"))

    def validate(self) -> bool:
        """
        Validate required configuration is present

        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        if not self.api_url:
            raise ValueError("{API_NAME}_URL is required")

        # Check authentication method
        has_oauth = self.client_id and self.client_secret
        has_api_key = self.api_key

        if not (has_oauth or has_api_key):
            raise ValueError(
                "Either OAuth credentials ({API_NAME}_CLIENT_ID, {API_NAME}_CLIENT_SECRET) "
                "or API key ({API_NAME}_API_KEY) is required"
            )

        return True


@dataclass
class Neo4jConfig:
    """
    Neo4j database configuration

    Loaded from environment variables with sensible defaults.

    Required environment variables:
    - NEO4J_URI: Connection URI (e.g., bolt://localhost:7687)
    - NEO4J_USERNAME: Database username
    - NEO4J_PASSWORD: Database password

    Optional environment variables:
    - NEO4J_DATABASE: Database name (default: neo4j)
    """

    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    def validate(self) -> bool:
        """
        Validate required configuration is present

        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        if not self.uri:
            raise ValueError("NEO4J_URI is required")
        if not self.username:
            raise ValueError("NEO4J_USERNAME is required")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD is required")

        return True


@dataclass
class SyncConfig:
    """
    Sync operation configuration

    Optional configuration for controlling sync behavior.

    Optional environment variables:
    - SYNC_{ENTITY}_DAYS_BACK: Lookback period for transactional data (default: 365)
    - SYNC_{ENTITY}_START_DATE: Fixed start date for historical backfill (YYYY-MM-DD)
    - SYNC_ENABLE_METRICS: Enable metrics calculation (default: true)
    - SYNC_ENABLE_ANALYTICS: Enable analytics aggregation (default: true)
    - SYNC_CREATE_INDEXES: Create indexes on startup (default: true)

    TODO: Add configuration options specific to your sync needs
    """

    # Date range configuration for transactional data
    # Example: SYNC_TRANSACTIONS_DAYS_BACK, SYNC_EVENTS_DAYS_BACK
    default_days_back: int = int(os.getenv("SYNC_DEFAULT_DAYS_BACK", "365"))

    # Feature flags
    enable_metrics: bool = os.getenv("SYNC_ENABLE_METRICS", "true").lower() == "true"
    enable_analytics: bool = os.getenv("SYNC_ENABLE_ANALYTICS", "true").lower() == "true"
    create_indexes: bool = os.getenv("SYNC_CREATE_INDEXES", "true").lower() == "true"

    def get_entity_days_back(self, entity_name: str) -> int:
        """
        Get days back for specific entity type

        Args:
            entity_name: Entity name (e.g., "transactions", "events")

        Returns:
            int: Days to look back
        """
        env_var = f"SYNC_{entity_name.upper()}_DAYS_BACK"
        return int(os.getenv(env_var, str(self.default_days_back)))

    def get_entity_start_date(self, entity_name: str) -> Optional[str]:
        """
        Get fixed start date for specific entity type

        Args:
            entity_name: Entity name (e.g., "transactions", "events")

        Returns:
            Optional[str]: Start date in YYYY-MM-DD format, or None
        """
        env_var = f"SYNC_{entity_name.upper()}_START_DATE"
        return os.getenv(env_var)
