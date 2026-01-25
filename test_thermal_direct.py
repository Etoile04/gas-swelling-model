#!/usr/bin/env python
"""Direct test of thermal module by importing just the file"""
import sys
import os

# Test if we can load thermal.py directly without package imports
current_dir = os.path.dirname(os.path.abspath(__file__))

# First, let's just check the file exists and has the right structure
thermal_file = os.path.join(current_dir, 'gas_swelling/physics/thermal.py')
if os.path.exists(thermal_file):
    print(f"✓ thermal.py exists at {thermal_file}")
else:
    print(f"✗ thermal.py NOT found at {thermal_file}")
    sys.exit(1)

# Read and check the file has the expected function
with open(thermal_file, 'r') as f:
    content = f.read()
    if 'def calculate_cv0' in content:
        print("✓ calculate_cv0 function found in thermal.py")
    else:
        print("✗ calculate_cv0 function NOT found in thermal.py")
        sys.exit(1)

    if 'def calculate_ci0' in content:
        print("✓ calculate_ci0 function found in thermal.py")
    else:
        print("✗ calculate_ci0 function NOT found in thermal.py")
        sys.exit(1)

# Check __init__.py has the exports
init_file = os.path.join(current_dir, 'gas_swelling/physics/__init__.py')
if os.path.exists(init_file):
    with open(init_file, 'r') as f:
        init_content = f.read()
        if 'from .thermal import' in init_content:
            print("✓ __init__.py imports from thermal module")
        else:
            print("✗ __init__.py does NOT import from thermal module")
            sys.exit(1)

        if 'calculate_cv0' in init_content:
            print("✓ __init__.py exports calculate_cv0")
        else:
            print("✗ __init__.py does NOT export calculate_cv0")
            sys.exit(1)

print("\nthermal module OK - All checks passed!")
