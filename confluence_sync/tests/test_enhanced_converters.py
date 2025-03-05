#!/usr/bin/env python3
"""
Test script for enhanced converters integration.

This script tests the integration of the enhanced converters for Confluence Sync.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Import the converter modules
from confluence_sync.converter import (
    convert_confluence_content,
    convert_markdown_to_confluence,
    enhanced_convert_confluence_content,
    enhanced_convert_markdown_to_confluence,
    MD2CONF_AVAILABLE,
    C2M_AVAILABLE
)

def test_converters():
    """Test the enhanced converters."""
    
    # Test HTML to Markdown conversion
    html_content = """
    <div class="wiki-content">
        <h1>Test Page</h1>
        <p>This is a test page with some <strong>bold</strong> and <em>italic</em> text.</p>
        <h2>Code Block</h2>
        <div class="code panel pdl" style="border-width: 1px;">
            <div class="codeContent panelContent pdl">
                <pre class="syntaxhighlighter-pre" data-syntaxhighlighter-params="brush: python; gutter: false; theme: Confluence" data-theme="Confluence">
def hello_world():
    print("Hello, World!")
                </pre>
            </div>
        </div>
        <h2>Table</h2>
        <table class="confluenceTable">
            <thead>
                <tr>
                    <th class="confluenceTh">Column 1</th>
                    <th class="confluenceTh">Column 2</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="confluenceTd">Row 1, Cell 1</td>
                    <td class="confluenceTd">Row 1, Cell 2</td>
                </tr>
                <tr>
                    <td class="confluenceTd">Row 2, Cell 1</td>
                    <td class="confluenceTd">Row 2, Cell 2</td>
                </tr>
            </tbody>
        </table>
        <h2>Image</h2>
        <p>
            <img class="confluence-embedded-image" src="https://example.com/image.png" data-image-src="https://example.com/image.png" data-unresolved-comment-count="0" data-linked-resource-id="12345" data-linked-resource-version="1" data-linked-resource-type="attachment" data-linked-resource-default-alias="image.png" data-base-url="https://example.com" data-linked-resource-content-type="image/png" data-linked-resource-container-id="67890" data-linked-resource-container-version="1" data-media-id="abcdef" data-media-type="image" alt="Example Image">
        </p>
    </div>
    """
    
    # Test Markdown to HTML conversion
    markdown_content = """
    # Test Page
    
    This is a test page with some **bold** and *italic* text.
    
    ## Code Block
    
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    
    ## Table
    
    | Column 1 | Column 2 |
    |----------|----------|
    | Row 1, Cell 1 | Row 1, Cell 2 |
    | Row 2, Cell 1 | Row 2, Cell 2 |
    
    ## Image
    
    ![Example Image](https://example.com/image.png)
    """
    
    # Test default converters
    print("Testing default converters...")
    
    print("\nHTML to Markdown conversion (default):")
    md_default = convert_confluence_content(html_content)
    print(md_default[:500] + "..." if len(md_default) > 500 else md_default)
    
    print("\nMarkdown to HTML conversion (default):")
    html_default = convert_markdown_to_confluence(markdown_content)
    print(html_default[:500] + "..." if len(html_default) > 500 else html_default)
    
    # Test enhanced converters if available
    if C2M_AVAILABLE:
        print("\nTesting enhanced HTML to Markdown converter (confluence2markdown)...")
        print("\nHTML to Markdown conversion (enhanced):")
        md_enhanced = enhanced_convert_confluence_content(html_content)
        print(md_enhanced[:500] + "..." if len(md_enhanced) > 500 else md_enhanced)
    else:
        print("\nEnhanced HTML to Markdown converter (confluence2markdown) is not available.")
    
    if MD2CONF_AVAILABLE:
        print("\nTesting enhanced Markdown to HTML converter (markdown-to-confluence)...")
        print("\nMarkdown to HTML conversion (enhanced):")
        html_enhanced = enhanced_convert_markdown_to_confluence(markdown_content)
        print(html_enhanced[:500] + "..." if len(html_enhanced) > 500 else html_enhanced)
    else:
        print("\nEnhanced Markdown to HTML converter (markdown-to-confluence) is not available.")


if __name__ == "__main__":
    print("Testing enhanced converters integration...")
    print(f"confluence2markdown available: {C2M_AVAILABLE}")
    print(f"markdown-to-confluence available: {MD2CONF_AVAILABLE}")
    test_converters()
    print("\nTest completed.") 