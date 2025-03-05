#!/usr/bin/env python3
"""
Test script for HTML to Markdown conversion.

This script tests the conversion of HTML content from Confluence to Markdown.
"""

import os
import sys
from pathlib import Path
import importlib.util

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the converter module
from confluence_sync.converter.integration import enhanced_convert_confluence_content, C2M_AVAILABLE

def main():
    """Main function to test HTML to Markdown conversion."""
    # Check if the enhanced converter is available
    if not C2M_AVAILABLE:
        print("Enhanced HTML to Markdown converter (confluence2markdown) is not available.")
        return False
    
    # Read the test HTML file
    test_html_path = project_root / "confluence_sync" / "tests" / "test_page.html"
    expected_md_path = project_root / "confluence_sync" / "tests" / "test-expected.md"
    
    if not test_html_path.exists():
        print(f"Test HTML file not found: {test_html_path}")
        return False
    
    if not expected_md_path.exists():
        print(f"Expected Markdown file not found: {expected_md_path}")
        return False
    
    # Read the test HTML content
    with open(test_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Read the expected Markdown content
    with open(expected_md_path, "r", encoding="utf-8") as f:
        expected_md = f.read()
    
    # Convert the HTML content to Markdown
    converted_md = enhanced_convert_confluence_content(html_content)
    
    # Write the converted Markdown to a file for comparison
    output_path = project_root / "confluence_sync" / "tests" / "test-output.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(converted_md)
    
    # Compare the converted Markdown with the expected Markdown
    if converted_md.strip() == expected_md.strip():
        print("Conversion successful! The converted Markdown matches the expected output.")
        return True
    else:
        print("Conversion failed! The converted Markdown does not match the expected output.")
        print(f"See the converted output at: {output_path}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 