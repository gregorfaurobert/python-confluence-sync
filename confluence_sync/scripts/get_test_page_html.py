#!/usr/bin/env python3
"""
Test script to retrieve the "Test" page from Confluence as HTML.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from confluence_sync.api.confluence_client import ConfluenceClient
from confluence_sync.config.credentials import CredentialsManager

def get_space_and_page_info(obsidian_path):
    """
    Get space key and page ID from the .confluence-sync.json file.
    
    Args:
        obsidian_path (str): Path to the Obsidian page directory
        
    Returns:
        tuple: (space_key, page_id) or None if not found
    """
    config_file = Path(obsidian_path) / ".confluence-sync.json"
    
    if not config_file.exists():
        print(f"Config file not found: {config_file}")
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Based on the actual structure of the .confluence-sync.json file
        page_id = config.get('id')
        space_key = config.get('space_key')
        
        if not space_key or not page_id:
            print(f"Missing space key or page ID in config file: {config_file}")
            return None
            
        return space_key, page_id
    
    except Exception as e:
        print(f"Error reading config file: {e}")
        return None

def get_page_as_html(page_id):
    """
    Retrieve a page from Confluence as HTML.
    
    Args:
        page_id (str): The ID of the page to retrieve
        
    Returns:
        str: HTML content of the page, or None if error
    """
    # Initialize the Confluence client
    client = ConfluenceClient()
    
    if not client.authenticated:
        print("Failed to authenticate with Confluence. Check your credentials.")
        return None
    
    # Get the page with body.storage (HTML) and body.view (rendered HTML)
    page = client.get_page_by_id(page_id, expand=["body.storage", "body.view"])
    
    if not page:
        print(f"Failed to retrieve page with ID: {page_id}")
        return None
    
    # Get the HTML content
    html_content = page.get('body', {}).get('storage', {}).get('value')
    
    if not html_content:
        print(f"No HTML content found for page with ID: {page_id}")
        return None
    
    return html_content

def save_html_to_file(html_content, output_path):
    """
    Save HTML content to a file.
    
    Args:
        html_content (str): HTML content to save
        output_path (str): Path to save the HTML file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML content saved to: {output_path}")
    except Exception as e:
        print(f"Error saving HTML content: {e}")

def main():
    # Path to the Test directory in Obsidian
    test_dir = "obsidian-test/Obsidian Test Home/Test"
    
    # Get space key and page ID from config file
    result = get_space_and_page_info(test_dir)
    if not result:
        return
    
    space_key, page_id = result
    print(f"Found page ID {page_id} in space {space_key}")
    
    # Get the page as HTML
    html_content = get_page_as_html(page_id)
    if not html_content:
        return
    
    # Save the HTML content to a file
    output_path = "confluence_sync/tests/test_page.html"
    save_html_to_file(html_content, output_path)

if __name__ == "__main__":
    main() 