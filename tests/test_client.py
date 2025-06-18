"""Tests for the Notion API client."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from notion_to_json.client import NotionClient, RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_interval(self):
        """Test that rate limiter enforces minimum interval between requests."""
        rate_limiter = RateLimiter(requests_per_second=10.0)  # 0.1 second interval

        start_time = asyncio.get_event_loop().time()
        await rate_limiter.acquire()
        await rate_limiter.acquire()
        end_time = asyncio.get_event_loop().time()

        # Second acquire should wait at least 0.1 seconds
        assert end_time - start_time >= 0.09  # Allow small margin

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_requests(self):
        """Test that rate limiter handles concurrent requests properly."""
        rate_limiter = RateLimiter(requests_per_second=10.0)

        async def make_request():
            await rate_limiter.acquire()
            return asyncio.get_event_loop().time()

        # Make 3 concurrent requests
        times = await asyncio.gather(
            make_request(),
            make_request(),
            make_request(),
        )

        # Each request should be at least 0.1 seconds apart
        for i in range(1, len(times)):
            assert times[i] - times[i - 1] >= 0.09


class TestNotionClient:
    """Test cases for NotionClient."""

    def test_client_initialization(self):
        """Test that client initializes with API key and proper configuration."""
        api_key = "test-api-key"
        client = NotionClient(api_key)

        assert client.api_key == api_key
        assert client.base_url == "https://api.notion.com/v1"
        assert isinstance(client.rate_limiter, RateLimiter)
        assert isinstance(client.client, httpx.AsyncClient)

    def test_headers_configuration(self):
        """Test that headers are properly configured."""
        api_key = "test-api-key"
        client = NotionClient(api_key)
        headers = client._get_headers()

        assert headers["Authorization"] == f"Bearer {api_key}"
        assert headers["Notion-Version"] == "2022-06-28"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Test successful API request."""
        client = NotionClient("test-api-key")

        # Mock the httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"id": "user1"}]}
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            result = await client.request("GET", "/users")

        assert result == {"results": [{"id": "user1"}]}
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test that client handles rate limit (429) responses."""
        client = NotionClient("test-api-key")

        # Mock rate limit response followed by success
        mock_rate_limit = Mock()
        mock_rate_limit.status_code = 429
        mock_rate_limit.headers = {"Retry-After": "1"}

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"success": True}
        mock_success.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[mock_rate_limit, mock_success])
        with patch.object(client.client, "request", mock_request):
            with patch("asyncio.sleep", AsyncMock()):  # Speed up test
                result = await client.request("GET", "/test")

        assert result == {"success": True}
        assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self):
        """Test that client retries on server errors (5xx)."""
        client = NotionClient("test-api-key")

        # Mock server error followed by success
        mock_error = Mock()
        mock_error.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=Mock(status_code=500)
        )

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"success": True}
        mock_success.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[mock_error, mock_success])
        with patch.object(client.client, "request", mock_request):
            with patch("asyncio.sleep", AsyncMock()):  # Speed up test
                result = await client.request("GET", "/test", retry_count=1)

        assert result == {"success": True}
        assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self):
        """Test that client doesn't retry on client errors (4xx)."""
        client = NotionClient("test-api-key")

        # Mock client error
        mock_error = Mock()
        mock_error.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=Mock(status_code=400)
        )

        mock_request = AsyncMock(return_value=mock_error)
        with patch.object(client.client, "request", mock_request):
            with pytest.raises(httpx.HTTPStatusError):
                await client.request("GET", "/test")

        # Should only try once for client errors
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """Test that client retries on network errors."""
        client = NotionClient("test-api-key")

        # Mock network error followed by success
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"success": True}
        mock_success.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[httpx.RequestError("Network error"), mock_success])
        with patch.object(client.client, "request", mock_request):
            with patch("asyncio.sleep", AsyncMock()):  # Speed up test
                result = await client.request("GET", "/test", retry_count=1)

        assert result == {"success": True}
        assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_get_users(self):
        """Test get_users method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"id": "user1", "name": "Test User"}]}
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            result = await client.get_users()

        assert result == {"results": [{"id": "user1", "name": "Test User"}]}
        mock_request.assert_called_with(
            method="GET",
            url="https://api.notion.com/v1/users",
            json=None,
            params=None,
        )

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test that client works as async context manager."""
        api_key = "test-api-key"

        async with NotionClient(api_key) as client:
            assert client.api_key == api_key

        # Client should be closed after exiting context
        assert client.client.is_closed

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test that close method properly closes the client."""
        client = NotionClient("test-api-key")
        await client.close()

        assert client.client.is_closed

    @pytest.mark.asyncio
    async def test_search_method(self):
        """Test search method with various parameters."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "page1", "object": "page"}],
            "has_more": False,
            "next_cursor": None,
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            result = await client.search(filter_type="page", query="test", page_size=50)

        assert result["results"][0]["id"] == "page1"
        mock_request.assert_called_with(
            method="POST",
            url="https://api.notion.com/v1/search",
            json={
                "page_size": 50,
                "filter": {"property": "object", "value": "page"},
                "query": "test",
            },
            params=None,
        )

    @pytest.mark.asyncio
    async def test_search_all_with_pagination(self):
        """Test search_all handles pagination correctly."""
        client = NotionClient("test-api-key")

        # First response with more pages
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "results": [{"id": "page1"}, {"id": "page2"}],
            "has_more": True,
            "next_cursor": "cursor123",
        }
        mock_response1.raise_for_status = Mock()

        # Second response without more pages
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "results": [{"id": "page3"}],
            "has_more": False,
            "next_cursor": None,
        }
        mock_response2.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[mock_response1, mock_response2])
        with patch.object(client.client, "request", mock_request):
            results = await client.search_all(filter_type="page")

        assert len(results) == 3
        assert results[0]["id"] == "page1"
        assert results[1]["id"] == "page2"
        assert results[2]["id"] == "page3"

        # Verify both calls were made
        assert mock_request.call_count == 2

        # Check second call included cursor
        second_call_json = mock_request.call_args_list[1][1]["json"]
        assert second_call_json["start_cursor"] == "cursor123"

    @pytest.mark.asyncio
    async def test_search_pages(self):
        """Test search_pages method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "page1", "object": "page"}],
            "has_more": False,
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            pages = await client.search_pages(query="test")

        assert len(pages) == 1
        assert pages[0]["id"] == "page1"

        # Verify filter was set correctly
        call_json = mock_request.call_args[1]["json"]
        assert call_json["filter"]["value"] == "page"
        assert call_json["query"] == "test"

    @pytest.mark.asyncio
    async def test_search_databases(self):
        """Test search_databases method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "db1", "object": "database"}],
            "has_more": False,
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            databases = await client.search_databases()

        assert len(databases) == 1
        assert databases[0]["id"] == "db1"

        # Verify filter was set correctly
        call_json = mock_request.call_args[1]["json"]
        assert call_json["filter"]["value"] == "database"

    @pytest.mark.asyncio
    async def test_get_page_blocks(self):
        """Test get_page_blocks method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "block1", "type": "paragraph", "has_children": False},
                {"id": "block2", "type": "heading_1", "has_children": False},
            ],
            "has_more": False,
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            blocks = await client.get_page_blocks("page123")

        assert blocks["results"][0]["id"] == "block1"
        assert blocks["results"][1]["type"] == "heading_1"
        mock_request.assert_called_with(
            method="GET",
            url="https://api.notion.com/v1/blocks/page123/children",
            json=None,
            params={"page_size": 100},
        )

    @pytest.mark.asyncio
    async def test_get_all_page_blocks_with_pagination(self):
        """Test get_all_page_blocks handles pagination."""
        client = NotionClient("test-api-key")

        # First response with more blocks
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "results": [{"id": "block1"}, {"id": "block2"}],
            "has_more": True,
            "next_cursor": "cursor123",
        }
        mock_response1.raise_for_status = Mock()

        # Second response without more blocks
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "results": [{"id": "block3"}],
            "has_more": False,
        }
        mock_response2.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[mock_response1, mock_response2])
        with patch.object(client.client, "request", mock_request):
            blocks = await client.get_all_page_blocks("page123")

        assert len(blocks) == 3
        assert blocks[0]["id"] == "block1"
        assert blocks[2]["id"] == "block3"

    @pytest.mark.asyncio
    async def test_get_page_content_recursive(self):
        """Test recursive page content retrieval."""
        client = NotionClient("test-api-key")

        # Mock response for parent page blocks
        parent_blocks = Mock()
        parent_blocks.status_code = 200
        parent_blocks.json.return_value = {
            "results": [
                {"id": "block1", "type": "paragraph", "has_children": False},
                {"id": "block2", "type": "toggle", "has_children": True},
            ],
            "has_more": False,
        }
        parent_blocks.raise_for_status = Mock()

        # Mock response for child blocks
        child_blocks = Mock()
        child_blocks.status_code = 200
        child_blocks.json.return_value = {
            "results": [
                {"id": "child1", "type": "paragraph", "has_children": False},
            ],
            "has_more": False,
        }
        child_blocks.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[parent_blocks, child_blocks])
        with patch.object(client.client, "request", mock_request):
            content = await client.get_page_content_recursive("page123")

        assert len(content["blocks"]) == 2
        assert content["blocks"][1]["has_children"] is True
        assert len(content["blocks"][1]["children"]) == 1
        assert content["blocks"][1]["children"][0]["id"] == "child1"

    @pytest.mark.asyncio
    async def test_query_database(self):
        """Test query_database method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "entry1", "properties": {}},
                {"id": "entry2", "properties": {}},
            ],
            "has_more": False,
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            entries = await client.query_database(
                "db123",
                filter_obj={"property": "Status", "select": {"equals": "Done"}},
                sorts=[{"property": "Created", "direction": "descending"}],
            )

        assert len(entries["results"]) == 2
        call_json = mock_request.call_args[1]["json"]
        assert call_json["filter"]["property"] == "Status"
        assert call_json["sorts"][0]["direction"] == "descending"

    @pytest.mark.asyncio
    async def test_get_all_database_entries(self):
        """Test get_all_database_entries with pagination."""
        client = NotionClient("test-api-key")

        # First response
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "results": [{"id": "entry1"}, {"id": "entry2"}],
            "has_more": True,
            "next_cursor": "cursor456",
        }
        mock_response1.raise_for_status = Mock()

        # Second response
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "results": [{"id": "entry3"}],
            "has_more": False,
        }
        mock_response2.raise_for_status = Mock()

        mock_request = AsyncMock(side_effect=[mock_response1, mock_response2])
        with patch.object(client.client, "request", mock_request):
            entries = await client.get_all_database_entries("db123")

        assert len(entries) == 3
        assert entries[0]["id"] == "entry1"
        assert entries[2]["id"] == "entry3"

    @pytest.mark.asyncio
    async def test_get_database(self):
        """Test get_database method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "db123",
            "title": [{"plain_text": "Test Database"}],
            "properties": {
                "Name": {"id": "title", "type": "title"},
                "Status": {"id": "status", "type": "select"},
            },
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            database = await client.get_database("db123")

        assert database["id"] == "db123"
        assert database["properties"]["Name"]["type"] == "title"
        mock_request.assert_called_with(
            method="GET",
            url="https://api.notion.com/v1/databases/db123",
            json=None,
            params=None,
        )

    @pytest.mark.asyncio
    async def test_get_page(self):
        """Test get_page method."""
        client = NotionClient("test-api-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "page123",
            "properties": {
                "title": {
                    "title": [{"plain_text": "Test Page"}],
                },
            },
        }
        mock_response.raise_for_status = Mock()

        mock_request = AsyncMock(return_value=mock_response)
        with patch.object(client.client, "request", mock_request):
            page = await client.get_page("page123")

        assert page["id"] == "page123"
        assert page["properties"]["title"]["title"][0]["plain_text"] == "Test Page"
        mock_request.assert_called_with(
            method="GET",
            url="https://api.notion.com/v1/pages/page123",
            json=None,
            params=None,
        )
