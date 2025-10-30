"""
Analytics modules - time-series aggregation and denormalization for reporting

Analytics enhance graph database for fast queries and reporting dashboards.

Analytics Modules:
- aggregation_nodes.py: Create time-period nodes (Year, Quarter, Month, Day)
- denormalization.py: Denormalize frequently accessed data

Pattern:
1. Inherit from Neo4jBase
2. Create helper entities: Year, Quarter, Month, Day nodes
3. Create RECORDED_IN relationships for fact nodes (WorkHour, Invoice)
4. Denormalize cached properties for dashboard performance
5. Support incremental updates

Example Workflow:
1. Create time-period hierarchy: 2025→Q1→January→Day1
2. WorkHour "2025-01-15": RECORDED_IN Month node
3. Denormalize: Month has totalHours, totalRevenue cached
4. Dashboard queries: MATCH (m:Month) RETURN m.totalRevenue (no aggregation)

Rationale:
- Time-period nodes provide fast period filtering
- Denormalized properties speed up dashboards
- Incremental updates only recalculate affected periods
"""
