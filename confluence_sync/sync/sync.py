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
from confluence_sync.converter import MD2CONF_AVAILABLE, C2M_AVAILABLE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()


def sync_space(space_key, password=None, force=False, direction=None):
    """
    Synchronize a Confluence space with local files.

    Args:
        space_key (str): The key of the Confluence space to sync.
        password (str, optional): Not used, kept for backward compatibility.
        force (bool, optional): Whether to force overwrite files/pages.
        direction (str, optional): The sync direction ('pull', 'push', or 'both').
            Defaults to 'both'.

    Returns:
        bool: True if the sync was successful, False otherwise.
    """
    # Set default direction
    if direction is None:
        direction = "both"

    # Validate direction
    if direction not in ["pull", "push", "both"]:
        logger.error(f"Invalid sync direction: {direction}")
        return False

    # Perform sync in the specified direction
    if direction in ["pull", "both"]:
        logger.info(f"Pulling content from Confluence space '{space_key}'...")
        pull_success = pull_space(space_key, force=force)
        if not pull_success:
            logger.error(f"Failed to pull content from Confluence space '{space_key}'.")
            return False

    if direction in ["push", "both"]:
        logger.info(f"Pushing content to Confluence space '{space_key}'...")
        push_success = push_space(space_key, force=force)
        if not push_success:
            logger.error(f"Failed to push content to Confluence space '{space_key}'.")
            return False

    logger.info(f"Successfully synced Confluence space '{space_key}'.")
    return True


def sync_all_spaces(password=None, force=False, direction=None):
    """
    Synchronize all configured Confluence spaces with local files.

    Args:
        password (str, optional): Not used, kept for backward compatibility.
        force (bool, optional): Whether to force overwrite files/pages.
        direction (str, optional): The sync direction ('pull', 'push', or 'both').
            Defaults to 'both'.

    Returns:
        bool: True if all spaces were synced successfully, False otherwise.
    """
    # Get all configured spaces
    space_configs = SpaceConfigManager().get_all_space_configs()
    if not space_configs:
        logger.error("No spaces configured.")
        return False

    # Sync each space
    success = True
    for space_key in space_configs:
        logger.info(f"Syncing space '{space_key}'...")
        space_success = sync_space(space_key, password=password, force=force, direction=direction)
        if not space_success:
            logger.error(f"Failed to sync space '{space_key}'.")
            success = False

    return success


if __name__ == "__main__":
    # Test the module
    import sys
    if len(sys.argv) > 1:
        space_key = sys.argv[1]
        sync_space(space_key)
    else:
        sync_all_spaces() 