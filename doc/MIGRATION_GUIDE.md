# Schema Migration Guide

Patterns for safely evolving your Neo4j schema over time.

---

## When to Use Migrations

**Use migrations for:**
- Adding new properties to existing nodes
- Renaming properties
- Changing property types
- Adding new node labels
- Restructuring relationships
- Backfilling computed values
- Schema version upgrades

**Don't use migrations for:**
- Initial schema creation (use schema setup script)
- One-off data fixes (use manual Cypher queries)
- Testing schema changes (use development database)

---

## Migration Workflow

### 1. Development Phase

**Create migration script:**
```python
# migrations/001_add_project_priority.py
"""
Migration: Add priority field to Project nodes

Changes:
- Add priority property (low/medium/high)
- Default existing projects to "medium"
"""

async def up(driver):
    """Apply migration"""
    query = """
    MATCH (p:Project)
    WHERE NOT exists(p.priority)
    SET p.priority = 'medium',
        p.migrationVersion = '001'
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set

async def down(driver):
    """Rollback migration"""
    query = """
    MATCH (p:Project)
    WHERE p.migrationVersion = '001'
    REMOVE p.priority, p.migrationVersion
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set
```

### 2. Testing Phase

**Test on development database:**
```bash
# Apply migration
uv run python migrations/run_migration.py --migration 001 --action up

# Verify results
neo4j_mcp: execute_cypher(query="MATCH (p:Project) RETURN p.priority, count(*)")

# Test rollback
uv run python migrations/run_migration.py --migration 001 --action down

# Verify rollback
neo4j_mcp: execute_cypher(query="MATCH (p:Project) WHERE exists(p.priority) RETURN count(*)")
```

### 3. Dry-Run Phase

**Test on production data without committing:**
```python
# migrations/run_migration.py
async def run_migration_dry_run(driver, migration_module):
    """Run migration in transaction, then rollback"""
    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            # Apply migration
            result = await migration_module.up(tx)
            print(f"Would update {result} records")

            # Count affected nodes
            verify_query = "MATCH (n) WHERE n.migrationVersion = '001' RETURN count(n) as count"
            verify_result = await tx.run(verify_query)
            record = await verify_result.single()
            print(f"Affected nodes: {record['count']}")

            # Rollback transaction (dry-run)
            await tx.rollback()
            print("Dry-run complete (changes rolled back)")
```

```bash
# Run dry-run
uv run python migrations/run_migration.py --migration 001 --action up --dry-run
```

### 4. Production Deployment

**Apply migration to production:**
```bash
# Backup database first!
# For Neo4j AuraDB: Automatic backups
# For self-hosted: neo4j-admin backup

# Apply migration
uv run python migrations/run_migration.py --migration 001 --action up

# Verify success
uv run python migrations/verify_migration.py --migration 001
```

---

## Migration Patterns

### Pattern 1: Adding New Property

**Scenario:** Add `status` field to all Customer nodes.

```python
# migrations/002_add_customer_status.py
async def up(driver):
    """Add status property to Customer nodes"""
    query = """
    MATCH (c:Customer)
    WHERE NOT exists(c.status)
    SET c.status = CASE
        WHEN exists((c)-[:HAS_PROJECT]->(:Project {status: 'active'}))
        THEN 'active'
        ELSE 'inactive'
    END,
    c.migrationVersion = '002'
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set

async def down(driver):
    """Remove status property"""
    query = """
    MATCH (c:Customer)
    WHERE c.migrationVersion = '002'
    REMOVE c.status, c.migrationVersion
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set
```

### Pattern 2: Renaming Property

**Scenario:** Rename `customerGuid` to `customerId` for consistency.

```python
# migrations/003_rename_customer_guid.py
async def up(driver):
    """Rename customerGuid to customerId"""
    query = """
    MATCH (p:Project)
    WHERE exists(p.customerGuid) AND NOT exists(p.customerId)
    SET p.customerId = p.customerGuid
    REMOVE p.customerGuid
    SET p.migrationVersion = '003'
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set

async def down(driver):
    """Rollback: rename back to customerGuid"""
    query = """
    MATCH (p:Project)
    WHERE c.migrationVersion = '003'
    SET p.customerGuid = p.customerId
    REMOVE p.customerId, p.migrationVersion
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set
```

### Pattern 3: Changing Property Type

**Scenario:** Convert `deadline` from string to date type.

```python
# migrations/004_convert_deadline_to_date.py
async def up(driver):
    """Convert deadline from string to date"""
    query = """
    MATCH (p:Project)
    WHERE exists(p.deadline) AND NOT p.deadline IS date
    WITH p, p.deadline as oldDeadline
    SET p.deadline = date(oldDeadline),
        p.migrationVersion = '004'
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set

async def down(driver):
    """Rollback: convert back to string"""
    query = """
    MATCH (p:Project)
    WHERE p.migrationVersion = '004'
    SET p.deadline = toString(p.deadline)
    REMOVE p.migrationVersion
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set
```

### Pattern 4: Adding Computed Properties

**Scenario:** Pre-compute project completion percentage.

```python
# migrations/005_add_completion_pct.py
async def up(driver):
    """Calculate and store completion percentage"""
    query = """
    MATCH (p:Project)
    WHERE NOT exists(p.completionPct)
    OPTIONAL MATCH (p)<-[wh:LOGGED_HOURS]-()
    WITH p, coalesce(sum(wh.hours), 0) as hoursWorked
    SET p.completionPct = CASE
        WHEN p.hourEstimate > 0 THEN hoursWorked / p.hourEstimate * 100.0
        ELSE 0
    END,
    p.migrationVersion = '005'
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set

async def down(driver):
    """Remove completion percentage"""
    query = """
    MATCH (p:Project)
    WHERE p.migrationVersion = '005'
    REMOVE p.completionPct, p.migrationVersion
    """
    result = await driver.execute_query(query)
    return result.summary.counters.properties_set
```

### Pattern 5: Restructuring Relationships

**Scenario:** Change (:User)-[:LOGGED_HOURS]->(:Project) to (:User)-[:LOGGED]->(:WorkHour)-[:FOR]->(:Project)

```python
# migrations/006_restructure_work_hours.py
async def up(driver):
    """Create WorkHour nodes from LOGGED_HOURS relationships"""
    query = """
    MATCH (u:User)-[rel:LOGGED_HOURS]->(p:Project)
    CREATE (wh:WorkHour {
        guid: randomUUID(),
        hours: rel.hours,
        date: rel.date,
        billable: rel.billable,
        userGuid: u.guid,
        projectGuid: p.guid,
        migrationVersion: '006'
    })
    MERGE (u)-[:LOGGED]->(wh)
    MERGE (wh)-[:FOR]->(p)
    DELETE rel
    """
    result = await driver.execute_query(query)
    counters = result.summary.counters
    return {
        "nodes_created": counters.nodes_created,
        "relationships_deleted": counters.relationships_deleted,
        "relationships_created": counters.relationships_created
    }

async def down(driver):
    """Rollback: Delete WorkHour nodes, recreate LOGGED_HOURS relationships"""
    query = """
    MATCH (u:User)-[:LOGGED]->(wh:WorkHour {migrationVersion: '006'})-[:FOR]->(p:Project)
    MERGE (u)-[rel:LOGGED_HOURS]->(p)
    SET rel.hours = wh.hours,
        rel.date = wh.date,
        rel.billable = wh.billable
    DETACH DELETE wh
    """
    result = await driver.execute_query(query)
    return result.summary.counters.nodes_deleted
```

### Pattern 6: Batch Processing for Large Datasets

**Scenario:** Update 1 million+ nodes in batches.

```python
# migrations/007_batch_update_large_dataset.py
async def up(driver):
    """Update large dataset in batches"""
    batch_size = 10000
    total_updated = 0

    while True:
        query = """
        MATCH (p:Project)
        WHERE NOT exists(p.normalizedName)
        WITH p LIMIT $batch_size
        SET p.normalizedName = toLower(trim(p.name)),
            p.migrationVersion = '007'
        RETURN count(p) as updated
        """

        result = await driver.execute_query(query, batch_size=batch_size)
        record = result.records[0]
        updated = record["updated"]
        total_updated += updated

        print(f"Updated {updated} nodes (total: {total_updated})")

        if updated < batch_size:
            break

    return total_updated

async def down(driver):
    """Remove normalized name in batches"""
    batch_size = 10000
    total_removed = 0

    while True:
        query = """
        MATCH (p:Project)
        WHERE p.migrationVersion = '007'
        WITH p LIMIT $batch_size
        REMOVE p.normalizedName, p.migrationVersion
        RETURN count(p) as removed
        """

        result = await driver.execute_query(query, batch_size=batch_size)
        record = result.records[0]
        removed = record["removed"]
        total_removed += removed

        if removed < batch_size:
            break

    return total_removed
```

---

## Migration Runner

### Migration Manager

```python
# migrations/manager.py
import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manage schema migrations"""

    def __init__(self, driver):
        self.driver = driver
        self.migrations_dir = Path(__file__).parent

    async def get_applied_migrations(self):
        """Get list of applied migrations from database"""
        query = """
        MATCH (m:Migration)
        RETURN m.version as version, m.appliedAt as appliedAt
        ORDER BY m.version
        """
        result = await self.driver.execute_query(query)
        return [record["version"] for record in result.records]

    async def mark_migration_applied(self, version):
        """Mark migration as applied"""
        query = """
        MERGE (m:Migration {version: $version})
        SET m.appliedAt = datetime()
        """
        await self.driver.execute_query(query, version=version)

    async def mark_migration_reverted(self, version):
        """Mark migration as reverted"""
        query = """
        MATCH (m:Migration {version: $version})
        DELETE m
        """
        await self.driver.execute_query(query, version=version)

    async def run_migration(self, version, action="up", dry_run=False):
        """Run a specific migration"""
        # Load migration module
        migration_module = importlib.import_module(f"migrations.{version}")

        if action == "up":
            logger.info(f"Applying migration {version}...")
            if dry_run:
                logger.info("DRY RUN - changes will be rolled back")

            result = await migration_module.up(self.driver)
            logger.info(f"Migration {version} applied: {result}")

            if not dry_run:
                await self.mark_migration_applied(version)
            else:
                # For dry-run, show what would happen but don't commit
                logger.info("Dry-run complete - no changes committed")

        elif action == "down":
            logger.info(f"Reverting migration {version}...")
            result = await migration_module.down(self.driver)
            logger.info(f"Migration {version} reverted: {result}")

            if not dry_run:
                await self.mark_migration_reverted(version)

        return result

    async def run_pending_migrations(self):
        """Run all pending migrations"""
        # Get applied migrations
        applied = await self.get_applied_migrations()

        # Get all migration files
        migration_files = sorted(self.migrations_dir.glob("[0-9]*.py"))

        # Run pending migrations
        for migration_file in migration_files:
            version = migration_file.stem
            if version not in applied:
                await self.run_migration(version, action="up")
```

### CLI Runner

```python
# migrations/run_migration.py
import asyncio
import argparse
from manager import MigrationManager
from {project}_sync.neo4j_base import Neo4jBase

async def main():
    parser = argparse.ArgumentParser(description="Run Neo4j migrations")
    parser.add_argument("--migration", help="Migration version (e.g., 001)")
    parser.add_argument("--action", choices=["up", "down"], default="up")
    parser.add_argument("--dry-run", action="store_true", help="Test migration without committing")
    parser.add_argument("--all", action="store_true", help="Run all pending migrations")

    args = parser.parse_args()

    # Connect to Neo4j
    neo4j = Neo4jBase()
    driver = await neo4j.get_driver()

    # Run migrations
    manager = MigrationManager(driver)

    if args.all:
        await manager.run_pending_migrations()
    elif args.migration:
        await manager.run_migration(args.migration, action=args.action, dry_run=args.dry_run)
    else:
        print("Specify --migration or --all")

    await driver.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Usage:**
```bash
# Run specific migration
uv run python migrations/run_migration.py --migration 001 --action up

# Dry-run (test without committing)
uv run python migrations/run_migration.py --migration 001 --action up --dry-run

# Rollback migration
uv run python migrations/run_migration.py --migration 001 --action down

# Run all pending migrations
uv run python migrations/run_migration.py --all
```

---

## Version Tracking

### Schema Version Node

```cypher
// Store current schema version
MERGE (meta:Metadata {key: "schema_version"})
SET meta.version = "1.2.0",
    meta.updatedAt = datetime()
```

### Migration History

```cypher
// Track applied migrations
(:Migration {
  version: "001",
  name: "add_project_priority",
  appliedAt: datetime("2024-10-30T14:30:00Z"),
  appliedBy: "admin",
  status: "completed"
})
```

**Query migration history:**
```cypher
MATCH (m:Migration)
RETURN m.version, m.name, m.appliedAt
ORDER BY m.version
```

---

## Rollback Strategies

### Strategy 1: Immediate Rollback

**For recent migrations that caused issues:**
```bash
# Rollback last migration
uv run python migrations/run_migration.py --migration 001 --action down
```

### Strategy 2: Restore from Backup

**For complex migrations that can't be easily rolled back:**
```bash
# Stop application
# Restore Neo4j from backup
# Resume application with previous schema version
```

### Strategy 3: Forward Fix

**For migrations in production:**
```python
# migrations/002_fix_001.py
async def up(driver):
    """Fix issues introduced by migration 001"""
    # Apply corrective changes
    ...
```

---

## Testing Migrations

### Unit Tests

```python
# test/test_migrations.py
import pytest
from migrations.001_add_project_priority import up, down

@pytest.mark.asyncio
async def test_migration_001_up(mock_driver):
    """Test migration 001 applies successfully"""
    result = await up(mock_driver)
    assert result > 0
    mock_driver.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_migration_001_down(mock_driver):
    """Test migration 001 rolls back successfully"""
    result = await down(mock_driver)
    assert result > 0
    mock_driver.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_migration_001_idempotent(mock_driver):
    """Test migration can be run multiple times"""
    # Run migration twice
    await up(mock_driver)
    await up(mock_driver)

    # Should not fail or create duplicates
    # Verify with WHERE NOT exists(property) in query
```

### Integration Tests

```python
@pytest.mark.live
@pytest.mark.asyncio
async def test_migration_001_integration(live_driver):
    """Test migration on real database"""
    # Apply migration
    result = await up(live_driver)
    assert result > 0

    # Verify results
    verify_query = "MATCH (p:Project) WHERE exists(p.priority) RETURN count(p) as count"
    verify_result = await live_driver.execute_query(verify_query)
    count = verify_result.records[0]["count"]
    assert count > 0

    # Rollback
    await down(live_driver)

    # Verify rollback
    rollback_result = await live_driver.execute_query(verify_query)
    rollback_count = rollback_result.records[0]["count"]
    assert rollback_count == 0
```

---

## Migration Best Practices

**✅ DO:**
- Write both `up()` and `down()` functions
- Test migrations on development database first
- Use dry-run before production deployment
- Make migrations idempotent (safe to run multiple times)
- Batch process large datasets (10,000 records per batch)
- Mark nodes with migration version for tracking
- Document what the migration changes
- Backup database before major migrations

**❌ DON'T:**
- Run migrations on production without testing
- Create migrations that can't be rolled back
- Assume all nodes have required properties (use WHERE exists())
- Delete data without backup
- Run multiple migrations simultaneously
- Modify migration files after they're applied

---

## Migration Checklist

**Before creating migration:**
- ✅ Identify what needs to change
- ✅ Plan rollback strategy
- ✅ Write migration script (up + down)
- ✅ Add unit tests

**Before applying to production:**
- ✅ Test on development database
- ✅ Run dry-run on production data
- ✅ Backup database
- ✅ Schedule downtime (if needed)
- ✅ Verify rollback works

**After applying migration:**
- ✅ Verify changes with Cypher queries
- ✅ Check application functionality
- ✅ Monitor performance
- ✅ Document changes in CHANGELOG
- ✅ Update schema documentation

---

## Example: Complete Migration

```python
# migrations/008_add_project_risk_score.py
"""
Migration: Add risk score to projects

Changes:
- Add riskScore property (0-100)
- Calculate based on:
  - Completion % vs deadline
  - Hours worked vs estimate
  - Budget vs actual costs

Rollback:
- Remove riskScore property
"""

async def up(driver):
    """Calculate and add risk score"""
    query = """
    MATCH (p:Project)
    WHERE NOT exists(p.riskScore)

    WITH p,
      // Calculate overrun risk
      CASE
        WHEN p.hourEstimate > 0 AND p.hoursWorked / p.hourEstimate > 0.9
        THEN 30
        ELSE 0
      END as overrunRisk,

      // Calculate deadline risk
      CASE
        WHEN p.deadline < date() AND p.status <> 'completed'
        THEN 50
        WHEN duration.between(date(), p.deadline).days < 30
        THEN 20
        ELSE 0
      END as deadlineRisk,

      // Calculate budget risk
      CASE
        WHEN p.totalCost > p.expectedValue * 0.9
        THEN 20
        ELSE 0
      END as budgetRisk

    SET p.riskScore = overrunRisk + deadlineRisk + budgetRisk,
        p.migrationVersion = '008',
        p.riskScoreCalculatedAt = datetime()

    RETURN count(p) as updated
    """

    result = await driver.execute_query(query)
    updated = result.records[0]["updated"]
    return updated

async def down(driver):
    """Remove risk score"""
    query = """
    MATCH (p:Project)
    WHERE p.migrationVersion = '008'
    REMOVE p.riskScore, p.riskScoreCalculatedAt, p.migrationVersion
    RETURN count(p) as reverted
    """

    result = await driver.execute_query(query)
    reverted = result.records[0]["reverted"]
    return reverted
```

**Apply migration:**
```bash
# Test on dev
uv run python migrations/run_migration.py --migration 008 --action up --dry-run

# Apply to dev
uv run python migrations/run_migration.py --migration 008 --action up

# Verify
neo4j_mcp: execute_cypher(query="MATCH (p:Project) RETURN p.riskScore, count(*)")

# Test rollback on dev
uv run python migrations/run_migration.py --migration 008 --action down

# Apply to production (after backup!)
uv run python migrations/run_migration.py --migration 008 --action up
```
