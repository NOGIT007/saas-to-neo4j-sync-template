"""
Neo4j Base Class
================
Base class for all Neo4j operations providing connection management and common utilities.

All entity sync, relationship, and metrics modules should inherit from this class.
"""

import logging
from typing import Dict, List, Any
from neo4j import GraphDatabase, Driver

from .config import Neo4jConfig

logger = logging.getLogger(__name__)


class Neo4jBase:
    """
    Base class for Neo4j operations

    Provides:
    - Connection management with connection pooling
    - Common query execution methods
    - Batch operation utilities
    - Error handling patterns

    All modules that interact with Neo4j should inherit from this class.

    Example usage:
        class CustomerSync(Neo4jBase):
            def sync_customer(self, data: Dict) -> bool:
                query = "MERGE (c:Customer {guid: $guid})"
                return self._execute_query(query, {"guid": data["guid"]})
    """

    def __init__(self, config: Neo4jConfig):
        """
        Initialize Neo4j connection

        Args:
            config: Neo4j configuration
        """
        self.config = config
        self.driver: Driver = None
        self.connect()

    def connect(self):
        """
        Establish connection to Neo4j database

        Creates driver with connection pooling.
        Connection is reused across all queries.
        """
        logger.info(f"Connecting to Neo4j at {self.config.uri}...")

        self.driver = GraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password)
        )

        # Test connection
        with self.driver.session(database=self.config.database) as session:
            result = session.run("RETURN 1 as test")
            result.single()

        logger.info("✓ Connected to Neo4j")

    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    # =========================================================================
    # Query Execution
    # =========================================================================

    def _execute_query(self, query: str, parameters: Dict[str, Any]) -> bool:
        """
        Execute single Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters (always use parameterized queries!)

        Returns:
            bool: True if successful
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters)
                result.consume()  # Consume result to complete query
            return True

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Parameters: {parameters}")
            raise

    def _execute_query_with_result(self, query: str, parameters: Dict[str, Any]) -> List[Dict]:
        """
        Execute query and return results

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Parameters: {parameters}")
            raise

    def _execute_batch(self, queries: List[Dict[str, Any]]) -> int:
        """
        Execute multiple queries in a single transaction

        Useful for bulk operations. All queries succeed or all fail (ACID).

        Args:
            queries: List of dicts with "query" and "parameters" keys
                Example: [
                    {"query": "CREATE (n:Node {id: $id})", "parameters": {"id": 1}},
                    {"query": "CREATE (n:Node {id: $id})", "parameters": {"id": 2}}
                ]

        Returns:
            int: Number of queries executed
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                with session.begin_transaction() as tx:
                    for query_obj in queries:
                        query = query_obj["query"]
                        parameters = query_obj.get("parameters", {})
                        tx.run(query, parameters)
                    tx.commit()

            return len(queries)

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise

    # =========================================================================
    # Batch Utilities
    # =========================================================================

    def batch_merge_nodes(
        self,
        label: str,
        items: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        Batch merge nodes using UNWIND for performance

        Example:
            items = [
                {"guid": "123", "name": "Customer A"},
                {"guid": "456", "name": "Customer B"}
            ]
            count = self.batch_merge_nodes("Customer", items)

        Args:
            label: Node label
            items: List of node properties
            batch_size: Number of nodes per batch

        Returns:
            int: Total nodes merged
        """
        if not items:
            return 0

        total_merged = 0

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # Build property SET clause dynamically
            # Assumes first item has all properties
            if not batch:
                continue

            sample_item = batch[0]
            set_clauses = [f"n.{key} = item.{key}" for key in sample_item.keys() if key != "guid"]
            set_clause = ", ".join(set_clauses) if set_clauses else "n.guid = item.guid"

            query = f"""
            UNWIND $batch AS item
            MERGE (n:{label} {{guid: item.guid}})
            SET {set_clause}
            """

            try:
                with self.driver.session(database=self.config.database) as session:
                    result = session.run(query, {"batch": batch})
                    summary = result.consume()
                    merged = summary.counters.nodes_created + summary.counters.properties_set
                    total_merged += len(batch)

            except Exception as e:
                logger.error(f"Batch merge failed for {label}: {e}")
                raise

        logger.info(f"  Merged {total_merged} {label} nodes")
        return total_merged

    # =========================================================================
    # Utilities
    # =========================================================================

    def extract_nested_guid(self, data: Dict, nested_field: str) -> str:
        """
        Safely extract GUID from nested API object

        CRITICAL PATTERN: API responses often have nested objects, not flat fields.

        Example API response:
            {
                "guid": "project-123",
                "name": "Project A",
                "customer": {              # Nested object
                    "guid": "customer-456",
                    "name": "Customer B"
                }
            }

        Usage:
            customer_guid = self.extract_nested_guid(data, "customer")

        Args:
            data: API response dict
            nested_field: Name of nested field

        Returns:
            str: GUID if found, None otherwise
        """
        nested_obj = data.get(nested_field)
        if nested_obj and isinstance(nested_obj, dict):
            return nested_obj.get("guid")
        return None
