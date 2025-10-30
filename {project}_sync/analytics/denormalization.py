"""
Denormalization module - cache aggregated metrics on nodes for fast dashboard queries

Rationale:
- Graph queries with aggregations can be slow for large datasets
- Denormalizing cached values trades storage for query speed
- Dashboard queries return pre-calculated values instead of aggregating

Pattern Implementation:
- Inherit from Neo4jBase for Neo4j operations
- calculate_period_metrics() aggregates and stores on time-period nodes
- Support incremental updates (specific periods or all)
- Methods match metrics/ module pattern but write to different nodes

TODO: Customize for your {API_NAME}:
1. Determine which metrics to denormalize (revenue, hours, cost, etc.)
2. Decide aggregation levels (daily/monthly/quarterly/yearly)
3. Implement incremental updates based on data sync intervals
4. Schedule recalculation: hourly, daily, or with each sync
5. Monitor cache staleness if near real-time accuracy required

Benefits:
- Dashboard: MATCH (m:Month) RETURN m.totalHours (instant)
- vs Without: MATCH (m:Month)-[r:RECORDED_IN]-(wh:WorkHour) RETURN sum(wh.quantity)
- Complexity: Simple property access vs complex aggregation
- Scale: O(1) vs O(n) where n = records in period

Trade-offs:
+ Fast dashboard queries
+ Simple visualization queries
- Additional storage for cached properties
- Staleness if not updated frequently
"""
import logging
from typing import List, Optional
from ..neo4j_base import Neo4jBase

logger = logging.getLogger(__name__)


class Denormalization(Neo4jBase):
    """Handles denormalizing metrics onto time-period and entity nodes

    Responsibilities:
    - Calculate period-level metrics (Month, Quarter, Year)
    - Store aggregated values as properties
    - Support incremental updates
    - Enable fast dashboard queries

    Denormalized Properties:
    - totalHours: Sum of WorkHour.quantity for period
    - billableHours: Sum of billable WorkHour.quantity
    - totalRevenue: Sum of Invoice.amount for period
    - totalCost: Sum of (WorkHour.quantity * unitCost)
    - projectCount: Count of unique projects in period
    - userCount: Count of unique users in period
    - lastDenormalizedAt: Timestamp of calculation

    Example:
    Month(2025-01) {
        totalHours: 456.5,
        billableHours: 412.0,
        totalRevenue: 45600.00,
        totalCost: 22800.00,
        margin: 22800.00,
        lastDenormalizedAt: "2025-01-31T23:59:00Z"
    }
    """

    def calculate_period_metrics(self, period_type: str = "month", periods: Optional[List[str]] = None) -> int:
        """Calculate and denormalize metrics on time-period nodes

        Aggregates work hours and invoices linked to periods, stores as properties.

        TODO: Implement aggregation for your metrics:
        1. For each period node (Month, Quarter, Year)
        2. MATCH related fact entities (WorkHour, Invoice)
        3. Aggregate: sum(hours), sum(revenue), sum(cost)
        4. SET denormalized properties
        5. RETURN count of updated periods

        Args:
            period_type: "month", "quarter", or "year"
            periods: Optional list of specific period IDs to update
                    (e.g., ["2025-01", "2025-02"] for months)
                    If None, updates all periods

        Returns:
            int: Number of periods updated
        """
        if periods is not None and len(periods) == 0:
            return 0

        # TODO: Customize for your {API_NAME}
        # This is a template query - adjust based on:
        # - Fact entity names (WorkHour, TimeEntry, etc.)
        # - Revenue source (Invoice, TimeTracking, etc.)
        # - Cost calculation method
        where_clause = f"WHERE p.id IN $periods" if periods else ""
        params = {"periods": periods} if periods else {}

        query = f"""
        MATCH (p:{period_type.capitalize()})
        {where_clause}

        // TODO: Aggregate work hours linked to this period
        // Adjust RECORDED_IN relationship and properties as needed
        OPTIONAL MATCH (p)<-[:RECORDED_IN]-(wh:WorkHour)
        WITH p,
             sum(wh.quantity) as totalHours,
             sum(CASE WHEN wh.isBillable THEN wh.quantity ELSE 0 END) as billableHours,
             sum(CASE WHEN NOT wh.isBillable THEN wh.quantity ELSE 0 END) as nonBillableHours,
             sum(wh.quantity * COALESCE(wh.unitCost, 0)) as totalCost

        // TODO: Aggregate revenue linked to this period
        // Adjust RECORDED_IN relationship and properties as needed
        OPTIONAL MATCH (p)<-[:RECORDED_IN]-(inv:Invoice)
        WITH p, totalHours, billableHours, nonBillableHours, totalCost,
             sum(inv.totalAmount) as totalRevenue

        // TODO: Count unique projects and users (optional)
        OPTIONAL MATCH (p)<-[:RECORDED_IN]-(wh2:WorkHour)-[:LOGGED_BY]-(u:User)
        WITH p, totalHours, billableHours, nonBillableHours, totalCost, totalRevenue,
             count(DISTINCT u.guid) as uniqueUsers

        OPTIONAL MATCH (p)<-[:RECORDED_IN]-(wh3:WorkHour)-[:FOR_PROJECT]-(proj:Project)
        WITH p, totalHours, billableHours, nonBillableHours, totalCost, totalRevenue, uniqueUsers,
             count(DISTINCT proj.guid) as uniqueProjects

        // TODO: Step 5 - Set denormalized properties
        SET p.totalHours = COALESCE(totalHours, 0),
            p.billableHours = COALESCE(billableHours, 0),
            p.nonBillableHours = COALESCE(nonBillableHours, 0),
            p.totalCost = COALESCE(totalCost, 0),
            p.totalRevenue = COALESCE(totalRevenue, 0),
            p.margin = COALESCE(totalRevenue, 0) - COALESCE(totalCost, 0),
            p.marginPct = CASE
                WHEN totalRevenue > 0
                THEN ((totalRevenue - COALESCE(totalCost, 0)) / totalRevenue) * 100
                ELSE 0
            END,
            p.uniqueUsers = COALESCE(uniqueUsers, 0),
            p.uniqueProjects = COALESCE(uniqueProjects, 0),
            p.lastDenormalizedAt = datetime()

        RETURN count(p) as periodCount
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, params)
                record = result.single()
                count = record["periodCount"] if record else 0
                logger.info(f"  ✓ Denormalized {count} {period_type.capitalize()} metrics")
                return count
        except Exception as e:
            logger.error(f"Failed to calculate {period_type} metrics: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            return 0

    def calculate_customer_summaries(self, customer_guids: Optional[List[str]] = None) -> int:
        """Denormalize Customer-level metrics

        Aggregates project revenue, hours, and costs per customer.

        TODO: Implement based on your entity relationships:
        - Customer-Project-WorkHour-User relationships
        - Revenue from invoices or work hours
        - Adjust based on your {API_NAME} schema

        Args:
            customer_guids: Optional list of customer GUIDs to update

        Returns:
            int: Number of customers updated
        """
        if customer_guids is not None and len(customer_guids) == 0:
            return 0

        where_clause = "WHERE c.guid IN $customerGuids" if customer_guids else ""
        params = {"customerGuids": customer_guids} if customer_guids else {}

        query = f"""
        MATCH (c:Customer)
        {where_clause}

        // TODO: Aggregate metrics for customer
        // - Active project count
        // - Total hours across projects
        // - Total revenue from invoices
        // - Average profitability
        OPTIONAL MATCH (c)-[:HAS_PROJECT]->(p:Project)
        WITH c,
             count(DISTINCT p.guid) as projectCount,
             sum(p.hoursWorked) as customerHours,
             sum(p.totalRevenue) as customerRevenue

        SET c.projectCount = COALESCE(projectCount, 0),
            c.totalHours = COALESCE(customerHours, 0),
            c.totalRevenue = COALESCE(customerRevenue, 0),
            c.lastDenormalizedAt = datetime()

        RETURN count(c) as customerCount
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, params)
                record = result.single()
                count = record["customerCount"] if record else 0
                logger.info(f"  ✓ Updated {count} Customer denormalized metrics")
                return count
        except Exception as e:
            logger.error(f"Failed to calculate Customer summaries: {e}")
            return 0

    def calculate_user_summaries(self, user_guids: Optional[List[str]] = None) -> int:
        """Denormalize User-level metrics

        Aggregates work hours and revenue per user.

        TODO: Implement based on your entity relationships:
        - User-WorkHour-Project relationships
        - Total hours logged
        - Billable vs non-billable hours
        - Average billing rate

        Args:
            user_guids: Optional list of user GUIDs to update

        Returns:
            int: Number of users updated
        """
        if user_guids is not None and len(user_guids) == 0:
            return 0

        where_clause = "WHERE u.guid IN $userGuids" if user_guids else ""
        params = {"userGuids": user_guids} if user_guids else {}

        query = f"""
        MATCH (u:User)
        {where_clause}

        // TODO: Aggregate metrics for user
        // - Total hours logged
        // - Billable vs non-billable
        // - Cost per hour / revenue per hour
        OPTIONAL MATCH (u)<-[:LOGGED_BY]-(wh:WorkHour)
        WITH u,
             sum(wh.quantity) as totalHours,
             sum(CASE WHEN wh.isBillable THEN wh.quantity ELSE 0 END) as billableHours,
             sum(wh.quantity * COALESCE(wh.unitCost, 0)) as totalCost

        SET u.totalHours = COALESCE(totalHours, 0),
            u.billableHours = COALESCE(billableHours, 0),
            u.totalCost = COALESCE(totalCost, 0),
            u.lastDenormalizedAt = datetime()

        RETURN count(u) as userCount
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, params)
                record = result.single()
                count = record["userCount"] if record else 0
                logger.info(f"  ✓ Updated {count} User denormalized metrics")
                return count
        except Exception as e:
            logger.error(f"Failed to calculate User summaries: {e}")
            return 0

    # TODO: Add more denormalization methods
    # Example:
    # def calculate_project_denormalized_metrics(self) -> int:
    #     """Denormalize project health score, risk level, etc."""
    #     pass
