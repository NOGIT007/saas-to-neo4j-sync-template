"""
Customer relationship creation module

Creates relationships for Customer entities:
- Customer → Project (HAS_PROJECT)
- Customer → Contact (HAS_CONTACT)
- Customer → Address (HAS_ADDRESS)
- Customer → Invoice (HAS_INVOICE)

Pattern Implementation:
- Inherits from Neo4jBase for Neo4j operations
- One method per relationship type
- MATCH both entities, MERGE relationship
- Return count for verification
- All methods called from orchestrator.py

TODO: Customize for your {API_NAME}:
1. Create methods for your entity relationships
2. Verify GUID properties are stored in entity nodes
3. Update orchestrator.py to call these methods
4. Use grep to verify: grep "create_.*_relationships()" orchestrator.py | wc -l
"""
import logging
from ..neo4j_base import Neo4jBase

logger = logging.getLogger(__name__)


class CustomerRelationships(Neo4jBase):
    """Handles creating relationships for Customer entities

    Responsibilities:
    - Connect Customer to Project entities
    - Connect Customer to Contact entities
    - Connect Customer to Address entities
    - Connect Customer to Invoice entities

    All relationships are created after entities are synced.
    Relationships are based on foreign GUIDs stored as properties.

    Example Workflow:
    1. Entities sync: Customer {guid: "c-123", name: "Acme"}
                      Project {guid: "p-456", customerGuid: "c-123", name: "BuildApp"}
    2. Relationships sync: MATCH (p:Project WHERE p.customerGuid = "c-123")
                          MATCH (c:Customer {guid: "c-123"})
                          MERGE (c)-[r:HAS_PROJECT]->(p)
    """

    def create_customer_project_relationships(self) -> int:
        """Create HAS_PROJECT relationships between Customers and Projects

        Pattern:
        - MATCH projects with customerGuid property
        - MATCH customer with that guid
        - MERGE relationship to avoid duplicates
        - RETURN count for verification

        Returns:
            int: Number of relationships created/found
        """
        query = """
        MATCH (p:{Entity2})
        WHERE p.customerGuid IS NOT NULL
        MATCH (c:Customer {guid: p.customerGuid})
        MERGE (c)-[r:HAS_{ENTITY2}]->(p)
        RETURN count(r) as count
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query)
                record = result.single()
                count = record["count"] if record else 0
                logger.info(f"  Created {count} Customer→{Entity2} relationships")
                return count
        except Exception as e:
            logger.error(f"Failed to create Customer→{Entity2} relationships: {e}")
            return 0

    def create_customer_contact_relationships(self) -> int:
        """Create HAS_CONTACT relationships between Customers and Contact entities

        Pattern: Same as create_customer_project_relationships()
        - Contact entities have customerGuid property
        - Match and create relationships

        TODO: Verify contact entity name and relationship type for your {API_NAME}:
        - Is it ContactPerson, Contact, or something else?
        - Is it HAS_CONTACT or HAS_CONTACT_PERSON?
        - Check doc/{api}_doc.json for correct names

        Returns:
            int: Number of relationships created/found
        """
        query = """
        MATCH (cp:ContactPerson)
        WHERE cp.customerGuid IS NOT NULL
        MATCH (c:Customer {guid: cp.customerGuid})
        MERGE (c)-[r:HAS_CONTACT]->(cp)
        RETURN count(r) as count
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query)
                record = result.single()
                count = record["count"] if record else 0
                logger.info(f"  Created {count} Customer→ContactPerson relationships")
                return count
        except Exception as e:
            logger.error(f"Failed to create Customer→ContactPerson relationships: {e}")
            return 0

    def create_customer_address_relationships(self) -> int:
        """Create HAS_ADDRESS relationships between Customers and Addresses

        Pattern: Same as create_customer_project_relationships()
        - Address entities have customerGuid property
        - Match and create relationships

        TODO: Verify address entity name for your {API_NAME}

        Returns:
            int: Number of relationships created/found
        """
        query = """
        MATCH (a:Address)
        WHERE a.customerGuid IS NOT NULL
        MATCH (c:Customer {guid: a.customerGuid})
        MERGE (c)-[r:HAS_ADDRESS]->(a)
        RETURN count(r) as count
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query)
                record = result.single()
                count = record["count"] if record else 0
                logger.info(f"  Created {count} Customer→Address relationships")
                return count
        except Exception as e:
            logger.error(f"Failed to create Customer→Address relationships: {e}")
            return 0

    def create_customer_invoice_relationships(self) -> int:
        """Create HAS_INVOICE relationships between Customers and Invoices

        Pattern: Same as create_customer_project_relationships()
        - Invoice entities have customerGuid property
        - Match and create relationships

        TODO: Verify invoice entity name for your {API_NAME}

        Returns:
            int: Number of relationships created/found
        """
        query = """
        MATCH (i:Invoice)
        WHERE i.customerGuid IS NOT NULL
        MATCH (c:Customer {guid: i.customerGuid})
        MERGE (c)-[r:HAS_INVOICE]->(i)
        RETURN count(r) as count
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query)
                record = result.single()
                count = record["count"] if record else 0
                logger.info(f"  Created {count} Customer→Invoice relationships")
                return count
        except Exception as e:
            logger.error(f"Failed to create Customer→Invoice relationships: {e}")
            return 0

    # TODO: Add more relationship methods following the same pattern
    # Example:
    # def create_customer_market_segment_relationships(self) -> int:
    #     """Create Customer→MarketSegment relationships via junction table
    #
    #     For many-to-many relationships:
    #     - Create junction node entity first (e.g., CustomerMarketSegment)
    #     - Then create relationships through junction
    #     - This represents proper graph structure for complex relationships
    #     """
    #     pass
