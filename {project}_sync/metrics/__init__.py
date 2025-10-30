"""
Metrics calculation modules - compute KPIs and aggregations

Metrics are calculated inline during sync - no separate maintenance jobs needed.
Calculated values are stored as properties on entity nodes.

Metrics Modules:
- project_metrics.py: Calculate {Entity}Metrics (revenue, hours, margin, etc.)

Pattern:
1. Inherit from Neo4jBase
2. calculate_*() method takes optional entity_guids list
3. MATCH entities and their related data
4. Aggregate values with Cypher (sum, count, avg, etc.)
5. SET calculated properties on entity nodes
6. RETURN count of updated entities

Example Workflow:
1. Sync all WorkHours for a Project
2. Call calculate_project_metrics(project_guids=["p-123"])
3. Query aggregates hours, revenue, cost from related entities
4. SET calculated properties on Project node
5. Return count of updated projects
"""
