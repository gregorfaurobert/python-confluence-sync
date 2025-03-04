# Image Reference Test Cases

This document contains various test cases for image references to help debug the conversion issue.

## Test Case 1: Standard Confluence Attachment

### HTML Input
```html
<img src="https://welocalizedev.atlassian.net/wiki/download/attachments/12345/image.png" alt="Image Description" />
```

### Expected Markdown Output
```markdown
![Image Description](_attachments/image.png)
```

### Actual Markdown Output
```markdown
![Image Description:confluence-attachment:image.png](https://welocalizedev.atlassian.net/wiki/download/attachments/12345/image.png)
```

## Test Case 2: Confluence Attachment with Timestamp

### HTML Input
```html
<img src="https://welocalizedev.atlassian.net/wiki/_attachments/image-20250302-084655.png" alt="Image with timestamp" />
```

### Expected Markdown Output
```markdown
![Image with timestamp](_attachments/image-20250302-084655.png)
```

### Actual Markdown Output
```markdown
![Image with timestamp:confluence-attachment:image-20250302-084655.png](https://welocalizedev.atlassian.net/_attachments/image-20250302-084655.png)
```

## Test Case 3: Relative Path Attachment

### HTML Input
```html
<img src="/wiki/download/attachments/12345/image.png" alt="Relative path image" />
```

### Expected Markdown Output
```markdown
![Relative path image](_attachments/image.png)
```

### Actual Markdown Output
```markdown
![Relative path image:confluence-attachment:image.png](https://welocalizedev.atlassian.net/wiki/download/attachments/12345/image.png)
```

## Debugging Steps

1. **HTML Preprocessing**
   - Log the HTML before and after preprocessing
   - Verify that attachment images are correctly identified
   - Check if special markers are added correctly

2. **HTML to Markdown Conversion**
   - Log the HTML passed to HTML2Text
   - Check how HTML2Text processes image tags
   - Verify if our markers survive the conversion

3. **Markdown Postprocessing**
   - Log the Markdown before and after postprocessing
   - Check if our regex patterns match the expected image references
   - Verify that the replacement logic works correctly

4. **Attachment Matching**
   - Log the attachments available for the page
   - Check how filenames are matched with attachments
   - Verify that the correct local paths are used

## Debugging Code

Add these logging statements to the code:

```python
# In _fix_relative_links
logger.debug(f"Processing image: {img_tag}")
logger.debug(f"Original src: {src}")
logger.debug(f"Modified src: {img_tag['src']}")

# In _mark_attachment_images
logger.debug(f"Processing image reference: {match.group(0)}")
logger.debug(f"Alt text: {alt_text}")
logger.debug(f"Image path: {image_path}")
logger.debug(f"Modified reference: {result}")

# In _update_image_references
logger.debug(f"Available attachments: {attachments}")
logger.debug(f"Processing image reference: {match.group(0)}")
logger.debug(f"Alt text: {alt_text}")
logger.debug(f"Image path: {image_path}")
logger.debug(f"Modified reference: {result}")
```

## Test Script

Create a test script to isolate the issue:

```python
import os
import logging
from confluence_sync.converter.html_to_markdown import ConfluenceHTMLConverter
from confluence_sync.sync.pull import PullManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test HTML
test_html = """
<p>Test content with an image:</p>
<img src="https://welocalizedev.atlassian.net/wiki/download/attachments/12345/image.png" alt="Test Image" />
"""

# Test attachments
test_attachments = {
    "image.png": {
        "id": "12345",
        "path": "/tmp/attachments/image.png",
        "relative_path": "_attachments/image.png"
    }
}

# Convert HTML to Markdown
converter = ConfluenceHTMLConverter(base_url="https://welocalizedev.atlassian.net")
markdown = converter.convert_to_markdown(test_html)
logger.debug(f"Converted Markdown:\n{markdown}")

# Update image references
pull_manager = PullManager("TEST")
updated_markdown = pull_manager._update_image_references(markdown, test_attachments)
logger.debug(f"Updated Markdown:\n{updated_markdown}")
```

Run this script to see exactly where the conversion is failing. 