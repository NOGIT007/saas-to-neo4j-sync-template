# Task Master Guide

## Phase-Based Implementation Strategy

This template follows a proven phase-based approach for building SaaS-to-Neo4j sync systems.

## Implementation Phases

### Phase 1: Setup & Configuration ✅ TEMPLATE PROVIDED
**Status:** Ready to customize
**Time:** 30 minutes

- Clone template
- Configure `.env` with credentials
- Customize placeholders ({PROJECT_NAME}, {API_NAME}, etc.)
- Test Neo4j connection

**Files to customize:**
- `.env` (from `.env.example`)
- `{project}_sync/config.py`

---

### Phase 2: API Integration
**Status:** Template provided, needs customization
**Time:** 2-4 hours

**Objective:** Integrate with your SaaS API

**Tasks:**
1. Implement authentication in `{api}_client.py`
2. Add entity fetch methods (`get_customers()`, `get_users()`, etc.)
3. Test pagination with your API
4. Handle rate limiting and retries

**Files to customize:**
- `{project}_sync/{api}_client.py`

**Validation:**
```bash
python -c "from {project}_sync.{api}_client import {API}Client; from {project}_sync.config import {API}Config; client = {API}Client({API}Config()); client.authenticate(); print('✓ Authentication successful')"
```

---

### Phase 3: Schema Design
**Status:** Need to design
**Time:** 2-3 hours

**Objective:** Design Neo4j graph schema

**Tasks:**
1. Identify entity types (nodes)
2. Identify relationships (edges)
3. Define properties for each node/edge type
4. Plan indexes and constraints
5. Document schema in `doc/schema_design.md`

**Use:** `doc/SCHEMA_DESIGN_GUIDE.md` for best practices

**Output:** Schema design document with:
- Node labels and properties
- Relationship types
- Constraints (NODE KEY on guid fields)
- Indexes (frequently queried properties)

---

### Phase 4: Entity Sync Implementation
**Status:** Templates provided
**Time:** 4-8 hours (depending on entity count)

**Objective:** Sync all entity types from API to Neo4j

**Pattern:** One module per entity type in `{project}_sync/entities/`

**Tasks:**
1. Create entity sync module for each entity type
2. Implement `sync_{entity}()` method
3. Handle nested object extraction
4. Register in orchestrator
5. Test each entity sync

**Files to create/customize:**
- `{project}_sync/entities/{entity}.py` (use customer.py as template)
- `{project}_sync/orchestrator.py` (add sync calls)

**Critical Pattern:** Entity modules ONLY create their own entity type, store foreign GUIDs as properties

---

### Phase 5: Relationship Creation
**Status:** Templates provided
**Time:** 2-4 hours

**Objective:** Create relationships between synced entities

**Pattern:** Group related relationships in modules

**Tasks:**
1. Create relationship modules in `{project}_sync/relationships/`
2. Implement `create_{entity}_{relationship}_relationships()` methods
3. **CRITICAL:** Register ALL methods in orchestrator
4. Verify with grep pattern

**Files to create/customize:**
- `{project}_sync/relationships/{entity}_relationships.py`
- `{project}_sync/orchestrator.py` (add relationship calls)

**Validation:**
```bash
# Verify all relationship methods are registered
grep -r "def create_.*_relationships" {project}_sync/relationships/*.py | wc -l
grep "create_.*_relationships()" {project}_sync/orchestrator.py | wc -l
# These counts MUST match!
```

---

### Phase 6: Testing
**Status:** Template provided
**Time:** 2-3 hours

**Objective:** Achieve 85%+ test coverage

**Tasks:**
1. Write entity sync tests
2. Write relationship tests
3. Implement orchestrator coverage test
4. Write integration tests

**Files to create:**
- `test/test_{entity}_sync.py`
- `test/test_{entity}_relationships.py`
- `test/test_integration.py`

**Use:** `test/test_orchestrator_template.py` and `doc/TEST_GUIDE.md`

---

### Phase 7: Metrics (Optional)
**Status:** Template provided
**Time:** 2-4 hours

**Objective:** Calculate derived metrics and store on nodes

**Tasks:**
1. Identify metrics to calculate (totals, averages, scores)
2. Implement in `{project}_sync/metrics/`
3. Register in orchestrator
4. Add metrics to MCP server tools

**Files to customize:**
- `{project}_sync/metrics/{entity}_metrics.py`
- `{project}_sync/orchestrator.py`

---

### Phase 8: Performance Optimization
**Status:** Guide provided
**Time:** 2-6 hours (3 phases)

**Objective:** Optimize query performance

**Phases:**
1. **Indexes** (60-80% improvement, 30 min)
2. **Time-series aggregation** (80-95% improvement, 2-3 hours)
3. **Denormalization** (instant queries, 2-3 hours)

**Use:** `doc/PERFORMANCE_OPTIMIZATION_GUIDE.md`

---

### Phase 9: MCP Server (Optional)
**Status:** Template provided
**Time:** 2-3 hours

**Objective:** Expose graph to Claude AI via FastMCP

**Tasks:**
1. Add custom tools to `main.py`
2. Implement dashboard metrics tools
3. Implement entity list/detail tools
4. Deploy to FastMCP Cloud

**Files to customize:**
- `main.py`

---

### Phase 10: Deployment
**Status:** Guide provided
**Time:** 1-2 hours

**Objective:** Deploy to production

**Options:**
1. FastMCP Cloud (MCP server)
2. Cron job (sync script)
3. Cloud Run + Cloud Scheduler (Google Cloud)
4. Lambda + EventBridge (AWS)

**Use:** FastMCP deployment docs

---

## Estimated Total Time

- **Minimal (core sync only):** 10-15 hours
- **Full featured (with metrics, optimization, MCP):** 20-30 hours

## Success Metrics

- [ ] All entities syncing successfully
- [ ] All relationships created correctly
- [ ] 85%+ test coverage
- [ ] Full sync completes < 15 minutes
- [ ] Dashboard queries < 500ms
- [ ] MCP server deployed (if applicable)

## Task Templates

Individual task templates are provided in this folder:
- `task_template.md` - Template for creating your own task docs
- `issue_template.md` - Template for GitHub issues with learnings

## References

- `doc/GETTING_STARTED.md` - Initial setup guide
- `doc/DEVELOPMENT_GUIDELINES.md` - Coding standards
- `doc/TEST_GUIDE.md` - Testing strategies
- `CLAUDE.md` - Feature branch workflow
