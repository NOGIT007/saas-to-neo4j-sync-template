"""
{API_NAME} API Client
=====================
HTTP client for {API_NAME} API with authentication, pagination, and retry logic.

Features:
- OAuth 2.0 authentication with automatic token refresh
- Token-based pagination support
- Exponential backoff retry logic
- Rate limiting handling
- Request timeout configuration

TODO: Customize for your specific API
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
import requests

from .config import {API}Config

logger = logging.getLogger(__name__)


class {API}Client:
    """
    HTTP client for {API_NAME} API

    Handles authentication, pagination, retries, and rate limiting.

    TODO: Adjust authentication method for your API (OAuth, API key, JWT, etc.)
    """

    def __init__(self, config: {API}Config):
        """
        Initialize API client

        Args:
            config: {API_NAME} API configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "{project}-sync/0.1.0",
            "Accept": "application/json"
        })

    # =========================================================================
    # Authentication
    # =========================================================================

    def authenticate(self) -> bool:
        """
        Authenticate with {API_NAME} API using OAuth 2.0

        TODO: Implement authentication for your specific API:
        - OAuth 2.0 (client credentials, authorization code)
        - API key in headers
        - JWT tokens
        - Basic auth

        Returns:
            bool: True if authentication successful
        """
        logger.info("Authenticating with {API_NAME} API...")

        try:
            # TODO: Implement your authentication flow
            # Example: OAuth 2.0 client credentials
            response = self.session.post(
                f"{self.config.api_url}/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret
                },
                timeout=self.config.request_timeout
            )
            response.raise_for_status()

            data = response.json()
            self.config.token = data["access_token"]

            # Set authorization header
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.token}"
            })

            logger.info("✓ Authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Authentication failed: {e}")
            return False

    # =========================================================================
    # Request Methods
    # =========================================================================

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        paginated: bool = True
    ) -> List[Dict]:
        """
        Make HTTP GET request with automatic pagination

        Handles token-based pagination and collects all pages.

        TODO: Adjust pagination logic for your API:
        - Token-based pagination (NextPageToken header)
        - Offset-based pagination (?offset=0&limit=100)
        - Cursor-based pagination (?cursor=xyz)
        - Page number pagination (?page=1&per_page=100)

        Args:
            endpoint: API endpoint path (e.g., "/customers")
            params: Query parameters
            paginated: Whether to automatically paginate

        Returns:
            List of items from all pages
        """
        url = f"{self.config.api_url}{endpoint}"
        all_items = []
        next_page_token = None
        page_num = 1

        params = params or {}

        while True:
            # TODO: Adjust pagination parameter for your API
            paginated_params = params.copy()
            if paginated and next_page_token:
                paginated_params["pageToken"] = next_page_token  # Token-based
                # OR: paginated_params["offset"] = page_num * self.config.batch_size  # Offset-based
                # OR: paginated_params["cursor"] = next_page_token  # Cursor-based
                # OR: paginated_params["page"] = page_num  # Page number-based

            logger.info(f"  Fetching {endpoint} (page {page_num})...")

            # Make single request with retry logic
            data, next_page_token = self._make_single_request(url, paginated_params)

            # Extract items from response
            # TODO: Adjust for your API response structure
            items = data.get("items", [])  # Or data.get("results"), or just data if list
            all_items.extend(items)

            logger.info(f"    Got {len(items)} items (total: {len(all_items)})")

            # Check if more pages
            if not paginated or not next_page_token:
                break

            page_num += 1

        logger.info(f"✓ Fetched {len(all_items)} total items from {endpoint}")
        return all_items

    def _make_single_request(
        self,
        url: str,
        params: Dict
    ) -> Tuple[Dict, Optional[str]]:
        """
        Make single HTTP request with retry logic and exponential backoff

        Handles:
        - 401 Unauthorized: Re-authenticate and retry
        - 429 Too Many Requests: Exponential backoff
        - 5xx Server Errors: Retry with backoff
        - Network errors: Retry with backoff

        Args:
            url: Full URL to request
            params: Query parameters

        Returns:
            Tuple of (response data, next page token)
        """
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.request_timeout
                )
                response.raise_for_status()

                data = response.json()

                # Extract next page token
                # TODO: Adjust for your API pagination
                next_token = response.headers.get("NextPageToken")  # Header-based
                # OR: next_token = data.get("nextPageToken")  # Body-based
                # OR: next_token = data.get("pagination", {}).get("next")

                return data, next_token

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # Unauthorized - re-authenticate
                    logger.warning("Token expired, re-authenticating...")
                    if self.authenticate():
                        continue  # Retry with new token
                    else:
                        raise

                elif e.response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                elif 500 <= e.response.status_code < 600:
                    # Server error - retry with backoff
                    wait_time = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    # Other HTTP error - don't retry
                    raise

            except requests.exceptions.RequestException as e:
                # Network error - retry with backoff
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed ({e}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise

        # Max retries exceeded
        raise Exception(f"Max retries ({self.config.max_retries}) exceeded for {url}")

    # =========================================================================
    # Entity-Specific Methods
    # =========================================================================
    # TODO: Add methods for fetching each entity type from your API
    #
    # Example patterns:
    #
    # def get_customers(self) -> List[Dict]:
    #     """Fetch all customers"""
    #     return self._make_request("/customers")
    #
    # def get_users(self) -> List[Dict]:
    #     """Fetch all users"""
    #     return self._make_request("/users")
    #
    # def get_projects(self, customer_id: Optional[str] = None) -> List[Dict]:
    #     """Fetch projects, optionally filtered by customer"""
    #     params = {"customerId": customer_id} if customer_id else {}
    #     return self._make_request("/projects", params=params)
    #
    # def get_transactions(self, start_date: str, end_date: str) -> List[Dict]:
    #     """Fetch transactions within date range"""
    #     params = {"startDate": start_date, "endDate": end_date}
    #     return self._make_request("/transactions", params=params)
    #
    # def get_{entity}(self) -> List[Dict]:
    #     """Fetch {entity} data"""
    #     return self._make_request("/{entities}")
