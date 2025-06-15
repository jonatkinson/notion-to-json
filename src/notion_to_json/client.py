"""Notion API client implementation."""

from typing import Any


class NotionClient:
    """Client for interacting with the Notion API."""

    def __init__(self, api_key: str) -> None:
        """Initialize the Notion client.

        Args:
            api_key: Notion integration token
        """
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> dict:
        """Make an API request to Notion.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response data as dictionary
        """
        # To be implemented in Phase 2
        raise NotImplementedError("API functionality will be implemented in Phase 2")
