"""Notion API client implementation."""

import asyncio
import time
from typing import Any

import httpx

from notion_to_json.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for Notion API (3 requests per second)."""

    def __init__(self, requests_per_second: float = 3.0) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait if necessary to respect rate limit."""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)
            self.last_request_time = time.time()


class NotionClient:
    """Client for interacting with the Notion API."""

    def __init__(self, api_key: str) -> None:
        """Initialize the Notion client.

        Args:
            api_key: Notion integration token
        """
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.rate_limiter = RateLimiter()

        # Configure httpx client with timeout and retries
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=self._get_headers(),
            follow_redirects=True,
        )
        logger.debug(f"Initialized NotionClient with base URL: {self.base_url}")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Notion API requests.

        Returns:
            Dictionary of headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
        retry_count: int = 3,
    ) -> dict:
        """Make an API request to Notion with rate limiting and retries.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            json: JSON body for request
            params: Query parameters
            retry_count: Number of retries for failed requests

        Returns:
            Response data as dictionary

        Raises:
            httpx.HTTPStatusError: For non-recoverable HTTP errors
            httpx.RequestError: For network errors
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None

        logger.debug(f"Making {method} request to {endpoint}")

        for attempt in range(retry_count + 1):
            try:
                # Respect rate limit
                await self.rate_limiter.acquire()

                # Make request
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                )

                # Handle rate limit errors
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    continue

                # Raise for other HTTP errors
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx) except rate limits
                if e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                last_error = e

            except httpx.RequestError as e:
                # Network errors - retry
                last_error = e

            # Exponential backoff for retries
            if attempt < retry_count:
                wait_time = 2 ** attempt
                logger.warning(f"Request failed. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        # All retries exhausted
        raise last_error or Exception("Request failed after all retries")

    async def get_users(self) -> dict:
        """Get list of users in the workspace.

        Returns:
            Dictionary with users data
        """
        return await self.request("GET", "/users")

    async def search(
        self,
        filter_type: str | None = None,
        query: str | None = None,
        start_cursor: str | None = None,
        page_size: int = 100,
    ) -> dict:
        """Search for objects in Notion.

        Args:
            filter_type: Type of object to filter ("page" or "database")
            query: Text query to search for
            start_cursor: Pagination cursor
            page_size: Number of results per page (max 100)

        Returns:
            Dictionary with search results
        """
        payload: dict[str, Any] = {
            "page_size": min(page_size, 100),  # API max is 100
        }

        if filter_type:
            payload["filter"] = {
                "property": "object",
                "value": filter_type,
            }

        if query:
            payload["query"] = query

        if start_cursor:
            payload["start_cursor"] = start_cursor

        return await self.request("POST", "/search", json=payload)

    async def search_all(
        self,
        filter_type: str | None = None,
        query: str | None = None,
    ) -> list[dict]:
        """Search for all objects, handling pagination automatically.

        Args:
            filter_type: Type of object to filter ("page" or "database")
            query: Text query to search for

        Returns:
            List of all results
        """
        all_results = []
        has_more = True
        start_cursor = None

        while has_more:
            response = await self.search(
                filter_type=filter_type,
                query=query,
                start_cursor=start_cursor,
            )

            results = response.get("results", [])
            all_results.extend(results)

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return all_results

    async def search_pages(self, query: str | None = None) -> list[dict]:
        """Search for all pages in the workspace.

        Args:
            query: Optional text query to search for

        Returns:
            List of all pages
        """
        return await self.search_all(filter_type="page", query=query)

    async def search_databases(self, query: str | None = None) -> list[dict]:
        """Search for all databases in the workspace.

        Args:
            query: Optional text query to search for

        Returns:
            List of all databases
        """
        return await self.search_all(filter_type="database", query=query)

    async def get_page_blocks(
        self,
        page_id: str,
        start_cursor: str | None = None,
        page_size: int = 100,
    ) -> dict:
        """Get blocks (content) from a page.

        Args:
            page_id: ID of the page
            start_cursor: Pagination cursor
            page_size: Number of results per page (max 100)

        Returns:
            Dictionary with block data
        """
        params = {"page_size": min(page_size, 100)}
        if start_cursor:
            params["start_cursor"] = start_cursor

        return await self.request("GET", f"/blocks/{page_id}/children", params=params)

    async def get_all_page_blocks(self, page_id: str) -> list[dict]:
        """Get all blocks from a page, handling pagination.

        Args:
            page_id: ID of the page

        Returns:
            List of all blocks in the page
        """
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            response = await self.get_page_blocks(page_id, start_cursor=start_cursor)
            blocks = response.get("results", [])
            all_blocks.extend(blocks)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return all_blocks

    async def get_page_content_recursive(self, page_id: str) -> dict:
        """Get page content including nested blocks recursively.

        Args:
            page_id: ID of the page

        Returns:
            Dictionary with page content and all nested blocks
        """
        # Get top-level blocks
        blocks = await self.get_all_page_blocks(page_id)

        # Recursively get children for blocks that can have children
        for block in blocks:
            if block.get("has_children", False):
                block_id = block.get("id")
                if block_id:
                    # Recursively get children
                    block["children"] = await self.get_all_page_blocks(block_id)
                    # Continue recursion for nested blocks
                    for child_block in block["children"]:
                        if child_block.get("has_children", False):
                            child_id = child_block.get("id")
                            if child_id:
                                child_block["children"] = await self.get_page_content_recursive(child_id)

        return {"blocks": blocks}

    async def query_database(
        self,
        database_id: str,
        start_cursor: str | None = None,
        page_size: int = 100,
        filter_obj: dict | None = None,
        sorts: list[dict] | None = None,
    ) -> dict:
        """Query a database for its entries.

        Args:
            database_id: ID of the database
            start_cursor: Pagination cursor
            page_size: Number of results per page (max 100)
            filter_obj: Filter conditions
            sorts: Sort conditions

        Returns:
            Dictionary with database entries
        """
        payload: dict[str, Any] = {"page_size": min(page_size, 100)}

        if start_cursor:
            payload["start_cursor"] = start_cursor
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts

        return await self.request("POST", f"/databases/{database_id}/query", json=payload)

    async def get_all_database_entries(
        self,
        database_id: str,
        filter_obj: dict | None = None,
        sorts: list[dict] | None = None,
    ) -> list[dict]:
        """Get all entries from a database, handling pagination.

        Args:
            database_id: ID of the database
            filter_obj: Filter conditions
            sorts: Sort conditions

        Returns:
            List of all database entries
        """
        all_entries = []
        has_more = True
        start_cursor = None

        while has_more:
            response = await self.query_database(
                database_id,
                start_cursor=start_cursor,
                filter_obj=filter_obj,
                sorts=sorts,
            )
            entries = response.get("results", [])
            all_entries.extend(entries)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return all_entries

    async def get_database(self, database_id: str) -> dict:
        """Get database schema and properties.

        Args:
            database_id: ID of the database

        Returns:
            Dictionary with database metadata
        """
        return await self.request("GET", f"/databases/{database_id}")

    async def get_page(self, page_id: str) -> dict:
        """Get page metadata and properties.

        Args:
            page_id: ID of the page

        Returns:
            Dictionary with page metadata
        """
        return await self.request("GET", f"/pages/{page_id}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "NotionClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
