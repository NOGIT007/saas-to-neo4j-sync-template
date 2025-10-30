# CLAUDE.md - Implementation Details

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔴 CRITICAL: Always Use MCP Server for Testing

**ALWAYS use the connected MCP server `{project}mcp` for ALL Neo4j operations and testing.**

✅ **Connected MCP Server:** `{project}mcp` (live connection)

**When to use:**
- Testing new MCP tools
- Querying Neo4j database
- Verifying dashboard metrics
- Checking sync results
- ANY Neo4j database operation

**Example Usage:**
```
# Test dashboard metrics
Use {project}mcp: get_dashboard_metrics()

# Query entity list
Use {project}mcp: get_{entity}_list(filters={"is_closed": False}, limit=10)

# Check if data was synced
Use {project}mcp: execute_cypher(query="MATCH (n:{Entity}) RETURN count(n) as count")
```

**DO NOT:**
- ❌ Try to connect directly to Neo4j via code
- ❌ Run `python main.py` for testing
- ❌ Use local driver connections

**ALWAYS:**
- ✅ Use `{project}mcp` MCP server for all Neo4j interactions
- ✅ This server is already connected and ready to use

## Project Overview

{PROJECT_NAME} Neo4j Sync - A modular sync framework that syncs data from {API_NAME} to Neo4j graph database. Built with async Neo4j driver and modular architecture.

## Architecture

**Modular package design (`{project}_sync/`):**
- `config.py`: Configuration dataclasses loaded from environment
- `{api}_client.py`: API client with pagination, retry logic, rate limiting
- `neo4j_base.py`: Base class for Neo4j operations
- `orchestrator.py`: Coordinates all sync operations
- `entities/`: Entity sync modules (one per entity type)
- `relationships/`: Relationship creation modules
- `metrics/`: Metrics calculation modules
- `analytics/`: Time-series aggregation and denormalization
- `migrations/`: Schema migration modules

**Key components:**
1. **Connection management**: Base class pattern with connection pooling
2. **Orchestration**: Single entry point coordinates all operations
3. **Entity modules**: Single responsibility - one entity type per module
4. **Relationship modules**: Create relationships using stored GUIDs
5. **Metrics**: Calculate derived metrics during sync

## Development Commands

**Setup:**
```bash
cp .env.example .env  # Configure Neo4j and {API_NAME} credentials
uv sync              # Install dependencies
```

**Run sync:**
```bash
uv run {project}_sync.py              # Full sync
uv run {project}_sync.py --mode full  # Full sync with indexes
```

**Run tests:**
```bash
# Structural tests (no database needed)
uv run pytest test/ -v -m "not live"

# Full test suite (requires synced data)
uv run pytest test/ -v
```

**Run MCP server locally:**
```bash
fastmcp dev main.py  # Interactive testing
python main.py       # Start uvicorn server
```

## Code Modification Guidelines

**When adding new entity sync modules:**
1. Create new file in `{project}_sync/entities/{entity}.py`
2. Inherit from `Neo4jBase`
3. Implement `sync_{entity}(data: Dict) -> bool` method
4. Extract nested object GUIDs (never create foreign entities)
5. Use MERGE with NODE KEY constraint
6. Register in `orchestrator.py` sync methods

**When adding new relationship methods:**
1. Create method in appropriate `relationships/*.py` file
2. Use MATCH to find both nodes by GUIDs
3. Use MERGE to create relationship
4. Return count for verification
5. **CRITICAL**: Register call in `orchestrator.py` create_relationships method
6. Verify with: `grep -r "def create_.*_relationships" {project}_sync/relationships/*.py | wc -l`

**Connection handling:**
- Always use `Neo4jBase` as parent class
- Driver is initialized in `__init__`, reused across methods
- Connection pooling handled automatically
- Close connections in orchestrator finally block

**Cypher query safety:**
- Always use parameterized queries via `parameters` dict
- Never use f-strings for user input in queries
- Use NODE KEY constraints to prevent duplicates

## {API_NAME} Sync Architecture

**Modular Sync Package** - All sync logic in `{project}_sync/` package with CLI entry point.

**Quick Start:**
```bash
# Setup
uv sync

# Full sync
uv run {project}_sync.py --mode full
```

**Architecture Components:**
- `{project}_sync/orchestrator.py` - Coordinates all sync operations
- `{project}_sync/{api}_client.py` - API client with pagination & retry (~N methods)
- `{project}_sync/neo4j_base.py` - Base Neo4j operations
- `{project}_sync/entities/` - Entity sync modules (~N modules)
- `{project}_sync/relationships/` - Relationship modules (~N modules)
- `{project}_sync/metrics/` - Metrics calculator

**Features:**
- **N entity types**: {List entity types here}
- **Modular design**: Each entity type has its own sync module
- **Composable relationships**: Separate relationship modules
- **Inline metrics**: Metrics calculated during sync
- **Performance**: Full sync ~X minutes
- **Configurable data range**: Default N days, supports historical backfill

**Requirements:**
- {API_NAME} API credentials
- {API_NAME} API scopes: {list required scopes}
- Neo4j connection
- Configure in `.env` file

**Data Range Configuration:**

By default, transactional data (e.g., transactions, events) are synced for the last N days. Customize:

```bash
# Option 1: Change lookback period (in .env)
SYNC_{ENTITY}_DAYS_BACK=730  # Last 2 years

# Option 2: Full historical backfill (in .env)
SYNC_{ENTITY}_START_DATE=2020-01-01  # All data since date

# Option 3: Keep default (N days)
# Don't set either variable
```

## File Structure

### Core Application Files

- **main.py** - FastMCP server with MCP tools. Exposes Neo4j operations to Claude AI. Uses async Neo4j driver. Critical: app variable must be named `app`.

- **{project}_sync.py** - CLI script for sync. Entry point using modular `{project}_sync/` package. Supports `--mode full` for complete sync.

### {project}_sync/ - Modular Sync Package

**Core Infrastructure:**
- **config.py** - Configuration classes loaded from environment
- **{api}_client.py** - API client with pagination, retry logic, rate limiting
- **neo4j_base.py** - Base class for Neo4j operations
- **orchestrator.py** - Coordinates full sync workflow

**Entity Sync Modules (entities/):**
- {entity}.py - Entity sync modules (~3 methods each)

**Relationship Modules (relationships/):**
- {entity}_relationships.py - Relationship creation modules

**Metrics Module (metrics/):**
- metrics.py - Calculates metrics inline during sync

**Analytics Module (analytics/):**
- aggregation_nodes.py - Time-series aggregation (Month/Quarter/Year)
- denormalization.py - Performance optimization patterns

**Migrations Module (migrations/):**
- migration_001_create_indexes.py - Schema migrations with dry-run support

### Configuration Files

- **.env.example** - Environment variable template
- **requirements.txt** - Python dependencies
- **pyproject.toml** - Project metadata and uv configuration
- **.gitignore** - Git ignore patterns

### Documentation

- **README.md** - Setup and deployment guide
- **CLAUDE.md** - Project-level workflow guidance
- **.claude/CLAUDE.md** - This file - implementation details
- **TEMPLATE_USAGE.md** - How to customize this template

### doc/ - API Documentation & Design

- **doc/{api}_doc.json** - API specification (if available)
- **doc/{schema}_design.txt** - Neo4j schema design
- **doc/{API}_doc.md** - API integration documentation
- **doc/DEVELOPMENT_GUIDELINES.md** - Coding standards
- **doc/TEST_GUIDE.md** - Testing instructions
- **doc/PERFORMANCE_OPTIMIZATION_GUIDE.md** - Optimization strategies

### task/ - Project Planning

- **task/TASK_MASTER_GUIDE.md** - Overview of all tasks
- **task/task_NN_{feature}.md** - Individual task documentation

### test/ - Testing Infrastructure

- **test/pytest.ini** - Pytest configuration
- **test/test_coverage.py** - Orchestration tests
- **test/test_*.py** - Test modules

## Tools Summary

**Read tools:**
- execute_cypher - General query execution
- get_schema - Graph schema information
- get_node_labels - List all node types
- get_relationship_types - List all relationship types

**TODO: Add your custom tools:**
- get_dashboard_metrics - Top-level KPIs
- get_{entity}_list - Entity list with filters
- get_{entity}_detail - Single entity details
- search_{entity} - Search entities

## Performance Optimization

**Three-Phase Strategy:**

**Phase 1: Indexes (60-80% improvement)**
- Unique constraints on GUIDs
- Property indexes on queried fields
- Composite indexes for multi-field queries

**Phase 2: Time-Series Aggregation (80-95% improvement)**
- Pre-aggregate to Month/Quarter/Year nodes
- Calculate metrics during sync
- Hierarchical relationships for roll-ups

**Phase 3: Analytics Denormalization (further gains)**
- Denormalize multi-hop traversals (3+ hops)
- Create aggregation nodes
- Derived relationships
- Health scores pre-calculated

## TODO: Customize This File

**Replace placeholders:**
- `{PROJECT_NAME}` → Your project name
- `{API_NAME}` → Your API name
- `{project}` → Your project slug
- `{api}` → Your API slug
- `{Entity}` → Your entity names
- `{entity}` → Your entity names (lowercase)

**Update sections:**
- Add your actual entity types
- List your relationship types
- Document your API quirks
- Add your custom MCP tools
