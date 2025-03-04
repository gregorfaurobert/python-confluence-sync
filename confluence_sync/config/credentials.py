"""
Credentials management module for Confluence Sync.

This module handles the storage and retrieval of Confluence API credentials.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.confluence_sync")
CREDENTIALS_FILE = "credentials.json"


class CredentialsManager:
    """Manages the storage and retrieval of Confluence API credentials."""

    def __init__(self, config_dir=None):
        """
        Initialize the credentials manager.

        Args:
            config_dir (str, optional): Directory to store credentials. 
                                       Defaults to ~/.confluence_sync.
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.credentials_path = os.path.join(self.config_dir, CREDENTIALS_FILE)
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

    def store_credentials(self, url, email, api_token, password=None):
        """
        Store Confluence credentials in plain text.

        Args:
            url (str): Confluence instance URL.
            email (str): User email for Confluence.
            api_token (str): API token for Confluence.
            password (str, optional): Not used, kept for backward compatibility.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Prepare credentials
            credentials = {
                "url": url,
                "email": email,
                "api_token": api_token
            }
            
            # Save credentials as JSON
            with open(self.credentials_path, 'w') as file:
                json.dump(credentials, file, indent=2)
                
            print(f"Credentials stored at {self.credentials_path}")
            return True
            
        except Exception as e:
            print(f"Error storing credentials: {str(e)}")
            return False

    def get_credentials(self, password=None):
        """
        Retrieve stored Confluence credentials.

        Args:
            password (str, optional): Not used, kept for backward compatibility.

        Returns:
            dict: Dictionary containing url, email, and api_token.
            None: If credentials cannot be retrieved.
        """
        if not os.path.exists(self.credentials_path):
            print("No credentials found. Please set up credentials first.")
            return None
            
        try:
            # Read credentials from JSON file
            with open(self.credentials_path, 'r') as file:
                credentials = json.load(file)
                
            return credentials
            
        except Exception as e:
            print(f"Error retrieving credentials: {str(e)}")
            return None

    def delete_credentials(self):
        """
        Delete stored credentials.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if os.path.exists(self.credentials_path):
                os.remove(self.credentials_path)
                print("Credentials deleted successfully.")
                return True
            else:
                print("No credentials found to delete.")
                return False
        except Exception as e:
            print(f"Error deleting credentials: {str(e)}")
            return False


def setup_credentials_interactive():
    """Interactive function to set up Confluence credentials."""
    print("\n=== Confluence Credentials Setup ===\n")
    
    url = input("Enter your Confluence URL (e.g., https://your-domain.atlassian.net): ")
    email = input("Enter your Confluence email: ")
    api_token = input("Enter your Confluence API token: ")
    
    manager = CredentialsManager()
    success = manager.store_credentials(url, email, api_token)
    
    if success:
        print("\nCredentials setup completed successfully!")
    else:
        print("\nCredentials setup failed. Please try again.")
    
    return success


if __name__ == "__main__":
    # Test the module
    setup_credentials_interactive() 