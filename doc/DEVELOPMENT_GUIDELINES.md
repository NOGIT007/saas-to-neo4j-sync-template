# Development Guidelines

Coding standards and patterns for {PROJECT_NAME} development.

---

## Communication Style

**Be concise, sacrifice grammar for brevity:**

✅ "add indexes, 75x faster queries"
❌ "I have added database indexes which should make queries approximately 75 times faster"

✅ "fix nested object extraction in project.py"
❌ "Fixed a bug where we were not properly extracting nested objects"

**Apply to:**
- Git commit messages
- Pull request descriptions
- Issue titles and comments
- Code comments
- Documentation updates

---

## Git Workflow

### Feature Branch Workflow

**Use for all non-trivial changes:**
- New features
- Performance optimizations
- Refactoring
- Bug fixes requiring multiple commits

### 1. Create Issue

```bash
gh issue create --title "Feature/Bug: description" --body "phases + plan"
```

**Example:**
```bash
gh issue create --title "Feature: Add invoice sync support" --body "
Phase 1: API client methods for invoices
Phase 2: Entity sync module
Phase 3: Relationship creation
Phase 4: Testing and validation
"
```

### 2. Branch & Develop

```bash
git checkout -b feature/descriptive-name

# Phase 1 - implement and test
git add .
git commit -m "Phase 1: add invoice API client methods (#42)"
git push origin feature/descriptive-name

# Phase 2 - implement and test
git add .
git commit -m "Phase 2: implement invoice entity sync (#42)"
git push

# Repeat for all phases
```

### 3. Create PR After Testing

```bash
gh pr create --title "Feature: Invoice sync support" --body "
- ✅ API client methods for invoices
- ✅ Entity sync with batch MERGE
- ✅ Relationships to customers and projects
- ✅ All tests passing

Closes #42
"
```

### 4. Close Issue With Learnings

```bash
gh issue comment 42 --body "## Learnings
- Mistake: Tried to access flat fields that didn't exist in API
- Fix: Checked API docs, found nested customer object
- Lesson: Always verify API response structure before implementing
"

gh issue close 42 --comment "merged to main"
gh issue edit 42 --add-label "completed,dev-history"
```

### Direct to Main (Exceptions)

**OK to commit directly for:**
- Documentation typos
- README updates
- Minor comment fixes
- Emergency hotfixes (but test immediately!)

---

## Pre-Push Checklist

**ALWAYS run before pushing to main:**

```bash
# 1. Run tests
uv run pytest test/ -v

# 2. Check coverage (minimum 85%)
uv run pytest test/ -v --cov={project}_sync

# 3. Run full sync to verify (optional, for code changes)
uv run {project}_sync.py --mode full

# 4. Verify no regressions
uv run pytest test/ -v
```

**Requirements:**
- ✅ All tests pass
- ✅ Coverage ≥ 85%
- ✅ No linter errors (if using ruff/black)
- ✅ Full sync completes without errors

---

## Critical Patterns

### 1. Entity Single Responsibility

**Entity modules ONLY create their own entity type.**

**❌ WRONG - Creating foreign entities inline:**
```python
# project_sync.py - DON'T DO THIS
async def sync_projects(driver, projects):
    query = """
    UNWIND $batch as row
    MERGE (p:Project {guid: row.guid})
    SET p.name = row.name
    // ❌ Creating Customer inline
    MERGE (c:Customer {guid: row.customerGuid})
    MERGE (c)-[:HAS_PROJECT]->(p)
    """
    await driver.execute_query(query, batch=projects)
```

**✅ CORRECT - Store GUIDs only:**
```python
# project_sync.py - Entity sync
async def sync_projects(driver, projects):
    query = """
    UNWIND $batch as row
    MERGE (p:Project {guid: row.guid})
    SET p.name = row.name,
        p.customerGuid = row.customerGuid  // ✅ Store GUID only
    """
    await driver.execute_query(query, batch=projects)

# relationships/project_relationships.py - Separate relationship sync
async def create_project_customer_relationships(driver):
    query = """
    MATCH (p:Project), (c:Customer)
    WHERE p.customerGuid = c.guid
    MERGE (c)-[:HAS_PROJECT]->(p)
    """
    await driver.execute_query(query)
```

**Why this pattern?**
- Entity modules have single responsibility
- Easier to test individual entity sync
- Relationships created after all entities exist
- Clear separation of concerns

### 2. Relationship Orchestration

**When adding relationship methods, MUST register in orchestrator.**

**Verify counts match:**
```bash
# Count relationship methods
grep -r "def create_.*_relationships" {project}_sync/relationships/*.py | wc -l

# Count orchestrator calls
grep "create_.*_relationships()" {project}_sync/orchestrator.py | wc -l

# Counts MUST match!
```

**❌ WRONG - Add method, forget orchestrator:**
```python
# relationships/project_relationships.py
async def create_project_phase_relationships(driver):
    # ... implementation

# orchestrator.py
async def sync_relationships(self):
    await create_project_customer_relationships(self.driver)
    # ❌ Missing: create_project_phase_relationships()
```

**✅ CORRECT - Add both together:**
```python
# relationships/project_relationships.py
async def create_project_phase_relationships(driver):
    # ... implementation

# orchestrator.py
async def sync_relationships(self):
    await create_project_customer_relationships(self.driver)
    await create_project_phase_relationships(self.driver)  # ✅ Registered
```

**Commit both in same commit:**
```bash
git add {project}_sync/relationships/project_relationships.py
git add {project}_sync/orchestrator.py
git commit -m "add project-phase relationships"
```

### 3. API Nested Object Extraction

**⚠️ APIs return nested objects, NOT flat fields.**

**Before implementing entity sync:**
1. Check API documentation for schema
2. Test API endpoint with sample request
3. Look for `$ref` fields (object references)
4. Map nested paths to flat properties

**❌ WRONG - Assuming flat fields:**
```python
# Accessing non-existent fields
customer_guid = data.get("customerGuid")  # doesn't exist!
owner_email = data.get("ownerEmail")  # doesn't exist!
```

**✅ CORRECT - Navigate nested structure:**
```python
# Safely extract from nested objects
customer_guid = None
if data.get("customer"):
    customer_guid = data["customer"].get("guid")

owner_email = None
if data.get("owner"):
    owner_email = data["owner"].get("email")
```

**Use helper function:**
```python
def safe_get_nested(data, *keys, default=None):
    """Safely navigate nested dict"""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result

# Usage:
customer_guid = safe_get_nested(data, "customer", "guid")
```

### 4. Batch Operations

**Always use batch MERGE for entity sync (500-1000 records per batch).**

**❌ WRONG - One query per record:**
```python
for project in projects:
    query = "MERGE (p:Project {guid: $guid}) SET p.name = $name"
    await driver.execute_query(query, guid=project["guid"], name=project["name"])
```

**✅ CORRECT - Batch with UNWIND:**
```python
query = """
UNWIND $batch as row
MERGE (p:Project {guid: row.guid})
SET p.name = row.name, p.status = row.status
"""
await driver.execute_query(query, batch=projects)
```

**For large datasets, chunk into batches:**
```python
async def sync_projects(driver, projects):
    batch_size = 500
    for i in range(0, len(projects), batch_size):
        batch = projects[i:i+batch_size]
        query = """
        UNWIND $batch as row
        MERGE (p:Project {guid: row.guid})
        SET p.name = row.name
        """
        await driver.execute_query(query, batch=batch)
        logger.info(f"Synced batch {i//batch_size + 1}: {len(batch)} projects")
```

---

## Code Organization

### Module Structure

```
{project}_sync/
├── __init__.py
├── config.py              # Configuration classes
├── api_client.py          # API client with pagination
├── neo4j_base.py          # Base Neo4j operations
├── orchestrator.py        # Sync orchestration
├── entities/              # Entity sync modules
│   ├── __init__.py
│   ├── customer.py
│   ├── user.py
│   ├── project.py
│   └── ...
└── relationships/         # Relationship sync modules
    ├── __init__.py
    ├── customer_relationships.py
    ├── project_relationships.py
    └── ...
```

### Entity Module Template

```python
# entities/{entity}.py
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

async def fetch_all_{entities}(client) -> List[Dict]:
    """Fetch all {entities} from API with pagination"""
    logger.info("Fetching {entities} from API...")
    {entities} = await client.fetch_paginated("/{entities}")
    logger.info(f"Fetched {len({entities})} {entities}")
    return {entities}

async def sync_{entities}(driver, {entities}: List[Dict]) -> int:
    """Sync {entities} to Neo4j using batch MERGE"""
    if not {entities}:
        logger.info("No {entities} to sync")
        return 0

    query = """
    UNWIND $batch as row
    MERGE (e:{Entity} {guid: row.guid})
    SET e.name = row.name,
        e.updatedAt = datetime(row.updatedAt)
    """

    result = await driver.execute_query(query, batch={entities})
    logger.info(f"Synced {len({entities})} {entities}")
    return len({entities})

async def sync_all_{entities}(client, driver) -> int:
    """Fetch and sync all {entities}"""
    {entities} = await fetch_all_{entities}(client)
    return await sync_{entities}(driver, {entities})
```

### Relationship Module Template

```python
# relationships/{entity}_relationships.py
import logging

logger = logging.getLogger(__name__)

async def create_{entity}_relationships(driver):
    """Create relationships for {entity}"""
    query = """
    MATCH (a:{EntityA}), (b:{EntityB})
    WHERE a.{foreign_key} = b.guid
    MERGE (a)-[:RELATIONSHIP_TYPE]->(b)
    """

    result = await driver.execute_query(query)
    summary = result.summary
    rels_created = summary.counters.relationships_created
    logger.info(f"Created {rels_created} {Entity} relationships")
    return rels_created
```

---

## Testing Standards

### Test File Naming

```
test/
├── test_{entity}_coverage.py      # Entity-specific tests
├── test_relationship_coverage.py   # Relationship tests
├── test_orchestrator.py            # Integration tests
└── test_api_client.py              # API client tests
```

### Test Structure

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_sync_{entity}_success():
    """Test successful {entity} sync"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()
    {entities} = [{"guid": "1", "name": "Test"}]

    # Act
    result = await sync_{entities}(driver, {entities})

    # Assert
    assert result == 1
    driver.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_sync_{entity}_empty_list():
    """Test sync with empty list"""
    driver = Mock()
    result = await sync_{entities}(driver, [])
    assert result == 0
```

### Coverage Requirements

- Minimum: 85% overall
- Target: 95%+
- All entity modules: > 90%
- All relationship modules: > 90%

---

## Error Handling

### Logging Levels

```python
# INFO - Normal operations
logger.info(f"Fetched {len(customers)} customers")

# WARNING - Recoverable issues
logger.warning(f"API rate limit hit, retrying in {wait_time}s")

# ERROR - Failures that should be investigated
logger.error(f"Failed to sync customer {guid}: {e}")

# CRITICAL - System failures
logger.critical(f"Database connection failed: {e}")
```

### Exception Handling Pattern

```python
async def sync_entity_with_error_tracking(driver, entities):
    """Sync entities with error tracking"""
    failed = []
    succeeded = 0

    for entity in entities:
        try:
            await sync_single_entity(driver, entity)
            succeeded += 1
        except Exception as e:
            logger.error(f"Failed to sync {entity['guid']}: {e}")
            failed.append({"guid": entity["guid"], "error": str(e)})

    if failed:
        logger.warning(f"Failed to sync {len(failed)} entities")
        # Optional: write to error log
        await log_failures(failed)

    return succeeded
```

---

## Code Style

### Python Conventions

- Follow PEP 8
- Use type hints where helpful
- Max line length: 100 chars
- Use async/await for I/O operations
- Descriptive variable names (no single letters except loops)

### Cypher Conventions

- UPPERCASE for keywords: `MATCH`, `MERGE`, `SET`, `RETURN`
- camelCase for properties: `customerGuid`, `updatedAt`
- UPPER_SNAKE_CASE for relationships: `:HAS_PROJECT`, `:OWNS`
- Use parameters for all values: `$guid`, `$batch`

### Example:

```python
async def sync_projects(driver, projects: List[Dict]) -> int:
    """
    Sync projects to Neo4j using batch MERGE.

    Args:
        driver: Neo4j driver instance
        projects: List of project dicts from API

    Returns:
        Number of projects synced
    """
    if not projects:
        return 0

    query = """
    UNWIND $batch as row
    MERGE (p:Project {guid: row.guid})
    SET p.name = row.name,
        p.status = row.status,
        p.customerGuid = row.customerGuid,
        p.updatedAt = datetime(row.updatedAt)
    """

    result = await driver.execute_query(query, batch=projects)
    logger.info(f"Synced {len(projects)} projects")
    return len(projects)
```

---

## Common Anti-Patterns

### ❌ Creating Foreign Entities in Entity Sync

Don't create Customer nodes in project_sync.py - store GUIDs only.

### ❌ Adding Relationship Method Without Orchestrator Call

Both must be in same commit, verify with grep.

### ❌ Assuming Flat API Fields

Always check API docs/response structure for nested objects.

### ❌ Pushing Without Running Tests

Always run full test suite before pushing to main.

### ❌ Single-Record Database Operations

Use batch operations with UNWIND for performance.

### ❌ Missing Indexes on Foreign Keys

Index all `{entity}Guid` properties used in relationship creation.

### ❌ Creating PR Before Testing All Phases

Test each phase individually, then create PR.

---

## Commit Message Guidelines

**Format:**
```
<type>: <description>

[optional body]
[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `perf`: Performance improvement
- `refactor`: Code restructuring
- `test`: Add/update tests
- `docs`: Documentation changes
- `chore`: Maintenance tasks

**Examples:**

✅ Good:
```
feat: add invoice sync support (#42)

- API client methods for invoices
- Entity sync with batch MERGE
- Relationships to customers and projects
```

✅ Good:
```
fix: nested object extraction in project.py

API returns nested customer object, not flat customerGuid field
```

✅ Good:
```
perf: add indexes, 75x faster queries

Added indexes on Project.customerGuid and WorkHour.date
```

❌ Bad:
```
Updated project sync
```

❌ Bad:
```
I have added comprehensive support for invoices including API client methods, entity synchronization, and relationship creation. This feature allows us to sync invoice data from the API to Neo4j.
```

---

## Review Checklist

**Before submitting PR:**

- ✅ All tests pass
- ✅ Coverage ≥ 85%
- ✅ Entity methods registered in orchestrator
- ✅ Relationship methods registered in orchestrator
- ✅ Indexes created for new foreign keys
- ✅ API nested objects extracted correctly
- ✅ Batch operations used (not single-record queries)
- ✅ Concise commit messages
- ✅ Documentation updated (if needed)
- ✅ No commented-out code
- ✅ Logs at appropriate levels
