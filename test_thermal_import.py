#!/usr/bin/env python
"""Test script to verify thermal module imports correctly"""
import sys
sys.path.insert(0, '.')

from gas_swelling.physics.thermal import calculate_cv0
print('thermal module OK')
