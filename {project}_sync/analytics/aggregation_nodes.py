"""
Time-series aggregation node creation

Creates time-period hierarchy for efficient time-range queries:
- Year nodes (e.g., 2025)
- Quarter nodes (e.g., 2025-Q1)
- Month nodes (e.g., 2025-01)
- Day nodes (e.g., 2025-01-15, optional)

Pattern Implementation:
- Inherit from Neo4jBase for Neo4j operations
- create_year/quarter/month_nodes() methods
- MERGE nodes to handle incremental updates
- Create parent relationships: Day→Month→Quarter→Year
- Link fact nodes (WorkHour, Invoice) to periods via RECORDED_IN

TODO: Customize for your {API_NAME}:
1. Determine date range: extract from existing fact nodes or config
2. Create aggregation periods matching your reporting granularity
3. Link fact entities to time periods (e.g., WorkHour.eventDate → Month node)
4. Denormalize period metrics: totalHours, totalRevenue, etc.
5. Test incremental updates after new data sync

Benefits:
- Fast period queries: MATCH (m:Month) RETURN m.totalHours (cached)
- Time-range filtering: MATCH (y:Year {year: 2025})-[:CONTAINS]-(m:Month)
- Dashboard support: Pre-aggregated data for rendering
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple
from ..neo4j_base import Neo4jBase

logger = logging.getLogger(__name__)


class AggregationNodes(Neo4jBase):
    """Handles creating time-period aggregation nodes for analytics

    Responsibilities:
    - Create time-period hierarchy (Year→Quarter→Month→Day)
    - Create relationships between periods
    - Link fact entities to periods
    - Support incremental updates

    Example Hierarchy:
    Year(2025)
      ├─ CONTAINS ─→ Quarter(Q1)
      │               ├─ CONTAINS ─→ Month(01)
      │               │               ├─ CONTAINS ─→ Day(2025-01-01)
      │               │               └─ CONTAINS ─→ Day(2025-01-02)
      │               └─ CONTAINS ─→ Month(02)
      └─ CONTAINS ─→ Quarter(Q2)
    """

    def create_year_nodes(self, start_year: int = 2020, end_year: int = 2030) -> int:
        """Create Year aggregation nodes

        TODO: Customize year range based on your data:
        - Determine from config or data
        - Default: 2020-2030 (10 years)
        - Adjust based on your {API_NAME} data coverage

        Args:
            start_year: First year to create (default: 2020)
            end_year: Last year to create (default: 2030)

        Returns:
            int: Number of year nodes created
        """
        queries = []
        for year in range(start_year, end_year + 1):
            queries.append({
                "query": """
                MERGE (y:Year {year: $year})
                SET y.yearString = $yearString
                """,
                "parameters": {
                    "year": year,
                    "yearString": str(year)
                }
            })

        count = self._execute_batch(queries)
        logger.info(f"  ✓ Created {count} Year nodes ({start_year}-{end_year})")
        return count

    def create_quarter_nodes(self, start_year: int = 2020, end_year: int = 2030) -> int:
        """Create Quarter aggregation nodes

        Creates Q1-Q4 nodes for each year and links to Year nodes.

        TODO: Customize year range (see create_year_nodes)

        Args:
            start_year: First year
            end_year: Last year

        Returns:
            int: Number of quarter nodes created
        """
        queries = []
        for year in range(start_year, end_year + 1):
            for quarter in range(1, 5):
                quarter_id = f"{year}-Q{quarter}"
                queries.append({
                    "query": """
                    MATCH (y:Year {year: $year})
                    MERGE (q:Quarter {id: $quarter_id})
                    SET q.year = $year,
                        q.quarter = $quarter,
                        q.yearQuarter = $quarter_id
                    MERGE (y)-[:CONTAINS]->(q)
                    """,
                    "parameters": {
                        "year": year,
                        "quarter": quarter,
                        "quarter_id": quarter_id
                    }
                })

        count = self._execute_batch(queries)
        logger.info(f"  ✓ Created {count} Quarter nodes")
        return count

    def create_month_nodes(self, start_year: int = 2020, end_year: int = 2030) -> int:
        """Create Month aggregation nodes

        Creates Month nodes for each year-month and links to Quarter nodes.

        TODO: Customize year range (see create_year_nodes)

        Args:
            start_year: First year
            end_year: Last year

        Returns:
            int: Number of month nodes created
        """
        queries = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                quarter = (month - 1) // 3 + 1
                quarter_id = f"{year}-Q{quarter}"
                month_id = f"{year}-{month:02d}"

                queries.append({
                    "query": """
                    MATCH (q:Quarter {id: $quarter_id})
                    MERGE (m:Month {id: $month_id})
                    SET m.year = $year,
                        m.month = $month,
                        m.yearMonth = $month_id,
                        m.quarter = $quarter
                    MERGE (q)-[:CONTAINS]->(m)
                    """,
                    "parameters": {
                        "year": year,
                        "month": month,
                        "quarter": quarter,
                        "quarter_id": quarter_id,
                        "month_id": month_id
                    }
                })

        count = self._execute_batch(queries)
        logger.info(f"  ✓ Created {count} Month nodes")
        return count

    def create_day_nodes(self, start_date: str = "2020-01-01", end_date: str = "2030-12-31") -> int:
        """Create Day aggregation nodes (optional for very detailed analytics)

        WARNING: Creates many nodes - only use if needed for daily granularity.
        For 10 years: ~3,650 Day nodes. Consider whether you need daily aggregation.

        TODO: Decide if daily nodes are needed for your reporting:
        - Use if: daily dashboards, time-tracking details
        - Skip if: weekly/monthly aggregation sufficient

        Args:
            start_date: First date (YYYY-MM-DD)
            end_date: Last date (YYYY-MM-DD)

        Returns:
            int: Number of day nodes created
        """
        queries = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            year = current.year
            month = current.month
            day = current.day
            date_str = current.strftime("%Y-%m-%d")
            month_id = f"{year}-{month:02d}"

            queries.append({
                "query": """
                MATCH (m:Month {id: $month_id})
                MERGE (d:Day {id: $date_str})
                SET d.year = $year,
                    d.month = $month,
                    d.day = $day,
                    d.date = $date_str
                MERGE (m)-[:CONTAINS]->(d)
                """,
                "parameters": {
                    "year": year,
                    "month": month,
                    "day": day,
                    "date_str": date_str,
                    "month_id": month_id
                }
            })

            current += timedelta(days=1)

        if queries:
            count = self._execute_batch(queries)
            logger.info(f"  ✓ Created {count} Day nodes ({start_date} to {end_date})")
            return count
        return 0

    def link_facts_to_periods(self, fact_entity: str, date_property: str) -> int:
        """Link fact entities (WorkHour, Invoice) to time-period nodes

        Creates RECORDED_IN relationships between fact nodes and Month nodes.

        TODO: Call after creating time-period hierarchy:
        1. Create aggregation nodes: create_year_nodes() → create_month_nodes()
        2. Link facts: link_facts_to_periods("WorkHour", "eventDate")
        3. Calculate period metrics: denormalize.calculate_period_metrics()

        Args:
            fact_entity: Entity type (e.g., "WorkHour", "Invoice")
            date_property: Property containing date (e.g., "eventDate", "invoiceDate")

        Returns:
            int: Number of relationships created
        """
        query = f"""
        MATCH (f:{fact_entity})
        WHERE f.{date_property} IS NOT NULL
        WITH f, f.{date_property} as dateStr
        WITH f, dateStr,
             date(dateStr).year as year,
             date(dateStr).month as month
        WITH f, dateStr, year, month,
             year + '-' + sprintf('%02d', month) as monthId
        MATCH (m:Month {{id: monthId}})
        MERGE (f)-[:RECORDED_IN]->(m)
        RETURN count(*) as count
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(query)
                record = result.single()
                count = record["count"] if record else 0
                logger.info(f"  ✓ Linked {count} {fact_entity} entities to Month periods")
                return count
        except Exception as e:
            logger.error(f"Failed to link {fact_entity} to periods: {e}")
            return 0

    # TODO: Add more aggregation levels or custom periods
    # Example:
    # def create_week_nodes(self) -> int:
    #     """Create Week aggregation nodes for weekly reporting"""
    #     pass

    # def create_custom_periods(self) -> int:
    #     """Create fiscal year or other custom period definitions"""
    #     pass
