#!/usr/bin/env python
"""Verification script for ParameterSweep class"""

try:
    from parameter_sweep import ParameterSweep
    from params.parameters import create_default_parameters

    params = create_default_parameters()
    sweep = ParameterSweep(params)
    print('Sweep created')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
