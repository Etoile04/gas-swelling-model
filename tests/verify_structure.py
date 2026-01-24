#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Verification Script (No dependencies required)

This script verifies the visualization module structure without requiring
numpy, scipy, or matplotlib. Useful for basic checks in minimal environments.

Usage:
    python tests/verify_structure.py
"""

import sys
from pathlib import Path


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_file_structure():
    """Verify all visualization module files exist"""
    print_section("File Structure Check")

    viz_path = Path("gas_swelling/visualization")
    required_files = [
        ("__init__.py", 3),  # (filename, min_size_kb)
        ("core.py", 18),
        ("evolution_plots.py", 37),
        ("parameter_sweeps.py", 16),
        ("comparison_plots.py", 36),
        ("utils.py", 17),
    ]

    all_exist = True
    total_size = 0

    for filename, min_size_kb in required_files:
        filepath = viz_path / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            total_size += size_kb
            status = "✓" if size_kb >= min_size_kb else "⚠"
            print(f"  {status} {filename:30s} ({size_kb:6.1f} KB)")
        else:
            print(f"  ✗ {filename:30s} NOT FOUND")
            all_exist = False

    print(f"\n  Total: {total_size:.1f} KB")
    return all_exist


def check_function_count():
    """Count functions in each module"""
    print_section("Function Count")

    modules = [
        ("core.py", ("GasSwellingPlotter", "create_standard_plotter"), True),  # True = has class
        ("evolution_plots.py", (
            "plot_swelling_evolution",
            "plot_bubble_radius_evolution",
            "plot_gas_concentration_evolution",
            "plot_bubble_concentration_evolution",
            "plot_gas_atoms_evolution",
            "plot_gas_pressure_evolution",
            "plot_defect_concentration_evolution",
            "plot_released_gas_evolution",
            "plot_multi_panel_evolution",
        ), False),
        ("parameter_sweeps.py", (
            "plot_temperature_sweep",
            "plot_multi_param_temperature_sweep",
            "plot_parameter_sensitivity",
            "plot_arrhenius_analysis",
        ), False),
        ("comparison_plots.py", (
            "compare_bulk_interface",
            "plot_bulk_interface_ratio",
            "plot_gas_distribution_pie",
            "plot_gas_distribution_evolution",
            "plot_correlation_matrix",
            "plot_phase_comparison",
        ), False),
        ("utils.py", (
            "get_publication_style",
            "apply_publication_style",
            "get_color_palette",
            "save_figure",
            "convert_time_units",
            "convert_length_units",
            "calculate_burnup",
        ), False),
    ]

    all_found = True
    total_functions = 0

    for module_name, expected_functions, has_class in modules:
        filepath = Path("gas_swelling/visualization") / module_name
        if not filepath.exists():
            print(f"  ✗ {module_name} NOT FOUND")
            all_found = False
            continue

        content = filepath.read_text()
        found_count = 0
        for func in expected_functions:
            if has_class and func == "GasSwellingPlotter":
                # Check for class definition
                if f"class {func}" in content:
                    found_count += 1
            else:
                # Check for function definition
                if f"def {func}(" in content:
                    found_count += 1
        total_functions += found_count

        status = "✓" if found_count == len(expected_functions) else "⚠"
        print(f"  {status} {module_name:30s} {found_count:2d}/{len(expected_functions)} functions")

        if found_count < len(expected_functions):
            missing = [f for f in expected_functions if f"def {f}(" not in content]
            for func in missing:
                print(f"      - Missing: {func}")
            all_found = False

    print(f"\n  Total: {total_functions} functions found")
    return all_found


def check_docstrings():
    """Check for docstring presence"""
    print_section("Docstring Presence Check")

    modules = [
        "core.py",
        "evolution_plots.py",
        "parameter_sweeps.py",
        "comparison_plots.py",
        "utils.py",
    ]

    total_docstrings = 0

    for module_name in modules:
        filepath = Path("gas_swelling/visualization") / module_name
        if not filepath.exists():
            print(f"  ✗ {module_name} NOT FOUND")
            continue

        content = filepath.read_text()

        # Count triple-quoted strings (rough approximation for docstrings)
        docstring_count = content.count('"""')
        total_docstrings += docstring_count

        print(f"  ✓ {module_name:30s} ~{docstring_count//2:2d} docstrings")

    print(f"\n  Total: ~{total_docstrings//2} docstring sections")
    return True


def check_export_statement():
    """Check __init__.py exports"""
    print_section("Export Statement Check")

    init_path = Path("gas_swelling/visualization/__init__.py")
    if not init_path.exists():
        print("  ✗ __init__.py NOT FOUND")
        return False

    content = init_path.read_text()

    # Check for __all__ statement
    if "__all__ = [" in content:
        print("  ✓ __all__ list found")

        # Count exports
        start = content.find("__all__ = [")
        end = content.find("]", start)
        exports_section = content[start:end]

        export_count = exports_section.count("'")
        print(f"  ✓ {export_count//2} items in __all__")
    else:
        print("  ✗ __all__ list NOT FOUND")
        return False

    # Check for import statements
    import_count = content.count("from .")
    print(f"  ✓ {import_count} module import statements")

    return True


def check_readme():
    """Check for README file"""
    print_section("README Check")

    readme_path = Path("gas_swelling/visualization/README.md")
    if readme_path.exists():
        size_kb = readme_path.stat().st_size / 1024
        print(f"  ✓ README.md exists ({size_kb:.1f} KB)")

        # Check for key sections
        content = readme_path.read_text()
        sections = [
            "## Installation",
            "## Quick Start",
            "## Evolution Plots",
            "## Parameter Sweeps",
            "## Comparison Plots",
        ]

        found = sum(1 for section in sections if section in content)
        print(f"  ✓ {found}/{len(sections)} key sections found")

        return found >= 3
    else:
        print("  ✗ README.md NOT FOUND")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "=" * 70)
    print("  VISUALIZATION MODULE STRUCTURE VERIFICATION")
    print("=" * 70)

    results = {
        "File Structure": check_file_structure(),
        "Function Count": check_function_count(),
        "Docstrings": check_docstrings(),
        "Export Statements": check_export_statement(),
        "README": check_readme(),
    }

    # Print summary
    print_section("VERIFICATION SUMMARY")

    all_passed = True
    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ ALL CHECKS PASSED")
        print("\nThe visualization module structure is complete!")
    else:
        print("  ✗ SOME CHECKS FAILED")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
