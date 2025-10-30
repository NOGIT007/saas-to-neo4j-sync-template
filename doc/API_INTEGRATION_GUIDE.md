# API Integration Guide

Patterns for integrating any REST API with Neo4j sync.

---

## Authentication Methods

### OAuth2 (Token-Based)

**Pattern from production integration:**

```python
class APIClient:
    async def _get_access_token(self):
        """Get OAuth2 access token"""
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        response = await self.http_client.post(
            f"{self.config.auth_url}/token",
            data=payload
        )
        return response.json()["access_token"]

    async def _request(self, method, endpoint, **kwargs):
        """Add OAuth2 bearer token to request"""
        if not self.access_token:
            self.access_token = await self._get_access_token()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.http_client.request(
            method, f"{self.base_url}{endpoint}",
            headers=headers, **kwargs
        )
        return response
```

### API Key Authentication

```python
class APIClient:
    def __init__(self, api_key):
        self.api_key = api_key

    async def _request(self, method, endpoint, **kwargs):
        """Add API key to headers"""
        headers = {"X-API-Key": self.api_key}
        response = await self.http_client.request(
            method, f"{self.base_url}{endpoint}",
            headers=headers, **kwargs
        )
        return response
```

### JWT with Refresh Token

```python
class APIClient:
    async def _ensure_valid_token(self):
        """Refresh JWT if expired"""
        if self.token_expires_at < time.time():
            await self._refresh_token()

    async def _refresh_token(self):
        """Refresh JWT token"""
        response = await self.http_client.post(
            f"{self.auth_url}/refresh",
            json={"refresh_token": self.refresh_token}
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"]

    async def _request(self, method, endpoint, **kwargs):
        await self._ensure_valid_token()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        # ... rest of request
```

---

## Pagination Patterns

### Token-Based Pagination (example project Pattern)

**API returns `nextPageToken` in response:**

```python
async def _fetch_paginated(self, endpoint, params=None):
    """Fetch all pages using token-based pagination"""
    all_data = []
    next_page_token = None
    page_num = 1

    while True:
        # Add page token to params
        request_params = {**(params or {})}
        if next_page_token:
            request_params["pageToken"] = next_page_token

        response = await self._request("GET", endpoint, params=request_params)
        data = response.json()

        # Extract records (adjust key based on API)
        batch = data.get("results", [])
        all_data.extend(batch)

        logger.info(f"Fetched page {page_num}: {len(batch)} records")

        # Check for next page
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        page_num += 1
        await asyncio.sleep(0.1)  # Rate limiting

    return all_data
```

### Offset/Limit Pagination

**API uses `offset` and `limit` parameters:**

```python
async def _fetch_paginated(self, endpoint, params=None, page_size=100):
    """Fetch all pages using offset/limit"""
    all_data = []
    offset = 0

    while True:
        request_params = {
            **(params or {}),
            "limit": page_size,
            "offset": offset
        }

        response = await self._request("GET", endpoint, params=request_params)
        data = response.json()

        batch = data.get("items", [])
        all_data.extend(batch)

        logger.info(f"Fetched {len(batch)} records (offset: {offset})")

        # Stop if we got fewer records than page size
        if len(batch) < page_size:
            break

        offset += page_size
        await asyncio.sleep(0.1)

    return all_data
```

### Cursor-Based Pagination

**API returns `cursor` for next page:**

```python
async def _fetch_paginated(self, endpoint, params=None):
    """Fetch all pages using cursor"""
    all_data = []
    cursor = None

    while True:
        request_params = {**(params or {})}
        if cursor:
            request_params["cursor"] = cursor

        response = await self._request("GET", endpoint, params=request_params)
        data = response.json()

        batch = data.get("data", [])
        all_data.extend(batch)

        logger.info(f"Fetched {len(batch)} records")

        # Get next cursor
        paging = data.get("paging", {})
        cursor = paging.get("next")
        if not cursor:
            break

        await asyncio.sleep(0.1)

    return all_data
```

### Page Number Pagination

**API uses page numbers:**

```python
async def _fetch_paginated(self, endpoint, params=None, page_size=50):
    """Fetch all pages using page numbers"""
    all_data = []
    page = 1

    while True:
        request_params = {
            **(params or {}),
            "page": page,
            "per_page": page_size
        }

        response = await self._request("GET", endpoint, params=request_params)
        data = response.json()

        batch = data.get("items", [])
        all_data.extend(batch)

        logger.info(f"Fetched page {page}: {len(batch)} records")

        # Check if there's a next page
        if len(batch) < page_size or not data.get("has_more"):
            break

        page += 1
        await asyncio.sleep(0.1)

    return all_data
```

---

## Rate Limiting Strategies

### Fixed Delay Between Requests

```python
async def _request(self, method, endpoint, **kwargs):
    """Add fixed delay between requests"""
    response = await self.http_client.request(...)
    await asyncio.sleep(0.2)  # 200ms between requests
    return response
```

### Exponential Backoff for 429 Errors

```python
async def _request_with_retry(self, method, endpoint, max_retries=5, **kwargs):
    """Retry with exponential backoff on rate limit"""
    for attempt in range(max_retries):
        try:
            response = await self.http_client.request(
                method, f"{self.base_url}{endpoint}", **kwargs
            )

            if response.status_code == 429:
                # Rate limited - exponential backoff
                wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
                logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt+1})")
                await asyncio.sleep(wait_time)
                continue

            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                continue
            raise

    raise Exception(f"Max retries ({max_retries}) exceeded")
```

### Respect Rate Limit Headers

```python
async def _request(self, method, endpoint, **kwargs):
    """Use rate limit headers to adjust delays"""
    response = await self.http_client.request(...)

    # Check rate limit headers
    remaining = int(response.headers.get("X-RateLimit-Remaining", 100))
    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))

    if remaining < 10:
        # Approaching limit - slow down
        wait_time = max(1, reset_time - time.time()) / remaining
        await asyncio.sleep(wait_time)

    return response
```

---

## Nested Object Extraction

### Critical Pattern from example project Integration

**⚠️ APIs often return nested objects, not flat fields**

**WRONG approach:**
```python
# Accessing non-existent flat fields
customer_guid = data.get("customerGuid")  # doesn't exist!
owner_email = data.get("ownerEmail")  # doesn't exist!
```

**CORRECT approach:**
```python
# Navigate nested structure safely
customer_guid = None
if data.get("customer"):
    customer_guid = data["customer"].get("guid")

owner_email = None
if data.get("owner"):
    owner_email = data["owner"].get("email")
```

### Best Practice: Check API Schema First

**Before implementing entity sync:**

1. Check API documentation or OpenAPI spec
2. Look for `$ref` fields (references to other entities)
3. Test API response with sample requests
4. Map nested paths to flat properties

**Example from example project:**
```json
// API response structure
{
  "guid": "project-123",
  "name": "Project X",
  "customer": {              // ← Nested object
    "guid": "customer-456",
    "name": "Acme Corp"
  },
  "owner": {                 // ← Nested object
    "guid": "user-789",
    "firstName": "John"
  }
}
```

**Extraction code:**
```python
def extract_project_data(api_response):
    """Extract flattened data from nested API response"""
    project_data = {
        "guid": api_response.get("guid"),
        "name": api_response.get("name"),
        "customerGuid": None,  # Store GUID only
        "ownerGuid": None,     # Store GUID only
    }

    # Extract nested customer GUID
    if api_response.get("customer"):
        project_data["customerGuid"] = api_response["customer"].get("guid")

    # Extract nested owner GUID
    if api_response.get("owner"):
        project_data["ownerGuid"] = api_response["owner"].get("guid")

    return project_data
```

### Generic Helper Function

```python
def safe_get_nested(data, *keys, default=None):
    """Safely navigate nested dict structure"""
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
owner_email = safe_get_nested(data, "owner", "email")
project_name = safe_get_nested(data, "project", "customer", "name")
```

---

## Date Range Filtering

### Pattern from example project Work Hours

**Configure lookback period:**
```python
# .env configuration
SYNC_DATE_RANGE_DAYS=365  # Last year
# OR
SYNC_START_DATE=2020-01-01  # All data since date
```

**Implementation:**
```python
async def fetch_work_hours(self, start_date=None):
    """Fetch work hours with date filtering"""
    if not start_date:
        # Default to configured lookback period
        days_back = int(os.getenv("SYNC_DATE_RANGE_DAYS", 365))
        start_date = datetime.now() - timedelta(days=days_back)

    params = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": datetime.now().strftime("%Y-%m-%d")
    }

    return await self._fetch_paginated("/workhours", params=params)
```

### Incremental Sync Pattern

```python
async def fetch_updated_since(self, entity_type, last_sync_time):
    """Fetch only records updated since last sync"""
    params = {
        "updatedAfter": last_sync_time.isoformat(),
        "orderBy": "updatedAt"
    }
    return await self._fetch_paginated(f"/{entity_type}", params=params)
```

---

## Error Handling Patterns

### Retry with Logging

```python
async def _request_with_retry(self, method, endpoint, max_retries=3, **kwargs):
    """Retry failed requests with error logging"""
    last_error = None

    for attempt in range(max_retries):
        try:
            response = await self.http_client.request(
                method, f"{self.base_url}{endpoint}", **kwargs
            )
            response.raise_for_status()
            return response

        except httpx.HTTPError as e:
            last_error = e
            logger.warning(
                f"Request failed (attempt {attempt+1}/{max_retries}): {e}"
            )

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All retries failed for {endpoint}")

    raise last_error
```

### Partial Failure Handling

```python
async def sync_entities_with_error_tracking(self, entities):
    """Continue sync even if some entities fail"""
    failed_entities = []

    for entity in entities:
        try:
            await self.sync_single_entity(entity)
        except Exception as e:
            logger.error(f"Failed to sync {entity['guid']}: {e}")
            failed_entities.append({
                "guid": entity["guid"],
                "error": str(e)
            })

    if failed_entities:
        logger.warning(f"Failed to sync {len(failed_entities)} entities")
        # Write to error log or dead letter queue
        await self._log_failures(failed_entities)

    return len(entities) - len(failed_entities)
```

---

## API Schema Discovery

### Test Endpoint Structure

```python
async def discover_api_structure(self):
    """Fetch sample data to understand API structure"""
    endpoints = [
        "/customers?limit=1",
        "/projects?limit=1",
        "/users?limit=1"
    ]

    for endpoint in endpoints:
        response = await self._request("GET", endpoint)
        data = response.json()

        # Pretty print structure
        print(f"\n{endpoint} structure:")
        print(json.dumps(data, indent=2))
```

### Document Field Mappings

```python
# Create mapping documentation
FIELD_MAPPINGS = {
    "Project": {
        "api_field": "neo4j_property",
        "id": "guid",
        "project_name": "name",
        "customer.guid": "customerGuid",  # nested extraction
        "owner.email": "ownerEmail",      # nested extraction
        "created_at": "createdAt",
    }
}
```

---

## Testing API Integration

### Manual Testing Script

```python
# test_api_connection.py
async def test_connection():
    client = APIClient()

    # Test auth
    token = await client._get_access_token()
    print(f"✅ Authentication successful: {token[:20]}...")

    # Test pagination
    customers = await client.fetch_all_customers()
    print(f"✅ Fetched {len(customers)} customers")

    # Test nested extraction
    if customers:
        sample = customers[0]
        print(f"✅ Sample customer: {json.dumps(sample, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

---

## Common API Gotchas

**1. Nested Objects**
- Always check API docs for object references
- Test with actual API responses, not assumptions
- Extract GUIDs from nested objects, don't create entities inline

**2. Pagination**
- Some APIs return empty `nextPageToken` when done
- Others return `null` or omit the field entirely
- Handle both cases: `if not next_page_token:`

**3. Rate Limits**
- Read API documentation for limits (requests/minute)
- Implement delays between requests (0.1-0.2s minimum)
- Use exponential backoff for 429 errors

**4. Date Formats**
- ISO 8601 is common but not universal
- Some APIs use Unix timestamps
- Others use custom formats (e.g., "2024-10-30 14:30:00")
- Always parse and normalize dates

**5. Authentication Token Expiry**
- OAuth2 tokens expire (typically 1-24 hours)
- Implement token refresh logic
- Cache tokens between requests

**6. API Versioning**
- Use versioned endpoints (`/v1/`, `/v2/`)
- Pin to specific version in config
- Test before upgrading API version
