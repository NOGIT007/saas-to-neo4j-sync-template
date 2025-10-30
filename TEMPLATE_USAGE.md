# Template Usage Guide

Complete guide to customizing this template for your specific SaaS API.

---

## Overview

This template uses **placeholders** that you replace with your project specifics. This guide walks through every file that needs customization and provides detailed examples.

**Estimated time:** 30-60 minutes for complete customization

---

## Placeholder Reference

**Global placeholders used throughout:**

| Placeholder | Description | Example (Salesforce) | Example (Jira) |
|------------|-------------|---------------------|----------------|
| `{PROJECT_NAME}` | Full project name | "Salesforce Neo4j Sync" | "Jira Knowledge Graph" |
| `{API_NAME}` | SaaS API name | "Salesforce" | "Jira" |
| `{API_NAME_UPPER}` | API name uppercase (env vars) | "SALESFORCE" | "JIRA" |
| `{project}` | Project slug (lowercase, underscore) | "salesforce" | "jira" |
| `{api}` | API client name (lowercase) | "salesforce" | "jira" |
| `{Entity}` | Entity type (PascalCase) | "Account", "Contact" | "Issue", "Project" |
| `{entity}` | Entity type (lowercase) | "account", "contact" | "issue", "project" |
| `{entities}` | Entity type (plural) | "accounts", "contacts" | "issues", "projects" |
| `{service}` | Deployment service | "fastmcp" | "fastmcp" |

**Example project values:**

```bash
# For Salesforce integration:
PROJECT_NAME="Salesforce Neo4j Sync"
API_NAME="Salesforce"
API_NAME_UPPER="SALESFORCE"
project="salesforce"
api="salesforce"

# For Jira integration:
PROJECT_NAME="Jira Knowledge Graph"
API_NAME="Jira"
API_NAME_UPPER="JIRA"
project="jira"
api="jira"

# For HubSpot integration:
PROJECT_NAME="HubSpot CRM Sync"
API_NAME="HubSpot"
API_NAME_UPPER="HUBSPOT"
project="hubspot"
api="hubspot"
```

---

## Step-by-Step Customization

### Step 1: Define Your Values

**Create a values file** (e.g., `my_values.txt`):

```bash
# Example for Salesforce
PROJECT_NAME="Salesforce Neo4j Sync"
API_NAME="Salesforce"
API_NAME_UPPER="SALESFORCE"
project="salesforce"
api="salesforce"
```

**Use for search/replace:**
```bash
# macOS/Linux - use sed to replace in all files
find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.toml" -o -name ".env.example" \) -not -path "./.venv/*" -not -path "./.git/*" -exec sed -i '' 's/{PROJECT_NAME}/Salesforce Neo4j Sync/g' {} +

find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.toml" -o -name ".env.example" \) -not -path "./.venv/*" -not -path "./.git/*" -exec sed -i '' 's/{API_NAME_UPPER}/SALESFORCE/g' {} +

find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.toml" -o -name ".env.example" \) -not -path "./.venv/*" -not -path "./.git/*" -exec sed -i '' 's/{API_NAME}/Salesforce/g' {} +

find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.toml" -o -name ".env.example" \) -not -path "./.venv/*" -not -path "./.git/*" -exec sed -i '' 's/{project}/salesforce/g' {} +

find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.toml" -o -name ".env.example" \) -not -path "./.venv/*" -not -path "./.git/*" -exec sed -i '' 's/{api}/salesforce/g' {} +
```

**Or use your editor's global search/replace:**
- VS Code: Cmd/Ctrl + Shift + H
- JetBrains: Cmd/Ctrl + Shift + R

---

### Step 2: Rename Directories and Files

**Rename the main sync package:**
```bash
mv {project}_sync salesforce_sync
```

**Rename the CLI script:**
```bash
mv {project}_sync.py salesforce_sync.py
```

**Verify:**
```bash
ls -l | grep salesforce
# Should show:
# salesforce_sync/
# salesforce_sync.py
```

---

### Step 3: Configure Environment Variables

**Edit `.env.example`:**

```bash
cp .env.example .env
nano .env
```

**Replace with your values:**

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687  # or neo4j+s://your-cloud-instance
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j

# Salesforce API (replace with your API name)
SALESFORCE_CLIENT_ID=your-client-id-here
SALESFORCE_CLIENT_SECRET=your-client-secret-here
SALESFORCE_AUTH_URL=https://login.salesforce.com/services/oauth2/token
SALESFORCE_API_URL=https://your-instance.salesforce.com/services/data/v58.0

# Optional: Work Hours Date Range (if applicable)
# SYNC_WORKHOURS_DAYS_BACK=365
# SYNC_WORKHOURS_START_DATE=2020-01-01
```

**Different authentication patterns:**

**API Key Authentication:**
```bash
{API_NAME_UPPER}_API_KEY=your-api-key-here
{API_NAME_UPPER}_API_URL=https://api.yourservice.com/v1
```

**JWT Authentication:**
```bash
{API_NAME_UPPER}_JWT_SECRET=your-jwt-secret
{API_NAME_UPPER}_API_URL=https://api.yourservice.com
```

**Basic Auth:**
```bash
{API_NAME_UPPER}_USERNAME=your-username
{API_NAME_UPPER}_PASSWORD=your-password
{API_NAME_UPPER}_API_URL=https://api.yourservice.com
```

---

### Step 4: Customize API Client

**File:** `{project}_sync/{api}_client.py` → `salesforce_sync/salesforce_client.py`

**Authentication implementation (OAuth2 example):**

```python
class SalesforceClient:
    def __init__(self, config: SalesforceConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.token_expires_at = None

    async def authenticate(self):
        """OAuth2 authentication"""
        response = await self.client.post(
            self.config.auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
            }
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        # Set expiration (typically 1 hour, refresh at 50%)
        expires_in = data.get("expires_in", 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in * 0.5)
```

**API Key authentication example:**
```python
async def authenticate(self):
    """API Key - no special auth needed, just set headers"""
    self.access_token = self.config.api_key  # Store in token field for consistency
    self.token_expires_at = datetime.max  # Never expires

async def _request(self, method: str, endpoint: str, **kwargs):
    """Make authenticated request with API key"""
    headers = kwargs.get("headers", {})
    headers["X-API-Key"] = self.access_token  # Or Authorization: Bearer {key}
    kwargs["headers"] = headers

    response = await self.client.request(method, endpoint, **kwargs)
    return response
```

**Add entity fetch methods:**

```python
async def get_accounts(self, modified_since: str = None) -> List[Dict]:
    """Fetch Salesforce accounts (customers)

    Args:
        modified_since: ISO date to filter by last modified date

    Returns:
        List of account dictionaries
    """
    endpoint = "/sobjects/Account"
    params = {}
    if modified_since:
        params["q"] = f"SELECT Id, Name, ... WHERE LastModifiedDate > {modified_since}"

    all_records = []
    next_url = endpoint

    while next_url:
        data = await self._paginated_request("GET", next_url, params=params)
        all_records.extend(data.get("records", []))
        next_url = data.get("nextRecordsUrl")  # Salesforce pagination

    return all_records

async def get_contacts(self, account_id: str = None) -> List[Dict]:
    """Fetch Salesforce contacts"""
    endpoint = "/sobjects/Contact"
    params = {}
    if account_id:
        params["q"] = f"SELECT Id, FirstName, LastName, AccountId ... WHERE AccountId = '{account_id}'"

    return await self._fetch_all_pages("GET", endpoint, params=params)
```

---

### Step 5: Design Your Schema

**Create:** `doc/schema_design.md`

**Template:**

```markdown
# {API_NAME} Neo4j Schema Design

## Entity Types (Nodes)

### Account (Customer)
**Label:** `Account`
**Primary Key:** `guid` (Salesforce Id)
**Properties:**
- `guid: String` - Salesforce Account Id
- `name: String` - Account name
- `type: String` - Account type
- `industry: String` - Industry
- `annualRevenue: Float` - Annual revenue
- `createdDate: DateTime` - Created timestamp
- `lastModifiedDate: DateTime` - Last modified timestamp

**Indexes:**
```cypher
CREATE CONSTRAINT account_guid IF NOT EXISTS
FOR (a:Account) REQUIRE a.guid IS NODE KEY;

CREATE INDEX account_name IF NOT EXISTS
FOR (a:Account) ON (a.name);
```

### Contact
**Label:** `Contact`
**Primary Key:** `guid` (Salesforce Id)
**Properties:**
- `guid: String` - Salesforce Contact Id
- `firstName: String`
- `lastName: String`
- `email: String`
- `phone: String`
- `accountGuid: String` - Foreign key to Account (store GUID only!)
- `createdDate: DateTime`

**Indexes:**
```cypher
CREATE CONSTRAINT contact_guid IF NOT EXISTS
FOR (c:Contact) REQUIRE c.guid IS NODE KEY;

CREATE INDEX contact_account_guid IF NOT EXISTS
FOR (c:Contact) ON (c.accountGuid);

CREATE INDEX contact_email IF NOT EXISTS
FOR (c:Contact) ON (c.email);
```

## Relationships

### BELONGS_TO
**Pattern:** `(Contact)-[:BELONGS_TO]->(Account)`
**Created by:** `contact_relationships.py`
**Cypher:**
```cypher
MATCH (c:Contact), (a:Account)
WHERE c.accountGuid = a.guid
MERGE (c)-[:BELONGS_TO]->(a)
```

### HAS_CONTACT
**Pattern:** `(Account)-[:HAS_CONTACT]->(Contact)`
**Created by:** `contact_relationships.py`
**Cypher:**
```cypher
MATCH (a:Account), (c:Contact)
WHERE c.accountGuid = a.guid
MERGE (a)-[:HAS_CONTACT]->(c)
```

## Query Patterns

### Get account with all contacts
```cypher
MATCH (a:Account {guid: $accountGuid})
OPTIONAL MATCH (a)-[:HAS_CONTACT]->(c:Contact)
RETURN a, collect(c) as contacts
```

### Find contacts by email domain
```cypher
MATCH (c:Contact)
WHERE c.email ENDS WITH '@example.com'
RETURN c
```
```

---

### Step 6: Customize Entity Sync Modules

**Example:** Create `salesforce_sync/entities/account.py`

```python
"""Account (Customer) entity sync for Salesforce"""

from typing import List, Dict
from ..neo4j_base import Neo4jBase

class AccountSync(Neo4jBase):
    """Sync Salesforce Accounts to Neo4j Account nodes"""

    async def sync_accounts(self, accounts: List[Dict]) -> int:
        """Sync accounts from Salesforce

        Args:
            accounts: List of account dicts from Salesforce API

        Returns:
            Number of accounts synced
        """
        if not accounts:
            return 0

        query = """
        UNWIND $accounts as account
        MERGE (a:Account {guid: account.Id})
        SET a.name = account.Name,
            a.type = account.Type,
            a.industry = account.Industry,
            a.annualRevenue = account.AnnualRevenue,
            a.createdDate = datetime(account.CreatedDate),
            a.lastModifiedDate = datetime(account.LastModifiedDate),
            a.syncedAt = datetime()
        RETURN count(a) as count
        """

        result = await self.execute_write(query, accounts=accounts)
        return result[0]["count"] if result else 0
```

**Critical pattern - Nested object extraction:**

```python
async def sync_contacts(self, contacts: List[Dict]) -> int:
    """Sync contacts with nested Account references"""

    # Prepare data - extract nested objects
    prepared = []
    for contact in contacts:
        # API returns: {"Id": "123", "Account": {"Id": "acc-456"}}
        # Extract accountGuid from nested object
        account_guid = None
        if contact.get("Account"):  # Check if nested object exists
            account_guid = contact["Account"].get("Id")

        prepared.append({
            "guid": contact["Id"],
            "firstName": contact.get("FirstName"),
            "lastName": contact.get("LastName"),
            "email": contact.get("Email"),
            "accountGuid": account_guid,  # Store foreign key only!
            "createdDate": contact.get("CreatedDate"),
        })

    query = """
    UNWIND $contacts as contact
    MERGE (c:Contact {guid: contact.guid})
    SET c.firstName = contact.firstName,
        c.lastName = contact.lastName,
        c.email = contact.email,
        c.accountGuid = contact.accountGuid,
        c.createdDate = datetime(contact.createdDate),
        c.syncedAt = datetime()
    RETURN count(c) as count
    """

    result = await self.execute_write(query, contacts=prepared)
    return result[0]["count"] if result else 0
```

---

### Step 7: Customize Relationship Modules

**Example:** Create `salesforce_sync/relationships/account_relationships.py`

```python
"""Account relationship sync for Salesforce"""

from ..neo4j_base import Neo4jBase

class AccountRelationshipSync(Neo4jBase):
    """Create relationships for Account entities"""

    async def create_contact_account_relationships(self) -> int:
        """Create BELONGS_TO relationships: Contact -> Account

        Uses accountGuid property on Contact nodes
        """
        query = """
        MATCH (c:Contact)
        WHERE c.accountGuid IS NOT NULL
        MATCH (a:Account {guid: c.accountGuid})
        MERGE (c)-[:BELONGS_TO]->(a)
        RETURN count(*) as count
        """

        result = await self.execute_write(query)
        return result[0]["count"] if result else 0

    async def create_account_contact_relationships(self) -> int:
        """Create HAS_CONTACT relationships: Account -> Contact"""
        query = """
        MATCH (a:Account)
        MATCH (c:Contact {accountGuid: a.guid})
        MERGE (a)-[:HAS_CONTACT]->(c)
        RETURN count(*) as count
        """

        result = await self.execute_write(query)
        return result[0]["count"] if result else 0
```

---

### Step 8: Update Orchestrator

**File:** `{project}_sync/orchestrator.py`

**Register all entity sync methods:**

```python
class SyncOrchestrator:
    def __init__(self, config):
        self.config = config
        self.api_client = SalesforceClient(config.salesforce)

        # Import your entity sync modules
        from .entities.account import AccountSync
        from .entities.contact import ContactSync
        # ... more imports

        self.account_sync = AccountSync(config.neo4j)
        self.contact_sync = ContactSync(config.neo4j)
        # ... more instances

    async def sync_all_entities(self):
        """Sync all entity types"""
        logger.info("Starting entity sync...")

        # Sync accounts
        logger.info("Syncing accounts...")
        accounts = await self.api_client.get_accounts()
        count = await self.account_sync.sync_accounts(accounts)
        logger.info(f"Synced {count} accounts")

        # Sync contacts
        logger.info("Syncing contacts...")
        contacts = await self.api_client.get_contacts()
        count = await self.contact_sync.sync_contacts(contacts)
        logger.info(f"Synced {count} contacts")

        # ... more entity types

        logger.info("Entity sync complete")
```

**Register all relationship methods:**

```python
async def create_all_relationships(self):
    """Create all relationship types"""
    logger.info("Creating relationships...")

    # Import relationship modules
    from .relationships.account_relationships import AccountRelationshipSync

    account_rel_sync = AccountRelationshipSync(self.config.neo4j)

    # Create Contact -> Account relationships
    count = await account_rel_sync.create_contact_account_relationships()
    logger.info(f"Created {count} Contact->Account relationships")

    # Create Account -> Contact relationships
    count = await account_rel_sync.create_account_contact_relationships()
    logger.info(f"Created {count} Account->Contact relationships")

    # ... more relationship types

    logger.info("Relationship creation complete")
```

**CRITICAL: Verify all methods are registered:**

```bash
# Count relationship method definitions
grep -r "def create_.*_relationships" salesforce_sync/relationships/*.py | wc -l

# Count relationship method calls in orchestrator
grep "create_.*_relationships()" salesforce_sync/orchestrator.py | wc -l

# These numbers MUST match!
```

---

### Step 9: Update Configuration

**File:** `{project}_sync/config.py`

```python
"""Configuration for Salesforce Neo4j Sync"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Neo4jConfig:
    """Neo4j connection configuration"""
    uri: str
    username: str
    password: str
    database: str = "neo4j"

    @classmethod
    def from_env(cls):
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", ""),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )

@dataclass
class SalesforceConfig:
    """Salesforce API configuration"""
    client_id: str
    client_secret: str
    auth_url: str
    api_url: str

    @classmethod
    def from_env(cls):
        return cls(
            client_id=os.getenv("SALESFORCE_CLIENT_ID", ""),
            client_secret=os.getenv("SALESFORCE_CLIENT_SECRET", ""),
            auth_url=os.getenv("SALESFORCE_AUTH_URL", "https://login.salesforce.com/services/oauth2/token"),
            api_url=os.getenv("SALESFORCE_API_URL", ""),
        )

@dataclass
class AppConfig:
    """Application configuration"""
    neo4j: Neo4jConfig
    salesforce: SalesforceConfig

    @classmethod
    def from_env(cls):
        return cls(
            neo4j=Neo4jConfig.from_env(),
            salesforce=SalesforceConfig.from_env(),
        )
```

---

### Step 10: Write Tests

**File:** `test/test_account_sync.py`

```python
"""Tests for Account entity sync"""

import pytest
from salesforce_sync.entities.account import AccountSync

@pytest.mark.asyncio
async def test_sync_accounts(neo4j_config):
    """Test syncing accounts"""
    sync = AccountSync(neo4j_config)

    # Mock data
    accounts = [
        {
            "Id": "acc-1",
            "Name": "Acme Corp",
            "Type": "Customer",
            "Industry": "Technology",
            "AnnualRevenue": 1000000.0,
            "CreatedDate": "2024-01-01T00:00:00Z",
            "LastModifiedDate": "2024-10-01T00:00:00Z",
        }
    ]

    count = await sync.sync_accounts(accounts)
    assert count == 1

    # Verify in Neo4j
    result = await sync.execute_read(
        "MATCH (a:Account {guid: $guid}) RETURN a",
        guid="acc-1"
    )
    assert len(result) == 1
    assert result[0]["a"]["name"] == "Acme Corp"
```

**File:** `test/test_account_relationships.py`

```python
"""Tests for Account relationships"""

import pytest
from salesforce_sync.entities.account import AccountSync
from salesforce_sync.entities.contact import ContactSync
from salesforce_sync.relationships.account_relationships import AccountRelationshipSync

@pytest.mark.asyncio
async def test_create_contact_account_relationships(neo4j_config):
    """Test creating Contact -> Account relationships"""

    # Setup: Create test data
    account_sync = AccountSync(neo4j_config)
    contact_sync = ContactSync(neo4j_config)

    await account_sync.sync_accounts([
        {"Id": "acc-1", "Name": "Acme Corp", "CreatedDate": "2024-01-01T00:00:00Z"}
    ])

    await contact_sync.sync_contacts([
        {
            "Id": "con-1",
            "FirstName": "John",
            "LastName": "Doe",
            "Email": "john@acme.com",
            "Account": {"Id": "acc-1"},  # Nested object!
            "CreatedDate": "2024-01-01T00:00:00Z"
        }
    ])

    # Test: Create relationships
    rel_sync = AccountRelationshipSync(neo4j_config)
    count = await rel_sync.create_contact_account_relationships()

    assert count == 1

    # Verify relationship exists
    result = await rel_sync.execute_read("""
        MATCH (c:Contact {guid: 'con-1'})-[:BELONGS_TO]->(a:Account {guid: 'acc-1'})
        RETURN count(*) as count
    """)
    assert result[0]["count"] == 1
```

---

### Step 11: Update Documentation

**Files to customize:**

1. **README.md** - Update project name, API references
2. **CLAUDE.md** - Update workflow examples
3. **doc/GETTING_STARTED.md** - Update setup instructions
4. **doc/API_INTEGRATION_GUIDE.md** - Add API-specific patterns
5. **doc/SCHEMA_DESIGN_GUIDE.md** - Reference your schema
6. **doc/DEVELOPMENT_GUIDELINES.md** - Update examples
7. **doc/TEST_GUIDE.md** - Update test examples

**Search for remaining placeholders:**
```bash
grep -r "{PROJECT_NAME}" --exclude-dir=.venv --exclude-dir=.git .
grep -r "{API_NAME}" --exclude-dir=.venv --exclude-dir=.git .
grep -r "{project}" --exclude-dir=.venv --exclude-dir=.git .
```

---

## Verification Checklist

**After customization, verify:**

- [ ] All placeholders replaced (run grep commands above)
- [ ] Directories renamed (`{project}_sync` → `your_project_sync`)
- [ ] Files renamed (`{project}_sync.py` → `your_project_sync.py`)
- [ ] `.env` configured with real credentials
- [ ] `config.py` loads correct environment variables
- [ ] API client implements authentication
- [ ] Entity sync modules created for all entity types
- [ ] Relationship modules created
- [ ] All methods registered in orchestrator
- [ ] Orchestrator method counts match: `grep -r "def create_.*_relationships" | wc -l` == `grep "create_.*_relationships()" orchestrator.py | wc -l`
- [ ] Tests written for entities and relationships
- [ ] Documentation updated with project name

**Test basic setup:**
```bash
# 1. Config loads
uv run python -c "from salesforce_sync.config import AppConfig; config = AppConfig.from_env(); print('✓ Config loaded')"

# 2. Neo4j connection works
uv run python -c "from salesforce_sync.neo4j_base import Neo4jBase; from salesforce_sync.config import Neo4jConfig; import asyncio; base = Neo4jBase(Neo4jConfig.from_env()); asyncio.run(base.verify_connection()); print('✓ Neo4j connected')"

# 3. API client authenticates
uv run python -c "from salesforce_sync.salesforce_client import SalesforceClient; from salesforce_sync.config import SalesforceConfig; import asyncio; client = SalesforceClient(SalesforceConfig.from_env()); asyncio.run(client.authenticate()); print('✓ API authenticated')"

# 4. Run tests
uv run pytest test/ -v -m "not live" --cov=salesforce_sync

# 5. Full sync
uv run salesforce_sync.py --mode full
```

---

## Common Customization Scenarios

### Scenario 1: Jira API with Bearer Token

**Authentication:**
```python
# config.py
@dataclass
class JiraConfig:
    api_token: str
    api_url: str
    email: str  # Jira requires email for auth

    @classmethod
    def from_env(cls):
        return cls(
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            api_url=os.getenv("JIRA_API_URL", ""),
            email=os.getenv("JIRA_EMAIL", ""),
        )

# jira_client.py
async def authenticate(self):
    """Jira uses Basic auth with email + API token"""
    import base64
    auth_string = f"{self.config.email}:{self.config.api_token}"
    encoded = base64.b64encode(auth_string.encode()).decode()
    self.access_token = f"Basic {encoded}"
    self.token_expires_at = datetime.max  # Never expires

async def _request(self, method: str, endpoint: str, **kwargs):
    headers = kwargs.get("headers", {})
    headers["Authorization"] = self.access_token
    headers["Accept"] = "application/json"
    kwargs["headers"] = headers

    url = f"{self.config.api_url}{endpoint}"
    response = await self.client.request(method, url, **kwargs)
    return response
```

### Scenario 2: Shopify with Cursor-Based Pagination

**Pagination:**
```python
async def get_orders(self, created_at_min: str = None) -> List[Dict]:
    """Fetch Shopify orders with cursor pagination"""
    endpoint = "/admin/api/2024-01/orders.json"
    params = {"limit": 250}  # Shopify max
    if created_at_min:
        params["created_at_min"] = created_at_min

    all_orders = []

    while True:
        response = await self._request("GET", endpoint, params=params)
        data = response.json()

        orders = data.get("orders", [])
        all_orders.extend(orders)

        # Cursor-based pagination via Link header
        link_header = response.headers.get("Link")
        if not link_header or "rel=\"next\"" not in link_header:
            break

        # Parse next cursor from Link header
        next_url = self._parse_next_link(link_header)
        endpoint = next_url.replace(self.config.api_url, "")
        params = {}  # Cursor included in URL

    return all_orders

def _parse_next_link(self, link_header: str) -> str:
    """Extract next URL from Link header"""
    import re
    match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
    return match.group(1) if match else None
```

### Scenario 3: Stripe with Offset Pagination

**Pagination:**
```python
async def get_customers(self, created_after: int = None) -> List[Dict]:
    """Fetch Stripe customers with offset pagination"""
    endpoint = "/v1/customers"
    params = {"limit": 100}  # Stripe max
    if created_after:
        params["created[gte]"] = created_after

    all_customers = []

    while True:
        response = await self._request("GET", endpoint, params=params)
        data = response.json()

        customers = data.get("data", [])
        all_customers.extend(customers)

        # Check if more pages
        if not data.get("has_more"):
            break

        # Use last customer ID as offset
        params["starting_after"] = customers[-1]["id"]

    return all_customers
```

### Scenario 4: GitHub with Page Number Pagination

**Pagination:**
```python
async def get_issues(self, repo: str, state: str = "all") -> List[Dict]:
    """Fetch GitHub issues with page-number pagination"""
    endpoint = f"/repos/{repo}/issues"
    params = {"state": state, "per_page": 100, "page": 1}  # GitHub max 100

    all_issues = []

    while True:
        response = await self._request("GET", endpoint, params=params)
        issues = response.json()

        if not issues:
            break

        all_issues.extend(issues)
        params["page"] += 1

        # GitHub returns empty array when no more pages
        if len(issues) < 100:
            break

    return all_issues
```

---

## Troubleshooting

### Issue: "Module not found after renaming"

**Solution:** Update imports in all files

```bash
# Find all imports of old module name
grep -r "from {project}_sync" --exclude-dir=.venv .
grep -r "import {project}_sync" --exclude-dir=.venv .

# Replace with new name
find . -type f -name "*.py" -not -path "./.venv/*" -exec sed -i '' 's/from {project}_sync/from salesforce_sync/g' {} +
```

### Issue: "Config validation fails"

**Solution:** Check `.env` has all required variables

```bash
# List required env vars
grep "os.getenv" salesforce_sync/config.py

# Verify .env has these vars
cat .env | grep -E "SALESFORCE|NEO4J"
```

### Issue: "Authentication fails"

**Solution:** Test API credentials separately

```bash
# Test with curl (Salesforce OAuth2 example)
curl -X POST https://login.salesforce.com/services/oauth2/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"

# Should return: {"access_token": "...", "expires_in": 3600}
```

### Issue: "Nested object extraction fails"

**Solution:** Print API response to verify structure

```python
# In entity sync, before processing:
import json
print(json.dumps(api_response[0], indent=2))

# Look for nested objects like:
# {
#   "Id": "123",
#   "Account": {        # <-- Nested object!
#     "Id": "acc-456"
#   }
# }

# Extract correctly:
account_guid = None
if data.get("Account"):
    account_guid = data["Account"].get("Id")
```

### Issue: "Relationship creation returns 0"

**Solution:** Verify foreign GUIDs are stored

```cypher
// Check if foreign keys exist
MATCH (c:Contact)
RETURN c.guid, c.accountGuid
LIMIT 5

// If accountGuid is NULL, entity sync isn't extracting correctly
```

### Issue: "Tests fail with 'connection refused'"

**Solution:** Start Neo4j and verify connection

```bash
# Check Neo4j is running
docker ps | grep neo4j
# OR for desktop:
ps aux | grep neo4j

# Test connection
curl http://localhost:7474
# Should return Neo4j browser HTML

# Verify credentials in .env match Neo4j
```

---

## Next Steps

**After customization:**

1. **Run verification checklist** (above)
2. **Follow doc/GETTING_STARTED.md** for first sync
3. **Review task/TASK_MASTER_GUIDE.md** for implementation phases
4. **Start Phase 1** (Setup & Configuration)

**Questions?** Create an issue or check the documentation guides.

**Ready to sync?** Run `uv run {project}_sync.py --mode full`
