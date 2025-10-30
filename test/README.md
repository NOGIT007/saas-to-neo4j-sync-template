# Test Suite

## Two-Phase Testing Strategy

**Phase 1: Structural Tests** (fast, no database required)
```bash
pytest -v -m "not live"
```

**Phase 2: Integration Tests** (requires synced data)
```bash
# First run full sync
uv run {project}_sync.py --mode full

# Then run all tests
pytest -v
```

## Test Organization

- `test_orchestrator_template.py` - **Critical coverage test** (checks all relationship methods registered)
- Add your own test files following patterns in doc/TEST_GUIDE.md

## Pre-Push Checklist

**ALWAYS run before pushing:**
```bash
# 1. Structural tests
pytest -v -m "not live"

# 2. Full sync + integration tests
uv run {project}_sync.py --mode full
pytest -v
```

## Coverage Requirements

Minimum: **85% coverage**

```bash
pytest --cov={project}_sync --cov-report=html
open htmlcov/index.html
```

See doc/TEST_GUIDE.md for comprehensive testing guide.
