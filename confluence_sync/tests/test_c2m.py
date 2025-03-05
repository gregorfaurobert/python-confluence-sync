#!/usr/bin/env python3
"""
Simple test script for c2m.py.

This script tests the c2m.py file directly.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Add the confluence2markdown directory to the Python path
c2m_dir = project_root / "confluence2markdown"
sys.path.append(str(c2m_dir))

# Import the c2m module
try:
    import confluence2markdown.c2m as c2m
    print("Successfully imported c2m module")
except ImportError as e:
    print(f"Failed to import c2m module: {e}")
    sys.exit(1)

def main():
    """Main function to test c2m.py."""
    # Read the test HTML file
    test_html_path = project_root / "confluence_sync" / "tests" / "test_page.html"
    
    if not test_html_path.exists():
        print(f"Test HTML file not found: {test_html_path}")
        return False
    
    # Read the test HTML content
    with open(test_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Convert the HTML content to Markdown
    converted_md = c2m.convert_html_content(html_content)
    
    # Write the converted Markdown to a file for comparison
    output_path = project_root / "confluence_sync" / "tests" / "test-c2m-output.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(converted_md)
    
    print(f"Converted HTML to Markdown. Output written to: {output_path}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 