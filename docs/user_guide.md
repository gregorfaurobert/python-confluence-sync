# Confluence Sync User Guide

This guide provides detailed information on how to use the Confluence Sync tool to synchronize content between Confluence spaces and local directories.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
   - [Managing Credentials](#managing-credentials)
   - [Managing Space Configurations](#managing-space-configurations)
3. [Syncing Content](#syncing-content)
   - [Pulling Content from Confluence](#pulling-content-from-confluence)
   - [Pushing Content to Confluence](#pushing-content-to-confluence)
   - [Bidirectional Sync](#bidirectional-sync)
4. [Troubleshooting](#troubleshooting)
5. [FAQ](#faq)

## File Structure

When you pull content from Confluence, the tool creates a directory structure that mirrors the page hierarchy in Confluence. Each page is represented by a directory containing a Markdown file with the same name (slugified).

For example, if you have a Confluence space with the following structure:

```
Space Home
├── Development Guide
│   ├── Setup Instructions
│   └── Coding Standards
└── User Guide
    ├── Installation
    └── Configuration
```

The local directory structure will look like this:

```
local-directory/
├── Space Home/
│   └── space-home.md
├── Development Guide/
│   ├── development-guide.md
│   ├── Setup Instructions/
│   │   └── setup-instructions.md
│   └── Coding Standards/
│       └── coding-standards.md
└── User Guide/
    ├── user-guide.md
    ├── Installation/
    │   └── installation.md
    └── Configuration/
        └── configuration.md
```

Each directory also contains a `.confluence-metadata.json` file that stores information about the page, such as its ID, version, and last updated time. This metadata is used to track changes and handle conflicts during sync operations.

## Attachments and Images

When pulling content from Confluence, attachments (including images) are stored in a special `_attachments` directory within each page's directory. This allows you to reference images in your Markdown files using relative paths.

### Image References

The Confluence Sync tool now provides improved handling of image references in Markdown files. When pulling content from Confluence, image references are automatically converted to use relative paths pointing to the local `_attachments` directory. This ensures that images display correctly when viewing the Markdown files locally.

For example, an image in Confluence that appears as:

```html
<img src="https://confluence.example.com/download/attachments/12345/image.png" alt="Example Image" />
```

Will be converted to the following Markdown with a local path:

```markdown
![Example Image](_attachments/image.png)
```

This works with various image reference formats from Confluence, including:
- Absolute URLs to attachments
- Relative URLs to attachments
- Attachments with timestamps in the filename
- Images embedded directly in the Confluence page

### Working with Images

When editing Markdown files locally, you can continue to use the relative paths to reference images. When pushing content back to Confluence, the tool will automatically upload any referenced images as attachments to the Confluence page.

For best results:
1. Use relative paths to reference images in your Markdown files
2. Keep images in the `_attachments` directory
3. Use descriptive filenames for your images

If you're using a Markdown editor like Obsidian that supports relative paths, you'll be able to see the images while editing locally, and they'll be correctly synchronized with Confluence when you push your changes.

## Installation

### Prerequisites

- Python 3.8 or higher
- Confluence API access token (can be generated in your Atlassian account settings)

### Installation Methods

#### Quick Install (Recommended)

**On Linux/macOS:**

```bash
# Clone the repository
git clone https://github.com/yourusername/python-confluence-sync.git
cd python-confluence-sync

# Run the installation script
./install.sh
```

**On Windows:**

```cmd
# Clone the repository
git clone https://github.com/yourusername/python-confluence-sync.git
cd python-confluence-sync

# Run the installation script
install.bat
```

#### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/python-confluence-sync.git
   cd python-confluence-sync
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Configuration

Before you can sync content, you need to configure your Confluence credentials and space mappings.

### Managing Credentials

#### Setting Up Credentials

To set up your Confluence API credentials:

```bash
confluence-sync config credentials
```

This will prompt you for:
- Your Confluence URL (e.g., https://your-domain.atlassian.net)
- Your Confluence email
- Your Confluence API token
- A password to encrypt your credentials locally

Example:
```
$ confluence-sync config credentials

=== Confluence Credentials Setup ===

Enter your Confluence URL (e.g., https://your-domain.atlassian.net): https://example.atlassian.net
Enter your Confluence email: user@example.com
Enter your Confluence API token: ************
Enter a password to encrypt your credentials: 
Confirm password: 
Credentials stored securely at /Users/username/.confluence_sync/credentials.enc

Credentials setup completed successfully!
```

#### Deleting Credentials

To delete your stored credentials:

```bash
confluence-sync config credentials --delete
```

Example:
```
$ confluence-sync config credentials --delete
Are you sure you want to delete your stored credentials? [y/N]: y
Credentials deleted successfully.
```

### Managing Space Configurations

Space configurations map Confluence spaces to local directories.

#### Adding a Space Configuration Interactively

To add a space configuration interactively:

```bash
confluence-sync config spaces --add
```

This will prompt you for:
- The Confluence space key (e.g., TEAM)
- A friendly name for the space (optional)
- The local directory to sync with

Example:
```
$ confluence-sync config spaces --add

=== Confluence Space Configuration ===

Enter the Confluence space key (e.g., TEAM): DOCS
Enter a friendly name for the space (optional): Documentation
Enter the local directory to sync with: ~/Documents/confluence-docs
Space 'DOCS' configured to sync with '/Users/username/Documents/confluence-docs'

Space configuration completed successfully!
```

#### Adding a Space Configuration Directly

To add a space configuration directly with command-line arguments:

```bash
confluence-sync config spaces --space-key SPACE_KEY --space-name "Space Name" --local-dir PATH
```

Example:
```
$ confluence-sync config spaces --space-key TEAM --space-name "Team Space" --local-dir ~/Documents/team-docs
Space 'TEAM' configured to sync with '/Users/username/Documents/team-docs'
```

#### Listing Configured Spaces

To list all configured spaces:

```bash
confluence-sync config spaces --list
```

Example:
```
$ confluence-sync config spaces --list
                                Configured Spaces                                
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Space Key ┃ Name          ┃ Local Directory                                   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ DOCS      │ Documentation │ /Users/username/Documents/confluence-docs          │
│ TEAM      │ Team Space    │ /Users/username/Documents/team-docs                │
└───────────┴───────────────┴───────────────────────────────────────────────────┘
```

#### Removing a Space Configuration

To remove a space configuration:

```bash
confluence-sync config spaces --remove SPACE_KEY
```

Example:
```
$ confluence-sync config spaces --remove TEAM
Are you sure you want to remove space 'TEAM' from configuration? [y/N]: y
Space 'TEAM' removed from configuration.
```

#### Updating a Space's Local Directory

To update the local directory for an existing space configuration, you need to remove the space configuration and then add it again with the new directory path:

```bash
# Step 1: Remove the existing space configuration
confluence-sync config spaces --remove SPACE_KEY

# Step 2: Add the space configuration with the new directory
confluence-sync config spaces --add --space-key SPACE_KEY --local-dir NEW_PATH
```

Example:
```
$ confluence-sync config spaces --remove DOCS
Are you sure you want to remove space 'DOCS' from configuration? [y/N]: y
Space 'DOCS' removed from configuration.

$ confluence-sync config spaces --add --space-key DOCS --local-dir ~/Documents/new-docs-location
Space 'DOCS' configured to sync with '/Users/username/Documents/new-docs-location'
```

Note: This process preserves any existing content in the new directory. If you want to transfer content from the old directory to the new one, you should manually copy the files before updating the configuration.

## Syncing Content

### Pulling Content from Confluence

To download content from a Confluence space to your local directory:

```bash
confluence-sync pull --space SPACE_KEY
```

Add the `--force` flag to overwrite local changes:

```bash
confluence-sync pull --space SPACE_KEY --force
```

Example:
```
$ confluence-sync pull --space DOCS
Pulling content from space 'DOCS' to '/Users/username/Documents/confluence-docs'...
Downloaded 15 pages successfully.
```

### Pushing Content to Confluence

To upload content from your local directory to a Confluence space:

```bash
confluence-sync push --space SPACE_KEY
```

Add the `--force` flag to overwrite remote changes:

```bash
confluence-sync push --space SPACE_KEY --force
```

Example:
```
$ confluence-sync push --space DOCS
Pushing content from '/Users/username/Documents/confluence-docs' to space 'DOCS'...
Uploaded 3 pages successfully.
```

### Bidirectional Sync

To synchronize content in both directions, handling conflicts:

```bash
confluence-sync sync --space SPACE_KEY
```

This will prompt you to choose a sync direction:
1. Pull (Confluence → Local)
2. Push (Local → Confluence)
3. Both (Two-way sync)

Example:
```
$ confluence-sync sync --space DOCS
Choose sync direction:
1. Pull (Confluence → Local)
2. Push (Local → Confluence)
3. Both (Two-way sync)
Enter your choice (1-3): 3

Starting two-way sync between space 'DOCS' and '/Users/username/Documents/confluence-docs'...

Pulling from Confluence...
Retrieved 15 pages from Confluence.
5 pages were already up-to-date locally.
10 pages were updated locally.

Pushing to Confluence...
3 local pages were newer than Confluence versions.
Updated 3 pages in Confluence.

Sync completed successfully!
```

During bidirectional sync, the tool will:
1. First pull content from Confluence, skipping any local files that are newer
2. Then push local content to Confluence, updating any pages that have been modified locally

## Content Conversion

The Confluence Sync tool automatically handles conversion between Confluence HTML content and Markdown format.

### Confluence HTML to Markdown

When pulling content from Confluence, the tool converts the HTML content to Markdown format, handling:

- Headings, paragraphs, and text formatting
- Lists (ordered and unordered)
- Tables
- Code blocks
- Confluence-specific macros:
  - Info, note, and warning panels
  - Code blocks with syntax highlighting
  - Expand/collapse sections
  - Table of contents

### Markdown to Confluence HTML

When pushing content to Confluence, the tool converts Markdown to Confluence-compatible HTML, supporting:

- All standard Markdown syntax
- Special syntax for Confluence-specific elements:
  - Info panels: `[INFO] This is an info panel [/INFO]`
  - Note panels: `[NOTE] This is a note panel [/NOTE]`
  - Warning panels: `[WARNING] This is a warning panel [/WARNING]`
  - Expand sections: `[EXPAND] Title [CONTENT] Content here [/EXPAND]`

Example Markdown with Confluence-specific syntax:

```markdown
# Page Title

This is a regular paragraph with **bold** and *italic* text.

[INFO]
This is an information panel that will be rendered properly in Confluence.
[/INFO]

## Code Example

```python
def hello_world():
    print("Hello, Confluence!")
```

[WARNING]
Be careful when editing this page!
[/WARNING]
```

## Troubleshooting

### Common Issues

#### Authentication Failures

If you encounter authentication issues:

1. Verify your Confluence URL, email, and API token
2. Regenerate your API token in Atlassian account settings
3. Reconfigure your credentials with `confluence-sync config credentials`

#### Space Not Found

If a space cannot be found:

1. Verify the space key is correct (case-sensitive)
2. Check that you have access to the space in Confluence
3. Verify your API token has sufficient permissions

#### Sync Conflicts

When conflicts occur during sync:

1. Use the interactive conflict resolution when prompted
2. Use `--force` flag with caution to override conflicts
3. Manually resolve conflicts by editing the affected files

## FAQ

### Where are my credentials stored?

Credentials are stored encrypted in `~/.confluence_sync/credentials.enc`. The encryption key is derived from your password and a salt stored in `~/.confluence_sync/salt`.

### How do I update my credentials?

Simply run `confluence-sync config credentials` again to update your credentials.

### Can I sync multiple spaces at once?

Currently, you need to sync spaces individually. Batch operations may be added in future versions.

### How are Confluence pages converted to Markdown?

The tool converts Confluence storage format (XHTML) to Markdown, preserving most formatting, links, and embedded content where possible.

### Are attachments synced?

Yes, attachments are downloaded to a subdirectory named `_attachments` within each page's directory.

### How are page hierarchies handled?

Page hierarchies in Confluence are represented as directory structures locally, with child pages stored in subdirectories named after their parent pages. 