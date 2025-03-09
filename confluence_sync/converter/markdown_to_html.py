"""
Markdown to HTML converter module for Confluence Sync.

This module handles the conversion of Markdown content to Confluence HTML format.
"""

import re
import os
import logging
import markdown
import base64
from bs4 import BeautifulSoup

from confluence_sync.converter.integration import MD2CONF_AVAILABLE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if the markdown-to-confluence library is available
MD2CONF_PATH = MD2CONF_AVAILABLE

class MarkdownToConfluenceConverter:
    """Converter for Markdown content to Confluence HTML."""

    def __init__(self, base_url=None):
        """
        Initialize the converter.

        Args:
            base_url (str, optional): Base URL for converting relative links.
        """
        self.base_url = base_url
        self.md = markdown.Markdown(
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
                'markdown.extensions.smarty',
                'pymdownx.tilde'  # Add support for strikethrough with ~~text~~
            ]
        )

    def __del__(self):
        """Clean up temporary resources when the object is destroyed."""
        pass

    def cleanup(self):
        """Clean up temporary resources."""
        pass

    def convert_to_html(self, markdown_content):
        """
        Convert Markdown content to HTML.

        Args:
            markdown_content (str): The Markdown content to convert.

        Returns:
            str: Converted HTML content.
        """
        if not markdown_content:
            return ""
        
        try:
            # Preprocess the Markdown
            processed_markdown = self.preprocess_markdown(markdown_content)
            
            # Convert to HTML
            html = self.md.convert(processed_markdown)
            
            # Post-process the HTML
            html = self.postprocess_html(html)
            
            # Fix image paths for Confluence
            soup = BeautifulSoup(html, 'html.parser')
            self._fix_relative_links(soup)
            html = str(soup)
            
            # Convert to Confluence storage format
            html = self._convert_to_storage_format(html)
            
            # No need for final check for image paths as we now properly convert to Confluence format
            
            return html
            
        except Exception as e:
            logger.error(f"Error converting Markdown to HTML: {str(e)}")
            return ""

    def preprocess_markdown(self, markdown_content):
        """
        Preprocess the Markdown content before conversion.

        Args:
            markdown_content (str): The Markdown content to preprocess.

        Returns:
            str: Preprocessed Markdown content.
        """
        if not markdown_content:
            return ""
        
        # Handle Confluence-specific patterns
        markdown_content = self._handle_info_blocks(markdown_content)
        markdown_content = self._handle_note_blocks(markdown_content)
        markdown_content = self._handle_warning_blocks(markdown_content)
        markdown_content = self._handle_expand_blocks(markdown_content)
        
        return markdown_content

    def _handle_info_blocks(self, markdown_content):
        """Handle info blocks in Markdown."""
        # Match blockquotes that start with "ℹ️ Info:" or similar
        pattern = r'(^|\n)> \*\*ℹ️ Info:\*\* (.*?)(\n(?!\s*>)|\Z)'
        replacement = r'\1<ac:structured-macro ac:name="info"><ac:rich-text-body><p>\2</p></ac:rich-text-body></ac:structured-macro>\3'
        return re.sub(pattern, replacement, markdown_content, flags=re.DOTALL)

    def _handle_note_blocks(self, markdown_content):
        """Handle note blocks in Markdown."""
        # Match blockquotes that start with "📝 Note:" or similar
        pattern = r'(^|\n)> \*\*📝 Note:\*\* (.*?)(\n(?!\s*>)|\Z)'
        replacement = r'\1<ac:structured-macro ac:name="note"><ac:rich-text-body><p>\2</p></ac:rich-text-body></ac:structured-macro>\3'
        return re.sub(pattern, replacement, markdown_content, flags=re.DOTALL)

    def _handle_warning_blocks(self, markdown_content):
        """Handle warning blocks in Markdown."""
        # Match blockquotes that start with "⚠️ Warning:" or similar
        pattern = r'(^|\n)> \*\*⚠️ Warning:\*\* (.*?)(\n(?!\s*>)|\Z)'
        replacement = r'\1<ac:structured-macro ac:name="warning"><ac:rich-text-body><p>\2</p></ac:rich-text-body></ac:structured-macro>\3'
        return re.sub(pattern, replacement, markdown_content, flags=re.DOTALL)

    def _handle_expand_blocks(self, markdown_content):
        """Handle expand blocks in Markdown."""
        # Match details/summary elements
        pattern = r'<details>\s*<summary>(.*?)</summary>(.*?)</details>'
        replacement = r'<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">\1</ac:parameter><ac:rich-text-body>\2</ac:rich-text-body></ac:structured-macro>'
        return re.sub(pattern, replacement, markdown_content, flags=re.DOTALL)

    def postprocess_html(self, html_content):
        """
        Post-process the HTML content after conversion.

        Args:
            html_content (str): The HTML content to post-process.

        Returns:
            str: Post-processed HTML content.
        """
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process code blocks
        self._process_code_blocks(soup)
        
        # Fix relative links if base_url is provided
        if self.base_url:
            self._fix_relative_links(soup)
        
        # Convert to Confluence storage format
        html = self._convert_to_storage_format(str(soup))
        
        return html

    def _process_code_blocks(self, soup):
        """Process code blocks in HTML."""
        # Find all pre/code elements
        code_blocks = soup.find_all('pre')
        
        logger.info(f"Found {len(code_blocks)} code blocks in total")
        
        for block in code_blocks:
            code_elem = block.find('code')
            if code_elem:
                # Get the language class if available
                language = ""
                if 'class' in code_elem.attrs:
                    logger.info(f"Code block has classes: {code_elem.attrs['class']}")
                    for cls in code_elem['class']:
                        if cls.startswith('language-'):
                            language = cls[9:]  # Remove 'language-' prefix
                            break
                
                # Get the code content
                code_content = code_elem.text
                
                # Create a Confluence code macro for all code blocks
                code_macro = f"""
                <ac:structured-macro ac:name="code">
                    <ac:parameter ac:name="language">{language}</ac:parameter>
                    <ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>
                </ac:structured-macro>
                """
                
                # Replace the original pre element with the code macro
                new_tag = BeautifulSoup(code_macro, 'html.parser')
                block.replace_with(new_tag)

    def _fix_relative_links(self, soup):
        """Fix relative links in the HTML content."""
        logger.info("Fixing relative links in HTML content")
        
        # Fix images regardless of base URL
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            logger.info(f"Processing image with src: {src}")
            
            # For all image references, we'll extract just the filename
            # The actual conversion to Confluence format happens in _convert_to_storage_format
            if src and not src.startswith(('data:')):
                # Extract the filename from the path or URL
                filename = os.path.basename(src)
                # Update the src to just the filename
                img_tag['src'] = filename
                logger.info(f"Updated image src to: {filename}")
        
        # Skip link fixing if no base URL is provided
        if not self.base_url:
            logger.info("No base URL provided, skipping link fixing")
            return
        
        # Fix links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and not href.startswith(('http://', 'https://', 'mailto:', '#')):
                a_tag['href'] = self.base_url.rstrip('/') + '/' + href.lstrip('/')
                logger.info(f"Updated link href to: {a_tag['href']}")

    def _convert_to_storage_format(self, html_content):
        """
        Convert HTML to Confluence storage format.

        Args:
            html_content (str): The HTML content to convert.

        Returns:
            str: HTML in Confluence storage format.
        """
        # Replace HTML entities
        html_content = html_content.replace('&lt;', '<').replace('&gt;', '>')
        
        # Add CDATA sections for script and style tags
        html_content = re.sub(r'<script>(.*?)</script>', r'<script><![CDATA[\1]]></script>', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style>(.*?)</style>', r'<style><![CDATA[\1]]></style>', html_content, flags=re.DOTALL)
        
        # Parse the HTML to handle image tags properly
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Convert img tags to Confluence's ac:image format
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            alt_text = img_tag.get('alt', os.path.basename(src))
            
            # Extract just the filename if it's a path or URL
            filename = os.path.basename(src)
            
            # Create the Confluence image macro
            ac_image = soup.new_tag('ac:image')
            
            # Add attributes
            ac_image['ac:alt'] = alt_text
            
            # Add alignment if specified
            if 'align' in img_tag.attrs:
                ac_image['ac:align'] = img_tag['align']
            
            # Create the attachment reference
            ri_attachment = soup.new_tag('ri:attachment')
            ri_attachment['ri:filename'] = filename
            
            # Add the attachment reference to the image macro
            ac_image.append(ri_attachment)
            
            # Replace the original img tag with the Confluence image macro
            img_tag.replace_with(ac_image)
            
            logger.info(f"Converted image reference from '{src}' to Confluence format with filename '{filename}'")
        
        # Convert the soup back to HTML
        html_content = str(soup)
        
        return html_content


def convert_markdown_to_confluence(markdown_content, base_url=None):
    """
    Convert Markdown content to Confluence HTML.

    Args:
        markdown_content (str): The Markdown content to convert.
        base_url (str, optional): Base URL for converting relative links.

    Returns:
        str: Converted HTML content.
    """
    converter = MarkdownToConfluenceConverter(base_url)
    return converter.convert_to_html(markdown_content)


if __name__ == "__main__":
    # Test the converter
    test_markdown = """
# Test Heading

This is a test paragraph with **bold** and *italic* text.

```python
def hello_world():
    print("Hello, World!")
```

> **ℹ️ Info:** This is an info box.
    """
    
    html = convert_markdown_to_confluence(test_markdown)
    print(html) 