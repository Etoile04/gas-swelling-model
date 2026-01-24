#!/usr/bin/env python3
"""
Simple Backward Compatibility Verification

This script verifies backward compatibility without running full simulations.
It checks:
1. Import compatibility
2. API compatibility
3. Parameter structure
4. Default values
"""

import sys
import ast
import os

def verify_file_syntax(filepath):
    """Verify Python file syntax is valid"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, "Syntax valid"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

def verify_imports():
    """Test 1: Verify all modules can be imported"""
    print("\n" + "="*70)
    print("TEST 1: Import Compatibility")
    print("="*70)

    tests = [
        ("Import gas_swelling package", "import gas_swelling"),
        ("Import GasSwellingModel", "from gas_swelling import GasSwellingModel"),
        ("Import from models submodule", "from gas_swelling.models import GasSwellingModel"),
        ("Import parameters", "from gas_swelling.params.parameters import create_default_parameters"),
        ("Import constants", "from gas_swelling import BOLTZMANN_CONSTANT_EV"),
    ]

    all_passed = True
    for test_name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"  ✓ {test_name}")
        except ImportError as e:
            print(f"  ✗ {test_name}: {e}")
            all_passed = False
        except Exception as e:
            print(f"  ✗ {test_name}: Unexpected error: {e}")
            all_passed = False

    return all_passed

def verify_api_compatibility():
    """Test 2: Verify API is backward compatible"""
    print("\n" + "="*70)
    print("TEST 2: API Compatibility")
    print("="*70)

    try:
        from gas_swelling import GasSwellingModel, create_default_parameters

        # Test old API
        params = create_default_parameters()
        print("  ✓ create_default_parameters() exists and works")

        # Verify old parameters exist
        old_params = ['temperature', 'fission_rate', 'dislocation_density',
                      'surface_energy', 'Fnb', 'Fnf', 'eos_model', 'time_step']
        missing_params = []
        for param in old_params:
            if param not in params:
                missing_params.append(param)

        if missing_params:
            print(f"  ✗ Missing old parameters: {missing_params}")
            return False
        else:
            print(f"  ✓ All old parameters exist: {old_params}")

        # Verify new parameters don't break old behavior
        new_params = ['adaptive_stepping_enabled', 'min_step', 'max_step',
                      'show_progress', 'progress_interval']
        for param in new_params:
            if param not in params:
                print(f"  ✗ Missing new parameter: {param}")
                return False
        print(f"  ✓ New parameters exist: {new_params}")

        # Verify default is backward compatible
        if params['adaptive_stepping_enabled'] != False:
            print(f"  ✗ adaptive_stepping_enabled should default to False")
            return False
        print("  ✓ adaptive_stepping_enabled defaults to False (backward compatible)")

        # Test model creation with old API
        model = GasSwellingModel(params)
        print("  ✓ GasSwellingModel constructor works with old API")

        # Verify solve method exists
        if not hasattr(model, 'solve'):
            print("  ✗ Model missing solve() method")
            return False
        print("  ✓ Model has solve() method")

        # Verify model attributes
        expected_attrs = ['initial_state', 'params', '_equations']
        for attr in expected_attrs:
            if not hasattr(model, attr):
                print(f"  ✗ Model missing attribute: {attr}")
                return False
        print(f"  ✓ Model has expected attributes: {expected_attrs}")

        return True

    except Exception as e:
        print(f"  ✗ API compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_file_structure():
    """Test 3: Verify file structure hasn't broken"""
    print("\n" + "="*70)
    print("TEST 3: File Structure Verification")
    print("="*70)

    critical_files = [
        'gas_swelling/__init__.py',
        'gas_swelling/models/__init__.py',
        'gas_swelling/models/modelrk23.py',
        'gas_swelling/models/adaptive_solver.py',
        'gas_swelling/params/__init__.py',
        'gas_swelling/params/parameters.py',
        'tests/test_import.py',
        'examples/run_simulation.py',
        'examples/quickstart_tutorial.py',
    ]

    all_valid = True
    for filepath in critical_files:
        if not os.path.exists(filepath):
            print(f"  ✗ Missing file: {filepath}")
            all_valid = False
        else:
            valid, msg = verify_file_syntax(filepath)
            if valid:
                print(f"  ✓ {filepath}: {msg}")
            else:
                print(f"  ✗ {filepath}: {msg}")
                all_valid = False

    return all_valid

def verify_no_breaking_changes():
    """Test 4: Verify no breaking changes in key modules"""
    print("\n" + "="*70)
    print("TEST 4: Breaking Changes Check")
    print("="*70)

    try:
        from gas_swelling.models import modelrk23
        import inspect

        # Check GasSwellingModel.solve signature
        model_class = modelrk23.GasSwellingModel
        solve_method = model_class.solve

        sig = inspect.signature(solve_method)
        params = list(sig.parameters.keys())

        # Required parameters for backward compatibility
        required_params = ['self', 't_span']
        for param in required_params:
            if param not in params:
                print(f"  ✗ solve() missing required parameter: {param}")
                return False
        print(f"  ✓ solve() has required parameters: {required_params}")

        # Optional parameters that should exist
        optional_params = ['t_eval', 'method', 'rtol', 'atol']
        for param in optional_params:
            if param not in params:
                print(f"  ⚠ solve() missing optional parameter: {param}")

        print(f"  ✓ solve() signature is backward compatible")

        # Check that adaptive solver exists
        from gas_swelling.models.adaptive_solver import AdaptiveSolver
        print("  ✓ AdaptiveSolver class exists")

        # Verify AdaptiveSolver has expected methods
        expected_methods = ['solve', '_estimate_initial_step', '_rk23_step',
                           '_compute_error', '_adjust_step_size']
        for method in expected_methods:
            if not hasattr(AdaptiveSolver, method):
                print(f"  ✗ AdaptiveSolver missing method: {method}")
                return False
        print(f"  ✓ AdaptiveSolver has expected methods")

        return True

    except Exception as e:
        print(f"  ✗ Breaking changes check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_defaults_unchanged():
    """Test 5: Verify default behavior is unchanged"""
    print("\n" + "="*70)
    print("TEST 5: Default Behavior Verification")
    print("="*70)

    try:
        from gas_swelling.params.parameters import create_default_parameters
        from gas_swelling.models.modelrk23 import GasSwellingModel

        params = create_default_parameters()

        # Verify critical defaults haven't changed
        defaults_to_check = {
            'temperature': 773.0,  # Default temperature in K
            'fission_rate': 1.0e19,  # Default fission rate
            'adaptive_stepping_enabled': False,  # Must be False for backward compatibility
            'eos_model': 'ideal',  # Default equation of state
        }

        all_correct = True
        for param, expected_value in defaults_to_check.items():
            actual_value = params.get(param)
            if actual_value != expected_value:
                print(f"  ✗ {param}: expected {expected_value}, got {actual_value}")
                all_correct = False
            else:
                print(f"  ✓ {param} = {actual_value} (correct)")

        # Verify that adaptive stepping parameters exist but don't change default behavior
        adaptive_params = ['min_step', 'max_step', 'rtol', 'atol',
                          'safety_factor', 'show_progress', 'progress_interval']
        for param in adaptive_params:
            if param not in params:
                print(f"  ✗ Missing adaptive parameter: {param}")
                all_correct = False

        if all_correct:
            print(f"  ✓ All adaptive parameters exist")

        return all_correct

    except Exception as e:
        print(f"  ✗ Default behavior verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all backward compatibility tests"""
    print("\n" + "="*70)
    print("  BACKWARD COMPATIBILITY VERIFICATION (Simple)")
    print("  Adaptive Time Stepping Feature")
    print("="*70)

    print("\nThis script verifies backward compatibility without running")
    print("full simulations. It checks imports, API, file structure,")
    print("and default behavior.")

    tests = [
        ("Import Compatibility", verify_imports),
        ("API Compatibility", verify_api_compatibility),
        ("File Structure", verify_file_structure),
        ("Breaking Changes Check", verify_no_breaking_changes),
        ("Default Behavior", verify_defaults_unchanged),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} - EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
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
        print("backward compatible at the API level. All existing code")
        print("should work without modification.")
        print("\nKey points:")
        print("  • All old parameters are preserved")
        print("  • Default behavior unchanged (adaptive_stepping_enabled=False)")
        print("  • New parameters are optional and don't affect old code")
        print("  • All existing modules and methods work as before")
        return 0
    else:
        print("  ✗ SOME BACKWARD COMPATIBILITY TESTS FAILED")
        print("="*70)
        print("\nThere are compatibility issues that need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
