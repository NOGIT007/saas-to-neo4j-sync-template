"""
Customer entity sync module

Syncs Customer entities from {API_NAME} to Neo4j.

Pattern Implementation:
- Inherits from Neo4jBase for Neo4j operations
- sync_customer() method handles single entity sync
- MERGE on guid (NODE KEY) to avoid duplicates
- Stores only primitive values and foreign GUIDs
- Returns bool indicating success/failure
- Nested object extraction follows "{Entity} in {API_NAME} is a nested object" pattern

TODO: Customize for your {API_NAME}:
1. Add/remove properties from MERGE query based on {API_NAME} schema
2. Extract nested object GUIDs (e.g., customer.businessUnit.guid)
3. Validate field names match {API_NAME} API response
4. Check doc/{api}_doc.json for "$ref" fields to identify nested objects
"""
from typing import Dict, Any
from ..neo4j_base import Neo4jBase


class CustomerSync(Neo4jBase):
    """Handles syncing Customer entities from {API_NAME} to Neo4j

    Responsibilities:
    - Extract customer data from {API_NAME}
    - Create/update Customer nodes with MERGE
    - Store foreign GUIDs as properties only (no inline entity creation)

    Related:
    - Relationships: customer_relationships.py creates Customer→Project, Customer→Contact, etc.
    - Metrics: Not applicable for reference data
    """

    def sync_customer(self, customer_data: Dict[str, Any]) -> bool:
        """Sync a single customer to Neo4j

        Creates or updates a Customer node with properties from {API_NAME}.
        Only stores customer attributes and foreign GUIDs - does not create
        related entities inline.

        Pattern:
        1. MERGE on guid (NODE KEY) - ensures idempotency
        2. SET properties with customer data
        3. Extract nested object GUIDs (e.g., customer.businessUnit.guid)
        4. Store GUIDs as properties, not as relationships

        Args:
            customer_data: Dict with customer entity from {API_NAME} API
                          Expected keys: guid, name, number, isActive, etc.

        Returns:
            bool: True if sync succeeded, False on error

        TODO: Common nested objects in {API_NAME}:
        - businessUnit: Extract GUID and store as businessUnitGuid property
        - accountOwner: Extract GUID and store as accountOwnerGuid property
        - marketSegments: Handle as many-to-many (separate sync method)

        Example {API_NAME} response:
        {{
            "guid": "abc-123",
            "name": "Acme Corp",
            "number": "C-001",
            "isActive": true,
            "businessUnit": {{"guid": "bu-456", "name": "Engineering"}},
            "accountOwner": {{"guid": "user-789", "firstName": "John"}},
            "lastModifiedDateTime": "2025-01-15T10:30:00Z"
        }}
        """
        query = """
        MERGE (c:Customer {guid: $guid})
        SET
            c.name = $name,
            c.number = $number,
            c.isActive = $isActive,
            c.businessUnitGuid = $businessUnitGuid,
            c.accountOwnerGuid = $accountOwnerGuid,
            c.lastModified = $lastModified
        RETURN c.guid AS guid
        """

        # TODO: Extract nested object GUIDs following this pattern
        # Check for nested object existence before accessing properties
        business_unit_guid = None
        if customer_data.get("businessUnit"):
            business_unit_guid = customer_data["businessUnit"].get("guid")

        account_owner_guid = None
        if customer_data.get("accountOwner"):
            account_owner_guid = customer_data["accountOwner"].get("guid")

        return self._execute_query(query, {
            "guid": customer_data.get("guid"),
            "name": customer_data.get("name", ""),
            "number": customer_data.get("number", ""),
            "isActive": customer_data.get("isActive", True),
            "businessUnitGuid": business_unit_guid,
            "accountOwnerGuid": account_owner_guid,
            "lastModified": customer_data.get("lastModifiedDateTime", "")
        })

    # TODO: Add more entity sync methods following the same pattern
    # Example:
    # def sync_contact_person(self, contact_data: Dict[str, Any]) -> bool:
    #     """Sync ContactPerson entity - follows same pattern as sync_customer"""
    #     pass
