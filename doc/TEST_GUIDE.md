# Test Guide

Testing strategy and patterns for {PROJECT_NAME}.

---

## Two-Phase Testing Strategy

### Phase 1: Structural Tests (Fast)

**Test code structure without live connections.**

**Run with:**
```bash
# From project root
uv run pytest test/ -v --cov={project}_sync

# From test/ directory
cd test
uv run pytest . -v --cov={project}_sync
```

**What it tests:**
- Entity sync logic with mocked driver
- Relationship creation logic
- API client pagination logic
- Error handling
- Edge cases (empty lists, null values)
- Code coverage

**Requirements:**
- All tests pass
- Coverage ≥ 85% (target: 95%+)
- No external dependencies (API, Neo4j)

### Phase 2: Integration Tests (Live)

**Test with actual Neo4j database and/or API.**

**Run with:**
```bash
# Full sync with real API and Neo4j
uv run {project}_sync.py --mode full

# Then verify with Neo4j queries
neo4j_mcp: get_node_count()
neo4j_mcp: get_node_labels()
```

**What it tests:**
- End-to-end data sync
- API authentication
- Neo4j connection
- Data integrity
- Relationship creation
- Query performance

---

## Test File Structure

```
test/
├── test_{entity}_coverage.py       # Entity-specific unit tests
├── test_relationship_coverage.py   # Relationship unit tests
├── test_orchestrator_coverage.py   # Orchestrator tests
├── test_api_client_coverage.py     # API client tests
└── test_integration_live.py        # Optional live integration tests
```

---

## Writing Entity Tests

### Template

```python
# test/test_{entity}_coverage.py
import pytest
from unittest.mock import Mock, AsyncMock
from {project}_sync.entities.{entity} import (
    fetch_all_{entities},
    sync_{entities},
    sync_all_{entities}
)

@pytest.mark.asyncio
async def test_fetch_{entities}_success():
    """Test fetching {entities} from API"""
    # Arrange
    client = Mock()
    client.fetch_paginated = AsyncMock(return_value=[
        {"guid": "1", "name": "Test 1"},
        {"guid": "2", "name": "Test 2"}
    ])

    # Act
    result = await fetch_all_{entities}(client)

    # Assert
    assert len(result) == 2
    assert result[0]["guid"] == "1"
    client.fetch_paginated.assert_called_once_with("/{entities}")

@pytest.mark.asyncio
async def test_sync_{entities}_success():
    """Test syncing {entities} to Neo4j"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()
    {entities} = [
        {"guid": "1", "name": "Test 1"},
        {"guid": "2", "name": "Test 2"}
    ]

    # Act
    result = await sync_{entities}(driver, {entities})

    # Assert
    assert result == 2
    driver.execute_query.assert_called_once()

    # Verify query structure
    call_args = driver.execute_query.call_args
    query = call_args[0][0]
    assert "UNWIND $batch" in query
    assert "MERGE" in query
    assert "{Entity}" in query

@pytest.mark.asyncio
async def test_sync_{entities}_empty_list():
    """Test sync with empty list"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()

    # Act
    result = await sync_{entities}(driver, [])

    # Assert
    assert result == 0
    driver.execute_query.assert_not_called()

@pytest.mark.asyncio
async def test_sync_{entities}_with_nested_objects():
    """Test extraction of nested object fields"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()
    {entities} = [{
        "guid": "1",
        "name": "Test",
        "related": {"guid": "related-123"}  # Nested object
    }]

    # Act
    result = await sync_{entities}(driver, {entities})

    # Assert
    assert result == 1
    call_args = driver.execute_query.call_args
    batch = call_args[1]["batch"]
    assert batch[0]["relatedGuid"] == "related-123"

@pytest.mark.asyncio
async def test_sync_all_{entities}_integration():
    """Test full fetch + sync workflow"""
    # Arrange
    client = Mock()
    client.fetch_paginated = AsyncMock(return_value=[
        {"guid": "1", "name": "Test"}
    ])
    driver = Mock()
    driver.execute_query = AsyncMock()

    # Act
    result = await sync_all_{entities}(client, driver)

    # Assert
    assert result == 1
    client.fetch_paginated.assert_called_once()
    driver.execute_query.assert_called_once()
```

---

## Writing Relationship Tests

### Template

```python
# test/test_relationship_coverage.py
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from {project}_sync.relationships.{entity}_relationships import (
    create_{entity}_relationships
)

@pytest.mark.asyncio
async def test_create_{entity}_relationships():
    """Test creating {entity} relationships"""
    # Arrange
    driver = Mock()

    # Mock result with summary
    mock_result = Mock()
    mock_summary = Mock()
    mock_counters = Mock()
    mock_counters.relationships_created = 5
    mock_summary.counters = mock_counters
    mock_result.summary = mock_summary

    driver.execute_query = AsyncMock(return_value=mock_result)

    # Act
    result = await create_{entity}_relationships(driver)

    # Assert
    assert result == 5
    driver.execute_query.assert_called_once()

    # Verify query structure
    call_args = driver.execute_query.call_args
    query = call_args[0][0]
    assert "MATCH" in query
    assert "WHERE" in query
    assert "MERGE" in query
    assert "RELATIONSHIP_TYPE" in query

@pytest.mark.asyncio
async def test_create_{entity}_relationships_no_matches():
    """Test when no matching entities found"""
    # Arrange
    driver = Mock()
    mock_result = Mock()
    mock_summary = Mock()
    mock_counters = Mock()
    mock_counters.relationships_created = 0
    mock_summary.counters = mock_counters
    mock_result.summary = mock_summary
    driver.execute_query = AsyncMock(return_value=mock_result)

    # Act
    result = await create_{entity}_relationships(driver)

    # Assert
    assert result == 0
```

---

## Writing Orchestrator Tests

```python
# test/test_orchestrator_coverage.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from {project}_sync.orchestrator import SyncOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_sync_all_entities():
    """Test orchestrator entity sync workflow"""
    # Arrange
    orchestrator = SyncOrchestrator()
    orchestrator.client = Mock()
    orchestrator.driver = Mock()

    # Mock all entity sync functions
    with patch("{project}_sync.entities.customer.sync_all_customers", new_callable=AsyncMock) as mock_customers, \
         patch("{project}_sync.entities.project.sync_all_projects", new_callable=AsyncMock) as mock_projects:

        mock_customers.return_value = 10
        mock_projects.return_value = 50

        # Act
        await orchestrator.sync_all_entities()

        # Assert
        mock_customers.assert_called_once()
        mock_projects.assert_called_once()

@pytest.mark.asyncio
async def test_orchestrator_sync_relationships():
    """Test orchestrator relationship sync workflow"""
    # Arrange
    orchestrator = SyncOrchestrator()
    orchestrator.driver = Mock()

    # Mock relationship functions
    with patch("{project}_sync.relationships.customer_relationships.create_customer_relationships", new_callable=AsyncMock) as mock_rel:
        mock_rel.return_value = 5

        # Act
        await orchestrator.sync_relationships()

        # Assert
        mock_rel.assert_called_once()
```

---

## Writing API Client Tests

```python
# test/test_api_client_coverage.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from {project}_sync.api_client import APIClient

@pytest.mark.asyncio
async def test_api_client_pagination():
    """Test pagination logic"""
    # Arrange
    client = APIClient()

    # Mock HTTP responses
    page1 = {"results": [{"id": 1}, {"id": 2}], "nextPageToken": "token123"}
    page2 = {"results": [{"id": 3}, {"id": 4}], "nextPageToken": None}

    with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            Mock(json=lambda: page1),
            Mock(json=lambda: page2)
        ]

        # Act
        result = await client._fetch_paginated("/test")

        # Assert
        assert len(result) == 4
        assert result[0]["id"] == 1
        assert result[3]["id"] == 4
        assert mock_request.call_count == 2

@pytest.mark.asyncio
async def test_api_client_rate_limit_retry():
    """Test retry on rate limit"""
    # Arrange
    client = APIClient()

    # Mock 429 error then success
    error_response = Mock(status_code=429)
    success_response = Mock(status_code=200, json=lambda: {"data": "test"})

    with patch.object(client.http_client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [error_response, success_response]

        # Act
        result = await client._request_with_retry("GET", "/test")

        # Assert
        assert result.status_code == 200
        assert mock_request.call_count == 2
```

---

## Testing Nested Object Extraction

```python
@pytest.mark.asyncio
async def test_extract_nested_customer_guid():
    """Test extracting nested customer GUID"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()

    # API response with nested customer object
    projects = [{
        "guid": "proj-1",
        "name": "Project X",
        "customer": {  # ← Nested object
            "guid": "cust-123",
            "name": "Acme Corp"
        }
    }]

    # Act
    result = await sync_projects(driver, projects)

    # Assert
    call_args = driver.execute_query.call_args
    batch = call_args[1]["batch"]

    # Verify nested GUID was extracted
    assert batch[0]["customerGuid"] == "cust-123"
    # Verify nested Customer node was NOT created
    query = call_args[0][0]
    assert "Customer" not in query
```

---

## Testing Edge Cases

```python
@pytest.mark.asyncio
async def test_sync_with_null_values():
    """Test handling null/None values"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()
    entities = [{
        "guid": "1",
        "name": "Test",
        "optional_field": None
    }]

    # Act
    result = await sync_entities(driver, entities)

    # Assert
    assert result == 1

@pytest.mark.asyncio
async def test_sync_with_missing_nested_object():
    """Test when nested object is missing"""
    # Arrange
    driver = Mock()
    driver.execute_query = AsyncMock()
    projects = [{
        "guid": "proj-1",
        "name": "Project X"
        # customer field missing
    }]

    # Act
    result = await sync_projects(driver, projects)

    # Assert
    call_args = driver.execute_query.call_args
    batch = call_args[1]["batch"]
    assert batch[0]["customerGuid"] is None
```

---

## Coverage Requirements

### Minimum Thresholds

- **Overall coverage**: 85%
- **Entity modules**: 90%+
- **Relationship modules**: 90%+
- **API client**: 85%+
- **Orchestrator**: 85%+

### Check Coverage

```bash
# Run with coverage report
uv run pytest test/ -v --cov={project}_sync --cov-report=html

# Open HTML report
open htmlcov/index.html

# Terminal report with missing lines
uv run pytest test/ -v --cov={project}_sync --cov-report=term-missing
```

### Example Output

```
Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
{project}_sync/__init__.py                    2      0   100%
{project}_sync/api_client.py                 85      5    94%   145-150
{project}_sync/entities/customer.py          35      1    97%   42
{project}_sync/entities/project.py           42      2    95%   56, 78
{project}_sync/relationships/customer.py     28      0   100%
-----------------------------------------------------------------------
TOTAL                                       450     12    97%
```

---

## Pre-Push Testing Workflow

**ALWAYS run before pushing to main:**

```bash
# 1. Run all tests
uv run pytest test/ -v

# 2. Check coverage
uv run pytest test/ -v --cov={project}_sync

# 3. Verify coverage meets minimum (85%)
# 4. Fix any failing tests
# 5. Commit and push
```

**After code changes affecting sync logic:**

```bash
# 1. Run unit tests
uv run pytest test/ -v --cov={project}_sync

# 2. Run full sync to verify
uv run {project}_sync.py --mode full

# 3. Verify data in Neo4j
neo4j_mcp: get_node_count()
neo4j_mcp: execute_cypher(query="MATCH (n) RETURN labels(n)[0], count(*)")

# 4. Re-run tests (optional)
uv run pytest test/ -v
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run tests
        run: uv run pytest test/ -v --cov={project}_sync

      - name: Check coverage
        run: |
          uv run pytest test/ --cov={project}_sync --cov-fail-under=85
```

---

## Testing Live Integration (Optional)

### Mark Live Tests

```python
# test/test_integration_live.py
import pytest

@pytest.mark.live
@pytest.mark.asyncio
async def test_full_sync_workflow():
    """Test complete sync workflow with live Neo4j"""
    # Requires NEO4J_URI, credentials in .env
    from {project}_sync.orchestrator import SyncOrchestrator

    orchestrator = SyncOrchestrator()

    # Run full sync
    await orchestrator.sync_all_entities()
    await orchestrator.sync_relationships()

    # Verify data exists
    result = await orchestrator.driver.execute_query(
        "MATCH (c:Customer) RETURN count(c) as count"
    )
    customer_count = result.records[0]["count"]
    assert customer_count > 0
```

### Run Only Structural Tests

```bash
# Skip live tests (default)
uv run pytest test/ -v -m "not live"
```

### Run All Tests Including Live

```bash
# Run everything (requires live Neo4j)
uv run pytest test/ -v
```

---

## Test Markers

### Define in `pytest.ini`

```ini
[pytest]
markers =
    live: tests requiring live Neo4j connection
    slow: slow-running tests (> 1s)
    api: tests requiring live API connection
```

### Use in Tests

```python
@pytest.mark.live
async def test_with_real_neo4j():
    ...

@pytest.mark.slow
async def test_large_dataset():
    ...

@pytest.mark.api
async def test_api_connection():
    ...
```

### Run Specific Markers

```bash
# Only live tests
uv run pytest -v -m live

# Exclude slow tests
uv run pytest -v -m "not slow"

# Only API tests
uv run pytest -v -m api
```

---

## Debugging Tests

### Run Single Test

```bash
uv run pytest test/test_{entity}_coverage.py::test_sync_{entity}_success -v
```

### Print Debug Output

```python
@pytest.mark.asyncio
async def test_with_debug():
    result = await sync_entities(driver, entities)
    print(f"Result: {result}")  # Will show in pytest output with -s
    assert result == expected
```

```bash
uv run pytest test/test_file.py -v -s  # -s shows print statements
```

### Use Pytest Debugger

```bash
# Drop into debugger on failure
uv run pytest test/test_file.py --pdb

# Drop into debugger on first test
uv run pytest test/test_file.py --trace
```

---

## Common Test Failures

**"AssertionError: expected X, got Y"**
- Check mock setup matches actual function behavior
- Verify test data structure matches API response

**"RuntimeError: no running event loop"**
- Missing `@pytest.mark.asyncio` decorator
- Install pytest-asyncio: `pip install pytest-asyncio`

**"AttributeError: Mock object has no attribute X"**
- Mock not configured correctly
- Add: `mock.X = Mock()` or `mock.X = AsyncMock()`

**"Coverage below 85%"**
- Add tests for uncovered lines (see `--cov-report=term-missing`)
- Check for error handling branches
- Test edge cases (empty lists, null values)

---

## Resources

- pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- Coverage.py: https://coverage.readthedocs.io/
