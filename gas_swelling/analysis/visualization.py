"""
Visualization module for gas swelling model sensitivity analysis.

This module provides plotting functions for visualizing sensitivity analysis results,
including tornado plots for One-at-a-Time (OAT) analysis, Morris plots, and Sobol charts.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional, Union
from .sensitivity import OATResult, MorrisResult, SobolResult


def plot_tornado(
    oat_results: List[OATResult],
    output_name: str = 'swelling',
    metric: str = 'elasticity',
    top_n: Optional[int] = None,
    figsize: tuple = (10, 6),
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    color_positive: str = '#d62728',
    color_negative: str = '#1f77b4',
    alpha: float = 0.8,
    grid: bool = True,
    save_path: Optional[str] = None,
    show: bool = True,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """Create a tornado plot for One-at-a-Time sensitivity analysis results.

    A tornado plot displays the sensitivity of model outputs to parameter variations,
    with horizontal bars showing the magnitude and direction of each parameter's effect.
    Parameters are sorted by the absolute value of their sensitivity.

    Args:
        oat_results: List of OATResult objects from sensitivity analysis
        output_name: Name of the model output to visualize (default: 'swelling')
        metric: Sensitivity metric to plot - 'elasticity', 'normalized', or 'std' (default: 'elasticity')
        top_n: Only show the top N most sensitive parameters (None = show all)
        figsize: Figure size as (width, height) in inches
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label (auto-generated if None)
        color_positive: Color for positive sensitivities
        color_negative: Color for negative sensitivities
        alpha: Bar transparency (0 = transparent, 1 = opaque)
        grid: Whether to show grid lines
        save_path: Path to save the figure (None = don't save)
        show: Whether to display the plot
        ax: Matplotlib Axes object (creates new figure if None)

    Returns:
        Matplotlib Axes object with the tornado plot

    Raises:
        ValueError: If oat_results is empty or output_name/metric not found
        TypeError: If oat_results is not a list of OATResult objects

    Example:
        >>> from gas_swelling.analysis.sensitivity import OATAnalyzer, create_default_parameter_ranges
        >>> from gas_swelling.analysis.visualization import plot_tornado
        >>> analyzer = OATAnalyzer(parameter_ranges=create_default_parameter_ranges())
        >>> results = analyzer.run_oat_analysis(percent_variations=[-10, 10], verbose=False)
        >>> plot_tornado(results, output_name='swelling', save_path='tornado.png')
    """
    # Validate inputs
    if not isinstance(oat_results, list) or len(oat_results) == 0:
        raise ValueError("oat_results must be a non-empty list of OATResult objects")

    if not all(isinstance(r, OATResult) for r in oat_results):
        raise TypeError("All items in oat_results must be OATResult objects")

    # Extract sensitivity data
    param_names = []
    sensitivities = []

    for result in oat_results:
        param_names.append(result.parameter_name)

        # Check if output_name exists in sensitivities
        if output_name not in result.sensitivities:
            available = list(result.sensitivities.keys())
            raise ValueError(
                f"Output '{output_name}' not found in results. "
                f"Available outputs: {available}"
            )

        # Check if metric exists
        if metric not in result.sensitivities[output_name]:
            available = list(result.sensitivities[output_name].keys())
            raise ValueError(
                f"Metric '{metric}' not found for output '{output_name}'. "
                f"Available metrics: {available}"
            )

        sensitivities.append(result.sensitivities[output_name][metric])

    # Convert to numpy arrays
    param_names = np.array(param_names)
    sensitivities = np.array(sensitivities)

    # Sort by absolute sensitivity (descending)
    sort_idx = np.argsort(np.abs(sensitivities))[::-1]
    param_names = param_names[sort_idx]
    sensitivities = sensitivities[sort_idx]

    # Limit to top_n if specified
    if top_n is not None and top_n < len(param_names):
        param_names = param_names[:top_n]
        sensitivities = sensitivities[:top_n]

    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Create y-axis positions
    y_pos = np.arange(len(param_names))

    # Create color array based on sign of sensitivity
    colors = [color_positive if s > 0 else color_negative for s in sensitivities]

    # Create horizontal bars
    bars = ax.barh(
        y_pos,
        sensitivities,
        align='center',
        color=colors,
        alpha=alpha,
        edgecolor='black',
        linewidth=0.5
    )

    # Add value labels on bars
    for i, (bar, sens) in enumerate(zip(bars, sensitivities)):
        # Position label based on sign
        if sens > 0:
            x_pos = sens + 0.01 * np.max(np.abs(sensitivities))
            ha = 'left'
        else:
            x_pos = sens - 0.01 * np.max(np.abs(sensitivities))
            ha = 'right'

        ax.text(
            x_pos,
            bar.get_y() + bar.get_height() / 2,
            f'{sens:.3f}',
            va='center',
            ha=ha,
            fontsize=9,
            fontweight='bold'
        )

    # Set axis labels
    if title is None:
        title = f'Tornado Plot - {output_name.replace("_", " ").title()} Sensitivity'
    if xlabel is None:
        xlabel = f'{metric.replace("_", " ").title()}'
    if ylabel is None:
        ylabel = 'Parameters'

    ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)

    # Set y-tick labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(param_names, fontsize=10)

    # Add vertical line at x=0
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # Invert y-axis to show highest sensitivity at top
    ax.invert_yaxis()

    # Add grid if requested
    if grid:
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.grid(axis='y', alpha=0.0)  # No horizontal grid lines

    # Adjust layout
    plt.tight_layout()

    # Save figure if path provided
    if save_path is not None:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    # Show plot if requested
    if show:
        plt.show()

    return ax


def plot_tornado_multi_output(
    oat_results: List[OATResult],
    output_names: List[str],
    metric: str = 'elasticity',
    top_n: Optional[int] = None,
    figsize: tuple = (14, 8),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    show: bool = True
) -> plt.Figure:
    """Create a multi-panel tornado plot comparing multiple model outputs.

    This function creates a figure with multiple tornado plots, one for each
    specified output, allowing easy comparison of parameter sensitivities
    across different model outputs.

    Args:
        oat_results: List of OATResult objects from sensitivity analysis
        output_names: List of output names to visualize
        metric: Sensitivity metric to plot (default: 'elasticity')
        top_n: Only show the top N most sensitive parameters (None = show all)
        figsize: Figure size as (width, height) in inches
        title: Overall figure title (auto-generated if None)
        save_path: Path to save the figure (None = don't save)
        show: Whether to display the plot

    Returns:
        Matplotlib Figure object with multiple tornado plots

    Raises:
        ValueError: If oat_results is empty or output_names not found

    Example:
        >>> from gas_swelling.analysis.sensitivity import OATAnalyzer
        >>> from gas_swelling.analysis.visualization import plot_tornado_multi_output
        >>> analyzer = OATAnalyzer()
        >>> results = analyzer.run_oat_analysis(percent_variations=[-10, 10], verbose=False)
        >>> plot_tornado_multi_output(
        ...     results,
        ...     output_names=['swelling', 'final_bubble_radius_bulk'],
        ...     save_path='tornado_multi.png'
        ... )
    """
    # Validate inputs
    if not output_names:
        raise ValueError("output_names must be a non-empty list")

    n_outputs = len(output_names)

    # Calculate subplot layout
    n_cols = min(2, n_outputs)
    n_rows = (n_outputs + n_cols - 1) // n_cols

    # Create figure and subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)

    # Handle single row/column cases
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    elif n_rows == 1 or n_cols == 1:
        axes = axes.flatten()

    # Create tornado plot for each output
    for i, output_name in enumerate(output_names):
        ax = axes[i] if n_outputs > 1 else axes

        try:
            plot_tornado(
                oat_results=oat_results,
                output_name=output_name,
                metric=metric,
                top_n=top_n,
                ax=ax,
                show=False,
                grid=True
            )

            # Adjust title to be shorter for subplots
            ax.set_title(
                output_name.replace('_', ' ').title(),
                fontsize=11,
                fontweight='bold'
            )

        except ValueError as e:
            # Hide subplot if output not found
            ax.text(
                0.5, 0.5,
                f'Error: {str(e)}',
                ha='center',
                va='center',
                transform=ax.transAxes,
                color='red'
            )
            ax.set_xticks([])
            ax.set_yticks([])

    # Hide unused subplots
    for i in range(n_outputs, len(axes)):
        axes[i].set_visible(False)

    # Set overall title
    if title is None:
        title = f'Tornado Plot - Parameter Sensitivities ({metric.replace("_", " ").title()})'
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)

    # Adjust layout
    plt.tight_layout()

    # Save figure if path provided
    if save_path is not None:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    # Show plot if requested
    if show:
        plt.show()

    return fig


def plot_oat_variation(
    oat_result: OATResult,
    output_name: str = 'swelling',
    figsize: tuple = (10, 6),
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    marker: str = 'o',
    linewidth: int = 2,
    markersize: int = 8,
    color: str = '#1f77b4',
    grid: bool = True,
    save_path: Optional[str] = None,
    show: bool = True
) -> plt.Axes:
    """Plot the variation of a single parameter's effect on model output.

    This function creates a line plot showing how the model output changes
    as a single parameter is varied from its minimum to maximum value.

    Args:
        oat_result: OATResult object for a single parameter
        output_name: Name of the model output to visualize (default: 'swelling')
        figsize: Figure size as (width, height) in inches
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label (auto-generated if None)
        marker: Marker style for data points
        linewidth: Width of the line connecting points
        markersize: Size of the markers
        color: Color of the line and markers
        grid: Whether to show grid lines
        save_path: Path to save the figure (None = don't save)
        show: Whether to display the plot

    Returns:
        Matplotlib Axes object with the variation plot

    Raises:
        ValueError: If output_name not found in oat_result

    Example:
        >>> from gas_swelling.analysis.sensitivity import OATAnalyzer
        >>> from gas_swelling.analysis.visualization import plot_oat_variation
        >>> analyzer = OATAnalyzer()
        >>> results = analyzer.run_oat_analysis(percent_variations=[-20, -10, 10, 20], verbose=False)
        >>> plot_oat_variation(results[0], output_name='swelling', save_path='variation.png')
    """
    # Check if output_name exists
    if output_name not in oat_result.outputs:
        available = list(oat_result.outputs.keys())
        raise ValueError(
            f"Output '{output_name}' not found in OATResult. "
            f"Available: {available}"
        )

    # Create figure and axes
    fig, ax = plt.subplots(figsize=figsize)

    # Extract data
    param_values = np.array(oat_result.variations)
    output_values = oat_result.outputs[output_name]

    # Plot variation
    ax.plot(
        param_values,
        output_values,
        marker=marker,
        linewidth=linewidth,
        markersize=markersize,
        color=color,
        label='Model output'
    )

    # Mark nominal value
    nominal_output = oat_result.baseline_outputs.get(output_name, output_values[len(output_values) // 2])
    ax.axhline(
        y=nominal_output,
        color='red',
        linestyle='--',
        linewidth=1.5,
        alpha=0.7,
        label=f'Nominal ({nominal_output:.4g})'
    )

    # Mark nominal parameter value
    ax.axvline(
        x=oat_result.nominal_value,
        color='green',
        linestyle='--',
        linewidth=1.5,
        alpha=0.7,
        label=f'Nominal param ({oat_result.nominal_value:.4g})'
    )

    # Set axis labels
    if title is None:
        param_label = oat_result.parameter_name.replace('_', ' ').title()
        output_label = output_name.replace('_', ' ').title()
        title = f'Effect of {param_label} on {output_label}'
    if xlabel is None:
        xlabel = oat_result.parameter_name.replace('_', ' ').title()
    if ylabel is None:
        ylabel = output_name.replace('_', ' ').title()

    ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)

    # Add legend
    ax.legend(loc='best', fontsize=10)

    # Add grid if requested
    if grid:
        ax.grid(True, alpha=0.3, linestyle='--')

    # Adjust layout
    plt.tight_layout()

    # Save figure if path provided
    if save_path is not None:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    # Show plot if requested
    if show:
        plt.show()

    return ax


def plot_sensitivity_heatmap(
    results: Union[List[OATResult], MorrisResult, SobolResult],
    metric: str = 'elasticity',
    index_type: str = 'S1',
    output_names: Optional[List[str]] = None,
    parameter_names: Optional[List[str]] = None,
    top_n_params: Optional[int] = None,
    figsize: tuple = (10, 8),
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    cmap: str = 'RdYlBu_r',
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    annot: bool = True,
    fmt: str = '.3f',
    linewidths: float = 0.5,
    linecolor: str = 'white',
    cbar_kws: Optional[Dict[str, Any]] = None,
    square: bool = True,
    save_path: Optional[str] = None,
    show: bool = True,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """Create a sensitivity heatmap showing parameter-output interactions.

    This function creates a heatmap visualization where rows represent parameters,
    columns represent model outputs, and cell colors represent the magnitude of
    sensitivity. Supports OAT, Morris, and Sobol analysis results.

    Args:
        results: Sensitivity analysis results:
            - List[OATResult]: OAT analysis results
            - MorrisResult: Morris screening results
            - SobolResult: Sobol variance-based results
        metric: Sensitivity metric for OAT results - 'elasticity', 'normalized', or 'std' (default: 'elasticity')
        index_type: Index type for Morris/Sobol results - 'mu_star' (Morris), 'S1' or 'ST' (Sobol) (default: 'S1')
        output_names: List of output names to display (None = show all)
        parameter_names: List of parameter names to display (None = show all)
        top_n_params: Only show top N most sensitive parameters (None = show all)
        figsize: Figure size as (width, height) in inches
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label (auto-generated if None)
        cmap: Colormap name (default: 'RdYlBu_r' - reversed red-yellow-blue)
        vmin: Minimum value for color scale (None = auto)
        vmax: Maximum value for color scale (None = auto)
        annot: Whether to annotate cells with values
        fmt: Format string for annotations (default: '.3f')
        linewidths: Width of grid lines between cells
        linecolor: Color of grid lines
        cbar_kws: Additional keyword arguments for colorbar
        square: Whether to make cells square
        save_path: Path to save the figure (None = don't save)
        show: Whether to display the plot
        ax: Matplotlib Axes object (creates new figure if None)

    Returns:
        Matplotlib Axes object with the heatmap

    Raises:
        ValueError: If results is empty or invalid type
        TypeError: If results is not a recognized type

    Example:
        >>> from gas_swelling.analysis.sensitivity import OATAnalyzer, create_default_parameter_ranges
        >>> from gas_swelling.analysis.visualization import plot_sensitivity_heatmap
        >>> analyzer = OATAnalyzer(parameter_ranges=create_default_parameter_ranges())
        >>> results = analyzer.run_oat_analysis(percent_variations=[-10, 10], verbose=False)
        >>> plot_sensitivity_heatmap(results, save_path='heatmap.png')
    """
    # Import seaborn for heatmap
    try:
        import seaborn as sns
    except ImportError:
        raise ImportError(
            "seaborn is required for plot_sensitivity_heatmap. "
            "Install it with: pip install seaborn"
        )

    # Determine result type and extract sensitivity matrix
    if isinstance(results, list) and len(results) > 0 and isinstance(results[0], OATResult):
        # OAT results
        oat_results = results

        # Get all output names if not specified
        if output_names is None:
            output_names = set()
            for result in oat_results:
                output_names.update(result.outputs.keys())
            output_names = sorted(list(output_names))

        # Get parameter names
        if parameter_names is None:
            parameter_names = [r.parameter_name for r in oat_results]

        # Build sensitivity matrix
        sens_matrix = np.zeros((len(parameter_names), len(output_names)))

        for i, result in enumerate(oat_results):
            param_name = result.parameter_name
            if param_name not in parameter_names:
                continue

            param_idx = parameter_names.index(param_name)

            for j, output_name in enumerate(output_names):
                if output_name in result.sensitivities and metric in result.sensitivities[output_name]:
                    sens_matrix[param_idx, j] = result.sensitivities[output_name][metric]

        result_type = 'OAT'

    elif isinstance(results, MorrisResult):
        # Morris results
        morris_result = results

        # Get output names if not specified
        if output_names is None:
            output_names = morris_result.output_names

        # Get parameter names if not specified
        if parameter_names is None:
            parameter_names = morris_result.parameter_names

        # Build sensitivity matrix from mu_star
        sens_matrix = np.zeros((len(parameter_names), len(output_names)))

        if index_type == 'mu_star':
            indices = morris_result.mu_star
        elif index_type == 'mu':
            indices = morris_result.mu
        elif index_type == 'sigma':
            indices = morris_result.sigma
        else:
            raise ValueError(
                f"Invalid index_type '{index_type}' for Morris results. "
                "Use 'mu_star', 'mu', or 'sigma'."
            )

        # Morris has same indices for all outputs (global screening)
        for i in range(len(parameter_names)):
            for j in range(len(output_names)):
                sens_matrix[i, j] = indices[i]

        result_type = 'Morris'

    elif isinstance(results, SobolResult):
        # Sobol results
        sobol_result = results

        # Get output names if not specified
        if output_names is None:
            output_names = sobol_result.output_names

        # Get parameter names if not specified
        if parameter_names is None:
            parameter_names = sobol_result.parameter_names

        # Build sensitivity matrix
        if index_type == 'S1':
            sens_matrix = sobol_result.S1.copy()
        elif index_type == 'ST':
            sens_matrix = sobol_result.ST.copy()
        else:
            raise ValueError(
                f"Invalid index_type '{index_type}' for Sobol results. "
                "Use 'S1' or 'ST'."
            )

        # Filter by parameter names and output names
        param_indices = [i for i, name in enumerate(sobol_result.parameter_names) if name in parameter_names]
        output_indices = [i for i, name in enumerate(sobol_result.output_names) if name in output_names]

        sens_matrix = sens_matrix[np.ix_(param_indices, output_indices)]

        # Update parameter/output names to match filtered order
        parameter_names = [sobol_result.parameter_names[i] for i in param_indices]
        output_names = [sobol_result.output_names[i] for i in output_indices]

        result_type = 'Sobol'

    else:
        raise TypeError(
            "results must be a List[OATResult], MorrisResult, or SobolResult. "
            f"Got: {type(results)}"
        )

    # Filter to top N parameters if specified
    if top_n_params is not None and top_n_params < len(parameter_names):
        # Calculate overall sensitivity for each parameter (e.g., max or mean across outputs)
        param_sensitivity = np.max(np.abs(sens_matrix), axis=1)
        top_indices = np.argsort(param_sensitivity)[-top_n_params:][::-1]

        parameter_names = [parameter_names[i] for i in top_indices]
        sens_matrix = sens_matrix[top_indices, :]

    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Set default colorbar kwargs
    if cbar_kws is None:
        cbar_kws = {'label': 'Sensitivity'}

    # Create heatmap
    sns.heatmap(
        sens_matrix,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        linewidths=linewidths,
        linecolor=linecolor,
        cbar_kws=cbar_kws,
        square=square,
        xticklabels=output_names,
        yticklabels=parameter_names,
        ax=ax
    )

    # Set axis labels
    if title is None:
        if result_type == 'OAT':
            title = f'Sensitivity Heatmap ({result_type} - {metric.replace("_", " ").title()})'
        elif result_type == 'Morris':
            title = f'Sensitivity Heatmap ({result_type} - {index_type.replace("_", " ").title()})'
        else:  # Sobol
            title = f'Sensitivity Heatmap ({result_type} - {index_type} Index)'

    if xlabel is None:
        xlabel = 'Model Outputs'
    if ylabel is None:
        ylabel = 'Parameters'

    ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)

    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

    # Adjust layout
    plt.tight_layout()

    # Save figure if path provided
    if save_path is not None:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    # Show plot if requested
    if show:
        plt.show()

    return ax


def plot_parameter_ranking(
    results: Union[List[OATResult], MorrisResult, SobolResult],
    output_name: str = 'swelling',
    metric: str = 'elasticity',
    index_type: str = 'ST',
    top_n: Optional[int] = None,
    figsize: tuple = (10, 6),
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    color: str = '#1f77b4',
    alpha: float = 0.8,
    edgecolor: str = 'black',
    linewidth: float = 0.5,
    grid: bool = True,
    show_values: bool = True,
    value_format: str = '.3f',
    horizontal: bool = True,
    save_path: Optional[str] = None,
    show: bool = True,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """Create a parameter ranking bar chart.

    This function creates a bar chart showing parameters ranked by their
    sensitivity indices. Parameters are sorted by the magnitude of their
    sensitivity, making it easy to identify the most influential parameters.

    Args:
        results: Sensitivity analysis results:
            - List[OATResult]: OAT analysis results
            - MorrisResult: Morris screening results
            - SobolResult: Sobol variance-based results
        output_name: Name of the model output to visualize (default: 'swelling')
        metric: Sensitivity metric for OAT results - 'elasticity', 'normalized', or 'std' (default: 'elasticity')
        index_type: Index type for Morris/Sobol results:
            - Morris: 'mu_star', 'mu', or 'sigma' (default: 'ST' for Sobol)
            - Sobol: 'S1' or 'ST' (default: 'ST')
        top_n: Only show the top N most sensitive parameters (None = show all)
        figsize: Figure size as (width, height) in inches
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label (auto-generated if None)
        color: Bar color
        alpha: Bar transparency (0 = transparent, 1 = opaque)
        edgecolor: Color of bar edges
        linewidth: Width of bar edges
        grid: Whether to show grid lines
        show_values: Whether to display values on bars
        value_format: Format string for values (default: '.3f')
        horizontal: Whether to create horizontal bars (True) or vertical bars (False)
        save_path: Path to save the figure (None = don't save)
        show: Whether to display the plot
        ax: Matplotlib Axes object (creates new figure if None)

    Returns:
        Matplotlib Axes object with the ranking plot

    Raises:
        ValueError: If results is empty or output_name/index_type not found
        TypeError: If results is not a recognized type

    Example:
        >>> from gas_swelling.analysis.sensitivity import SobolAnalyzer, create_default_parameter_ranges
        >>> from gas_swelling.analysis.visualization import plot_parameter_ranking
        >>> analyzer = SobolAnalyzer(parameter_ranges=create_default_parameter_ranges())
        >>> result = analyzer.run_sobol_analysis(n_samples=1000, verbose=False)
        >>> plot_parameter_ranking(result, output_name='swelling', save_path='ranking.png')
    """
    # Determine result type and extract sensitivity data
    if isinstance(results, list) and len(results) > 0 and isinstance(results[0], OATResult):
        # OAT results
        oat_results = results

        param_names = []
        sensitivities = []

        for result in oat_results:
            param_names.append(result.parameter_name)

            # Check if output_name exists
            if output_name not in result.sensitivities:
                available = list(result.sensitivities.keys())
                raise ValueError(
                    f"Output '{output_name}' not found in results. "
                    f"Available outputs: {available}"
                )

            # Check if metric exists
            if metric not in result.sensitivities[output_name]:
                available = list(result.sensitivities[output_name].keys())
                raise ValueError(
                    f"Metric '{metric}' not found for output '{output_name}'. "
                    f"Available metrics: {available}"
                )

            sensitivities.append(result.sensitivities[output_name][metric])

        param_names = np.array(param_names)
        sensitivities = np.array(sensitivities)
        result_type = 'OAT'

    elif isinstance(results, MorrisResult):
        # Morris results
        morris_result = results

        # Check if output_name exists
        if output_name not in morris_result.output_names:
            available = morris_result.output_names
            raise ValueError(
                f"Output '{output_name}' not found in Morris results. "
                f"Available: {available}"
            )

        param_names = np.array(morris_result.parameter_names)

        # Extract the requested index
        if index_type == 'mu_star':
            sensitivities = morris_result.mu_star
        elif index_type == 'mu':
            sensitivities = morris_result.mu
        elif index_type == 'sigma':
            sensitivities = morris_result.sigma
        else:
            raise ValueError(
                f"Invalid index_type '{index_type}' for Morris results. "
                "Use 'mu_star', 'mu', or 'sigma'."
            )

        # Morris indices are the same for all outputs (global screening)
        result_type = 'Morris'

    elif isinstance(results, SobolResult):
        # Sobol results
        sobol_result = results

        # Check if output_name exists
        if output_name not in sobol_result.output_names:
            available = sobol_result.output_names
            raise ValueError(
                f"Output '{output_name}' not found in Sobol results. "
                f"Available: {available}"
            )

        param_names = np.array(sobol_result.parameter_names)

        # Get output index
        output_idx = sobol_result.output_names.index(output_name)

        # Extract the requested index
        if index_type == 'S1':
            sensitivities = sobol_result.S1[:, output_idx]
        elif index_type == 'ST':
            sensitivities = sobol_result.ST[:, output_idx]
        else:
            raise ValueError(
                f"Invalid index_type '{index_type}' for Sobol results. "
                "Use 'S1' or 'ST'."
            )

        result_type = 'Sobol'

    else:
        raise TypeError(
            "results must be a List[OATResult], MorrisResult, or SobolResult. "
            f"Got: {type(results)}"
        )

    # Sort by sensitivity (descending)
    sort_idx = np.argsort(np.abs(sensitivities))[::-1]
    param_names = param_names[sort_idx]
    sensitivities = sensitivities[sort_idx]

    # Limit to top_n if specified
    if top_n is not None and top_n < len(param_names):
        param_names = param_names[:top_n]
        sensitivities = sensitivities[:top_n]

    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Create positions
    positions = np.arange(len(param_names))

    # Create bar chart
    if horizontal:
        bars = ax.barh(
            positions,
            sensitivities,
            align='center',
            color=color,
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth
        )

        # Add value labels if requested
        if show_values:
            for i, (bar, sens) in enumerate(zip(bars, sensitivities)):
                # Position label based on sign
                if sens >= 0:
                    x_pos = sens + 0.01 * np.max(np.abs(sensitivities))
                    ha = 'left'
                else:
                    x_pos = sens - 0.01 * np.max(np.abs(sensitivities))
                    ha = 'right'

                ax.text(
                    x_pos,
                    bar.get_y() + bar.get_height() / 2,
                    format(sens, value_format),
                    va='center',
                    ha=ha,
                    fontsize=9,
                    fontweight='bold'
                )

        # Set y-tick labels
        ax.set_yticks(positions)
        ax.set_yticklabels(param_names, fontsize=10)

        # Invert y-axis to show highest sensitivity at top
        ax.invert_yaxis()

        # Set axis labels
        if xlabel is None:
            if result_type == 'OAT':
                xlabel = f'{metric.replace("_", " ").title()}'
            elif result_type == 'Morris':
                xlabel = f'{index_type.replace("_", " ").title()}'
            else:  # Sobol
                xlabel = f'{index_type} Index'
        if ylabel is None:
            ylabel = 'Parameters'

        # Add vertical line at x=0
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        if grid:
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.grid(axis='y', alpha=0.0)

    else:  # Vertical bars
        bars = ax.bar(
            positions,
            sensitivities,
            align='center',
            color=color,
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth
        )

        # Add value labels if requested
        if show_values:
            for i, (bar, sens) in enumerate(zip(bars, sensitivities)):
                # Position label based on sign
                if sens >= 0:
                    y_pos = sens + 0.01 * np.max(np.abs(sensitivities))
                    va = 'bottom'
                else:
                    y_pos = sens - 0.01 * np.max(np.abs(sensitivities))
                    va = 'top'

                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    y_pos,
                    format(sens, value_format),
                    va=va,
                    ha='center',
                    fontsize=9,
                    fontweight='bold'
                )

        # Set x-tick labels
        ax.set_xticks(positions)
        ax.set_xticklabels(param_names, fontsize=10, rotation=45, ha='right')

        # Set axis labels
        if xlabel is None:
            xlabel = 'Parameters'
        if ylabel is None:
            if result_type == 'OAT':
                ylabel = f'{metric.replace("_", " ").title()}'
            elif result_type == 'Morris':
                ylabel = f'{index_type.replace("_", " ").title()}'
            else:  # Sobol
                ylabel = f'{index_type} Index'

        # Add horizontal line at y=0
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        if grid:
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.grid(axis='x', alpha=0.0)

    # Set title
    if title is None:
        output_label = output_name.replace('_', ' ').title()
        if result_type == 'OAT':
            title = f'Parameter Ranking - {output_label} ({result_type} - {metric.replace("_", " ").title()})'
        elif result_type == 'Morris':
            title = f'Parameter Ranking - {output_label} ({result_type} - {index_type.replace("_", " ").title()})'
        else:  # Sobol
            title = f'Parameter Ranking - {output_label} ({result_type} - {index_type} Index)'

    ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)

    # Adjust layout
    plt.tight_layout()

    # Save figure if path provided
    if save_path is not None:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    # Show plot if requested
    if show:
        plt.show()

    return ax


def plot_sobol_convergence(
    sobol_result: SobolResult,
    output_name: str = 'swelling',
    index_type: str = 'ST',
    parameter_names: Optional[List[str]] = None,
    top_n: Optional[int] = None,
    figsize: tuple = (12, 6),
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    colormap: str = 'tab10',
    linewidth: float = 2,
    markersize: int = 6,
    alpha: float = 0.7,
    grid: bool = True,
    legend: bool = True,
    legend_loc: str = 'best',
    confidence_interval: bool = False,
    save_path: Optional[str] = None,
    show: bool = True,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """Create a Sobol convergence plot showing how indices stabilize with sample size.

    This function creates a line plot showing the convergence of Sobol indices
    as the sample size increases. This is useful for determining whether the
    analysis has used sufficient samples for stable results.

    Args:
        sobol_result: SobolResult object with convergence data
        output_name: Name of the model output to visualize (default: 'swelling')
        index_type: Which Sobol index to plot - 'S1' or 'ST' (default: 'ST')
        parameter_names: List of parameter names to plot (None = plot all)
        top_n: Only plot the top N most sensitive parameters (None = plot all)
        figsize: Figure size as (width, height) in inches
        title: Plot title (auto-generated if None)
        xlabel: X-axis label (auto-generated if None)
        ylabel: Y-axis label (auto-generated if None)
        colormap: Colormap name for parameter lines
        linewidth: Width of lines
        markersize: Size of markers
        alpha: Line transparency (0 = transparent, 1 = opaque)
        grid: Whether to show grid lines
        legend: Whether to show legend
        legend_loc: Location of legend (default: 'best')
        confidence_interval: Whether to plot confidence intervals if available
        save_path: Path to save the figure (None = don't save)
        show: Whether to display the plot
        ax: Matplotlib Axes object (creates new figure if None)

    Returns:
        Matplotlib Axes object with the convergence plot

    Raises:
        ValueError: If convergence data is not available or output_name not found
        TypeError: If sobol_result is not a SobolResult object

    Example:
        >>> from gas_swelling.analysis.sensitivity import SobolAnalyzer, create_default_parameter_ranges
        >>> from gas_swelling.analysis.visualization import plot_sobol_convergence
        >>> analyzer = SobolAnalyzer(
        ...     parameter_ranges=create_default_parameter_ranges(),
        ...     track_convergence=True,
        ...     convergence_checkpoints=[100, 250, 500, 750, 1000]
        ... )
        >>> result = analyzer.run_sobol_analysis(n_samples=1000, verbose=False)
        >>> plot_sobol_convergence(result, output_name='swelling', save_path='convergence.png')
    """
    # Validate input
    if not isinstance(sobol_result, SobolResult):
        raise TypeError(f"sobol_result must be a SobolResult object. Got: {type(sobol_result)}")

    # Check if convergence data is available
    if not hasattr(sobol_result, 'convergence_data') or sobol_result.convergence_data is None:
        raise ValueError(
            "Convergence data not available in SobolResult. "
            "Enable tracking by setting track_convergence=True and convergence_checkpoints "
            "when creating the SobolAnalyzer."
        )

    # Check if output_name exists
    if output_name not in sobol_result.output_names:
        available = sobol_result.output_names
        raise ValueError(
            f"Output '{output_name}' not found in Sobol results. "
            f"Available: {available}"
        )

    # Get output index
    output_idx = sobol_result.output_names.index(output_name)

    # Extract convergence data
    convergence_data = sobol_result.convergence_data

    # Check if index_type exists in convergence data
    if index_type not in convergence_data:
        raise ValueError(
            f"Index type '{index_type}' not found in convergence data. "
            f"Available: {list(convergence_data.keys())}"
        )

    # Get sample sizes and indices for the requested index type
    index_data = convergence_data[index_type]

    # Get final indices to determine top parameters
    final_indices = sobol_result.S1[:, output_idx] if index_type == 'S1' else sobol_result.ST[:, output_idx]

    # Determine which parameters to plot
    if parameter_names is None:
        parameter_names = list(sobol_result.parameter_names)

    # Filter to top_n if specified
    if top_n is not None and top_n < len(parameter_names):
        # Get indices of parameters in parameter_names
        param_indices = [i for i, name in enumerate(sobol_result.parameter_names) if name in parameter_names]

        # Get final sensitivities for these parameters
        param_sensitivities = np.abs(final_indices[param_indices])

        # Get top_n indices
        top_local_indices = np.argsort(param_sensitivities)[-top_n:][::-1]

        # Get global indices of top parameters
        top_global_indices = [param_indices[i] for i in top_local_indices]

        # Update parameter names
        parameter_names = [sobol_result.parameter_names[i] for i in top_global_indices]
    else:
        # Get global indices of requested parameters
        top_global_indices = [i for i, name in enumerate(sobol_result.parameter_names) if name in parameter_names]

    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Get colormap
    cmap = plt.get_cmap(colormap)

    # Extract convergence history for each parameter
    sample_sizes = sorted(set([key for data in index_data.values() for key in data.keys()]))

    # Plot each parameter
    for i, param_idx in enumerate(top_global_indices):
        param_name = sobol_result.parameter_names[param_idx]
        color = cmap(i / len(top_global_indices))

        # Extract convergence values for this parameter
        values = []
        sizes = []

        for sample_size in sample_sizes:
            if sample_size in index_data:
                # Get value at this checkpoint
                values.append(index_data[sample_size][param_idx])
                sizes.append(sample_size)

        # Plot line
        ax.plot(
            sizes,
            values,
            marker='o',
            linewidth=linewidth,
            markersize=markersize,
            color=color,
            alpha=alpha,
            label=param_name
        )

    # Set axis labels
    if title is None:
        output_label = output_name.replace('_', ' ').title()
        index_label = 'First-Order (S1)' if index_type == 'S1' else 'Total-Order (ST)'
        title = f'Sobol {index_label} Index Convergence - {output_label}'

    if xlabel is None:
        xlabel = 'Sample Size (N)'
    if ylabel is None:
        ylabel = f'{index_type} Index Value'

    ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)

    # Add grid if requested
    if grid:
        ax.grid(True, alpha=0.3, linestyle='--')

    # Add legend if requested
    if legend:
        ax.legend(loc=legend_loc, fontsize=9, framealpha=0.9)

    # Use log scale for x-axis if sample sizes span orders of magnitude
    if len(sample_sizes) > 1:
        min_size = min(sample_sizes)
        max_size = max(sample_sizes)
        if max_size / min_size >= 10:
            ax.set_xscale('log')

    # Adjust layout
    plt.tight_layout()

    # Save figure if path provided
    if save_path is not None:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    # Show plot if requested
    if show:
        plt.show()

    return ax
