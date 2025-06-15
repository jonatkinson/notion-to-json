"""Tests for the Notion API client."""

import pytest

from notion_to_json.client import NotionClient


class TestNotionClient:
    """Test cases for NotionClient."""

    def test_client_initialization(self):
        """Test that client initializes with API key."""
        api_key = "test-api-key"
        client = NotionClient(api_key)

        assert client.api_key == api_key
        assert client.base_url == "https://api.notion.com/v1"

    @pytest.mark.asyncio
    async def test_request_not_implemented(self):
        """Test that request method raises NotImplementedError."""
        client = NotionClient("test-api-key")

        with pytest.raises(NotImplementedError):
            await client.request("GET", "/users")
