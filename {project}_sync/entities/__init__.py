"""
Entity sync modules - synchronize {API_NAME} entities to Neo4j

Each module handles syncing a specific entity type from {API_NAME} to Neo4j.
Entities are created independently, storing only foreign GUIDs as properties.
Relationships are created separately in the relationships/ package.

Entity Modules:
- customer.py: Sync Customer entities
- user.py: Sync User entities
- {entity3}.py: TODO - Sync {Entity3} entities
- {entity4}.py: TODO - Sync {Entity4} entities

Pattern:
1. Inherit from Neo4jBase
2. One sync method per entity type (sync_{entity}())
3. MERGE on NODE KEY (typically guid)
4. Store only primitive values and foreign GUIDs
5. Return bool indicating success/failure
"""
