# Performance Optimization Guide

Three-phase strategy for optimizing Neo4j query performance, based on real-world results from production sync project.

---

## Overview

**Optimization follows diminishing returns:**
- Phase 1 (Indexes): 60-80% improvement, minimal effort
- Phase 2 (Time-Series Aggregation): 80-95% improvement, moderate effort
- Phase 3 (Analytics Denormalization): Further gains, high effort

**Key Principle:** Start with indexes. Only move to Phase 2/3 if performance is still insufficient.

---

## Phase 1: Database Indexes (60-80% Improvement)

**Fastest gains with minimal code changes.**

### What to Index

**1. Primary identifiers (NODE KEY constraints):**
```cypher
CREATE CONSTRAINT customer_guid IF NOT EXISTS
FOR (c:Customer) REQUIRE c.guid IS NODE KEY;

CREATE CONSTRAINT project_guid IF NOT EXISTS
FOR (p:Project) REQUIRE p.guid IS NODE KEY;

CREATE CONSTRAINT user_guid IF NOT EXISTS
FOR (u:User) REQUIRE u.guid IS NODE KEY;
```

**2. Foreign key GUIDs (for relationship creation):**
```cypher
CREATE INDEX project_customer_guid IF NOT EXISTS
FOR (p:Project) ON (p.customerGuid);

CREATE INDEX project_owner_guid IF NOT EXISTS
FOR (p:Project) ON (p.ownerGuid);

CREATE INDEX work_hour_user_guid IF NOT EXISTS
FOR (w:WorkHour) ON (w.userGuid);

CREATE INDEX work_hour_project_guid IF NOT EXISTS
FOR (w:WorkHour) ON (w.projectGuid);
```

**3. Query filter fields:**
```cypher
CREATE INDEX project_status IF NOT EXISTS
FOR (p:Project) ON (p.status);

CREATE INDEX project_deadline IF NOT EXISTS
FOR (p:Project) ON (p.deadline);

CREATE INDEX work_hour_date IF NOT EXISTS
FOR (w:WorkHour) ON (w.date);
```

**4. Search fields:**
```cypher
CREATE TEXT INDEX customer_name_search IF NOT EXISTS
FOR (c:Customer) ON (c.name);

CREATE TEXT INDEX project_name_search IF NOT EXISTS
FOR (p:Project) ON (p.name);
```

### Implementation

**Create indexes during schema setup:**
```python
# {project}_sync/schema_setup.py
async def create_indexes(driver):
    """Create all indexes and constraints"""
    constraints = [
        "CREATE CONSTRAINT customer_guid IF NOT EXISTS FOR (c:Customer) REQUIRE c.guid IS NODE KEY",
        "CREATE CONSTRAINT project_guid IF NOT EXISTS FOR (p:Project) REQUIRE p.guid IS NODE KEY",
        # ... more constraints
    ]

    indexes = [
        "CREATE INDEX project_customer_guid IF NOT EXISTS FOR (p:Project) ON (p.customerGuid)",
        "CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status)",
        # ... more indexes
    ]

    for constraint in constraints:
        await driver.execute_query(constraint)
        logger.info(f"Created constraint")

    for index in indexes:
        await driver.execute_query(index)
        logger.info(f"Created index")
```

### Benchmarking Impact

**Before indexes:**
```cypher
// Query: Get projects with their customers
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
WHERE p.status = 'active'
RETURN c.name, count(p)

// Execution time: 2500ms
// db hits: 45,000
```

**After indexes:**
```cypher
// Same query
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
WHERE p.status = 'active'
RETURN c.name, count(p)

// Execution time: 150ms (16x faster!)
// db hits: 3,200
```

### Results from example project Project

- Dashboard metrics: 3200ms → 245ms (13x faster)
- Project list queries: 1800ms → 120ms (15x faster)
- Time-series queries: 5500ms → 800ms (7x faster)

**Verdict:** Indexes alone provide 60-80% improvement for most queries.

---

## Phase 2: Time-Series Aggregation (80-95% Improvement)

**For high-volume time-series data (work hours, transactions, events).**

### Problem

**Query aggregates millions of WorkHour records:**
```cypher
// Aggregating 500,000+ WorkHour records
MATCH (wh:WorkHour)
WHERE wh.date >= date('2024-01-01') AND wh.date <= date('2024-12-31')
RETURN
  wh.date.year as year,
  wh.date.month as month,
  sum(wh.hours) as totalHours,
  sum(wh.revenue) as totalRevenue

// Execution time: 800ms (even with indexes!)
```

### Solution: Pre-Aggregate by Time Period

**Create aggregation nodes:**
```cypher
// Month aggregation node
(:Month {
  year: 2024,
  month: 10,
  totalHours: 8500.5,
  billableHours: 7200.0,
  nonBillableHours: 1300.5,
  totalRevenue: 1080000.00,
  totalCost: 680000.00,
  margin: 400000.00
})

// Connect to individual work hours
(:Month)-[:HAS_HOURS]->(:WorkHour)
```

**Query aggregated data:**
```cypher
// Query pre-aggregated Month nodes instead
MATCH (m:Month)
WHERE m.year = 2024 AND m.month >= 7
RETURN m.month, m.totalHours, m.totalRevenue
ORDER BY m.month

// Execution time: 45ms (18x faster than indexed query!)
```

### Implementation

**1. Create aggregation nodes during sync:**
```python
# {project}_sync/aggregation/time_series.py
async def create_monthly_aggregations(driver):
    """Aggregate WorkHours by month"""
    query = """
    MATCH (wh:WorkHour)
    WITH
      wh.date.year as year,
      wh.date.month as month,
      sum(wh.hours) as totalHours,
      sum(CASE WHEN wh.billable THEN wh.hours ELSE 0 END) as billableHours,
      sum(CASE WHEN NOT wh.billable THEN wh.hours ELSE 0 END) as nonBillableHours,
      sum(wh.revenue) as totalRevenue,
      sum(wh.cost) as totalCost
    MERGE (m:Month {year: year, month: month})
    SET
      m.totalHours = totalHours,
      m.billableHours = billableHours,
      m.nonBillableHours = nonBillableHours,
      m.totalRevenue = totalRevenue,
      m.totalCost = totalCost,
      m.margin = totalRevenue - totalCost,
      m.lastUpdated = datetime()
    """
    await driver.execute_query(query)
    logger.info("Created monthly aggregations")
```

**2. Connect aggregations to source data:**
```python
async def link_work_hours_to_months(driver):
    """Link WorkHours to Month nodes"""
    query = """
    MATCH (wh:WorkHour), (m:Month)
    WHERE wh.date.year = m.year AND wh.date.month = m.month
    MERGE (m)-[:HAS_HOURS]->(wh)
    """
    await driver.execute_query(query)
```

**3. Add to orchestrator:**
```python
# orchestrator.py
async def sync_all(self):
    # Sync entities
    await self.sync_all_entities()

    # Sync relationships
    await self.sync_relationships()

    # Create time-series aggregations
    await create_monthly_aggregations(self.driver)
    await link_work_hours_to_months(self.driver)
```

### Hierarchy of Aggregations

**Multiple levels for different granularities:**
```cypher
// Year aggregation
(:Year {year: 2024, totalHours: 102000, totalRevenue: 15300000})-[:HAS_QUARTER]->(:Quarter)

// Quarter aggregation
(:Quarter {year: 2024, quarter: 4, totalHours: 26000})-[:HAS_MONTH]->(:Month)

// Month aggregation
(:Month {year: 2024, month: 10, totalHours: 8500})-[:HAS_WEEK]->(:Week)

// Week aggregation (optional)
(:Week {year: 2024, week: 44, totalHours: 320})-[:HAS_HOURS]->(:WorkHour)
```

**Query at appropriate level:**
```cypher
// Annual trends - query Year nodes
MATCH (y:Year)
WHERE y.year >= 2020
RETURN y.year, y.totalRevenue
ORDER BY y.year

// Quarterly trends - query Quarter nodes
MATCH (q:Quarter)
WHERE q.year = 2024
RETURN q.quarter, q.totalRevenue
ORDER BY q.quarter

// Monthly details - query Month nodes
MATCH (m:Month)
WHERE m.year = 2024 AND m.month >= 7
RETURN m.month, m.totalHours, m.billableHours
ORDER BY m.month
```

### Results from example project Project

- Time-series dashboard: 800ms → 45ms (18x faster)
- Monthly trends: 1200ms → 60ms (20x faster)
- Quarterly reports: 2500ms → 80ms (31x faster)

**Verdict:** Pre-aggregation reduces query time by 80-95% for time-series data.

---

## Phase 3: Analytics Denormalization (Further Gains)

**Store computed metrics on entity nodes for instant dashboard queries.**

### Problem

**Dashboard requires aggregations across relationships:**
```cypher
// Calculate project metrics on-the-fly
MATCH (p:Project)<-[wh:LOGGED_HOURS]-(u:User)
WITH p, sum(wh.hours) as totalHours
MATCH (p)-[:HAS_INVOICE]->(inv:Invoice)
WITH p, totalHours, sum(inv.amount) as totalRevenue
RETURN
  p.name,
  totalHours,
  totalRevenue,
  totalRevenue - (totalHours * p.avgCost) as margin

// Execution time: 500ms per project (even with indexes!)
```

### Solution: Pre-Compute and Store Metrics

**Store calculated metrics as properties:**
```cypher
(:Project {
  guid: "proj-123",
  name: "Website Redesign",
  // ... API properties
  // Pre-computed metrics:
  hoursWorked: 850.5,
  hourEstimate: 1000.0,
  totalRevenue: 125000.00,
  totalCost: 85000.00,
  margin: 40000.00,
  marginPct: 32.0,
  completionPct: 85.05,
  billableHours: 750.0,
  nonBillableHours: 100.5,
  billablePct: 88.17,
  lastMetricsUpdate: datetime("2024-10-30T12:00:00Z")
})
```

**Query reads properties directly:**
```cypher
// Read pre-computed metrics (no aggregation!)
MATCH (p:Project)
WHERE p.status = 'active'
RETURN
  p.name,
  p.hoursWorked,
  p.totalRevenue,
  p.margin,
  p.marginPct
ORDER BY p.margin DESC
LIMIT 10

// Execution time: 15ms (33x faster!)
```

### Implementation

**Calculate metrics during sync:**
```python
# {project}_sync/metrics/project_metrics.py
async def calculate_project_metrics(driver, project_guid):
    """Calculate and store metrics for a project"""
    query = """
    MATCH (p:Project {guid: $guid})

    // Calculate hours worked
    OPTIONAL MATCH (p)<-[wh:LOGGED_HOURS]-()
    WITH p,
      coalesce(sum(wh.hours), 0) as hoursWorked,
      coalesce(sum(CASE WHEN wh.billable THEN wh.hours ELSE 0 END), 0) as billableHours,
      coalesce(sum(CASE WHEN NOT wh.billable THEN wh.hours ELSE 0 END), 0) as nonBillableHours

    // Calculate financials
    OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv:Invoice)
    WITH p, hoursWorked, billableHours, nonBillableHours,
      coalesce(sum(inv.amount), 0) as totalRevenue

    // Calculate costs
    OPTIONAL MATCH (p)<-[wh2:LOGGED_HOURS]-(u:User)
    WITH p, hoursWorked, billableHours, nonBillableHours, totalRevenue,
      coalesce(sum(wh2.hours * u.hourlyRate), 0) as totalCost

    // Store calculated metrics
    SET
      p.hoursWorked = hoursWorked,
      p.billableHours = billableHours,
      p.nonBillableHours = nonBillableHours,
      p.totalRevenue = totalRevenue,
      p.totalCost = totalCost,
      p.margin = totalRevenue - totalCost,
      p.marginPct = CASE
        WHEN totalRevenue > 0 THEN (totalRevenue - totalCost) / totalRevenue * 100.0
        ELSE 0
      END,
      p.completionPct = CASE
        WHEN p.hourEstimate > 0 THEN hoursWorked / p.hourEstimate * 100.0
        ELSE 0
      END,
      p.billablePct = CASE
        WHEN hoursWorked > 0 THEN billableHours / hoursWorked * 100.0
        ELSE 0
      END,
      p.lastMetricsUpdate = datetime()

    RETURN p.name, p.hoursWorked, p.margin
    """

    result = await driver.execute_query(query, guid=project_guid)
    return result

async def calculate_all_projects(driver):
    """Calculate metrics for all projects"""
    # Get all project GUIDs
    result = await driver.execute_query("MATCH (p:Project) RETURN p.guid as guid")
    project_guids = [record["guid"] for record in result.records]

    # Calculate metrics for each project
    for guid in project_guids:
        await calculate_project_metrics(driver, guid)

    logger.info(f"Calculated metrics for {len(project_guids)} projects")
```

**Update metrics during sync:**
```python
# orchestrator.py
async def sync_all(self):
    # Sync entities
    await self.sync_all_entities()

    # Sync relationships
    await self.sync_relationships()

    # Calculate analytics metrics
    await calculate_all_projects(self.driver)
```

### Incremental Updates

**Only recalculate affected projects:**
```python
async def update_project_metrics_incremental(driver, project_guids):
    """Update metrics only for specific projects"""
    for guid in project_guids:
        await calculate_project_metrics(driver, guid)

# After syncing work hours for a project
await update_project_metrics_incremental(driver, [project_guid])
```

### Results from example project Project

- Dashboard queries: 500ms → 15ms (33x faster)
- Project list with metrics: 800ms → 50ms (16x faster)
- Top projects by margin: 1200ms → 25ms (48x faster)

**Verdict:** Denormalization provides instant dashboard queries (< 50ms).

---

## Benchmarking Queries

### Use EXPLAIN and PROFILE

**EXPLAIN - Show query plan:**
```cypher
EXPLAIN
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
WHERE p.status = 'active'
RETURN c.name, count(p)
```

**PROFILE - Measure actual performance:**
```cypher
PROFILE
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
WHERE p.status = 'active'
RETURN c.name, count(p)
```

**Key metrics to watch:**
- **db hits**: Total database operations (lower is better)
- **rows**: Number of rows processed
- **Operator**: Index scans vs full scans (NodeByLabelScan = bad, NodeIndexSeek = good)

### Benchmark Script

```python
# benchmark_queries.py
import time
from neo4j import AsyncGraphDatabase

async def benchmark_query(driver, name, query):
    """Benchmark a single query"""
    # Warm up
    await driver.execute_query(query)

    # Benchmark (10 runs)
    times = []
    for _ in range(10):
        start = time.time()
        await driver.execute_query(query)
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"{name}:")
    print(f"  Avg: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")

# Usage
await benchmark_query(driver, "Project List", """
    MATCH (p:Project)
    WHERE p.status = 'active'
    RETURN p.name, p.hoursWorked, p.margin
    LIMIT 20
""")
```

---

## Performance Optimization Checklist

**Phase 1: Indexes (Do this first!)**
- ✅ NODE KEY constraints on all entity `guid` properties
- ✅ Indexes on foreign key GUIDs (for relationship queries)
- ✅ Indexes on commonly queried fields (status, dates)
- ✅ Text indexes for search fields
- ✅ Benchmark queries with PROFILE

**Phase 2: Time-Series Aggregation (If time-series queries > 200ms)**
- ✅ Create Month/Quarter/Year aggregation nodes
- ✅ Pre-aggregate high-volume time-series data
- ✅ Link aggregations to source data
- ✅ Query at appropriate granularity level
- ✅ Update aggregations during sync

**Phase 3: Analytics Denormalization (If dashboard queries > 100ms)**
- ✅ Identify frequently queried aggregates
- ✅ Calculate and store as entity properties
- ✅ Update metrics during sync (inline or post-sync)
- ✅ Add `lastMetricsUpdate` timestamp
- ✅ Implement incremental updates

**General Best Practices:**
- ✅ Use batch operations (UNWIND) for bulk updates
- ✅ Avoid Cartesian products (use WHERE clauses)
- ✅ Limit result sets with LIMIT
- ✅ Use PROFILE to verify query plans
- ✅ Monitor query performance in production

---

## Real-World Results Summary

**example project Project Performance (10,000+ projects, 500,000+ work hours):**

| Query Type | Before Optimization | Phase 1 (Indexes) | Phase 2 (Aggregation) | Phase 3 (Denormalization) |
|------------|---------------------|-------------------|-----------------------|---------------------------|
| Dashboard KPIs | 3200ms | 245ms (13x) | 180ms (18x) | 15ms (213x) |
| Project List | 1800ms | 120ms (15x) | 95ms (19x) | 50ms (36x) |
| Time-Series (monthly) | 5500ms | 800ms (7x) | 45ms (122x) | 30ms (183x) |
| Top Projects by Margin | 2400ms | 380ms (6x) | 320ms (8x) | 25ms (96x) |

**Key Takeaway:** Phase 1 alone provides 70-85% improvement. Phase 2 and 3 are optional for further gains.

---

## When to Optimize

**Start optimizing when:**
- Query response time > 500ms
- Dashboard feels sluggish
- Time-series queries > 1 second
- Sync performance degrades with data growth

**Optimization order:**
1. Always start with Phase 1 (indexes) - fastest ROI
2. Move to Phase 2 if time-series queries still slow
3. Move to Phase 3 if dashboard queries still > 100ms

**Don't optimize prematurely:**
- Small datasets (< 10,000 nodes) perform well without optimization
- Focus on correctness first, performance second
- Measure before optimizing (use PROFILE)
