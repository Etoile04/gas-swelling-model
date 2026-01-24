#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temperature Sweep Plotting Example
==================================

This script demonstrates how to run and visualize temperature sweep studies
for the gas swelling model. It shows how fuel swelling behavior varies with
temperature, which is critical for understanding reactor operating conditions.

What this script does:
- Runs simulations across a range of temperatures
- Creates temperature vs swelling plots
- Visualizes bubble radius evolution with temperature
- Generates Arrhenius plots for activation energy analysis
- Compares bulk vs phase boundary behaviors

Key Features:
- Configurable temperature ranges
- Parallel simulation support
- Multiple plot types (line, scatter, Arrhenius)
- Publication-quality output
- CSV export for further analysis

Usage:
    python examples/temperature_sweep_plotting.py --help
    python examples/temperature_sweep_plotting.py --temp-range 600 900 --step 50
    python examples/temperature_sweep_plotting.py --arrhenius

Author: Gas Swelling Model Team
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
import csv
from typing import List, Tuple, Dict, Optional

# Import model components
try:
    from gas_swelling.models.modelrk23 import GasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters
except ImportError:
    # Fallback for development environment
    from models.modelrk23 import GasSwellingModel
    from params.parameters import create_default_parameters

# Set up matplotlib for publication-quality plotting
matplotlib.rcParams['figure.dpi'] = 100
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['axes.linewidth'] = 1.0
matplotlib.rcParams['grid.alpha'] = 0.3


def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_model_parameters(temperature: float, base_params: Optional[Dict] = None) -> Dict:
    """
    Create model parameters for a given temperature.

    Args:
        temperature: Temperature in Kelvin
        base_params: Optional base parameters to modify

    Returns:
        Dictionary of model parameters
    """
    if base_params is None:
        params = create_default_parameters()
    else:
        params = base_params.copy()

    # Set temperature
    params['temperature'] = temperature

    # Optimized parameters based on validation studies
    params['time_step'] = 1e-9
    params['max_time_step'] = 0.1
    params['Fnb'] = 1e-5  # Bulk bubble nucleation factor
    params['Fnf'] = 1e-5  # Interface bubble nucleation factor
    params['dislocation_density'] = 7.0e13  # m^-2
    params['surface_energy'] = 0.5  # J/m^2
    params['resolution_rate'] = 2.0e-5  # s^-1
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1e0
    params['Dv0'] = 7.767e-10
    params['Di0'] = 1.259e-8
    params['Evm'] = 0.347  # eV
    params['Eim'] = 0.42  # eV
    params['Evfmuti'] = 1.0
    params['fission_rate'] = 5e19  # fissions/m^3/s
    params['gas_production_rate'] = 0.5
    params['critical_radius'] = 50e-9
    params['radius_smoothing_factor'] = 0.8
    params['pressure_scaling_factor'] = 0.5
    params['vacancy_contribution_weight'] = 1.2

    return params


def run_temperature_sweep(
    temp_min: float = 600,
    temp_max: float = 900,
    temp_step: float = 50,
    sim_time: float = 4176980,
    verbose: bool = True
) -> List[Dict]:
    """
    Run simulations across a temperature range.

    Args:
        temp_min: Minimum temperature (K)
        temp_max: Maximum temperature (K)
        temp_step: Temperature step (K)
        sim_time: Simulation time (seconds)
        verbose: Print progress messages

    Returns:
        List of result dictionaries, one per temperature
    """
    temperatures = np.arange(temp_min, temp_max + temp_step, temp_step)
    results = []

    print_section_header(f"Temperature Sweep: {temp_min}-{temp_max} K (step: {temp_step} K)")
    print(f"Number of temperature points: {len(temperatures)}")
    print(f"Simulation time: {sim_time:.2e} seconds ({sim_time/86400:.2f} days)")

    for i, temp in enumerate(temperatures):
        if verbose:
            print(f"\n[{i+1}/{len(temperatures)}] Running at T = {temp} K...")

        try:
            # Create parameters
            params = create_model_parameters(temp)

            # Create model
            model = GasSwellingModel(params)

            # Set initial conditions
            model.initial_state[2] = 4.0  # Ncb (gas atoms per bulk cavity)
            model.initial_state[6] = 4.0  # Ncf (gas atoms per interface cavity)

            # Run simulation
            t_eval = np.linspace(0, sim_time, 100)
            result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

            # Calculate swelling
            V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
            V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
            swelling = (V_bubble_b + V_bubble_f) * 100  # Convert to percent

            # Store results
            results.append({
                'temperature': temp,
                'time': result['time'],
                'time_days': result['time'] / 86400,
                'swelling': swelling,
                'Rcb': result['Rcb'],
                'Rcf': result['Rcf'],
                'Ccb': result['Ccb'],
                'Ccf': result['Ccf'],
                'Ncb': result['Ncb'],
                'Ncf': result['Ncf'],
                'final_swelling': swelling[-1],
                'final_Rcb': result['Rcb'][-1],
                'final_Rcf': result['Rcf'][-1],
                'success': True
            })

            if verbose:
                print(f"  Final swelling: {swelling[-1]:.4f}%")
                print(f"  Final bubble radius (bulk): {result['Rcb'][-1]*1e9:.2f} nm")
                print(f"  Final bubble radius (interface): {result['Rcf'][-1]*1e9:.2f} nm")

        except Exception as e:
            if verbose:
                print(f"  ERROR: {str(e)}")

            results.append({
                'temperature': temp,
                'success': False,
                'error': str(e)
            })

    return results


def plot_swelling_vs_temperature(
    results: List[Dict],
    save_path: str = 'swelling_vs_temperature.png',
    show_plot: bool = True
):
    """
    Create a plot of final swelling vs temperature.

    Args:
        results: List of result dictionaries from run_temperature_sweep
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    # Filter successful results
    valid_results = [r for r in results if r.get('success', False)]

    if not valid_results:
        print("No valid results to plot!")
        return

    temperatures = [r['temperature'] for r in valid_results]
    final_swellings = [r['final_swelling'] for r in valid_results]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot with markers and line
    ax.plot(temperatures, final_swellings, 'bo-', linewidth=2, markersize=8,
            markeredgecolor='white', markeredgewidth=1.5, label='Total swelling')

    # Add fill under curve
    ax.fill_between(temperatures, final_swellings, alpha=0.2, color='blue')

    # Customize plot
    ax.set_xlabel('Temperature (K)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Final Swelling (%)', fontsize=12, fontweight='bold')
    ax.set_title('Temperature Dependence of Fuel Swelling',
                 fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=11)

    # Add statistics text box
    stats_text = f"Max swelling: {max(final_swellings):.3f}% at {temperatures[np.argmax(final_swellings)]} K\n"
    stats_text += f"Min swelling: {min(final_swellings):.3f}% at {temperatures[np.argmin(final_swellings)]} K\n"
    stats_text += f"Mean swelling: {np.mean(final_swellings):.3f}%"

    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_bubble_radius_vs_temperature(
    results: List[Dict],
    save_path: str = 'bubble_radius_vs_temperature.png',
    show_plot: bool = True
):
    """
    Create a plot of final bubble radius vs temperature.

    Args:
        results: List of result dictionaries from run_temperature_sweep
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    valid_results = [r for r in results if r.get('success', False)]

    if not valid_results:
        print("No valid results to plot!")
        return

    temperatures = [r['temperature'] for r in valid_results]
    Rcb_final = [r['final_Rcb'] * 1e9 for r in valid_results]  # Convert to nm
    Rcf_final = [r['final_Rcf'] * 1e9 for r in valid_results]  # Convert to nm

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot both bubble types
    ax.plot(temperatures, Rcb_final, 'o-', linewidth=2, markersize=8,
            label='Bulk bubbles', color='#2E86AB',
            markeredgecolor='white', markeredgewidth=1.5)
    ax.plot(temperatures, Rcf_final, 's-', linewidth=2, markersize=8,
            label='Interface bubbles', color='#A23B72',
            markeredgecolor='white', markeredgewidth=1.5)

    # Customize plot
    ax.set_xlabel('Temperature (K)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Final Bubble Radius (nm)', fontsize=12, fontweight='bold')
    ax.set_title('Temperature Dependence of Bubble Size',
                 fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=11)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_swelling_evolution_comparison(
    results: List[Dict],
    save_path: str = 'swelling_evolution_comparison.png',
    show_plot: bool = True
):
    """
    Create a plot comparing swelling evolution at different temperatures.

    Args:
        results: List of result dictionaries from run_temperature_sweep
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    valid_results = [r for r in results if r.get('success', False)]

    if not valid_results:
        print("No valid results to plot!")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))

    # Use colormap for different temperatures
    cmap = plt.get_cmap('viridis')
    colors = cmap(np.linspace(0, 1, len(valid_results)))

    # Plot swelling evolution for each temperature
    for i, result in enumerate(valid_results):
        ax.plot(result['time_days'], result['swelling'],
                label=f"{result['temperature']} K",
                linewidth=2, color=colors[i])

    # Customize plot
    ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Swelling (%)', fontsize=12, fontweight='bold')
    ax.set_title('Swelling Evolution at Different Temperatures',
                 fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=10, ncol=2)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_arrhenius_analysis(
    results: List[Dict],
    save_path: str = 'arrhenius_analysis.png',
    show_plot: bool = True
):
    """
    Create an Arrhenius plot for swelling rate analysis.

    The Arrhenius plot shows ln(swelling_rate) vs 1/T, which can be used
    to estimate activation energy for the swelling process.

    Args:
        results: List of result dictionaries from run_temperature_sweep
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    valid_results = [r for r in results if r.get('success', False)]

    if not valid_results or len(valid_results) < 2:
        print("Need at least 2 valid results for Arrhenius plot!")
        return

    # Calculate swelling rates (final swelling / simulation time)
    temperatures_K = np.array([r['temperature'] for r in valid_results])
    swelling_rates = np.array([r['final_swelling'] / (r['time_days'][-1] + 1e-10)
                               for r in valid_results])

    # Filter out zero or negative rates
    mask = swelling_rates > 0
    if np.sum(mask) < 2:
        print("Not enough positive swelling rates for Arrhenius plot!")
        return

    temperatures_K = temperatures_K[mask]
    swelling_rates = swelling_rates[mask]

    # Calculate Arrhenius coordinates
    inv_T = 1000 / temperatures_K  # 1000/T in K^-1
    ln_rate = np.log(swelling_rates)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot Arrhenius relationship
    ax.plot(inv_T, ln_rate, 'ro', linewidth=2, markersize=10,
            markeredgecolor='white', markeredgewidth=1.5, label='Data')

    # Fit linear trend line
    if len(inv_T) > 1:
        coeffs = np.polyfit(inv_T, ln_rate, 1)
        trend_line = np.poly1d(coeffs)
        inv_T_smooth = np.linspace(min(inv_T), max(inv_T), 100)
        ax.plot(inv_T_smooth, trend_line(inv_T_smooth), 'b--',
                linewidth=2, label='Linear fit')

        # Calculate apparent activation energy
        # Slope = -Ea/R (where R = 8.314 J/mol·K)
        # Slope is in units of K, so multiply by 1000
        slope = coeffs[0]
        Ea = -slope * 8.314 * 1000 / 1000  # kJ/mol

        ax.text(0.02, 0.02, f'Apparent Ea ≈ {Ea:.1f} kJ/mol',
                transform=ax.transAxes, fontsize=11,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    # Customize plot
    ax.set_xlabel('1000/T (K$^{-1}$)', fontsize=12, fontweight='bold')
    ax.set_ylabel('ln(Swelling Rate)', fontsize=12, fontweight='bold')
    ax.set_title('Arrhenius Plot: Temperature Dependence of Swelling Rate',
                 fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=11)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def save_results_to_csv(results: List[Dict], filename: str = 'temperature_sweep_results.csv'):
    """
    Save temperature sweep results to a CSV file.

    Args:
        results: List of result dictionaries from run_temperature_sweep
        filename: Output CSV filename
    """
    valid_results = [r for r in results if r.get('success', False)]

    if not valid_results:
        print("No valid results to save!")
        return

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['temperature', 'final_swelling', 'final_Rcb_nm', 'final_Rcf_nm',
                     'swelling_rate_per_day']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for r in valid_results:
            writer.writerow({
                'temperature': r['temperature'],
                'final_swelling': f"{r['final_swelling']:.6f}",
                'final_Rcb_nm': f"{r['final_Rcb']*1e9:.4f}",
                'final_Rcf_nm': f"{r['final_Rcf']*1e9:.4f}",
                'swelling_rate_per_day': f"{r['final_swelling']/(r['time_days'][-1]+1e-10):.8f}"
            })

    print(f"  Saved: {filename}")


def main():
    """Main function with command-line interface"""

    parser = argparse.ArgumentParser(
        description='Temperature sweep plotting example for Gas Swelling Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run temperature sweep from 600-900 K with 50 K steps
  python temperature_sweep_plotting.py --temp-range 600 900 --step 50

  # Run with custom simulation time
  python temperature_sweep_plotting.py --temp-range 700 800 --sim-time 1e6

  # Generate Arrhenius plot only
  python temperature_sweep_plotting.py --arrhenius --temp-range 600 900

  # Run without showing plots (for batch processing)
  python temperature_sweep_plotting.py --temp-range 600 900 --no-show
        """
    )

    parser.add_argument('--temp-range', nargs=2, type=float, metavar=('TMIN', 'TMAX'),
                        default=[600, 900],
                        help='Temperature range in Kelvin (default: 600 900)')
    parser.add_argument('--step', type=float, default=50,
                        help='Temperature step in Kelvin (default: 50)')
    parser.add_argument('--sim-time', type=float, default=4176980,
                        help='Simulation time in seconds (default: 4176980)')
    parser.add_argument('--output', '-o', type=str,
                        help='Output file prefix (default: auto-generated)')
    parser.add_argument('--no-show', action='store_true',
                        help='Do not display plots interactively')
    parser.add_argument('--arrhenius', action='store_true',
                        help='Generate Arrhenius plot')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress messages')

    args = parser.parse_args()

    # Print header
    if not args.quiet:
        print("\n" + "=" * 70)
        print("  TEMPERATURE SWEEP PLOTTING EXAMPLE")
        print("  Gas Swelling Model Visualization Tool")
        print("=" * 70)

    # Run temperature sweep
    results = run_temperature_sweep(
        temp_min=args.temp_range[0],
        temp_max=args.temp_range[1],
        temp_step=args.step,
        sim_time=args.sim_time,
        verbose=not args.quiet
    )

    # Check if we have any results
    valid_results = [r for r in results if r.get('success', False)]
    if not valid_results:
        print("\nNo successful simulations!")
        return 1

    if not args.quiet:
        print(f"\nSuccessful simulations: {len(valid_results)}/{len(results)}")

    # Determine output prefix
    if args.output:
        prefix = args.output
    else:
        prefix = f'temp_sweep_{args.temp_range[0]}_{args.temp_range[1]}'

    show_plots = not args.no_show

    # Generate plots
    print_section_header("Generating Plots")

    plot_swelling_vs_temperature(results, f'{prefix}_swelling.png', show_plots)
    plot_bubble_radius_vs_temperature(results, f'{prefix}_radius.png', show_plots)
    plot_swelling_evolution_comparison(results, f'{prefix}_evolution.png', show_plots)

    if args.arrhenius:
        plot_arrhenius_analysis(results, f'{prefix}_arrhenius.png', show_plots)

    # Save results to CSV
    print_section_header("Saving Results")
    save_results_to_csv(results, f'{prefix}_results.csv')

    # Summary
    if not args.quiet:
        print_section_header("Summary")
        temperatures = [r['temperature'] for r in valid_results]
        swellings = [r['final_swelling'] for r in valid_results]

        print(f"Temperature range: {min(temperatures)} - {max(temperatures)} K")
        print(f"Swelling range: {min(swellings):.4f} - {max(swellings):.4f}%")
        print(f"Peak swelling: {max(swellings):.4f}% at {temperatures[np.argmax(swellings)]} K")

        print("\n" + "=" * 70)
        print("  Temperature sweep completed successfully!")
        print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
