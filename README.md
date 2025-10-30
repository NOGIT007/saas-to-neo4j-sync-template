# SaaS to Neo4j Sync Template

**Production-ready template for syncing any SaaS API to Neo4j graph database.**

Battle-tested patterns extracted from real-world example API integration. Skip 20-30 hours of setup and get straight to building your knowledge graph.

---

## Why Use This Template?

**Built from proven production code:**
- Modular architecture tested with 16 entity types
- Handles complex API patterns (OAuth2, nested objects, pagination)
- Performance optimized (213x faster dashboard queries)
- 85%+ test coverage with two-phase testing strategy
- Complete documentation from actual implementation

**What you get:**
- Drop-in code templates for API integration
- Neo4j schema best practices
- Claude AI development workflows
- Testing infrastructure
- Performance optimization playbook
- Real-world examples and anti-patterns

**Time savings:**
- Setup: 30 minutes (vs 2-4 hours from scratch)
- API integration: 2-4 hours (vs 8-12 hours)
- Schema design: 2-3 hours (with comprehensive guide)
- Testing: 2-3 hours (templates provided)
- **Total:** 10-15 hours to production vs 30-40 hours from scratch

---

## What's Included

### Core Infrastructure
- **Modular sync architecture** - Separate concerns: API client, entity sync, relationships, orchestration
- **FastMCP server** - Expose graph to Claude AI via Model Context Protocol
- **Two-phase testing** - Structural tests (fast) + integration tests (comprehensive)
- **Performance optimization** - Three-phase strategy with real benchmarks
- **Schema migration system** - Safe production schema evolution

### Battle-Tested Patterns
- **API Integration** - OAuth2, token refresh, pagination (token/offset/cursor), rate limiting, retries
- **Nested Object Extraction** - Critical pattern for complex API responses
- **Entity Single Responsibility** - Clean separation of entity creation and relationship building
- **Batch Operations** - Efficient bulk inserts with UNWIND
- **Relationship Orchestration** - Systematic relationship creation after entity sync
- **Inline Metrics** - Calculate derived metrics during sync

### Documentation (7 Comprehensive Guides)
1. **GETTING_STARTED.md** - 5-minute setup to first sync
2. **API_INTEGRATION_GUIDE.md** - Authentication, pagination, nested objects
3. **SCHEMA_DESIGN_GUIDE.md** - Graph modeling best practices
4. **DEVELOPMENT_GUIDELINES.md** - Coding standards and workflows
5. **TEST_GUIDE.md** - Two-phase testing strategy
6. **PERFORMANCE_OPTIMIZATION_GUIDE.md** - 3-phase optimization playbook
7. **MIGRATION_GUIDE.md** - Safe schema evolution

### Development Workflows
- **Feature branch workflow** - Issue tracking, phased development, preview testing
- **Pre-push checklist** - Automated quality gates
- **Concise communication** - Git commits, PRs, issues
- **Issue learnings** - Document mistakes/fixes for future reference

---

## Quick Start (5 Minutes)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd {project}-sync
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your Neo4j + API credentials

# 3. Customize for your API (see TEMPLATE_USAGE.md)
# Replace placeholders: {PROJECT_NAME}, {API_NAME}, {project}, etc.

# 4. Test connection
uv run python -c "from {project}_sync.config import Neo4jConfig; print('Config loaded')"

# 5. First sync (after customization)
uv run {project}_sync.py --mode full
```

**Next steps:** See [TEMPLATE_USAGE.md](./TEMPLATE_USAGE.md) for complete customization guide.

---

## Architecture Overview

```
SaaS API                    Neo4j Graph Database
┌─────────────┐            ┌──────────────────┐
│             │            │                  │
│  OAuth2     │◄───auth────┤  API Client      │
│  REST API   │            │  - Token refresh │
│  Pagination │──fetch────►│  - Pagination    │
│  Rate Limit │            │  - Retry logic   │
│             │            │                  │
└─────────────┘            └────────┬─────────┘
                                    │
                           ┌────────▼─────────┐
                           │  Orchestrator    │
                           │  - Coordinates   │
                           │  - Error handling│
                           └────────┬─────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼──────┐  ┌────▼────┐  ┌──────▼──────┐
            │ Entity Sync  │  │Relation-│  │  Metrics    │
            │ - Customer   │  │ships    │  │  Calculator │
            │ - Project    │  │- OWNED_BY│  │- Aggregates│
            │ - User       │  │- HAS_PHASE│ │- Derived   │
            │ - etc.       │  │- etc.    │  │            │
            └──────────────┘  └─────────┘  └────────────┘
                                    │
                           ┌────────▼─────────┐
                           │   Neo4j Graph    │
                           │  ┌─────────┐     │
                           │  │Customer │     │
                           │  └────┬────┘     │
                           │       │OWNS      │
                           │  ┌────▼────┐     │
                           │  │Project  │     │
                           │  └────┬────┘     │
                           │       │HAS       │
                           │  ┌────▼────┐     │
                           │  │WorkHour │     │
                           │  └─────────┘     │
                           └──────────────────┘
                                    │
                           ┌────────▼─────────┐
                           │  FastMCP Server  │
                           │  - Query tools   │
                           │  - Dashboard API │
                           │  - Claude AI     │
                           └──────────────────┘
```

**Key Components:**

1. **API Client** - Handles authentication, pagination, rate limiting
2. **Entity Sync** - One module per entity type, only creates own entities
3. **Relationship Sync** - Creates connections after all entities exist
4. **Metrics Calculator** - Computes derived properties inline
5. **Orchestrator** - Coordinates full sync workflow
6. **FastMCP Server** - Exposes graph to Claude AI

---

## Key Features

### 1. Modular Architecture
**Separation of concerns:**
- `{api}_client.py` - API integration only
- `entities/*.py` - Entity creation only (one per entity type)
- `relationships/*.py` - Relationship creation only
- `metrics/*.py` - Metric calculation only
- `orchestrator.py` - Workflow coordination

**Benefits:**
- Easy to test individual components
- Clear responsibility boundaries
- Simple to add new entity types
- Maintainable codebase

### 2. API Integration Patterns
**Handles complex scenarios:**
- OAuth2 with automatic token refresh
- Multiple pagination types (token, offset, cursor, page-number)
- Rate limiting with exponential backoff
- Nested object extraction (critical!)
- Date range filtering for large datasets
- Retry logic with configurable attempts

**Example - Nested Object Extraction:**
```python
# API returns nested objects, not flat fields
# WRONG:
customer_guid = data.get("customerGuid")  # doesn't exist!

# CORRECT:
customer_guid = None
if data.get("customer"):
    customer_guid = data["customer"].get("guid")
```

### 3. Entity Single Responsibility Pattern
**Critical design principle:**
- Entity sync modules ONLY create their own entity type
- Store foreign GUIDs as properties
- Relationships created in separate orchestration step

**Example:**
```python
# In project.py - ONLY create Project nodes
query = """
MERGE (p:Project {guid: $guid})
SET p.name = $name,
    p.customerGuid = $customerGuid  # Store GUID only!
"""
# Customer node created elsewhere, relationship created later
```

**Why this matters:**
- Avoids duplicate entity creation
- Clear dependency ordering
- Easy to test
- Relationships can reference any entity

### 4. Two-Phase Testing Strategy
**Fast + comprehensive:**

**Phase 1: Structural Tests** (fast, no external dependencies)
```bash
uv run pytest test/ -v -m "not live" --cov={project}_sync
# Target: 85%+ coverage
```

**Phase 2: Integration Tests** (live Neo4j + API)
```bash
uv run {project}_sync.py --mode full
uv run pytest test/ -v
```

**Pre-push checklist:**
1. Run structural tests → verify coverage ≥ 85%
2. Run full sync → verify data in Neo4j
3. Run integration tests → verify end-to-end

### 5. Performance Optimization (3 Phases)

**Phase 1: Indexes** (60-80% improvement, 30 minutes)
```cypher
CREATE INDEX project_customer_guid IF NOT EXISTS
FOR (p:Project) ON (p.customerGuid);
```
Real result: Dashboard KPIs 3200ms → 800ms

**Phase 2: Time-Series Aggregation** (80-95% improvement, 2-3 hours)
```cypher
CREATE (m:Month {year: 2024, month: 10})
SET m.totalHours = sum_of_work_hours,
    m.totalRevenue = sum_of_revenue
```
Real result: Time-series queries 5500ms → 300ms

**Phase 3: Analytics Denormalization** (instant queries, 2-3 hours)
```cypher
SET project.hoursWorked = calculated_total,
    project.totalRevenue = calculated_revenue
```
Real result: Dashboard KPIs 800ms → 15ms (213x faster total)

**See:** `doc/PERFORMANCE_OPTIMIZATION_GUIDE.md` for complete strategy

### 6. Schema Migration System
**Safe production evolution:**
```python
# migrations/001_add_project_status.py
def up(tx):
    """Add status property to Project nodes"""
    tx.run("""
        MATCH (p:Project)
        WHERE p.status IS NULL
        SET p.status = 'active'
    """)

def down(tx):
    """Rollback - remove status property"""
    tx.run("MATCH (p:Project) REMOVE p.status")
```

**Workflow:** Dev → Test → Dry-run → Backup → Production → Verify

### 7. FastMCP Server Integration
**Expose graph to Claude AI:**
```python
@app.tool()
async def get_project_dashboard_metrics(filters: dict = None):
    """Get dashboard KPIs matching SaaS UI"""
    # Returns: order_book, work_in_progress, hours_this_month, etc.
```

**Deploy to FastMCP Cloud:**
```bash
# Configure main.py:app as entrypoint
fastmcp deploy
```

---

## Customization Overview

**This template uses placeholders that you replace with your specifics:**

```
{PROJECT_NAME}      → "Salesforce Neo4j Sync"
{API_NAME}          → "Salesforce"
{API_NAME_UPPER}    → "SALESFORCE" (for env vars)
{project}           → "salesforce" (file/module names)
{api}               → "salesforce" (API client name)
{Entity}            → "Account", "Contact", etc.
{entity}            → "account", "contact"
{entities}          → "accounts", "contacts"
```

**Complete customization guide:** [TEMPLATE_USAGE.md](./TEMPLATE_USAGE.md)

**Quick customization checklist:**
1. Search/replace all placeholders in code
2. Implement authentication in `{api}_client.py`
3. Add entity fetch methods to API client
4. Design Neo4j schema for your entities
5. Create entity sync modules
6. Create relationship modules
7. Register all methods in orchestrator
8. Write tests
9. Run first sync!

---

## Documentation Structure

### For Getting Started
- **README.md** (this file) - Overview and quick start
- **TEMPLATE_USAGE.md** - Complete customization guide
- **doc/GETTING_STARTED.md** - Step-by-step setup
- **doc/README.md** - Documentation index

### For Implementation
- **doc/API_INTEGRATION_GUIDE.md** - API patterns and authentication
- **doc/SCHEMA_DESIGN_GUIDE.md** - Graph modeling best practices
- **doc/DEVELOPMENT_GUIDELINES.md** - Coding standards and workflows
- **doc/TEST_GUIDE.md** - Testing strategies

### For Production
- **doc/PERFORMANCE_OPTIMIZATION_GUIDE.md** - 3-phase optimization
- **doc/MIGRATION_GUIDE.md** - Schema evolution
- **CLAUDE.md** - Claude AI development workflows

### For Planning
- **task/TASK_MASTER_GUIDE.md** - Phase-based implementation plan
- **task/task_template.md** - Create your own task docs
- **task/issue_template.md** - GitHub issue with learnings

---

## Phase-Based Implementation Guide

**Proven approach from real-world production project:**

### Phase 1: Setup & Configuration (30 minutes)
- Clone template
- Configure `.env`
- Customize placeholders
- Test Neo4j connection

### Phase 2: API Integration (2-4 hours)
- Implement authentication
- Add entity fetch methods
- Test pagination
- Handle rate limiting

### Phase 3: Schema Design (2-3 hours)
- Identify entity types
- Define relationships
- Plan indexes and constraints
- Document schema

### Phase 4: Entity Sync (4-8 hours)
- Create entity modules (one per type)
- Implement sync methods
- Handle nested objects
- Register in orchestrator

### Phase 5: Relationship Creation (2-4 hours)
- Create relationship modules
- Implement relationship methods
- Register in orchestrator
- Verify with grep pattern

### Phase 6: Testing (2-3 hours)
- Write entity tests
- Write relationship tests
- Achieve 85%+ coverage
- Integration tests

### Phase 7: Metrics (2-4 hours, optional)
- Calculate derived metrics
- Store on nodes
- Add to MCP server

### Phase 8: Performance Optimization (2-6 hours)
- Add indexes (Phase 1)
- Time-series aggregation (Phase 2)
- Denormalize analytics (Phase 3)

### Phase 9: MCP Server (2-3 hours, optional)
- Add custom tools
- Implement dashboard APIs
- Deploy to FastMCP Cloud

### Phase 10: Deployment (1-2 hours)
- Choose deployment method
- Configure production environment
- Set up monitoring

**Total time:** 10-15 hours (core) to 20-30 hours (full-featured)

**See:** `task/TASK_MASTER_GUIDE.md` for detailed phase guide

---

## Success Stories

**example API Integration (Real-World Results):**

**Scope:**
- 16 entity types synced
- 8+ relationship types
- 85%+ test coverage
- Full sync: ~10 minutes

**Performance gains:**
- Dashboard KPIs: 3200ms → 15ms (213x faster)
- Time-series queries: 5500ms → 30ms (183x faster)
- Project list: 1800ms → 50ms (36x faster)

**Development metrics:**
- Initial setup: 40 hours (without template)
- Template extraction: 20 hours
- **Estimated savings for next project: 20-30 hours**

**Key learnings extracted:**
- Nested object extraction pattern (critical!)
- Entity single responsibility principle
- Relationship orchestration verification
- Two-phase testing strategy
- Three-phase performance optimization

---

## Project Structure

```
saas-to-neo4j-sync-template/
├── README.md                    # This file
├── TEMPLATE_USAGE.md           # Customization guide
├── CLAUDE.md                   # Feature branch workflow
├── .env.example                # Environment template
├── pyproject.toml              # Python project config
├── requirements.txt            # Core dependencies
├── requirements-dev.txt        # Development dependencies
│
├── main.py                     # FastMCP server (15 tools)
├── {project}_sync.py          # CLI script for sync
│
├── {project}_sync/            # Modular sync package
│   ├── __init__.py
│   ├── config.py              # Configuration classes
│   ├── {api}_client.py        # API client (OAuth2, pagination)
│   ├── neo4j_base.py          # Base Neo4j operations
│   ├── orchestrator.py        # Sync coordinator
│   ├── entities/              # Entity sync modules
│   │   ├── __init__.py
│   │   ├── customer.py        # Example entity
│   │   └── ...
│   ├── relationships/         # Relationship modules
│   │   ├── __init__.py
│   │   ├── customer_relationships.py
│   │   └── ...
│   └── metrics/               # Metrics calculators
│       ├── __init__.py
│       └── project_metrics.py
│
├── test/                      # Testing infrastructure
│   ├── conftest.py            # pytest fixtures
│   ├── test_config.py
│   ├── test_api_client.py
│   ├── test_entity_sync.py
│   ├── test_orchestrator_template.py
│   └── README.md
│
├── doc/                       # Comprehensive guides
│   ├── README.md              # Documentation index
│   ├── GETTING_STARTED.md
│   ├── API_INTEGRATION_GUIDE.md
│   ├── SCHEMA_DESIGN_GUIDE.md
│   ├── DEVELOPMENT_GUIDELINES.md
│   ├── TEST_GUIDE.md
│   ├── PERFORMANCE_OPTIMIZATION_GUIDE.md
│   └── MIGRATION_GUIDE.md
│
└── task/                      # Implementation guides
    ├── TASK_MASTER_GUIDE.md   # Phase-based plan
    ├── task_template.md       # Task doc template
    └── issue_template.md      # GitHub issue template
```

---

## Requirements

**Runtime:**
- Python 3.12+
- Neo4j 5.0+ (local or cloud)
- Your SaaS API credentials

**Development:**
- uv package manager (`pip install uv`)
- pytest for testing
- FastMCP for MCP server (optional)
- GitHub CLI for workflow (optional)

**Python packages:**
- `neo4j` - Neo4j Python driver
- `httpx` - Async HTTP client
- `pydantic` - Configuration validation
- `fastmcp` - FastMCP framework (optional)
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting

---

## Contributing

**Found an issue or have improvements?**

1. Create issue: `gh issue create --title "Template: [description]"`
2. Fork repository
3. Create feature branch
4. Make changes with tests
5. Submit PR with clear description
6. Update documentation

**When contributing:**
- Follow existing patterns
- Add tests for new features
- Update relevant documentation
- Use concise commit messages
- Document learnings in PR

---

## License

MIT License - use freely for any project.

---

## Support

**Need help?**
1. Check `doc/` guides for your specific question
2. Review `task/TASK_MASTER_GUIDE.md` for implementation phases
3. See `TEMPLATE_USAGE.md` for customization help
4. Create issue with details

**Found a bug?**
- Create issue: `gh issue create --title "Bug: [description]"`
- Include error logs and steps to reproduce
- Mention your environment (Python version, Neo4j version, etc.)

**Want to share your implementation?**
- We'd love to hear about it!
- Create issue: `gh issue create --title "Success Story: [API name]"`
- Share metrics, learnings, challenges

---

## Acknowledgments

**Built from real-world experience:**
- example API integration (16 entities, 8+ relationships)
- FastMCP framework by Jonathan Lowin
- Neo4j graph database best practices
- Claude AI development workflows

**Special thanks:**
- FastMCP community for MCP server patterns
- Neo4j community for performance optimization insights
- Early template users for feedback and improvements

---

## Next Steps

1. **Read TEMPLATE_USAGE.md** for complete customization guide
2. **Follow doc/GETTING_STARTED.md** for step-by-step setup
3. **Review task/TASK_MASTER_GUIDE.md** for implementation phases
4. **Start with Phase 1** (Setup & Configuration)

**Questions?** Create an issue or check the documentation guides.

**Ready to build?** Let's go!
