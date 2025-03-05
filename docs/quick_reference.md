# Confluence Sync Quick Reference

This quick reference guide provides the most commonly used commands for the Confluence Sync tool.

## Installation

### On Linux/macOS

```bash
./install.sh
```

### On Windows

```bash
install.bat
```

## Configuration Commands

### Credentials Management

### Set up credentials

```bash
confluence-sync config credentials
```

### Delete credentials

```bash
confluence-sync config credentials --delete
```

### Space Configuration

### Add space interactively

```bash
confluence-sync config spaces --add
```

### Add space directly

```bash
confluence-sync config spaces --space-key SPACE_KEY --space-name "Space Name" --local-dir PATH
```

### List configured spaces

```bash
confluence-sync config spaces --list
```

### Remove space

```bash
confluence-sync config spaces --remove SPACE_KEY
```

### Update a space's local directory (two-step process)

#### Step 1: Remove the existing space configuration

```bash
confluence-sync config spaces --remove SPACE_KEY
```

#### Step 2: Add the space configuration with the new directory

```bash
confluence-sync config spaces --add --space-key SPACE_KEY --local-dir NEW_PATH
```

## Sync Commands

### Pull from Confluence to local

```bash
confluence-sync pull --space SPACE_KEY
```

### Pull and overwrite local changes

```bash
confluence-sync pull --space SPACE_KEY --force
```

### Push from local to Confluence

```bash
confluence-sync push --space SPACE_KEY
```

### Push and overwrite remote changes

```bash
confluence-sync push --space SPACE_KEY --force
```

### Bidirectional sync (performs both pull and push operations)

```bash
confluence-sync sync --space SPACE_KEY
```

## Special Markdown Syntax

When writing Markdown files for Confluence, you can use special syntax for Confluence-specific elements:

### Info, Note, and Warning Panels

```markdown
[INFO]
This is an information panel.
[/INFO]

[NOTE]
This is a note panel.
[/NOTE]

[WARNING]
This is a warning panel.
[/WARNING]
```

### Expand/Collapse Sections

```markdown
[EXPAND] Section Title
[CONTENT]
This content will be in an expandable section.
[/EXPAND]
```

### Code Blocks with Syntax Highlighting

````markdown
```python
def hello_world():
    print("Hello, Confluence!")
```
````

### Images and Attachments

You can include images in your Markdown files using standard Markdown syntax:

```markdown
![Image Description](image-name.png)
```

Images can be placed in:
- The same directory as your Markdown file
- The `_attachments` directory within your page directory

Both approaches are supported and will be properly synced with Confluence.

The tool provides advanced attachment handling with:
- Batch processing for better performance
- Progress reporting during upload/download
- Robust error handling
- Support for special characters in filenames

## Image References

- Images from Confluence are automatically downloaded to the `_attachments` directory
- Image references in Markdown are converted to use relative paths: `![Alt text](_attachments/image.png)`
- When pushing to Confluence, images with relative paths are automatically uploaded as attachments
- The tool supports various image reference formats and handles filename matching intelligently

## File Structure

When pages are pulled from Confluence, they are organized as follows:

```
local-directory/
├── Space Home/                # Directory for space home page
│   ├── space-home.md          # Markdown file named after the page
│   └── _attachments/          # Directory for page attachments
│       ├── image1.png
│       └── document.pdf
├── .confluence-metadata.json  # Sync metadata (do not edit)
├── Page 1/                    # Directory for a top-level page
│   └── page-1.md              # Markdown file with slugified page name
├── Page 2/                    # Directory for another top-level page
│   └── page-2.md              # Markdown file with slugified page name
└── Subfolder/                 # Directory for child pages
    ├── Child Page 1/          # Directory for a child page
    │   └── child-page-1.md    # Markdown file with slugified page name
    └── Child Page 2/          # Directory for another child page
        └── child-page-2.md    # Markdown file with slugified page name
```

## Help Commands

### General help

```bash
confluence-sync --help
```

### Help for config command

```bash
confluence-sync config --help
```

### Help for spaces subcommand

```bash
confluence-sync config spaces --help
```

### Help for pull command

```bash
confluence-sync pull --help
```

### Version Information

```bash
confluence-sync --version
```

## Converters

The tool uses built-in converters for translating between Confluence HTML and Markdown formats.

### Usage

### Pull content from a Confluence space

```bash
confluence-sync pull --space YOUR_SPACE_KEY
```

### Push content to a Confluence space

```bash
confluence-sync push --space YOUR_SPACE_KEY
``` 