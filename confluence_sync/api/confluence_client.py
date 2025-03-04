"""
Confluence API client module for Confluence Sync.

This module handles communication with the Confluence API, including authentication,
page retrieval, and page creation/update.
"""

import os
import logging
from urllib.parse import urljoin
import requests
from atlassian import Confluence
from rich.console import Console
from rich.progress import Progress

from confluence_sync.config.credentials import CredentialsManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()


class ConfluenceClient:
    """Client for interacting with the Confluence API."""

    def __init__(self, credentials=None, password=None):
        """
        Initialize the Confluence API client.

        Args:
            credentials (dict, optional): Dictionary containing url, email, and api_token.
                                         If not provided, will attempt to load from credentials manager.
            password (str, optional): Not used, kept for backward compatibility.
        """
        self.credentials = credentials
        self.client = None
        self.authenticated = False
        
        # If credentials not provided, try to load them
        if not self.credentials:
            creds_manager = CredentialsManager()
            self.credentials = creds_manager.get_credentials()
            
        # Initialize the client if credentials are available
        if self.credentials:
            self._init_client()
    
    def _init_client(self):
        """Initialize the Confluence client with the provided credentials."""
        try:
            url = self.credentials.get('url')
            email = self.credentials.get('email')
            api_token = self.credentials.get('api_token')
            
            # Validate credentials
            if not all([url, email, api_token]):
                logger.error("Incomplete credentials. Please provide url, email, and api_token.")
                return False
            
            # Initialize the Atlassian Python API client
            self.client = Confluence(
                url=url,
                username=email,
                password=api_token,
                cloud=True  # Assuming Confluence Cloud; set to False for Server
            )
            
            # Test the connection
            self.authenticated = self._test_connection()
            
            if self.authenticated:
                logger.info(f"Successfully authenticated to Confluence as {email}")
            else:
                logger.error("Failed to authenticate to Confluence. Please check your credentials.")
            
            return self.authenticated
            
        except Exception as e:
            logger.error(f"Error initializing Confluence client: {str(e)}")
            return False
    
    def _test_connection(self):
        """Test the connection to Confluence API."""
        try:
            # Try to get space information as a simple API test
            # Using get_all_spaces() instead of get_current_user() which may not be available
            spaces = self.client.get_all_spaces(start=0, limit=1)
            return spaces is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_space(self, space_key):
        """
        Get information about a Confluence space.

        Args:
            space_key (str): The key of the space to retrieve.

        Returns:
            dict: Space information, or None if not found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            space = self.client.get_space(space_key)
            return space
        except Exception as e:
            logger.error(f"Error retrieving space {space_key}: {str(e)}")
            return None
    
    def get_pages_in_space(self, space_key, limit=100, expand=None):
        """
        Get all pages in a Confluence space.

        Args:
            space_key (str): The key of the space to retrieve pages from.
            limit (int, optional): Maximum number of pages to retrieve. Defaults to 100.
            expand (list, optional): List of properties to expand in the response.

        Returns:
            list: List of pages, or empty list if none found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return []
        
        try:
            # Default expand properties if none provided
            if expand is None:
                expand = ["body.storage", "version", "ancestors"]
            
            with Progress() as progress:
                task = progress.add_task(f"Retrieving pages from {space_key}...", total=None)
                
                # Get all pages in the space
                pages = self.client.get_all_pages_from_space(
                    space=space_key,
                    start=0,
                    limit=limit,
                    expand=",".join(expand),
                    status=None,
                    content_type="page"
                )
                
                progress.update(task, completed=True)
            
            logger.info(f"Retrieved {len(pages)} pages from space {space_key}")
            return pages
            
        except Exception as e:
            logger.error(f"Error retrieving pages from space {space_key}: {str(e)}")
            return []
    
    def get_page_by_id(self, page_id, expand=None):
        """
        Get a specific page by ID.

        Args:
            page_id (str): The ID of the page to retrieve.
            expand (list, optional): List of properties to expand in the response.

        Returns:
            dict: Page information, or None if not found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Default expand properties if none provided
            if expand is None:
                expand = ["body.storage", "version", "ancestors"]
            
            page = self.client.get_page_by_id(
                page_id=page_id,
                expand=",".join(expand)
            )
            
            return page
            
        except Exception as e:
            logger.error(f"Error retrieving page {page_id}: {str(e)}")
            return None
    
    def get_page_by_title(self, space_key, title, expand=None):
        """
        Get a specific page by title.

        Args:
            space_key (str): The key of the space to search in.
            title (str): The title of the page to retrieve.
            expand (list, optional): List of properties to expand in the response.

        Returns:
            dict: Page information, or None if not found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Default expand properties if none provided
            if expand is None:
                expand = ["body.storage", "version", "ancestors"]
            
            page = self.client.get_page_by_title(
                space=space_key,
                title=title,
                expand=",".join(expand)
            )
            
            return page
            
        except Exception as e:
            logger.error(f"Error retrieving page '{title}' from space {space_key}: {str(e)}")
            return None
    
    def get_page_attachments(self, page_id):
        """
        Get attachments for a specific page.

        Args:
            page_id (str): The ID of the page to retrieve attachments from.

        Returns:
            list: List of attachments, or empty list if none found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return []
        
        try:
            attachments = self.client.get_attachments_from_content(page_id)
            return attachments.get('results', [])
            
        except Exception as e:
            logger.error(f"Error retrieving attachments for page {page_id}: {str(e)}")
            return []
    
    def download_attachment(self, page_id, attachment_id, filename, download_path):
        """
        Download a specific attachment.

        Args:
            page_id (str): The ID of the page the attachment belongs to.
            attachment_id (str): The ID of the attachment to download.
            filename (str): The filename of the attachment.
            download_path (str): The path to save the attachment to.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return False
        
        try:
            # Ensure the download directory exists
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            # Get the download URL from the attachment info
            attachments = self.client.get_attachments_from_content(page_id)
            attachment = None
            for att in attachments.get('results', []):
                if att.get('id') == attachment_id:
                    attachment = att
                    break
            
            if not attachment:
                logger.error(f"Attachment with ID {attachment_id} not found on page {page_id}")
                return False
            
            # Get the download link
            download_link = attachment.get('_links', {}).get('download')
            if not download_link:
                logger.error(f"Download link not found for attachment {filename}")
                return False
            
            # Construct the correct download URL
            # Confluence Cloud URLs need /wiki appended
            base_url = self.credentials.get('url')
            if not base_url.endswith('/wiki'):
                base_url = base_url + '/wiki'
            download_url = base_url + download_link
            
            # Use requests to download the file
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Downloading {filename}...", total=1)
                
                response = requests.get(
                    download_url,
                    auth=(self.credentials.get('email'), self.credentials.get('api_token')),
                    stream=True
                )
                
                if response.status_code == 200:
                    with open(download_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    progress.update(task, advance=1)
                    logger.info(f"Downloaded attachment '{filename}' to {download_path}")
                    return True
                else:
                    logger.error(f"Error downloading attachment '{filename}': HTTP {response.status_code}")
                    return False
            
        except Exception as e:
            logger.error(f"Error downloading attachment '{filename}': {str(e)}")
            return False
    
    def create_attachment(self, page_id, file_path):
        """
        Create a new attachment on a page.

        Args:
            page_id (str): The ID of the page to attach the file to.
            file_path (str): The path to the file to upload.

        Returns:
            dict: Attachment information, or None if error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Get the filename from the path
            filename = os.path.basename(file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            # Upload the attachment using the direct REST API approach
            url = f"{self.credentials.get('url')}/rest/api/content/{page_id}/child/attachment"
            
            headers = {
                'X-Atlassian-Token': 'no-check'
            }
            
            auth = (self.credentials.get('email'), self.credentials.get('api_token'))
            
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Uploading {filename}...", total=1)
                
                with open(file_path, 'rb') as file_obj:
                    files = {
                        'file': (filename, file_obj, 'application/octet-stream')
                    }
                    
                    response = requests.post(
                        url, 
                        headers=headers, 
                        auth=auth, 
                        files=files
                    )
                    
                    progress.update(task, advance=1)
                    
                    if response.status_code in (200, 201):
                        result = response.json()
                        logger.info(f"Created attachment '{filename}' on page {page_id}")
                        return result
                    else:
                        logger.error(f"Error creating attachment '{filename}': HTTP {response.status_code}")
                        logger.error(f"Response: {response.text}")
                        return None
            
        except Exception as e:
            logger.error(f"Error creating attachment from '{file_path}': {str(e)}")
            return None
    
    def update_attachment(self, page_id, attachment_id, file_path):
        """
        Update an existing attachment on a page.

        Args:
            page_id (str): The ID of the page the attachment belongs to.
            attachment_id (str): The ID of the attachment to update.
            file_path (str): The path to the new file to upload.

        Returns:
            dict: Updated attachment information, or None if error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Get the filename from the path
            filename = os.path.basename(file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            # Update the attachment using the direct REST API approach
            url = f"{self.credentials.get('url')}/rest/api/content/{page_id}/child/attachment/{attachment_id}/data"
            
            headers = {
                'X-Atlassian-Token': 'no-check'
            }
            
            auth = (self.credentials.get('email'), self.credentials.get('api_token'))
            
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Updating {filename}...", total=1)
                
                with open(file_path, 'rb') as file_obj:
                    files = {
                        'file': (filename, file_obj, 'application/octet-stream')
                    }
                    
                    response = requests.post(
                        url, 
                        headers=headers, 
                        auth=auth, 
                        files=files
                    )
                    
                    progress.update(task, advance=1)
                    
                    if response.status_code in (200, 201):
                        result = response.json()
                        logger.info(f"Updated attachment '{filename}' on page {page_id}")
                        return result
                    else:
                        logger.error(f"Error updating attachment '{filename}': HTTP {response.status_code}")
                        logger.error(f"Response: {response.text}")
                        return None
            
        except Exception as e:
            logger.error(f"Error updating attachment from '{file_path}': {str(e)}")
            return None
    
    def create_page(self, space_key, title, body, parent_id=None):
        """
        Create a new page in Confluence.

        Args:
            space_key (str): The key of the space to create the page in.
            title (str): The title of the page.
            body (str): The body content of the page (in storage format).
            parent_id (str, optional): The ID of the parent page.

        Returns:
            dict: Created page information, or None if error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Create the page
            page = self.client.create_page(
                space=space_key,
                title=title,
                body=body,
                parent_id=parent_id,
                type='page',
                representation='storage'
            )
            
            logger.info(f"Created page '{title}' in space {space_key}")
            return page
            
        except Exception as e:
            logger.error(f"Error creating page '{title}' in space {space_key}: {str(e)}")
            return None
    
    def update_page(self, page_id, title, body, parent_id=None):
        """
        Update an existing page in Confluence.

        Args:
            page_id (str): The ID of the page to update.
            title (str): The new title of the page.
            body (str): The new body content of the page (in storage format).
            parent_id (str, optional): The ID of the parent page.

        Returns:
            dict: Updated page information, or None if error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Get current page info to get the version number
            current_page = self.get_page_by_id(page_id)
            if not current_page:
                logger.error(f"Could not retrieve current page info for {page_id}")
                return None
            
            # Update the page
            page = self.client.update_page(
                page_id=page_id,
                title=title,
                body=body,
                parent_id=parent_id,
                type='page',
                representation='storage'
            )
            
            logger.info(f"Updated page '{title}' (ID: {page_id})")
            return page
            
        except Exception as e:
            logger.error(f"Error updating page '{title}' (ID: {page_id}): {str(e)}")
            return None
    
    def download_attachments_from_page(self, page_id, download_dir):
        """
        Download all attachments from a page to a directory.

        Args:
            page_id (str): The ID of the page to download attachments from.
            download_dir (str): The directory to save attachments to.

        Returns:
            dict: Dictionary of attachment filenames and their local paths, or None if error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Get attachments
            attachments = self.get_page_attachments(page_id)
            if not attachments:
                logger.info(f"No attachments found for page {page_id}")
                return {}
            
            # Create download directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            # Dictionary to store attachment info
            attachment_info = {}
            
            # Download each attachment
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Downloading attachments...", total=len(attachments))
                
                for attachment in attachments:
                    attachment_id = attachment.get('id')
                    filename = attachment.get('title')
                    
                    if attachment_id and filename:
                        download_path = os.path.join(download_dir, filename)
                        success = self.download_attachment(page_id, attachment_id, filename, download_path)
                        
                        if success:
                            # Store the attachment info
                            attachment_info[filename] = {
                                'id': attachment_id,
                                'path': download_path,
                                'relative_path': os.path.relpath(download_path, download_dir)
                            }
                    
                    progress.update(task, advance=1)
            
            logger.info(f"Downloaded {len(attachment_info)} attachments to {download_dir}")
            return attachment_info
            
        except Exception as e:
            logger.error(f"Error downloading attachments from page {page_id}: {str(e)}")
            return None
            
    def upload_attachments_to_page(self, page_id, file_paths):
        """
        Upload multiple attachments to a page.

        Args:
            page_id (str): The ID of the page to upload attachments to.
            file_paths (list): List of file paths to upload.

        Returns:
            dict: Dictionary of attachment filenames and their info, or None if error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Get current attachments
            current_attachments = self.get_page_attachments(page_id)
            current_attachments_dict = {attachment.get('title'): attachment for attachment in current_attachments}
            
            # Dictionary to store attachment info
            attachment_info = {}
            
            # Upload each file
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Uploading attachments...", total=len(file_paths))
                
                for file_path in file_paths:
                    filename = os.path.basename(file_path)
                    
                    # Check if attachment already exists
                    if filename in current_attachments_dict:
                        # Update attachment
                        result = self.update_attachment(
                            page_id, 
                            current_attachments_dict[filename].get('id'), 
                            file_path
                        )
                    else:
                        # Create new attachment
                        result = self.create_attachment(page_id, file_path)
                    
                    if result:
                        attachment_info[filename] = result
                    
                    progress.update(task, advance=1)
            
            logger.info(f"Uploaded {len(attachment_info)} attachments to page {page_id}")
            return attachment_info
            
        except Exception as e:
            logger.error(f"Error uploading attachments to page {page_id}: {str(e)}")
            return None


def test_authentication(password=None):
    """
    Test authentication with Confluence API.

    Args:
        password (str, optional): Not used, kept for backward compatibility.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        client = ConfluenceClient()
        if client.authenticated:
            console.print("[green]Authentication successful![/green]")
            return True
        else:
            console.print("[red]Authentication failed. Please check your credentials.[/red]")
            return False
    except Exception as e:
        console.print(f"[red]Error testing authentication: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    # Test the module
    test_authentication() 