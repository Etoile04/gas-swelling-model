#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reproduce Figure 6 - U-10Zr Swelling vs Burnup
================================================

This script reproduces Figure 6 from the reference paper:
"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase
of irradiated U-Zr and U-Pu-Zr fuel"

Figure 6 shows cavity-calculated unrestrained swelling as a function of fuel
length (burnup) for U-10Zr fuel elements irradiated in EBR-II assembly X423,
compared with experimental data.

What this script does:
- Runs simulations for U-10Zr at different temperatures (600-800 K)
- Calculates swelling evolution over burnup
- Compares model predictions with experimental data from the paper
- Generates publication-quality plots matching Figure 6

Material parameters (from Table 1 in paper):
- Dislocation density: 7e13 m^-2
- Bulk nucleation factor (Fnb): 1e-5
- Boundary nucleation factor (Fnf): 1e-5
- Surface energy: 0.5 J/m^2

Usage:
    python -m gas_swelling.validation.scripts.reproduce_figure6 --help
    python -m gas_swelling.validation.scripts.reproduce_figure6 --output figure6.png
    python -m gas_swelling.validation.scripts.reproduce_figure6 --output figure6.pdf --no-show

Author: Gas Swelling Model Team
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import model components
try:
    from gas_swelling.models.modelrk23 import GasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters
    from gas_swelling.validation.datasets import get_figure6_data
    from gas_swelling.validation.metrics import calculate_rmse, calculate_r2
except ImportError:
    # Fallback for development environment
    from models.modelrk23 import GasSwellingModel
    from params.parameters import create_default_parameters
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from validation.datasets import get_figure6_data
    from validation.metrics import calculate_rmse, calculate_r2

# Set up matplotlib for publication-quality plotting
matplotlib.rcParams['figure.dpi'] = 100
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['axes.linewidth'] = 1.0
matplotlib.rcParams['grid.alpha'] = 0.3


# U-10Zr material parameters from Table 1 in the paper
U10ZR_PARAMETERS = {
    'dislocation_density': 7e13,  # m^-2
    'Fnb': 1e-5,                  # Bulk nucleation factor
    'Fnf': 1e-5,                  # Boundary nucleation factor
    'surface_energy': 0.5,        # J/m^2
    'Dv0': 2.0e-8,               # m^2/s (vacancy diffusivity prefactor)
    'Evm': 1.28,                 # eV (vacancy migration energy)
    'Zv': 1.0,                   # Vacancy bias factor
    'Zi': 1.025,                 # Interstitial bias factor
    # Additional parameters from examples
    'Dgb_prefactor': 8.55e-12,   # m^2/s
    'Dgb_fission_term': 1.0e-40,
    'Dgf_multiplier': 1.0,
    'gas_production_rate': 0.5,
    'resolution_rate': 2.0e-5,   # s^-1
}


def print_section_header(title: str) -> None:
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_u10zr_simulation(
    temperature: float,
    fission_rate: float = 2.0e20,
    sim_time: float = 100 * 24 * 3600,
    num_points: int = 100
) -> Dict:
    """
    Run a simulation for U-10Zr material at specified temperature.

    Parameters
    ----------
    temperature : float
        Temperature in Kelvin
    fission_rate : float
        Fission rate in fissions/m^3/s
    sim_time : float
        Total simulation time in seconds
    num_points : int
        Number of time points for output

    Returns
    -------
    dict
        Simulation results dictionary containing time series and derived quantities
    """
    # Create parameters with U-10Zr specific values
    params = create_default_parameters()
    params['temperature'] = temperature
    params['fission_rate'] = fission_rate

    # Apply U-10Zr material parameters
    for key, value in U10ZR_PARAMETERS.items():
        if key not in ['temperature', 'fission_rate']:
            params[key] = value

    # Create model and run simulation
    model = GasSwellingModel(params)
    t_eval = np.linspace(0, sim_time, num_points)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    return result


def calculate_burnup(
    time_seconds: np.ndarray,
    fission_rate: float
) -> np.ndarray:
    """
    Convert simulation time to burnup in atomic percent.

    Parameters
    ----------
    time_seconds : np.ndarray
        Time array in seconds
    fission_rate : float
        Fission rate in fissions/m^3/s

    Returns
    -------
    np.ndarray
        Burnup in atomic percent (at.%)
    """
    # Approximate conversion: 1 at.% ≈ 1.15e20 fissions/m^3 for U-10Zr
    # This is a simplified conversion based on typical values
    fissions_per_atom_percent = 1.15e20  # fissions/m^3 per at.%

    total_fissions = time_seconds * fission_rate
    burnup = total_fissions / fissions_per_atom_percent

    return burnup


def plot_figure6(
    results_dict: Dict[float, Dict],
    experimental_data: List[Dict],
    output_path: Optional[str] = None,
    show_plot: bool = True
) -> None:
    """
    Create Figure 6 reproduction plot.

    Parameters
    ----------
    results_dict : dict
        Dictionary mapping temperature to simulation results
    experimental_data : list
        List of experimental data points from the paper
    output_path : str, optional
        Path to save the figure
    show_plot : bool
        Whether to display the plot interactively
    """
    print_section_header("Creating Figure 6 Reproduction Plot")

    # Create figure with proper size for publication
    fig, ax = plt.subplots(figsize=(8, 6))

    # Colors for different temperatures
    colors = {
        600: '#1f77b4',  # Blue
        700: '#d62728',  # Red
        800: '#2ca02c',  # Green
    }

    # Plot model predictions for each temperature
    for temp in sorted(results_dict.keys()):
        result = results_dict[temp]
        time_days = result['time'] / (24 * 3600)

        # Calculate burnup
        fission_rate = result.get('fission_rate', 2.0e20)
        burnup = calculate_burnup(result['time'], fission_rate)

        # Calculate swelling
        V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
        V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
        swelling = (V_bubble_b + V_bubble_f) * 100  # Convert to percent

        # Plot model prediction as line
        ax.plot(burnup, swelling,
                linewidth=2.5,
                color=colors.get(temp, 'gray'),
                label=f'Model {temp} K',
                alpha=0.8)

        print(f"  T={temp}K: Final swelling = {swelling[-1]:.2f}% at burnup = {burnup[-1]:.2f}%")

    # Plot experimental data points
    exp_burnup_04 = []
    exp_swelling_04 = []
    exp_temp_04 = []

    exp_burnup_09 = []
    exp_swelling_09 = []
    exp_temp_09 = []

    for data_point in experimental_data:
        if data_point.get('data_type') == 'experimental':
            burnup = data_point['burnup_at_percent']
            swelling = data_point['swelling_percent']
            temp = data_point['temperature_k']

            if abs(burnup - 0.4) < 0.1:
                exp_burnup_04.append(burnup)
                exp_swelling_04.append(swelling)
                exp_temp_04.append(temp)
            elif abs(burnup - 0.9) < 0.1:
                exp_burnup_09.append(burnup)
                exp_swelling_09.append(swelling)
                exp_temp_09.append(temp)

    # Plot experimental points
    if exp_burnup_04:
        ax.scatter(exp_burnup_04, exp_swelling_04,
                   s=100, marker='o',
                   facecolors='none', edgecolors='black',
                   linewidth=2, label='Experimental (0.4 at.%)', zorder=5)

    if exp_burnup_09:
        ax.scatter(exp_burnup_09, exp_swelling_09,
                   s=100, marker='s',
                   facecolors='none', edgecolors='black',
                   linewidth=2, label='Experimental (0.9 at.%)', zorder=5)

    # Customize plot
    ax.set_xlabel('Burnup (at.%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Swelling (%)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 6: U-10Zr Swelling vs Burnup\\n(EBR-II Assembly X423)',
                 fontsize=13, fontweight='bold')

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 3.5)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add legend
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

    # Add reference text
    ax.text(0.98, 0.02,
            'Reference: "Kinetics of fission-gas-bubble-nucleated\\nvoid swelling of the alpha-uranium phase\\nof irradiated U-Zr and U-Pu-Zr fuel"',
            transform=ax.transAxes,
            fontsize=7,
            verticalalignment='bottom',
            horizontalalignment='right',
            style='italic',
            alpha=0.7)

    plt.tight_layout()

    # Save figure
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Determine format from extension
        fmt = output_file.suffix.lstrip('.')
        if fmt in ['pdf', 'png', 'svg', 'eps']:
            plt.savefig(output_path, bbox_inches='tight', format=fmt)
            print(f"  Saved: {output_path}")
        else:
            plt.savefig(output_path, bbox_inches='tight')
            print(f"  Saved: {output_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def calculate_validation_metrics(
    results_dict: Dict[float, Dict],
    experimental_data: List[Dict]
) -> Dict:
    """
    Calculate validation metrics comparing model predictions with experimental data.

    Parameters
    ----------
    results_dict : dict
        Dictionary mapping temperature to simulation results
    experimental_data : list
        List of experimental data points from the paper

    Returns
    -------
    dict
        Dictionary containing RMSE, R², and other validation metrics
    """
    print_section_header("Calculating Validation Metrics")

    metrics = {
        'temperatures': [],
        'rmse': [],
        'r2': [],
        'max_error': []
    }

    for temp, result in results_dict.items():
        # Get model prediction at experimental burnup points
        fission_rate = result.get('fission_rate', 2.0e20)
        burnup = calculate_burnup(result['time'], fission_rate)

        V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
        V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
        model_swelling = (V_bubble_b + V_bubble_f) * 100

        # Find experimental data for this temperature
        exp_burnup = []
        exp_swelling = []
        model_swelling_at_exp = []

        for data_point in experimental_data:
            if (data_point.get('data_type') == 'experimental' and
                abs(data_point['temperature_k'] - temp) < 20):

                exp_burnup_val = data_point['burnup_at_percent']
                exp_swelling_val = data_point['swelling_percent']

                # Interpolate model prediction to experimental burnup
                model_swell_at_burnup = np.interp(exp_burnup_val, burnup, model_swelling)

                exp_burnup.append(exp_burnup_val)
                exp_swelling.append(exp_swelling_val)
                model_swelling_at_exp.append(model_swell_at_burnup)

        if len(exp_swelling) > 0:
            rmse = calculate_rmse(exp_swelling, model_swelling_at_exp)
            r2 = calculate_r2(exp_swelling, model_swelling_at_exp)
            max_err = calculate_max_error(exp_swelling, model_swelling_at_exp)

            metrics['temperatures'].append(temp)
            metrics['rmse'].append(rmse)
            metrics['r2'].append(r2)
            metrics['max_error'].append(max_err)

            print(f"  T = {temp} K:")
            print(f"    RMSE: {rmse:.4f}%")
            print(f"    R²: {r2:.4f}")
            print(f"    Max Error: {max_err:.4f}%")

    return metrics


def calculate_max_error(y_true, y_pred):
    """Calculate maximum absolute error"""
    from gas_swelling.validation.metrics import calculate_max_error as _calc
    return _calc(y_true, y_pred)


def main():
    """Main function with command-line interface"""

    parser = argparse.ArgumentParser(
        description='Reproduce Figure 6 - U-10Zr Swelling vs Burnup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m gas_swelling.validation.scripts.reproduce_figure6
  python -m gas_swelling.validation.scripts.reproduce_figure6 --output figure6.png
  python -m gas_swelling.validation.scripts.reproduce_figure6 --output figure6.pdf --no-show
        """
    )

    parser.add_argument('--output', '-o',
                        type=str,
                        default=None,
                        help='Output filename for the figure (e.g., figure6.png, figure6.pdf)')
    parser.add_argument('--no-show',
                        action='store_true',
                        help='Do not display the plot interactively (useful for batch runs)')
    parser.add_argument('--fission-rate',
                        type=float,
                        default=2.0e20,
                        help='Fission rate in fissions/m^3/s (default: 2.0e20)')
    parser.add_argument('--sim-time',
                        type=float,
                        default=100,
                        help='Simulation time in days (default: 100)')
    parser.add_argument('--temperatures',
                        type=str,
                        default='600,700,800',
                        help='Comma-separated list of temperatures in Kelvin (default: 600,700,800)')

    args = parser.parse_args()

    # Parse temperatures
    temperatures = [float(t) for t in args.temperatures.split(',')]

    print("\n" + "=" * 70)
    print("  FIGURE 6 REPRODUCTION - U-10Zr SWELLING VS BURNUP")
    print("=" * 70)
    print(f"\nTemperatures: {temperatures} K")
    print(f"Fission rate: {args.fission_rate:.2e} fissions/m³/s")
    print(f"Simulation time: {args.sim_time} days")

    # Get experimental data
    try:
        experimental_data = get_figure6_data()
        print(f"\nLoaded {len(experimental_data)} experimental data points")
    except Exception as e:
        print(f"\nWarning: Could not load experimental data: {e}")
        experimental_data = []

    # Run simulations at different temperatures
    print_section_header("Running Simulations")

    sim_time_seconds = args.sim_time * 24 * 3600
    results_dict = {}

    for temp in temperatures:
        print(f"\nRunning simulation at T = {temp} K...")
        try:
            result = run_u10zr_simulation(
                temperature=temp,
                fission_rate=args.fission_rate,
                sim_time=sim_time_seconds,
                num_points=100
            )
            results_dict[temp] = result
            print(f"  Completed: T = {temp} K")
        except Exception as e:
            print(f"  Error at T = {temp} K: {e}")
            import traceback
            traceback.print_exc()

    if not results_dict:
        print("\nError: No simulations completed successfully")
        return 1

    # Create plot
    plot_figure6(
        results_dict=results_dict,
        experimental_data=experimental_data,
        output_path=args.output,
        show_plot=not args.no_show
    )

    # Calculate validation metrics if experimental data is available
    if experimental_data:
        try:
            metrics = calculate_validation_metrics(results_dict, experimental_data)
            print_section_header("Validation Summary")
            print(f"  Average RMSE: {np.mean(metrics['rmse']):.4f}%")
            print(f"  Average R²: {np.mean(metrics['r2']):.4f}")
        except Exception as e:
            print(f"\nWarning: Could not calculate validation metrics: {e}")

    print("\n" + "=" * 70)
    print("  Figure 6 reproduction completed successfully!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
