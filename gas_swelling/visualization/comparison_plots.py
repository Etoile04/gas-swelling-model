"""
Comparison and Analysis Plots Module

Provides plotting functions for comparative visualizations between bulk and
interface behavior, gas distribution analysis, and other comparison plots.

This module includes functions for:
- Bulk vs phase boundary behavior comparisons
- Side-by-side comparison plots
- Gas distribution pie charts and analysis
- Cross-correlation analysis plots
- Multi-variable comparison visualizations

Examples:
    >>> from gas_swelling.visualization.comparison_plots import compare_bulk_interface
    >>> fig = compare_bulk_interface(result, save_path='bulk_interface_comparison.png')
    >>>
    >>> # Gas distribution analysis
    >>> analysis = calculate_gas_distribution_analysis(result)
    >>> fig = plot_gas_distribution_pie_simple(result, save_path='gas_pie.png')
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path

from .utils import (
    save_figure,
    create_figure_grid,
    get_color_palette,
    convert_time_units,
    convert_length_units,
    calculate_burnup,
    format_axis_scientific,
    set_axis_limits,
    add_subfigure_labels,
    validate_result_data,
    get_time_unit_label,
    get_length_unit_label,
    VARIABLE_LABELS,
    apply_publication_style
)


def compare_bulk_interface(result: Dict[str, np.ndarray],
                          params: Optional[Dict[str, Any]] = None,
                          variables: Optional[List[str]] = None,
                          time_unit: str = 'minutes',
                          length_unit: str = 'nm',
                          use_burnup: bool = False,
                          figsize: Tuple[float, float] = (14, 10),
                          save_path: Optional[str] = None,
                          style: str = 'default') -> plt.Figure:
    """
    Create comprehensive bulk vs interface comparison plots.

    This function creates a multi-panel figure comparing bulk and interface
    behavior for key variables including bubble radius, gas concentration,
    bubble concentration, and gas atoms per bubble.

    Args:
        result: Dictionary containing simulation results with keys:
                - 'time': Time array (seconds)
                - 'Rcb': Bulk bubble radius (m)
                - 'Rcf': Interface bubble radius (m)
                - 'Ccb': Bulk bubble concentration (cavities/m³)
                - 'Ccf': Interface bubble concentration (cavities/m³)
                - 'Cgb': Bulk gas concentration (atoms/m³)
                - 'Cgf': Interface gas concentration (atoms/m³)
                - 'Ncb': Gas atoms per bulk bubble
                - 'Ncf': Gas atoms per interface bubble
                - 'cvb': Bulk vacancy concentration
                - 'cvf': Interface vacancy concentration
                - 'cib': Bulk interstitial concentration
                - 'cif': Interface interstitial concentration
        params: Optional simulation parameters dictionary
        variables: List of variable pairs to compare. If None, uses default set.
                   Format: ['Rc', 'Cg', 'Cc', 'Nc', 'cv', 'ci'] where
                   'b' suffix means bulk, 'f' suffix means interface
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        length_unit: Unit for length axis ('m', 'mm', 'um', 'nm')
        use_burnup: Use burnup (%FIMA) instead of time for x-axis
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing from result

    Examples:
        >>> fig = compare_bulk_interface(result, save_path='comparison.png')
        >>> fig = compare_bulk_interface(
        ...     result, params, time_unit='hours',
        ...     use_burnup=True, save_path='burnup_comparison.pdf'
        ... )

    Notes:
        This function provides a quick way to visualize the differences
        between bulk and interface behavior in the gas swelling model.
        Uses blue color for bulk and orange for interface by default.
    """
    # Validate required keys
    required_keys = ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf', 'Cgb', 'Cgf',
                    'Ncb', 'Ncf', 'cvb', 'cvf', 'cib', 'cif']
    validate_result_data(result, required_keys)

    # Apply style
    apply_publication_style(style)

    # Set default variables if not specified
    if variables is None:
        variables = ['Rc', 'Cg', 'Cc', 'Nc', 'cv', 'ci']

    # Get time data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        time_data = calculate_burnup(time_seconds, fission_rate)
        time_label = VARIABLE_LABELS['burnup']
    else:
        time_data = convert_time_units(time_seconds, time_unit)
        time_label = get_time_unit_label(time_unit)

    # Get length conversion
    length_scale = 1e9 if length_unit == 'nm' else 1e6 if length_unit == 'um' else 1

    # Get colors
    colors = get_color_palette('bulk_interface')

    # Create figure with subplots
    n_vars = len(variables)
    n_cols = 2
    n_rows = (n_vars + 1) // 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1 or n_cols == 1:
        axes = axes.reshape(n_rows, n_cols)

    # Flatten axes for easy iteration
    axes_flat = axes.flatten()

    # Plot each variable pair
    for idx, var in enumerate(variables):
        ax = axes_flat[idx]
        bulk_key = var + 'b'
        interface_key = var + 'f'

        if bulk_key in result and interface_key in result:
            # Convert length units if needed
            if var in ['Rc']:
                bulk_data = result[bulk_key] * length_scale
                interface_data = result[interface_key] * length_scale
                ylabel = f'{VARIABLE_LABELS.get(bulk_key, bulk_key)} ({length_unit})'
            else:
                bulk_data = result[bulk_key]
                interface_data = result[interface_key]
                ylabel = VARIABLE_LABELS.get(bulk_key, bulk_key)

            # Use log scale for certain variables
            use_log = var in ['Nc', 'cv', 'ci', 'Cc', 'Cg']

            if use_log:
                ax.semilogy(time_data, bulk_data, label='Bulk',
                           color=colors[0], linewidth=2)
                ax.semilogy(time_data, interface_data, label='Interface',
                           color=colors[1], linewidth=2)
            else:
                ax.plot(time_data, bulk_data, label='Bulk',
                       color=colors[0], linewidth=2)
                ax.plot(time_data, interface_data, label='Interface',
                       color=colors[1], linewidth=2)

            ax.set_xlabel(time_label)
            ax.set_ylabel(ylabel)
            ax.set_title(f'{VARIABLE_LABELS.get(bulk_key, bulk_key)}: Bulk vs Interface')
            ax.legend()
            ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for idx in range(n_vars, len(axes_flat)):
        axes_flat[idx].set_visible(False)

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def plot_bulk_interface_ratio(result: Dict[str, np.ndarray],
                             ratios: Optional[List[str]] = None,
                             time_unit: str = 'minutes',
                             use_burnup: bool = False,
                             figsize: Tuple[float, float] = (12, 8),
                             save_path: Optional[str] = None,
                             style: str = 'default') -> plt.Figure:
    """
    Plot ratios of interface to bulk variables.

    This function creates plots showing the ratio of interface to bulk
    quantities, useful for understanding where interface effects dominate.

    Args:
        result: Dictionary containing simulation results
        ratios: List of variable base names to plot ratios for.
                Format: ['Rc', 'Cc', 'Nc'] will plot Rcf/Rcb, Ccf/Ccb, Ncf/Ncb
                If None, uses default set ['Rc', 'Cc', 'Nc', 'Cg']
        time_unit: Unit for time axis
        use_burnup: Use burnup instead of time for x-axis
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_bulk_interface_ratio(result, save_path='ratios.png')
        >>> fig = plot_bulk_interface_ratio(
        ...     result, ratios=['Rc', 'Cc'], time_unit='hours'
        ... )

    Notes:
        Ratio > 1 indicates interface values are larger than bulk
        Ratio < 1 indicates bulk values are larger than interface
        Ratio = 1 indicates bulk and interface are equal
    """
    # Validate required keys
    validate_result_data(result, ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf'])

    apply_publication_style(style)

    if ratios is None:
        ratios = ['Rc', 'Cc', 'Nc', 'Cg']

    # Get time data
    time_seconds = result['time']
    if use_burnup:
        time_data = calculate_burnup(time_seconds, 5e19)
        time_label = VARIABLE_LABELS['burnup']
    else:
        time_data = convert_time_units(time_seconds, time_unit)
        time_label = get_time_unit_label(time_unit)

    # Create figure
    n_ratios = len(ratios)
    n_cols = 2
    n_rows = (n_ratios + 1) // 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1 or n_cols == 1:
        axes = axes.reshape(n_rows, n_cols)

    axes_flat = axes.flatten()

    # Plot each ratio
    for idx, var in enumerate(ratios):
        ax = axes_flat[idx]
        bulk_key = var + 'b'
        interface_key = var + 'f'

        if bulk_key in result and interface_key in result:
            # Calculate ratio (interface/bulk)
            bulk_data = result[bulk_key]
            interface_data = result[interface_key]

            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = np.where(bulk_data > 0, interface_data / bulk_data, np.nan)

            ax.plot(time_data, ratio, color='purple', linewidth=2)
            ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Equal')

            ax.set_xlabel(time_label)
            ax.set_ylabel(f'Interface / Bulk Ratio')
            ax.set_title(f'{VARIABLE_LABELS.get(interface_key, interface_key)} Ratio')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Set y-axis to log scale if ratios vary widely
            if np.nanmax(ratio) / np.nanmin(ratio) > 10:
                ax.set_yscale('log')

    # Hide unused subplots
    for idx in range(n_ratios, len(axes_flat)):
        axes_flat[idx].set_visible(False)

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def plot_gas_distribution_pie(result: Dict[str, np.ndarray],
                              time_index: int = -1,
                              figsize: Tuple[float, float] = (10, 8),
                              save_path: Optional[str] = None,
                              style: str = 'default') -> plt.Figure:
    """
    Create pie charts showing gas distribution at specific time points.

    This function creates pie charts showing how gas is distributed among
    different reservoirs (bulk solution, bulk bubbles, interface solution,
    interface bubbles, released gas) at a specific time point.

    Args:
        result: Dictionary containing simulation results with keys:
                - 'Cgb': Bulk gas concentration (atoms/m³)
                - 'Cgf': Interface gas concentration (atoms/m³)
                - 'Ccb': Bulk bubble concentration (cavities/m³)
                - 'Ccf': Interface bubble concentration (cavities/m³)
                - 'Ncb': Gas atoms per bulk bubble
                - 'Ncf': Gas atoms per interface bubble
                - 'released_gas': Released gas (atoms/m³)
        time_index: Index in time array to plot (default: -1 for final time)
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing from result

    Examples:
        >>> fig = plot_gas_distribution_pie(result, save_path='gas_pie.png')
        >>> fig = plot_gas_distribution_pie(result, time_index=50)

    Notes:
        The pie chart shows the fraction of total gas in each reservoir:
        - Bulk solution: Gas atoms dissolved in bulk matrix
        - Bulk bubbles: Gas atoms in bulk cavities
        - Interface solution: Gas atoms at phase boundaries
        - Interface bubbles: Gas atoms in interface cavities
        - Released: Gas released from the fuel
    """
    # Validate required keys
    required_keys = ['Cgb', 'Cgf', 'Ccb', 'Ccf', 'Ncb', 'Ncf', 'released_gas']
    validate_result_data(result, required_keys)

    apply_publication_style(style)

    # Get data at specified time index
    Cgb = result['Cgb'][time_index]
    Cgf = result['Cgf'][time_index]
    Ccb = result['Ccb'][time_index]
    Ccf = result['Ccf'][time_index]
    Ncb = result['Ncb'][time_index]
    Ncf = result['Ncf'][time_index]
    released_gas = result['released_gas'][time_index]

    # Calculate gas in each reservoir
    gas_in_bulk_solution = Cgb
    gas_in_bulk_bubbles = Ccb * Ncb
    gas_in_interface_solution = Cgf
    gas_in_interface_bubbles = Ccf * Ncf
    gas_released = released_gas

    total_gas = (gas_in_bulk_solution + gas_in_bulk_bubbles +
                gas_in_interface_solution + gas_in_interface_bubbles +
                gas_released)

    # Prepare pie chart data
    labels = [
        'Bulk Solution',
        'Bulk Bubbles',
        'Interface Solution',
        'Interface Bubbles',
        'Released Gas'
    ]

    sizes = [
        gas_in_bulk_solution / total_gas * 100 if total_gas > 0 else 0,
        gas_in_bulk_bubbles / total_gas * 100 if total_gas > 0 else 0,
        gas_in_interface_solution / total_gas * 100 if total_gas > 0 else 0,
        gas_in_interface_bubbles / total_gas * 100 if total_gas > 0 else 0,
        gas_released / total_gas * 100 if total_gas > 0 else 0
    ]

    colors = get_color_palette('default')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors[:len(labels)],
        autopct='%1.1f%%',
        startangle=90,
        explode=[0.02] * len(labels)  # Slight separation
    )

    # Enhance text appearance
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    for text in texts:
        text.set_fontsize(12)

    ax.set_title('Gas Distribution at Final Time', fontsize=14, fontweight='bold')

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def plot_gas_distribution_evolution(result: Dict[str, np.ndarray],
                                   time_unit: str = 'minutes',
                                   use_burnup: bool = False,
                                   figsize: Tuple[float, float] = (12, 6),
                                   save_path: Optional[str] = None,
                                   style: str = 'default') -> plt.Figure:
    """
    Plot evolution of gas distribution over time.

    This function creates a stacked area plot showing how the distribution
    of gas among different reservoirs evolves over time.

    Args:
        result: Dictionary containing simulation results
        time_unit: Unit for time axis
        use_burnup: Use burnup instead of time for x-axis
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_gas_distribution_evolution(result, save_path='gas_evo.png')

    Notes:
        This plot helps visualize gas redistribution during irradiation
        and shows which reservoirs dominate at different times.
    """
    # Validate required keys
    required_keys = ['time', 'Cgb', 'Cgf', 'Ccb', 'Ccf', 'Ncb', 'Ncf', 'released_gas']
    validate_result_data(result, required_keys)

    apply_publication_style(style)

    # Get time data
    time_seconds = result['time']
    if use_burnup:
        time_data = calculate_burnup(time_seconds, 5e19)
        time_label = VARIABLE_LABELS['burnup']
    else:
        time_data = convert_time_units(time_seconds, time_unit)
        time_label = get_time_unit_label(time_unit)

    # Calculate gas in each reservoir over time
    gas_in_bulk_solution = result['Cgb']
    gas_in_bulk_bubbles = result['Ccb'] * result['Ncb']
    gas_in_interface_solution = result['Cgf']
    gas_in_interface_bubbles = result['Ccf'] * result['Ncf']
    gas_released = result['released_gas']

    # Stack data for area plot
    gas_arrays = np.vstack([
        gas_in_bulk_solution,
        gas_in_bulk_bubbles,
        gas_in_interface_solution,
        gas_in_interface_bubbles,
        gas_released
    ])

    # Normalize to get fractions
    total_gas = np.sum(gas_arrays, axis=0)
    gas_fractions = np.divide(gas_arrays, total_gas, where=total_gas>0)

    labels = [
        'Bulk Solution',
        'Bulk Bubbles',
        'Interface Solution',
        'Interface Bubbles',
        'Released Gas'
    ]

    colors = get_color_palette('default')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Create stacked area plot
    ax.stackplot(time_data, gas_fractions * 100, labels=labels, colors=colors[:len(labels)], alpha=0.8)

    ax.set_xlabel(time_label)
    ax.set_ylabel('Gas Fraction (%)')
    ax.set_title('Gas Distribution Evolution')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def calculate_gas_distribution_analysis(result: Dict[str, np.ndarray],
                                       time_index: int = -1) -> Dict[str, float]:
    """
    Calculate gas distribution analysis fractions.

    This function computes the fraction of gas in different reservoirs
    (solution, bubbles, released) at a specific time point, following
    the analysis pattern from the simulation examples.

    Args:
        result: Dictionary containing simulation results with keys:
                - 'Cgb': Bulk gas concentration (atoms/m³)
                - 'Cgf': Interface gas concentration (atoms/m³)
                - 'Ccb': Bulk bubble concentration (cavities/m³)
                - 'Ccf': Interface bubble concentration (cavities/m³)
                - 'Ncb': Gas atoms per bulk bubble
                - 'Ncf': Gas atoms per interface bubble
                - 'released_gas': Released gas (atoms/m³)
        time_index: Index in time array to analyze (default: -1 for final time)

    Returns:
        Dictionary with gas distribution fractions:
        - 'gas_in_solution_fraction': Fraction of gas in solution (bulk + interface)
        - 'gas_in_bubbles_fraction': Fraction of gas in bubbles (bulk + interface)
        - 'gas_release_fraction': Fraction of gas released

    Examples:
        >>> analysis = calculate_gas_distribution_analysis(result)
        >>> print(f"Solution: {analysis['gas_in_solution_fraction']:.2%}")
        >>> print(f"Bubbles: {analysis['gas_in_bubbles_fraction']:.2%}")
        >>> print(f"Released: {analysis['gas_release_fraction']:.2%}")

    Notes:
        This matches the analysis pattern from examples/run_simulation.py
        where gas is categorized into three main reservoirs.
    """
    # Validate required keys
    required_keys = ['Cgb', 'Cgf', 'Ccb', 'Ccf', 'Ncb', 'Ncf', 'released_gas']
    validate_result_data(result, required_keys)

    # Get data at specified time index
    Cgb = result['Cgb'][time_index]
    Cgf = result['Cgf'][time_index]
    Ccb = result['Ccb'][time_index]
    Ccf = result['Ccf'][time_index]
    Ncb = result['Ncb'][time_index]
    Ncf = result['Ncf'][time_index]
    released_gas = result['released_gas'][time_index]

    # Calculate gas in each reservoir
    gas_in_solution = Cgb + Cgf
    gas_in_bubbles = Ccb * Ncb + Ccf * Ncf
    gas_released = released_gas

    # Calculate total gas
    total_gas = gas_in_solution + gas_in_bubbles + gas_released

    # Calculate fractions
    if total_gas > 0:
        analysis = {
            'gas_in_solution_fraction': gas_in_solution / total_gas,
            'gas_in_bubbles_fraction': gas_in_bubbles / total_gas,
            'gas_release_fraction': gas_released / total_gas
        }
    else:
        analysis = {
            'gas_in_solution_fraction': 0.0,
            'gas_in_bubbles_fraction': 0.0,
            'gas_release_fraction': 0.0
        }

    return analysis


def plot_correlation_matrix(result: Dict[str, np.ndarray],
                           variables: Optional[List[str]] = None,
                           time_index: int = -1,
                           figsize: Tuple[float, float] = (10, 8),
                           save_path: Optional[str] = None,
                           style: str = 'default') -> plt.Figure:
    """
    Plot correlation matrix between variables at a specific time point.

    This function creates a heatmap showing correlations between different
    variables, useful for understanding relationships and dependencies.

    Args:
        result: Dictionary containing simulation results
        variables: List of variable keys to include in correlation matrix.
                   If None, uses default set of key variables.
        time_index: Index in time array to analyze (default: -1 for final time)
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_correlation_matrix(result, save_path='correlation.png')
        >>> fig = plot_correlation_matrix(result, time_index=50)

    Notes:
        Correlation values range from -1 (perfect negative correlation)
        to +1 (perfect positive correlation). 0 indicates no correlation.
    """
    apply_publication_style(style)

    if variables is None:
        variables = ['Rcb', 'Rcf', 'Ccb', 'Ccf', 'Ncb', 'Ncf',
                    'Cgb', 'Cgf', 'cvb', 'cvf', 'swelling']

    # Validate that variables exist in result
    valid_vars = [v for v in variables if v in result]
    if len(valid_vars) < 2:
        raise ValueError("Need at least 2 valid variables for correlation matrix")

    # Extract data at specified time index
    # Use full time series for better correlation estimation
    data_matrix = np.vstack([result[var] for var in valid_vars])

    # Calculate correlation matrix
    corr_matrix = np.corrcoef(data_matrix)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Create heatmap
    im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Correlation Coefficient', rotation=270, labelpad=20)

    # Set ticks and labels
    ax.set_xticks(np.arange(len(valid_vars)))
    ax.set_yticks(np.arange(len(valid_vars)))
    ax.set_xticklabels([VARIABLE_LABELS.get(v, v) for v in valid_vars], rotation=45, ha='right')
    ax.set_yticklabels([VARIABLE_LABELS.get(v, v) for v in valid_vars])

    # Add correlation values as text
    for i in range(len(valid_vars)):
        for j in range(len(valid_vars)):
            text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)

    ax.set_title('Variable Correlation Matrix', fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def plot_phase_comparison(result: Dict[str, np.ndarray],
                         variable: str,
                         time_unit: str = 'minutes',
                         length_unit: str = 'nm',
                         use_burnup: bool = False,
                         figsize: Tuple[float, float] = (12, 5),
                         save_path: Optional[str] = None,
                         style: str = 'default') -> plt.Figure:
    """
    Create detailed side-by-side comparison of bulk and interface for a single variable.

    This function creates two subplots showing bulk and interface behavior
    side-by-side for detailed comparison.

    Args:
        result: Dictionary containing simulation results
        variable: Variable base name (e.g., 'Rc', 'Cc', 'Nc', 'Cg', 'cv', 'ci')
        time_unit: Unit for time axis
        length_unit: Unit for length axis
        use_burnup: Use burnup instead of time for x-axis
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If variable keys are not found in result

    Examples:
        >>> fig = plot_phase_comparison(result, 'Rc', save_path='rc_comparison.png')
        >>> fig = plot_phase_comparison(result, 'Nc', time_unit='hours')

    Notes:
        This is useful for detailed examination of differences between
        bulk and interface behavior for a specific variable.
    """
    bulk_key = variable + 'b'
    interface_key = variable + 'f'

    if bulk_key not in result or interface_key not in result:
        raise ValueError(f"Variables '{bulk_key}' and/or '{interface_key}' not found in result")

    apply_publication_style(style)

    # Get time data
    time_seconds = result['time']
    if use_burnup:
        time_data = calculate_burnup(time_seconds, 5e19)
        time_label = VARIABLE_LABELS['burnup']
    else:
        time_data = convert_time_units(time_seconds, time_unit)
        time_label = get_time_unit_label(time_unit)

    colors = get_color_palette('bulk_interface')

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Get length conversion if needed
    if variable in ['Rc']:
        scale = 1e9 if length_unit == 'nm' else 1e6 if length_unit == 'um' else 1
        bulk_data = result[bulk_key] * scale
        interface_data = result[interface_key] * scale
        ylabel = f'{VARIABLE_LABELS.get(bulk_key, bulk_key)} ({length_unit})'
    else:
        bulk_data = result[bulk_key]
        interface_data = result[interface_key]
        ylabel = VARIABLE_LABELS.get(bulk_key, bulk_key)

    # Determine if log scale is appropriate
    use_log = variable in ['Nc', 'cv', 'ci', 'Cc', 'Cg']

    # Plot bulk
    if use_log:
        axes[0].semilogy(time_data, bulk_data, color=colors[0], linewidth=2, label='Bulk')
    else:
        axes[0].plot(time_data, bulk_data, color=colors[0], linewidth=2, label='Bulk')

    axes[0].set_xlabel(time_label)
    axes[0].set_ylabel(ylabel)
    axes[0].set_title(f'Bulk: {VARIABLE_LABELS.get(bulk_key, bulk_key)}')
    axes[0].grid(True, alpha=0.3)

    # Plot interface
    if use_log:
        axes[1].semilogy(time_data, interface_data, color=colors[1], linewidth=2, label='Interface')
    else:
        axes[1].plot(time_data, interface_data, color=colors[1], linewidth=2, label='Interface')

    axes[1].set_xlabel(time_label)
    axes[1].set_ylabel(ylabel)
    axes[1].set_title(f'Interface: {VARIABLE_LABELS.get(interface_key, interface_key)}')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def plot_gas_distribution_pie_simple(result: Dict[str, np.ndarray],
                                     time_index: int = -1,
                                     labels: Optional[List[str]] = None,
                                     figsize: Tuple[float, float] = (8, 8),
                                     save_path: Optional[str] = None,
                                     style: str = 'default') -> plt.Figure:
    """
    Create simplified pie chart showing gas distribution (3 categories).

    This function creates a pie chart showing how gas is distributed among
    three main reservoirs: solution, bubbles, and released gas. This matches
    the pattern from examples/run_simulation.py.

    Args:
        result: Dictionary containing simulation results with keys:
                - 'Cgb': Bulk gas concentration (atoms/m³)
                - 'Cgf': Interface gas concentration (atoms/m³)
                - 'Ccb': Bulk bubble concentration (cavities/m³)
                - 'Ccf': Interface bubble concentration (cavities/m³)
                - 'Ncb': Gas atoms per bulk bubble
                - 'Ncf': Gas atoms per interface bubble
                - 'released_gas': Released gas (atoms/m³)
        time_index: Index in time array to plot (default: -1 for final time)
        labels: Custom labels for the three categories.
                If None, uses ['Solution', 'In Bubbles', 'Released']
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing from result

    Examples:
        >>> fig = plot_gas_distribution_pie_simple(result, save_path='gas_pie_simple.png')
        >>> fig = plot_gas_distribution_pie_simple(
        ...     result, time_index=50,
        ...     labels=['溶解态', '气泡内', '已释放']
        ... )

    Notes:
        This follows the pattern from examples/run_simulation.py lines 1386-1392
        with three categories:
        - Solution: Gas atoms dissolved in bulk + interface matrix
        - In Bubbles: Gas atoms in bulk + interface cavities
        - Released: Gas released from the fuel
    """
    # Validate required keys
    required_keys = ['Cgb', 'Cgf', 'Ccb', 'Ccf', 'Ncb', 'Ncf', 'released_gas']
    validate_result_data(result, required_keys)

    apply_publication_style(style)

    # Calculate gas distribution analysis
    analysis = calculate_gas_distribution_analysis(result, time_index)

    # Set default labels if not provided
    if labels is None:
        labels = ['Solution', 'In Bubbles', 'Released']

    # Prepare pie chart data
    sizes = [
        analysis['gas_in_solution_fraction'] * 100,
        analysis['gas_in_bubbles_fraction'] * 100,
        analysis['gas_release_fraction'] * 100
    ]

    colors = get_color_palette('default')[:3]

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )

    # Enhance text appearance
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)

    for text in texts:
        text.set_fontsize(13)

    ax.set_title('Gas Distribution', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


def plot_gas_release_fraction(results: Dict[str, Any],
                              figsize: Tuple[float, float] = (10, 6),
                              save_path: Optional[str] = None,
                              style: str = 'default') -> plt.Figure:
    """
    Plot gas release fraction vs temperature from temperature sweep results.

    This function creates a line plot showing how gas release fraction varies
    with temperature, following the pattern from examples/run_simulation.py.

    Args:
        results: Dictionary containing temperature sweep results with keys:
                - 'temperatures': List/array of temperature values (K)
                - 'gas_release_fractions': List/array of gas release fractions
                OR
                - 'detailed_results': Dict with temperature as keys, containing
                  'analysis' sub-dict with 'gas_release_fraction'
        figsize: Figure size (width, height) in inches
        save_path: Optional path to save the figure
        style: Matplotlib style preset name

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required data is not found in results

    Examples:
        >>> fig = plot_gas_release_fraction(temperature_results, save_path='gas_release.png')
        >>> fig = plot_gas_release_fraction(
        ...     high_burnup_results,
        ...     save_path='gas_release_hb.pdf'
        ... )

    Notes:
        This follows the pattern from examples/run_simulation.py lines 1394-1400
        showing gas release fraction as a function of temperature.
        Gas release fraction typically increases with temperature.
    """
    apply_publication_style(style)

    # Extract temperature and gas release data
    if 'temperatures' in results and 'gas_release_fractions' in results:
        temperatures = results['temperatures']
        gas_release_fractions = results['gas_release_fractions']
    elif 'detailed_results' in results:
        temperatures = []
        gas_release_fractions = []
        for temp, data in results['detailed_results'].items():
            if data is not None and 'analysis' in data:
                temperatures.append(temp)
                gas_release_fractions.append(data['analysis']['gas_release_fraction'])
        temperatures = np.array(temperatures)
        gas_release_fractions = np.array(gas_release_fractions)
    else:
        raise ValueError("Results must contain either 'temperatures' + 'gas_release_fractions' "
                        "or 'detailed_results' with temperature keys")

    # Sort by temperature
    sort_idx = np.argsort(temperatures)
    temperatures = np.array(temperatures)[sort_idx]
    gas_release_fractions = np.array(gas_release_fractions)[sort_idx]

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot gas release fraction vs temperature
    ax.plot(temperatures, gas_release_fractions, 'ro-',
           linewidth=2, markersize=8, label='Gas Release Fraction')

    ax.set_xlabel('Temperature (K)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Gas Release Fraction', fontsize=12, fontweight='bold')
    ax.set_title('Gas Release Fraction vs Temperature', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)

    # Set reasonable limits
    ax.set_ylim(0, max(1.0, np.max(gas_release_fractions) * 1.1))

    plt.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig
