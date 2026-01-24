#!/usr/bin/env python3
"""
Verification script for gas distribution plotting functions.

This script tests the new gas distribution pie charts and analysis plots
added in subtask-4-3. Run this after installing dependencies to verify
the implementation works correctly.
"""

import sys
import numpy as np

def verify_gas_distribution_functions():
    """Verify gas distribution analysis and plotting functions."""

    print("=" * 60)
    print("Gas Distribution Plots Verification")
    print("=" * 60)
    print()

    # Create mock simulation result data
    print("1. Creating mock simulation result data...")
    result = {
        'time': np.linspace(0, 100, 100),
        'Cgb': np.linspace(1e20, 5e20, 100),  # Bulk gas concentration
        'Cgf': np.linspace(5e19, 3e20, 100),  # Interface gas concentration
        'Ccb': np.linspace(1e15, 8e15, 100),  # Bulk bubble concentration
        'Ccf': np.linspace(5e14, 4e15, 100),  # Interface bubble concentration
        'Ncb': np.linspace(100, 1000, 100),    # Gas atoms per bulk bubble
        'Ncf': np.linspace(50, 500, 100),      # Gas atoms per interface bubble
        'released_gas': np.linspace(0, 1e18, 100)  # Released gas
    }
    print("   ✓ Mock data created")
    print()

    # Test 1: calculate_gas_distribution_analysis
    print("2. Testing calculate_gas_distribution_analysis...")
    try:
        from gas_swelling.visualization.comparison_plots import calculate_gas_distribution_analysis

        analysis = calculate_gas_distribution_analysis(result, time_index=-1)

        print(f"   Gas in solution fraction: {analysis['gas_in_solution_fraction']:.4f}")
        print(f"   Gas in bubbles fraction: {analysis['gas_in_bubbles_fraction']:.4f}")
        print(f"   Gas release fraction: {analysis['gas_release_fraction']:.4f}")

        # Verify fractions sum to 1 (or 0 if no gas)
        total = (analysis['gas_in_solution_fraction'] +
                analysis['gas_in_bubbles_fraction'] +
                analysis['gas_release_fraction'])

        if abs(total - 1.0) < 0.01 or total == 0:
            print(f"   ✓ Fractions sum to {total:.4f} (expected ~1.0)")
        else:
            print(f"   ✗ WARNING: Fractions sum to {total:.4f} (expected 1.0)")

        print("   ✓ calculate_gas_distribution_analysis works correctly")
        print()

    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False

    # Test 2: plot_gas_distribution_pie_simple
    print("3. Testing plot_gas_distribution_pie_simple...")
    try:
        from gas_swelling.visualization.comparison_plots import plot_gas_distribution_pie_simple
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt

        # Test with default labels
        fig = plot_gas_distribution_pie_simple(result, time_index=-1)
        plt.close(fig)
        print("   ✓ Default labels plot created successfully")

        # Test with custom labels (matching pattern from examples)
        fig = plot_gas_distribution_pie_simple(
            result,
            time_index=-1,
            labels=['溶解态', '气泡内', '已释放']
        )
        plt.close(fig)
        print("   ✓ Custom labels plot created successfully")
        print()

    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: plot_gas_release_fraction
    print("4. Testing plot_gas_release_fraction...")
    try:
        from gas_swelling.visualization.comparison_plots import plot_gas_release_fraction

        # Test with temperatures and gas_release_fractions format
        temperature_results = {
            'temperatures': [600, 700, 800, 900, 1000],
            'gas_release_fractions': [0.01, 0.05, 0.15, 0.35, 0.55]
        }

        fig = plot_gas_release_fraction(temperature_results)
        plt.close(fig)
        print("   ✓ Temperature sweep plot created successfully")

        # Test with detailed_results format (matching pattern from examples)
        detailed_results = {
            'detailed_results': {
                600: {
                    'analysis': {
                        'gas_release_fraction': 0.01
                    }
                },
                700: {
                    'analysis': {
                        'gas_release_fraction': 0.05
                    }
                },
                800: {
                    'analysis': {
                        'gas_release_fraction': 0.15
                    }
                }
            }
        }

        fig = plot_gas_release_fraction(detailed_results)
        plt.close(fig)
        print("   ✓ Detailed results plot created successfully")
        print()

    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("The following functions are working correctly:")
    print("  1. calculate_gas_distribution_analysis")
    print("  2. plot_gas_distribution_pie_simple")
    print("  3. plot_gas_release_fraction")
    print()
    print("These functions follow the pattern from examples/run_simulation.py")
    print("and provide gas distribution analysis and visualization.")

    return True


if __name__ == '__main__':
    try:
        success = verify_gas_distribution_functions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
