#!/usr/bin/env python
"""Direct test of thermal module without package imports"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the thermal module directly, bypassing package __init__
import importlib.util
spec = importlib.util.spec_from_file_location(
    "thermal",
    "gas_swelling/physics/thermal.py"
)
thermal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thermal)

# Test the function
result = thermal.calculate_cv0(600, [1.034, 7.6e-4])
print(f"cv0 at 600K: {result:.6e}")
print("thermal module OK")
