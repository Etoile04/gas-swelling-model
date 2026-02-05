#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radial Temperature Profile Demo
================================

This script demonstrates how to use radial temperature profiles in the
1D gas swelling model. Temperature gradients are critical in nuclear fuel
as they strongly affect swelling behavior, with higher temperatures generally
leading to increased swelling due to enhanced diffusion.

What this script does:
- Demonstrates different temperature profile types (uniform, parabolic, user-defined)
- Shows how temperature gradients affect swelling distribution
- Creates comparative visualizations of temperature effects
- Analyzes centerline vs surface swelling differences
- Generates temperature-dependent radial profiles

Key Features:
- Multiple temperature profile options
- Parabolic profile with configurable temperature gradient
- User-defined custom profiles
- Side-by-side comparisons
- Publication-quality radial profile plots
- CSV export for further analysis

Usage:
    python examples/radial_temperature_profile_demo.py --help
    python examples/radial_temperature_profile_demo.py --profiles uniform parabolic
    python examples/radial_temperature_profile_demo.py --centerline-temp 900 --surface-temp 600

Author: Gas Swelling Model Team
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
import csv
from typing import List, Dict, Optional, Tuple

# Import model components
try:
    from gas_swelling.models.radial_model import RadialGasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters
    from gas_swelling.visualization.radial_plots import RadialProfilePlotter
except ImportError:
    # Fallback for development environment
    from models.radial_model import RadialGasSwellingModel
    from params.parameters import create_default_parameters
    from visualization.radial_plots import RadialProfilePlotter

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


def create_model_parameters(
    base_temperature: float = 773.15,
    fission_rate: float = 5e19
) -> Dict:
    """
    Create base model parameters.

    Args:
        base_temperature: Base temperature in Kelvin (default: 773.15 K = 500°C)
        fission_rate: Fission rate in fissions/m³/s

    Returns:
        Dictionary of model parameters
    """
    params = create_default_parameters()

    # Set base temperature
    params['temperature'] = base_temperature

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
    params['fission_rate'] = fission_rate
    params['gas_production_rate'] = 0.5
    params['critical_radius'] = 50e-9
    params['radius_smoothing_factor'] = 0.8
    params['pressure_scaling_factor'] = 0.5
    params['vacancy_contribution_weight'] = 1.2

    return params


def run_simulation_with_profile(
    profile_type: str,
    params: Dict,
    n_nodes: int = 10,
    centerline_temp: Optional[float] = None,
    surface_temp: Optional[float] = None,
    custom_temps: Optional[np.ndarray] = None,
    sim_time: float = 8640000,
    verbose: bool = True
) -> Tuple[RadialGasSwellingModel, Dict]:
    """
    Run a simulation with the specified temperature profile.

    Args:
        profile_type: Type of temperature profile ('uniform', 'parabolic', 'user')
        params: Model parameters dictionary
        n_nodes: Number of radial nodes
        centerline_temp: Centerline temperature for parabolic profile (K)
        surface_temp: Surface temperature for parabolic profile (K)
        custom_temps: Custom temperature array for 'user' profile
        sim_time: Simulation time in seconds
        verbose: Print progress messages

    Returns:
        Tuple of (model, result_dict)
    """
    if verbose:
        print(f"\nRunning simulation with {profile_type} temperature profile...")

    try:
        # Create model with specified temperature profile
        if profile_type == 'uniform':
            model = RadialGasSwellingModel(
                params=params,
                n_nodes=n_nodes,
                temperature_profile='uniform'
            )

        elif profile_type == 'parabolic':
            # For parabolic, we need to set up the gradient
            model = RadialGasSwellingModel(
                params=params,
                n_nodes=n_nodes,
                temperature_profile='parabolic'
            )

            # Override temperature if specific values provided
            if centerline_temp is not None and surface_temp is not None:
                r_norm = np.linspace(0, 1, n_nodes)
                # Parabolic profile: T(r) = T_surface + (T_center - T_surface) * (1 - r²/R²)
                temperatures = surface_temp + (centerline_temp - surface_temp) * (1 - r_norm**2)
                model.temperature = temperatures

        elif profile_type == 'user':
            if custom_temps is None:
                raise ValueError("custom_temps must be provided for 'user' profile")

            if len(custom_temps) != n_nodes:
                raise ValueError(f"custom_temps length ({len(custom_temps)}) must match n_nodes ({n_nodes})")

            model = RadialGasSwellingModel(
                params=params,
                n_nodes=n_nodes,
                temperature_profile='user',
                temperature_data=custom_temps
            )
        else:
            raise ValueError(f"Unknown profile type: {profile_type}")

        # Run simulation
        t_eval = np.linspace(0, sim_time, 100)
        result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

        if verbose:
            temp_range = f"{model.temperature[0]:.0f} - {model.temperature[-1]:.0f} K"
            print(f"  Temperature range: {temp_range}")
            print(f"  Final centerline swelling: {result['swelling'][-1, 0]:.4f}%")
            print(f"  Final surface swelling: {result['swelling'][-1, -1]:.4f}%")
            print(f"  Average swelling: {np.mean(result['swelling'][-1, :]):.4f}%")

        return model, result

    except Exception as e:
        if verbose:
            print(f"  ERROR: {str(e)}")
        raise


def run_profile_comparison(
    profiles: List[str],
    centerline_temp: float = 900,
    surface_temp: float = 600,
    n_nodes: int = 10,
    sim_time: float = 8640000,
    verbose: bool = True
) -> List[Tuple[str, RadialGasSwellingModel, Dict]]:
    """
    Run simulations for multiple temperature profiles.

    Args:
        profiles: List of profile types to run
        centerline_temp: Centerline temperature for parabolic profile (K)
        surface_temp: Surface temperature for parabolic profile (K)
        n_nodes: Number of radial nodes
        sim_time: Simulation time in seconds
        verbose: Print progress messages

    Returns:
        List of (profile_type, model, result) tuples
    """
    results = []

    print_section_header(f"Temperature Profile Comparison")
    print(f"Profiles to compare: {', '.join(profiles)}")
    print(f"Number of radial nodes: {n_nodes}")
    print(f"Simulation time: {sim_time:.2e} seconds ({sim_time/86400:.2f} days)")

    # Create base parameters
    base_temp = (centerline_temp + surface_temp) / 2
    params = create_model_parameters(base_temperature=base_temp)

    for profile in profiles:
        try:
            if profile == 'parabolic':
                model, result = run_simulation_with_profile(
                    profile_type='parabolic',
                    params=params,
                    n_nodes=n_nodes,
                    centerline_temp=centerline_temp,
                    surface_temp=surface_temp,
                    sim_time=sim_time,
                    verbose=verbose
                )
            elif profile == 'uniform':
                # For uniform, use surface temperature as reference
                params_uniform = create_model_parameters(base_temperature=surface_temp)
                model, result = run_simulation_with_profile(
                    profile_type='uniform',
                    params=params_uniform,
                    n_nodes=n_nodes,
                    sim_time=sim_time,
                    verbose=verbose
                )
            elif profile == 'user':
                # Create a custom profile (linear gradient)
                custom_temps = np.linspace(centerline_temp, surface_temp, n_nodes)
                params_user = create_model_parameters(base_temperature=base_temp)
                model, result = run_simulation_with_profile(
                    profile_type='user',
                    params=params_user,
                    n_nodes=n_nodes,
                    custom_temps=custom_temps,
                    sim_time=sim_time,
                    verbose=verbose
                )
            else:
                print(f"  Unknown profile type: {profile}")
                continue

            results.append((profile, model, result))

        except Exception as e:
            if verbose:
                print(f"  Failed to run {profile} profile: {str(e)}")

    return results


def plot_temperature_profiles(
    results: List[Tuple[str, RadialGasSwellingModel, Dict]],
    save_path: str = 'temperature_profiles.png',
    show_plot: bool = True
):
    """
    Plot temperature profiles for comparison.

    Args:
        results: List of (profile_type, model, result) tuples
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    if not results:
        print("No results to plot!")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {
        'uniform': '#2E86AB',
        'parabolic': '#A23B72',
        'user': '#F18F01'
    }

    markers = {
        'uniform': 'o',
        'parabolic': 's',
        'user': '^'
    }

    for profile, model, _ in results:
        radius = model.mesh.nodes * 1000  # Convert to mm
        temp = model.temperature

        ax.plot(radius, temp, marker=markers.get(profile, 'o'),
                linewidth=2, markersize=8, label=profile.capitalize(),
                color=colors.get(profile, None),
                markeredgecolor='white', markeredgewidth=1.5)

    ax.set_xlabel('Radius (mm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Temperature (K)', fontsize=12, fontweight='bold')
    ax.set_title('Radial Temperature Profile Comparison',
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


def plot_swelling_profiles(
    results: List[Tuple[str, RadialGasSwellingModel, Dict]],
    save_path: str = 'swelling_profiles.png',
    show_plot: bool = True
):
    """
    Plot final swelling profiles for comparison.

    Args:
        results: List of (profile_type, model, result) tuples
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    if not results:
        print("No results to plot!")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {
        'uniform': '#2E86AB',
        'parabolic': '#A23B72',
        'user': '#F18F01'
    }

    markers = {
        'uniform': 'o',
        'parabolic': 's',
        'user': '^'
    }

    for profile, model, result in results:
        radius = model.mesh.nodes * 1000  # Convert to mm
        swelling = result['swelling'][-1, :]  # Final swelling

        ax.plot(radius, swelling, marker=markers.get(profile, 'o'),
                linewidth=2, markersize=8, label=f'{profile.capitalize()} T',
                color=colors.get(profile, None),
                markeredgecolor='white', markeredgewidth=1.5)

    ax.set_xlabel('Radius (mm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Swelling (%)', fontsize=12, fontweight='bold')
    ax.set_title('Radial Swelling Profile Comparison',
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


def plot_comprehensive_comparison(
    results: List[Tuple[str, RadialGasSwellingModel, Dict]],
    save_path: str = 'comprehensive_comparison.png',
    show_plot: bool = True
):
    """
    Create a comprehensive comparison plot with temperature and swelling.

    Args:
        results: List of (profile_type, model, result) tuples
        save_path: Path to save the plot
        show_plot: Whether to display the plot interactively
    """
    if not results:
        print("No results to plot!")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    colors = {
        'uniform': '#2E86AB',
        'parabolic': '#A23B72',
        'user': '#F18F01'
    }

    # Plot 1: Temperature profiles
    ax = axes[0, 0]
    for profile, model, _ in results:
        radius = model.mesh.nodes * 1000
        temp = model.temperature
        ax.plot(radius, temp, 'o-', linewidth=2, markersize=6,
                label=profile.capitalize(), color=colors.get(profile, None))

    ax.set_xlabel('Radius (mm)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Temperature (K)', fontsize=11, fontweight='bold')
    ax.set_title('Temperature Profiles', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=10)

    # Plot 2: Swelling profiles
    ax = axes[0, 1]
    for profile, model, result in results:
        radius = model.mesh.nodes * 1000
        swelling = result['swelling'][-1, :]
        ax.plot(radius, swelling, 's-', linewidth=2, markersize=6,
                label=profile.capitalize(), color=colors.get(profile, None))

    ax.set_xlabel('Radius (mm)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Swelling (%)', fontsize=11, fontweight='bold')
    ax.set_title('Final Swelling Profiles', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=10)

    # Plot 3: Bubble radius profiles
    ax = axes[1, 0]
    for profile, model, result in results:
        radius = model.mesh.nodes * 1000
        Rcb = result['Rcb'][-1, :] * 1e9  # Convert to nm
        ax.plot(radius, Rcb, '^-', linewidth=2, markersize=6,
                label=profile.capitalize(), color=colors.get(profile, None))

    ax.set_xlabel('Radius (mm)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Bubble Radius (nm)', fontsize=11, fontweight='bold')
    ax.set_title('Bulk Bubble Radius Profiles', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=10)

    # Plot 4: Gas concentration profiles
    ax = axes[1, 1]
    for profile, model, result in results:
        radius = model.mesh.nodes * 1000
        Cgb = result['Cgb'][-1, :]
        ax.plot(radius, Cgb, 'd-', linewidth=2, markersize=6,
                label=profile.capitalize(), color=colors.get(profile, None))

    ax.set_xlabel('Radius (mm)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Gas Concentration (atoms/m³)', fontsize=11, fontweight='bold')
    ax.set_title('Gas Concentration Profiles', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def save_results_to_csv(
    results: List[Tuple[str, RadialGasSwellingModel, Dict]],
    filename: str = 'radial_temperature_profile_results.csv'
):
    """
    Save radial profile results to a CSV file.

    Args:
        results: List of (profile_type, model, result) tuples
        filename: Output CSV filename
    """
    if not results:
        print("No results to save!")
        return

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['profile', 'radius_mm', 'temperature_K',
                     'swelling_pct', 'bubble_radius_nm',
                     'gas_concentration', 'cavity_concentration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for profile, model, result in results:
            radius = model.mesh.nodes * 1000  # mm
            temp = model.temperature
            swelling = result['swelling'][-1, :]
            Rcb = result['Rcb'][-1, :] * 1e9  # nm
            Cgb = result['Cgb'][-1, :]
            Ccb = result['Ccb'][-1, :]

            for i in range(len(radius)):
                writer.writerow({
                    'profile': profile,
                    'radius_mm': f"{radius[i]:.4f}",
                    'temperature_K': f"{temp[i]:.2f}",
                    'swelling_pct': f"{swelling[i]:.6f}",
                    'bubble_radius_nm': f"{Rcb[i]:.4f}",
                    'gas_concentration': f"{Cgb[i]:.6e}",
                    'cavity_concentration': f"{Ccb[i]:.6e}"
                })

    print(f"  Saved: {filename}")


def main():
    """Main function with command-line interface"""

    parser = argparse.ArgumentParser(
        description='Radial temperature profile demonstration for Gas Swelling Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare uniform and parabolic temperature profiles
  python radial_temperature_profile_demo.py --profiles uniform parabolic

  # Set custom temperature range for parabolic profile
  python radial_temperature_profile_demo.py --centerline-temp 900 --surface-temp 600

  # Run with user-defined linear gradient
  python radial_temperature_profile_demo.py --profiles user --centerline-temp 950 --surface-temp 650

  # Run without showing plots (for batch processing)
  python radial_temperature_profile_demo.py --profiles uniform parabolic --no-show

  # Use different number of radial nodes
  python radial_temperature_profile_demo.py --n-nodes 20 --profiles parabolic
        """
    )

    parser.add_argument('--profiles', nargs='+', type=str,
                        default=['uniform', 'parabolic'],
                        choices=['uniform', 'parabolic', 'user'],
                        help='Temperature profile types to compare (default: uniform parabolic)')
    parser.add_argument('--centerline-temp', type=float, default=900,
                        help='Centerline temperature in Kelvin (default: 900)')
    parser.add_argument('--surface-temp', type=float, default=600,
                        help='Surface temperature in Kelvin (default: 600)')
    parser.add_argument('--n-nodes', type=int, default=10,
                        help='Number of radial nodes (default: 10)')
    parser.add_argument('--sim-time', type=float, default=8640000,
                        help='Simulation time in seconds (default: 8640000 = 100 days)')
    parser.add_argument('--output', '-o', type=str,
                        help='Output file prefix (default: auto-generated)')
    parser.add_argument('--no-show', action='store_true',
                        help='Do not display plots interactively')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress messages')
    parser.add_argument('--dry-run', action='store_true',
                        help='Set up models without running full simulation')

    args = parser.parse_args()

    # Print header
    if not args.quiet:
        print("\n" + "=" * 70)
        print("  RADIAL TEMPERATURE PROFILE DEMO")
        print("  Gas Swelling Model - 1D Radial Temperature Effects")
        print("=" * 70)

    # Handle dry run
    if args.dry_run:
        if not args.quiet:
            print("\n" + "-" * 70)
            print("DRY RUN MODE: Setting up models without full simulation")
            print("-" * 70)

        params = create_model_parameters()

        for profile in args.profiles:
            print(f"\nSetting up {profile} temperature profile...")

            if profile == 'uniform':
                model = RadialGasSwellingModel(
                    params=params,
                    n_nodes=args.n_nodes,
                    temperature_profile='uniform'
                )
            elif profile == 'parabolic':
                model = RadialGasSwellingModel(
                    params=params,
                    n_nodes=args.n_nodes,
                    temperature_profile='parabolic'
                )
                # Set temperature range
                r_norm = np.linspace(0, 1, args.n_nodes)
                temps = args.surface_temp + (args.centerline_temp - args.surface_temp) * (1 - r_norm**2)
                model.temperature = temps
            elif profile == 'user':
                custom_temps = np.linspace(args.centerline_temp, args.surface_temp, args.n_nodes)
                model = RadialGasSwellingModel(
                    params=params,
                    n_nodes=args.n_nodes,
                    temperature_profile='user',
                    temperature_data=custom_temps
                )

            print(f"  Profile: {profile}")
            print(f"  Nodes: {model.n_nodes}")
            print(f"  Temperature range: {model.temperature[0]:.0f} - {model.temperature[-1]:.0f} K")

        if not args.quiet:
            print("\nDry run complete. Models are ready for simulation.")
        return 0

    # Run simulations
    results = run_profile_comparison(
        profiles=args.profiles,
        centerline_temp=args.centerline_temp,
        surface_temp=args.surface_temp,
        n_nodes=args.n_nodes,
        sim_time=args.sim_time,
        verbose=not args.quiet
    )

    # Check if we have any results
    if not results:
        print("\nNo successful simulations!")
        return 1

    if not args.quiet:
        print(f"\nSuccessful simulations: {len(results)}")

    # Determine output prefix
    if args.output:
        prefix = args.output
    else:
        profiles_str = '_'.join(args.profiles)
        prefix = f'radial_temp_profile_{profiles_str}'

    show_plots = not args.no_show

    # Generate plots
    print_section_header("Generating Plots")

    plot_temperature_profiles(results, f'{prefix}_temperature.png', show_plots)
    plot_swelling_profiles(results, f'{prefix}_swelling.png', show_plots)
    plot_comprehensive_comparison(results, f'{prefix}_comprehensive.png', show_plots)

    # Save results to CSV
    print_section_header("Saving Results")
    save_results_to_csv(results, f'{prefix}_results.csv')

    # Summary
    if not args.quiet:
        print_section_header("Summary")

        for profile, model, result in results:
            swelling = result['swelling'][-1, :]
            print(f"\n{profile.capitalize()} temperature profile:")
            print(f"  Temperature range: {model.temperature[0]:.0f} - {model.temperature[-1]:.0f} K")
            print(f"  Centerline swelling: {swelling[0]:.4f}%")
            print(f"  Surface swelling: {swelling[-1]:.4f}%")
            print(f"  Average swelling: {np.mean(swelling):.4f}%")
            print(f"  Swelling gradient: {swelling[0] - swelling[-1]:.4f}%")

        print("\n" + "=" * 70)
        print("  Radial temperature profile demo completed successfully!")
        print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
