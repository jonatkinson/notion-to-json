"""Notion API client implementation."""

import asyncio
import time
from typing import Any

import httpx
from rich.console import Console

console = Console()


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
                    console.print(f"[yellow]Rate limited. Waiting {retry_after} seconds...[/yellow]")
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
                console.print(f"[yellow]Request failed. Retrying in {wait_time} seconds...[/yellow]")
                await asyncio.sleep(wait_time)

        # All retries exhausted
        raise last_error or Exception("Request failed after all retries")

    async def get_users(self) -> dict:
        """Get list of users in the workspace.

        Returns:
            Dictionary with users data
        """
        return await self.request("GET", "/users")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "NotionClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
