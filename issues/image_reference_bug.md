# Bug Report: Image References Not Converting to Local Paths

## Issue Description
When pulling content from Confluence, image references in Markdown files are not being properly converted to local paths. Instead, they remain as absolute URLs pointing to the Confluence server, which breaks image rendering when viewing the Markdown files locally.

## Steps to Reproduce
1. Configure a Confluence space in the tool
2. Add an image to a Confluence page
3. Run `confluence-sync pull --space <SPACE_KEY>`
4. Open the resulting Markdown file
5. Observe that image references still use Confluence URLs instead of local paths

## Expected Behavior
Image references should be converted to local paths pointing to the `_attachments` directory, like:
```markdown
![Image Alt Text](_attachments/image-filename.png)
```

## Actual Behavior
Image references remain as absolute URLs pointing to the Confluence server, like:
```markdown
![Image Alt Text:confluence-attachment:image-filename.png](https://confluence.example.com/_attachments/image-filename.png)
```

## Root Cause Analysis
The issue appears to be in the HTML to Markdown conversion process. While we've implemented special markers and handling for attachment images, the conversion from Confluence URLs to local paths is not working correctly. 

The problem occurs in these key areas:
1. The `_fix_relative_links` method in `ConfluenceHTMLConverter` correctly identifies attachment images but doesn't properly prepare them for conversion
2. The `_mark_attachment_images` method adds special markers, but these aren't being properly processed
3. The `_update_image_references` method in `PullManager` isn't effectively matching Confluence URLs with local attachments

## Attempted Fixes
We've tried several approaches:
1. Enhanced the `_fix_relative_links` method to use a special marker format
2. Improved the `_mark_attachment_images` method to handle the special marker
3. Updated the `_update_image_references` method with more aggressive URL detection and better matching

Despite these changes, the issue persists.

## Proposed Solution
A more comprehensive approach is needed:
1. Modify the HTML parsing to capture more metadata about attachments
2. Implement a more direct mapping between Confluence attachments and local files
3. Consider a different approach to the conversion process, possibly intercepting the HTML before it's converted to Markdown

## Impact
This issue affects the usability of the tool for offline viewing and editing of Confluence content. Users must manually fix image references after pulling content, which defeats the purpose of an automated synchronization tool.

## Priority
High - This is a core functionality issue that impacts the primary use case of the tool.

## Related Files
- `confluence_sync/converter/html_to_markdown.py`
- `confluence_sync/sync/pull.py`

## Additional Notes
The issue might be related to how the HTML2Text library handles image references. We may need to consider a different approach or library for the HTML to Markdown conversion process. 