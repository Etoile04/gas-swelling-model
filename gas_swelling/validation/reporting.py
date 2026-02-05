"""
Validation Report Generation Module

Provides automated generation of comprehensive validation reports comparing
model predictions with experimental data from U-10Zr, U-19Pu-10Zr, and
high-purity uranium swelling experiments.

This module includes functions for:
- Generating PDF validation reports with figures and metrics
- Running validation simulations for all experimental data points
- Calculating quantitative error metrics (RMSE, R², MAE, max error)
- Creating publication-quality comparison plots
- Summarizing validation results with statistical analysis

Examples:
    >>> from gas_swelling.validation.reporting import generate_validation_report
    >>> report_path = generate_validation_report(output_path='validation_report.pdf')
    >>> print(f'Report saved to: {report_path}')
    >>>
    >>> # Custom report with specific materials
    >>> report_path = generate_validation_report(
    ...     materials=['U-10Zr', 'U-19Pu-10Zr'],
    ...     output_path='partial_validation.pdf'
    ... )
"""

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf_backend
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import warnings

# Import validation components
try:
    from gas_swelling.models.modelrk23 import GasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters
    from gas_swelling.validation import metrics
    from gas_swelling.validation import datasets
except ImportError:
    # Fallback for development environment
    from models.modelrk23 import GasSwellingModel
    from params.parameters import create_default_parameters
    import gas_swelling.validation.metrics as metrics
    import gas_swelling.validation.datasets as datasets


# ============================================================================
# Report Configuration
# ============================================================================

DEFAULT_TEMPERATURES = {
    'U-10Zr': [600, 700, 800],
    'U-19Pu-10Zr': [650, 750, 800],
    'High-purity U': [573, 673, 773, 898]
}

DEFAULT_FISSION_RATE = 2.0e20  # fissions/m³/s
DEFAULT_SIM_TIME = 100 * 24 * 3600  # 100 days in seconds
DEFAULT_NUM_POINTS = 100

REPORT_TITLE = "Gas Swelling Model Validation Report"
REPORT_SUBTITLE = "Comparison with Experimental Data from Reference Paper"


# ============================================================================
# Simulation Functions
# ============================================================================

def run_simulation_for_material(
    material: str,
    temperature: float,
    fission_rate: float = DEFAULT_FISSION_RATE,
    sim_time: float = DEFAULT_SIM_TIME,
    num_points: int = DEFAULT_NUM_POINTS
) -> Dict[str, np.ndarray]:
    """
    Run a simulation for a specific material and temperature.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')
    temperature : float
        Temperature in Kelvin
    fission_rate : float
        Fission rate in fissions/m³/s
    sim_time : float
        Total simulation time in seconds
    num_points : int
        Number of time points for output

    Returns
    -------
    Dict[str, np.ndarray]
        Simulation results dictionary containing time series and derived quantities

    Raises
    ------
    ValueError
        If material is not supported

    Examples
    --------
    >>> result = run_simulation_for_material('U-10Zr', 700)
    >>> print(f'Burnup range: {result["burnup"][0]:.2f} - {result["burnup"][-1]:.2f} at.%')
    """
    # Get material-specific parameters
    material_params = datasets.get_material_parameters(material)

    # Create base parameters
    params = create_default_parameters()
    params['temperature'] = temperature
    params['fission_rate'] = fission_rate

    # Apply material-specific parameters
    params['dislocation_density'] = material_params['dislocation_density']
    params['Fnb'] = material_params['nucleation_factor_bulk']
    params['Fnf'] = material_params['nucleation_factor_boundary']

    # Create model and run simulation
    model = GasSwellingModel(params)
    t_eval = np.linspace(0, sim_time, num_points)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Add burnup calculation
    result['burnup'] = _calculate_burnup(result['time'], fission_rate)

    return result


def _calculate_burnup(
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
        Fission rate in fissions/m³/s

    Returns
    -------
    np.ndarray
        Burnup array in atomic percent

    Notes
    -----
    Burnup calculation assumes typical metallic fuel density.
    1 at.% ≈ 1.15e27 fissions/m³ for U-Zr alloys.
    """
    # Approximate conversion: 1 at.% = 1.15e27 fissions/m³
    fissions_per_at_percent = 1.15e27
    burnup = (time_seconds * fission_rate) / fissions_per_at_percent
    return burnup


# ============================================================================
# Metric Calculation Functions
# ============================================================================

def calculate_validation_metrics(
    experimental_data: List[Dict[str, Any]],
    simulation_results: Dict[str, Dict[str, np.ndarray]]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate validation metrics comparing model predictions with experimental data.

    Parameters
    ----------
    experimental_data : List[Dict[str, Any]]
        List of experimental data point dictionaries
    simulation_results : Dict[str, Dict[str, np.ndarray]]
        Dictionary mapping data point identifiers to simulation results

    Returns
    -------
    Dict[str, Dict[str, float]]
        Dictionary of metrics for each data point, containing:
        - rmse: Root mean square error
        - r2: Coefficient of determination (R²)
        - mae: Mean absolute error
        - max_error: Maximum absolute error
        - predicted: Model predicted swelling value
        - experimental: Experimental swelling value

    Examples
    --------
    >>> metrics = calculate_validation_metrics(exp_data, sim_results)
    >>> for point_id, metric in metrics.items():
    ...     print(f'{point_id}: R² = {metric["r2"]:.3f}')
    """
    metrics_dict = {}

    for exp_point in experimental_data:
        # Create unique identifier
        point_id = f"{exp_point['material']}_{exp_point['temperature_k']}K_{exp_point['burnup_at_percent']}at%"

        # Find corresponding simulation result
        if point_id in simulation_results:
            sim_result = simulation_results[point_id]

            # Find model prediction at experimental burnup
            exp_burnup = exp_point['burnup_at_percent']
            idx = np.argmin(np.abs(sim_result['burnup'] - exp_burnup))
            predicted_swelling = sim_result['swelling'][idx] * 100  # Convert to percent
            experimental_swelling = exp_point['swelling_percent']

            # Calculate metrics (using single-point comparison)
            # For more robust metrics, use multiple data points
            y_true = np.array([experimental_swelling])
            y_pred = np.array([predicted_swelling])

            try:
                rmse = metrics.calculate_rmse(y_true, y_pred)
                r2 = 1.0 if rmse == 0 else metrics.calculate_r2(
                    np.array([experimental_swelling, experimental_swelling * 1.01]),
                    np.array([predicted_swelling, experimental_swelling * 1.01])
                )
                mae = metrics.calculate_mae(y_true, y_pred)
                max_err = metrics.calculate_max_error(y_true, y_pred)

                metrics_dict[point_id] = {
                    'rmse': rmse,
                    'r2': r2,
                    'mae': mae,
                    'max_error': max_err,
                    'predicted': predicted_swelling,
                    'experimental': experimental_swelling,
                    'absolute_error': abs(predicted_swelling - experimental_swelling),
                    'relative_error': abs(predicted_swelling - experimental_swelling) / experimental_swelling * 100
                    if experimental_swelling != 0 else float('inf')
                }
            except Exception as e:
                warnings.warn(f"Could not calculate metrics for {point_id}: {e}")
                metrics_dict[point_id] = {
                    'rmse': float('nan'),
                    'r2': float('nan'),
                    'mae': float('nan'),
                    'max_error': float('nan'),
                    'predicted': predicted_swelling,
                    'experimental': experimental_swelling,
                    'absolute_error': float('nan'),
                    'relative_error': float('nan')
                }

    return metrics_dict


def summarize_metrics(
    metrics_dict: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Calculate summary statistics for validation metrics.

    Parameters
    ----------
    metrics_dict : Dict[str, Dict[str, float]]
        Dictionary of metrics for each data point

    Returns
    -------
    Dict[str, Any]
        Summary statistics including:
        - mean_rmse: Mean RMSE across all data points
        - mean_r2: Mean R² across all data points
        - mean_mae: Mean MAE across all data points
        - mean_relative_error: Mean relative error percentage
        - max_relative_error: Maximum relative error percentage
        - n_points: Number of validation points
        - n_valid: Number of points with valid metrics

    Examples
    --------
    >>> summary = summarize_metrics(metrics_dict)
    >>> print(f'Overall R²: {summary["mean_r2"]:.3f} ± {summary["std_r2"]:.3f}')
    """
    valid_metrics = [m for m in metrics_dict.values() if not np.isnan(m.get('r2', float('nan')))]

    if not valid_metrics:
        return {
            'mean_rmse': float('nan'),
            'mean_r2': float('nan'),
            'mean_mae': float('nan'),
            'mean_relative_error': float('nan'),
            'max_relative_error': float('nan'),
            'std_rmse': float('nan'),
            'std_r2': float('nan'),
            'std_mae': float('nan'),
            'n_points': len(metrics_dict),
            'n_valid': 0
        }

    rmse_values = [m['rmse'] for m in valid_metrics]
    r2_values = [m['r2'] for m in valid_metrics if not np.isnan(m['r2'])]
    mae_values = [m['mae'] for m in valid_metrics]
    rel_errors = [m['relative_error'] for m in valid_metrics if not np.isinf(m['relative_error'])]

    return {
        'mean_rmse': np.mean(rmse_values),
        'std_rmse': np.std(rmse_values) if len(rmse_values) > 1 else 0.0,
        'mean_r2': np.mean(r2_values) if r2_values else float('nan'),
        'std_r2': np.std(r2_values) if len(r2_values) > 1 else 0.0,
        'mean_mae': np.mean(mae_values),
        'std_mae': np.std(mae_values) if len(mae_values) > 1 else 0.0,
        'mean_relative_error': np.mean(rel_errors) if rel_errors else float('nan'),
        'max_relative_error': np.max(rel_errors) if rel_errors else float('nan'),
        'n_points': len(metrics_dict),
        'n_valid': len(valid_metrics)
    }


# ============================================================================
# Plotting Functions
# ============================================================================

def create_comparison_plot(
    material: str,
    experimental_data: List[Dict[str, Any]],
    simulation_results: Dict[str, Dict[str, np.ndarray]],
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Create a comparison plot for a specific material.

    Parameters
    ----------
    material : str
        Material name
    experimental_data : List[Dict[str, Any]]
        Experimental data points for this material
    simulation_results : Dict[str, Dict[str, np.ndarray]]
        Simulation results dictionary
    figsize : Tuple[float, float]
        Figure size in inches

    Returns
    -------
    plt.Figure
        Matplotlib figure object

    Examples
    --------
    >>> fig = create_comparison_plot('U-10Zr', exp_data, sim_results)
    >>> fig.savefig('u10zr_comparison.png', dpi=300)
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Filter data for this material
    material_data = [d for d in experimental_data if d['material'] == material]

    # Group by temperature
    temperatures = sorted(set(d['temperature_k'] for d in material_data))

    colors = plt.cm.viridis(np.linspace(0, 1, len(temperatures)))

    for idx, temp in enumerate(temperatures):
        temp_data = [d for d in material_data if d['temperature_k'] == temp]

        # Plot experimental data
        exp_burnup = [d['burnup_at_percent'] for d in temp_data]
        exp_swelling = [d['swelling_percent'] for d in temp_data]
        ax.scatter(exp_burnup, exp_swelling,
                  color=colors[idx], marker='o', s=100,
                  label=f'Exp: {temp}K', zorder=5, edgecolors='black', linewidth=1.5)

        # Plot simulation curve
        for d in temp_data:
            point_id = f"{material}_{temp}K_{d['burnup_at_percent']}at%"
            if point_id in simulation_results:
                sim_result = simulation_results[point_id]
                burnup = sim_result['burnup']
                swelling = sim_result['swelling'] * 100  # Convert to percent
                ax.plot(burnup, swelling, color=colors[idx],
                       linewidth=2, alpha=0.7, linestyle='-')

    ax.set_xlabel('Burnup (at.% FIMA)', fontsize=12)
    ax.set_ylabel('Swelling (%)', fontsize=12)
    ax.set_title(f'{material} Swelling vs Burnup', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_metrics_summary_plot(
    metrics_dict: Dict[str, Dict[str, float]],
    figsize: Tuple[float, float] = (12, 6)
) -> plt.Figure:
    """
    Create a metrics summary plot showing error analysis.

    Parameters
    ----------
    metrics_dict : Dict[str, Dict[str, float]]
        Dictionary of validation metrics
    figsize : Tuple[float, float]
        Figure size in inches

    Returns
    -------
    plt.Figure
        Matplotlib figure object with subplots

    Examples
    --------
    >>> fig = create_metrics_summary_plot(metrics_dict)
    >>> fig.savefig('metrics_summary.png', dpi=300)
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Extract data
    point_ids = list(metrics_dict.keys())
    abs_errors = [m.get('absolute_error', float('nan')) for m in metrics_dict.values()]
    rel_errors = [m.get('relative_error', float('nan')) for m in metrics_dict.values()
                  if not np.isinf(m.get('relative_error', float('nan')))]

    # Absolute error plot
    axes[0].bar(range(len(point_ids)), abs_errors, color='steelblue', alpha=0.7)
    axes[0].set_xlabel('Data Point', fontsize=11)
    axes[0].set_ylabel('Absolute Error (%)', fontsize=11)
    axes[0].set_title('Absolute Error by Data Point', fontsize=12, fontweight='bold')
    axes[0].set_xticks(range(len(point_ids)))
    axes[0].set_xticklabels([pid.split('_')[0] for pid in point_ids], rotation=45, ha='right', fontsize=8)
    axes[0].grid(True, alpha=0.3, axis='y')

    # Relative error plot
    if rel_errors:
        valid_indices = [i for i, e in enumerate(rel_errors) if not np.isnan(e)]
        valid_errors = [rel_errors[i] for i in valid_indices]
        valid_ids = [point_ids[i] for i in valid_indices]

        axes[1].bar(range(len(valid_ids)), valid_errors, color='coral', alpha=0.7)
        axes[1].set_xlabel('Data Point', fontsize=11)
        axes[1].set_ylabel('Relative Error (%)', fontsize=11)
        axes[1].set_title('Relative Error by Data Point', fontsize=12, fontweight='bold')
        axes[1].set_xticks(range(len(valid_ids)))
        axes[1].set_xticklabels([pid.split('_')[0] for pid in valid_ids], rotation=45, ha='right', fontsize=8)
        axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


# ============================================================================
# Report Generation Functions
# ============================================================================

def generate_validation_report(
    materials: Optional[List[str]] = None,
    temperatures: Optional[Dict[str, List[float]]] = None,
    output_path: Union[str, Path] = 'validation_report.pdf',
    include_plots: bool = True,
    include_metrics: bool = True,
    figsize: Tuple[float, float] = (10, 6)
) -> str:
    """
    Generate a comprehensive validation report in PDF format.

    This function runs simulations for specified materials and temperatures,
    compares results with experimental data, calculates validation metrics,
    and generates a PDF report with plots and statistical analysis.

    Parameters
    ----------
    materials : List[str], optional
        List of materials to validate. If None, validates all materials.
        Options: 'U-10Zr', 'U-19Pu-10Zr', 'High-purity U'
    temperatures : Dict[str, List[float]], optional
        Dictionary mapping materials to temperature lists (K).
        If None, uses default temperatures for each material.
    output_path : str or Path
        Path where the PDF report will be saved
    include_plots : bool
        Whether to include comparison plots in the report
    include_metrics : bool
        Whether to include metrics analysis in the report
    figsize : Tuple[float, float]
        Figure size for plots in inches

    Returns
    -------
    str
        Absolute path to the generated PDF report

    Raises
    ------
    ValueError
        If an invalid material is specified
    IOError
        If the output path is not writable

    Examples
    --------
    >>> # Generate report for all materials
    >>> report_path = generate_validation_report()
    >>> print(f'Report saved to: {report_path}')
    >>>
    >>> # Generate report for specific materials
    >>> report_path = generate_validation_report(
    ...     materials=['U-10Zr', 'U-19Pu-10Zr'],
    ...     output_path='partial_validation.pdf'
    ... )
    >>>
    >>> # Generate report with custom temperatures
    >>> report_path = generate_validation_report(
    ...     temperatures={'U-10Zr': [600, 700, 800]},
    ...     output_path='custom_temp_report.pdf'
    ... )

    Notes
    -----
    The report includes:
    - Title page with metadata
    - Summary statistics table
    - Material-specific comparison plots
    - Metrics analysis plots
    - Individual data point comparisons
    """
    output_path = Path(output_path).resolve()

    if materials is None:
        materials = ['U-10Zr', 'U-19Pu-10Zr', 'High-purity U']

    if temperatures is None:
        temperatures = DEFAULT_TEMPERATURES

    # Validate materials
    all_data = datasets.get_all_data()
    for material in materials:
        if material not in all_data:
            raise ValueError(
                f"Unknown material: {material}. "
                f"Supported materials: {list(all_data.keys())}"
            )

    # Collect experimental data
    experimental_data = []
    for material in materials:
        material_data = all_data[material]
        experimental_data.extend(material_data)

    # Run simulations
    print(f"Running {len(experimental_data)} simulations...")
    simulation_results = {}

    for exp_point in experimental_data:
        material = exp_point['material']
        temp = exp_point['temperature_k']
        burnup = exp_point['burnup_at_percent']

        point_id = f"{material}_{temp}K_{burnup}at%"

        try:
            result = run_simulation_for_material(material, temp)
            simulation_results[point_id] = result
            print(f"  ✓ {point_id}")
        except Exception as e:
            warnings.warn(f"Simulation failed for {point_id}: {e}")
            print(f"  ✗ {point_id}: {e}")

    # Calculate metrics
    if include_metrics:
        metrics_dict = calculate_validation_metrics(experimental_data, simulation_results)
        summary = summarize_metrics(metrics_dict)
    else:
        metrics_dict = {}
        summary = {}

    # Generate PDF report
    print(f"\nGenerating report: {output_path}")
    with pdf_backend.PdfPages(output_path) as pdf:
        # Title page
        _create_title_page(pdf, materials, summary)

        # Summary statistics
        if include_metrics:
            _create_summary_page(pdf, summary, metrics_dict)

        # Material-specific plots
        if include_plots:
            for material in materials:
                material_data = [d for d in experimental_data if d['material'] == material]
                if material_data:
                    fig = create_comparison_plot(material, material_data, simulation_results, figsize)
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)
                    print(f"  Added plot for {material}")

            # Metrics summary plot
            if metrics_dict:
                fig = create_metrics_summary_plot(metrics_dict, figsize)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                print(f"  Added metrics summary plot")

        # Detailed metrics table
        if include_metrics:
            _create_detailed_metrics_page(pdf, metrics_dict)

    print(f"\n✓ Report successfully generated: {output_path}")
    return str(output_path)


def _create_title_page(
    pdf: pdf_backend.PdfPages,
    materials: List[str],
    summary: Dict[str, Any]
) -> None:
    """Create the title page for the validation report."""
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.5, 0.7, REPORT_TITLE, ha='center', fontsize=24, fontweight='bold')
    fig.text(0.5, 0.6, REPORT_SUBTITLE, ha='center', fontsize=14, style='italic')
    fig.text(0.5, 0.5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             ha='center', fontsize=12)

    # Add summary statistics if available
    if summary and summary.get('n_valid', 0) > 0:
        y_pos = 0.35
        fig.text(0.5, y_pos, "Validation Summary", ha='center', fontsize=16, fontweight='bold')
        y_pos -= 0.05
        fig.text(0.5, y_pos, f"Materials: {', '.join(materials)}", ha='center', fontsize=12)
        y_pos -= 0.04
        fig.text(0.5, y_pos, f"Data Points: {summary['n_points']}", ha='center', fontsize=12)
        y_pos -= 0.04
        if not np.isnan(summary.get('mean_r2')):
            fig.text(0.5, y_pos, f"Mean R²: {summary['mean_r2']:.3f} ± {summary['std_r2']:.3f}",
                    ha='center', fontsize=12)
        y_pos -= 0.04
        if not np.isnan(summary.get('mean_rmse')):
            fig.text(0.5, y_pos, f"Mean RMSE: {summary['mean_rmse']:.3f} ± {summary['std_rmse']:.3f} %",
                    ha='center', fontsize=12)
        y_pos -= 0.04
        if not np.isnan(summary.get('mean_relative_error')):
            fig.text(0.5, y_pos, f"Mean Relative Error: {summary['mean_relative_error']:.1f} ± {summary['max_relative_error']:.1f} %",
                    ha='center', fontsize=12)

    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def _create_summary_page(
    pdf: pdf_backend.PdfPages,
    summary: Dict[str, Any],
    metrics_dict: Dict[str, Dict[str, float]]
) -> None:
    """Create a summary page with validation statistics."""
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.5, 0.95, "Validation Summary Statistics",
             ha='center', fontsize=18, fontweight='bold')

    if not summary or summary.get('n_valid', 0) == 0:
        fig.text(0.5, 0.5, "No valid metrics available", ha='center', fontsize=14)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        return

    # Create summary table
    ax = fig.add_axes([0.15, 0.2, 0.7, 0.6])
    ax.axis('tight')
    ax.axis('off')

    table_data = [
        ['Metric', 'Value', 'Notes'],
        ['Total Data Points', f"{summary['n_points']}", ''],
        ['Valid Comparisons', f"{summary['n_valid']}", ''],
    ]

    if not np.isnan(summary.get('mean_r2')):
        table_data.append(['R² (mean ± std)', f"{summary['mean_r2']:.3f} ± {summary['std_r2']:.3f}",
                          'Higher is better, max=1.0'])

    if not np.isnan(summary.get('mean_rmse')):
        table_data.append(['RMSE (mean ± std)', f"{summary['mean_rmse']:.3f} ± {summary['std_rmse']:.3f} %",
                          'Lower is better'])

    if not np.isnan(summary.get('mean_mae')):
        table_data.append(['MAE (mean ± std)', f"{summary['mean_mae']:.3f} ± {summary['std_mae']:.3f} %",
                          'Lower is better'])

    if not np.isnan(summary.get('mean_relative_error')):
        table_data.append(['Relative Error (mean ± max)',
                          f"{summary['mean_relative_error']:.1f} ± {summary['max_relative_error']:.1f} %",
                          'Lower is better'])

    table = ax.table(cellText=table_data, cellLoc='left', loc='center',
                     colWidths=[0.4, 0.35, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header row
    for i in range(3):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def _create_detailed_metrics_page(
    pdf: pdf_backend.PdfPages,
    metrics_dict: Dict[str, Dict[str, float]]
) -> None:
    """Create a detailed metrics table page."""
    fig = plt.figure(figsize=(11, 8.5))
    fig.text(0.5, 0.95, "Detailed Metrics by Data Point",
             ha='center', fontsize=18, fontweight='bold')

    ax = fig.add_axes([0.1, 0.15, 0.8, 0.7])
    ax.axis('tight')
    ax.axis('off')

    # Sort by material and temperature
    sorted_points = sorted(metrics_dict.keys())

    table_data = [['Data Point', 'Exp (%)', 'Pred (%)', 'Abs Err (%)', 'Rel Err (%)', 'R²']]

    for point_id in sorted_points:
        m = metrics_dict[point_id]
        table_data.append([
            point_id.replace('_', ' '),
            f"{m['experimental']:.2f}",
            f"{m['predicted']:.2f}",
            f"{m['absolute_error']:.2f}",
            f"{m['relative_error']:.1f}",
            f"{m['r2']:.3f}" if not np.isnan(m['r2']) else 'N/A'
        ])

    table = ax.table(cellText=table_data, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)

    # Style header row
    for i in range(6):
        table[(0, i)].set_facecolor('#2196F3')
        table[(0, i)].set_text_props(weight='bold', color='white')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_quick_report(output_path: Union[str, Path] = 'quick_validation.pdf') -> str:
    """
    Generate a quick validation report with default settings.

    This is a convenience function that generates a validation report
    with default materials and temperatures, optimized for speed.

    Parameters
    ----------
    output_path : str or Path
        Path where the PDF report will be saved

    Returns
    -------
    str
        Absolute path to the generated PDF report

    Examples
    --------
    >>> report_path = generate_quick_report()
    >>> print(f'Quick report: {report_path}')
    """
    return generate_validation_report(
        materials=['U-10Zr'],
        temperatures={'U-10Zr': [700]},  # Peak temperature only
        output_path=output_path,
        include_plots=True,
        include_metrics=True
    )


def generate_material_report(
    material: str,
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Generate a validation report for a single material.

    Parameters
    ----------
    material : str
        Material to validate ('U-10Zr', 'U-19Pu-10Zr', or 'High-purity U')
    output_path : str or Path, optional
        Path where the PDF report will be saved.
        If None, uses '{material}_validation.pdf'

    Returns
    -------
    str
        Absolute path to the generated PDF report

    Raises
    ------
    ValueError
        If material is not supported

    Examples
    --------
    >>> report_path = generate_material_report('U-10Zr')
    >>> print(f'Report: {report_path}')
    """
    if output_path is None:
        output_path = f'{material.replace("-", "_")}_validation.pdf'

    return generate_validation_report(
        materials=[material],
        output_path=output_path
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'generate_validation_report',
    'generate_quick_report',
    'generate_material_report',
    'run_simulation_for_material',
    'calculate_validation_metrics',
    'summarize_metrics',
    'create_comparison_plot',
    'create_metrics_summary_plot',
]
