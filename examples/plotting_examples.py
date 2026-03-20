#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotting Examples for Gas Swelling Model
==========================================

This script demonstrates various plotting capabilities for visualizing
gas swelling simulation results.

What this script does:
- Demonstrates different types of plots for simulation results
- Shows how to customize plot appearance (colors, labels, styles)
- Illustrates publication-quality figure generation
- Provides examples for common visualization tasks

Available plot types:
- Swelling evolution plots
- Bubble radius growth plots
- Gas pressure evolution plots
- Temperature sweep visualizations
- Phase boundary vs bulk comparison plots
- Multi-panel summary figures

Usage:
    python examples/plotting_examples.py --help
    python examples/plotting_examples.py --example basic
    python examples/plotting_examples.py --example temperature --output results.pdf

Author: Gas Swelling Model Team
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

# Import model components
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

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


def example_basic_simulation_plot():
    """
    Example 1: Basic simulation results plotting

    Demonstrates:
    - Running a basic simulation
    - Creating time-series plots
    - Customizing line styles and colors
    - Adding labels, titles, and legends
    - Saving to different file formats
    """

    print_section_header("Example 1: Basic Simulation Plot")

    # Create parameters and run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600  # 100 days in seconds
    t_eval = np.linspace(0, sim_time, 100)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Convert time to days
    time_days = result['time'] / (24 * 3600)

    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Gas Swelling Simulation Results', fontsize=14, fontweight='bold')

    # Plot 1: Bubble radius evolution
    axes[0, 0].plot(time_days, result['Rcb'] * 1e9,
                    label='Bulk bubbles', linewidth=2, color='blue')
    axes[0, 0].plot(time_days, result['Rcf'] * 1e9,
                    label='Boundary bubbles', linewidth=2, color='red', linestyle='--')
    axes[0, 0].set_xlabel('Time (days)', fontsize=11)
    axes[0, 0].set_ylabel('Bubble radius (nm)', fontsize=11)
    axes[0, 0].set_title('Bubble Radius Evolution', fontsize=12)
    axes[0, 0].legend(fontsize=10)
    axes[0, 0].grid(True)

    # Plot 2: Swelling evolution
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    axes[0, 1].plot(time_days, swelling, linewidth=2, color='darkgreen')
    axes[0, 1].fill_between(time_days, swelling, alpha=0.3, color='darkgreen')
    axes[0, 1].set_xlabel('Time (days)', fontsize=11)
    axes[0, 1].set_ylabel('Swelling (%)', fontsize=11)
    axes[0, 1].set_title('Fuel Swelling Evolution', fontsize=12)
    axes[0, 1].grid(True)

    # Plot 3: Bubble concentration (log scale)
    axes[1, 0].semilogy(time_days, result['Ccb'],
                        label='Bulk bubbles', linewidth=2, color='purple')
    axes[1, 0].semilogy(time_days, result['Ccf'],
                        label='Boundary bubbles', linewidth=2, color='orange')
    axes[1, 0].set_xlabel('Time (days)', fontsize=11)
    axes[1, 0].set_ylabel('Bubble concentration (m⁻³)', fontsize=11)
    axes[1, 0].set_title('Bubble Concentration', fontsize=12)
    axes[1, 0].legend(fontsize=10)
    axes[1, 0].grid(True)

    # Plot 4: Gas atoms per bubble
    axes[1, 1].plot(time_days, result['Ncb'],
                    label='Bulk bubbles', linewidth=2, color='teal')
    axes[1, 1].plot(time_days, result['Ncf'],
                    label='Boundary bubbles', linewidth=2, color='brown', linestyle='--')
    axes[1, 1].set_xlabel('Time (days)', fontsize=11)
    axes[1, 1].set_ylabel('Gas atoms per bubble', fontsize=11)
    axes[1, 1].set_title('Gas Accumulation in Bubbles', fontsize=12)
    axes[1, 1].legend(fontsize=10)
    axes[1, 1].grid(True)

    plt.tight_layout()

    # Save to multiple formats
    output_base = 'example_basic_simulation'
    for ext in ['png', 'pdf', 'svg']:
        filename = f'{output_base}.{ext}'
        plt.savefig(filename, bbox_inches='tight')
        print(f"  Saved: {filename}")

    plt.show()

    return result


def example_custom_styling():
    """
    Example 2: Custom plot styling

    Demonstrates:
    - Custom color schemes
    - Different line styles (solid, dashed, dotted)
    - Marker styles for data points
    - Custom fonts and text sizes
    - Figure size and aspect ratio control
    """

    print_section_header("Example 2: Custom Styling")

    # Run a quick simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 50 * 24 * 3600  # 50 days
    t_eval = np.linspace(0, sim_time, 50)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    time_days = result['time'] / (24 * 3600)

    # Create custom figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Calculate swelling
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    # Custom color palette
    colors = {
        'bulk': '#2E86AB',      # Blue
        'boundary': '#A23B72',  # Magenta
        'total': '#06A77D'      # Green
    }

    # Plot with custom styling
    ax.plot(time_days, swelling,
            linewidth=3,
            color=colors['total'],
            label='Total swelling',
            marker='o',
            markersize=4,
            markeredgecolor='white',
            markeredgewidth=1.5)

    # Add shaded region
    ax.fill_between(time_days, swelling, alpha=0.2, color=colors['total'])

    # Customize axes
    ax.set_xlabel('Irradiation Time (days)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Volumetric Swelling (%)', fontsize=14, fontweight='bold')
    ax.set_title('Custom Styled Swelling Evolution Plot',
                 fontsize=16, fontweight='bold', pad=20)

    # Custom grid
    ax.grid(True, linestyle=':', alpha=0.6, color='gray')
    ax.set_axisbelow(True)

    # Custom legend
    ax.legend(loc='upper left', fontsize=12, framealpha=0.9)

    # Custom spine styling
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_edgecolor('#333333')

    plt.tight_layout()

    filename = 'example_custom_styling.png'
    plt.savefig(filename, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {filename}")

    plt.show()

    return result


def example_temperature_comparison():
    """
    Example 3: Temperature sweep visualization

    Demonstrates:
    - Running multiple simulations at different temperatures
    - Comparing results on the same plot
    - Using color maps to distinguish conditions
    - Creating publication-quality comparison plots
    """

    print_section_header("Example 3: Temperature Comparison")

    temperatures = [600, 700, 800, 900]  # Kelvin
    results = []

    print(f"Running simulations at {len(temperatures)} temperatures...")

    for temp in temperatures:
        print(f"  Temperature: {temp} K")

        params = create_default_parameters()
        params['temperature'] = temp

        model = GasSwellingModel(params)

        sim_time = 100 * 24 * 3600
        t_eval = np.linspace(0, sim_time, 100)

        result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

        # Calculate swelling
        V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
        V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
        swelling = (V_bubble_b + V_bubble_f) * 100

        results.append({
            'temperature': temp,
            'time_days': result['time'] / (24 * 3600),
            'swelling': swelling,
            'Rcb': result['Rcb'],
            'Rcf': result['Rcf']
        })

    # Create comparison plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Temperature Effect on Gas Swelling Behavior',
                 fontsize=14, fontweight='bold')

    # Use a colormap
    cmap = plt.get_cmap('viridis')
    colors = cmap(np.linspace(0, 1, len(temperatures)))

    # Plot 1: Swelling evolution comparison
    for i, result in enumerate(results):
        axes[0].plot(result['time_days'], result['swelling'],
                    label=f"{result['temperature']} K",
                    linewidth=2.5, color=colors[i])

    axes[0].set_xlabel('Time (days)', fontsize=12)
    axes[0].set_ylabel('Swelling (%)', fontsize=12)
    axes[0].set_title('(a) Swelling Evolution', fontsize=12, fontweight='bold')
    axes[0].legend(fontsize=10)
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Final bubble radius comparison
    final_Rcb = [result['Rcb'][-1] * 1e9 for result in results]
    final_Rcf = [result['Rcf'][-1] * 1e9 for result in results]

    x = np.arange(len(temperatures))
    width = 0.35

    axes[1].bar(x - width/2, final_Rcb, width, label='Bulk bubbles',
                color=colors[0], alpha=0.8)
    axes[1].bar(x + width/2, final_Rcf, width, label='Boundary bubbles',
                color=colors[-1], alpha=0.8)

    axes[1].set_xlabel('Temperature (K)', fontsize=12)
    axes[1].set_ylabel('Final bubble radius (nm)', fontsize=12)
    axes[1].set_title('(b) Final Bubble Radius', fontsize=12, fontweight='bold')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f'{T}' for T in temperatures])
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    filename = 'example_temperature_comparison.pdf'
    plt.savefig(filename, bbox_inches='tight')
    print(f"  Saved: {filename}")

    plt.show()

    return results


def example_phase_boundary_comparison():
    """
    Example 4: Bulk vs Phase Boundary behavior

    Demonstrates:
    - Comparing bulk and phase boundary behaviors
    - Using different plot types (line, semilog, bar)
    - Highlighting differences between physical domains
    - Creating multi-panel summary figures
    """

    print_section_header("Example 4: Phase Boundary Comparison")

    # Run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 100)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    time_days = result['time'] / (24 * 3600)

    # Create comprehensive comparison figure
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    fig.suptitle('Bulk vs Phase Boundary Behavior Comparison',
                 fontsize=14, fontweight='bold')

    # Plot 1: Bubble radius comparison
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(time_days, result['Rcb'] * 1e9, label='Bulk', linewidth=2)
    ax1.plot(time_days, result['Rcf'] * 1e9, label='Phase Boundary',
             linewidth=2, linestyle='--')
    ax1.set_ylabel('Radius (nm)')
    ax1.set_title('Bubble Radius', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Bubble concentration comparison (log scale)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.semilogy(time_days, result['Ccb'], label='Bulk', linewidth=2)
    ax2.semilogy(time_days, result['Ccf'], label='Phase Boundary',
                 linewidth=2, linestyle='--')
    ax2.set_ylabel('Concentration (m⁻³)')
    ax2.set_title('Bubble Concentration', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Gas atoms per bubble
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(time_days, result['Ncb'], label='Bulk', linewidth=2)
    ax3.plot(time_days, result['Ncf'], label='Phase Boundary',
             linewidth=2, linestyle='--')
    ax3.set_ylabel('Atoms per bubble')
    ax3.set_title('Gas Content', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Gas concentration in matrix
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(time_days, result['Cgb'], label='Bulk', linewidth=2)
    ax4.plot(time_days, result['Cgf'], label='Phase Boundary',
             linewidth=2, linestyle='--')
    ax4.set_ylabel('Gas concentration (atoms/m³)')
    ax4.set_title('Gas in Matrix', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Plot 5: Swelling contribution
    ax5 = fig.add_subplot(gs[2, :])
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb'] * 100
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf'] * 100

    ax5.plot(time_days, V_bubble_b, label='Bulk contribution',
             linewidth=2, alpha=0.7)
    ax5.plot(time_days, V_bubble_f, label='Phase boundary contribution',
             linewidth=2, alpha=0.7, linestyle='--')
    ax5.plot(time_days, V_bubble_b + V_bubble_f,
             label='Total swelling', linewidth=3, color='black')
    ax5.set_xlabel('Time (days)')
    ax5.set_ylabel('Swelling contribution (%)')
    ax5.set_title('Swelling Contribution by Domain', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    filename = 'example_phase_boundary_comparison.png'
    plt.savefig(filename, bbox_inches='tight')
    print(f"  Saved: {filename}")

    plt.show()

    return result


def example_publication_quality():
    """
    Example 5: Publication-quality figure

    Demonstrates:
    - Creating figures suitable for scientific papers
    - Proper font sizes and line weights
    - High-resolution output
    - Multi-panel figures with letter labels
    - Export to vector formats (PDF, SVG)
    """

    print_section_header("Example 5: Publication Quality Figure")

    # Run simulation
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 100)

    print("Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    time_days = result['time'] / (24 * 3600)

    # Create publication-quality figure
    # Typical journal figure size: 3.5 inches (single column) or 7 inches (double column)
    fig, axes = plt.subplots(2, 2, figsize=(7, 6))

    # Publication style settings
    plt.rcParams['font.size'] = 8
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['lines.linewidth'] = 1.2

    # Panel (a): Bubble radius
    axes[0, 0].plot(time_days, result['Rcb'] * 1e9, 'b-', linewidth=1.5, label='Bulk')
    axes[0, 0].plot(time_days, result['Rcf'] * 1e9, 'r--', linewidth=1.5, label='Interface')
    axes[0, 0].set_xlabel('Time (days)')
    axes[0, 0].set_ylabel('Radius (nm)')
    axes[0, 0].legend(fontsize=7)
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].text(0.02, 0.98, '(a)', transform=axes[0, 0].transAxes,
                    fontsize=10, fontweight='bold', va='top')

    # Panel (b): Swelling
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    axes[0, 1].plot(time_days, swelling, 'k-', linewidth=1.5)
    axes[0, 1].set_xlabel('Time (days)')
    axes[0, 1].set_ylabel('Swelling (%)')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].text(0.02, 0.98, '(b)', transform=axes[0, 1].transAxes,
                    fontsize=10, fontweight='bold', va='top')

    # Panel (c): Bubble concentration
    axes[1, 0].semilogy(time_days, result['Ccb'], 'b-', linewidth=1.5, label='Bulk')
    axes[1, 0].semilogy(time_days, result['Ccf'], 'r--', linewidth=1.5, label='Interface')
    axes[1, 0].set_xlabel('Time (days)')
    axes[1, 0].set_ylabel('Concentration (m⁻³)')
    axes[1, 0].legend(fontsize=7)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].text(0.02, 0.98, '(c)', transform=axes[1, 0].transAxes,
                    fontsize=10, fontweight='bold', va='top')

    # Panel (d): Gas atoms per bubble
    axes[1, 1].plot(time_days, result['Ncb'], 'b-', linewidth=1.5, label='Bulk')
    axes[1, 1].plot(time_days, result['Ncf'], 'r--', linewidth=1.5, label='Interface')
    axes[1, 1].set_xlabel('Time (days)')
    axes[1, 1].set_ylabel('Gas atoms per bubble')
    axes[1, 1].legend(fontsize=7)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].text(0.02, 0.98, '(d)', transform=axes[1, 1].transAxes,
                    fontsize=10, fontweight='bold', va='top')

    plt.tight_layout()

    # Save to multiple formats
    base_name = 'example_publication_figure'
    for fmt in ['pdf', 'png', 'svg']:
        filename = f'{base_name}.{fmt}'
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        print(f"  Saved: {filename}")

    plt.show()

    return result


def list_examples():
    """List all available examples with descriptions"""
    examples = {
        'basic': 'Basic simulation results plotting',
        'styling': 'Custom plot styling and colors',
        'temperature': 'Temperature sweep comparison',
        'phase': 'Bulk vs phase boundary comparison',
        'publication': 'Publication-quality figure generation',
    }

    print("\nAvailable Examples:")
    print("-" * 70)
    for name, description in examples.items():
        print(f"  {name:15s} - {description}")
    print("-" * 70)
    print("\nUsage:")
    print("  python plotting_examples.py --example <name>")
    print("  python plotting_examples.py --example all")


def main():
    """Main function with command-line interface"""

    parser = argparse.ArgumentParser(
        description='Plotting examples for Gas Swelling Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plotting_examples.py --list
  python plotting_examples.py --example basic
  python plotting_examples.py --example all
  python plotting_examples.py --example temperature --output temp_results.pdf
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
    print("  GAS SWELLING MODEL - PLOTTING EXAMPLES")
    print("=" * 70)

    examples_to_run = []

    if args.example == 'all':
        examples_to_run = ['basic', 'styling', 'temperature', 'phase', 'publication']
    elif args.example == 'basic':
        examples_to_run = ['basic']
    elif args.example == 'styling':
        examples_to_run = ['styling']
    elif args.example == 'temperature':
        examples_to_run = ['temperature']
    elif args.example == 'phase':
        examples_to_run = ['phase']
    elif args.example == 'publication':
        examples_to_run = ['publication']
    else:
        print(f"\nUnknown example: {args.example}")
        print("Use --list to see available examples")
        return 1

    # Run selected examples
    for example_name in examples_to_run:
        try:
            if example_name == 'basic':
                example_basic_simulation_plot()
            elif example_name == 'styling':
                example_custom_styling()
            elif example_name == 'temperature':
                example_temperature_comparison()
            elif example_name == 'phase':
                example_phase_boundary_comparison()
            elif example_name == 'publication':
                example_publication_quality()
        except Exception as e:
            print(f"\nError running example '{example_name}': {e}")
            import traceback
            traceback.print_exc()
            return 1

    print("\n" + "=" * 70)
    print("  All examples completed successfully!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
