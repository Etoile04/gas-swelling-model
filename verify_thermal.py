#!/usr/bin/env python3
"""Verify thermal module can be imported"""
import sys
sys.path.insert(0, '.')

try:
    from gas_swelling.physics.thermal import calculate_cv0
    print('thermal module OK')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
