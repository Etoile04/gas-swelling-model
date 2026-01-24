"""
CLI main entry point for 'python -m cli' command execution.

This module enables the CLI to be run as a Python module using:
    python -m cli run config.yaml
"""

from cli.main import cli

if __name__ == '__main__':
    cli()
