#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for sampling_strategies module"""

from sampling_strategies import grid_sampling

# Test the grid sampling function
params = grid_sampling({'temperature': [300, 400], 'fission_rate': [1e19, 2e19]})
print(f'Grid samples: {len(params)}')

# Print the actual samples to verify
print('\nGenerated samples:')
for i, p in enumerate(params):
    print(f'  {i+1}. {p}')

# Verify the result
expected_count = 4
if len(params) == expected_count:
    print(f'\n✓ Test passed: Got expected {expected_count} samples')
else:
    print(f'\n✗ Test failed: Expected {expected_count} samples, got {len(params)}')
    exit(1)
