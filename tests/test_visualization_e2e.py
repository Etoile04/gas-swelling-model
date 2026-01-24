#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Test for Visualization Module

This script performs comprehensive testing of all plotting functions
in the gas_swelling.visualization module to verify:
- All plot types generate successfully
- PNG, PDF, and SVG exports work correctly
- Publication-quality styling is applied (DPI, fonts, colors)

Usage:
    python tests/test_visualization_e2e.py
    python tests/test_visualization_e2e.py --quick  # Run quick tests only
    python tests/test_visualization_e2e.py --format png  # Test single format
"""

import sys
import os
from pathlib import Path
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Import all visualization functions
from gas_swelling.visualization import (
    # Core classes
    GasSwellingPlotter,
    create_standard_plotter,

    # Evolution plots
    plot_swelling_evolution,
    plot_bubble_radius_evolution,
    plot_gas_concentration_evolution,
    plot_bubble_concentration_evolution,
    plot_gas_atoms_evolution,
    plot_gas_pressure_evolution,
    plot_defect_concentration_evolution,
    plot_released_gas_evolution,
    plot_multi_panel_evolution,

    # Parameter sweep plots
    plot_temperature_sweep,
    plot_multi_param_temperature_sweep,
    plot_parameter_sensitivity,
    plot_arrhenius_analysis,

    # Comparison plots
    compare_bulk_interface,
    plot_bulk_interface_ratio,
    plot_gas_distribution_pie,
    plot_gas_distribution_evolution,
    plot_correlation_matrix,
    plot_phase_comparison,

    # Utilities
    get_publication_style,
    save_figure,
)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name):
        self.passed += 1
        print(f"  ✓ {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"  TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"  {self.failed} tests failed:")
            for test_name, error in self.errors:
                print(f"    - {test_name}: {error}")
        print("=" * 70)
        return self.failed == 0


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_test_result(sim_time_days=50):
    """Create test simulation result data"""
    print("\nCreating test simulation data...")
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = sim_time_days * 24 * 3600  # Convert days to seconds
    t_eval = np.linspace(0, sim_time, 50)  # Fewer points for faster testing

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
    print(f"  Simulation completed: {sim_time_days} days, {len(t_eval)} time points")
    return result


def test_evolution_plots(result, formats, results):
    """Test all evolution plot functions"""
    print_section("Evolution Plots")

    tests = [
        ("plot_swelling_evolution",
         lambda: plot_swelling_evolution(result, save_path=None)),
        ("plot_bubble_radius_evolution",
         lambda: plot_bubble_radius_evolution(result, save_path=None)),
        ("plot_gas_concentration_evolution",
         lambda: plot_gas_concentration_evolution(result, save_path=None)),
        ("plot_bubble_concentration_evolution",
         lambda: plot_bubble_concentration_evolution(result, save_path=None)),
        ("plot_gas_atoms_evolution",
         lambda: plot_gas_atoms_evolution(result, save_path=None)),
        ("plot_gas_pressure_evolution",
         lambda: plot_gas_pressure_evolution(result, save_path=None)),
        ("plot_defect_concentration_evolution",
         lambda: plot_defect_concentration_evolution(result, save_path=None)),
        ("plot_released_gas_evolution",
         lambda: plot_released_gas_evolution(result, save_path=None)),
        ("plot_multi_panel_evolution",
         lambda: plot_multi_panel_evolution(result, save_path=None)),
    ]

    for test_name, test_func in tests:
        try:
            fig = test_func()
            if fig is not None:
                plt.close(fig)
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, "Returned None")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_parameter_sweep_plots(formats, results):
    """Test parameter sweep plot functions"""
    print_section("Parameter Sweep Plots")

    # Create temperature sweep data
    print("\nCreating temperature sweep data...")
    temperatures = np.array([600, 700, 800, 900])
    swellings = np.array([0.5, 2.3, 3.8, 2.1])

    tests = [
        ("plot_temperature_sweep",
         lambda: plot_temperature_sweep(temperatures, swellings, save_path=None)),
    ]

    # Test multi-param temperature sweep
    try:
        results_list = []
        for i, temp in enumerate([600, 700, 800]):
            params = create_default_parameters()
            params['temperature'] = temp
            model = GasSwellingModel(params)
            sim_time = 20 * 24 * 3600
            t_eval = np.linspace(0, sim_time, 20)
            result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

            V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
            V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
            swelling = (V_bubble_b + V_bubble_f) * 100

            results_list.append({
                'temperatures': np.full(20, temp),
                'swellings': swelling
            })

        tests.append((
            "plot_multi_param_temperature_sweep",
            lambda: plot_multi_param_temperature_sweep(
                results_list, param_name='Temperature', save_path=None
            )
        ))
    except Exception as e:
        results.add_fail("plot_multi_param_temperature_sweep_data", f"Data creation failed: {e}")

    # Test parameter sensitivity
    try:
        param_values = [0.5, 1.0, 2.0]
        final_values = [1.2, 2.5, 1.8]
        tests.append((
            "plot_parameter_sensitivity",
            lambda: plot_parameter_sensitivity(
                param_values, final_values, param_name='Dislocation Density Multiplier',
                save_path=None
            )
        ))
    except Exception as e:
        results.add_fail("plot_parameter_sensitivity", str(e))

    # Test Arrhenius analysis
    try:
        # Create Arrhenius data: ln(rate) vs 1/T
        T_kelvin = np.array([600, 700, 800, 900])
        rate = np.array([0.001, 0.01, 0.05, 0.02])  # Mock rates
        tests.append((
            "plot_arrhenius_analysis",
            lambda: plot_arrhenius_analysis(T_kelvin, rate, save_path=None)
        ))
    except Exception as e:
        results.add_fail("plot_arrhenius_analysis", str(e))

    for test_name, test_func in tests:
        try:
            fig = test_func()
            if fig is not None:
                plt.close(fig)
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, "Returned None")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_comparison_plots(result, formats, results):
    """Test comparison plot functions"""
    print_section("Comparison Plots")

    tests = [
        ("compare_bulk_interface",
         lambda: compare_bulk_interface(result, save_path=None)),
        ("plot_bulk_interface_ratio",
         lambda: plot_bulk_interface_ratio(result, save_path=None)),
        ("plot_gas_distribution_pie",
         lambda: plot_gas_distribution_pie(result, save_path=None)),
        ("plot_gas_distribution_evolution",
         lambda: plot_gas_distribution_evolution(result, save_path=None)),
        ("plot_correlation_matrix",
         lambda: plot_correlation_matrix(result, save_path=None)),
        ("plot_phase_comparison",
         lambda: plot_phase_comparison(result, variable='Rc', save_path=None)),
    ]

    for test_name, test_func in tests:
        try:
            fig = test_func()
            if fig is not None:
                plt.close(fig)
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, "Returned None")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_core_plotter(result, formats, results):
    """Test GasSwellingPlotter core class"""
    print_section("Core Plotter Class")

    tests = []

    # Test GasSwellingPlotter
    try:
        plotter = GasSwellingPlotter(result)
        tests.append((
            "GasSwellingPlotter instantiation",
            lambda: plotter.load_result(result)
        ))
    except Exception as e:
        results.add_fail("GasSwellingPlotter instantiation", str(e))

    # Test create_standard_plotter
    try:
        tests.append((
            "create_standard_plotter",
            lambda: create_standard_plotter(result)
        ))
    except Exception as e:
        results.add_fail("create_standard_plotter", str(e))

    # Test plot_all method
    try:
        plotter = GasSwellingPlotter(result)
        tests.append((
            "GasSwellingPlotter.plot_all",
            lambda: plotter.plot_all(save_path=None)
        ))
    except Exception as e:
        results.add_fail("GasSwellingPlotter.plot_all", str(e))

    for test_name, test_func in tests:
        try:
            result_obj = test_func()
            if result_obj is not None:
                if hasattr(result_obj, 'figure'):  # Figure object
                    plt.close(result_obj)
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, "Returned None")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_export_formats(result, formats, results):
    """Test export to different formats"""
    print_section("Export Format Testing")

    # Create test output directory
    test_output_dir = Path("test_output")
    test_output_dir.mkdir(exist_ok=True)

    for fmt in formats:
        try:
            filepath = test_output_dir / f"test_export.{fmt}"

            # Test using save_figure utility
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])
            ax.set_xlabel("Test X")
            ax.set_ylabel("Test Y")

            save_figure(fig, str(filepath), fmt, dpi=300)
            plt.close(fig)

            # Check file exists and has reasonable size
            if filepath.exists():
                size_kb = filepath.stat().st_size / 1024
                if size_kb > 1:  # At least 1KB
                    results.add_pass(f"Export to {fmt.upper()}")
                else:
                    results.add_fail(f"Export to {fmt.upper()}", f"File too small: {size_kb:.1f}KB")
            else:
                results.add_fail(f"Export to {fmt.upper()}", "File not created")

        except Exception as e:
            results.add_fail(f"Export to {fmt.upper()}", str(e))


def test_publication_quality(result, results):
    """Test publication-quality styling"""
    print_section("Publication-Quality Styling")

    tests = [
        ("get_publication_style",
         lambda: get_publication_style('default')),
        ("get_publication_style IEEE",
         lambda: get_publication_style('IEEE')),
        ("get_publication_style Nature",
         lambda: get_publication_style('Nature')),
    ]

    for test_name, test_func in tests:
        try:
            style_dict = test_func()
            if isinstance(style_dict, dict) and 'figure.dpi' in style_dict:
                # Verify DPI is 300 for publication quality
                if style_dict['figure.dpi'] == 300:
                    results.add_pass(test_name)
                else:
                    results.add_fail(test_name, f"DPI is {style_dict['figure.dpi']}, expected 300")
            else:
                results.add_fail(test_name, "Invalid style dictionary")
        except Exception as e:
            results.add_fail(test_name, str(e))

    # Test publication-quality plot generation
    try:
        fig = plot_swelling_evolution(
            result,
            style='IEEE',
            dpi=300,
            figsize=(6, 4),
            save_path=None
        )

        # Verify figure properties
        if fig is not None:
            fig_dpi = fig.get_dpi()
            fig_size = fig.get_size_inches()

            checks = []
            if abs(fig_dpi - 300) < 1:  # Allow small floating point differences
                checks.append("DPI=300")
            if abs(fig_size[0] - 6) < 0.1 and abs(fig_size[1] - 4) < 0.1:
                checks.append("figsize=(6,4)")

            if len(checks) == 2:
                results.add_pass("Publication-quality figure properties")
            else:
                results.add_fail("Publication-quality figure properties",
                               f"Missing: {', '.join(checks)}")

            plt.close(fig)
        else:
            results.add_fail("Publication-quality figure properties", "Figure is None")
    except Exception as e:
        results.add_fail("Publication-quality figure properties", str(e))


def test_utility_functions(results):
    """Test utility functions"""
    print_section("Utility Functions")

    # Test color palettes
    try:
        palette = get_color_palette('default')
        if isinstance(palette, list) and len(palette) > 0:
            results.add_pass("get_color_palette('default')")
        else:
            results.add_fail("get_color_palette('default')", "Invalid palette")
    except Exception as e:
        results.add_fail("get_color_palette('default')", str(e))

    try:
        palette = get_color_palette('bulk_interface')
        if isinstance(palette, list) and len(palette) == 2:
            results.add_pass("get_color_palette('bulk_interface')")
        else:
            results.add_fail("get_color_palette('bulk_interface')", f"Length: {len(palette) if isinstance(palette, list) else 'N/A'}")
    except Exception as e:
        results.add_fail("get_color_palette('bulk_interface')", str(e))


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='End-to-end visualization tests')
    parser.add_argument('--quick', '-q', action='store_true',
                        help='Run quick tests (skip time-intensive tests)')
    parser.add_argument('--format', '-f', type=str, default='all',
                        choices=['all', 'png', 'pdf', 'svg'],
                        help='Test specific export format')
    parser.add_argument('--no-sweep', action='store_true',
                        help='Skip temperature sweep tests (time-intensive)')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  GAS SWELLING VISUALIZATION - END-TO-END TEST SUITE")
    print("=" * 70)

    results = TestResults()

    # Determine formats to test
    if args.format == 'all':
        formats = ['png', 'pdf', 'svg']
    else:
        formats = [args.format]

    print(f"\nTesting export formats: {', '.join(formats).upper()}")

    # Create test data
    try:
        result = create_test_result(sim_time_days=50 if args.quick else 100)
    except Exception as e:
        print(f"\n✗ Failed to create test data: {e}")
        return 1

    # Run test suites
    try:
        test_utility_functions(results)
        test_evolution_plots(result, formats, results)
        test_core_plotter(result, formats, results)
        test_comparison_plots(result, formats, results)

        if not args.no_sweep:
            test_parameter_sweep_plots(formats, results)

        test_export_formats(result, formats, results)
        test_publication_quality(result, results)

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Print summary
    success = results.summary()

    # Cleanup test output directory if all tests passed
    if success:
        test_output_dir = Path("test_output")
        if test_output_dir.exists():
            import shutil
            shutil.rmtree(test_output_dir)
            print("\n✓ Cleaned up test output files")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
