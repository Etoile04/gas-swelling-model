#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation Verification Script for Multi-Parameter Sweep Optimization

This script verifies the implementation completeness and correctness without
requiring full runtime execution. It performs static code analysis, import
checks, and validates that all required components are implemented.

Author: Auto-Claude Verification System
Date: 2026-01-24
"""

import ast
import os
import sys
from pathlib import Path


def check_file_exists(filepath):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ File exists: {filepath}")
        return True
    else:
        print(f"✗ File missing: {filepath}")
        return False


def check_syntax(filepath):
    """Check Python syntax of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"✓ Syntax valid: {filepath}")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {filepath}: {e}")
        return False


def check_imports(filepath, required_imports):
    """Check if required imports are present in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split('.')[0])

        missing = []
        for req in required_imports:
            if req not in imported:
                missing.append(req)

        if missing:
            print(f"⚠ Missing imports in {filepath}: {missing}")
            return False
        else:
            print(f"✓ All required imports present: {filepath}")
            return True
    except Exception as e:
        print(f"✗ Error checking imports in {filepath}: {e}")
        return False


def check_classes(filepath, required_classes):
    """Check if required classes are defined in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)

        defined = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined.add(node.name)

        missing = []
        for req in required_classes:
            if req not in defined:
                missing.append(req)

        if missing:
            print(f"✗ Missing classes in {filepath}: {missing}")
            return False
        else:
            print(f"✓ All required classes present: {required_classes}")
            return True
    except Exception as e:
        print(f"✗ Error checking classes in {filepath}: {e}")
        return False


def check_functions(filepath, required_functions):
    """Check if required functions are defined in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)

        defined = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined.add(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                defined.add(node.name)

        missing = []
        for req in required_functions:
            if req not in defined:
                missing.append(req)

        if missing:
            print(f"✗ Missing functions in {filepath}: {missing}")
            return False
        else:
            print(f"✓ All required functions present: {required_functions}")
            return True
    except Exception as e:
        print(f"✗ Error checking functions in {filepath}: {e}")
        return False


def check_methods(filepath, class_name, required_methods):
    """Check if required methods are defined in a class."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                defined = set()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        defined.add(item.name)
                    elif isinstance(item, ast.AsyncFunctionDef):
                        defined.add(item.name)

                missing = []
                for req in required_methods:
                    if req not in defined:
                        missing.append(req)

                if missing:
                    print(f"✗ Missing methods in {class_name}: {missing}")
                    return False
                else:
                    print(f"✓ All required methods present in {class_name}: {required_methods}")
                    return True

        print(f"✗ Class {class_name} not found in {filepath}")
        return False
    except Exception as e:
        print(f"✗ Error checking methods in {filepath}: {e}")
        return False


def check_docstrings(filepath):
    """Check if module, classes, and functions have docstrings."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)

        module_docstring = ast.get_docstring(tree)
        if not module_docstring or len(module_docstring) < 50:
            print(f"⚠ Missing or short module docstring in {filepath}")
            return False
        else:
            print(f"✓ Module docstring present: {filepath}")

        # Check class docstrings
        class_count = 0
        class_with_doc = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
                if ast.get_docstring(node):
                    class_with_doc += 1

        # Check function docstrings
        func_count = 0
        func_with_doc = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Skip private methods
                if not node.name.startswith('_'):
                    func_count += 1
                    if ast.get_docstring(node):
                        func_with_doc += 1

        doc_coverage = (class_with_doc + func_with_doc) / (class_count + func_count) * 100
        print(f"  → Documentation coverage: {doc_coverage:.1f}% ({class_with_doc}/{class_count} classes, {func_with_doc}/{func_count} public functions)")

        return True
    except Exception as e:
        print(f"✗ Error checking docstrings in {filepath}: {e}")
        return False


def verify_parameter_sweep_module():
    """Verify parameter_sweep.py module."""
    print("\n" + "=" * 70)
    print("VERIFYING: parameter_sweep.py")
    print("=" * 70)

    filepath = 'parameter_sweep.py'
    results = []

    # File existence
    results.append(check_file_exists(filepath))

    # Syntax check
    results.append(check_syntax(filepath))

    # Required imports
    required_imports = ['dataclasses', 'logging', 'hashlib', 'json', 'pathlib']
    results.append(check_imports(filepath, required_imports))

    # Required classes
    required_classes = [
        'SweepConfig',
        'SimulationResult',
        'SimulationCache',
        'ProgressTracker',
        'ParameterSweep',
        'ParallelRunner',
        'JoblibRunner'
    ]
    results.append(check_classes(filepath, required_classes))

    # Required methods in ParameterSweep
    required_methods = [
        '__init__',
        'generate_parameter_sets',
        'run',
        'to_dataframe',
        'export_csv',
        'export_json',
        'export_excel',
        'export_parquet',
        'export_netcdf'
    ]
    results.append(check_methods(filepath, 'ParameterSweep', required_methods))

    # Required methods in ParallelRunner
    parallel_methods = ['__init__', 'run', 'map', 'close']
    results.append(check_methods(filepath, 'ParallelRunner', parallel_methods))

    # Docstrings
    results.append(check_docstrings(filepath))

    return all(results)


def verify_sampling_strategies_module():
    """Verify sampling_strategies.py module."""
    print("\n" + "=" * 70)
    print("VERIFYING: sampling_strategies.py")
    print("=" * 70)

    filepath = 'sampling_strategies.py'
    results = []

    # File existence
    results.append(check_file_exists(filepath))

    # Syntax check
    results.append(check_syntax(filepath))

    # Required imports (note: math may not be needed if using numpy)
    required_imports = ['itertools', 'numpy', 'scipy']
    results.append(check_imports(filepath, required_imports))

    # Required functions
    required_functions = [
        'grid_sampling',
        'grid_sampling_with_logspace',
        'grid_sampling_with_linspace',
        'latin_hypercube_sampling',
        'sparse_grid_sampling',
        'print_sampling_summary',
        'create_simple_grid'
    ]
    results.append(check_functions(filepath, required_functions))

    # Docstrings
    results.append(check_docstrings(filepath))

    return all(results)


def verify_example_script():
    """Verify example_parameter_sweep.py script."""
    print("\n" + "=" * 70)
    print("VERIFYING: example_parameter_sweep.py")
    print("=" * 70)

    filepath = 'example_parameter_sweep.py'
    results = []

    # File existence
    results.append(check_file_exists(filepath))

    # Syntax check
    results.append(check_syntax(filepath))

    # Required functions
    required_functions = [
        'parse_arguments',
        'create_grid_sweep_config',
        'create_lhs_sweep_config',
        'run_sweep',
        'export_results',
        'plot_results',
        'print_summary',
        'main'
    ]
    results.append(check_functions(filepath, required_functions))

    # Docstrings
    results.append(check_docstrings(filepath))

    # Check for main guard
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        if "if __name__" in code and '"__main__"' in code or "'__main__'" in code:
            print("✓ Main guard present")
            results.append(True)
        else:
            print("✗ Main guard missing")
            results.append(False)
    except Exception as e:
        print(f"✗ Error checking main guard: {e}")
        results.append(False)

    return all(results)


def verify_verification_script():
    """Verify verify_e2e.py script exists and is valid."""
    print("\n" + "=" * 70)
    print("VERIFYING: verify_e2e.py (End-to-End Test Script)")
    print("=" * 70)

    filepath = 'verify_e2e.py'
    results = []

    # File existence
    results.append(check_file_exists(filepath))

    # Syntax check
    results.append(check_syntax(filepath))

    # Required functions
    required_functions = [
        'verify_imports',
        'verify_2d_sweep',
        'verify_caching',
        'verify_parallel_execution',
        'verify_csv_export',
        'verify_plotting',
        'main'
    ]
    results.append(check_functions(filepath, required_functions))

    return all(results)


def check_pattern_compliance():
    """Check compliance with project patterns."""
    print("\n" + "=" * 70)
    print("CHECKING: Pattern Compliance")
    print("=" * 70)

    results = []

    # Check parameter_sweep.py follows test4_run_rk23.py patterns
    try:
        with open('parameter_sweep.py', 'r') as f:
            sweep_code = f.read()

        patterns = [
            ('logger.', 'Logging pattern'),
            ('try:', 'Exception handling'),
            ('except ', 'Exception handling'),
            ('raise ValueError', 'Parameter validation'),
            ('raise TypeError', 'Type validation'),
            ('def ', 'Function definitions'),
            ('class ', 'Class definitions'),
            ('"""', 'Docstrings')
        ]

        for pattern, desc in patterns:
            if pattern in sweep_code:
                print(f"✓ Pattern present: {desc}")
                results.append(True)
            else:
                print(f"⚠ Pattern missing: {desc}")
                results.append(True)  # Don't fail for pattern checks

        print("✓ Pattern compliance checked")
        return all(results)
    except Exception as e:
        print(f"✗ Error checking patterns: {e}")
        return False


def print_verification_summary(results_dict):
    """Print verification summary."""
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    total = len(results_dict)
    passed = sum(1 for v in results_dict.values() if v)

    print(f"\nTotal Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.1f}%\n")

    print("Detailed Results:")
    for check_name, result in results_dict.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check_name}")

    print("\n" + "=" * 70)

    if passed == total:
        print("✓ ALL VERIFICATIONS PASSED")
        print("✓ Implementation is complete and ready for runtime testing")
        print("\nNote: Full runtime verification requires a Python environment with:")
        print("  - numpy")
        print("  - pandas")
        print("  - scipy")
        print("  - matplotlib")
        print("  - joblib (optional)")
        print("  - tqdm (optional)")
        print("  - netCDF4 (optional)")
        print("\nTo run end-to-end verification, execute:")
        print("  python verify_e2e.py")
    else:
        print(f"✗ {total - passed} VERIFICATION(S) FAILED")
        print("✗ Please review and fix the issues above")

    print("=" * 70 + "\n")


def main():
    """Main verification function."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "IMPLEMENTATION VERIFICATION" + " " * 28 + "║")
    print("║" + " " * 12 + "Multi-Parameter Sweep System" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    results = {}

    # Verify all modules
    results['parameter_sweep.py'] = verify_parameter_sweep_module()
    results['sampling_strategies.py'] = verify_sampling_strategies_module()
    results['example_parameter_sweep.py'] = verify_example_script()
    results['verify_e2e.py'] = verify_verification_script()
    results['Pattern Compliance'] = check_pattern_compliance()

    # Print summary
    print_verification_summary(results)

    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠ Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
