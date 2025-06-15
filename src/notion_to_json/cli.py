"""Command-line interface for notion-to-json."""

import click
from rich.console import Console

from notion_to_json import __version__

console = Console()


@click.command()
@click.version_option(version=__version__)
@click.option(
    "--api-key",
    envvar="NOTION_API_KEY",
    help="Notion API integration token",
    required=True,
)
@click.option(
    "--output-dir",
    default="./exports",
    help="Directory to save exported JSON files",
    type=click.Path(),
)
def main(api_key: str, output_dir: str) -> None:
    """Export Notion pages and databases to JSON."""
    console.print(f"[bold green]Notion to JSON Exporter v{__version__}[/bold green]")
    console.print(f"Output directory: {output_dir}")

    # Placeholder for Phase 2
    console.print("[yellow]Note: API functionality will be implemented in Phase 2[/yellow]")


if __name__ == "__main__":
    main()
