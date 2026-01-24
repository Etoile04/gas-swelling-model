#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualization Module Verification Script

This script verifies the visualization module structure and imports
without running full simulations. Useful for quick CI/CD checks.

Usage:
    python tests/verify_visualization_module.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Change to project root for file checks
import os
os.chdir(project_root)


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
        "__init__.py",
        "core.py",
        "evolution_plots.py",
        "parameter_sweeps.py",
        "comparison_plots.py",
        "utils.py",
    ]

    all_exist = True
    for filename in required_files:
        filepath = viz_path / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"  ✓ {filename} ({size_kb:.1f} KB)")
        else:
            print(f"  ✗ {filename} NOT FOUND")
            all_exist = False

    return all_exist


def check_imports():
    """Verify all imports work correctly"""
    print_section("Import Check")

    try:
        # Try importing the visualization module
        import gas_swelling.visualization as viz

        # Check if all expected items are in __all__
        expected_exports = [
            'GasSwellingPlotter',
            'create_standard_plotter',
            'plot_swelling_evolution',
            'plot_bubble_radius_evolution',
            'plot_gas_concentration_evolution',
            'plot_bubble_concentration_evolution',
            'plot_gas_atoms_evolution',
            'plot_gas_pressure_evolution',
            'plot_defect_concentration_evolution',
            'plot_released_gas_evolution',
            'plot_multi_panel_evolution',
            'plot_temperature_sweep',
            'plot_multi_param_temperature_sweep',
            'plot_parameter_sensitivity',
            'plot_arrhenius_analysis',
            'compare_bulk_interface',
            'plot_bulk_interface_ratio',
            'plot_gas_distribution_pie',
            'plot_gas_distribution_evolution',
            'plot_correlation_matrix',
            'plot_phase_comparison',
            'get_publication_style',
            'apply_publication_style',
            'get_color_palette',
            'save_figure',
        ]

        all_found = True
        for export_name in expected_exports:
            if hasattr(viz, export_name):
                print(f"  ✓ {export_name}")
            else:
                print(f"  ✗ {export_name} NOT FOUND")
                all_found = False

        return all_found

    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def check_function_signatures():
    """Check that all plotting functions have correct signatures"""
    print_section("Function Signature Check")

    try:
        from gas_swelling.visualization import (
            plot_swelling_evolution,
            plot_bubble_radius_evolution,
            plot_temperature_sweep,
            compare_bulk_interface,
        )
        import inspect

        # Check evolution plot signature
        sig = inspect.signature(plot_swelling_evolution)
        params = list(sig.parameters.keys())
        if 'result' in params and 'save_path' in params:
            print(f"  ✓ plot_swelling_evolution signature OK")
        else:
            print(f"  ✗ plot_swelling_evolution signature incorrect: {params}")
            return False

        # Check bubble radius plot signature
        sig = inspect.signature(plot_bubble_radius_evolution)
        params = list(sig.parameters.keys())
        if 'result' in params and 'save_path' in params:
            print(f"  ✓ plot_bubble_radius_evolution signature OK")
        else:
            print(f"  ✗ plot_bubble_radius_evolution signature incorrect: {params}")
            return False

        # Check temperature sweep signature
        sig = inspect.signature(plot_temperature_sweep)
        params = list(sig.parameters.keys())
        if 'temperatures' in params and 'swellings' in params:
            print(f"  ✓ plot_temperature_sweep signature OK")
        else:
            print(f"  ✗ plot_temperature_sweep signature incorrect: {params}")
            return False

        # Check comparison plot signature
        sig = inspect.signature(compare_bulk_interface)
        params = list(sig.parameters.keys())
        if 'result' in params and 'save_path' in params:
            print(f"  ✓ compare_bulk_interface signature OK")
        else:
            print(f"  ✗ compare_bulk_interface signature incorrect: {params}")
            return False

        return True

    except Exception as e:
        print(f"  ✗ Signature check failed: {e}")
        return False


def check_docstrings():
    """Verify all functions have docstrings"""
    print_section("Docstring Check")

    try:
        from gas_swelling.visualization.evolution_plots import plot_swelling_evolution
        from gas_swelling.visualization.parameter_sweeps import plot_temperature_sweep
        from gas_swelling.visualization.comparison_plots import compare_bulk_interface

        functions = [
            ("plot_swelling_evolution", plot_swelling_evolution),
            ("plot_temperature_sweep", plot_temperature_sweep),
            ("compare_bulk_interface", compare_bulk_interface),
        ]

        all_have_docs = True
        for name, func in functions:
            if func.__doc__ and len(func.__doc__) > 50:
                lines = func.__doc__.strip().split('\n')
                print(f"  ✓ {name} ({len(lines)} lines)")
            else:
                print(f"  ✗ {name} missing or short docstring")
                all_have_docs = False

        return all_have_docs

    except Exception as e:
        print(f"  ✗ Docstring check failed: {e}")
        return False


def check_export_formats():
    """Check that save_figure supports all required formats"""
    print_section("Export Format Support")

    try:
        from gas_swelling.visualization.utils import save_figure

        # Check if save_figure exists and is callable
        if not callable(save_figure):
            print("  ✗ save_figure is not callable")
            return False

        print("  ✓ save_figure function exists")

        # Check function signature supports format parameter
        import inspect
        sig = inspect.signature(save_figure)
        params = list(sig.parameters.keys())

        if 'fig' in params and 'path' in params and 'fmt' in params:
            print(f"  ✓ save_figure signature includes format parameter")
            return True
        else:
            print(f"  ✗ save_figure signature missing format parameter: {params}")
            return False

    except Exception as e:
        print(f"  ✗ Export format check failed: {e}")
        return False


def check_publication_styles():
    """Check that publication style presets are available"""
    print_section("Publication Style Presets")

    try:
        from gas_swelling.visualization.utils import get_publication_style

        styles = ['default', 'IEEE', 'Nature', 'presentation', 'poster', 'grayscale']
        all_found = True

        for style_name in styles:
            try:
                style_dict = get_publication_style(style_name)
                if isinstance(style_dict, dict) and 'figure.dpi' in style_dict:
                    dpi = style_dict['figure.dpi']
                    print(f"  ✓ {style_name} (DPI={dpi})")
                else:
                    print(f"  ✗ {style_name} invalid style dictionary")
                    all_found = False
            except Exception as e:
                print(f"  ✗ {style_name} failed: {e}")
                all_found = False

        return all_found

    except Exception as e:
        print(f"  ✗ Style check failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "=" * 70)
    print("  GAS SWELLING VISUALIZATION MODULE VERIFICATION")
    print("=" * 70)

    results = {
        "File Structure": check_file_structure(),
        "Imports": check_imports(),
        "Function Signatures": check_function_signatures(),
        "Docstrings": check_docstrings(),
        "Export Formats": check_export_formats(),
        "Publication Styles": check_publication_styles(),
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
    else:
        print("  ✗ SOME CHECKS FAILED")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
