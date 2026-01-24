#!/usr/bin/env python3
"""
Simple script to verify test imports and basic functionality
"""
import sys
sys.path.insert(0, '.')

print("Checking test imports...")

try:
    from gas_swelling.analysis.sensitivity import (
        ParameterRange,
        SensitivityAnalyzer,
        OATAnalyzer,
        OATResult,
        MorrisAnalyzer,
        MorrisResult,
        SobolAnalyzer,
        SobolResult,
        create_default_parameter_ranges
    )
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

try:
    from tests.test_sensitivity import test_oat_workflow
    print("✓ test_oat_workflow function found")
except ImportError as e:
    print(f"✗ Failed to import test function: {e}")
    sys.exit(1)

# Check that the function signature is correct
import inspect
sig = inspect.signature(test_oat_workflow)
print(f"✓ test_oat_workflow signature: {sig}")

# Create a simple parameter range to verify it works
try:
    pr = ParameterRange('temperature', 650, 750, nominal_value=700)
    print(f"✓ ParameterRange created: {pr.name}")
except Exception as e:
    print(f"✗ Failed to create ParameterRange: {e}")
    sys.exit(1)

# Check that the test file is parseable
import ast
with open('tests/test_sensitivity.py', 'r') as f:
    source = f.read()
    try:
        ast.parse(source)
        print("✓ test_sensitivity.py syntax is valid")
    except SyntaxError as e:
        print(f"✗ Syntax error in test file: {e}")
        sys.exit(1)

# Count the number of test functions
tree = ast.parse(source)
test_functions = [node.name for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
print(f"✓ Found {len(test_functions)} test functions")
print(f"  Workflow tests: {[t for t in test_functions if 'workflow' in t]}")

print("\nAll verification checks passed!")
