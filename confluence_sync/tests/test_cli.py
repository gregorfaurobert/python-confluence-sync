#!/usr/bin/env python3
"""
Test script for the CLI command.

This script tests the 'confluence sync --space OT --pull' command.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main function to test the CLI command."""
    # Run the CLI command
    cmd = ["confluence", "sync", "--space", "OT", "--pull"]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Command output:")
        print(result.stdout)
        
        if result.stderr:
            print("Command error output:")
            print(result.stderr)
        
        print("Command completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("Command output:")
        print(e.stdout)
        
        if e.stderr:
            print("Command error output:")
            print(e.stderr)
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 