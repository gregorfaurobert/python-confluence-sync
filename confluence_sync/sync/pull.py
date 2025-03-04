"""
Pull module for Confluence Sync.

This module handles pulling content from Confluence to local files.
"""

import os
import logging
import json
from pathlib import Path
from datetime import datetime
import re
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from confluence_sync.api.confluence_client import ConfluenceClient
from confluence_sync.config.spaces import SpaceConfigManager
from confluence_sync.converter.html_to_markdown import convert_confluence_content

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()

# Constants
METADATA_FILENAME = ".confluence-sync.json"
ATTACHMENTS_DIR = "_attachments"


class PullManager:
    """Manager for pulling content from Confluence to local files."""

    def __init__(self, space_key, password=None, force=False):
        """
        Initialize the pull manager.

        Args:
            space_key (str): The key of the Confluence space to pull from.
            password (str, optional): Not used, kept for backward compatibility.
            force (bool, optional): Whether to force overwrite local files.
        """
        self.space_key = space_key
        self.force = force
        self.client = ConfluenceClient()
        self.space_config = SpaceConfigManager().get_space_config(space_key)
        
        if not self.space_config:
            logger.error(f"Space '{space_key}' not found in configuration.")
            raise ValueError(f"Space '{space_key}' not found in configuration.")
        
        self.local_dir = self.space_config.get('local_dir')
        if not self.local_dir:
            logger.error(f"Local directory not configured for space '{space_key}'.")
            raise ValueError(f"Local directory not configured for space '{space_key}'.")
        
        # Ensure local directory exists
        os.makedirs(self.local_dir, exist_ok=True)

    def pull(self):
        """
        Pull content from Confluence to local files.

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
            
            # Get all pages in the space
            pages = self.client.get_pages_in_space(self.space_key)
            if not pages:
                logger.warning(f"No pages found in space '{self.space_key}'.")
                return True
            
            # Create a page hierarchy
            page_hierarchy = self._build_page_hierarchy(pages)
            
            # Pull pages
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn()
            ) as progress:
                task = progress.add_task(f"Pulling content from '{self.space_key}'...", total=len(pages))
                
                # Process root pages first
                for page in page_hierarchy.get('root', []):
                    self._process_page(page, progress, task)
                
                # Update task completion
                progress.update(task, completed=len(pages))
            
            console.print(f"[green]Successfully pulled {len(pages)} pages from '{self.space_key}' to '{self.local_dir}'[/green]")
            return True
            
        except Exception as e:
            logger.error(f"Error pulling content from '{self.space_key}': {str(e)}")
            return False

    def _build_page_hierarchy(self, pages):
        """
        Build a hierarchy of pages based on their ancestors.

        Args:
            pages (list): List of pages from Confluence.

        Returns:
            dict: Dictionary with 'root' key for root pages and page IDs as keys for child pages.
        """
        hierarchy = {'root': []}
        
        # First pass: create entries for all pages
        for page in pages:
            page_id = page.get('id')
            hierarchy[page_id] = []
        
        # Second pass: organize pages into hierarchy
        for page in pages:
            page_id = page.get('id')
            ancestors = page.get('ancestors', [])
            
            if not ancestors:
                # This is a root page
                hierarchy['root'].append(page)
            else:
                # Get the immediate parent
                parent_id = ancestors[-1].get('id')
                if parent_id in hierarchy:
                    hierarchy[parent_id].append(page)
        
        return hierarchy

    def _process_page(self, page, progress, task, parent_path=None):
        """
        Process a page and its children.

        Args:
            page (dict): The page to process.
            progress (Progress): Progress bar instance.
            task (int): Task ID for the progress bar.
            parent_path (str, optional): Path to the parent directory.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            page_id = page.get('id')
            page_title = page.get('title', 'Untitled')
            
            # Create a safe filename
            safe_title = self._safe_filename(page_title)
            
            # Determine the directory path
            if parent_path:
                dir_path = os.path.join(parent_path, safe_title)
            else:
                dir_path = os.path.join(self.local_dir, safe_title)
            
            # Create directory if it doesn't exist
            os.makedirs(dir_path, exist_ok=True)
            
            # Determine the file path - use slugified page title instead of README.md
            file_name = self._slugify(page_title) + ".md"
            file_path = os.path.join(dir_path, file_name)
            
            # Check if we should skip this file
            if not self.force and os.path.exists(file_path):
                metadata_path = os.path.join(dir_path, METADATA_FILENAME)
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Skip if the local version is newer
                    local_updated = metadata.get('local_updated')
                    remote_updated = page.get('version', {}).get('when')
                    
                    if local_updated and remote_updated and local_updated > remote_updated:
                        logger.info(f"Skipping '{page_title}' as local version is newer.")
                        progress.update(task, advance=1)
                        return True
            
            # Get the page content
            body = page.get('body', {}).get('storage', {}).get('value', '')
            
            # Convert to Markdown
            markdown_content = convert_confluence_content(body, self.client.credentials.get('url'))
            
            # Add a title at the top
            markdown_content = f"# {page_title}\n\n{markdown_content}"
            
            # Process attachments before writing the file
            attachments = self._process_attachments(page_id, dir_path)
            
            # Update image references in the markdown to use relative paths
            if attachments:
                markdown_content = self._update_image_references(markdown_content, attachments)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Save metadata
            metadata = {
                'id': page_id,
                'title': page_title,
                'version': page.get('version', {}).get('number'),
                'remote_updated': page.get('version', {}).get('when'),
                'local_updated': datetime.now().isoformat(),
                'space_key': self.space_key,
                'file_name': file_name  # Store the file name in metadata
            }
            
            with open(os.path.join(dir_path, METADATA_FILENAME), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update progress
            progress.update(task, advance=1)
            
            # Process child pages
            for child_page in self.client.client.get_child_pages(page_id) or []:
                # Get the full page content for the child
                child_page_full = self.client.get_page_by_id(child_page.get('id'))
                if child_page_full:
                    self._process_page(child_page_full, progress, task, dir_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing page '{page.get('title')}': {str(e)}")
            return False

    def _process_attachments(self, page_id, dir_path):
        """
        Process attachments for a page.

        Args:
            page_id (str): The ID of the page.
            dir_path (str): Path to the directory to save attachments.

        Returns:
            dict: Dictionary of attachment filenames and their local paths, or None if no attachments.
        """
        try:
            # Create attachments directory
            attachments_dir = os.path.join(dir_path, ATTACHMENTS_DIR)
            
            # Use the improved batch download method
            attachment_info = self.client.download_attachments_from_page(page_id, attachments_dir)
            
            if not attachment_info:
                return None
            
            # Convert to the format expected by _update_image_references
            result = {}
            for filename, info in attachment_info.items():
                result[filename] = {
                    'id': info.get('id'),
                    'path': info.get('path'),
                    'relative_path': os.path.join(ATTACHMENTS_DIR, filename)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing attachments for page {page_id}: {str(e)}")
            return None
            
    def _update_image_references(self, markdown_content, attachments):
        """
        Update image references in Markdown to use relative paths.
        
        Args:
            markdown_content (str): The Markdown content to update.
            attachments (dict): Dictionary of attachment filenames and their info.
            
        Returns:
            str: Updated Markdown content.
        """
        if not attachments:
            return markdown_content
        
        # Find image references in the Markdown that match attachment filenames
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def replace_image_path(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Check for our special marker
            if image_path.startswith('confluence-attachment://'):
                # Extract the filename from the path
                filename = image_path.replace('confluence-attachment://', '')
                
                # Try to find a matching attachment by filename
                for attachment_name, attachment_info in attachments.items():
                    if self._match_filenames(filename, attachment_name):
                        # Clean up the alt text by removing any confluence markers
                        clean_alt_text = alt_text.split(':')[0] if ':' in alt_text else alt_text
                        return f'![{clean_alt_text}]({attachment_info["relative_path"]})'
                
                # If we couldn't find a match, use the first attachment as a fallback
                if attachments:
                    first_attachment = next(iter(attachments.values()))
                    # Clean up the alt text
                    clean_alt_text = alt_text.split(':')[0] if ':' in alt_text else alt_text
                    return f'![{clean_alt_text}]({first_attachment["relative_path"]})'
            
            # Force conversion of Confluence URLs to local paths
            if 'atlassian.net' in image_path or 'confluence' in image_path or '/download/attachments/' in image_path:
                # Extract the filename from the path
                filename = os.path.basename(image_path)
                
                # Try to find a matching attachment by filename
                for attachment_name, attachment_info in attachments.items():
                    if self._match_filenames(filename, attachment_name):
                        # Clean up the alt text
                        clean_alt_text = alt_text.split(':')[0] if ':' in alt_text else alt_text
                        return f'![{clean_alt_text}]({attachment_info["relative_path"]})'
                
                # If we couldn't find a match, use the first attachment as a fallback
                if attachments:
                    first_attachment = next(iter(attachments.values()))
                    # Clean up the alt text
                    clean_alt_text = alt_text.split(':')[0] if ':' in alt_text else alt_text
                    return f'![{clean_alt_text}]({first_attachment["relative_path"]})'
            
            # Standard check if this is a local attachment
            filename = os.path.basename(image_path)
            for attachment_name, attachment_info in attachments.items():
                if self._match_filenames(filename, attachment_name):
                    # Clean up the alt text
                    clean_alt_text = alt_text.split(':')[0] if ':' in alt_text else alt_text
                    return f'![{clean_alt_text}]({attachment_info["relative_path"]})'
            
            return match.group(0)
        
        # Process all image references
        updated_markdown = re.sub(image_pattern, replace_image_path, markdown_content)
        
        return updated_markdown

    def _match_filenames(self, filename1, filename2):
        """
        Check if two filenames match, accounting for Confluence's timestamp additions.
        
        Args:
            filename1 (str): First filename to compare.
            filename2 (str): Second filename to compare.
            
        Returns:
            bool: True if the filenames match, False otherwise.
        """
        # Direct match
        if filename1 == filename2:
            return True
        
        # One is a substring of the other
        if filename1 in filename2 or filename2 in filename1:
            return True
        
        # Remove timestamps (Confluence often adds timestamps to filenames)
        base_filename1 = re.sub(r'-\d{8}-\d{6}(\.\w+)$', r'\1', filename1)
        base_filename2 = re.sub(r'-\d{8}-\d{6}(\.\w+)$', r'\1', filename2)
        
        # Compare without timestamps
        if base_filename1 == base_filename2:
            return True
        
        # Compare without timestamps, one is a substring of the other
        if base_filename1 in base_filename2 or base_filename2 in base_filename1:
            return True
        
        return False

    def _safe_filename(self, filename):
        """
        Create a safe filename from a page title.

        Args:
            filename (str): The original filename.

        Returns:
            str: A safe filename.
        """
        # Replace invalid characters with underscores
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', filename)
        
        # Limit length
        if len(safe_name) > 100:
            safe_name = safe_name[:97] + '...'
        
        return safe_name

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


def pull_space(space_key, password=None, force=False):
    """
    Pull content from a Confluence space to local files.

    Args:
        space_key (str): The key of the Confluence space to pull from.
        password (str, optional): Not used, kept for backward compatibility.
        force (bool, optional): Whether to force overwrite local files.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        manager = PullManager(space_key, force=force)
        return manager.pull()
    except Exception as e:
        logger.error(f"Error pulling space '{space_key}': {str(e)}")
        console.print(f"[red]Error pulling space '{space_key}': {str(e)}[/red]")
        return False


if __name__ == "__main__":
    # Test the module
    import sys
    if len(sys.argv) > 1:
        space_key = sys.argv[1]
        pull_space(space_key) 