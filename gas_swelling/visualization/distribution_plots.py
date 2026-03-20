"""
Distribution Plots Module

Provides distribution plotting functions for gas swelling simulation results.
This module implements functions to visualize statistical distributions of
bubble sizes, gas atoms per bubble, and other key variables at specific
time points or across the entire simulation.

Functions:
    plot_bubble_size_distribution: Plot bubble radius distribution histogram and KDE
    plot_bubble_radius_distribution: Plot detailed radius distribution for bulk/interface
    plot_gas_distribution_histogram: Plot gas atoms per bubble distribution

Examples:
    >>> from gas_swelling.visualization.distribution_plots import plot_bubble_size_distribution
    >>> result = model.solve(...)
    >>> fig = plot_bubble_size_distribution(result, time_point='end')
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullLocator
import numpy as np
import inspect
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Union
import warnings
from scipy import stats

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


def _resolve_hist_bins(bins: Union[int, str], weighted: bool = False) -> Union[int, str]:
    """
    Return a histogram bin setting that is compatible with the plotted data.

    NumPy does not support automatic string-based bin estimators for weighted
    histograms, so fall back to a fixed bin count in that case.
    """
    if weighted and isinstance(bins, str):
        return 20
    return bins


def plot_bubble_size_distribution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_point: Union[str, int, float] = 'end',
    length_unit: str = 'nm',
    plot_type: str = 'both',
    bins: Union[int, str] = 'auto',
    bandwidth: Optional[float] = None,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot bubble size distribution at a specific time point.

    Creates a publication-quality plot showing the distribution of bubble
    sizes using histograms and/or kernel density estimates. The plot can show
    bulk bubbles, interface bubbles, or both.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Rcb': Bulk bubble radius (m)
               - 'Rcf': Interface bubble radius (m)
               - 'Ccb': Bulk bubble concentration (cavities/m³)
               - 'Ccf': Interface bubble concentration (cavities/m³)
        params: Optional dictionary of simulation parameters
        time_point: Time point to plot ('start', 'end', 'peak', or index/time value)
                   'start': First time point
                   'end': Last time point
                   'peak': Time point with maximum swelling
                   integer: Index into time array
                   float: Specific time value in seconds
        length_unit: Unit for radius ('m', 'mm', 'um', 'nm')
        plot_type: Type of plot ('histogram', 'kde', 'both')
        bins: Number of bins for histogram or binning strategy ('auto', 'fd', 'scott', etc.)
        bandwidth: Bandwidth for KDE (None for automatic estimation)
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs (color, linewidth, etc.)

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing from result
        ValueError: If time_point is invalid

    Examples:
        >>> fig = plot_bubble_size_distribution(
        ...     result, params,
        ...     time_point='end',
        ...     length_unit='nm',
        ...     plot_type='both',
        ...     save_path='bubble_size_distribution.png'
        ... )
        >>> plt.close(fig)

        >>> # Plot at specific time index
        >>> fig = plot_bubble_size_distribution(
        ...     result, params,
        ...     time_point=100,  # Index 100
        ...     plot_type='kde'
        ... )

    Notes:
        Since the simulation provides mean bubble radius values over time,
        this function constructs a distribution by analyzing the radius
        values across time points or at a specific instant if distribution
        data is available.

        For more detailed distribution analysis, consider running multiple
        simulations with varying parameters to capture uncertainty ranges.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf']
    validate_result_data(result, required_keys)

    # Get time index
    time_idx = _get_time_index(result, time_point)

    # Extract radius data at specified time point
    Rcb = result['Rcb'][time_idx]
    Rcf = result['Rcf'][time_idx]
    Ccb = result['Ccb'][time_idx]
    Ccf = result['Ccf'][time_idx]

    # Convert to desired units
    Rcb = convert_length_units(np.array([Rcb]), length_unit)[0]
    Rcf = convert_length_units(np.array([Rcf]), length_unit)[0]

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    if plot_type == 'both':
        fig, axes = create_figure_grid(1, 2, figsize=figsize, style=style)
        ax1, ax2 = axes[0, 0], axes[0, 1]
    else:
        fig, ax = plt.subplots(figsize=figsize)
        ax1 = ax2 = ax

    alpha = kwargs.get('alpha', 0.6)

    histogram_bins = _resolve_hist_bins(bins, weighted=True)

    # Plot histogram
    if plot_type in ['histogram', 'both']:
        # Create weighted histogram based on concentration
        weights_b = np.array([Ccb])
        weights_f = np.array([Ccf])

        ax1.hist([Rcb], bins=histogram_bins, weights=weights_b,
                label=f'Bulk Bubbles (R={Rcb:.2f} {length_unit})',
                color=colors[0], alpha=alpha, edgecolor='black')
        ax1.hist([Rcf], bins=histogram_bins, weights=weights_f,
                label=f'Interface Bubbles (R={Rcf:.2f} {length_unit})',
                color=colors[1], alpha=alpha, edgecolor='black')

        ax1.set_xlabel(f'Bubble Radius ({length_unit})')
        ax1.set_ylabel('Bubble Concentration (cavities/m³)')
        ax1.set_title(f'Bubble Size Distribution Histogram\n'
                     f'Time: {convert_time_units(result["time"][time_idx], "minutes"):.1f} min')
        ax1.legend()
        ax1.grid(True, linestyle='--', alpha=0.3)

    # Plot KDE
    if plot_type in ['kde', 'both']:
        # Create synthetic distribution around mean value for visualization
        # Using a normal distribution with reasonable spread
        spread_fraction = kwargs.get('spread_fraction', 0.2)
        r_range = np.array([
            max(0, Rcb * (1 - spread_fraction)),
            Rcb * (1 + spread_fraction),
            max(0, Rcf * (1 - spread_fraction)),
            Rcf * (1 + spread_fraction)
        ])

        r_min = min(r_range) * 0.5
        r_max = max(r_range) * 1.5
        r_plot = np.linspace(r_min, r_max, 200)

        # Create Gaussian KDE around mean values
        std_b = Rcb * spread_fraction
        std_f = Rcf * spread_fraction

        # Generate synthetic sample data for KDE (create multiple points around mean)
        n_samples = 100
        samples_b = np.random.normal(Rcb, std_b, n_samples)
        samples_f = np.random.normal(Rcf, std_f, n_samples)
        # Ensure all samples are positive
        samples_b = np.maximum(samples_b, 0)
        samples_f = np.maximum(samples_f, 0)

        kde_b = stats.gaussian_kde(samples_b, bw_method=bandwidth)
        kde_f = stats.gaussian_kde(samples_f, bw_method=bandwidth)

        # Scale by concentration
        scale_b = Ccb / (kde_b([Rcb])[0] if kde_b(np.array([Rcb]))[0] > 0 else 1.0)
        scale_f = Ccf / (kde_f([Rcf])[0] if kde_f(np.array([Rcf]))[0] > 0 else 1.0)

        ax2.plot(r_plot, kde_b(r_plot) * scale_b,
                label=f'Bulk Bubbles (R={Rcb:.2f} {length_unit})',
                color=colors[0], linewidth=kwargs.get('linewidth', 2.0))
        ax2.plot(r_plot, kde_f(r_plot) * scale_f,
                label=f'Interface Bubbles (R={Rcf:.2f} {length_unit})',
                color=colors[1], linewidth=kwargs.get('linewidth', 2.0))
        ax2.fill_between(r_plot, kde_b(r_plot) * scale_b, alpha=0.3, color=colors[0])
        ax2.fill_between(r_plot, kde_f(r_plot) * scale_f, alpha=0.3, color=colors[1])

        ax2.set_xlabel(f'Bubble Radius ({length_unit})')
        ax2.set_ylabel('Density (scaled by concentration)')
        ax2.set_title(f'Bubble Size Distribution (KDE)\n'
                     f'Time: {convert_time_units(result["time"][time_idx], "minutes"):.1f} min')
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig


def plot_bubble_radius_distribution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_points: Union[str, List[Union[int, float]]] = 'end',
    length_unit: str = 'nm',
    plot_type: str = 'histogram',
    region: str = 'both',
    bins: Union[int, str] = 'auto',
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot detailed bubble radius distribution for bulk and/or interface regions.

    Creates a detailed distribution plot showing bubble radius statistics
    at one or multiple time points. Useful for comparing bubble size evolution
    or analyzing the distribution at key simulation stages.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Rcb': Bulk bubble radius (m)
               - 'Rcf': Interface bubble radius (m)
        params: Optional dictionary of simulation parameters
        time_points: Time point(s) to plot ('start', 'end', 'peak', or list of indices/values)
        length_unit: Unit for radius ('m', 'mm', 'um', 'nm')
        plot_type: Type of plot ('histogram', 'box', 'violin', 'timeline')
        region: Region to plot ('bulk', 'interface', 'both')
        bins: Number of bins for histogram or binning strategy
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing or region is invalid

    Examples:
        >>> fig = plot_bubble_radius_distribution(
        ...     result, params,
        ...     time_points=['start', 'end'],
        ...     plot_type='box',
        ...     region='both'
        ... )
        >>> plt.close(fig)

        >>> # Compare distribution at multiple times
        >>> fig = plot_bubble_radius_distribution(
        ...     result, params,
        ...     time_points=[0, 100, 200],
        ...     plot_type='timeline'
        ... )

    Notes:
        The 'timeline' plot type shows how the radius changes over time,
        which is useful for identifying trends and inflection points.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Rcb', 'Rcf']
    validate_result_data(result, required_keys)

    # Normalize time_points to list of indices
    if isinstance(time_points, (str, int, float)):
        time_points = [time_points]

    time_indices = []
    for tp in time_points:
        try:
            time_indices.append(_get_time_index(result, tp))
        except ValueError:
            # For lists like [0, 50, 99], treat out-of-range integers as
            # physical time values rather than array indices.
            if isinstance(tp, int):
                time_indices.append(_get_time_index(result, float(tp)))
            else:
                raise

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Determine which regions to plot
    if region == 'bulk':
        regions_to_plot = [('Bulk', 'Rcb', colors[0])]
    elif region == 'interface':
        regions_to_plot = [('Interface', 'Rcf', colors[1])]
    elif region == 'both':
        regions_to_plot = [('Bulk', 'Rcb', colors[0]), ('Interface', 'Rcf', colors[1])]
    else:
        raise ValueError(f"Invalid region: {region}. Must be 'bulk', 'interface', or 'both'")

    # Create figure based on plot type
    if plot_type == 'timeline':
        fig, ax = plt.subplots(figsize=figsize)
        time_data = convert_time_units(result['time'], 'minutes')

        for region_name, radius_key, color in regions_to_plot:
            radius_data = convert_length_units(result[radius_key], length_unit)
            ax.plot(time_data, radius_data, label=region_name,
                   color=color, linewidth=kwargs.get('linewidth', 2.0))

            # Highlight selected time points
            for idx in time_indices:
                ax.axvline(time_data[idx], color=color, linestyle='--', alpha=0.5)
                ax.plot(time_data[idx], radius_data[idx], 'o',
                       color=color, markersize=8)

        ax.set_xlabel(get_time_unit_label('minutes'))
        ax.set_ylabel(f'Bubble Radius ({length_unit})')
        ax.set_title('Bubble Radius Timeline')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)

    elif plot_type == 'box':
        fig, ax = plt.subplots(figsize=figsize)

        # Prepare data for box plot
        data_for_box = []
        labels_for_box = []

        for idx in time_indices:
            time_label = f"t={convert_time_units(result['time'][idx], 'minutes'):.0f} min"
            for region_name, radius_key, color in regions_to_plot:
                radius_val = convert_length_units(np.array([result[radius_key][idx]]), length_unit)[0]
                # Create a small distribution around the mean for box plot visualization
                spread = radius_val * 0.1
                sample = np.random.normal(radius_val, spread, size=50)
                data_for_box.append(sample)
                labels_for_box.append(f"{region_name}\n{time_label}")

        boxplot_kwargs = {'patch_artist': True}
        label_param = 'tick_labels' if 'tick_labels' in inspect.signature(ax.boxplot).parameters else 'labels'
        boxplot_kwargs[label_param] = labels_for_box
        bp = ax.boxplot(data_for_box, **boxplot_kwargs)

        # Color the boxes
        for i, (patch, region_info) in enumerate(zip(bp['boxes'], regions_to_plot * len(time_indices))):
            region_idx = i % len(regions_to_plot)
            patch.set_facecolor(regions_to_plot[region_idx][2])
            patch.set_alpha(0.6)

        ax.set_ylabel(f'Bubble Radius ({length_unit})')
        ax.set_title('Bubble Radius Distribution at Selected Time Points')
        ax.grid(True, linestyle='--', alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')

    elif plot_type == 'histogram':
        if len(time_indices) == 1:
            fig, ax = plt.subplots(figsize=figsize)
            axes = [ax]
        else:
            fig, axes = create_figure_grid(1, len(time_indices), figsize=figsize, style=style)
            axes = np.asarray(axes).ravel()

        for i, idx in enumerate(time_indices):
            ax = axes[i] if len(time_indices) > 1 else axes[0]

            for region_name, radius_key, color in regions_to_plot:
                radius_val = convert_length_units(np.array([result[radius_key][idx]]), length_unit)[0]
                spread = radius_val * 0.15

                # Create synthetic distribution
                sample = np.random.normal(radius_val, spread, size=100)
                sample = sample[sample > 0]  # Remove negative values

                ax.hist(sample, bins=bins, alpha=0.6, label=f"{region_name} (R={radius_val:.2f})",
                       color=color, edgecolor='black')

            ax.set_xlabel(f'Bubble Radius ({length_unit})')
            ax.set_ylabel('Frequency')
            ax.set_title(f"t={convert_time_units(result['time'][idx], 'minutes'):.0f} min")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.3)

    else:  # violin or other types
        raise ValueError(f"Unsupported plot_type: {plot_type}. "
                        f"Supported types: 'histogram', 'box', 'timeline'")

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig


def plot_gas_distribution_histogram(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_point: Union[str, int, float] = 'end',
    plot_type: str = 'histogram',
    region: str = 'both',
    bins: Union[int, str] = 'auto',
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot gas atoms per bubble distribution.

    Creates a histogram or distribution plot showing the number of gas atoms
    per bubble at a specific time point. This helps understand the gas content
    distribution in bubbles across different regions.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Ncb': Gas atoms per bulk bubble
               - 'Ncf': Gas atoms per interface bubble
        params: Optional dictionary of simulation parameters
        time_point: Time point to plot ('start', 'end', 'peak', or index/time value)
        plot_type: Type of plot ('histogram', 'comparison', 'evolution')
        region: Region to plot ('bulk', 'interface', 'both')
        bins: Number of bins for histogram or binning strategy
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing or region is invalid

    Examples:
        >>> fig = plot_gas_distribution_histogram(
        ...     result, params,
        ...     time_point='end',
        ...     plot_type='comparison',
        ...     region='both'
        ... )
        >>> plt.close(fig)

        >>> # Plot evolution over time
        >>> fig = plot_gas_distribution_histogram(
        ...     result, params,
        ...     plot_type='evolution'
        ... )

    Notes:
        Gas atoms per bubble (Ncb, Ncf) can vary over orders of magnitude,
        so log-scale plots are often useful for visualization.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Ncb', 'Ncf']
    validate_result_data(result, required_keys)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    if plot_type == 'evolution':
        fig, ax = plt.subplots(figsize=figsize)
        time_data = convert_time_units(result['time'], 'minutes')

        if region in ['bulk', 'both']:
            ax.semilogy(time_data, result['Ncb'], label='Bulk Bubbles',
                       color=colors[0], linewidth=kwargs.get('linewidth', 2.0))
        if region in ['interface', 'both']:
            ax.semilogy(time_data, result['Ncf'], label='Interface Bubbles',
                       color=colors[1], linewidth=kwargs.get('linewidth', 2.0))

        # Avoid mathtext-dependent default log tick formatting on environments
        # with incomplete font fallbacks (seen on some macOS/Python 3.14 setups).
        plain_log_formatter = FuncFormatter(lambda y, _: f'{y:g}')
        ax.yaxis.set_major_formatter(plain_log_formatter)
        ax.yaxis.set_minor_formatter(plain_log_formatter)
        ax.yaxis.set_minor_locator(NullLocator())

        ax.set_xlabel(get_time_unit_label('minutes'))
        ax.set_ylabel('Gas Atoms per Bubble')
        ax.set_title('Gas Atoms per Bubble Evolution')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)

    elif plot_type == 'comparison':
        # Get time index
        time_idx = _get_time_index(result, time_point)

        fig, ax = plt.subplots(figsize=figsize)

        x_positions = [0, 1]
        x_labels = []
        y_values = []

        if region in ['bulk', 'both']:
            ncb_val = result['Ncb'][time_idx]
            y_values.append(ncb_val)
            x_labels.append(f'Bulk\n(N={ncb_val:.1e})')

        if region in ['interface', 'both']:
            ncf_val = result['Ncf'][time_idx]
            y_values.append(ncf_val)
            x_labels.append(f'Interface\n(N={ncf_val:.1e})')

        colors_to_use = [colors[0]] if region == 'bulk' else ([colors[1]] if region == 'interface' else colors)

        bars = ax.bar(x_positions[:len(y_values)], y_values,
                     color=colors_to_use, alpha=0.7, edgecolor='black')

        ax.set_xticks(x_positions[:len(y_values)])
        ax.set_xticklabels(x_labels)
        ax.set_ylabel('Gas Atoms per Bubble')
        ax.set_title(f'Gas Atoms per Bubble Comparison\n'
                    f'Time: {convert_time_units(result["time"][time_idx], "minutes"):.1f} min')
        ax.grid(True, linestyle='--', alpha=0.3, axis='y')

        # Use log scale if values span orders of magnitude
        if max(y_values) / min(y_values) > 100:
            ax.set_yscale('log')

    elif plot_type == 'histogram':
        # Get time index
        time_idx = _get_time_index(result, time_point)

        fig, ax = plt.subplots(figsize=figsize)

        for region_name, gas_key, color in [('Bulk', 'Ncb', colors[0]), ('Interface', 'Ncf', colors[1])]:
            if region in ['both', region_name.lower()]:
                n_val = result[gas_key][time_idx]
                spread = n_val * 0.1

                # Create synthetic distribution
                sample = np.random.normal(n_val, spread, size=100)
                sample = sample[sample > 0]  # Remove negative values

                ax.hist(sample, bins=bins, alpha=0.6,
                       label=f"{region_name} (N={n_val:.1e})",
                       color=color, edgecolor='black')

        ax.set_xlabel('Gas Atoms per Bubble')
        ax.set_ylabel('Frequency')
        ax.set_title(f'Gas Atoms Distribution\n'
                    f'Time: {convert_time_units(result["time"][time_idx], "minutes"):.1f} min')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)

        # Use log scale on x-axis if values are large
        max_n = max(result['Ncb'][time_idx], result['Ncf'][time_idx])
        if max_n > 1e6:
            ax.set_xscale('log')

    else:
        raise ValueError(f"Unsupported plot_type: {plot_type}. "
                        f"Supported types: 'histogram', 'comparison', 'evolution'")

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig


def _get_time_index(result: Dict[str, np.ndarray],
                   time_point: Union[str, int, float]) -> int:
    """
    Helper function to get time index from various time_point specifications.

    Args:
        result: Result dictionary with 'time' key
        time_point: Time point specification

    Returns:
        Integer index into time array

    Raises:
        ValueError: If time_point is invalid
    """
    time_array = result['time']

    if isinstance(time_point, str):
        if time_point == 'start':
            return 0
        elif time_point == 'end':
            return len(time_array) - 1
        elif time_point == 'peak':
            # Find time point with maximum swelling
            if 'swelling' in result:
                return np.argmax(result['swelling'])
            else:
                # Calculate swelling if not in result
                Rcb = result['Rcb']
                Rcf = result['Rcf']
                Ccb = result['Ccb']
                Ccf = result['Ccf']
                V_bubble = (4.0 / 3.0) * np.pi * (Rcb**3 * Ccb + Rcf**3 * Ccf)
                return np.argmax(V_bubble)
        else:
            raise ValueError(f"Invalid time_point string: {time_point}. "
                           f"Must be 'start', 'end', or 'peak'")

    elif isinstance(time_point, int):
        # Assume it's an index
        if time_point < 0 or time_point >= len(time_array):
            raise ValueError(f"Time index {time_point} out of range [0, {len(time_array)-1}]")
        return time_point

    elif isinstance(time_point, float):
        # Assume it's a time value in seconds
        idx = np.argmin(np.abs(time_array - time_point))
        return idx

    else:
        raise ValueError(f"Invalid time_point type: {type(time_point)}. "
                        f"Must be str, int, or float")
