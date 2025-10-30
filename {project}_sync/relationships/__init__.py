"""
Relationship creation modules - connect entities in the Neo4j graph

Each module handles creating relationships between entity types.
Relationships are created after all entities are synced.

Relationship Modules:
- customer_relationships.py: Create Customer→Project, Customer→Contact, etc.
- project_relationships.py: TODO - Create Project→Phase, Project→Owner, etc.
- other_relationships.py: TODO - Create cross-entity relationships

Pattern:
1. Inherit from Neo4jBase
2. One method per relationship type (create_*_relationships())
3. MATCH both entities by guid properties stored in source entity
4. MERGE relationship to avoid duplicates
5. Return count of created relationships

Example:
- Customer has projectGuids → create HAS_PROJECT relationships
- Project has ownerGuid → create MANAGED_BY relationships
- WorkHour has userGuid → create LOGGED_BY relationships
"""
