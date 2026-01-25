#!/usr/bin/env python3
"""Test script to verify refactored model import"""

import sys
sys.path.append('/Users/lwj04/Library/Python/3.9/lib/python/site-packages')
sys.path.insert(0, '.')

try:
    from gas_swelling.models.refactored_model import RefactoredGasSwellingModel
    print("refactored model OK")

    # Additional verification
    model = RefactoredGasSwellingModel()
    print(f"Model created: {model}")
    print(f"Initial state shape: {model.initial_state.shape}")
    print(f"Number of state variables: {len(model.initial_state)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
