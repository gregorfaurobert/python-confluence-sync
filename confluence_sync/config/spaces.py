"""
Space configuration module for Confluence Sync.

This module handles the configuration of which Confluence spaces are synced to which local directories.
"""

import os
import yaml
from pathlib import Path

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.confluence_sync")
SPACES_CONFIG_FILE = "spaces.yaml"


class SpaceConfigManager:
    """Manages the configuration of Confluence spaces to local directories."""

    def __init__(self, config_dir=None):
        """
        Initialize the space configuration manager.

        Args:
            config_dir (str, optional): Directory to store configuration.
                                       Defaults to ~/.confluence_sync.
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_path = os.path.join(self.config_dir, SPACES_CONFIG_FILE)
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize empty config if it doesn't exist
        if not os.path.exists(self.config_path):
            self._save_config({"spaces": {}})

    def _load_config(self):
        """
        Load the space configuration from file.

        Returns:
            dict: The space configuration.
        """
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file) or {"spaces": {}}
        except Exception as e:
            print(f"Error loading space configuration: {str(e)}")
            return {"spaces": {}}

    def _save_config(self, config):
        """
        Save the space configuration to file.

        Args:
            config (dict): The space configuration to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving space configuration: {str(e)}")
            return False

    def add_space(self, space_key, local_dir, space_name=None):
        """
        Add or update a space configuration.

        Args:
            space_key (str): The Confluence space key.
            local_dir (str): The local directory to sync with.
            space_name (str, optional): A friendly name for the space.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure local_dir is absolute
            local_dir = os.path.abspath(os.path.expanduser(local_dir))
            
            # Create the directory if it doesn't exist
            os.makedirs(local_dir, exist_ok=True)
            
            # Load current config
            config = self._load_config()
            
            # Add or update space
            config["spaces"][space_key] = {
                "local_dir": local_dir,
                "name": space_name or space_key
            }
            
            # Save updated config
            success = self._save_config(config)
            
            if success:
                print(f"Space '{space_key}' configured to sync with '{local_dir}'")
            
            return success
            
        except Exception as e:
            print(f"Error adding space configuration: {str(e)}")
            return False

    def remove_space(self, space_key):
        """
        Remove a space configuration.

        Args:
            space_key (str): The Confluence space key to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Load current config
            config = self._load_config()
            
            # Check if space exists
            if space_key not in config["spaces"]:
                print(f"Space '{space_key}' not found in configuration.")
                return False
                
            # Remove space
            del config["spaces"][space_key]
            
            # Save updated config
            success = self._save_config(config)
            
            if success:
                print(f"Space '{space_key}' removed from configuration.")
            
            return success
            
        except Exception as e:
            print(f"Error removing space configuration: {str(e)}")
            return False

    def get_space_config(self, space_key):
        """
        Get the configuration for a specific space.

        Args:
            space_key (str): The Confluence space key.

        Returns:
            dict: The space configuration, or None if not found.
        """
        config = self._load_config()
        return config["spaces"].get(space_key)

    def get_all_spaces(self):
        """
        Get all configured spaces.

        Returns:
            dict: Dictionary of all configured spaces.
        """
        config = self._load_config()
        return config["spaces"]

    def get_local_dir(self, space_key):
        """
        Get the local directory for a space.

        Args:
            space_key (str): The Confluence space key.

        Returns:
            str: The local directory path, or None if not found.
        """
        space_config = self.get_space_config(space_key)
        return space_config["local_dir"] if space_config else None


def setup_space_config_interactive():
    """Interactive function to set up space configuration."""
    print("\n=== Confluence Space Configuration ===\n")
    
    space_key = input("Enter the Confluence space key (e.g., TEAM): ")
    space_name = input("Enter a friendly name for the space (optional): ")
    local_dir = input("Enter the local directory to sync with: ")
    
    manager = SpaceConfigManager()
    success = manager.add_space(space_key, local_dir, space_name)
    
    if success:
        print("\nSpace configuration completed successfully!")
    else:
        print("\nSpace configuration failed. Please try again.")
    
    return success


def list_configured_spaces():
    """List all configured spaces."""
    manager = SpaceConfigManager()
    spaces = manager.get_all_spaces()
    
    if not spaces:
        print("No spaces configured.")
        return
    
    print("\n=== Configured Spaces ===\n")
    for key, config in spaces.items():
        print(f"Space Key: {key}")
        print(f"Name: {config.get('name', key)}")
        print(f"Local Directory: {config.get('local_dir')}")
        print("-" * 30)


if __name__ == "__main__":
    # Test the module
    setup_space_config_interactive()
    list_configured_spaces() 