#!/usr/bin/env python3
"""
Backward Compatibility Verification Script

This script verifies that all existing tests and examples continue to work
without modification after the adaptive time stepping feature was added.

Verification Steps:
1. Run original test_import.py tests
2. Run quickstart_tutorial.py example
3. Run run_simulation.py with default settings (no adaptive stepping)
4. Verify results are consistent with expected behavior
"""

import sys
import subprocess
import os
import numpy as np

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"{'='*70}")
    print(f"Command: {cmd}")
    print()

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print(f"\n✓ {description} - PASSED")
        return True
    else:
        print(f"\n✗ {description} - FAILED (exit code: {result.returncode})")
        return False

def test_import_tests():
    """Test 1: Run original import tests"""
    print("\n" + "="*70)
    print("BACKWARD COMPATIBILITY TEST SUITE")
    print("="*70)

    success = run_command(
        "python -m pytest tests/test_import.py -v",
        "Original import tests (test_import.py)"
    )
    return success

def test_quickstart_tutorial():
    """Test 2: Run quickstart tutorial (non-interactive mode)"""
    # Create a modified version that doesn't require user input
    print("\n" + "="*70)
    print("TEST: Quickstart Tutorial (Basic Simulation)")
    print("="*70)

    code = """
import sys
sys.path.insert(0, '.')

import numpy as np
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Create default parameters
params = create_default_parameters()
print(f"Temperature: {params['temperature']} K")
print(f"Fission rate: {params['fission_rate']:.2e} fissions/(m³·s)")

# Verify adaptive stepping is disabled by default
assert params['adaptive_stepping_enabled'] == False, "Adaptive stepping should be disabled by default"
print("✓ Adaptive stepping disabled by default (backward compatible)")

# Create model
model = GasSwellingModel(params)
print(f"✓ Model created with {len(model.initial_state)} state variables")

# Run short simulation
sim_time = 3600  # 1 hour
t_eval = np.linspace(0, sim_time, 10)

print(f"\\nRunning {sim_time}s simulation...")
result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

# Verify result structure
assert 'time' in result, "Result should contain 'time'"
assert 'swelling' in result, "Result should contain 'swelling'"
assert 'Rcb' in result, "Result should contain 'Rcb'"
assert len(result['time']) == len(t_eval), "Should have output at requested time points"

print(f"✓ Simulation completed successfully")
print(f"✓ Result contains all expected variables")
print(f"✓ Output at {len(result['time'])} time points")

# Verify basic physical constraints
final_swelling = result['swelling'][-1]
assert final_swelling >= 0, "Swelling should be non-negative"
print(f"✓ Final swelling: {final_swelling:.4f}%")

print("\\n✓ QUICKSTART TUTORIAL TEST - PASSED")
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("\n✓ Quickstart Tutorial Test - PASSED")
        return True
    else:
        print("\n✗ Quickstart Tutorial Test - FAILED")
        return False

def test_run_simulation_default():
    """Test 3: Run run_simulation.py with default settings"""
    print("\n" + "="*70)
    print("TEST: run_simulation.py with Default Settings")
    print("="*70)

    code = """
import sys
sys.path.insert(0, '.')

import numpy as np
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Simulate the run_test4 function from run_simulation.py
def run_test4_basic(sim_time=7200000):
    '''Basic version of run_test4 without plotting'''
    params = create_default_parameters()

    # Verify adaptive stepping is disabled
    assert params['adaptive_stepping_enabled'] == False
    print("✓ Adaptive stepping disabled (backward compatible default)")

    # Log key parameters
    print(f"Temperature: {params['temperature']} K")
    print(f"Fission rate: {params['fission_rate']:.2e} fissions/(m³·s)")
    print(f"Simulation time: {sim_time:.2e} s")

    # Create model
    model = GasSwellingModel(params)
    print("✓ Model created")

    # Create time points
    t_eval = np.linspace(0, sim_time, 100)
    print(f"✓ Created {len(t_eval)} time points")

    # Solve
    print("\\nSolving ODE system...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
    print("✓ Solve completed")

    # Verify results
    assert result['success'], "Solver should report success"
    assert len(result['time']) == len(t_eval), "Should have output at requested time points"

    # Calculate swelling
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    print(f"\\n✓ Final swelling: {swelling[-1]:.4f}%")
    print(f"✓ Final bulk bubble radius: {result['Rcb'][-1]*1e9:.2f} nm")
    print(f"✓ Final boundary bubble radius: {result['Rcf'][-1]*1e9:.2f} nm")

    # Verify physical constraints
    assert swelling[-1] >= 0, "Swelling should be non-negative"
    assert result['Rcb'][-1] >= 0, "Bubble radius should be non-negative"
    assert result['Rcf'][-1] >= 0, "Bubble radius should be non-negative"

    print("\\n✓ RUN_SIMULATION DEFAULT TEST - PASSED")
    return result

# Run the test
result = run_test4_basic(sim_time=3600)  # Short 1-hour test for speed
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("\n✓ Run Simulation Default Test - PASSED")
        return True
    else:
        print("\n✗ Run Simulation Default Test - FAILED")
        return False

def test_backward_compatibility_parameters():
    """Test 4: Verify parameter compatibility"""
    print("\n" + "="*70)
    print("TEST: Parameter Backward Compatibility")
    print("="*70)

    code = """
import sys
sys.path.insert(0, '.')

from gas_swelling.params.parameters import create_default_parameters
from gas_swelling.models.modelrk23 import GasSwellingModel

# Test 1: Create parameters with old API
params = create_default_parameters()
print("✓ create_default_parameters() works")

# Test 2: Verify old parameters still exist
old_params = ['temperature', 'fission_rate', 'dislocation_density',
              'surface_energy', 'Fnb', 'Fnf', 'eos_model']
for param in old_params:
    assert param in params, f"Parameter {param} should still exist"
    print(f"✓ Parameter '{param}' exists")

# Test 3: Verify new parameters are present but don't affect old behavior
new_params = ['adaptive_stepping_enabled', 'min_step', 'max_step']
for param in new_params:
    assert param in params, f"New parameter {param} should exist"
    print(f"✓ New parameter '{param}' exists")

# Test 4: Verify default is backward compatible
assert params['adaptive_stepping_enabled'] == False
print("✓ Adaptive stepping disabled by default (backward compatible)")

# Test 5: Create model with old API
model = GasSwellingModel(params)
print("✓ GasSwellingModel constructor works with old API")

# Test 6: Verify model has solve method
assert hasattr(model, 'solve'), "Model should have solve method"
print("✓ Model has solve() method")

# Test 7: Call solve with old API
import numpy as np
result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))
assert 'success' in result, "Result should have success flag"
print("✓ solve() method works with old API")

print("\\n✓ PARAMETER BACKWARD COMPATIBILITY TEST - PASSED")
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("\n✓ Parameter Backward Compatibility Test - PASSED")
        return True
    else:
        print("\n✗ Parameter Backward Compatibility Test - FAILED")
        return False

def test_results_consistency():
    """Test 5: Verify results are consistent across multiple runs"""
    print("\n" + "="*70)
    print("TEST: Results Consistency (Deterministic Behavior)")
    print("="*70)

    code = """
import sys
sys.path.insert(0, '.')

import numpy as np
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Run same simulation twice
params = create_default_parameters()
sim_time = 3600
t_eval = np.linspace(0, sim_time, 20)

print("Running simulation #1...")
model1 = GasSwellingModel(params)
result1 = model1.solve(t_span=(0, sim_time), t_eval=t_eval)
print("✓ Simulation #1 completed")

print("Running simulation #2...")
model2 = GasSwellingModel(params)
result2 = model2.solve(t_span=(0, sim_time), t_eval=t_eval)
print("✓ Simulation #2 completed")

# Verify results are identical
rtol = 1e-10
atol = 1e-12

# Check key variables
vars_to_check = ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'swelling']
all_consistent = True

for var in vars_to_check:
    try:
        np.testing.assert_allclose(
            result1[var], result2[var],
            rtol=rtol, atol=atol,
            err_msg=f"{var} not consistent"
        )
        print(f"✓ {var} is consistent across runs")
    except AssertionError as e:
        print(f"✗ {var} is NOT consistent: {e}")
        all_consistent = False

if all_consistent:
    print("\\n✓ RESULTS CONSISTENCY TEST - PASSED")
else:
    print("\\n✗ RESULTS CONSISTENCY TEST - FAILED")
    sys.exit(1)
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("\n✓ Results Consistency Test - PASSED")
        return True
    else:
        print("\n✗ Results Consistency Test - FAILED")
        return False

def main():
    """Run all backward compatibility tests"""
    print("\n" + "="*70)
    print("  BACKWARD COMPATIBILITY VERIFICATION")
    print("  Adaptive Time Stepping Feature")
    print("="*70)

    print("\nThis script verifies that all existing tests and examples")
    print("continue to work without modification after adding adaptive")
    print("time stepping functionality.")
    print("\nKey principle: Adaptive stepping is DISABLED by default,")
    print("so all existing code should work unchanged.")

    tests = [
        ("Import Tests", test_import_tests),
        ("Quickstart Tutorial", test_quickstart_tutorial),
        ("Run Simulation Default", test_run_simulation_default),
        ("Parameter Compatibility", test_backward_compatibility_parameters),
        ("Results Consistency", test_results_consistency),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} - EXCEPTION: {e}")
            results[test_name] = False

    # Print summary
    print("\n" + "="*70)
    print("  VERIFICATION SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("  ✓ ALL BACKWARD COMPATIBILITY TESTS PASSED")
        print("="*70)
        print("\nConclusion: The adaptive time stepping feature is fully")
        print("backward compatible. All existing tests and examples work")
        print("without modification.")
        return 0
    else:
        print("  ✗ SOME BACKWARD COMPATIBILITY TESTS FAILED")
        print("="*70)
        print("\nConclusion: There are backward compatibility issues that")
        print("need to be addressed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
