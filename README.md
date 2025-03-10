# Python Confluence Sync

! FULLY IMPLEMENTED with Cursor and AI!

A suite of Python scripts for syncing Confluence spaces with local directories. This tool allows you to work with Confluence content in your preferred text editor or IDE, using Markdown format, and sync changes back to Confluence.

## Features

- **Credential Storage**: Store your Confluence API credentials
- **Space Configuration Management**: Configure which Confluence spaces to sync with which local directories
- **Content Synchronization**:
  - Pull content from Confluence to local Markdown files
  - Push content from local Markdown files to Confluence
  - Bidirectional sync with conflict detection and resolution
- **Format Conversion**:
  - Convert Confluence HTML to Markdown when pulling content
  - Convert Markdown to Confluence HTML when pushing content
  - Support for Confluence-specific elements (info/note/warning panels, code blocks, etc.)
  - Support for common Markdown syntax including tables, code blocks, headings, lists, links, images, and strikethrough text
- **Attachment Handling**: Sync attachments between Confluence and local directories
- **Page Hierarchy Support**: Maintain page hierarchies and relationships
- **Metadata Tracking**: Track sync state and changes with metadata
- **Command-line Interface**: Easy-to-use CLI for configuration and syncing

## Installation

### Linux/macOS

```bash
# Clone the repository
git clone https://github.com/yourusername/python-confluence-sync.git
cd python-confluence-sync

# Run the installation script
./install.sh
```

### Windows

```cmd
# Clone the repository
git clone https://github.com/yourusername/python-confluence-sync.git
cd python-confluence-sync

# Run the installation script
install.bat
```

## Usage

### Initial Configuration

### Set up your Confluence credentials. (1 set up only)

```bash
confluence-sync config credentials
```

### Configure a space to sync (interactive)

```bash
confluence-sync config spaces --add
```

### Configure a space to sync (with direct parameters)

```bash
confluence-sync config spaces --space-key SPACE_KEY --space-name "Space Name" --local-dir PATH
```

### Syncing Content

### Pull content from Confluence

```bash
confluence-sync pull --space SPACE_KEY
```

### Push content to Confluence

```bash
confluence-sync push --space SPACE_KEY
```

### Bidirectional sync (performs both pull and push operations)

```bash
confluence-sync sync --space SPACE_KEY
```

## Configuration

The tool uses a configuration file to store settings for Confluence spaces. You can configure spaces using the following commands:

### Add a new space configuration

```bash
confluence-sync config spaces --add
```

### List configured spaces

```bash
confluence-sync config spaces --list
```

### Remove a space configuration

```bash
confluence-sync config spaces --remove SPACE_KEY
```

### Confluence Result

When synced to Confluence, code blocks will be displayed as code blocks with syntax highlighting.

## Documentation

For detailed usage instructions, see the [User Guide](docs/user_guide.md).

For a concise summary of commands and features, check out the [Quick Reference Guide](docs/quick_reference.md).

## Project Status

This project is fully functional with all core features implemented. The tool supports bidirectional synchronization between Confluence spaces and local directories, with HTML-to-Markdown and Markdown-to-HTML conversion.

## License

N/A

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 