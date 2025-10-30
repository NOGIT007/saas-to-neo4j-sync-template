# {PROJECT_NAME} Sync Development Guide

## Core Philosophy

**Keep it simple, keep it working.**

- **Simplicity First**: 10 lines > 20 lines
- **Working > Perfect**: Don't fix what isn't broken
- **Small Steps**: Break work into minimal logical changes
- **Follow Patterns**: Match project style exactly

---

## Quick Reference

**Always MCP for Neo4j:** Use `{project}mcp:` tools, never `python main.py`
**Always Feature Branch:** For non-trivial changes (see exceptions below)
**Always Pre-Push:** `pytest -m "not live"` → `{project}_sync.py --mode full` → `pytest`
**Always Concise:** Sacrifice grammar for brevity in all communication

---

## Communication Style

**Be extremely concise, sacrifice grammar:**

✅ "add indexes, 75x faster queries"
❌ "I have added database indexes which should make queries approximately 75 times faster"

✅ "fix nested object extraction in {entity}.py"
❌ "Fixed a bug where we were not properly extracting nested objects"

**Apply to:** commits, PRs, issues, code comments, all communication

---

## Feature Branch Workflow

**Use for:** All features, optimizations, non-trivial changes

### 1. Create Issue

```bash
gh issue create --title "Feature/Bug: description" --body "phases + plan"
```

### 2. Branch & Develop

```bash
git checkout -b feature/descriptive-name

# Phase 1
git commit -m "Phase 1: description (#issue)"
git push origin feature/descriptive-name
# Wait 3min, test on preview: https://feature-descriptive-name.{service}.app/mcp

# Phase 2
git commit -m "Phase 2: description (#issue)"
git push
# Test on preview

# Repeat for all phases
```

### 3. PR After All Phases Tested

```bash
gh pr create --title "Feature: name" --body "all phases tested"
```

### 4. Close Issue With Learnings

```bash
gh issue comment <num> --body "## Learnings
- Mistake: X
- Fix: Y
- Lesson: Z"

gh issue close <num> --comment "merged to main"
gh issue edit <num> --add-label "completed,dev-history"
```

**Direct to main OK for:**

- Documentation typos
- README updates
- Minor comments
- Emergency hotfixes (test immediately)

---

## Pre-Push Checklist

**ALWAYS run before push:**

```bash
# 1. Structural tests
uv run pytest test/ -v -m "not live"

# 2. Full workflow (after code changes)
uv run {project}_sync.py --mode full
uv run pytest test/ -v
```

**Requirements:** 85% coverage, all tests pass

---

## Critical Patterns

### 1. {API_NAME} API Nested Objects

#### ⚠️ API returns nested objects, NOT flat fields

❌ **WRONG:**

```python
customer_guid = address_data.get("customerGuid")  # doesn't exist!
```

✅ **CORRECT:**

```python
customer_guid = None
if address_data.get("customer"):
    customer_guid = address_data["customer"].get("guid")
```

**Before new entity sync:**

1. Check `doc/{api}_doc.json` for schema + `"$ref"` fields
2. Extract GUIDs from nested objects
3. Verify field names match API response

### 2. Relationship Orchestration

**When adding relationship methods, register in orchestrator:**

```bash
# Verify counts match
grep -r "def create_.*_relationships" {project}_sync/relationships/*.py | wc -l
grep "create_.*_relationships()" {project}_sync/orchestrator.py | wc -l
```

❌ **WRONG:** Add method, forget orchestrator call
✅ **CORRECT:** Add method + orchestrator call in same commit

### 3. Entity Sync Single Responsibility

### Entity modules ONLY create their own entity type

❌ **WRONG:** Create foreign entities inline
✅ **CORRECT:** Store foreign GUIDs as properties only

```python
# ONLY create {Entity}, store GUIDs
query = """
MERGE (e:{Entity} {guid: $guid})
SET e.customerGuid = $customerGuid  # store GUID, don't create Customer
"""
```

### 4. MCP Server Usage

**For ALL Neo4j operations:**

✅ `{project}mcp: execute_cypher(query="...")`
✅ `{project}mcp: get_dashboard_metrics()`
❌ Never `python main.py` for testing

---

## Task Execution Template

When working on tasks, follow this structure:

**1. Analysis:** What type? (feature/bug/optimization)
**2. Approach:** Steps following patterns
**3. Implementation:** Code/commands
**4. Testing:** Verification method
**5. Commit Strategy:** Feature branch or direct?

---

## Common Anti-Patterns

### Nested Objects

- ❌ Accessing flat fields that don't exist
- ✅ Navigate nested structure, check existence

### Relationships

- ❌ Create relationship method without orchestrator call
- ✅ Both in same commit, verify with grep

### Entity Creation

- ❌ Create foreign entities in entity sync
- ✅ Store GUIDs only, let relationship methods handle connections

### Testing

- ❌ Push without running full test suite
- ✅ Always run pre-push checklist

### Workflow

- ❌ Create PR before testing all phases
- ✅ Test each phase on preview deployment first

---

## TODO: Customize This File

**Replace placeholders:**
- `{PROJECT_NAME}` → Your project name
- `{API_NAME}` → Your API name (e.g., Jira, Salesforce)
- `{project}` → Your project slug (e.g., jira, salesforce)
- `{service}` → Your service name
- `{Entity}` → Your entity names

**Add API-specific patterns:**
- Common mistakes with your specific API
- Authentication quirks
- Rate limiting patterns
- Pagination edge cases
