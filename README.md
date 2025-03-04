# Python Confluence Sync

A suite of Python scripts for syncing Confluence spaces with local directories. This tool allows you to work with Confluence content in your preferred text editor or IDE, using Markdown format, and sync changes back to Confluence.

## Features

- **Secure Credential Storage**: Safely store your Confluence API credentials with local encryption
- **Space Configuration Management**: Configure which Confluence spaces to sync with which local directories
- **Content Synchronization**:
  - Pull content from Confluence to local Markdown files
  - Push content from local Markdown files to Confluence
  - Bidirectional sync with conflict detection and resolution
- **Format Conversion**:
  - Convert Confluence HTML to Markdown when pulling content
  - Convert Markdown to Confluence HTML when pushing content
  - Support for Confluence-specific elements (info/note/warning panels, code blocks, etc.)
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

1. Set up your Confluence credentials:
   ```bash
   confluence-sync config credentials
   ```

2. Configure a space to sync:
   ```bash
   confluence-sync config spaces --add
   ```
   
   Or with direct parameters:
   ```bash
   confluence-sync config spaces --space-key SPACE_KEY --space-name "Space Name" --local-dir PATH
   ```

### Syncing Content

Pull content from Confluence:
```bash
confluence-sync pull --space SPACE_KEY
```

Push content to Confluence:
```bash
confluence-sync push --space SPACE_KEY
```

Bidirectional sync:
```bash
confluence-sync sync --space SPACE_KEY
```

## Documentation

For detailed usage instructions, see the [User Guide](docs/user_guide.md).

## Project Status

This project is fully functional with all core features implemented. The tool supports bidirectional synchronization between Confluence spaces and local directories, with HTML-to-Markdown and Markdown-to-HTML conversion.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 