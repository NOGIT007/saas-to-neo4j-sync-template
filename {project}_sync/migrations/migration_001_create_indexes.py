"""
Migration 001: Create indexes and constraints

Run after initial data sync to optimize query performance.
Indexes speed up common queries (filtering, searching, sorting).
Constraints ensure data integrity (uniqueness, node keys).

Execution:
1. Dry-run to plan: from migrations.migration_001_create_indexes import run_migration
                   result = run_migration(config, dry_run=True)
2. Apply: result = run_migration(config, dry_run=False)
3. Verify: SHOW INDEXES → check state (ONLINE vs POPULATING vs FAILED)

Rollback:
1. Drop individual indexes: DROP INDEX index_name
2. Drop constraints: DROP CONSTRAINT constraint_name
3. Manual: DELETE FROM neo4j schema without removing data

TODO: Customize for your {API_NAME}:
1. Add entity labels for your data model
2. Select frequently queried properties
3. Create composite indexes for common filter combinations
4. Add full-text indexes if searching text fields
5. Test index impact on query performance

Performance:
- Indexes add write overhead (INSERT/UPDATE/DELETE slightly slower)
- Benefits: Query read speed, typical ratio 10x-100x faster
- For reporting/analytics: worth the tradeoff
- Monitor: neo4j.metrics db hits/misses
"""
import logging
from typing import Dict
from ..neo4j_base import Neo4jBase
from ..config import Neo4jConfig

logger = logging.getLogger(__name__)


class IndexMigration(Neo4jBase):
    """Create indexes and constraints for performance

    Responsibilities:
    - Create unique constraints on GUID fields (Node Key)
    - Create indexes on frequently queried properties
    - Create composite indexes for multi-property filters
    - Create full-text indexes for text search
    - Support dry-run mode for planning
    - Report creation results
    """

    def __init__(self, config: Neo4jConfig, dry_run: bool = False):
        super().__init__(config)
        self.dry_run = dry_run
        self.stats = {
            "indexes_created": 0,
            "constraints_created": 0,
            "errors": []
        }

    def run(self) -> Dict[str, any]:
        """Execute all index/constraint creation

        Returns:
            Dict with stats:
            - indexes_created: count
            - constraints_created: count
            - errors: list of error messages
        """
        logger.info("=" * 80)
        logger.info("STARTING INDEX MIGRATION (001_create_indexes)")
        logger.info(f"Dry run mode: {self.dry_run}")
        logger.info("=" * 80)

        try:
            # Step 1: Unique constraints (also creates indexes)
            self._create_unique_constraints()

            # Step 2: Property indexes on frequently queried properties
            self._create_property_indexes()

            # Step 3: Composite indexes for multi-property filters
            self._create_composite_indexes()

            # Step 4: Full-text search indexes (optional)
            self._create_fulltext_indexes()

            # Step 5: Verify index creation
            self._verify_indexes()

            self._print_summary()
            return self.stats

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.stats["errors"].append(str(e))
            return self.stats

    def _create_unique_constraints(self):
        """Create unique constraints on GUID fields (also creates indexes)

        TODO: Customize for your {API_NAME}:
        1. Add entity labels from your schema
        2. Verify "guid" is the unique identifier (not "id" or "key")
        3. Add business key constraints (e.g., customer "number")
        4. Handle duplicate values: may need data cleanup first

        Typical entities: Customer, User, Project, Invoice, etc.
        """
        logger.info("\n1. Creating unique constraints (also creates indexes)...")

        # TODO: Add your entity types here
        constraints = [
            # ({Entity}, "guid") pairs - adjust based on your schema
            ("Customer", "guid"),
            ("User", "guid"),
            ("Project", "guid"),
            ("{Entity3}", "guid"),
            ("{Entity4}", "guid"),
            # Optional: business key constraints
            ("Customer", "number"),  # Customer reference number
        ]

        for label, property_name in constraints:
            constraint_name = f"{label}_{property_name}_unique"
            query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.{property_name} IS UNIQUE
            """
            self._execute_migration(query, f"UNIQUE {label}.{property_name}")

    def _create_property_indexes(self):
        """Create indexes on frequently queried properties

        TODO: Customize for your {API_NAME}:
        1. Identify common filters (status, date range, owner, etc.)
        2. Profile queries to find slow ones
        3. Add indexes for each commonly filtered property
        4. Start conservative (fewer indexes) then add as needed

        Common patterns:
        - Status fields: isActive, isClosed, isApproved
        - Dates: createdDate, modifiedDate, eventDate, deadline
        - References: ownerGuid, customerGuid, projectGuid
        - Search: name, email, description
        """
        logger.info("\n2. Creating property indexes...")

        # TODO: Add indexes for your frequently queried properties
        indexes = [
            # Customer indexes
            ("Customer", "number"),
            ("Customer", "name"),
            ("Customer", "isActive"),

            # User indexes
            ("User", "email"),
            ("User", "isActive"),
            ("User", "firstName"),
            ("User", "lastName"),

            # Project indexes
            ("Project", "isActive"),
            ("Project", "isClosed"),
            ("Project", "deadline"),
            ("Project", "customerGuid"),

            # TODO: Add more indexes for your entities
            # ("{Entity}", "{property}"),
        ]

        for label, property_name in indexes:
            index_name = f"{label}_{property_name}_idx"
            query = f"""
            CREATE INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON (n.{property_name})
            """
            self._execute_migration(query, f"INDEX {label}.{property_name}")

    def _create_composite_indexes(self):
        """Create composite indexes for multi-property queries

        TODO: Customize for your {API_NAME}:
        1. Find common multi-property filters
        2. Create indexes for frequently combined filters
        3. Example: Project queries often filter (isActive=true, deadline < date)
        4. Create composite index: (isActive, deadline)

        Composite Index Benefits:
        - Speed up queries with multiple filters
        - Reduce work: one index covers two properties
        - Order matters: (isActive, deadline) ≠ (deadline, isActive)
        """
        logger.info("\n3. Creating composite indexes...")

        # TODO: Add composite indexes for common multi-filter queries
        composite_indexes = [
            # ({Entity}, [properties], "index_name") tuples
            ("Project", ["isActive", "isClosed"], "project_status_idx"),
            ("User", ["firstName", "lastName"], "user_name_idx"),

            # TODO: Add more composite indexes for your queries
            # ("{Entity}", ["{property1}", "{property2}"], "{entity}_multi_idx"),
        ]

        for label, properties, index_name in composite_indexes:
            props_str = ", ".join([f"n.{p}" for p in properties])
            query = f"""
            CREATE INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON ({props_str})
            """
            self._execute_migration(query, f"COMPOSITE {label}.{'+'.join(properties)}")

    def _create_fulltext_indexes(self):
        """Create full-text search indexes

        TODO: Customize for your {API_NAME}:
        1. Identify text search fields (names, descriptions, notes)
        2. Create full-text indexes for better search
        3. Use: db.index.fulltext.queryNodes("index_name", "search query")

        Full-text Search Benefits:
        - Fuzzy matching: typos, case-insensitive
        - Stemming: search "run" finds "running", "runs"
        - Relevance scoring: rank by match quality
        """
        logger.info("\n4. Creating full-text search indexes...")

        # TODO: Add full-text indexes for searchable fields
        fulltext_indexes = [
            # ("index_name", ["Entity"], ["property"]) tuples
            ("customer_search", ["Customer"], ["name"]),
            ("user_search", ["User"], ["firstName", "lastName", "email"]),
            ("project_search", ["Project"], ["name"]),

            # TODO: Add more full-text indexes
            # ("{entity}_search", ["{Entity}"], ["{property}"]),
        ]

        for index_name, labels, properties in fulltext_indexes:
            labels_str = "`, `".join(labels)
            props_str = "`, `".join(properties)
            query = f"""
            CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
            FOR (n:`{labels_str}`)
            ON EACH [n.`{props_str.replace('`, `', '`, n.`')}`]
            """
            self._execute_migration(query, f"FULLTEXT {index_name}")

    def _verify_indexes(self):
        """Verify all indexes were created successfully

        Checks:
        1. Total indexes created
        2. Indexes in ONLINE state (ready for use)
        3. Any FAILED or POPULATING indexes (potential issues)
        """
        logger.info("\n5. Verifying indexes...")

        query = "SHOW INDEXES"
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query)
                indexes = [record["name"] for record in result]
                logger.info(f"  ✓ Total indexes: {len(indexes)}")

                # Check for non-ONLINE indexes
                result = session.run("SHOW INDEXES YIELD name, state WHERE state <> 'ONLINE'")
                pending = list(result)
                if pending:
                    logger.warning(f"  ⚠ Indexes not yet ONLINE: {len(pending)}")
                    for record in pending:
                        logger.warning(f"    - {record['name']}: {record['state']}")

        except Exception as e:
            logger.error(f"Failed to verify indexes: {e}")
            self.stats["errors"].append(f"Verification failed: {e}")

    def _execute_migration(self, query: str, description: str):
        """Execute a single migration statement

        Args:
            query: Cypher query to execute
            description: Human-readable description for logging
        """
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would create: {description}")
            return

        try:
            with self.driver.session(database=self.config.database) as session:
                session.run(query)
                logger.info(f"  ✓ Created: {description}")

                if "CONSTRAINT" in query:
                    self.stats["constraints_created"] += 1
                else:
                    self.stats["indexes_created"] += 1

        except Exception as e:
            # Check if index/constraint already exists (idempotent)
            if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                logger.info(f"  ⊙ Already exists: {description}")
            else:
                logger.error(f"  ✗ Failed to create {description}: {e}")
                self.stats["errors"].append(f"{description}: {e}")

    def _print_summary(self):
        """Print migration summary"""
        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Constraints created: {self.stats['constraints_created']}")
        logger.info(f"Indexes created:     {self.stats['indexes_created']}")
        logger.info(f"Errors:              {len(self.stats['errors'])}")
        if self.stats["errors"]:
            logger.error("Errors encountered:")
            for error in self.stats["errors"]:
                logger.error(f"  - {error}")
        logger.info("=" * 80 + "\n")


def run_migration(neo4j_config: Neo4jConfig, dry_run: bool = False):
    """Convenience function to run migration

    Args:
        neo4j_config: Neo4jConfig instance
        dry_run: If True, plan without applying

    Returns:
        Dict with migration stats
    """
    migration = IndexMigration(neo4j_config, dry_run=dry_run)
    return migration.run()
