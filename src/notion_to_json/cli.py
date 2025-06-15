"""Command-line interface for notion-to-json."""

import asyncio
import sys

import click
from rich.console import Console
from rich.panel import Panel

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
def main(api_key: str, output_dir: str, test: bool) -> None:
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
    else:
        console.print(f"Output directory: {output_dir}")

        # Test connection first
        success = asyncio.run(test_connection(api_key))
        if not success:
            console.print("[red]Please check your API key and try again.[/red]")
            sys.exit(1)

        console.print("\n[yellow]Full export functionality will be implemented in Phase 3+[/yellow]")


if __name__ == "__main__":
    main()
