#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Visualization Examples for Gas Swelling Model
=======================================================

This script demonstrates the NEW enhanced visualization features added to
the gas swelling model, including distribution plots, contour plots, and
uncertainty visualization with error bands.

What this script does:
- Demonstrates new distribution plotting capabilities (bubble size, radius, gas distributions)
- Shows contour plots for temperature sweeps and parameter studies
- Illustrates uncertainty quantification with error bands
- Provides publication-quality examples of all new features

New visualization features:
- Bubble size distribution plots (histograms + KDE)
- Bubble radius distribution across time points
- Gas atom distribution histograms
- Temperature sweep contour plots
- 2D parameter sweep heatmaps
- Swelling evolution with confidence intervals
- Bubble radius evolution with error bands

Usage:
    python examples/example_enhanced_visualization.py --help
    python examples/example_enhanced_visualization.py --example distribution
    python examples/example_enhanced_visualization.py --example contour --output results.pdf
    python examples/example_enhanced_visualization.py --example uncertainty

Author: Gas Swelling Model Team
Version: 0.3.0
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

# Import model components
try:
    from gas_swelling.models.modelrk23 import GasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters
    # Import NEW enhanced visualization functions
    from gas_swelling.visualization import (
        # Distribution plots
        plot_bubble_size_distribution,
        plot_bubble_radius_distribution,
        plot_gas_distribution_histogram,
        # Contour plots
        plot_temperature_contour,
        plot_2d_parameter_sweep,
        plot_swelling_heatmap,
        # Uncertainty plots
        plot_swelling_with_uncertainty,
        plot_bubble_radius_with_uncertainty,
        # Utilities
        calculate_burnup,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Ensure the gas_swelling package is installed or in PYTHONPATH")
    sys.exit(1)

# Set up matplotlib for publication-quality plotting
matplotlib.rcParams['figure.dpi'] = 100
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['axes.linewidth'] = 1.0
matplotlib.rcParams['grid.alpha'] = 0.3


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def example_bubble_size_distribution():
    """
    Example 1: Bubble Size Distribution Plots

    Demonstrates:
    - Plotting bubble size distributions at different time points
    - Using histogram + KDE for smooth distribution visualization
    - Comparing bulk vs phase boundary bubble sizes
    - Customizing bin counts and colors
    """

    print_section_header("Example 1: Bubble Size Distribution")

    # Run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600  # 100 days in seconds
    t_eval = np.linspace(0, sim_time, 100)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    print("  Creating bubble size distribution plots...")

    # Plot bubble size distribution at end of simulation
    fig = plot_bubble_size_distribution(
        result,
        time_index=-1,  # End of simulation
        region='both',
        bins=30,
        kde=True,
        figsize=(10, 6),
        save_path='example_bubble_size_distribution.png'
    )

    print("  Saved: example_bubble_size_distribution.png")
    plt.show()

    return result


def example_bubble_radius_distribution():
    """
    Example 2: Bubble Radius Distribution Analysis

    Demonstrates:
    - Multiple plot types: histogram, box plot, timeline
    - Comparing bubble radius distributions at multiple time points
    - Both bulk and interface regions
    - Timeline evolution of radius statistics
    """

    print_section_header("Example 2: Bubble Radius Distribution")

    # Run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 100)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    print("  Creating bubble radius distribution analysis...")

    # Create multi-panel figure with different plot types
    time_indices = [0, 50, 99]  # Start, middle, end

    fig = plot_bubble_radius_distribution(
        result,
        time_indices=time_indices,
        plot_type='histogram',
        region='both',
        figsize=(12, 8),
        save_path='example_radius_distribution_hist.png'
    )

    print("  Saved: example_radius_distribution_hist.png")
    plt.close()

    # Box plot comparison
    fig = plot_bubble_radius_distribution(
        result,
        time_indices=time_indices,
        plot_type='box',
        region='both',
        figsize=(10, 6),
        save_path='example_radius_distribution_box.png'
    )

    print("  Saved: example_radius_distribution_box.png")
    plt.close()

    # Timeline evolution
    fig = plot_bubble_radius_distribution(
        result,
        plot_type='timeline',
        region='both',
        figsize=(12, 6),
        save_path='example_radius_distribution_timeline.png'
    )

    print("  Saved: example_radius_distribution_timeline.png")
    plt.show()

    return result


def example_gas_distribution():
    """
    Example 3: Gas Atom Distribution Analysis

    Demonstrates:
    - Histogram of gas atoms per bubble
    - Comparison between bulk and interface
    - Evolution of gas distribution over time
    - Log-scale for wide value ranges
    """

    print_section_header("Example 3: Gas Distribution Histogram")

    # Run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 100)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    print("  Creating gas distribution plots...")

    # Histogram at peak time
    fig = plot_gas_distribution_histogram(
        result,
        time_point='peak',
        plot_type='histogram',
        region='both',
        bins=25,
        log_scale=True,
        figsize=(10, 6),
        save_path='example_gas_distribution_histogram.png'
    )

    print("  Saved: example_gas_distribution_histogram.png")
    plt.close()

    # Evolution over time
    fig = plot_gas_distribution_histogram(
        result,
        plot_type='evolution',
        region='both',
        time_points=[0, 25, 50, 75, 99],
        figsize=(12, 8),
        save_path='example_gas_distribution_evolution.png'
    )

    print("  Saved: example_gas_distribution_evolution.png")
    plt.show()

    return result


def example_temperature_contour():
    """
    Example 4: Temperature Sweep Contour Plot

    Demonstrates:
    - Creating 2D contour plots of swelling vs temperature and time
    - Using filled contours with colorbar
    - Customizing colormaps and contour levels
    """

    print_section_header("Example 4: Temperature Contour Plot")

    print("  Running temperature sweep...")

    # Define temperature range and time points
    temperatures = np.linspace(600, 1000, 20)  # 600-1000 K
    time_points = np.linspace(0, 100, 30)  # 0-100 days

    # Run simulations at different temperatures
    swelling_data = np.zeros((len(temperatures), len(time_points)))

    for i, temp in enumerate(temperatures):
        if (i + 1) % 5 == 0:
            print(f"    Temperature {i+1}/{len(temperatures)}...")

        params = create_default_parameters()
        params['temperature'] = temp

        model = GasSwellingModel(params)

        sim_time = 100 * 24 * 3600  # 100 days
        t_eval = np.linspace(0, sim_time, len(time_points))

        result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

        # Calculate swelling
        V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
        V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
        swelling = (V_bubble_b + V_bubble_f) * 100

        swelling_data[i, :] = swelling

    # Create contour plot
    fig = plot_temperature_contour(
        temperature_values=temperatures,
        time_values=time_points,
        swelling_data=swelling_data,
        param_name='Swelling',
        param_unit='%',
        colormap='viridis',
        show_contour_lines=True,
        figsize=(10, 7),
        save_path='example_temperature_contour.png'
    )

    print("  Saved: example_temperature_contour.png")
    plt.show()

    return swelling_data


def example_2d_parameter_sweep():
    """
    Example 5: 2D Parameter Sweep Heatmap

    Demonstrates:
    - Creating heatmaps for two-parameter studies
    - Dislocation density vs temperature effects
    - Automatic log-scale detection
    - Colorbar customization
    """

    print_section_header("Example 5: 2D Parameter Sweep")

    print("  Running 2D parameter sweep (dislocation density vs temperature)...")

    # Define parameter ranges
    temperatures = np.linspace(600, 1000, 15)
    dislocation_densities = np.logspace(13, 15, 15)  # 10^13 to 10^15 m^-2

    # Run parameter sweep
    swelling_data = np.zeros((len(dislocation_densities), len(temperatures)))

    for i, rho in enumerate(dislocation_densities):
        if (i + 1) % 3 == 0:
            print(f"    Dislocation density {i+1}/{len(dislocation_densities)}...")

        for j, temp in enumerate(temperatures):
            params = create_default_parameters()
            params['temperature'] = temp
            params['dislocation_density'] = rho

            model = GasSwellingModel(params)

            sim_time = 50 * 24 * 3600  # 50 days
            t_eval = np.linspace(0, sim_time, 50)

            result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

            # Calculate final swelling
            V_bubble_b = (4.0/3.0) * np.pi * result['Rcb'][-1]**3 * result['Ccb'][-1]
            V_bubble_f = (4.0/3.0) * np.pi * result['Rcf'][-1]**3 * result['Ccf'][-1]
            swelling = (V_bubble_b + V_bubble_f) * 100

            swelling_data[i, j] = swelling

    # Create parameter sweep plot
    fig = plot_2d_parameter_sweep(
        param1_values=dislocation_densities,
        param2_values=temperatures,
        output_data=swelling_data,
        param1_name='Dislocation Density',
        param1_unit='m⁻²',
        param2_name='Temperature',
        param2_unit='K',
        output_name='Final Swelling',
        output_unit='%',
        colormap='plasma',
        show_contour_lines=True,
        figsize=(11, 8),
        save_path='example_2d_parameter_sweep.png'
    )

    print("  Saved: example_2d_parameter_sweep.png")
    plt.show()

    return swelling_data


def example_swelling_heatmap():
    """
    Example 6: Swelling Heatmap with Annotations

    Demonstrates:
    - Creating heatmaps with enhanced contourf
    - Adding contour lines overlay
    - Customizable colorbar orientation
    """

    print_section_header("Example 6: Swelling Heatmap")

    print("  Generating sample data for heatmap...")

    # Create synthetic data for demonstration
    temperatures = np.linspace(600, 1000, 25)
    fission_rates = np.linspace(1e13, 1e15, 25)

    # Create synthetic swelling surface (for demonstration)
    temp_grid, rate_grid = np.meshgrid(temperatures, fission_rates)
    swelling_data = 2.0 * np.exp(-((temp_grid - 800)**2) / (2 * 100**2)) * \
                    (rate_grid / 1e14)**0.5

    # Create heatmap
    fig = plot_swelling_heatmap(
        x_values=temperatures,
        y_values=fission_rates,
        heatmap_data=swelling_data,
        x_label='Temperature',
        x_unit='K',
        y_label='Fission Rate',
        y_unit='fissions/m³/s',
        colorbar_label='Swelling (%)',
        colormap='coolwarm',
        show_contour_lines=True,
        contour_levels=15,
        figsize=(11, 9),
        save_path='example_swelling_heatmap.png'
    )

    print("  Saved: example_swelling_heatmap.png")
    plt.show()

    return swelling_data


def example_uncertainty_visualization():
    """
    Example 7: Uncertainty Quantification with Error Bands

    Demonstrates:
    - Running multiple simulations with parameter variations
    - Plotting swelling evolution with confidence intervals
    - Using fill_between for error bands
    - Customizing confidence levels and transparency
    """

    print_section_header("Example 7: Uncertainty Visualization")

    print("  Running multiple simulations for uncertainty analysis...")

    # Run simulations with parameter variations
    num_runs = 10
    results = []

    base_params = create_default_parameters()

    for i in range(num_runs):
        if (i + 1) % 2 == 0:
            print(f"    Simulation {i+1}/{num_runs}...")

        # Vary parameters slightly to simulate uncertainty
        params = base_params.copy()
        params['temperature'] = base_params['temperature'] + np.random.normal(0, 10)
        params['dislocation_density'] = base_params['dislocation_density'] * \
                                        (1 + np.random.normal(0, 0.1))

        model = GasSwellingModel(params)

        sim_time = 100 * 24 * 3600
        t_eval = np.linspace(0, sim_time, 100)

        result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
        results.append(result)

    # Plot swelling with uncertainty
    print("  Creating swelling plot with error bands...")

    fig = plot_swelling_with_uncertainty(
        results=results,
        confidence=0.95,
        variable='swelling',
        fill_color='blue',
        fill_alpha=0.3,
        line_color='darkblue',
        figsize=(10, 6),
        save_path='example_swelling_uncertainty.png'
    )

    print("  Saved: example_swelling_uncertainty.png")
    plt.close()

    # Plot bubble radius with uncertainty
    print("  Creating bubble radius plot with error bands...")

    fig = plot_bubble_radius_with_uncertainty(
        results=results,
        confidence=0.95,
        region='both',
        figsize=(10, 6),
        save_path='example_radius_uncertainty.png'
    )

    print("  Saved: example_radius_uncertainty.png")
    plt.show()

    return results


def example_comprehensive_analysis():
    """
    Example 8: Comprehensive Multi-Panel Analysis

    Demonstrates:
    - Combining multiple visualization types in one figure
    - Distribution analysis + contour plots + uncertainty
    - Publication-quality multi-panel figure
    """

    print_section_header("Example 8: Comprehensive Analysis")

    print("  Running simulation for comprehensive analysis...")

    # Run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 100)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Create multi-panel figure
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.3)

    fig.suptitle('Comprehensive Bubble Analysis - Enhanced Visualization',
                 fontsize=14, fontweight='bold')

    # Panel 1: Bubble size distribution
    ax1 = fig.add_subplot(gs[0, 0])
    # Simplified distribution plot
    from scipy.stats import gaussian_kde
    final_radius = result['Rcb'][-1] * 1e9  # Convert to nm
    if len(final_radius) > 0 and np.std(final_radius) > 0:
        kde = gaussian_kde(final_radius)
        x_range = np.linspace(final_radius.min(), final_radius.max(), 100)
        ax1.hist(final_radius, bins=20, density=True, alpha=0.6, color='steelblue')
        ax1.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')
    ax1.set_xlabel('Bubble Radius (nm)')
    ax1.set_ylabel('Density')
    ax1.set_title('(a) Size Distribution', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Panel 2: Swelling evolution
    ax2 = fig.add_subplot(gs[0, 1])
    time_days = result['time'] / (24 * 3600)
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    ax2.plot(time_days, swelling, linewidth=2.5, color='darkgreen')
    ax2.fill_between(time_days, swelling, alpha=0.3, color='darkgreen')
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Swelling (%)')
    ax2.set_title('(b) Swelling Evolution', fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Panel 3: Gas atoms per bubble
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(time_days, result['Ncb'], label='Bulk', linewidth=2)
    ax3.plot(time_days, result['Ncf'], label='Interface', linewidth=2,
             linestyle='--')
    ax3.set_xlabel('Time (days)')
    ax3.set_ylabel('Gas atoms per bubble')
    ax3.set_title('(c) Gas Accumulation', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Panel 4: Temperature effect (synthetic data for demo)
    ax4 = fig.add_subplot(gs[1, 1])
    temps = np.array([600, 700, 800, 900, 1000])
    swellings = np.array([0.8, 1.9, 2.5, 1.7, 0.9])
    ax4.plot(temps, swellings, marker='o', linewidth=2.5, markersize=8,
             color='crimson')
    ax4.set_xlabel('Temperature (K)')
    ax4.set_ylabel('Final Swelling (%)')
    ax4.set_title('(d) Temperature Effect', fontweight='bold')
    ax4.grid(True, alpha=0.3)

    # Panel 5: Bubble radius evolution
    ax5 = fig.add_subplot(gs[2, :])
    ax5.plot(time_days, result['Rcb'] * 1e9, label='Bulk', linewidth=2.5)
    ax5.plot(time_days, result['Rcf'] * 1e9, label='Interface', linewidth=2.5,
             linestyle='--')
    ax5.set_xlabel('Time (days)')
    ax5.set_ylabel('Bubble Radius (nm)')
    ax5.set_title('(e) Radius Evolution', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    filename = 'example_comprehensive_analysis.png'
    plt.savefig(filename, bbox_inches='tight')
    print(f"  Saved: {filename}")

    plt.show()

    return result


def list_examples():
    """List all available examples with descriptions"""
    examples = {
        'distribution': 'Bubble size distribution plots (histogram + KDE)',
        'radius': 'Bubble radius distribution analysis',
        'gas': 'Gas atom distribution histograms',
        'temperature': 'Temperature sweep contour plots',
        'sweep': '2D parameter sweep heatmaps',
        'heatmap': 'Swelling heatmap with annotations',
        'uncertainty': 'Uncertainty quantification with error bands',
        'comprehensive': 'Comprehensive multi-panel analysis',
    }

    print("\nAvailable Enhanced Visualization Examples:")
    print("-" * 70)
    for name, description in examples.items():
        print(f"  {name:15s} - {description}")
    print("-" * 70)
    print("\nUsage:")
    print("  python example_enhanced_visualization.py --example <name>")
    print("  python example_enhanced_visualization.py --example all")


def main():
    """Main function with command-line interface"""

    parser = argparse.ArgumentParser(
        description='Enhanced visualization examples for Gas Swelling Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python example_enhanced_visualization.py --list
  python example_enhanced_visualization.py --example distribution
  python example_enhanced_visualization.py --example all
  python example_enhanced_visualization.py --example uncertainty --output uncertainty.pdf
        """
    )

    parser.add_argument('--example', '-e',
                        type=str,
                        help='Example to run (use --list to see available examples)')
    parser.add_argument('--list', '-l',
                        action='store_true',
                        help='List all available examples')
    parser.add_argument('--output', '-o',
                        type=str,
                        help='Output filename (overrides default)')

    args = parser.parse_args()

    # Handle --list
    if args.list:
        list_examples()
        return 0

    # Handle --example
    if args.example is None:
        parser.print_help()
        return 1

    # Run examples
    print("\n" + "=" * 70)
    print("  ENHANCED VISUALIZATION EXAMPLES")
    print("  Gas Swelling Model v0.3.0")
    print("=" * 70)

    examples_to_run = []

    if args.example == 'all':
        examples_to_run = ['distribution', 'radius', 'gas', 'temperature',
                          'sweep', 'heatmap', 'uncertainty', 'comprehensive']
    elif args.example == 'distribution':
        examples_to_run = ['distribution']
    elif args.example == 'radius':
        examples_to_run = ['radius']
    elif args.example == 'gas':
        examples_to_run = ['gas']
    elif args.example == 'temperature':
        examples_to_run = ['temperature']
    elif args.example == 'sweep':
        examples_to_run = ['sweep']
    elif args.example == 'heatmap':
        examples_to_run = ['heatmap']
    elif args.example == 'uncertainty':
        examples_to_run = ['uncertainty']
    elif args.example == 'comprehensive':
        examples_to_run = ['comprehensive']
    else:
        print(f"\nUnknown example: {args.example}")
        print("Use --list to see available examples")
        return 1

    # Run selected examples
    try:
        for example_name in examples_to_run:
            if example_name == 'distribution':
                example_bubble_size_distribution()
            elif example_name == 'radius':
                example_bubble_radius_distribution()
            elif example_name == 'gas':
                example_gas_distribution()
            elif example_name == 'temperature':
                example_temperature_contour()
            elif example_name == 'sweep':
                example_2d_parameter_sweep()
            elif example_name == 'heatmap':
                example_swelling_heatmap()
            elif example_name == 'uncertainty':
                example_uncertainty_visualization()
            elif example_name == 'comprehensive':
                example_comprehensive_analysis()
    except Exception as e:
        print(f"\nError running example: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    print("  All examples completed successfully!")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
