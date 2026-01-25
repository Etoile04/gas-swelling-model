#!/usr/bin/env python3
"""Verify thermal module with explicit path"""
import sys
import os

# Add user site-packages to path
user_site = os.path.expanduser('~/Library/Python/3.9/lib/python/site-packages')
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

# Add current directory to path
sys.path.insert(0, '.')

print("Testing import...")
try:
    import numpy
    print(f"✓ numpy version: {numpy.__version__}")
except ImportError as e:
    print(f"✗ numpy not available: {e}")
    sys.exit(1)

try:
    from gas_swelling.physics.thermal import calculate_cv0
    print('✓ thermal module OK')
except Exception as e:
    print(f'✗ Error importing thermal module: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
