"""
Contour Plots Module

Provides plotting functions for 2D contour plots and heatmaps, including
temperature-burnup contour plots and parameter-parameter heatmaps.

This module implements functions to visualize how model outputs vary with
two parameters simultaneously, enabling comprehensive parameter sensitivity
studies and identification of optimal operating conditions.

Functions:
    plot_temperature_contour: Create 2D contour plot of swelling vs temperature and burnup
    plot_2d_parameter_sweep: Create general parameter-parameter heatmap
    plot_swelling_heatmap: Create heatmap with colorbar and contour lines

Examples:
    >>> from gas_swelling.visualization.contour_plots import plot_temperature_contour
    >>> temperatures = np.linspace(600, 800, 20)
    >>> burnups = np.linspace(0, 5, 20)
    >>> swelling_data = np.random.rand(20, 20)  # Shape (n_temps, n_burnups)
    >>> fig = plot_temperature_contour(temperatures, burnups, swelling_data)
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Union
import warnings


def _harden_log_axis(ax, axis: str = 'x') -> None:
    """Replace log-axis tick formatters with plain FuncFormatters to avoid mathtext rendering."""
    def _fmt(val, pos):
        if val <= 0:
            return ''
        exp = int(np.floor(np.log10(val)))
        mantissa = val / (10 ** exp)
        if abs(mantissa - 1.0) < 1e-9:
            return f'1e{exp}'
        return f'{mantissa:.2g}e{exp}'

    formatter = mticker.FuncFormatter(_fmt)
    if axis in ('x', 'both'):
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    if axis in ('y', 'both'):
        ax.yaxis.set_major_formatter(formatter)
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())

from .utils import (
    save_figure,
    create_figure_grid,
    get_color_palette,
    format_axis_scientific,
    set_axis_limits,
    apply_publication_style
)


def plot_temperature_contour(
    temperatures: np.ndarray,
    x_param: np.ndarray,
    swelling_data: np.ndarray,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 8),
    style: str = 'default',
    xlabel: str = 'Burnup (%FIMA)',
    ylabel: str = 'Temperature (K)',
    title: str = 'Swelling Contour Plot',
    cmap: str = 'viridis',
    contour_levels: Optional[int] = None,
    show_contour_lines: bool = True,
    colorbar_label: str = 'Swelling (%)',
    **kwargs
) -> plt.Figure:
    """
    Create a 2D contour plot showing swelling as a function of temperature and another parameter.

    Creates a publication-quality filled contour plot with optional contour lines
    and colorbar, showing how swelling varies with temperature and a second parameter
    (typically burnup, time, or another material parameter).

    Args:
        temperatures: 1D array of temperature values (K)
        x_param: 1D array of values for the x-axis parameter (e.g., burnup, time)
        swelling_data: 2D array of swelling values with shape (len(temperatures), len(x_param))
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        cmap: Colormap name (e.g., 'viridis', 'plasma', 'coolwarm', 'RdYlBu_r')
        contour_levels: Number of contour levels (None for automatic)
        show_contour_lines: Whether to draw contour lines on top of filled contours
        colorbar_label: Label for the colorbar
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If array shapes are incompatible or data is invalid

    Examples:
        >>> import numpy as np
        >>> temps = np.linspace(600, 800, 20)
        >>> burnups = np.linspace(0, 5, 20)
        >>> # swelling_data shape: (20, 20) - swelling for each (temp, burnup) pair
        >>> swelling = np.random.rand(20, 20) * 3
        >>> fig = plot_temperature_contour(
        ...     temps, burnups, swelling,
        ...     save_path='temperature_burnup_contour.png'
        ... )
        >>> plt.close(fig)

    Notes:
        - The swelling_data array should have shape (n_temperatures, n_x_param)
        - Temperature is always plotted on the y-axis
        - The x-axis parameter can be burnup, time, or any other parameter
        - Recommended colormaps: 'viridis', 'plasma' (sequential); 'coolwarm', 'RdYlBu_r' (diverging)
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input shapes
    if temperatures.ndim != 1 or x_param.ndim != 1:
        raise ValueError("temperatures and x_param must be 1D arrays")

    if swelling_data.ndim != 2:
        raise ValueError("swelling_data must be a 2D array")

    if swelling_data.shape != (len(temperatures), len(x_param)):
        raise ValueError(
            f"swelling_data shape {swelling_data.shape} incompatible with "
            f"temperatures ({len(temperatures)}) and x_param ({len(x_param)})"
        )

    # Create meshgrid for contour plotting
    X, Y = np.meshgrid(x_param, temperatures)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Determine contour levels
    if contour_levels is None:
        # Automatic level selection
        contour_levels = 15

    # Create filled contour plot
    contour_fill = ax.contourf(
        X, Y, swelling_data,
        levels=contour_levels,
        cmap=cmap,
        alpha=0.9
    )

    # Add contour lines if requested
    if show_contour_lines:
        contour_lines = ax.contour(
            X, Y, swelling_data,
            levels=contour_levels,
            colors='black',
            linewidths=0.5,
            alpha=0.4
        )
        # Add labels to contour lines
        ax.clabel(contour_lines, inline=True, fontsize=9, fmt='%1.1f')

    # Add colorbar
    cbar = fig.colorbar(contour_fill, ax=ax)
    cbar.set_label(colorbar_label)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    # Set axis limits if provided
    if 'xlim' in kwargs:
        ax.set_xlim(kwargs['xlim'])
    if 'ylim' in kwargs:
        ax.set_ylim(kwargs['ylim'])

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig


def plot_2d_parameter_sweep(
    param1_values: np.ndarray,
    param2_values: np.ndarray,
    output_data: np.ndarray,
    param1_name: str = 'Parameter 1',
    param2_name: str = 'Parameter 2',
    output_name: str = 'Output',
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 8),
    style: str = 'default',
    cmap: str = 'viridis',
    contour_levels: Optional[int] = None,
    show_contour_lines: bool = True,
    param1_unit: str = '',
    param2_unit: str = '',
    output_unit: str = '',
    **kwargs
) -> plt.Figure:
    """
    Create a general 2D parameter sweep heatmap/contour plot.

    Creates a publication-quality contour plot showing how an output variable
    varies with two input parameters. This is useful for visualizing parameter
    sensitivity and identifying optimal operating regions.

    Args:
        param1_values: 1D array of values for the first parameter (x-axis)
        param2_values: 1D array of values for the second parameter (y-axis)
        output_data: 2D array of output values with shape (len(param2_values), len(param1_values))
        param1_name: Name of the first parameter
        param2_name: Name of the second parameter
        output_name: Name of the output variable
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        cmap: Colormap name
        contour_levels: Number of contour levels (None for automatic)
        show_contour_lines: Whether to draw contour lines on top of filled contours
        param1_unit: Unit for parameter 1
        param2_unit: Unit for parameter 2
        output_unit: Unit for output variable
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If array shapes are incompatible or data is invalid

    Examples:
        >>> import numpy as np
        >>> dislocation_densities = np.logspace(13, 15, 20)
        >>> temperatures = np.linspace(600, 800, 20)
        >>> # Simulate swelling for each combination
        >>> swelling = np.random.rand(20, 20) * 3
        >>> fig = plot_2d_parameter_sweep(
        ...     dislocation_densities, temperatures, swelling,
        ...     param1_name='Dislocation Density',
        ...     param2_name='Temperature',
        ...     output_name='Swelling',
        ...     param1_unit='m^-2',
        ...     param2_unit='K',
        ...     output_unit='%',
        ...     save_path='param_sweep_contour.png'
        ... )
        >>> plt.close(fig)

    Notes:
        - The output_data array should have shape (n_param2, n_param1)
        - Parameter 1 is plotted on the x-axis, Parameter 2 on the y-axis
        - Log scale is automatically applied to x-axis if param1 spans >2 orders of magnitude
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input shapes
    if param1_values.ndim != 1 or param2_values.ndim != 1:
        raise ValueError("param1_values and param2_values must be 1D arrays")

    if output_data.ndim != 2:
        raise ValueError("output_data must be a 2D array")

    if output_data.shape != (len(param2_values), len(param1_values)):
        raise ValueError(
            f"output_data shape {output_data.shape} incompatible with "
            f"param2_values ({len(param2_values)}) and param1_values ({len(param1_values)})"
        )

    # Create meshgrid for contour plotting
    X, Y = np.meshgrid(param1_values, param2_values)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Determine contour levels
    if contour_levels is None:
        contour_levels = 15

    # Create filled contour plot
    contour_fill = ax.contourf(
        X, Y, output_data,
        levels=contour_levels,
        cmap=cmap,
        alpha=0.9
    )

    # Add contour lines if requested
    if show_contour_lines:
        contour_lines = ax.contour(
            X, Y, output_data,
            levels=contour_levels,
            colors='black',
            linewidths=0.5,
            alpha=0.4
        )
        ax.clabel(contour_lines, inline=True, fontsize=9, fmt='%1.1f')

    # Add colorbar
    cbar_label = output_name if not output_unit else f'{output_name} ({output_unit})'
    cbar = fig.colorbar(contour_fill, ax=ax)
    cbar.set_label(cbar_label)

    # Axis labels
    xlabel = param1_name if not param1_unit else f'{param1_name} ({param1_unit})'
    ylabel = param2_name if not param2_unit else f'{param2_name} ({param2_unit})'

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'{output_name} vs {param1_name} and {param2_name}')

    # Use log scale for x-axis if parameter spans multiple orders of magnitude
    if np.max(param1_values) / np.min(param1_values) > 100:
        ax.set_xscale('log')
        _harden_log_axis(ax, axis='x')

    # Set axis limits if provided
    if 'xlim' in kwargs:
        ax.set_xlim(kwargs['xlim'])
    if 'ylim' in kwargs:
        ax.set_ylim(kwargs['ylim'])

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig


def plot_swelling_heatmap(
    temperatures: np.ndarray,
    param_values: np.ndarray,
    swelling_data: np.ndarray,
    param_name: str = 'Burnup',
    param_unit: str = '%FIMA',
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (12, 8),
    style: str = 'default',
    cmap: str = 'YlOrRd',
    show_colorbar: bool = True,
    colorbar_orientation: str = 'vertical',
    show_contour_lines: bool = True,
    contour_levels: Optional[int] = None,
    annotate_values: bool = False,
    annotation_format: str = '%.2f',
    **kwargs
) -> plt.Figure:
    """
    Create a heatmap visualization of swelling with colorbar and contour lines.

    Creates a publication-quality heatmap showing swelling as a function
    of temperature and another parameter, with a colorbar and optional contour
    lines for enhanced visualization of data gradients.

    Args:
        temperatures: 1D array of temperature values (K)
        param_values: 1D array of values for the x-axis parameter
        swelling_data: 2D array of swelling values with shape (len(temperatures), len(param_values))
        param_name: Name of the x-axis parameter
        param_unit: Unit of the x-axis parameter
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        cmap: Colormap name
        show_colorbar: Whether to show colorbar
        colorbar_orientation: Orientation of colorbar ('vertical' or 'horizontal')
        show_contour_lines: Whether to draw contour lines on top of the heatmap
        contour_levels: Number of contour levels (None for automatic)
        annotate_values: Whether to annotate each cell with its value
        annotation_format: Format string for annotations (e.g., '%.2f', '%.1f')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If array shapes are incompatible or data is invalid

    Examples:
        >>> import numpy as np
        >>> temps = np.linspace(600, 800, 20)
        >>> burnups = np.linspace(0, 5, 20)
        >>> swelling = np.random.rand(20, 20) * 3
        >>> fig = plot_swelling_heatmap(
        ...     temps, burnups, swelling,
        ...     param_name='Burnup',
        ...     show_contour_lines=True,
        ...     save_path='swelling_heatmap.png'
        ... )
        >>> plt.close(fig)

    Notes:
        - This function uses contourf for filled contours with optional overlay lines
        - Temperature is on the y-axis, parameter is on the x-axis
        - The 'YlOrRd' (Yellow-Orange-Red) colormap is commonly used for swelling visualization
        - For diverging data, consider 'coolwarm' or 'RdYlBu_r' colormaps
        - Contour lines help visualize gradients and identify regions of similar swelling values
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input shapes
    if temperatures.ndim != 1 or param_values.ndim != 1:
        raise ValueError("temperatures and param_values must be 1D arrays")

    if swelling_data.ndim != 2:
        raise ValueError("swelling_data must be a 2D array")

    if swelling_data.shape != (len(temperatures), len(param_values)):
        raise ValueError(
            f"swelling_data shape {swelling_data.shape} incompatible with "
            f"temperatures ({len(temperatures)}) and param_values ({len(param_values)})"
        )

    # Create meshgrid for contour plotting
    X, Y = np.meshgrid(param_values, temperatures)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Determine contour levels
    if contour_levels is None:
        contour_levels = 15

    # Create filled contour plot (heatmap)
    contour_fill = ax.contourf(
        X, Y, swelling_data,
        levels=contour_levels,
        cmap=cmap,
        alpha=0.9
    )

    # Add contour lines if requested
    if show_contour_lines:
        contour_lines = ax.contour(
            X, Y, swelling_data,
            levels=contour_levels,
            colors='black',
            linewidths=0.5,
            alpha=0.4
        )
        # Add labels to contour lines
        ax.clabel(contour_lines, inline=True, fontsize=9, fmt='%1.1f')

    # Add colorbar
    if show_colorbar:
        if colorbar_orientation == 'horizontal':
            cbar = fig.colorbar(contour_fill, ax=ax, orientation='horizontal', pad=0.15)
            cbar_label = 'Swelling (%)'
            cbar.set_label(cbar_label)
        else:
            cbar = fig.colorbar(contour_fill, ax=ax)
            cbar.set_label('Swelling (%)')

    # Annotate values if requested (only for small grids)
    if annotate_values:
        n_params = len(param_values)
        n_temps = len(temperatures)

        # Only annotate if grid is not too large
        if n_params * n_temps <= 100:
            for i in range(n_temps):
                for j in range(n_params):
                    text = ax.text(
                        param_values[j], temperatures[i],
                        annotation_format % swelling_data[i, j],
                        ha="center",
                        va="center",
                        color="black",
                        fontsize=8
                    )
        else:
            warnings.warn(
                "Grid too large for annotation. "
                "Consider using contour lines instead (show_contour_lines=True)"
            )

    # Labels
    xlabel = param_name if not param_unit else f'{param_name} ({param_unit})'
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Temperature (K)')
    ax.set_title('Swelling Heatmap')

    # Set axis limits if provided
    if 'xlim' in kwargs:
        ax.set_xlim(kwargs['xlim'])
    if 'ylim' in kwargs:
        ax.set_ylim(kwargs['ylim'])

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig
