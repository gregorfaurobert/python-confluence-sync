"""
Entry point for running the package directly.

This allows running the package with `python -m confluence_sync`.
"""

from confluence_sync.cli.main import cli

if __name__ == "__main__":
    cli() 