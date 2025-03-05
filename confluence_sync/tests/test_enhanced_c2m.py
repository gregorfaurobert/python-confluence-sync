#!/usr/bin/env python3
"""
Test script for enhanced c2m.py.

This script tests the enhanced c2m.py file.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the enhanced c2m module
try:
    from confluence2markdown.enhanced_c2m import enhanced_convert_html_content
    print("Successfully imported enhanced_c2m module")
except ImportError as e:
    print(f"Failed to import enhanced_c2m module: {e}")
    sys.exit(1)

def main():
    """Main function to test enhanced_c2m.py."""
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
    converted_md = enhanced_convert_html_content(html_content)
    
    # Write the converted Markdown to a file for comparison
    output_path = project_root / "confluence_sync" / "tests" / "test-enhanced-output.md"
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