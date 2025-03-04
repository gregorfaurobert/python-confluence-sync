# Solution Proposal: Fixing Image Reference Conversion

## Problem Summary
The current implementation fails to properly convert Confluence image URLs to local paths during the pull operation. Despite our attempts to add special markers and improve the matching logic, the issue persists.

## Root Cause
After careful analysis, the root cause appears to be in the conversion pipeline:

1. **HTML Parsing Stage**: The BeautifulSoup parser correctly identifies attachment images and adds special markers, but these markers are not preserved correctly through the conversion process.

2. **HTML to Markdown Conversion**: The HTML2Text library processes the HTML and generates Markdown, but it doesn't preserve our custom attributes and markers in a way that's easily accessible in the resulting Markdown.

3. **Post-Processing Stage**: Our post-processing attempts to identify and fix image references, but it's working with already-converted Markdown where much of the original context has been lost.

## Proposed Solution

### Approach 1: Pre-conversion Transformation
Instead of trying to fix the references after conversion, we should transform the HTML before it's passed to HTML2Text:

```python
def preprocess_html(self, html_content):
    """Preprocess the HTML content before conversion."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Process Confluence macros and other elements...
    
    # Transform attachment image URLs directly in the HTML
    for img_tag in soup.find_all('img', src=True):
        src = img_tag['src']
        if self._is_attachment_url(src):
            # Replace the src with a placeholder that will survive conversion
            filename = os.path.basename(src)
            img_tag['src'] = f"LOCAL_ATTACHMENT:{filename}"
    
    return str(soup)
```

Then, in the post-processing stage:

```python
def postprocess_markdown(self, markdown):
    """Post-process the Markdown content."""
    # Replace our placeholders with the correct local paths
    markdown = re.sub(
        r'!\[([^\]]*)\]\(LOCAL_ATTACHMENT:([^)]+)\)',
        r'![\1](_attachments/\2)',
        markdown
    )
    
    # Other post-processing...
    
    return markdown
```

### Approach 2: Custom HTML2Text Subclass
Create a custom subclass of HTML2Text that handles attachment images specially:

```python
class ConfluenceHTML2Text(html2text.HTML2Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachment_images = {}
    
    def handle_img(self, tag):
        src = tag.get('src', '')
        if self._is_attachment_url(src):
            # Store information about this attachment
            filename = os.path.basename(src)
            alt = tag.get('alt', filename)
            
            # Generate a unique placeholder
            placeholder = f"LOCAL_ATTACHMENT:{filename}"
            self.attachment_images[placeholder] = {
                'filename': filename,
                'alt': alt,
                'src': src
            }
            
            # Use the placeholder in the Markdown
            return f"![{alt}]({placeholder})"
        
        # Default handling for other images
        return super().handle_img(tag)
```

Then, in the PullManager:

```python
def _update_image_references(self, markdown_content, attachments):
    """Update image references in Markdown to use relative paths."""
    if not attachments:
        return markdown_content
    
    # Replace placeholders with local paths
    for placeholder, info in self.converter.attachment_images.items():
        filename = info['filename']
        for attachment_name, attachment_info in attachments.items():
            if self._match_filenames(filename, attachment_name):
                markdown_content = markdown_content.replace(
                    f"]({placeholder})",
                    f"]({attachment_info['relative_path']})"
                )
                break
    
    return markdown_content
```

### Approach 3: Direct HTML Processing
Skip HTML2Text entirely for image processing:

1. Use BeautifulSoup to extract all image tags from the HTML
2. For each attachment image, store its information
3. Convert the HTML to Markdown using HTML2Text
4. After conversion, use regex to find all image references
5. Replace the references with the correct local paths based on the stored information

## Implementation Plan

1. Create a new branch for this feature
2. Implement Approach 1 as it's the least invasive
3. Add comprehensive tests for various image reference scenarios
4. If Approach 1 doesn't work, try Approach 2
5. Document the solution in the codebase

## Testing Strategy

1. Create test cases with various image reference formats
2. Test with real Confluence pages containing images
3. Verify that all image references are correctly converted
4. Test edge cases like images with special characters in filenames

## Timeline
Estimated implementation time: 2-3 days
- Day 1: Implementation
- Day 2: Testing and refinement
- Day 3: Documentation and PR review 