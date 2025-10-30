# Getting Started with {PROJECT_NAME}

Quick guide to sync your {API_NAME} data to Neo4j using this template.

## Prerequisites

**Required:**
- Python 3.12+
- Neo4j database (local or cloud)
- {API_NAME} account with API credentials
- uv package manager (`pip install uv`)

**Optional:**
- FastMCP Cloud account for MCP server deployment
- GitHub CLI (`gh`) for issue/PR workflow

---

## Step 1: Clone and Setup

```bash
# Clone template
git clone <your-repo-url>
cd {project}-sync

# Install dependencies
uv sync

# Activate virtual environment (if needed)
source .venv/bin/activate
```

---

## Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# {API_NAME} Credentials
{API_NAME_UPPER}_CLIENT_ID=your-client-id
{API_NAME_UPPER}_CLIENT_SECRET=your-secret
{API_NAME_UPPER}_API_URL=https://api.{api-name}.com
```

**Optional variables:**
```bash
# Sync configuration
SYNC_FULL_HISTORY=false  # true = all historical data
SYNC_DATE_RANGE_DAYS=365  # lookback period for time-series data
```

---

## Step 3: Customize for Your API

**Checklist:**

### A. Update API Client (`{project}_sync/api_client.py`)

1. **Authentication method:**
   - OAuth2? Update `_get_access_token()`
   - API key? Update headers in `_request()`
   - JWT? Implement token refresh logic

2. **Pagination:**
   - Token-based? Keep existing pattern
   - Offset/limit? Update `_fetch_paginated()`
   - Cursor-based? Implement cursor tracking
   - Page numbers? Adjust pagination logic

3. **Rate limiting:**
   - Update `time.sleep()` delays if needed
   - Implement exponential backoff for 429 errors

### B. Define Your Entities (`{project}_sync/entities/`)

**For each entity type:**

1. Create `{entity}.py` in `entities/` folder
2. Implement 3 methods:
   - `fetch_all_{entities}()` - API fetch
   - `sync_{entities}()` - Batch MERGE to Neo4j
   - `sync_all_{entities}()` - Orchestration

**Example structure:**
```python
async def fetch_all_customers(client):
    """Fetch from API with pagination"""
    return await client.fetch_paginated("/customers")

async def sync_customers(driver, customers):
    """Batch MERGE to Neo4j"""
    query = """
    UNWIND $batch as row
    MERGE (c:Customer {guid: row.guid})
    SET c.name = row.name, c.updatedAt = row.updatedAt
    """
    await driver.execute_query(query, batch=customers)

async def sync_all_customers(client, driver):
    """Fetch + sync"""
    customers = await fetch_all_customers(client)
    await sync_customers(driver, customers)
```

### C. Define Schema (`doc/{api_name}_schema.md`)

Document your Neo4j schema:
```cypher
// Core entities
(:Customer {guid, name, email, createdAt})
(:Project {guid, name, status, deadline})
(:User {guid, email, firstName, lastName})

// Relationships
(:Customer)-[:HAS_PROJECT]->(:Project)
(:User)-[:OWNS]->(:Project)
(:User)-[:WORKS_ON]->(:Project)

// Indexes
CREATE CONSTRAINT customer_guid IF NOT EXISTS FOR (c:Customer) REQUIRE c.guid IS NODE KEY;
CREATE CONSTRAINT project_guid IF NOT EXISTS FOR (p:Project) REQUIRE p.guid IS NODE KEY;
CREATE INDEX project_deadline IF NOT EXISTS FOR (p:Project) ON (p.deadline);
```

### D. Create Relationships (`{project}_sync/relationships/`)

1. Create relationship modules (e.g., `project_relationships.py`)
2. Register in `orchestrator.py`

**Pattern:**
```python
# relationships/project_relationships.py
async def create_project_customer_relationships(driver):
    query = """
    MATCH (p:Project), (c:Customer)
    WHERE p.customerGuid = c.guid
    MERGE (c)-[:HAS_PROJECT]->(p)
    """
    await driver.execute_query(query)

# orchestrator.py - register it
async def sync_relationships(self):
    await create_project_customer_relationships(self.driver)
    await create_project_owner_relationships(self.driver)
```

### E. Update Orchestrator (`{project}_sync/orchestrator.py`)

Register all entity sync methods:
```python
async def sync_all_entities(self):
    # Core entities first
    await sync_all_customers(self.client, self.driver)
    await sync_all_users(self.client, self.driver)
    await sync_all_projects(self.client, self.driver)

    # Transactional data
    await sync_all_invoices(self.client, self.driver)
    await sync_all_work_hours(self.client, self.driver)
```

---

## Step 4: First Sync

**Test connection:**
```bash
# Verify API credentials
uv run python -c "from {project}_sync.api_client import {API}Client; import asyncio; asyncio.run({API}Client().test_connection())"

# Verify Neo4j connection
uv run python -c "from {project}_sync.neo4j_base import Neo4jBase; import asyncio; asyncio.run(Neo4jBase().test_connection())"
```

**Run full sync:**
```bash
# Development mode (small sample)
uv run {project}_sync.py --mode sample --limit 10

# Full sync (all data)
uv run {project}_sync.py --mode full
```

**Monitor progress:**
- Check console output for entity counts
- Watch for errors or warnings
- Verify completion message

---

## Step 5: Verify Data

**Using MCP Server (if deployed):**
```bash
# Check node counts
neo4j_mcp: get_node_count()

# List all labels
neo4j_mcp: get_node_labels()

# Sample data
neo4j_mcp: execute_cypher(query="MATCH (c:Customer) RETURN c LIMIT 5")
```

**Using Neo4j Browser:**
```cypher
// Count nodes by type
MATCH (n) RETURN labels(n)[0] as Type, count(*) as Count

// Check relationships
MATCH (a)-[r]->(b) RETURN type(r) as Relationship, count(*) as Count

// Sample customers
MATCH (c:Customer) RETURN c LIMIT 10

// Sample projects with customers
MATCH (c:Customer)-[:HAS_PROJECT]->(p:Project)
RETURN c.name, p.name, p.status LIMIT 10
```

**Validate completeness:**
```bash
# Compare API record count to Neo4j
# API count:
curl -H "Authorization: Bearer $TOKEN" https://api.{api-name}.com/customers | jq 'length'

# Neo4j count:
neo4j_mcp: execute_cypher(query="MATCH (c:Customer) RETURN count(c)")
```

---

## Next Steps

**✅ You now have:**
- Working sync pipeline from {API_NAME} to Neo4j
- Scheduled or on-demand sync capability
- Graph data ready for analytics

**Continue with:**
1. [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md) - Deep dive on API patterns
2. [SCHEMA_DESIGN_GUIDE.md](./SCHEMA_DESIGN_GUIDE.md) - Optimize your graph schema
3. [TEST_GUIDE.md](./TEST_GUIDE.md) - Write comprehensive tests
4. [PERFORMANCE_OPTIMIZATION_GUIDE.md](./PERFORMANCE_OPTIMIZATION_GUIDE.md) - Speed up queries

---

## Common Issues

**"Authentication failed"**
- Check API credentials in `.env`
- Verify OAuth2 token endpoint URL
- Confirm API scopes/permissions

**"Connection refused" (Neo4j)**
- Verify Neo4j is running: `docker ps` or check service status
- Check URI format: `bolt://localhost:7687` vs `neo4j://...`
- Confirm credentials match Neo4j user

**"Rate limit exceeded"**
- Reduce batch size in API client
- Increase delay between requests
- Implement exponential backoff

**Missing relationships**
- Run `sync_relationships()` after entities
- Check GUID fields match between entities
- Verify orchestrator calls all relationship methods

---

## Support

- Check `doc/` folder for detailed guides
- Review `doc/issue_history/` for solved problems
- Search closed GitHub issues for similar problems
- Create new issue with logs and error messages
