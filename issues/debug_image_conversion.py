#!/usr/bin/env python3
"""
Debug script for image reference conversion issue.

This script isolates the image reference conversion process to help debug
the issue with Confluence URLs not being converted to local paths.
"""

import os
import sys
import logging
import re
from bs4 import BeautifulSoup
import html2text

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the relevant modules
from confluence_sync.converter.html_to_markdown import ConfluenceHTMLConverter, convert_confluence_content
from confluence_sync.sync.pull import PullManager

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_conversion_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def debug_html_preprocessing():
    """Debug the HTML preprocessing stage."""
    logger.info("=== Testing HTML Preprocessing ===")
    
    # Test HTML with various image formats
    test_html = """
    <p>Test content with various image formats:</p>
    
    <h3>1. Absolute URL to Confluence attachment</h3>
    <img src="https://welocalizedev.atlassian.net/wiki/download/attachments/12345/image1.png" alt="Absolute URL Image" />
    
    <h3>2. Relative URL to Confluence attachment</h3>
    <img src="/wiki/download/attachments/12345/image2.png" alt="Relative URL Image" />
    
    <h3>3. Attachment with timestamp</h3>
    <img src="https://welocalizedev.atlassian.net/_attachments/image3-20250302-084655.png" alt="Timestamped Image" />
    
    <h3>4. Regular image (not an attachment)</h3>
    <img src="https://example.com/image4.png" alt="Regular Image" />
    """
    
    # Create a converter instance
    converter = ConfluenceHTMLConverter(base_url="https://welocalizedev.atlassian.net")
    
    # Log the original HTML
    logger.debug(f"Original HTML:\n{test_html}")
    
    # Process the HTML
    processed_html = converter.preprocess_html(test_html)
    
    # Log the processed HTML
    logger.debug(f"Processed HTML:\n{processed_html}")
    
    # Parse the processed HTML to check image tags
    soup = BeautifulSoup(processed_html, 'html.parser')
    for i, img_tag in enumerate(soup.find_all('img'), 1):
        logger.info(f"Image {i}:")
        logger.info(f"  src: {img_tag.get('src', '')}")
        logger.info(f"  alt: {img_tag.get('alt', '')}")
        logger.info(f"  class: {img_tag.get('class', [])}")
        logger.info(f"  data-filename: {img_tag.get('data-filename', '')}")
    
    return processed_html

def debug_html_to_markdown_conversion(processed_html):
    """Debug the HTML to Markdown conversion stage."""
    logger.info("=== Testing HTML to Markdown Conversion ===")
    
    # Create a converter instance
    converter = ConfluenceHTMLConverter(base_url="https://welocalizedev.atlassian.net")
    
    # Convert to Markdown
    markdown = converter.h2t.handle(processed_html)
    
    # Log the raw Markdown
    logger.debug(f"Raw Markdown (before post-processing):\n{markdown}")
    
    # Post-process the Markdown
    post_processed_markdown = converter.postprocess_markdown(markdown)
    
    # Log the post-processed Markdown
    logger.debug(f"Post-processed Markdown:\n{post_processed_markdown}")
    
    # Find all image references in the Markdown
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_matches = re.findall(image_pattern, post_processed_markdown)
    
    for i, (alt_text, image_path) in enumerate(image_matches, 1):
        logger.info(f"Image Reference {i}:")
        logger.info(f"  alt_text: {alt_text}")
        logger.info(f"  image_path: {image_path}")
    
    return post_processed_markdown

def debug_image_reference_updating(markdown):
    """Debug the image reference updating stage."""
    logger.info("=== Testing Image Reference Updating ===")
    
    # Create test attachments
    test_attachments = {
        "image1.png": {
            "id": "12345",
            "path": "/tmp/attachments/image1.png",
            "relative_path": "_attachments/image1.png"
        },
        "image2.png": {
            "id": "12346",
            "path": "/tmp/attachments/image2.png",
            "relative_path": "_attachments/image2.png"
        },
        "image3-20250302-084655.png": {
            "id": "12347",
            "path": "/tmp/attachments/image3-20250302-084655.png",
            "relative_path": "_attachments/image3-20250302-084655.png"
        }
    }
    
    # Log the available attachments
    logger.debug(f"Available attachments: {test_attachments}")
    
    # Create a mock PullManager
    class MockPullManager:
        def _update_image_references(self, markdown_content, attachments):
            """Mock implementation of _update_image_references."""
            if not attachments:
                return markdown_content
            
            # Find image references in the Markdown
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            
            def replace_image_path(match):
                alt_text = match.group(1)
                image_path = match.group(2)
                
                logger.debug(f"Processing image reference: {match.group(0)}")
                logger.debug(f"  alt_text: {alt_text}")
                logger.debug(f"  image_path: {image_path}")
                
                # Check for our special marker
                if image_path.startswith('confluence-attachment://'):
                    filename = image_path.replace('confluence-attachment://', '')
                    logger.debug(f"  Found special marker with filename: {filename}")
                    
                    # Try to find a matching attachment
                    for attachment_name, attachment_info in attachments.items():
                        if attachment_name == filename or filename in attachment_name:
                            result = f'![{alt_text.split(":confluence-attachment")[0]}]({attachment_info["relative_path"]})'
                            logger.debug(f"  Matched attachment: {attachment_name}")
                            logger.debug(f"  Result: {result}")
                            return result
                
                # Check for Confluence URLs
                if 'atlassian.net' in image_path or '/download/attachments/' in image_path:
                    filename = os.path.basename(image_path)
                    logger.debug(f"  Found Confluence URL with filename: {filename}")
                    
                    # Try to find a matching attachment
                    for attachment_name, attachment_info in attachments.items():
                        if attachment_name == filename or filename in attachment_name:
                            result = f'![{alt_text.split(":confluence-attachment")[0]}]({attachment_info["relative_path"]})'
                            logger.debug(f"  Matched attachment: {attachment_name}")
                            logger.debug(f"  Result: {result}")
                            return result
                
                # No match found
                logger.debug(f"  No matching attachment found, keeping original: {match.group(0)}")
                return match.group(0)
            
            # Process all image references
            updated_markdown = re.sub(image_pattern, replace_image_path, markdown_content)
            
            return updated_markdown
    
    # Update image references
    pull_manager = MockPullManager()
    updated_markdown = pull_manager._update_image_references(markdown, test_attachments)
    
    # Log the updated Markdown
    logger.debug(f"Updated Markdown:\n{updated_markdown}")
    
    # Find all image references in the updated Markdown
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_matches = re.findall(image_pattern, updated_markdown)
    
    for i, (alt_text, image_path) in enumerate(image_matches, 1):
        logger.info(f"Updated Image Reference {i}:")
        logger.info(f"  alt_text: {alt_text}")
        logger.info(f"  image_path: {image_path}")
        logger.info(f"  Is local path: {image_path.startswith('_attachments/')}")
    
    return updated_markdown

def debug_end_to_end():
    """Debug the entire conversion process end-to-end."""
    logger.info("=== Testing End-to-End Conversion ===")
    
    # Test HTML
    test_html = """
    <p>Test content with an image:</p>
    <img src="https://welocalizedev.atlassian.net/wiki/download/attachments/12345/image1.png" alt="Test Image" />
    """
    
    # Test attachments
    test_attachments = {
        "image1.png": {
            "id": "12345",
            "path": "/tmp/attachments/image1.png",
            "relative_path": "_attachments/image1.png"
        }
    }
    
    # Convert HTML to Markdown
    markdown = convert_confluence_content(test_html, "https://welocalizedev.atlassian.net")
    logger.debug(f"Converted Markdown:\n{markdown}")
    
    # Create a mock PullManager
    class MockPullManager:
        def _update_image_references(self, markdown_content, attachments):
            """Mock implementation of _update_image_references."""
            from confluence_sync.sync.pull import PullManager
            # Use the actual implementation
            return PullManager._update_image_references(self, markdown_content, attachments)
            
        def _match_filenames(self, filename1, filename2):
            """
            Check if two filenames match, accounting for Confluence's timestamp additions.
            
            Args:
                filename1 (str): First filename to compare.
                filename2 (str): Second filename to compare.
                
            Returns:
                bool: True if the filenames match, False otherwise.
            """
            import re
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
    
    # Update image references
    pull_manager = MockPullManager()
    updated_markdown = pull_manager._update_image_references(markdown, test_attachments)
    logger.debug(f"Updated Markdown:\n{updated_markdown}")
    
    # Check if the image reference was updated correctly
    if "_attachments/image1.png" in updated_markdown:
        logger.info("SUCCESS: Image reference was correctly updated to use local path")
    else:
        logger.error("FAILURE: Image reference was not updated to use local path")
    
    return updated_markdown

def main():
    """Main function to run all debug tests."""
    logger.info("Starting image reference conversion debug")
    
    try:
        # Debug HTML preprocessing
        processed_html = debug_html_preprocessing()
        
        # Debug HTML to Markdown conversion
        markdown = debug_html_to_markdown_conversion(processed_html)
        
        # Debug image reference updating
        updated_markdown = debug_image_reference_updating(markdown)
        
        # Debug end-to-end process
        end_to_end_result = debug_end_to_end()
        
        logger.info("Debug completed successfully")
        
    except Exception as e:
        logger.exception(f"Error during debug: {str(e)}")
    
    logger.info("Debug script completed")

if __name__ == "__main__":
    main() 