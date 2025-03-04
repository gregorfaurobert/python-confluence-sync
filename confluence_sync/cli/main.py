"""
Main command-line interface for Confluence Sync.

This module provides the main CLI entry point for the application.
"""

import click
from rich.console import Console
from rich.panel import Panel

from confluence_sync.cli.config_cli import config_cli
from confluence_sync.sync import pull_space, push_space, sync_space, sync_all_spaces

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Confluence Sync - Bidirectional synchronization between Confluence and local files.
    
    This tool allows you to sync Confluence spaces with local directories,
    converting Confluence pages to/from Markdown files.
    """
    pass


# Add subcommands
cli.add_command(config_cli)


@cli.command(name="pull")
@click.option("--space", help="Confluence space key to pull from")
@click.option("--all", "all_spaces", is_flag=True, help="Pull from all configured spaces")
@click.option("--force", is_flag=True, help="Force pull even if local changes would be overwritten")
def pull_command(space, all_spaces, force):
    """
    Pull content from Confluence to local directory.
    
    This command downloads pages from the specified Confluence space
    and converts them to Markdown files in the configured local directory.
    """
    if not space and not all_spaces:
        console.print("[red]Error: Either --space or --all must be specified.[/red]")
        return
    
    if space and all_spaces:
        console.print("[red]Error: Cannot specify both --space and --all.[/red]")
        return
    
    if all_spaces:
        # Pull from all spaces
        console.print("[bold]Pulling content from all configured spaces...[/bold]")
        success = sync_all_spaces(force=force, direction="pull")
    else:
        # Pull from specified space
        console.print(f"[bold]Pulling content from Confluence space '{space}'...[/bold]")
        success = pull_space(space, force=force)
    
    if success:
        console.print("[green]Pull completed successfully.[/green]")
    else:
        console.print("[red]Pull failed. See logs for details.[/red]")


@cli.command(name="push")
@click.option("--space", help="Confluence space key to push to")
@click.option("--all", "all_spaces", is_flag=True, help="Push to all configured spaces")
@click.option("--force", is_flag=True, help="Force push even if remote changes would be overwritten")
def push_command(space, all_spaces, force):
    """
    Push content from local directory to Confluence.
    
    This command uploads Markdown files from the configured local directory
    and converts them to pages in the specified Confluence space.
    """
    if not space and not all_spaces:
        console.print("[red]Error: Either --space or --all must be specified.[/red]")
        return
    
    if space and all_spaces:
        console.print("[red]Error: Cannot specify both --space and --all.[/red]")
        return
    
    if all_spaces:
        # Push to all spaces
        console.print("[bold]Pushing content to all configured spaces...[/bold]")
        success = sync_all_spaces(force=force, direction="push")
    else:
        # Push to specified space
        console.print(f"[bold]Pushing content to Confluence space '{space}'...[/bold]")
        success = push_space(space, force=force)
    
    if success:
        console.print("[green]Push completed successfully.[/green]")
    else:
        console.print("[red]Push failed. See logs for details.[/red]")


@cli.command(name="sync")
@click.option("--space", help="Confluence space key to sync with")
@click.option("--all", "all_spaces", is_flag=True, help="Sync all configured spaces")
@click.option("--force", is_flag=True, help="Force sync even if changes would be overwritten")
@click.option("--direction", type=click.Choice(["pull", "push", "both"]), help="Sync direction (default: interactive)")
def sync_command(space, all_spaces, force, direction):
    """
    Bidirectional sync between Confluence and local directory.
    
    This command synchronizes content between the specified Confluence space
    and the configured local directory, handling conflicts as needed.
    """
    if not space and not all_spaces:
        console.print("[red]Error: Either --space or --all must be specified.[/red]")
        return
    
    if space and all_spaces:
        console.print("[red]Error: Cannot specify both --space and --all.[/red]")
        return
    
    if all_spaces:
        # Sync all spaces
        console.print("[bold]Syncing all configured spaces...[/bold]")
        success = sync_all_spaces(force=force, direction=direction)
    else:
        # Sync specified space
        console.print(f"[bold]Syncing Confluence space '{space}'...[/bold]")
        success = sync_space(space, force=force, direction=direction)
    
    if success:
        console.print("[green]Sync completed successfully.[/green]")
    else:
        console.print("[red]Sync failed. See logs for details.[/red]")


if __name__ == "__main__":
    cli() 