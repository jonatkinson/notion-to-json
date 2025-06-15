"""Tests for Notion data models."""

from notion_to_json.models import Database, NotionObject, Page


class TestModels:
    """Test cases for data models."""

    def test_notion_object_creation(self):
        """Test NotionObject instantiation."""
        obj = NotionObject(
            id="test-id",
            type="page",
            properties={"title": "Test"},
            created_time="2024-01-01T00:00:00Z",
            last_edited_time="2024-01-01T00:00:00Z",
        )

        assert obj.id == "test-id"
        assert obj.type == "page"
        assert obj.properties == {"title": "Test"}

    def test_page_creation(self):
        """Test Page instantiation."""
        page = Page(
            id="page-id",
            type="page",
            properties={"title": "Test Page"},
            created_time="2024-01-01T00:00:00Z",
            last_edited_time="2024-01-01T00:00:00Z",
            content=[],
            parent={"type": "workspace"},
        )

        assert page.id == "page-id"
        assert page.content == []
        assert page.parent["type"] == "workspace"

    def test_database_creation(self):
        """Test Database instantiation."""
        database = Database(
            id="db-id",
            type="database",
            properties={"title": "Test DB"},
            created_time="2024-01-01T00:00:00Z",
            last_edited_time="2024-01-01T00:00:00Z",
            schema={},
            entries=[],
        )

        assert database.id == "db-id"
        assert database.schema == {}
        assert database.entries == []
