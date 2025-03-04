#!/bin/bash

# Confluence Sync Installation Script

echo "=== Confluence Sync Installation ==="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Error: Python 3.8 or higher is required."
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "Python version $PYTHON_VERSION detected."
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

# Install package in development mode
echo "Installing Confluence Sync..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "Error: Failed to install package."
    exit 1
fi

echo
echo "=== Installation Complete ==="
echo
echo "To use Confluence Sync, activate the virtual environment:"
echo "  source venv/bin/activate"
echo
echo "Then run the CLI:"
echo "  confluence-sync --help"
echo
echo "Or:"
echo "  python -m confluence_sync --help"
echo
echo "To set up your Confluence credentials:"
echo "  confluence-sync config credentials"
echo
echo "To configure a Confluence space:"
echo "  confluence-sync config spaces --add" 