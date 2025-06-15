"""Data models for Notion objects."""

from dataclasses import dataclass
from typing import Any


@dataclass
class NotionObject:
    """Base class for Notion objects."""

    id: str
    type: str  # "page" or "database"
    properties: dict[str, Any]
    created_time: str
    last_edited_time: str


@dataclass
class Page(NotionObject):
    """Represents a Notion page."""

    content: list[dict[str, Any]]  # blocks
    parent: dict[str, Any]


@dataclass
class Database(NotionObject):
    """Represents a Notion database."""

    schema: dict[str, Any]
    entries: list[dict[str, Any]]
