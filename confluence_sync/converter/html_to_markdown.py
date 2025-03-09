"""
HTML to Markdown converter module for Confluence Sync.

This module handles the conversion of Confluence HTML content to Markdown format.
"""

import re
import os
import logging
import html2text
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfluenceHTMLConverter:
    """Converter for Confluence HTML content to Markdown."""

    def __init__(self, base_url=None):
        """
        Initialize the converter.

        Args:
            base_url (str, optional): Base URL for converting relative links.
        """
        self.base_url = base_url
        self.h2t = html2text.HTML2Text()
        self.configure_converter()

    def configure_converter(self):
        """Configure the HTML2Text converter with appropriate settings."""
        # Configure html2text
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_tables = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # No wrapping
        self.h2t.unicode_snob = True
        self.h2t.single_line_break = True
        self.h2t.protect_links = True
        self.h2t.mark_code = True

    def preprocess_html(self, html_content):
        """
        Preprocess the HTML content before conversion.

        This handles Confluence-specific elements and structures.

        Args:
            html_content (str): The HTML content to preprocess.

        Returns:
            str: Preprocessed HTML content.
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Handle Confluence macros
        self._process_code_macros(soup)
        self._process_info_macros(soup)
        self._process_note_macros(soup)
        self._process_warning_macros(soup)
        self._process_expand_macros(soup)
        self._process_toc_macros(soup)

        # Fix relative links if base_url is provided
        if self.base_url:
            self._fix_relative_links(soup)

        # Return the processed HTML
        return str(soup)

    def _process_code_macros(self, soup):
        """Process Confluence code macros."""
        # Find all code blocks
        code_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'code'})
        
        for block in code_blocks:
            # Get the language parameter
            lang_param = block.find('ac:parameter', {'ac:name': 'language'})
            language = lang_param.text if lang_param else ''
            
            # Get the code content
            code_body = block.find('ac:plain-text-body')
            if code_body:
                code_content = code_body.text
                
                # Create a new code element
                code_elem = soup.new_tag('pre')
                code_inner = soup.new_tag('code', attrs={'class': f'language-{language}'})
                code_inner.string = code_content
                code_elem.append(code_inner)
                
                # Replace the original macro with the new code element
                block.replace_with(code_elem)

    def _process_info_macros(self, soup):
        """Process Confluence info macros."""
        info_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'info'})
        
        for block in info_blocks:
            # Get the content
            content = block.find('ac:rich-text-body')
            
            # Create a new div with info styling
            info_div = soup.new_tag('div', attrs={'class': 'confluence-info'})
            info_div.append(soup.new_tag('strong'))
            info_div.strong.string = "ℹ️ Info: "
            
            if content:
                info_div.append(content)
            
            # Replace the original macro
            block.replace_with(info_div)

    def _process_note_macros(self, soup):
        """Process Confluence note macros."""
        note_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'note'})
        
        for block in note_blocks:
            # Get the content
            content = block.find('ac:rich-text-body')
            
            # Create a new div with note styling
            note_div = soup.new_tag('div', attrs={'class': 'confluence-note'})
            note_div.append(soup.new_tag('strong'))
            note_div.strong.string = "📝 Note: "
            
            if content:
                note_div.append(content)
            
            # Replace the original macro
            block.replace_with(note_div)

    def _process_warning_macros(self, soup):
        """Process Confluence warning macros."""
        warning_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'warning'})
        
        for block in warning_blocks:
            # Get the content
            content = block.find('ac:rich-text-body')
            
            # Create a new div with warning styling
            warning_div = soup.new_tag('div', attrs={'class': 'confluence-warning'})
            warning_div.append(soup.new_tag('strong'))
            warning_div.strong.string = "⚠️ Warning: "
            
            if content:
                warning_div.append(content)
            
            # Replace the original macro
            block.replace_with(warning_div)

    def _process_expand_macros(self, soup):
        """Process Confluence expand macros."""
        expand_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'expand'})
        
        for block in expand_blocks:
            # Get the title parameter
            title_param = block.find('ac:parameter', {'ac:name': 'title'})
            title = title_param.text if title_param else 'Details'
            
            # Get the content
            content = block.find('ac:rich-text-body')
            
            # Create a new details element
            details = soup.new_tag('details')
            summary = soup.new_tag('summary')
            summary.string = title
            details.append(summary)
            
            if content:
                details.append(content)
            
            # Replace the original macro
            block.replace_with(details)

    def _process_toc_macros(self, soup):
        """Process Confluence TOC macros."""
        toc_blocks = soup.find_all('ac:structured-macro', {'ac:name': 'toc'})
        
        for block in toc_blocks:
            # Create a placeholder for TOC
            toc_div = soup.new_tag('div', attrs={'class': 'confluence-toc'})
            toc_div.string = "[TOC]"
            
            # Replace the original macro
            block.replace_with(toc_div)

    def _fix_relative_links(self, soup):
        """Fix relative links in the HTML."""
        if not self.base_url:
            return
        
        # Fix links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and not href.startswith(('http://', 'https://', 'mailto:', '#')):
                a_tag['href'] = self.base_url.rstrip('/') + '/' + href.lstrip('/')
        
        # Fix images
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            if src and not src.startswith(('http://', 'https://', 'data:')):
                # Check if this is an attachment
                if '/download/attachments/' in src or '/_attachments/' in src or '/attachments/' in src or 'attachments/' in src:
                    # Extract the filename from the path
                    filename = os.path.basename(src)
                    
                    # Replace the src with a special marker that will survive conversion
                    img_tag['src'] = f"CONFLUENCE_ATTACHMENT:{filename}"
                    
                    # Store the original filename in the alt text if it's not already there
                    if not img_tag.get('alt'):
                        img_tag['alt'] = filename
                else:
                    # Update the src to absolute URL for non-attachment images
                    img_tag['src'] = self.base_url.rstrip('/') + '/' + src.lstrip('/')
            elif src and src.startswith(('http://', 'https://')) and ('/download/attachments/' in src or '/_attachments/' in src or '/attachments/' in src or 'attachments/' in src):
                # This is an absolute URL to an attachment
                # Extract the filename from the path
                filename = os.path.basename(src)
                
                # Replace the src with a special marker that will survive conversion
                img_tag['src'] = f"CONFLUENCE_ATTACHMENT:{filename}"
                
                # Store the original filename in the alt text if it's not already there
                if not img_tag.get('alt'):
                    img_tag['alt'] = filename
        
        # Handle Confluence image macros
        for img_macro in soup.find_all('ac:image'):
            # Extract image filename from attachment
            attachment = img_macro.find('ri:attachment')
            if attachment and attachment.has_attr('ri:filename'):
                filename = attachment['ri:filename']
                
                # Create a new img tag to replace the ac:image macro
                new_img = soup.new_tag('img')
                
                # Set the src attribute with our special marker
                new_img['src'] = f"CONFLUENCE_ATTACHMENT:{filename}"
                
                # Try to get alt text from the ac:image macro
                if img_macro.has_attr('ac:alt'):
                    new_img['alt'] = img_macro['ac:alt']
                else:
                    new_img['alt'] = filename
                
                # Replace the ac:image macro with our new img tag
                img_macro.replace_with(new_img)

    def convert_to_markdown(self, html_content):
        """
        Convert HTML content to Markdown.

        Args:
            html_content (str): The HTML content to convert.

        Returns:
            str: Converted Markdown content.
        """
        if not html_content:
            return ""
        
        try:
            # Preprocess the HTML
            processed_html = self.preprocess_html(html_content)
            
            # Convert to Markdown
            markdown = self.h2t.handle(processed_html)
            
            # Post-process the Markdown
            markdown = self.postprocess_markdown(markdown)
            
            return markdown
            
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {str(e)}")
            return ""

    def postprocess_markdown(self, markdown):
        """
        Post-process the Markdown content.
        
        Args:
            markdown (str): The Markdown content to process.
            
        Returns:
            str: Processed Markdown content.
        """
        if not markdown:
            return ""
        
        # Fix code blocks (html2text sometimes adds extra backticks)
        markdown = re.sub(r'```\s*```([^`]+)```\s*```', r'```\1```', markdown)
        
        # Fix extra newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Replace our special attachment markers with a format that will be recognized by the PullManager
        markdown = re.sub(
            r'!\[([^\]]*)\]\(CONFLUENCE_ATTACHMENT:([^)]+)\)',
            r'![confluence-attachment:\2](confluence-attachment://\2)',
            markdown
        )
        
        # Fix image references that might have been missed
        # This handles cases where the image path is just _attachments/filename.jpg
        markdown = re.sub(
            r'!\[([^\]]*)\]\(_attachments/([^)]+)\)',
            r'![confluence-attachment:\2](confluence-attachment://\2)',
            markdown
        )
        
        # Fix Confluence-specific patterns
        markdown = self._fix_confluence_patterns(markdown)
        
        return markdown
        
    def _mark_attachment_images(self, markdown):
        """
        Add a special marker for attachment images.
        
        Args:
            markdown (str): The Markdown content to process.
            
        Returns:
            str: Processed Markdown content.
        """
        # This method is now less important since we're handling attachments in preprocessing
        # But we'll keep it for backward compatibility and to handle any cases we missed
        
        # Find image references in the Markdown
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def mark_attachment_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Check if this is our special marker (already processed)
            if image_path.startswith('confluence-attachment://') or image_path.startswith('CONFLUENCE_ATTACHMENT:'):
                return match.group(0)
            
            # Check if this is an attachment URL or a path to the _attachments directory
            if '/download/attachments/' in image_path or '/_attachments/' in image_path or '/attachments/' in image_path or 'attachments/' in image_path or image_path.startswith('_attachments/'):
                # Extract the filename from the path
                filename = os.path.basename(image_path)
                
                # If alt text is empty, use the filename as alt text
                if not alt_text:
                    alt_text = filename
                
                # Add a special marker to the alt text and include the filename
                return f'![confluence-attachment:{filename}](confluence-attachment://{filename})'
            
            return match.group(0)
        
        # Process all image references
        marked_markdown = re.sub(image_pattern, mark_attachment_image, markdown)
        
        return marked_markdown

    def _fix_confluence_patterns(self, markdown):
        """Fix Confluence-specific patterns in the Markdown."""
        # Fix info/note/warning blocks
        markdown = re.sub(r'\*\*ℹ️ Info:\s*\*\*', '> **ℹ️ Info:** ', markdown)
        markdown = re.sub(r'\*\*📝 Note:\s*\*\*', '> **📝 Note:** ', markdown)
        markdown = re.sub(r'\*\*⚠️ Warning:\s*\*\*', '> **⚠️ Warning:** ', markdown)
        
        # Ensure proper spacing around headers
        markdown = re.sub(r'([^\n])(\n#{1,6}\s)', r'\1\n\n\2', markdown)
        
        return markdown


def convert_confluence_content(html_content, base_url=None):
    """
    Convert Confluence HTML content to Markdown.

    This is a helper function that creates a ConfluenceHTMLConverter instance
    and uses it to convert the provided HTML content.

    Args:
        html_content (str): The HTML content to convert.
        base_url (str, optional): Base URL for converting relative links.

    Returns:
        str: Converted Markdown content.
    """
    converter = ConfluenceHTMLConverter(base_url=base_url)
    return converter.convert_to_markdown(html_content)


if __name__ == "__main__":
    # Test the converter
    test_html = """
    <h1>Test Heading</h1>
    <p>This is a test paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
    <ac:structured-macro ac:name="code">
        <ac:parameter ac:name="language">python</ac:parameter>
        <ac:plain-text-body><![CDATA[def hello_world():
    print("Hello, World!")
]]></ac:plain-text-body>
    </ac:structured-macro>
    <ac:structured-macro ac:name="info">
        <ac:rich-text-body>
            <p>This is an info box.</p>
        </ac:rich-text-body>
    </ac:structured-macro>
    """
    
    markdown = convert_confluence_content(test_html)
    print(markdown) 