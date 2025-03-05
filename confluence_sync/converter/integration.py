"""
Integration module for external Markdown/HTML conversion libraries.

This module integrates external libraries for enhanced conversion between
Confluence HTML and Markdown formats.
"""

import os
import sys
import logging
import importlib.util
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import md2conf (markdown-to-confluence)
try:
    import md2conf
    from md2conf.converter import MarkdownToStorageConverter
    MD2CONF_AVAILABLE = True
    logger.info("markdown-to-confluence (md2conf) library is available")
except ImportError:
    MD2CONF_AVAILABLE = False
    logger.warning("markdown-to-confluence (md2conf) library is not available")

# Try to find confluence2markdown
C2M_SCRIPT_PATH = None
C2M_AVAILABLE = False

# Look for confluence2markdown in the project directory
project_root = Path(__file__).parent.parent.parent
c2m_paths = [
    project_root / "confluence2markdown" / "c2m.py",
    project_root / "c2m.py"
]

for path in c2m_paths:
    if path.exists():
        C2M_SCRIPT_PATH = str(path)
        C2M_AVAILABLE = True
        logger.info(f"confluence2markdown script found at {C2M_SCRIPT_PATH}")
        break

if not C2M_AVAILABLE:
    logger.warning("confluence2markdown script not found")


class EnhancedMarkdownToConfluenceConverter:
    """Enhanced converter for Markdown content to Confluence HTML using md2conf."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the enhanced converter.

        Args:
            base_url (str, optional): Base URL for converting relative links.
        """
        self.base_url = base_url
        
        if not MD2CONF_AVAILABLE:
            raise ImportError("markdown-to-confluence (md2conf) library is not available")
        
        self.converter = MarkdownToStorageConverter()

    def convert_to_html(self, markdown_content: str) -> str:
        """
        Convert Markdown content to Confluence HTML using md2conf.

        Args:
            markdown_content (str): The Markdown content to convert.

        Returns:
            str: Converted HTML content in Confluence Storage Format.
        """
        try:
            # Parse the Markdown content
            result = self.converter.convert(markdown_content)
            
            # Return the HTML content in Confluence Storage Format
            return result
        except Exception as e:
            logger.error(f"Error converting Markdown to HTML using md2conf: {e}")
            raise


class EnhancedConfluenceHTMLConverter:
    """Enhanced converter for Confluence HTML content to Markdown using confluence2markdown."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the enhanced converter.

        Args:
            base_url (str, optional): Base URL for converting relative links.
        """
        self.base_url = base_url
        
        if not C2M_AVAILABLE:
            raise ImportError("confluence2markdown script is not available")

    def convert_to_markdown(self, html_content: str) -> str:
        """
        Convert Confluence HTML content to Markdown using confluence2markdown.

        Args:
            html_content (str): The HTML content to convert.

        Returns:
            str: Converted Markdown content.
        """
        try:
            # Import the c2m module dynamically
            spec = importlib.util.spec_from_file_location("c2m", C2M_SCRIPT_PATH)
            c2m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(c2m)
            
            # Use the convert_html_content function directly
            return c2m.convert_html_content(html_content)
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown using confluence2markdown: {e}")
            
            # Fall back to the original converter
            from confluence_sync.converter.html_to_markdown import convert_confluence_content
            return convert_confluence_content(html_content, self.base_url)


def enhanced_convert_markdown_to_confluence(markdown_content: str, base_url: Optional[str] = None) -> str:
    """
    Convert Markdown content to Confluence HTML using the enhanced converter.

    Args:
        markdown_content (str): The Markdown content to convert.
        base_url (str, optional): Base URL for converting relative links.

    Returns:
        str: Converted HTML content.
    """
    if MD2CONF_AVAILABLE:
        converter = EnhancedMarkdownToConfluenceConverter(base_url)
        return converter.convert_to_html(markdown_content)
    else:
        # Fall back to the original converter
        from confluence_sync.converter.markdown_to_html import convert_markdown_to_confluence
        return convert_markdown_to_confluence(markdown_content, base_url)


def enhanced_convert_confluence_content(html_content: str, base_url: Optional[str] = None) -> str:
    """
    Convert Confluence HTML content to Markdown using the enhanced converter.

    Args:
        html_content (str): The HTML content to convert.
        base_url (str, optional): Base URL for converting relative links.

    Returns:
        str: Converted Markdown content.
    """
    if C2M_AVAILABLE:
        try:
            # Get the directory containing c2m.py
            c2m_dir = Path(C2M_SCRIPT_PATH).parent
            
            # Add the directory to the Python path
            if str(c2m_dir) not in sys.path:
                sys.path.insert(0, str(c2m_dir))
            
            # Import the c2m module
            import c2m
            
            # Check if enhanced_c2m.py exists
            enhanced_c2m_path = c2m_dir / "enhanced_c2m.py"
            if enhanced_c2m_path.exists():
                # Import the enhanced_c2m module
                spec = importlib.util.spec_from_file_location("enhanced_c2m", str(enhanced_c2m_path))
                enhanced_c2m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(enhanced_c2m)
                
                # Use the enhanced_convert_html_content function
                return enhanced_c2m.enhanced_convert_html_content(html_content)
            
            # Fall back to the original c2m module
            return c2m.convert_html_content(html_content)
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown using confluence2markdown: {e}")
            
            # Fall back to the original converter
            from confluence_sync.converter.html_to_markdown import convert_confluence_content
            return convert_confluence_content(html_content, base_url)
    else:
        # Fall back to the original converter
        from confluence_sync.converter.html_to_markdown import convert_confluence_content
        return convert_confluence_content(html_content, base_url) 