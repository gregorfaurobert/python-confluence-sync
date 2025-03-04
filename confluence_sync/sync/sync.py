"""
Sync module for Confluence Sync.

This module combines pull and push functionality to synchronize content between Confluence and local files.
"""

import os
import logging
from rich.console import Console
from rich.prompt import Confirm

from confluence_sync.sync.pull import pull_space
from confluence_sync.sync.push import push_space
from confluence_sync.config.spaces import SpaceConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()


def sync_space(space_key, password=None, force=False, direction=None):
    """
    Synchronize content between Confluence and local files.

    Args:
        space_key (str): The key of the Confluence space to sync.
        password (str, optional): Not used, kept for backward compatibility.
        force (bool, optional): Whether to force overwrite files/pages.
        direction (str, optional): Direction of sync ('pull', 'push', or None for both).

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Validate space key
        space_config = SpaceConfigManager().get_space_config(space_key)
        if not space_config:
            logger.error(f"Space '{space_key}' not found in configuration.")
            console.print(f"[red]Space '{space_key}' not found in configuration.[/red]")
            return False
        
        # Determine sync direction
        if direction is None:
            # Interactive mode - ask user for direction
            console.print(f"[bold]Syncing space '{space_key}'[/bold]")
            console.print("Choose sync direction:")
            console.print("1. Pull (Confluence → Local)")
            console.print("2. Push (Local → Confluence)")
            console.print("3. Both (Two-way sync)")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == "1":
                direction = "pull"
            elif choice == "2":
                direction = "push"
            elif choice == "3":
                direction = "both"
            else:
                console.print("[red]Invalid choice. Aborting sync.[/red]")
                return False
        
        # Perform sync based on direction
        if direction == "pull" or direction == "both":
            console.print(f"[bold]Pulling content from Confluence space '{space_key}'...[/bold]")
            pull_success = pull_space(space_key, force=force)
            
            if not pull_success:
                console.print(f"[red]Failed to pull content from '{space_key}'.[/red]")
                if direction == "both":
                    # Ask if user wants to continue with push
                    continue_push = Confirm.ask("Pull failed. Do you want to continue with push?")
                    if not continue_push:
                        return False
                else:
                    return False
        
        if direction == "push" or direction == "both":
            console.print(f"[bold]Pushing content to Confluence space '{space_key}'...[/bold]")
            push_success = push_space(space_key, force=force)
            
            if not push_success:
                console.print(f"[red]Failed to push content to '{space_key}'.[/red]")
                return False
        
        console.print(f"[green]Successfully synchronized space '{space_key}'.[/green]")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing space '{space_key}': {str(e)}")
        console.print(f"[red]Error syncing space '{space_key}': {str(e)}[/red]")
        return False


def sync_all_spaces(password=None, force=False, direction=None):
    """
    Synchronize all configured spaces.

    Args:
        password (str, optional): Not used, kept for backward compatibility.
        force (bool, optional): Whether to force overwrite files/pages.
        direction (str, optional): Direction of sync ('pull', 'push', or None for both).

    Returns:
        bool: True if all spaces synced successfully, False otherwise.
    """
    try:
        # Get all configured spaces
        spaces = SpaceConfigManager().get_all_spaces()
        if not spaces:
            logger.warning("No spaces configured.")
            console.print("[yellow]No spaces configured. Use 'confluence-sync spaces add' to add a space.[/yellow]")
            return False
        
        # Determine sync direction if not specified
        if direction is None:
            console.print("[bold]Syncing all configured spaces[/bold]")
            console.print("Choose sync direction:")
            console.print("1. Pull (Confluence → Local)")
            console.print("2. Push (Local → Confluence)")
            console.print("3. Both (Two-way sync)")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == "1":
                direction = "pull"
            elif choice == "2":
                direction = "push"
            elif choice == "3":
                direction = "both"
            else:
                console.print("[red]Invalid choice. Aborting sync.[/red]")
                return False
        
        # Sync each space
        success = True
        for space_key in spaces:
            console.print(f"[bold]Syncing space '{space_key}'...[/bold]")
            space_success = sync_space(space_key, force=force, direction=direction)
            
            if not space_success:
                console.print(f"[red]Failed to sync space '{space_key}'.[/red]")
                success = False
                
                # Ask if user wants to continue with other spaces
                continue_sync = Confirm.ask(f"Sync failed for '{space_key}'. Continue with other spaces?")
                if not continue_sync:
                    break
        
        if success:
            console.print("[green]Successfully synchronized all spaces.[/green]")
        else:
            console.print("[yellow]Sync completed with some errors.[/yellow]")
        
        return success
        
    except Exception as e:
        logger.error(f"Error syncing all spaces: {str(e)}")
        console.print(f"[red]Error syncing all spaces: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    # Test the module
    import sys
    if len(sys.argv) > 1:
        space_key = sys.argv[1]
        sync_space(space_key)
    else:
        sync_all_spaces() 