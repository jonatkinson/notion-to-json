"""Export functionality for Notion data."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn

from notion_to_json.logging import console, get_logger

logger = get_logger(__name__)


class JSONExporter:
    """Handles exporting Notion data to JSON format."""

    def __init__(self, output_dir: str | Path) -> None:
        """Initialize the exporter.

        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.export_id = str(uuid.uuid4())
        self.export_timestamp = datetime.now().isoformat()
        self.statistics = {
            "pages_exported": 0,
            "databases_exported": 0,
            "blocks_exported": 0,
            "database_entries_exported": 0,
            "errors": [],
        }
        logger.info(f"Initialized exporter with output directory: {self.output_dir}")
        logger.debug(f"Export ID: {self.export_id}")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a filename to be filesystem-safe.

        Args:
            name: The filename to sanitize

        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        # Limit length
        name = name[:100]
        # Remove trailing dots and spaces
        name = name.rstrip(". ")
        return name or "untitled"

    def _extract_title(self, obj: dict) -> str:
        """Extract title from a page or database object.

        Args:
            obj: Page or database object

        Returns:
            Title string
        """
        # For databases
        if "title" in obj and isinstance(obj["title"], list):
            for item in obj["title"]:
                if "plain_text" in item:
                    return item["plain_text"]

        # For pages
        if "properties" in obj:
            for _prop_name, prop_value in obj["properties"].items():
                if prop_value.get("type") == "title":
                    title_array = prop_value.get("title", [])
                    if title_array and "plain_text" in title_array[0]:
                        return title_array[0]["plain_text"]

        return "Untitled"

    def save_page(self, page_metadata: dict, page_content: dict) -> Path:
        """Save a single page to JSON file.

        Args:
            page_metadata: Page metadata from API
            page_content: Page content (blocks)

        Returns:
            Path to saved file
        """
        page_id = page_metadata.get("id", "unknown")
        title = self._extract_title(page_metadata)
        filename = f"{self._sanitize_filename(title)}_{page_id[:8]}.json"

        # Create pages subdirectory
        pages_dir = self.output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)

        # Combine metadata and content
        full_page = {
            "export_info": {
                "export_id": self.export_id,
                "exported_at": datetime.now().isoformat(),
                "type": "page",
            },
            "metadata": page_metadata,
            "content": page_content,
        }

        # Write to file
        filepath = pages_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_page, f, indent=2, ensure_ascii=False)

        self.statistics["pages_exported"] += 1
        if "blocks" in page_content:
            self.statistics["blocks_exported"] += len(page_content["blocks"])

        logger.debug(f"Saved page '{title}' to {filepath}")
        return filepath

    def save_database(self, database_schema: dict, database_entries: list[dict]) -> Path:
        """Save a single database to JSON file.

        Args:
            database_schema: Database schema/properties
            database_entries: List of database entries

        Returns:
            Path to saved file
        """
        db_id = database_schema.get("id", "unknown")
        title = self._extract_title(database_schema)
        filename = f"{self._sanitize_filename(title)}_{db_id[:8]}.json"

        # Create databases subdirectory
        databases_dir = self.output_dir / "databases"
        databases_dir.mkdir(exist_ok=True)

        # Combine schema and entries
        full_database = {
            "export_info": {
                "export_id": self.export_id,
                "exported_at": datetime.now().isoformat(),
                "type": "database",
            },
            "schema": database_schema,
            "entries": database_entries,
            "entry_count": len(database_entries),
        }

        # Write to file
        filepath = databases_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_database, f, indent=2, ensure_ascii=False)

        self.statistics["databases_exported"] += 1
        self.statistics["database_entries_exported"] += len(database_entries)

        return filepath

    def save_manifest(self, pages: list[dict], databases: list[dict]) -> Path:
        """Save export manifest with metadata.

        Args:
            pages: List of exported pages
            databases: List of exported databases

        Returns:
            Path to manifest file
        """
        manifest = {
            "export_id": self.export_id,
            "export_timestamp": self.export_timestamp,
            "completed_at": datetime.now().isoformat(),
            "statistics": self.statistics,
            "content_summary": {
                "pages": [
                    {
                        "id": page.get("id"),
                        "title": self._extract_title(page),
                        "url": page.get("url", ""),
                        "last_edited": page.get("last_edited_time", ""),
                    }
                    for page in pages
                ],
                "databases": [
                    {
                        "id": db.get("id"),
                        "title": self._extract_title(db),
                        "url": db.get("url", ""),
                        "last_edited": db.get("last_edited_time", ""),
                    }
                    for db in databases
                ],
            },
        }

        filepath = self.output_dir / "manifest.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return filepath

    async def export_workspace(
        self,
        client: Any,
        pages: list[dict],
        databases: list[dict],
        progress_callback: Any = None,
    ) -> dict:
        """Export entire workspace to JSON files.

        Args:
            client: NotionClient instance
            pages: List of page objects to export
            databases: List of database objects to export
            progress_callback: Optional callback for progress updates

        Returns:
            Export summary with statistics
        """
        console.print(f"\n[bold]Starting export to: {self.output_dir}[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Export pages
            if pages:
                pages_task = progress.add_task(
                    f"[cyan]Exporting {len(pages)} pages...",
                    total=len(pages),
                )

                for _i, page in enumerate(pages):
                    try:
                        page_id = page.get("id")
                        title = self._extract_title(page)
                        progress.update(
                            pages_task,
                            description=f"[cyan]Exporting page: {title[:50]}...",
                        )

                        # Get full page metadata
                        page_metadata = await client.get_page(page_id)

                        # Get page content
                        page_content = await client.get_page_content_recursive(page_id)

                        # Save to file
                        self.save_page(page_metadata, page_content)

                        progress.advance(pages_task)

                    except Exception as e:
                        error_msg = f"Error exporting page {page_id}: {str(e)}"
                        self.statistics["errors"].append(error_msg)
                        console.print(f"[red]{error_msg}[/red]")
                        progress.advance(pages_task)

                progress.remove_task(pages_task)

            # Export databases
            if databases:
                db_task = progress.add_task(
                    f"[green]Exporting {len(databases)} databases...",
                    total=len(databases),
                )

                for _i, database in enumerate(databases):
                    try:
                        db_id = database.get("id")
                        title = self._extract_title(database)
                        progress.update(
                            db_task,
                            description=f"[green]Exporting database: {title[:50]}...",
                        )

                        # Get full database schema
                        db_schema = await client.get_database(db_id)

                        # Get all database entries
                        db_entries = await client.get_all_database_entries(db_id)

                        # Save to file
                        self.save_database(db_schema, db_entries)

                        progress.advance(db_task)

                    except Exception as e:
                        error_msg = f"Error exporting database {db_id}: {str(e)}"
                        self.statistics["errors"].append(error_msg)
                        console.print(f"[red]{error_msg}[/red]")
                        progress.advance(db_task)

                progress.remove_task(db_task)

        # Save manifest
        manifest_path = self.save_manifest(pages, databases)

        # Print summary
        console.print("\n[bold green]Export completed![/bold green]")
        console.print(f"Export ID: {self.export_id}")
        console.print(f"Output directory: {self.output_dir}")
        console.print(f"Pages exported: {self.statistics['pages_exported']}")
        console.print(f"Databases exported: {self.statistics['databases_exported']}")
        console.print(f"Total blocks: {self.statistics['blocks_exported']}")
        console.print(f"Total database entries: {self.statistics['database_entries_exported']}")

        if self.statistics["errors"]:
            console.print(f"\n[yellow]Errors encountered: {len(self.statistics['errors'])}[/yellow]")
            console.print("[dim]Check manifest.json for details[/dim]")

        return {
            "export_id": self.export_id,
            "output_dir": str(self.output_dir),
            "manifest_path": str(manifest_path),
            "statistics": self.statistics,
        }
