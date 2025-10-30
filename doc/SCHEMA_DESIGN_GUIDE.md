# Neo4j Schema Design Guide

Best practices for designing graph schemas for SaaS data sync.

---

## Core Principles

1. **Model business entities as nodes**
2. **Model relationships explicitly**
3. **Denormalize for query performance**
4. **Use NODE KEY constraints for uniqueness**
5. **Index properties used in queries**
6. **Store both GUIDs and human-readable IDs**

---

## Node Design Patterns

### Entity Node Structure

**Template:**
```cypher
(:{EntityType} {
  guid: "unique-identifier",        // From API (NODE KEY)
  name: "Human readable name",       // Display field
  externalId: "API-123",            // API's ID format
  createdAt: datetime("2024-..."),  // Temporal properties
  updatedAt: datetime("2024-..."),
  // Entity-specific properties
  status: "active",
  email: "user@example.com"
})
```

### Example: Customer Node

```cypher
(:Customer {
  guid: "cust-abc-123",             // Primary identifier
  name: "Acme Corporation",         // Display name
  externalId: "CUST-001",           // Customer's ID in source system
  email: "contact@acme.com",
  industry: "Technology",
  country: "USA",
  createdAt: datetime("2024-01-15T10:00:00Z"),
  updatedAt: datetime("2024-10-30T14:30:00Z"),
  isActive: true
})
```

### Example: Project Node

```cypher
(:Project {
  guid: "proj-xyz-456",
  name: "Website Redesign",
  number: "PRJ-2024-042",           // Human-readable project number
  status: "in_progress",            // active, on_hold, completed
  deadline: date("2024-12-31"),     // Date type for temporal queries
  expectedValue: 150000.00,         // Financial properties
  // Foreign keys (stored as properties, not inline entities)
  customerGuid: "cust-abc-123",
  ownerGuid: "user-john-789",
  // Computed metrics (calculated during sync)
  hoursWorked: 850.5,
  totalRevenue: 125000.00,
  marginPct: 32.0,
  lastMetricsUpdate: datetime("2024-10-30T12:00:00Z")
})
```

---

## Relationship Patterns

### Basic Relationship Types

**1. Ownership/Association:**
```cypher
// Customer owns project
(:Customer)-[:HAS_PROJECT]->(:Project)

// User owns project
(:User)-[:OWNS]->(:Project)

// User works for customer
(:User)-[:WORKS_FOR]->(:Customer)
```

**2. Hierarchical:**
```cypher
// Project has phases
(:Project)-[:HAS_PHASE]->(:Phase)

// Organization structure
(:Department)-[:PART_OF]->(:Company)
```

**3. Transactional:**
```cypher
// Time tracking
(:User)-[:LOGGED_HOURS {date, hours, billable}]->(:Project)

// Financial
(:Customer)-[:RECEIVED_INVOICE {amount, date, status}]->(:Invoice)
```

### Relationship with Properties

**When to add properties to relationships:**
- Temporal data (date, timestamp)
- Quantitative data (hours, amount)
- Status flags (billable, approved)

**Example:**
```cypher
(:User)-[:LOGGED_HOURS {
  date: date("2024-10-30"),
  hours: 8.5,
  billable: true,
  description: "Frontend development",
  hourlyRate: 150.00
}]->(:Project)
```

### Avoid Creating Entities Inline

**❌ WRONG - Creating foreign entities in entity sync:**
```python
# project_sync.py - DON'T DO THIS
query = """
MERGE (p:Project {guid: $guid})
SET p.name = $name
// ❌ Creating Customer inline
MERGE (c:Customer {guid: $customerGuid})
MERGE (c)-[:HAS_PROJECT]->(p)
"""
```

**✅ CORRECT - Store GUIDs, create relationships separately:**
```python
# project_sync.py - Entity sync
query = """
MERGE (p:Project {guid: $guid})
SET p.name = $name,
    p.customerGuid = $customerGuid  // ✅ Store GUID only
"""

# relationships/project_relationships.py - Separate relationship sync
query = """
MATCH (p:Project), (c:Customer)
WHERE p.customerGuid = c.guid
MERGE (c)-[:HAS_PROJECT]->(p)
"""
```

**Why?**
- Entity modules have single responsibility
- Relationships are created after all entities exist
- Easier to debug and maintain

---

## Property Types and Naming

### Neo4j Data Types

```cypher
// Strings
name: "John Doe"

// Numbers
age: 42
price: 99.99

// Booleans
isActive: true

// Dates and Times
createdDate: date("2024-10-30")
createdDateTime: datetime("2024-10-30T14:30:00Z")

// Lists
tags: ["important", "urgent"]
emails: ["john@example.com", "j.doe@work.com"]
```

### Naming Conventions

**Nodes:**
- PascalCase: `:Customer`, `:Project`, `:WorkHour`
- Singular form: `:User` not `:Users`

**Relationships:**
- UPPER_SNAKE_CASE: `:HAS_PROJECT`, `:WORKS_FOR`
- Verb phrases: `:OWNS`, `:BELONGS_TO`, `:CONTAINS`

**Properties:**
- camelCase: `firstName`, `updatedAt`, `customerGuid`
- Boolean prefix: `isActive`, `hasAccess`, `canEdit`
- Temporal suffix: `createdAt`, `updatedAt`, `deletedAt`

---

## Constraints and Indexes

### NODE KEY Constraints (Uniqueness + Not Null)

**Critical for entity integrity:**
```cypher
// Create NODE KEY on guid (primary identifier)
CREATE CONSTRAINT customer_guid IF NOT EXISTS
FOR (c:Customer) REQUIRE c.guid IS NODE KEY;

CREATE CONSTRAINT project_guid IF NOT EXISTS
FOR (p:Project) REQUIRE p.guid IS NODE KEY;

CREATE CONSTRAINT user_guid IF NOT EXISTS
FOR (u:User) REQUIRE u.guid IS NODE KEY;

// Composite keys (if needed)
CREATE CONSTRAINT work_hour_composite IF NOT EXISTS
FOR (w:WorkHour) REQUIRE (w.userGuid, w.date, w.projectGuid) IS NODE KEY;
```

### Index Types

**1. Single property indexes (most common):**
```cypher
// Frequently queried properties
CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status);
CREATE INDEX project_deadline IF NOT EXISTS FOR (p:Project) ON (p.deadline);
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);
```

**2. Composite indexes (for multi-property queries):**
```cypher
// Queries filtering by multiple properties
CREATE INDEX work_hour_date_user IF NOT EXISTS
FOR (w:WorkHour) ON (w.date, w.userGuid);

CREATE INDEX invoice_customer_status IF NOT EXISTS
FOR (i:Invoice) ON (i.customerGuid, i.status);
```

**3. Text indexes (for search):**
```cypher
// Full-text search
CREATE TEXT INDEX customer_name_search IF NOT EXISTS
FOR (c:Customer) ON (c.name);
```

### Index Strategy

**Index properties used in:**
- WHERE clauses: `WHERE p.status = 'active'`
- ORDER BY: `ORDER BY p.deadline`
- Relationship matching: `WHERE p.customerGuid = c.guid`

**Typical indexes for SaaS sync:**
```cypher
// GUIDs (covered by NODE KEY)
CREATE CONSTRAINT {entity}_guid IF NOT EXISTS
FOR (e:{Entity}) REQUIRE e.guid IS NODE KEY;

// Foreign key GUIDs (for relationship creation)
CREATE INDEX project_customer_guid IF NOT EXISTS
FOR (p:Project) ON (p.customerGuid);

CREATE INDEX project_owner_guid IF NOT EXISTS
FOR (p:Project) ON (p.ownerGuid);

// Status fields (for filtering)
CREATE INDEX project_status IF NOT EXISTS
FOR (p:Project) ON (p.status);

// Temporal fields (for date range queries)
CREATE INDEX work_hour_date IF NOT EXISTS
FOR (w:WorkHour) ON (w.date);

// Search fields
CREATE INDEX customer_name IF NOT EXISTS
FOR (c:Customer) ON (c.name);
```

---

## Query Optimization Patterns

### Use MERGE for Upsert Operations

```cypher
// Efficient upsert pattern
UNWIND $batch as row
MERGE (p:Project {guid: row.guid})
SET p.name = row.name,
    p.status = row.status,
    p.updatedAt = datetime(row.updatedAt)
```

### Batch Operations

```cypher
// Process 500-1000 records per batch
UNWIND $batch as row
MERGE (c:Customer {guid: row.guid})
SET c.name = row.name,
    c.email = row.email
```

### Avoid Cartesian Products

**❌ WRONG - Cartesian product:**
```cypher
// This creates all combinations of Projects × Customers
MATCH (p:Project), (c:Customer)
MERGE (c)-[:HAS_PROJECT]->(p)
```

**✅ CORRECT - Use WHERE clause:**
```cypher
// This only matches related Projects and Customers
MATCH (p:Project), (c:Customer)
WHERE p.customerGuid = c.guid
MERGE (c)-[:HAS_PROJECT]->(p)
```

### Use EXPLAIN and PROFILE

```cypher
// Check query plan
EXPLAIN
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
WHERE p.deadline < date('2024-12-31')
RETURN c.name, count(p) as projectCount

// Measure actual performance
PROFILE
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
WHERE p.deadline < date('2024-12-31')
RETURN c.name, count(p) as projectCount
```

---

## Denormalization for Performance

### Store Computed Metrics

**Calculate and store aggregates during sync:**
```cypher
// Calculate project metrics inline
MATCH (p:Project)<-[wh:LOGGED_HOURS]-(u:User)
WITH p, sum(wh.hours) as totalHours
SET p.hoursWorked = totalHours

MATCH (p:Project)<-[rel:RECEIVED_INVOICE]-(c:Customer)
WITH p, sum(rel.amount) as revenue
SET p.totalRevenue = revenue

SET p.lastMetricsUpdate = datetime()
```

**Benefits:**
- Fast queries (read pre-computed properties)
- No aggregation at query time
- Dashboard queries < 200ms

**Trade-off:**
- Requires recalculation on updates
- Slight storage overhead
- Sync time increases slightly

### Time-Series Aggregation Nodes

**For high-volume time-series data:**
```cypher
// Aggregate work hours by month
(:Month {
  year: 2024,
  month: 10,
  totalHours: 8500.5,
  billableHours: 7200.0,
  revenue: 1080000.00
})-[:HAS_HOURS]->(:WorkHour)

// Fast dashboard queries
MATCH (m:Month)
WHERE m.year = 2024 AND m.month >= 7
RETURN m.month, m.totalHours, m.revenue
ORDER BY m.month
```

**See [PERFORMANCE_OPTIMIZATION_GUIDE.md](./PERFORMANCE_OPTIMIZATION_GUIDE.md) for details.**

---

## Schema Versioning

### Track Schema Version

```cypher
// Store metadata node
MERGE (meta:Metadata {key: "schema_version"})
SET meta.version = "1.2.0",
    meta.updatedAt = datetime()
```

### Schema Migration Pattern

```cypher
// Migration: Add new property to all Projects
MATCH (p:Project)
WHERE NOT exists(p.priority)
SET p.priority = "medium"
```

**See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for migration patterns.**

---

## Common Schema Anti-Patterns

### ❌ Storing Lists of Complex Objects

**Don't:**
```cypher
// Storing JSON arrays - hard to query
SET p.phases = '[{"name": "Phase 1", "hours": 100}, ...]'
```

**Do:**
```cypher
// Create proper nodes and relationships
(:Project)-[:HAS_PHASE]->(:Phase {name: "Phase 1", hours: 100})
```

### ❌ String-Based Foreign Keys Without Relationships

**Don't:**
```cypher
// Only storing GUID - requires manual joins
SET p.customerGuid = "cust-123"
// Query becomes complex
MATCH (p:Project), (c:Customer)
WHERE p.customerGuid = c.guid
```

**Do:**
```cypher
// Store GUID + create relationship
SET p.customerGuid = "cust-123"
MERGE (c:Customer {guid: "cust-123"})
MERGE (c)-[:HAS_PROJECT]->(p)
// Simple query
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
```

### ❌ Over-Normalized Schemas

**Don't:**
```cypher
// Too normalized - requires many joins
(:Project)-[:HAS_CUSTOMER_REF]->(:CustomerRef {guid})-[:REFERS_TO]->(:Customer)
```

**Do:**
```cypher
// Direct relationships
(:Project)-[:BELONGS_TO]->(:Customer)
```

### ❌ Missing Indexes on Foreign Keys

**Don't:**
```cypher
// Slow relationship creation without index
MATCH (p:Project), (c:Customer)
WHERE p.customerGuid = c.guid  // ← Full scan on p.customerGuid
```

**Do:**
```cypher
// Create index first
CREATE INDEX project_customer_guid IF NOT EXISTS
FOR (p:Project) ON (p.customerGuid);

// Then create relationships efficiently
MATCH (p:Project), (c:Customer)
WHERE p.customerGuid = c.guid
MERGE (c)-[:HAS_PROJECT]->(p)
```

---

## Schema Design Checklist

**For each entity type:**
- ✅ NODE KEY constraint on `guid`
- ✅ Properties follow camelCase convention
- ✅ Temporal properties use `datetime()` or `date()`
- ✅ Foreign keys stored as `{entity}Guid` properties
- ✅ Indexes on foreign key properties
- ✅ Indexes on commonly queried fields (status, dates)

**For relationships:**
- ✅ Created in separate orchestration step
- ✅ Use WHERE clauses to match by GUID
- ✅ Properties for transactional data only
- ✅ Verb-based naming (HAS_, OWNS_, BELONGS_TO_)

**For performance:**
- ✅ Batch operations (500-1000 records)
- ✅ Pre-compute aggregates for dashboards
- ✅ Use PROFILE to measure query performance
- ✅ Consider time-series aggregation for high-volume data

---

## Example Complete Schema

```cypher
// Constraints
CREATE CONSTRAINT customer_guid IF NOT EXISTS FOR (c:Customer) REQUIRE c.guid IS NODE KEY;
CREATE CONSTRAINT user_guid IF NOT EXISTS FOR (u:User) REQUIRE u.guid IS NODE KEY;
CREATE CONSTRAINT project_guid IF NOT EXISTS FOR (p:Project) REQUIRE p.guid IS NODE KEY;
CREATE CONSTRAINT phase_guid IF NOT EXISTS FOR (ph:Phase) REQUIRE ph.guid IS NODE KEY;
CREATE CONSTRAINT work_hour_guid IF NOT EXISTS FOR (w:WorkHour) REQUIRE w.guid IS NODE KEY;

// Indexes on foreign keys
CREATE INDEX project_customer_guid IF NOT EXISTS FOR (p:Project) ON (p.customerGuid);
CREATE INDEX project_owner_guid IF NOT EXISTS FOR (p:Project) ON (p.ownerGuid);
CREATE INDEX phase_project_guid IF NOT EXISTS FOR (ph:Phase) ON (ph.projectGuid);
CREATE INDEX work_hour_user_guid IF NOT EXISTS FOR (w:WorkHour) ON (w.userGuid);
CREATE INDEX work_hour_project_guid IF NOT EXISTS FOR (w:WorkHour) ON (w.projectGuid);

// Indexes on query fields
CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status);
CREATE INDEX project_deadline IF NOT EXISTS FOR (p:Project) ON (p.deadline);
CREATE INDEX work_hour_date IF NOT EXISTS FOR (w:WorkHour) ON (w.date);
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);

// Text search
CREATE TEXT INDEX customer_name_search IF NOT EXISTS FOR (c:Customer) ON (c.name);

// Sample nodes
(:Customer {guid: "cust-1", name: "Acme Corp", email: "info@acme.com"})
(:User {guid: "user-1", email: "john@acme.com", firstName: "John", lastName: "Doe"})
(:Project {guid: "proj-1", name: "Website", customerGuid: "cust-1", ownerGuid: "user-1", deadline: date("2024-12-31")})
(:Phase {guid: "phase-1", name: "Design", projectGuid: "proj-1", hourEstimate: 100.0})
(:WorkHour {guid: "wh-1", date: date("2024-10-30"), hours: 8.0, userGuid: "user-1", projectGuid: "proj-1"})

// Relationships
(:Customer)-[:HAS_PROJECT]->(:Project)
(:User)-[:OWNS]->(:Project)
(:Project)-[:HAS_PHASE]->(:Phase)
(:User)-[:LOGGED_HOURS]->(:WorkHour)
(:WorkHour)-[:FOR_PROJECT]->(:Project)
```

---

## Resources

- Neo4j Graph Data Modeling Guide: https://neo4j.com/developer/guide-data-modeling/
- Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Performance Best Practices: https://neo4j.com/developer/guide-performance-tuning/
