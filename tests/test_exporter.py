"""Tests for the JSON exporter."""

from pathlib import Path

import pytest

from notion_to_json.exporter import JSONExporter


class TestJSONExporter:
    """Test cases for JSONExporter."""

    def test_exporter_initialization(self, tmp_path):
        """Test that exporter initializes with output directory."""
        exporter = JSONExporter(tmp_path)

        assert exporter.output_dir == tmp_path
        assert isinstance(exporter.output_dir, Path)

    def test_export_workspace_not_implemented(self, tmp_path):
        """Test that export_workspace raises NotImplementedError."""
        exporter = JSONExporter(tmp_path)

        with pytest.raises(NotImplementedError):
            exporter.export_workspace([], [])
