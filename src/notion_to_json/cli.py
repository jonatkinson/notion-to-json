"""Command-line interface for notion-to-json."""

import asyncio
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from notion_to_json import __version__
from notion_to_json.client import NotionClient

console = Console()


async def test_connection(api_key: str) -> bool:
    """Test connection to Notion API.

    Args:
        api_key: Notion API integration token

    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with NotionClient(api_key) as client:
            console.print("[cyan]Testing connection to Notion API...[/cyan]")
            result = await client.get_users()

            if "results" in result:
                user_count = len(result["results"])
                console.print(f"[green]✓ Successfully connected! Found {user_count} users.[/green]")

                # Display first user info if available
                if user_count > 0:
                    first_user = result["results"][0]
                    user_type = first_user.get("type", "unknown")
                    user_name = first_user.get("name", "Unknown")
                    console.print(f"[dim]First user: {user_name} (type: {user_type})[/dim]")

                return True
            else:
                console.print("[red]✗ Unexpected response format from API[/red]")
                return False

    except Exception as e:
        console.print(f"[red]✗ Connection failed: {str(e)}[/red]")
        return False


async def search_workspace(api_key: str) -> None:
    """Search and display all pages and databases in the workspace."""
    async with NotionClient(api_key) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Search for pages
            pages_task = progress.add_task("[cyan]Searching for pages...", total=None)
            pages = await client.search_pages()
            progress.remove_task(pages_task)

            # Search for databases
            db_task = progress.add_task("[cyan]Searching for databases...", total=None)
            databases = await client.search_databases()
            progress.remove_task(db_task)

        # Display results in a table
        console.print(f"\n[bold]Found {len(pages)} pages and {len(databases)} databases[/bold]\n")

        # Pages table
        if pages:
            pages_table = Table(title="Pages", show_lines=True)
            pages_table.add_column("Title", style="cyan", no_wrap=False)
            pages_table.add_column("ID", style="dim")
            pages_table.add_column("Last Edited", style="dim")

            for page in pages[:10]:  # Show first 10
                title = extract_title(page)
                page_id = page.get("id", "")
                last_edited = page.get("last_edited_time", "")[:10]  # Date only
                pages_table.add_row(title, page_id[:8] + "...", last_edited)

            if len(pages) > 10:
                pages_table.add_row(
                    f"[dim]... and {len(pages) - 10} more pages[/dim]",
                    "[dim]...[/dim]",
                    "[dim]...[/dim]",
                )

            console.print(pages_table)

        # Databases table
        if databases:
            console.print()  # Add spacing
            db_table = Table(title="Databases", show_lines=True)
            db_table.add_column("Title", style="green", no_wrap=False)
            db_table.add_column("ID", style="dim")
            db_table.add_column("Last Edited", style="dim")

            for db in databases:
                title = extract_database_title(db)
                db_id = db.get("id", "")
                last_edited = db.get("last_edited_time", "")[:10]  # Date only
                db_table.add_row(title, db_id[:8] + "...", last_edited)

            console.print(db_table)


def extract_title(page: dict) -> str:
    """Extract title from a page object."""
    if "properties" in page:
        # Look for title property
        for _prop_name, prop_value in page["properties"].items():
            if prop_value.get("type") == "title":
                title_array = prop_value.get("title", [])
                if title_array and "plain_text" in title_array[0]:
                    return title_array[0]["plain_text"]
    return "Untitled"


def extract_database_title(database: dict) -> str:
    """Extract title from a database object."""
    title_array = database.get("title", [])
    if title_array and "plain_text" in title_array[0]:
        return title_array[0]["plain_text"]
    return "Untitled"


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
@click.option(
    "--test",
    is_flag=True,
    help="Test API connection only",
)
@click.option(
    "--search",
    is_flag=True,
    help="Search and list all pages and databases",
)
def main(api_key: str, output_dir: str, test: bool, search: bool) -> None:
    """Export Notion pages and databases to JSON."""
    console.print(
        Panel(
            f"[bold green]Notion to JSON Exporter v{__version__}[/bold green]",
            expand=False,
        )
    )

    # Run async code
    if test:
        # Test mode - just verify connection
        success = asyncio.run(test_connection(api_key))
        sys.exit(0 if success else 1)
    elif search:
        # Search mode - discover all content
        asyncio.run(search_workspace(api_key))
    else:
        console.print(f"Output directory: {output_dir}")

        # Test connection first
        success = asyncio.run(test_connection(api_key))
        if not success:
            console.print("[red]Please check your API key and try again.[/red]")
            sys.exit(1)

        console.print("\n[yellow]Full export functionality will be implemented in Phase 4+[/yellow]")


if __name__ == "__main__":
    main()
