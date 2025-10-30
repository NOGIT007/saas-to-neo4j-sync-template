"""
{PROJECT_NAME} Sync Package
===========================
Modular sync framework for syncing {API_NAME} data to Neo4j.

Package structure:
- config.py: Configuration dataclasses
- {api}_client.py: API client with pagination/retry
- neo4j_base.py: Base class for Neo4j operations
- orchestrator.py: Coordinates all sync operations
- entities/: Entity sync modules
- relationships/: Relationship creation modules
- metrics/: Metrics calculation modules
- analytics/: Time-series aggregation and denormalization
- migrations/: Schema migration modules
"""

__version__ = "0.1.0"
