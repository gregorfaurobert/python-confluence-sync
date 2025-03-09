"""
Push module for Confluence Sync.

This module handles pushing content from local files to Confluence.
"""

import os
import logging
import json
from pathlib import Path
from datetime import datetime
import re
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import yaml

from confluence_sync.api.confluence_client import ConfluenceClient
from confluence_sync.config.spaces import SpaceConfigManager
from confluence_sync.converter import (
    convert_markdown_to_confluence,
    enhanced_convert_markdown_to_confluence,
    MD2CONF_AVAILABLE
)
from confluence_sync.converter.markdown_to_html import MarkdownToConfluenceConverter
from confluence_sync.config.credentials import CredentialsManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()

# Constants
METADATA_FILENAME = ".confluence-sync.json"
ATTACHMENTS_DIR = "_attachments"

# Helper functions for metadata
def read_metadata(dir_path):
    """Read metadata from a directory."""
    metadata_path = os.path.join(dir_path, METADATA_FILENAME)
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading metadata from {metadata_path}: {e}")
    return {}

def write_metadata(dir_path, metadata):
    """Write metadata to a directory."""
    metadata_path = os.path.join(dir_path, METADATA_FILENAME)
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error writing metadata to {metadata_path}: {e}")
        return False

class PushManager:
    """Manager for pushing content from local files to Confluence."""

    def __init__(self, space_key, password=None, force=False):
        """
        Initialize the push manager.

        Args:
            space_key (str): The key of the Confluence space to push to.
            password (str, optional): Password for decrypting credentials.
            force (bool, optional): Whether to force overwrite remote pages.
        """
        self.space_key = space_key
        self.force = force
        
        # Get credentials
        credentials_manager = CredentialsManager()
        credentials = credentials_manager.get_credentials(password)
        
        if not credentials:
            raise ValueError("No credentials found. Please run 'confluence-sync config credentials' first.")
        
        # Initialize Confluence client
        self.client = ConfluenceClient(credentials=credentials)
        
        logger.info("Using default Markdown to HTML converter")
        
        self.space_config = SpaceConfigManager().get_space_config(space_key)
        
        if not self.space_config:
            logger.error(f"Space '{space_key}' not found in configuration.")
            raise ValueError(f"Space '{space_key}' not found in configuration.")
        
        self.local_dir = self.space_config.get('local_dir')
        if not self.local_dir:
            logger.error(f"Local directory not configured for space '{space_key}'.")
            raise ValueError(f"Local directory not configured for space '{space_key}'.")
        
        # Ensure local directory exists
        if not os.path.exists(self.local_dir):
            logger.error(f"Local directory '{self.local_dir}' does not exist.")
            raise ValueError(f"Local directory '{self.local_dir}' does not exist.")

    def push(self):
        """
        Push content from local files to Confluence.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.client.authenticated:
            logger.error("Not authenticated. Please check your credentials.")
            return False
        
        try:
            # Get space information
            space = self.client.get_space(self.space_key)
            if not space:
                logger.error(f"Space '{self.space_key}' not found in Confluence.")
                return False
            
            # Get all directories in the local directory
            directories = self._get_content_directories()
            if not directories:
                logger.warning(f"No content directories found in '{self.local_dir}'.")
                return True
            
            # Push content
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn()
            ) as progress:
                task = progress.add_task(f"Pushing content to '{self.space_key}'...", total=len(directories))
                
                # Process root directories first
                for dir_path in directories:
                    self._process_directory(dir_path, None, progress, task)
                
                # Update task completion
                progress.update(task, completed=len(directories))
            
            console.print(f"[green]Successfully pushed content from '{self.local_dir}' to '{self.space_key}'[/green]")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing content to '{self.space_key}': {str(e)}")
            return False

    def _get_content_directories(self):
        """
        Get all content directories in the local directory.

        Returns:
            list: List of directory paths.
        """
        directories = []
        
        for item in os.listdir(self.local_dir):
            item_path = os.path.join(self.local_dir, item)
            
            # Skip hidden files and directories
            if item.startswith('.'):
                continue
            
            # Only include directories
            if os.path.isdir(item_path):
                # Check if it contains any Markdown file
                has_markdown = False
                for file in os.listdir(item_path):
                    if file.endswith('.md') and not file.startswith('.'):
                        has_markdown = True
                        break
                
                if has_markdown:
                    directories.append(item_path)
        
        return directories

    def _process_directory(self, dir_path, parent_id=None, progress=None, task=None):
        """
        Process a directory and its subdirectories.

        Args:
            dir_path (str): Path to the directory.
            parent_id (str, optional): ID of the parent page.
            progress (Progress): Progress bar instance.
            task (int): Task ID for the progress bar.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get the directory name
            dir_name = os.path.basename(dir_path)
            
            # Check for metadata file
            metadata_path = os.path.join(dir_path, METADATA_FILENAME)
            page_id = None
            page_title = dir_name
            file_name = None
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                page_id = metadata.get('id')
                page_title = metadata.get('title', dir_name)
                file_name = metadata.get('file_name')
            
            # Determine the markdown file path
            markdown_path = None
            
            # First check if we have a file name in metadata
            if file_name and os.path.exists(os.path.join(dir_path, file_name)):
                markdown_path = os.path.join(dir_path, file_name)
            else:
                # Fall back to README.md for backward compatibility
                readme_path = os.path.join(dir_path, "README.md")
                if os.path.exists(readme_path):
                    markdown_path = readme_path
                else:
                    # Try to find a markdown file with a name similar to the directory
                    slug_name = self._slugify(dir_name) + ".md"
                    potential_path = os.path.join(dir_path, slug_name)
                    if os.path.exists(potential_path):
                        markdown_path = potential_path
                    else:
                        # Look for any Markdown file in the directory
                        for file in os.listdir(dir_path):
                            if file.endswith('.md') and not file.startswith('.'):
                                markdown_path = os.path.join(dir_path, file)
                                break
            
            if not markdown_path:
                logger.warning(f"No markdown file found in '{dir_path}'. Skipping.")
                if progress and task:
                    progress.update(task, advance=1)
                return True
            
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Remove frontmatter if present
            frontmatter_pattern = r'^---\n(.*?)\n---\n\n'
            frontmatter_match = re.match(frontmatter_pattern, markdown_content, re.DOTALL)
            if frontmatter_match:
                # Remove the frontmatter from the content
                markdown_content = re.sub(frontmatter_pattern, '', markdown_content, 1, re.DOTALL)
                logger.debug(f"Removed frontmatter from '{markdown_path}'")
            
            # Extract title from markdown if it starts with a heading
            title_match = re.match(r'^#\s+(.+)$', markdown_content.split('\n')[0])
            if title_match:
                page_title = title_match.group(1)
                # Remove the title from the content
                markdown_content = '\n'.join(markdown_content.split('\n')[1:]).strip()
            
            # Process images with relative paths
            markdown_content, image_paths = self._process_relative_images(markdown_content, dir_path)
            
            # Convert to Confluence HTML
            html_content = self._convert_markdown_to_html(markdown_content, self.client.credentials.get('url'))
            
            # Check if we should update or create the page
            if page_id:
                # Get the current page to check if it needs updating
                current_page = self.client.get_page_by_id(page_id)
                
                if current_page:
                    # Check if we should skip this page
                    if not self.force:
                        # Get the last updated time from metadata
                        local_updated = None
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            local_updated = metadata.get('local_updated')
                        
                        remote_updated = current_page.get('version', {}).get('when')
                        
                        if local_updated and remote_updated and remote_updated > local_updated:
                            logger.info(f"Skipping '{page_title}' as remote version is newer.")
                            if progress and task:
                                progress.update(task, advance=1)
                            return True
                    
                    # Update the page
                    result = self.client.update_page(
                        page_id=page_id,
                        title=page_title,
                        body=html_content,
                        parent_id=parent_id
                    )
                    
                    if result:
                        logger.info(f"Updated page '{page_title}'")
                        
                        # Upload any images with relative paths
                        if image_paths:
                            if not self._upload_images(page_id, image_paths):
                                logger.warning(f"Failed to upload some attachments for page '{page_title}'")
                        
                        # Process attachments in the _attachments directory
                        if not self._process_attachments(page_id, dir_path):
                            logger.warning(f"Failed to process attachments for page '{page_title}'")
                        
                        # Update metadata
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            
                            metadata['version'] = result.get('version', {}).get('number')
                            metadata['remote_updated'] = result.get('version', {}).get('when')
                            metadata['local_updated'] = datetime.now().isoformat()
                            
                            # Store the file name in metadata if not already there
                            if 'file_name' not in metadata:
                                metadata['file_name'] = os.path.basename(markdown_path)
                            
                            with open(metadata_path, 'w') as f:
                                json.dump(metadata, f, indent=2)
                    else:
                        logger.error(f"Failed to update page '{page_title}'")
                        if progress and task:
                            progress.update(task, advance=1)
                        return False
                else:
                    # Page ID exists in metadata but not in Confluence
                    # Create a new page with parent_id
                    result = self.client.create_page(
                        space_key=self.space_key,
                        title=page_title,
                        body=html_content,
                        parent_id=parent_id
                    )
                    
                    if result:
                        logger.info(f"Created page '{page_title}'")
                        
                        # Upload any images with relative paths
                        if image_paths:
                            if not self._upload_images(result.get('id'), image_paths):
                                logger.warning(f"Failed to upload some attachments for page '{page_title}'")
                        
                        # Process attachments in the _attachments directory
                        if not self._process_attachments(result.get('id'), dir_path):
                            logger.warning(f"Failed to process attachments for page '{page_title}'")
                        
                        # Update metadata
                        metadata = {
                            'id': result.get('id'),
                            'title': page_title,
                            'version': result.get('version', {}).get('number'),
                            'remote_updated': result.get('version', {}).get('when'),
                            'local_updated': datetime.now().isoformat(),
                            'space_key': self.space_key,
                            'file_name': os.path.basename(markdown_path)
                        }
                        
                        with open(metadata_path, 'w') as f:
                            json.dump(metadata, f, indent=2)
                    else:
                        logger.error(f"Failed to create page '{page_title}'")
                        if progress and task:
                            progress.update(task, advance=1)
                        return False
            else:
                # Create a new page
                result = self.client.create_page(
                    space_key=self.space_key,
                    title=page_title,
                    body=html_content,
                    parent_id=parent_id
                )
                
                if result:
                    logger.info(f"Created page '{page_title}'")
                    
                    # Upload any images with relative paths
                    if image_paths:
                        if not self._upload_images(result.get('id'), image_paths):
                            logger.warning(f"Failed to upload some attachments for page '{page_title}'")
                    
                    # Process attachments in the _attachments directory
                    if not self._process_attachments(result.get('id'), dir_path):
                        logger.warning(f"Failed to process attachments for page '{page_title}'")
                    
                    # Create metadata
                    metadata = {
                        'id': result.get('id'),
                        'title': page_title,
                        'version': result.get('version', {}).get('number'),
                        'remote_updated': result.get('version', {}).get('when'),
                        'local_updated': datetime.now().isoformat(),
                        'space_key': self.space_key,
                        'file_name': os.path.basename(markdown_path)
                    }
                    
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                else:
                    logger.error(f"Failed to create page '{page_title}'")
                    if progress and task:
                        progress.update(task, advance=1)
                    return False
            
            # Update progress
            if progress and task:
                progress.update(task, advance=1)
            
            # Process subdirectories
            page_id = page_id or result.get('id')
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path) and not item.startswith('_') and not item.startswith('.'):
                    self._process_directory(item_path, page_id, progress, task)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing directory '{dir_path}': {str(e)}")
            if progress and task:
                progress.update(task, advance=1)
            return False
            
    def _slugify(self, text):
        """
        Convert text to a URL-friendly slug.
        
        Args:
            text (str): The text to slugify.
            
        Returns:
            str: A slugified version of the text.
        """
        # Convert to lowercase
        text = text.lower()
        # Replace spaces with hyphens
        text = re.sub(r'\s+', '-', text)
        # Remove special characters
        text = re.sub(r'[^\w\-]', '', text)
        # Remove consecutive hyphens
        text = re.sub(r'-+', '-', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        
        return text

    def _process_attachments(self, page_id, dir_path):
        """
        Process attachments for a page.

        Args:
            page_id (str): The ID of the page.
            dir_path (str): Path to the directory containing attachments.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if attachments directory exists
            attachments_dir = os.path.join(dir_path, ATTACHMENTS_DIR)
            if not os.path.exists(attachments_dir):
                logger.debug(f"No attachments directory found at {attachments_dir}")
                return True
            
            # Get all files in the attachments directory
            file_paths = []
            for filename in os.listdir(attachments_dir):
                file_path = os.path.join(attachments_dir, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_paths.append(file_path)
            
            if not file_paths:
                logger.info(f"No attachments found in {attachments_dir}")
                return True
            
            logger.info(f"Found {len(file_paths)} attachments to upload from {attachments_dir}")
            
            # Use the improved batch upload method
            result = self.client.upload_attachments_to_page(page_id, file_paths)
            
            if result is not None:
                logger.info(f"Successfully uploaded {len(result)} attachments to page {page_id}")
                return True
            else:
                logger.error(f"Failed to upload attachments to page {page_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error processing attachments for page {page_id}: {str(e)}")
            return False

    def _process_relative_images(self, markdown_content, dir_path):
        """
        Process images with relative paths in Markdown content.
        
        Args:
            markdown_content (str): The Markdown content to process.
            dir_path (str): The directory path where the Markdown file is located.
            
        Returns:
            tuple: (processed_markdown, list_of_image_paths)
        """
        # Find all image references in the Markdown
        image_paths = []
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def replace_image_path(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Skip URLs and data URIs
            if image_path.startswith(('http://', 'https://', 'data:')):
                return match.group(0)
            
            # Handle relative paths
            if not os.path.isabs(image_path):
                # Check if the path is relative to the _attachments directory
                if image_path.startswith('_attachments/'):
                    full_path = os.path.join(dir_path, image_path)
                else:
                    # Path is relative to the Markdown file's directory
                    full_path = os.path.join(dir_path, image_path)
                    
                    # If the file doesn't exist in the current directory,
                    # check if it exists in the _attachments directory
                    if not os.path.exists(full_path) or not os.path.isfile(full_path):
                        attachments_path = os.path.join(dir_path, '_attachments', os.path.basename(image_path))
                        if os.path.exists(attachments_path) and os.path.isfile(attachments_path):
                            full_path = attachments_path
                            # Update the image path to use _attachments/
                            image_path = f"_attachments/{os.path.basename(image_path)}"
                
                # Check if the file exists
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    image_paths.append(full_path)
                    # Keep the original reference in the Markdown
                    return f'![{alt_text}]({image_path})'
            
            # If we get here, keep the original reference
            return match.group(0)
        
        # Process all image references
        processed_markdown = re.sub(image_pattern, replace_image_path, markdown_content)
        
        return processed_markdown, image_paths
    
    def _upload_images(self, page_id, image_paths):
        """
        Upload images to a Confluence page.
        
        Args:
            page_id (str): The ID of the page.
            image_paths (list): List of image file paths to upload.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not image_paths:
                return True
            
            # Use the improved batch upload method
            result = self.client.upload_attachments_to_page(page_id, image_paths)
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error uploading images for page {page_id}: {str(e)}")
            return False

    def _convert_markdown_to_html(self, content, base_url=None):
        """
        Convert Markdown content to Confluence HTML.

        Args:
            content (str): The Markdown content to convert.
            base_url (str, optional): The base URL for converting links.

        Returns:
            str: The converted HTML content.
        """
        return convert_markdown_to_confluence(content, base_url)

    def _save_page_id_to_metadata(self, dir_path, page_id):
        """
        Save the page ID to the metadata file.

        Args:
            dir_path (str): Path to the directory containing the metadata file.
            page_id (str): The ID of the page to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not dir_path:
            logger.warning("Cannot save page ID to metadata: directory path is None")
            return False

        # Read existing metadata
        metadata = read_metadata(dir_path)
        
        # Update with page ID
        metadata['id'] = page_id
        
        # Get page details from Confluence to update metadata
        page_details = self.client.get_page_by_id(page_id)
        if page_details:
            # Update metadata with additional information
            metadata['title'] = page_details.get('title', metadata.get('title', ''))
            metadata['version'] = page_details.get('version', {}).get('number', metadata.get('version', 1))
            metadata['remote_updated'] = page_details.get('version', {}).get('when', metadata.get('remote_updated', ''))
            metadata['space_key'] = self.space_key
        
        # Always update local_updated timestamp
        metadata['local_updated'] = datetime.now().isoformat()
        
        # Write updated metadata
        return write_metadata(dir_path, metadata)

    def _update_or_create_page(self, page_id, space_key, title, markdown_content, parent_id=None, dir_path=None):
        """
        Update an existing page or create a new one.

        Args:
            page_id (str, optional): The ID of the page to update, or None to create a new page.
            space_key (str): The key of the space.
            title (str): The title of the page.
            markdown_content (str): The Markdown content to convert and upload.
            parent_id (str, optional): The ID of the parent page, if creating a new page.
            dir_path (str, optional): Path to the directory containing the Markdown file.

        Returns:
            str: The ID of the updated or created page, or None if error.
        """
        try:
            # Process images in the Markdown content
            processed_markdown, image_paths = self._process_relative_images(markdown_content, dir_path)
            
            # Convert Markdown to Confluence HTML
            html_content = self._convert_markdown_to_html(processed_markdown, self.client.credentials.get('url'))
            
            if page_id:
                # Update existing page
                page_id = self.client.update_page(page_id, title, html_content, parent_id)
                if page_id:
                    logger.info(f"Updated page '{title}'")
                
                    # Upload images if any
                    if image_paths:
                        if not self._upload_images(page_id, image_paths):
                            logger.warning(f"Failed to upload some attachments for page '{title}'")
                    
                    # Upload attachments if any
                    self._process_attachments(page_id, dir_path)
                    
                    return page_id
                else:
                    logger.error(f"Failed to update page '{title}'")
                    return None
            else:
                # Create new page
                page_id = self.client.create_page(space_key, title, html_content, parent_id)
                if page_id:
                    logger.info(f"Created page '{title}'")
                    
                    # Upload images if any
                    if image_paths:
                        if not self._upload_images(page_id, image_paths):
                            logger.warning(f"Failed to upload some attachments for page '{title}'")
                    
                    # Upload attachments if any
                    self._process_attachments(page_id, dir_path)
                    
                    # Save page ID to metadata
                    self._save_page_id_to_metadata(dir_path, page_id)
                    
                    return page_id
                else:
                    logger.error(f"Failed to create page '{title}'")
                    return None
        except Exception as e:
            logger.error(f"Error updating/creating page '{title}': {str(e)}")
            return None


def push_space(space_key, password=None, force=False):
    """
    Push content from local files to a Confluence space.

    Args:
        space_key (str): The key of the Confluence space to push to.
        password (str, optional): Not used, kept for backward compatibility.
        force (bool, optional): Whether to force overwrite remote pages.

    Returns:
        bool: True if the push was successful, False otherwise.
    """
    try:
        push_manager = PushManager(space_key, password=password, force=force)
        return push_manager.push()
    except Exception as e:
        logger.error(f"Error pushing space '{space_key}': {str(e)}")
        return False


if __name__ == "__main__":
    # Test the module
    import sys
    if len(sys.argv) > 1:
        space_key = sys.argv[1]
        push_space(space_key) 