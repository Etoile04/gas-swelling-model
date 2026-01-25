"""
Pytest configuration for docstring tests

This file configures pytest to properly import local modules and dependencies.
"""

import sys
import os

# Add parent directory to path to import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
