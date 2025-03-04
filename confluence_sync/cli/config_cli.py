"""
Command-line interface for configuration management.

This module provides CLI commands for managing Confluence Sync configuration.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from confluence_sync.config.credentials import CredentialsManager, setup_credentials_interactive
from confluence_sync.config.spaces import SpaceConfigManager, setup_space_config_interactive, list_configured_spaces

console = Console()


@click.group(name="config")
def config_cli():
    """Manage Confluence Sync configuration."""
    pass


@config_cli.command(name="credentials")
@click.option("--delete", is_flag=True, help="Delete stored credentials")
def credentials_command(delete):
    """Manage Confluence API credentials."""
    manager = CredentialsManager()
    
    if delete:
        if click.confirm("Are you sure you want to delete your stored credentials?"):
            success = manager.delete_credentials()
            if success:
                console.print(Panel("Credentials deleted successfully", title="Success", border_style="green"))
            else:
                console.print(Panel("Failed to delete credentials", title="Error", border_style="red"))
    else:
        setup_credentials_interactive()


@config_cli.command(name="spaces")
@click.option("--add", is_flag=True, help="Add a new space configuration")
@click.option("--remove", help="Remove a space configuration by space key")
@click.option("--list", "list_spaces", is_flag=True, help="List all configured spaces")
@click.option("--space-key", help="Confluence space key")
@click.option("--space-name", help="Friendly name for the space")
@click.option("--local-dir", help="Local directory to sync with")
def spaces_command(add, remove, list_spaces, space_key, space_name, local_dir):
    """Manage Confluence space configurations."""
    manager = SpaceConfigManager()
    
    if list_spaces:
        spaces = manager.get_all_spaces()
        
        if not spaces:
            console.print("No spaces configured.")
            return
        
        table = Table(title="Configured Spaces")
        table.add_column("Space Key", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Local Directory", style="yellow")
        
        for key, config in spaces.items():
            table.add_row(
                key,
                config.get("name", key),
                config.get("local_dir")
            )
        
        console.print(table)
        
    elif remove:
        if click.confirm(f"Are you sure you want to remove space '{remove}' from configuration?"):
            success = manager.remove_space(remove)
            if success:
                console.print(Panel(f"Space '{remove}' removed from configuration", title="Success", border_style="green"))
            else:
                console.print(Panel(f"Failed to remove space '{remove}'", title="Error", border_style="red"))
                
    elif add or (space_key and local_dir):
        if add and not (space_key and local_dir):
            setup_space_config_interactive()
        else:
            success = manager.add_space(space_key, local_dir, space_name)
            if success:
                console.print(Panel(f"Space '{space_key}' configured successfully", title="Success", border_style="green"))
            else:
                console.print(Panel(f"Failed to configure space '{space_key}'", title="Error", border_style="red"))
    else:
        click.echo(click.get_current_context().get_help())


if __name__ == "__main__":
    config_cli() 