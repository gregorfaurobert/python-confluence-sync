#!/usr/bin/env python3
"""
Test script for Confluence folder API functionality.

This script tests the folder-related methods in the ConfluenceClient class.
"""

import os
import sys
import logging
from pprint import pprint

from confluence_sync.api.confluence_client import ConfluenceClient
from confluence_sync.config.credentials import CredentialsManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_get_folders_in_space():
    """Test retrieving folders in a space."""
    client = ConfluenceClient()
    
    # Get the space key from the user
    space_key = input("Enter the space key: ")
    
    # Get folders in the space
    folders = client.get_folders_in_space(space_key)
    
    print(f"\nFound {len(folders)} folders in space {space_key}:")
    for folder in folders:
        print(f"  - {folder.get('title', 'Unknown')} (ID: {folder.get('id', 'Unknown')})")
    
    return folders

def test_get_folder_by_id():
    """Test retrieving a folder by ID."""
    client = ConfluenceClient()
    
    # Get the folder ID from the user
    folder_id = input("Enter the folder ID: ")
    
    # Get the folder
    folder = client.get_folder_by_id(folder_id)
    
    if folder:
        print(f"\nFolder details:")
        pprint(folder)
    else:
        print(f"\nNo folder found with ID {folder_id}")
    
    return folder

def test_get_folder_contents():
    """Test retrieving the contents of a folder."""
    client = ConfluenceClient()
    
    # Get the folder ID from the user
    folder_id = input("Enter the folder ID: ")
    
    # Get the folder contents
    contents = client.get_folder_contents(folder_id)
    
    print(f"\nFound {len(contents)} items in folder {folder_id}:")
    for item in contents:
        print(f"  - {item.get('title', 'Unknown')} (ID: {item.get('id', 'Unknown')}, Type: {item.get('type', 'Unknown')})")
    
    return contents

def test_create_folder():
    """Test creating a folder."""
    client = ConfluenceClient()
    
    # Get the space key from the user
    space_key = input("Enter the space key: ")
    
    # Get the folder title from the user
    title = input("Enter the folder title: ")
    
    # Get the parent ID from the user (optional)
    parent_id = input("Enter the parent ID (optional, press Enter to skip): ")
    if not parent_id:
        parent_id = None
    
    # Create the folder
    folder = client.create_folder(space_key, title, parent_id)
    
    if folder:
        print(f"\nFolder created:")
        pprint(folder)
    else:
        print(f"\nFailed to create folder")
    
    return folder

def test_delete_folder():
    """Test deleting a folder."""
    client = ConfluenceClient()
    
    # Get the folder ID from the user
    folder_id = input("Enter the folder ID to delete: ")
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete folder {folder_id}? (y/n): ")
    if confirm.lower() != 'y':
        print("Deletion cancelled")
        return False
    
    # Delete the folder
    success = client.delete_folder(folder_id)
    
    if success:
        print(f"\nFolder {folder_id} deleted successfully")
    else:
        print(f"\nFailed to delete folder {folder_id}")
    
    return success

def main():
    """Main function to run the tests."""
    print("Confluence Folder API Test")
    print("=========================")
    
    # Check if credentials are available
    creds_manager = CredentialsManager()
    if not creds_manager.get_credentials():
        print("No credentials found. Please set up your credentials first.")
        sys.exit(1)
    
    while True:
        print("\nSelect a test to run:")
        print("1. Get folders in a space")
        print("2. Get folder by ID")
        print("3. Get folder contents")
        print("4. Create folder")
        print("5. Delete folder")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ")
        
        if choice == '0':
            break
        elif choice == '1':
            test_get_folders_in_space()
        elif choice == '2':
            test_get_folder_by_id()
        elif choice == '3':
            test_get_folder_contents()
        elif choice == '4':
            test_create_folder()
        elif choice == '5':
            test_delete_folder()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 