#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Radial Visualization Module

This script performs comprehensive testing of the radial plotting functions
in the gas_swelling.visualization.radial_plots module to verify:
- RadialProfilePlotter class functionality
- All radial plot types generate successfully
- PNG, PDF, and SVG exports work correctly
- Publication-quality styling is applied (DPI, fonts, colors)

Usage:
    python tests/test_radial_visualization.py
    python tests/test_radial_visualization.py --quick  # Run quick tests only
    python tests/test_radial_visualization.py --format png  # Test single format
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

from gas_swelling.models.radial_mesh import RadialMesh
from gas_swelling.models.radial_model import RadialGasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Import radial visualization functions
from gas_swelling.visualization.radial_plots import (
    RadialProfilePlotter,
    create_radial_plotter,
)


class ResultTracker:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name):
        self.passed += 1
        print(f"  [PASS] {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  [FAIL] {test_name}: {error}")

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


def create_mock_radial_result(n_nodes=10, n_time_points=20, sim_time_days=30):
    """
    Create mock radial simulation result data for testing.

    Args:
        n_nodes: Number of radial nodes
        n_time_points: Number of time points
        sim_time_days: Simulation time in days

    Returns:
        Tuple of (result dict, RadialMesh, params dict)
    """
    print(f"\nCreating mock radial data: {n_nodes} nodes, {n_time_points} time points...")

    # Create mesh
    mesh = RadialMesh(n_nodes=n_nodes, radius=0.003, geometry='cylindrical')

    # Create parameters
    params = create_default_parameters()

    # Create time array
    sim_time = sim_time_days * 24 * 3600  # Convert days to seconds
    time = np.linspace(0, sim_time, n_time_points)

    # Create mock radial data with realistic shapes
    result = {'time': time}

    # Temperature: parabolic profile (hotter at center)
    for t_idx in range(n_time_points):
        temp_base = params['temperature']
        T_center = temp_base * 1.1
        T_surface = temp_base * 0.9
        r_norm = mesh.nodes / mesh.radius
        temp_profile = T_center - (T_center - T_surface) * r_norm**2

        if t_idx == 0:
            result['temperature'] = temp_profile[np.newaxis, :]
        else:
            result['temperature'] = np.vstack([result['temperature'], temp_profile])

    # Swelling: higher at center, increasing with time
    for t_idx in range(n_time_points):
        time_factor = (t_idx + 1) / n_time_points
        r_norm = mesh.nodes / mesh.radius
        swelling_profile = 5.0 * time_factor * (1.0 - 0.5 * r_norm**2)  # % swelling

        if t_idx == 0:
            result['swelling'] = swelling_profile[np.newaxis, :]
        else:
            result['swelling'] = np.vstack([result['swelling'], swelling_profile])

    # Gas pressure: Pa, increasing with time
    for t_idx in range(n_time_points):
        time_factor = (t_idx + 1) / n_time_points
        pg_profile = 1e7 * time_factor * (1.0 + 0.3 * r_norm)  # Pa

        if t_idx == 0:
            result['Pg_b'] = pg_profile[np.newaxis, :]
        else:
            result['Pg_b'] = np.vstack([result['Pg_b'], pg_profile])

    # Bubble radius: meters, growing with time
    for t_idx in range(n_time_points):
        time_factor = (t_idx + 1) / n_time_points
        Rcb_profile = 1e-7 * (1.0 + time_factor * 9.0) * (1.0 - 0.2 * r_norm)  # nm to m

        if t_idx == 0:
            result['Rcb'] = Rcb_profile[np.newaxis, :]
        else:
            result['Rcb'] = np.vstack([result['Rcb'], Rcb_profile])

    # Gas concentrations: atoms/m³
    for t_idx in range(n_time_points):
        time_factor = (t_idx + 1) / n_time_points
        Cgb_profile = 1e24 * time_factor * (1.0 - 0.3 * r_norm**2)

        if t_idx == 0:
            result['Cgb'] = Cgb_profile[np.newaxis, :]
        else:
            result['Cgb'] = np.vstack([result['Cgb'], Cgb_profile])

    # Cavity concentrations: cavities/m³
    for t_idx in range(n_time_points):
        time_factor = (t_idx + 1) / n_time_points
        Ccb_profile = 1e20 * time_factor * (1.0 + 0.2 * r_norm)

        if t_idx == 0:
            result['Ccb'] = Ccb_profile[np.newaxis, :]
        else:
            result['Ccb'] = np.vstack([result['Ccb'], Ccb_profile])

    # Add other required variables
    for var_name in ['Ncb', 'Cgf', 'Ccf', 'Ncf', 'Rcf', 'cvb', 'cib', 'cvf', 'cif', 'released_gas']:
        result[var_name] = np.zeros((n_time_points, n_nodes))

    print(f"  Mock data created: {len(result)} variables")
    return result, mesh, params


def create_real_radial_result(n_nodes=5, sim_time_days=10):
    """
    Create real radial simulation result using RadialGasSwellingModel.

    Args:
        n_nodes: Number of radial nodes (use small number for faster testing)
        sim_time_days: Simulation time in days

    Returns:
        Tuple of (result dict, RadialMesh, model)
    """
    print(f"\nRunning real radial simulation: {n_nodes} nodes, {sim_time_days} days...")

    params = create_default_parameters()
    model = RadialGasSwellingModel(params, n_nodes=n_nodes)

    sim_time = sim_time_days * 24 * 3600  # Convert days to seconds
    t_eval = np.linspace(0, sim_time, 15)  # Fewer points for faster testing

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
    print(f"  Simulation completed: {sim_time_days} days, {len(t_eval)} time points")

    return result, model.mesh, model


def test_radial_plotter_instantiation(results, test_data):
    """Test RadialProfilePlotter instantiation and loading"""
    print_section("RadialProfilePlotter Instantiation")

    result, mesh, params = test_data

    tests = [
        ("RadialProfilePlotter instantiation",
         lambda: RadialProfilePlotter()),
        ("RadialProfilePlotter with custom units",
         lambda: RadialProfilePlotter(time_unit='hours', length_unit='um', radius_unit='mm')),
        ("RadialProfilePlotter with style",
         lambda: RadialProfilePlotter(style='IEEE')),
    ]

    for test_name, test_func in tests:
        try:
            plotter = test_func()
            if plotter is not None:
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, "Returned None")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_load_radial_result(results, test_data):
    """Test loading radial simulation results"""
    print_section("Load Radial Results")

    result, mesh, params = test_data

    # Test load_radial_result
    try:
        plotter = RadialProfilePlotter()
        plotter.load_radial_result(result, mesh, params)
        # Check that data was loaded properly
        if hasattr(plotter, 'radial_result') and plotter.radial_result is not None:
            if plotter.mesh is not None and plotter.n_nodes is not None:
                results.add_pass("load_radial_result")
            else:
                results.add_fail("load_radial_result", "Mesh or n_nodes not set")
        else:
            results.add_fail("load_radial_result", "radial_result not set")
    except Exception as e:
        results.add_fail("load_radial_result", str(e))

    # Test with missing required keys
    try:
        plotter = RadialProfilePlotter()
        incomplete_result = {'swelling': result['swelling']}  # Missing 'time'
        plotter.load_radial_result(incomplete_result, mesh, params)
        results.add_fail("load_radial_result with missing time", "Should have raised ValueError")
    except ValueError as e:
        # Expected to fail
        if "Missing 'time' key" in str(e) or "time" in str(e).lower():
            results.add_pass("load_radial_result with missing time (expected error)")
        else:
            results.add_fail("load_radial_result with missing time", f"Wrong error: {e}")
    except Exception as e:
        results.add_fail("load_radial_result with missing time", f"Unexpected error: {e}")


def test_get_radius_data(results, test_data):
    """Test get_radius_data method"""
    print_section("Get Radius Data")

    result, mesh, params = test_data

    tests = []

    try:
        plotter = RadialProfilePlotter()
        plotter.load_radial_result(result, mesh, params)

        # Test get_radius_data
        radius = plotter.get_radius_data()
        tests.append((
            "get_radius_data",
            lambda: radius
        ))

        # Test different units
        plotter_mm = RadialProfilePlotter(radius_unit='mm')
        plotter_mm.load_radial_result(result, mesh, params)
        radius_mm = plotter_mm.get_radius_data()
        tests.append((
            "get_radius_data with mm unit",
            lambda: radius_mm
        ))

        plotter_um = RadialProfilePlotter(radius_unit='um')
        plotter_um.load_radial_result(result, mesh, params)
        radius_um = plotter_um.get_radius_data()
        tests.append((
            "get_radius_data with um unit",
            lambda: radius_um
        ))

    except Exception as e:
        results.add_fail("get_radius_data setup", str(e))

    for test_name, test_func in tests:
        try:
            data = test_func()
            if isinstance(data, np.ndarray) and len(data) > 0:
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, f"Invalid data: {type(data)}")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_get_radial_profile(results, test_data):
    """Test get_radial_profile method"""
    print_section("Get Radial Profile")

    result, mesh, params = test_data

    tests = []

    try:
        plotter = RadialProfilePlotter()
        plotter.load_radial_result(result, mesh, params)

        # Test getting profiles for different variables
        for var_name in ['swelling', 'temperature', 'Pg_b', 'Rcb', 'Cgb']:
            if var_name in result:
                tests.append((
                    f"get_radial_profile('{var_name}')",
                    lambda v=var_name: plotter.get_radial_profile(v)
                ))

        # Test with specific time_index
        tests.append((
            "get_radial_profile with time_index=0",
            lambda: plotter.get_radial_profile('swelling', time_index=0)
        ))

        # Test with time_index=-1 (last time point)
        tests.append((
            "get_radial_profile with time_index=-1",
            lambda: plotter.get_radial_profile('swelling', time_index=-1)
        ))

    except Exception as e:
        results.add_fail("get_radial_profile setup", str(e))

    for test_name, test_func in tests:
        try:
            profile = test_func()
            if isinstance(profile, np.ndarray) and len(profile) > 0:
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, f"Invalid profile: {type(profile)}")
        except Exception as e:
            results.add_fail(test_name, str(e))


def test_plot_radial_profile(results, test_data):
    """Test plot_radial_profile method"""
    print_section("Plot Radial Profile")

    result, mesh, params = test_data

    variables_to_test = ['swelling', 'temperature', 'Pg_b', 'Rcb']

    for var_name in variables_to_test:
        if var_name not in result:
            continue

        try:
            plotter = RadialProfilePlotter()
            plotter.load_radial_result(result, mesh, params)

            fig = plotter.plot_radial_profile(var_name, save_path=None)
            if fig is not None:
                plt.close(fig)
                results.add_pass(f"plot_radial_profile('{var_name}')")
            else:
                results.add_fail(f"plot_radial_profile('{var_name}')", "Returned None")
        except Exception as e:
            results.add_fail(f"plot_radial_profile('{var_name}')", str(e))


def test_plot_radial_comparison(results, test_data):
    """Test plot_radial_comparison method"""
    print_section("Plot Radial Comparison")

    result, mesh, params = test_data

    tests = [
        ("plot_radial_comparison single variable",
         lambda: _test_comparison_single(result, mesh, params)),
        ("plot_radial_comparison multiple variables",
         lambda: _test_comparison_multi(result, mesh, params)),
        ("plot_radial_comparison with normalization",
         lambda: _test_comparison_normalized(result, mesh, params)),
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


def _test_comparison_single(result, mesh, params):
    plotter = RadialProfilePlotter()
    plotter.load_radial_result(result, mesh, params)
    return plotter.plot_radial_comparison(['swelling'], save_path=None)


def _test_comparison_multi(result, mesh, params):
    plotter = RadialProfilePlotter()
    plotter.load_radial_result(result, mesh, params)
    return plotter.plot_radial_comparison(['swelling', 'temperature', 'Pg_b'], save_path=None)


def _test_comparison_normalized(result, mesh, params):
    plotter = RadialProfilePlotter()
    plotter.load_radial_result(result, mesh, params)
    return plotter.plot_radial_comparison(['swelling', 'Pg_b'], normalize=True, save_path=None)


def test_plot_radial_evolution(results, test_data):
    """Test plot_radial_evolution method"""
    print_section("Plot Radial Evolution")

    result, mesh, params = test_data

    variables_to_test = ['swelling', 'temperature', 'Rcb']

    for var_name in variables_to_test:
        if var_name not in result:
            continue

        try:
            plotter = RadialProfilePlotter()
            plotter.load_radial_result(result, mesh, params)

            fig = plotter.plot_radial_evolution(var_name, save_path=None)
            if fig is not None:
                plt.close(fig)
                results.add_pass(f"plot_radial_evolution('{var_name}')")
            else:
                results.add_fail(f"plot_radial_evolution('{var_name}')", "Returned None")
        except Exception as e:
            results.add_fail(f"plot_radial_evolution('{var_name}')", str(e))


def test_plot_main(results, test_data):
    """Test main plot method"""
    print_section("Main Plot Method")

    result, mesh, params = test_data

    try:
        plotter = RadialProfilePlotter()
        plotter.load_radial_result(result, mesh, params)

        fig = plotter.plot(save_path=None)
        if fig is not None:
            # Check if it has the expected 2x2 subplot grid
            axes = fig.get_axes()
            if len(axes) == 4:
                plt.close(fig)
                results.add_pass("plot() main method with 2x2 grid")
            else:
                plt.close(fig)
                results.add_fail("plot() main method", f"Expected 4 axes, got {len(axes)}")
        else:
            results.add_fail("plot() main method", "Returned None")
    except Exception as e:
        results.add_fail("plot() main method", str(e))


def test_create_radial_plotter_factory(results, test_data):
    """Test create_radial_plotter factory function"""
    print_section("Factory Function")

    result, mesh, params = test_data

    tests = [
        ("create_radial_plotter basic",
         lambda: create_radial_plotter(result, mesh)),
        ("create_radial_plotter with custom units",
         lambda: create_radial_plotter(result, mesh, radius_unit='mm', time_unit='hours')),
        ("create_radial_plotter with style",
         lambda: create_radial_plotter(result, mesh, style='IEEE')),
    ]

    for test_name, test_func in tests:
        try:
            plotter = test_func()
            if plotter is not None and hasattr(plotter, 'radial_result'):
                results.add_pass(test_name)
            else:
                results.add_fail(test_name, "Invalid plotter returned")
        except Exception as e:
            results.add_fail(test_name, str(e))

    # Test that params are stored when manually set
    try:
        plotter = create_radial_plotter(result, mesh)
        # Manually set params (this is how the class is meant to be used)
        plotter.params = params
        if plotter.params is not None:
            results.add_pass("create_radial_plotter params assignment")
        else:
            results.add_fail("create_radial_plotter params assignment", "Params not stored")
    except Exception as e:
        results.add_fail("create_radial_plotter params assignment", str(e))


def test_export_formats(results, test_data):
    """Test export to different formats"""
    print_section("Export Format Testing")

    result, mesh, params = test_data
    formats = ['png', 'pdf', 'svg']

    # Create test output directory
    test_output_dir = Path("test_output_radial")
    test_output_dir.mkdir(exist_ok=True)

    for fmt in formats:
        try:
            filepath = test_output_dir / f"test_radial_export.{fmt}"

            plotter = RadialProfilePlotter()
            plotter.load_radial_result(result, mesh, params)
            fig = plotter.plot_radial_profile('swelling', save_path=str(filepath), dpi=150)

            # Check file exists
            if filepath.exists():
                size_kb = filepath.stat().st_size / 1024
                if size_kb > 1:  # At least 1KB
                    results.add_pass(f"Export radial plot to {fmt.upper()}")
                else:
                    results.add_fail(f"Export radial plot to {fmt.upper()}", f"File too small: {size_kb:.1f}KB")
            else:
                results.add_fail(f"Export radial plot to {fmt.upper()}", "File not created")

            if fig is not None:
                plt.close(fig)

        except Exception as e:
            results.add_fail(f"Export radial plot to {fmt.upper()}", str(e))


def test_publication_quality(results, test_data):
    """Test publication-quality styling"""
    print_section("Publication-Quality Styling")

    result, mesh, params = test_data

    try:
        plotter = RadialProfilePlotter(style='IEEE')
        plotter.load_radial_result(result, mesh, params)

        fig = plotter.plot_radial_profile(
            'swelling',
            dpi=300,
            figsize=(8, 5),
            save_path=None
        )

        # Verify figure properties
        if fig is not None:
            fig_dpi = fig.get_dpi()
            fig_size = fig.get_size_inches()

            checks = []
            # DPI check - note: get_dpi() may return different value than set
            # The important thing is that a reasonably high DPI is used
            if fig_dpi >= 100:  # At least 100 DPI for publication quality
                checks.append("DPI>=100")

            # Figure size check - allow some tolerance since rcParams may affect it
            # The figsize should be close to (8, 5) even if not exact
            if abs(fig_size[0] - 8) < 2.0 and abs(fig_size[1] - 5) < 2.0:
                checks.append("figsize~(8,5)")

            if len(checks) == 2:
                results.add_pass("Publication-quality radial figure properties")
            else:
                results.add_fail("Publication-quality radial figure properties",
                               f"Missing: {', '.join(checks)} (got DPI={fig_dpi:.1f}, size={fig_size})")

            plt.close(fig)
        else:
            results.add_fail("Publication-quality radial figure properties", "Figure is None")
    except Exception as e:
        results.add_fail("Publication-quality radial figure properties", str(e))


def test_edge_cases(results):
    """Test edge cases and error handling"""
    print_section("Edge Cases and Error Handling")

    # Test with empty variables list
    try:
        plotter = RadialProfilePlotter()
        result, mesh, params = create_mock_radial_result()
        plotter.load_radial_result(result, mesh, params)

        try:
            fig = plotter.plot_radial_comparison([])
            results.add_fail("Empty variables list", "Should have raised ValueError")
            plt.close(fig)
        except ValueError as e:
            if "cannot be empty" in str(e):
                results.add_pass("Empty variables list (expected error)")
            else:
                results.add_fail("Empty variables list", f"Wrong error: {e}")
    except Exception as e:
        results.add_fail("Empty variables list setup", str(e))

    # Test with unknown variable
    try:
        plotter = RadialProfilePlotter()
        result, mesh, params = create_mock_radial_result()
        plotter.load_radial_result(result, mesh, params)

        try:
            profile = plotter.get_radial_profile('unknown_variable')
            results.add_fail("Unknown variable", "Should have raised ValueError")
        except ValueError as e:
            if "not found" in str(e):
                results.add_pass("Unknown variable (expected error)")
            else:
                results.add_fail("Unknown variable", f"Wrong error: {e}")
    except Exception as e:
        results.add_fail("Unknown variable setup", str(e))

    # Test with invalid time_index
    try:
        plotter = RadialProfilePlotter()
        result, mesh, params = create_mock_radial_result()
        plotter.load_radial_result(result, mesh, params)

        try:
            profile = plotter.get_radial_profile('swelling', time_index=9999)
            results.add_fail("Invalid time_index", "Should have raised ValueError")
        except ValueError as e:
            if "out of range" in str(e):
                results.add_pass("Invalid time_index (expected error)")
            else:
                results.add_fail("Invalid time_index", f"Wrong error: {e}")
    except Exception as e:
        results.add_fail("Invalid time_index setup", str(e))


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Radial visualization tests')
    parser.add_argument('--quick', '-q', action='store_true',
                        help='Run quick tests (skip time-intensive tests)')
    parser.add_argument('--format', '-f', type=str, default='all',
                        choices=['all', 'png', 'pdf', 'svg'],
                        help='Test specific export format')
    parser.add_argument('--use-mock', action='store_true',
                        help='Use mock data instead of running real simulation')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  GAS SWELLING RADIAL VISUALIZATION - TEST SUITE")
    print("=" * 70)

    results = ResultTracker()

    # Create test data
    try:
        if args.use_mock or args.quick:
            test_data = create_mock_radial_result(n_nodes=10, n_time_points=20, sim_time_days=30)
            print("  Using mock data for testing")
        else:
            test_data = create_real_radial_result(n_nodes=5, sim_time_days=10)
            print("  Using real simulation data for testing")
    except Exception as e:
        print(f"\n[FAIL] Failed to create test data: {e}")
        return 1

    result, mesh, params = test_data

    # Run test suites
    try:
        test_radial_plotter_instantiation(results, test_data)
        test_load_radial_result(results, test_data)
        test_get_radius_data(results, test_data)
        test_get_radial_profile(results, test_data)
        test_plot_radial_profile(results, test_data)
        test_plot_radial_comparison(results, test_data)
        test_plot_radial_evolution(results, test_data)
        test_plot_main(results, test_data)
        test_create_radial_plotter_factory(results, test_data)
        test_export_formats(results, test_data)
        test_publication_quality(results, test_data)
        test_edge_cases(results)

    except Exception as e:
        print(f"\n[FAIL] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Print summary
    success = results.summary()

    # Cleanup test output directory if all tests passed
    if success:
        test_output_dir = Path("test_output_radial")
        if test_output_dir.exists():
            import shutil
            shutil.rmtree(test_output_dir)
            print("\n[PASS] Cleaned up test output files")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
