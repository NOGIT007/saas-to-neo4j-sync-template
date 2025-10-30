"""
Project metrics calculation module

Calculates and stores KPIs as properties on {Entity} nodes.
Updated inline during sync - no separate maintenance jobs needed.

Metrics Pattern:
- Calculate metrics AFTER all entity syncs complete
- Aggregate values using Cypher (sum, count, avg)
- Store calculated values as properties on entity nodes
- Support partial updates: pass project_guids list to update specific projects
- Return count of updated projects for verification

TODO: Customize for your {API_NAME}:
1. Replace {Entity} with your entity name (e.g., Project, Service, Assignment)
2. Add/remove metrics based on business requirements
3. Verify relationship names match your Neo4j schema
4. Test metric calculations with sample data
5. Optimize Cypher queries if needed (use indexes for large datasets)

Common Metrics Patterns:
- Hours aggregation: sum(workhour.quantity) WHERE workhour.isBillable
- Revenue: sum(invoice.amount) by project or customer
- Cost: sum(workhour.quantity * workhour.unitCost)
- Margin: totalRevenue - totalCost
- Completion: hoursWorked / hoursEstimate * 100
- Billing rate: billableHours / totalHours * 100
"""
import logging
from typing import List, Optional
from ..neo4j_base import Neo4jBase

logger = logging.getLogger(__name__)


class ProjectMetrics(Neo4jBase):
    """Handles calculating and storing {Entity} metrics

    Responsibilities:
    - Calculate KPIs after entity syncs complete
    - Store calculated values as properties on entity nodes
    - Support partial updates (specific entities or all)
    - Log metrics update progress

    Metrics Calculated:
    - hoursWorked: Total hours across all work entries
    - billableHours: Hours marked as billable
    - nonBillableHours: Hours marked as non-billable
    - hourEstimate: Sum of estimated hours from phases/tasks
    - totalRevenue: Sum of invoice amounts
    - totalCost: Sum of (hours * unitCost) from work entries
    - margin: totalRevenue - totalCost
    - marginPct: (totalRevenue - totalCost) / totalRevenue * 100
    - completionPct: hoursWorked / hourEstimate * 100
    - billablePct: billableHours / totalHours * 100
    - lastMetricsUpdate: Timestamp of calculation

    Example Workflow:
    1. After all syncs: metrics = ProjectMetrics(config)
    2. Update all projects: count = metrics.calculate_project_metrics()
    3. Update specific projects: count = metrics.calculate_project_metrics(["p-123", "p-456"])
    4. Log shows: "✓ Updated 42 project metrics"
    """

    def calculate_project_metrics(self, project_guids: Optional[List[str]] = None) -> int:
        """Calculate and store metrics as properties on {Entity} nodes

        Aggregates related data (work hours, invoices, etc.) and stores
        calculated KPIs as properties. Updated inline during sync.

        Args:
            project_guids: Optional list of specific project GUIDs to update.
                          If None, updates all projects.

        Returns:
            int: Number of projects updated
        """
        if project_guids is not None and len(project_guids) == 0:
            return 0  # No projects to update

        where_clause = "WHERE p.guid IN $projectGuids" if project_guids else ""
        params = {"projectGuids": project_guids} if project_guids else {}

        query = f"""
        MATCH (p:{{Entity}})
        {where_clause}

        // TODO: Step 1 - Calculate hours metrics
        // Customize for your entity relationships:
        // - Does your entity have phases/tasks that contain work hours?
        // - Is the relationship HAS_PHASE, CONTAINS_TASK, or something else?
        // - Adjust OPTIONAL MATCH and relationship names accordingly
        OPTIONAL MATCH (p)-[:HAS_PHASE]->(ph:Phase)<-[:RECORDED_ON]-(wh:WorkHour)
        WITH p,
             sum(wh.quantity) as hoursWorked,
             sum(CASE WHEN wh.isBillable THEN wh.quantity ELSE 0 END) as billableHours,
             sum(CASE WHEN NOT wh.isBillable THEN wh.quantity ELSE 0 END) as nonBillableHours

        // TODO: Step 2 - Calculate estimate
        // Customize: OPTIONAL MATCH (p)-[:HAS_PHASE]->(ph2:Phase)
        // Then: sum(ph2.workHoursEstimate) as hourEstimate
        OPTIONAL MATCH (p)-[:HAS_PHASE]->(ph2:Phase)
        WITH p, hoursWorked, billableHours, nonBillableHours,
             sum(ph2.workHoursEstimate) as hourEstimate

        // TODO: Step 3 - Calculate revenue
        // Customize for your invoice/billing relationship:
        // - Does your entity have invoices?
        // - Is the relationship FOR_PROJECT, REFERENCES, or something else?
        // - Adjust relationship name and sum field accordingly
        OPTIONAL MATCH (p)<-[:FOR_PROJECT]-(inv:Invoice)
        WITH p, hoursWorked, billableHours, nonBillableHours, hourEstimate,
             sum(inv.totalAmount) as totalRevenue

        // TODO: Step 4 - Calculate costs
        // Customize: aggregate work hour unit costs or resource costs
        // Current pattern: hours * unitCost from work entries
        OPTIONAL MATCH (p)-[:HAS_PHASE]->(ph3:Phase)<-[:RECORDED_ON]-(wh2:WorkHour)
        WITH p, hoursWorked, billableHours, nonBillableHours, hourEstimate, totalRevenue,
             sum(wh2.quantity * COALESCE(wh2.unitCost, 0)) as totalCost

        // TODO: Step 5 - Set calculated properties
        // Add/remove SET properties based on your metrics requirements
        SET p.hoursWorked = COALESCE(hoursWorked, 0),
            p.billableHours = COALESCE(billableHours, 0),
            p.nonBillableHours = COALESCE(nonBillableHours, 0),
            p.hourEstimate = COALESCE(hourEstimate, 0),
            p.totalRevenue = COALESCE(totalRevenue, 0),
            p.totalCost = COALESCE(totalCost, 0),
            p.margin = COALESCE(totalRevenue, 0) - COALESCE(totalCost, 0),
            p.marginPct = CASE
                WHEN totalRevenue > 0
                THEN ((totalRevenue - COALESCE(totalCost, 0)) / totalRevenue) * 100
                ELSE 0
            END,
            p.completionPct = CASE
                WHEN hourEstimate > 0
                THEN (hoursWorked / hourEstimate) * 100
                ELSE 0
            END,
            p.billablePct = CASE
                WHEN hoursWorked > 0
                THEN (billableHours / hoursWorked) * 100
                ELSE 0
            END,
            p.lastMetricsUpdate = datetime()

        RETURN count(p) as projectsUpdated
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query, params)
                record = result.single()
                count = record["projectsUpdated"] if record else 0
                logger.info(f"  ✓ Updated {count} {{Entity}} metrics")
                return count
        except Exception as e:
            logger.error(f"Failed to calculate {{Entity}} metrics: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            return 0

    # TODO: Add more metric calculation methods
    # Example:
    # def calculate_customer_metrics(self, customer_guids: Optional[List[str]] = None) -> int:
    #     """Calculate Customer metrics: totalRevenue, totalCost, activeProjects, etc."""
    #     pass

    # def calculate_user_metrics(self, user_guids: Optional[List[str]] = None) -> int:
    #     """Calculate User metrics: hoursLogged, billableHours, averageRate, etc."""
    #     pass
