# Documentation Overview

Complete guide to building and maintaining your SaaS-to-Neo4j sync project using this template.

---

## Quick Start Path

**New to the template? Follow this path:**

1. **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Setup, configuration, first sync
2. **[API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)** - Integrate your API
3. **[SCHEMA_DESIGN_GUIDE.md](./SCHEMA_DESIGN_GUIDE.md)** - Design your graph schema
4. **[DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md)** - Coding standards
5. **[TEST_GUIDE.md](./TEST_GUIDE.md)** - Write comprehensive tests

**After working code:**

6. **[PERFORMANCE_OPTIMIZATION_GUIDE.md](./PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Speed up queries
7. **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - Evolve schema safely

---

## Document Reference

### Core Guides

#### [GETTING_STARTED.md](./GETTING_STARTED.md)
**Start here.** Step-by-step guide from clone to first sync.

**Contents:**
- Prerequisites and setup
- Environment configuration
- Customization checklist
- First sync walkthrough
- Verification steps
- Common issues and solutions

**Use when:** You're setting up the project for the first time.

---

#### [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)
**Patterns for any REST API.** Authentication, pagination, error handling.

**Contents:**
- OAuth2, API key, JWT authentication
- Token-based, offset, cursor, page-number pagination
- Rate limiting strategies
- Nested object extraction (critical!)
- Date range filtering
- Error handling patterns

**Use when:**
- Implementing API client for your SaaS
- Debugging authentication issues
- Handling API rate limits
- Extracting data from nested API responses

**Key Insight:** APIs return nested objects, not flat fields. Always check API docs before implementing entity sync.

---

#### [SCHEMA_DESIGN_GUIDE.md](./SCHEMA_DESIGN_GUIDE.md)
**Graph database best practices.** Nodes, relationships, constraints, indexes.

**Contents:**
- Node design patterns
- Relationship patterns
- Property types and naming conventions
- NODE KEY constraints
- Index strategy
- Query optimization
- Common anti-patterns

**Use when:**
- Designing initial schema
- Adding new entity types
- Creating relationships
- Optimizing query performance
- Avoiding schema anti-patterns

**Key Principles:**
- Store foreign GUIDs as properties only
- Create relationships in separate orchestration step
- Index foreign key GUIDs
- Use batch operations (UNWIND)

---

#### [DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md)
**Coding standards from real project.** Communication, patterns, workflow.

**Contents:**
- Communication style (concise commits)
- Git workflow (feature branches)
- Pre-push checklist
- Entity single responsibility pattern
- Relationship orchestration pattern
- API nested object extraction
- Batch operation patterns
- Common anti-patterns

**Use when:**
- Starting new feature
- Writing commit messages
- Creating pull requests
- Implementing entity sync
- Adding relationship methods

**Critical Patterns:**
1. Entity modules ONLY create their own entity type
2. Register relationship methods in orchestrator
3. Navigate nested API objects safely
4. Use batch operations (500-1000 records)

---

#### [TEST_GUIDE.md](./TEST_GUIDE.md)
**Two-phase testing strategy.** Unit tests + integration tests.

**Contents:**
- Structural tests (fast, no external dependencies)
- Integration tests (live Neo4j/API)
- Writing entity tests
- Writing relationship tests
- Coverage requirements (85% minimum)
- Pre-push workflow
- Continuous integration setup

**Use when:**
- Writing tests for new features
- Debugging test failures
- Setting up CI/CD
- Verifying code coverage

**Testing Workflow:**
1. Run structural tests: `uv run pytest test/ -v --cov={project}_sync`
2. Verify coverage ≥ 85%
3. Run full sync: `uv run {project}_sync.py --mode full`
4. Verify data in Neo4j

---

### Advanced Guides

#### [PERFORMANCE_OPTIMIZATION_GUIDE.md](./PERFORMANCE_OPTIMIZATION_GUIDE.md)
**Three-phase optimization strategy.** Real-world benchmarks and results.

**Contents:**
- Phase 1: Indexes (60-80% improvement)
- Phase 2: Time-series aggregation (80-95% improvement)
- Phase 3: Analytics denormalization (instant queries)
- Benchmarking with EXPLAIN/PROFILE
- Real-world performance results

**Use when:**
- Queries take > 500ms
- Dashboard feels sluggish
- Time-series queries > 1 second
- Database grows to 10,000+ nodes

**Optimization Order:**
1. Always start with indexes (fastest ROI)
2. Add time-series aggregation if needed
3. Denormalize analytics for dashboards

**Real Results (from real-world production project):**
- Dashboard KPIs: 3200ms → 15ms (213x faster)
- Time-series: 5500ms → 30ms (183x faster)
- Project list: 1800ms → 50ms (36x faster)

---

#### [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
**Safe schema evolution.** Migrations, versioning, rollback strategies.

**Contents:**
- When to use migrations
- Migration workflow (dev → test → dry-run → production)
- Common patterns (add property, rename, type change)
- Batch processing for large datasets
- Rollback strategies
- Version tracking
- Testing migrations

**Use when:**
- Adding new properties to existing nodes
- Renaming properties
- Changing property types
- Restructuring relationships
- Backfilling computed values

**Migration Workflow:**
1. Create migration script (up + down functions)
2. Test on development database
3. Run dry-run on production data
4. Backup database
5. Apply migration to production
6. Verify and monitor

---

## Knowledge Base

### issue_history/
**Track solved problems and learnings.**

When closing GitHub issues, document learnings:

```bash
gh issue comment <num> --body "## Learnings
- Mistake: Tried to access flat customerGuid field
- Fix: Checked API docs, found nested customer object
- Lesson: Always verify API response structure first
"

gh issue close <num> --comment "merged to main"
gh issue edit <num> --add-label "completed,dev-history"
```

Store issue summaries in `issue_history/` for future reference.

**Example files:**
- `issue_history/001_nested_object_extraction.md`
- `issue_history/002_relationship_orchestration.md`
- `issue_history/003_pagination_token_bug.md`

---

## Common Questions

### "Where do I start?"
**→ [GETTING_STARTED.md](./GETTING_STARTED.md)**

### "How do I handle OAuth2 authentication?"
**→ [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md) - Authentication Methods**

### "API returns nested objects, how do I extract them?"
**→ [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md) - Nested Object Extraction**

### "How do I design my Neo4j schema?"
**→ [SCHEMA_DESIGN_GUIDE.md](./SCHEMA_DESIGN_GUIDE.md)**

### "Should I create foreign entities in entity sync?"
**❌ No!** Store GUIDs only, create relationships separately.
**→ [DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md) - Entity Single Responsibility**

### "How do I add a new relationship type?"
**→ [DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md) - Relationship Orchestration**

### "What test coverage do I need?"
**Minimum 85%, target 95%.**
**→ [TEST_GUIDE.md](./TEST_GUIDE.md) - Coverage Requirements**

### "Queries are slow, how do I optimize?"
**Start with indexes (Phase 1).**
**→ [PERFORMANCE_OPTIMIZATION_GUIDE.md](./PERFORMANCE_OPTIMIZATION_GUIDE.md)**

### "How do I add a new property to existing nodes?"
**Use migrations.**
**→ [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Adding New Property**

---

## Best Practices Summary

### Communication
- **Concise commits:** "add indexes, 75x faster" not "I have added indexes..."
- **Track learnings:** Document mistakes/fixes in issue comments

### Development
- **Entity single responsibility:** Only create your own entity type
- **Relationship orchestration:** Register all methods in orchestrator
- **Nested objects:** Navigate safely, never assume flat fields
- **Batch operations:** 500-1000 records per query

### Testing
- **Pre-push:** Run tests + check coverage (≥85%)
- **Two-phase:** Structural tests, then integration tests
- **Full sync:** Verify after code changes

### Performance
- **Start with indexes:** 60-80% improvement, minimal effort
- **Profile queries:** Use EXPLAIN/PROFILE to verify plans
- **Denormalize when needed:** Pre-compute dashboard metrics

### Schema Evolution
- **Use migrations:** For schema changes in production
- **Test thoroughly:** Dev → dry-run → production
- **Backup first:** Always backup before major migrations

---

## Document Status

| Document | Status | Last Updated | Version |
|----------|--------|--------------|---------|
| GETTING_STARTED.md | ✅ Complete | 2024-10-30 | 1.0 |
| API_INTEGRATION_GUIDE.md | ✅ Complete | 2024-10-30 | 1.0 |
| SCHEMA_DESIGN_GUIDE.md | ✅ Complete | 2024-10-30 | 1.0 |
| DEVELOPMENT_GUIDELINES.md | ✅ Complete | 2024-10-30 | 1.0 |
| TEST_GUIDE.md | ✅ Complete | 2024-10-30 | 1.0 |
| PERFORMANCE_OPTIMIZATION_GUIDE.md | ✅ Complete | 2024-10-30 | 1.0 |
| MIGRATION_GUIDE.md | ✅ Complete | 2024-10-30 | 1.0 |

---

## Contributing to Documentation

**Found an issue or have improvements?**

1. Create issue: `gh issue create --title "Docs: [description]"`
2. Make changes in feature branch
3. Submit PR with clear description
4. Update "Document Status" table

**Documentation style:**
- Use concrete examples (not abstract)
- Include code snippets
- Show both ❌ wrong and ✅ correct patterns
- Reference real-world results (real-world production project)
- Keep it concise

---

## Template Variables

**When customizing for your project, replace:**

- `{PROJECT_NAME}` → Your project name
- `{API_NAME}` → Your SaaS API name (e.g., "Salesforce", "HubSpot")
- `{API_NAME_UPPER}` → API name in uppercase for env vars
- `{project}` → Project name in snake_case (for file/module names)
- `{Entity}` → Specific entity type (Customer, Project, User, etc.)
- `{entity}` → Entity in lowercase
- `{entities}` → Entity plural

**Example:**
```
{PROJECT_NAME} → Salesforce Neo4j Sync
{API_NAME} → Salesforce
{API_NAME_UPPER} → SALESFORCE
{project} → salesforce
{Entity} → Account
{entity} → account
{entities} → accounts
```

---

## Additional Resources

**Neo4j:**
- Graph Data Modeling: https://neo4j.com/developer/guide-data-modeling/
- Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Performance Tuning: https://neo4j.com/developer/guide-performance-tuning/

**FastMCP:**
- FastMCP Documentation: https://github.com/jlowin/fastmcp
- MCP Protocol: https://modelcontextprotocol.io/

**Python Testing:**
- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- Coverage.py: https://coverage.readthedocs.io/

---

## Support

**Need help?**
1. Check relevant guide above
2. Search `issue_history/` for similar problems
3. Review closed GitHub issues
4. Create new issue with:
   - What you tried
   - Error messages/logs
   - Environment details

**Found a bug in template?**
- Create issue: `gh issue create --title "Bug: [description]"`
- Include steps to reproduce
- Provide error logs

**Want to contribute?**
- Fork repository
- Create feature branch
- Submit PR with tests
- Update documentation
