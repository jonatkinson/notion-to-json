"""Tests for the JSON exporter."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from notion_to_json.exporter import JSONExporter


class TestJSONExporter:
    """Test cases for JSONExporter."""

    def test_exporter_initialization(self, tmp_path):
        """Test that exporter initializes with output directory."""
        exporter = JSONExporter(tmp_path)

        assert exporter.output_dir == tmp_path
        assert isinstance(exporter.output_dir, Path)
        assert tmp_path.exists()
        assert exporter.export_id
        assert exporter.export_timestamp
        assert exporter.statistics["pages_exported"] == 0
        assert exporter.statistics["databases_exported"] == 0

    def test_sanitize_filename(self, tmp_path):
        """Test filename sanitization."""
        exporter = JSONExporter(tmp_path)

        # Test various invalid characters
        assert exporter._sanitize_filename("test/file:name") == "test_file_name"
        assert exporter._sanitize_filename("test<>file") == "test__file"
        assert exporter._sanitize_filename("test|file?") == "test_file_"
        assert exporter._sanitize_filename("test file...") == "test file"
        assert exporter._sanitize_filename("") == "untitled"

        # Test length limit
        long_name = "a" * 150
        assert len(exporter._sanitize_filename(long_name)) == 100

    def test_extract_title(self, tmp_path):
        """Test title extraction from objects."""
        exporter = JSONExporter(tmp_path)

        # Test database title
        database = {"title": [{"plain_text": "My Database"}]}
        assert exporter._extract_title(database) == "My Database"

        # Test page title
        page = {"properties": {"title": {"type": "title", "title": [{"plain_text": "My Page"}]}}}
        assert exporter._extract_title(page) == "My Page"

        # Test empty object
        assert exporter._extract_title({}) == "Untitled"

    def test_save_page(self, tmp_path):
        """Test saving a page to JSON file."""
        exporter = JSONExporter(tmp_path)

        page_metadata = {
            "id": "123456789",
            "properties": {"title": {"type": "title", "title": [{"plain_text": "Test Page"}]}},
        }

        page_content = {"blocks": [{"id": "block1", "type": "paragraph"}, {"id": "block2", "type": "heading_1"}]}

        filepath = exporter.save_page(page_metadata, page_content)

        # Check file was created
        assert filepath.exists()
        assert filepath.parent == tmp_path / "pages"
        assert "Test Page" in filepath.name
        assert "12345678" in filepath.name

        # Check statistics were updated
        assert exporter.statistics["pages_exported"] == 1
        assert exporter.statistics["blocks_exported"] == 2

        # Check file content
        with open(filepath) as f:
            data = json.load(f)

        assert data["export_info"]["type"] == "page"
        assert data["export_info"]["export_id"] == exporter.export_id
        assert data["metadata"] == page_metadata
        assert data["content"] == page_content

    def test_save_database(self, tmp_path):
        """Test saving a database to JSON file."""
        exporter = JSONExporter(tmp_path)

        database_schema = {"id": "db123456", "title": [{"plain_text": "Test Database"}], "properties": {}}

        database_entries = [{"id": "entry1"}, {"id": "entry2"}, {"id": "entry3"}]

        filepath = exporter.save_database(database_schema, database_entries)

        # Check file was created
        assert filepath.exists()
        assert filepath.parent == tmp_path / "databases"
        assert "Test Database" in filepath.name
        assert "db123456" in filepath.name

        # Check statistics were updated
        assert exporter.statistics["databases_exported"] == 1
        assert exporter.statistics["database_entries_exported"] == 3

        # Check file content
        with open(filepath) as f:
            data = json.load(f)

        assert data["export_info"]["type"] == "database"
        assert data["schema"] == database_schema
        assert data["entries"] == database_entries
        assert data["entry_count"] == 3

    def test_save_manifest(self, tmp_path):
        """Test saving export manifest."""
        exporter = JSONExporter(tmp_path)

        pages = [
            {
                "id": "page1",
                "url": "https://notion.so/page1",
                "last_edited_time": "2024-01-01",
                "properties": {"title": {"type": "title", "title": [{"plain_text": "Page 1"}]}},
            }
        ]

        databases = [
            {
                "id": "db1",
                "url": "https://notion.so/db1",
                "last_edited_time": "2024-01-02",
                "title": [{"plain_text": "Database 1"}],
            }
        ]

        # Add some statistics
        exporter.statistics["pages_exported"] = 1
        exporter.statistics["databases_exported"] = 1

        filepath = exporter.save_manifest(pages, databases)

        assert filepath == tmp_path / "manifest.json"
        assert filepath.exists()

        # Check manifest content
        with open(filepath) as f:
            manifest = json.load(f)

        assert manifest["export_id"] == exporter.export_id
        assert manifest["statistics"] == exporter.statistics
        assert len(manifest["content_summary"]["pages"]) == 1
        assert len(manifest["content_summary"]["databases"]) == 1
        assert manifest["content_summary"]["pages"][0]["title"] == "Page 1"

    @pytest.mark.asyncio
    async def test_export_workspace(self, tmp_path):
        """Test exporting workspace with mocked client."""
        exporter = JSONExporter(tmp_path)

        # Mock client
        mock_client = AsyncMock()

        # Mock page data
        mock_client.get_page.return_value = {
            "id": "page123",
            "properties": {"title": {"type": "title", "title": [{"plain_text": "Test Page"}]}},
        }

        mock_client.get_page_content_recursive.return_value = {"blocks": [{"id": "block1"}]}

        # Mock database data
        mock_client.get_database.return_value = {"id": "db456", "title": [{"plain_text": "Test DB"}]}

        mock_client.get_all_database_entries.return_value = [{"id": "entry1"}, {"id": "entry2"}]

        # Pages and databases to export
        pages = [{"id": "page123"}]
        databases = [{"id": "db456"}]

        # Export
        result = await exporter.export_workspace(mock_client, pages, databases)

        # Check result
        assert result["export_id"] == exporter.export_id
        assert result["output_dir"] == str(tmp_path)
        assert result["statistics"]["pages_exported"] == 1
        assert result["statistics"]["databases_exported"] == 1
        assert result["statistics"]["blocks_exported"] == 1
        assert result["statistics"]["database_entries_exported"] == 2

        # Check files were created
        assert (tmp_path / "pages").exists()
        assert (tmp_path / "databases").exists()
        assert (tmp_path / "manifest.json").exists()

        # Verify API calls
        mock_client.get_page.assert_called_once_with("page123")
        mock_client.get_page_content_recursive.assert_called_once_with("page123")
        mock_client.get_database.assert_called_once_with("db456")
        mock_client.get_all_database_entries.assert_called_once_with("db456")
