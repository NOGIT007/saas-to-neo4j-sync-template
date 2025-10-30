"""
API Client Tests

Tests for API client authentication, pagination, retry logic, and error handling.

Run:
    pytest test/test_api_client.py -v

TODO: Customize for your specific API behavior and authentication method
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests

# TODO: Update import paths to match your project
from {project}_sync.{api}_client import {API}Client
from {project}_sync.config import {API}Config


class TestAuthentication:
    """Tests for API authentication"""

    @patch('requests.Session.post')
    def test_authenticate_success_oauth(self, mock_post, api_config):
        """Test successful OAuth authentication"""
        # Mock successful OAuth response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        client = {API}Client(api_config)
        result = client.authenticate()

        assert result is True
        assert client.config.token == "test_token_12345"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_token_12345"

    @patch('requests.Session.post')
    def test_authenticate_failure(self, mock_post, api_config):
        """Test authentication failure handling"""
        # Mock failed authentication
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response

        client = {API}Client(api_config)
        result = client.authenticate()

        assert result is False
        assert client.config.token is None

    @patch('requests.Session.post')
    def test_authenticate_network_error(self, mock_post, api_config):
        """Test authentication with network error"""
        # Mock network error
        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        client = {API}Client(api_config)
        result = client.authenticate()

        assert result is False

    # TODO: Add tests for other authentication methods if your API uses them
    # def test_authenticate_api_key(self):
    #     """Test API key authentication"""
    #     pass
    #
    # def test_authenticate_jwt(self):
    #     """Test JWT authentication"""
    #     pass


class TestPagination:
    """Tests for API pagination handling"""

    @patch.object({API}Client, '_make_single_request')
    def test_pagination_single_page(self, mock_request, api_config):
        """Test fetching single page (no pagination needed)"""
        # Mock single page response
        mock_request.return_value = (
            {"items": [{"id": 1}, {"id": 2}]},
            None  # No next page token
        )

        client = {API}Client(api_config)
        result = client._make_request("/test-endpoint", paginated=True)

        assert len(result) == 2
        assert mock_request.call_count == 1

    @patch.object({API}Client, '_make_single_request')
    def test_pagination_multiple_pages(self, mock_request, api_config):
        """Test fetching multiple pages"""
        # Mock three pages of results
        mock_request.side_effect = [
            ({"items": [{"id": 1}, {"id": 2}]}, "page2_token"),
            ({"items": [{"id": 3}, {"id": 4}]}, "page3_token"),
            ({"items": [{"id": 5}]}, None)  # Last page
        ]

        client = {API}Client(api_config)
        result = client._make_request("/test-endpoint", paginated=True)

        assert len(result) == 5
        assert mock_request.call_count == 3

    @patch.object({API}Client, '_make_single_request')
    def test_pagination_disabled(self, mock_request, api_config):
        """Test with pagination disabled"""
        # Mock response
        mock_request.return_value = (
            {"items": [{"id": 1}, {"id": 2}]},
            "page2_token"  # Token present but should be ignored
        )

        client = {API}Client(api_config)
        result = client._make_request("/test-endpoint", paginated=False)

        assert len(result) == 2
        assert mock_request.call_count == 1  # Only one call

    @patch.object({API}Client, '_make_single_request')
    def test_pagination_empty_response(self, mock_request, api_config):
        """Test handling empty response"""
        # Mock empty response
        mock_request.return_value = (
            {"items": []},
            None
        )

        client = {API}Client(api_config)
        result = client._make_request("/test-endpoint", paginated=True)

        assert len(result) == 0

    # TODO: Add tests for your specific pagination method
    # def test_pagination_offset_based(self):
    #     """Test offset-based pagination"""
    #     pass
    #
    # def test_pagination_cursor_based(self):
    #     """Test cursor-based pagination"""
    #     pass


class TestRetryLogic:
    """Tests for retry logic and error handling"""

    @patch('requests.Session.get')
    def test_retry_on_500_error(self, mock_get, api_config):
        """Test retry on 5xx server error"""
        # First two calls fail, third succeeds
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"items": []}
        success_response.headers = {}

        mock_get.side_effect = [
            error_response,
            error_response,
            success_response
        ]

        client = {API}Client(api_config)
        data, token = client._make_single_request("https://api.example.com/test", {})

        assert data == {"items": []}
        assert mock_get.call_count == 3

    @patch('requests.Session.get')
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_retry_on_rate_limit(self, mock_sleep, mock_get, api_config):
        """Test retry with exponential backoff on 429 rate limit"""
        # First call rate limited, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"items": []}
        success_response.headers = {}

        mock_get.side_effect = [rate_limit_response, success_response]

        client = {API}Client(api_config)
        data, token = client._make_single_request("https://api.example.com/test", {})

        assert data == {"items": []}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()  # Verify backoff occurred

    @patch('requests.Session.get')
    def test_retry_on_401_with_reauth(self, mock_get, api_config):
        """Test retry on 401 with re-authentication"""
        # First call unauthorized, should re-auth and retry
        unauth_response = Mock()
        unauth_response.status_code = 401
        unauth_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"items": []}
        success_response.headers = {}

        mock_get.side_effect = [unauth_response, success_response]

        client = {API}Client(api_config)

        # Mock successful re-authentication
        with patch.object(client, 'authenticate', return_value=True):
            data, token = client._make_single_request("https://api.example.com/test", {})

        assert data == {"items": []}
        assert mock_get.call_count == 2

    @patch('requests.Session.get')
    def test_max_retries_exceeded(self, mock_get, api_config):
        """Test that max retries limit is enforced"""
        # All calls fail
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = error_response

        client = {API}Client(api_config)
        client.config.max_retries = 3

        with pytest.raises(Exception, match="Max retries.*exceeded"):
            client._make_single_request("https://api.example.com/test", {})

        assert mock_get.call_count == 3

    @patch('requests.Session.get')
    def test_no_retry_on_400_error(self, mock_get, api_config):
        """Test that 4xx errors (except 401, 429) don't retry"""
        # 400 Bad Request should not retry
        error_response = Mock()
        error_response.status_code = 400
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = error_response

        client = {API}Client(api_config)

        with pytest.raises(requests.exceptions.HTTPError):
            client._make_single_request("https://api.example.com/test", {})

        assert mock_get.call_count == 1  # No retries


class TestRequestMethods:
    """Tests for request helper methods"""

    @patch('requests.Session.get')
    def test_make_request_with_params(self, mock_get, api_config):
        """Test request with query parameters"""
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"items": [{"id": 1}]}
        success_response.headers = {}
        mock_get.return_value = success_response

        client = {API}Client(api_config)
        result = client._make_request("/test", params={"filter": "active"}, paginated=False)

        assert len(result) == 1
        # Verify params were passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"] == {"filter": "active"}

    @patch('requests.Session.get')
    def test_request_timeout_configuration(self, mock_get, api_config):
        """Test that request timeout is configured"""
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"items": []}
        success_response.headers = {}
        mock_get.return_value = success_response

        api_config.request_timeout = 120
        client = {API}Client(api_config)
        client._make_single_request("https://api.example.com/test", {})

        # Verify timeout was passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["timeout"] == 120


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestAPIClientIntegration:
    """
    Integration tests with real API

    These tests require:
    - Valid API credentials in .env
    - Network connectivity
    - API availability

    Skip with: pytest -m "not integration"
    """

    def test_real_authentication(self, api_client):
        """Test authentication with real API"""
        result = api_client.authenticate()

        assert result is True
        assert api_client.config.token is not None

    # TODO: Add integration tests for your specific endpoints
    # def test_fetch_customers(self, api_client):
    #     """Test fetching customers from real API"""
    #     api_client.authenticate()
    #     customers = api_client.get_customers()
    #
    #     assert isinstance(customers, list)
    #     if len(customers) > 0:
    #         assert "guid" in customers[0]
    #
    # def test_fetch_with_pagination(self, api_client):
    #     """Test pagination with real API"""
    #     api_client.authenticate()
    #     results = api_client.get_{entity}()
    #
    #     # Should handle pagination automatically
    #     assert isinstance(results, list)
