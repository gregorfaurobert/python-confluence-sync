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
        # This method is deprecated and no longer used.
        # Functionality has been inlined in upload_attachments_to_page
        logger.warning("create_attachment is deprecated, use upload_attachments_to_page instead")
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
        # This method is deprecated and no longer used.
        # Functionality has been inlined in upload_attachments_to_page
        logger.warning("update_attachment is deprecated, use upload_attachments_to_page instead")
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
            title (str): The new title for the page.
            body (str): The new body content for the page.
            parent_id (str, optional): The ID of the parent page. If None, keeps existing parent.

        Returns:
            dict: Updated page data if successful, None if failed.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Get the current page to get the current version
            current_page = self.get_page_by_id(page_id)
            if not current_page:
                logger.error(f"Could not retrieve page with ID {page_id} for update")
                return None
            
            # Update the page
            updated_page = self.client.update_page(
                page_id=page_id,
                title=title,
                body=body,
                parent_id=parent_id,
                type='page',
                representation='storage',
                minor_edit=False
            )
            
            logger.info(f"Updated page: {title} (ID: {page_id})")
            return updated_page
            
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {str(e)}")
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
            
            # Download each attachment without using a new Progress instance
            # to avoid conflicts with any parent Progress instances
            for attachment in attachments:
                attachment_id = attachment.get('id')
                filename = attachment.get('title')
                
                if attachment_id and filename:
                    download_path = os.path.join(download_dir, filename)
                    success = self.download_attachment_without_progress(page_id, attachment_id, filename, download_path)
                    
                    if success:
                        # Store the attachment info
                        attachment_info[filename] = {
                            'id': attachment_id,
                            'path': download_path,
                            'relative_path': os.path.relpath(download_path, download_dir)
                        }
            
            logger.info(f"Downloaded {len(attachment_info)} attachments to {download_dir}")
            return attachment_info
            
        except Exception as e:
            logger.error(f"Error downloading attachments from page {page_id}: {str(e)}")
            return None
    
    def download_attachment_without_progress(self, page_id, attachment_id, filename, download_path):
        """
        Download a specific attachment without using a progress bar.

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
            
            # Use requests to download the file without progress bar
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
                
                logger.info(f"Downloaded attachment '{filename}' to {download_path}")
                return True
            else:
                logger.error(f"Error downloading attachment '{filename}': HTTP {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error downloading attachment '{filename}': {str(e)}")
            return False
    
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
            failed_attachments = []
            
            # Log the total number of attachments to upload
            logger.info(f"Uploading {len(file_paths)} attachments to page {page_id}")
            
            # Upload each file without using Progress (to avoid nested Progress instances)
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                
                try:
                    # Check if file exists
                    if not os.path.exists(file_path):
                        logger.error(f"File not found: {file_path}")
                        failed_attachments.append(filename)
                        continue
                    
                    # Note if this is an update to an existing attachment
                    if filename in current_attachments_dict:
                        attachment = current_attachments_dict[filename]
                        attachment_id = attachment.get('id')
                        logger.info(f"Updating existing attachment '{filename}' (ID: {attachment_id}) on page {page_id}")
                        # We don't need to delete the existing attachment - Confluence will handle versioning
                    else:
                        logger.info(f"Creating new attachment '{filename}' on page {page_id}")
                    
                    # Upload the attachment (whether it's new or replacing an existing one)
                    # Confluence will automatically handle versioning for existing attachments
                    logger.info(f"Uploading attachment '{filename}' to page {page_id}")
                    
                    # Check file size and log warning if it's large
                    file_size = os.path.getsize(file_path)
                    if file_size > 10 * 1024 * 1024:  # 10 MB
                        logger.warning(f"Large attachment '{filename}' ({file_size / 1024 / 1024:.2f} MB) may take longer to upload")
                    
                    result = self.client.attach_file(
                        filename=file_path,  # This is the local file path
                        name=filename,       # This is the name to use in Confluence
                        page_id=page_id      # The page to attach to
                    )
                    
                    if result:
                        logger.info(f"Successfully uploaded attachment '{filename}' to page {page_id}")
                        attachment_info[filename] = result
                    else:
                        logger.error(f"Error uploading attachment '{filename}' - API returned None")
                        failed_attachments.append(filename)
                
                except Exception as e:
                    logger.error(f"Error processing attachment '{filename}': {str(e)}")
                    failed_attachments.append(filename)
            
            if failed_attachments:
                logger.warning(f"Failed to upload {len(failed_attachments)} attachments: {', '.join(failed_attachments)}")
            
            logger.info(f"Uploaded {len(attachment_info)} attachments to page {page_id}")
            return attachment_info
            
        except Exception as e:
            logger.error(f"Error uploading attachments to page {page_id}: {str(e)}")
            return None
    
    # ===== Folder API Methods (using REST API v2) =====
    
    def get_folders_in_space(self, space_id):
        """
        Get all folders in a Confluence space.
        
        This method counts the number of folders in a space by looking for pages
        that have a parent of type 'folder'.
        
        Args:
            space_id (str): The ID or key of the space to retrieve folders from.
            
        Returns:
            list: List of folders, or empty list if none found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return []
        
        try:
            # First, get the space to ensure it exists and to get the space key
            space = self.get_space(space_id)
            if not space:
                logger.error(f"Could not retrieve space with ID/key {space_id}")
                return []
            
            space_key = space['key']
            logger.info(f"Retrieving folders from space {space_key}")
            
            # Use the CQL search to find pages in the space
            api_url = urljoin(self.credentials['url'], f"/rest/api/content/search")
            
            # Set up parameters for CQL search
            params = {
                'cql': f'space="{space_key}" AND type=page',
                'expand': 'ancestors,container',
                'limit': 100
            }
            
            # Set up authentication
            auth = (self.credentials['email'], self.credentials['api_token'])
            
            # Set up headers
            headers = {
                'Accept': 'application/json'
            }
            
            # Make the API request
            response = requests.get(api_url, params=params, headers=headers, auth=auth)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            all_pages = data.get('results', [])
            
            # Dictionary to store unique folders
            folders_dict = {}
            
            # For each page, check if it has a folder in its ancestors or container
            for page in all_pages:
                # Check ancestors for folders
                ancestors = page.get('ancestors', [])
                for ancestor in ancestors:
                    if ancestor.get('type') == 'folder':
                        folder_id = ancestor.get('id')
                        if folder_id and folder_id not in folders_dict:
                            folders_dict[folder_id] = ancestor
                
                # Check if the container is a folder
                container = page.get('container', {})
                if container.get('type') == 'folder':
                    folder_id = container.get('id')
                    if folder_id and folder_id not in folders_dict:
                        folders_dict[folder_id] = container
            
            # Convert the dictionary to a list
            folders = list(folders_dict.values())
            
            logger.info(f"Retrieved {len(folders)} folders from space {space_key}")
            return folders
            
        except Exception as e:
            logger.error(f"Error retrieving folders from space {space_id}: {str(e)}")
            return []
    
    def _is_folder(self, content):
        """
        Helper method to determine if a content item is a folder.
        
        Args:
            content (dict): The content item to check.
            
        Returns:
            bool: True if the content is a folder, False otherwise.
        """
        # Check if the content has a "type" property with value "folder"
        if content.get('type') == 'folder':
            return True
        
        # Check if the content has metadata indicating it's a folder
        metadata = content.get('metadata', {})
        if metadata.get('mediaType') == 'folder' or metadata.get('contentType') == 'folder':
            return True
        
        # Check if the content has properties indicating it's a folder
        properties = content.get('properties', {})
        if properties.get('isFolder') == True or properties.get('content-type') == 'folder':
            return True
        
        # Check if the content has a specific label that might indicate it's a folder
        labels = content.get('labels', [])
        for label in labels:
            if label.get('name') == 'folder':
                return True
        
        # Check the title for common folder indicators
        title = content.get('title', '').lower()
        if title == 'folder' or title.endswith(' folder'):
            return True
        
        return False
    
    def get_folder_by_id(self, folder_id):
        """
        Get a specific folder by ID using REST API v2.
        
        Args:
            folder_id (str): The ID of the folder to retrieve.
            
        Returns:
            dict: Folder data if successful, None if failed.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Construct the API URL for getting a folder by ID
            api_url = urljoin(self.credentials['url'], f"/wiki/api/v2/folders/{folder_id}")
            
            # Set up authentication
            auth = (self.credentials['email'], self.credentials['api_token'])
            
            # Set up headers
            headers = {
                'Accept': 'application/json'
            }
            
            # Make the API request
            response = requests.get(api_url, headers=headers, auth=auth)
            response.raise_for_status()
            
            # Parse the response
            folder = response.json()
            
            logger.info(f"Retrieved folder: {folder.get('title', 'Unknown')} (ID: {folder_id})")
            return folder
            
        except Exception as e:
            logger.error(f"Error retrieving folder {folder_id}: {str(e)}")
            return None
    
    def create_folder(self, space_id, title, parent_id=None):
        """
        Create a new folder in Confluence using REST API v2.
        
        Args:
            space_id (str): The ID of the space to create the folder in.
            title (str): The title for the new folder.
            parent_id (str, optional): The ID of the parent page or folder.
            
        Returns:
            dict: Created folder data if successful, None if failed.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return None
        
        try:
            # Construct the API URL for creating a folder
            api_url = urljoin(self.credentials['url'], "/wiki/api/v2/folders")
            
            # Set up the request body
            body = {
                "spaceId": space_id,
                "title": title
            }
            
            # Add parent ID if provided
            if parent_id:
                body["parentId"] = parent_id
            
            # Set up authentication
            auth = (self.credentials['email'], self.credentials['api_token'])
            
            # Set up headers
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Make the API request
            response = requests.post(api_url, json=body, headers=headers, auth=auth)
            response.raise_for_status()
            
            # Parse the response
            created_folder = response.json()
            
            logger.info(f"Created folder: {title} (ID: {created_folder.get('id', 'Unknown')})")
            return created_folder
            
        except Exception as e:
            logger.error(f"Error creating folder {title}: {str(e)}")
            return None
    
    def delete_folder(self, folder_id):
        """
        Delete a folder in Confluence using REST API v2.
        
        Args:
            folder_id (str): The ID of the folder to delete.
            
        Returns:
            bool: True if successful, False if failed.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return False
        
        try:
            # Construct the API URL for deleting a folder
            api_url = urljoin(self.credentials['url'], f"/wiki/api/v2/folders/{folder_id}")
            
            # Set up authentication
            auth = (self.credentials['email'], self.credentials['api_token'])
            
            # Make the API request
            response = requests.delete(api_url, auth=auth)
            response.raise_for_status()
            
            logger.info(f"Deleted folder with ID: {folder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting folder {folder_id}: {str(e)}")
            return False
    
    def get_folder_contents(self, folder_id):
        """
        Get the contents of a folder using REST API v2.
        
        Args:
            folder_id (str): The ID of the folder to get contents from.
            
        Returns:
            list: List of content items in the folder, or empty list if none found or error.
        """
        if not self.authenticated:
            logger.error("Not authenticated. Please initialize the client with valid credentials.")
            return []
        
        try:
            # Get the folder first to verify it exists
            folder = self.get_folder_by_id(folder_id)
            if not folder:
                logger.error(f"Could not retrieve folder with ID {folder_id}")
                return []
            
            # Construct the API URL for getting children of a folder
            # For v2 API, we can use the children endpoint
            api_url = urljoin(self.credentials['url'], f"/wiki/api/v2/folders/{folder_id}/children")
            
            # Set up parameters
            params = {
                'limit': 100  # Maximum allowed by the API
            }
            
            # Set up authentication
            auth = (self.credentials['email'], self.credentials['api_token'])
            
            # Set up headers
            headers = {
                'Accept': 'application/json'
            }
            
            with Progress() as progress:
                task = progress.add_task(f"Retrieving contents from folder {folder_id}...", total=None)
                
                # Make the API request
                response = requests.get(api_url, params=params, headers=headers, auth=auth)
                response.raise_for_status()
                
                # Parse the response
                data = response.json()
                contents = data.get('results', [])
                
                progress.update(task, completed=True)
            
            logger.info(f"Retrieved {len(contents)} items from folder {folder_id}")
            return contents
            
        except Exception as e:
            logger.error(f"Error retrieving contents from folder {folder_id}: {str(e)}")
            return []


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