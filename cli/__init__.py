"""
CLI Package for Gas Swelling Simulation

This package provides a command-line interface for running gas swelling
simulations without editing Python code. It supports configuration files,
multiple output formats, and progress tracking.

Modules:
    main: Main CLI entry point with click commands
    config: Configuration file loading and validation (YAML)
    output: Multi-format output exporters (CSV, JSON, HDF5, MATLAB)
    progress: Progress bar and status tracking during simulation

Usage:
    gas-swelling run config.yaml
    gas-swelling run config.yaml --output-dir results/ --format json
"""

__version__ = "0.1.0"
__author__ = "Gas Swelling Model Team"

# Export main CLI components for convenience
# These will be populated as modules are implemented in subsequent subtasks

__all__ = [
    "main",
    "config",
    "output",
    "progress",
]
