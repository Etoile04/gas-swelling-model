"""
Parameter Sweeps Module

Provides plotting functions for parameter sweep studies, including temperature
sweeps, dislocation density variations, and other parameter sensitivity analyses.

This module implements functions to visualize how model outputs vary with
different input parameters, enabling parameter sensitivity studies and
model validation against experimental data.

Functions:
    plot_temperature_sweep: Plot swelling vs temperature for single parameter set
    plot_multi_param_temperature_sweep: Plot multiple temperature sweep curves
    plot_parameter_sensitivity: Plot sensitivity to various parameters
    plot_arrhenius_analysis: Create Arrhenius plots for activation energy

Examples:
    >>> from gas_swelling.visualization.parameter_sweeps import plot_temperature_sweep
    >>> temperatures = [600, 650, 700, 750, 800]
    >>> swellings = [0.5, 1.2, 2.1, 1.8, 1.0]
    >>> fig = plot_temperature_sweep(temperatures, swellings)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Union
import warnings

from .utils import (
    save_figure,
    create_figure_grid,
    get_color_palette,
    format_axis_scientific,
    set_axis_limits,
    apply_publication_style
)


def plot_temperature_sweep(
    temperatures: np.ndarray,
    swellings: np.ndarray,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    xlabel: str = 'Temperature (K)',
    ylabel: str = 'Swelling (%)',
    title: str = 'Swelling vs Temperature',
    **kwargs
) -> plt.Figure:
    """
    Plot swelling rate as a function of temperature.

    Creates a publication-quality plot showing how the final swelling rate
    varies with temperature for a single set of simulation parameters.

    Args:
        temperatures: Array of temperature values (K)
        swellings: Array of final swelling percentages corresponding to temperatures
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        **kwargs: Additional matplotlib kwargs (color, linewidth, marker, etc.)

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If temperatures and swellings have different lengths

    Examples:
        >>> import numpy as np
        >>> temps = np.array([600, 650, 700, 750, 800])
        >>> swell = np.array([0.5, 1.2, 2.1, 1.8, 1.0])
        >>> fig = plot_temperature_sweep(
        ...     temps, swell,
        ...     save_path='temperature_sweep.png'
        ... )
        >>> plt.close(fig)

    Notes:
        This function creates a simple single-curve temperature sweep plot.
        For multiple parameter sets, use plot_multi_param_temperature_sweep instead.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input
    if len(temperatures) != len(swellings):
        raise ValueError(f"temperatures and swellings must have same length: "
                        f"{len(temperatures)} != {len(swellings)}")

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot settings
    color = kwargs.get('color', 'blue')
    linewidth = kwargs.get('linewidth', 2.0)
    marker = kwargs.get('marker', 'o')
    markersize = kwargs.get('markersize', 8)

    # Plot data
    ax.plot(temperatures, swellings,
            marker=marker,
            linestyle='-',
            color=color,
            linewidth=linewidth,
            markersize=markersize,
            label=kwargs.get('label', None))

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.3)

    # Add legend if label was provided
    if 'label' in kwargs:
        ax.legend()

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


def plot_multi_param_temperature_sweep(
    results: List[Dict[str, np.ndarray]],
    param_name: str = 'Dislocation Density',
    param_values: Optional[List[float]] = None,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (12, 8),
    style: str = 'default',
    xlabel: str = 'Temperature (K)',
    ylabel: str = 'Swelling (%)',
    title: Optional[str] = None,
    **kwargs
) -> plt.Figure:
    """
    Plot multiple temperature sweep curves for different parameter values.

    Creates a publication-quality plot showing how temperature dependence
    varies with a selected parameter (e.g., dislocation density, surface energy).

    Args:
        results: List of dictionaries, each containing:
                - 'temperatures': Array of temperature values (K)
                - 'swellings': Array of swelling percentages
        param_name: Name of the varying parameter for legend labels
        param_values: Optional list of parameter values for legend labels
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title (auto-generated if None)
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If results list is empty or data format is incorrect

    Examples:
        >>> results = [
        ...     {'temperatures': np.array([600, 700, 800]),
        ...      'swellings': np.array([0.5, 1.2, 2.1])},
        ...     {'temperatures': np.array([600, 700, 800]),
        ...      'swellings': np.array([0.3, 0.8, 1.5])}
        ... ]
        >>> fig = plot_multi_param_temperature_sweep(
        ...     results,
        ...     param_name='Dislocation Density',
        ...     param_values=['1x', '2x'],
        ...     save_path='multi_param_sweep.png'
        ... )
        >>> plt.close(fig)

    Notes:
        Uses different colors and markers for each parameter set to distinguish
        between different curves in the plot.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input
    if not results:
        raise ValueError("results list cannot be empty")

    # Get color palette and markers
    colors = get_color_palette('default')
    markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h']

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Default title if not provided
    if title is None:
        title = f'Swelling vs Temperature - {param_name} Variation'

    # Plot each curve
    linewidth = kwargs.get('linewidth', 2.0)
    markersize = kwargs.get('markersize', 8)

    for i, result in enumerate(results):
        # Validate result structure
        if 'temperatures' not in result or 'swellings' not in result:
            raise ValueError(f"Result {i} missing required keys 'temperatures' or 'swellings'")

        temps = result['temperatures']
        swell = result['swellings']

        # Create label for legend
        if param_values and i < len(param_values):
            label = f'{param_name} = {param_values[i]}'
        else:
            label = f'{param_name} Set {i+1}'

        # Plot with unique color and marker
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        ax.plot(temps, swell,
                marker=marker,
                linestyle='-',
                color=color,
                linewidth=linewidth,
                markersize=markersize,
                label=label)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

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


def plot_parameter_sensitivity(
    param_values: np.ndarray,
    swellings: np.ndarray,
    param_name: str = 'Parameter',
    param_unit: str = '',
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot sensitivity of swelling rate to a specific parameter.

    Creates a plot showing how the final swelling rate varies with
    a single parameter while keeping other parameters constant.

    Args:
        param_values: Array of parameter values
        swellings: Array of final swelling percentages
        param_name: Name of the parameter
        param_unit: Unit of the parameter (e.g., 'm^-2', 'eV')
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> dislocation_densities = np.array([1e13, 5e13, 1e14, 5e14, 1e15])
        >>> swellings = np.array([0.8, 1.2, 1.5, 1.9, 2.1])
        >>> fig = plot_parameter_sensitivity(
        ...     dislocation_densities, swellings,
        ...     param_name='Dislocation Density',
        ...     param_unit='m^-2',
        ...     save_path='dislocation_sensitivity.png'
        ... )
        >>> plt.close(fig)

    Notes:
        Uses log scale for x-axis if parameter values span multiple orders of magnitude.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input
    if len(param_values) != len(swellings):
        raise ValueError(f"param_values and swellings must have same length: "
                        f"{len(param_values)} != {len(swellings)}")

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot settings
    color = kwargs.get('color', 'green')
    linewidth = kwargs.get('linewidth', 2.0)
    marker = kwargs.get('marker', 'o')
    markersize = kwargs.get('markersize', 8)

    # Construct label
    xlabel = param_name if not param_unit else f'{param_name} ({param_unit})'

    # Plot data
    ax.plot(param_values, swellings,
            marker=marker,
            linestyle='-',
            color=color,
            linewidth=linewidth,
            markersize=markersize)

    # Use log scale for x-axis if values span orders of magnitude
    if np.max(param_values) / np.min(param_values) > 100:
        ax.set_xscale('log')

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Swelling (%)')
    ax.set_title(f'Sensitivity to {param_name}')
    ax.grid(True, linestyle='--', alpha=0.3)

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


def plot_arrhenius_analysis(
    temperatures: np.ndarray,
    swelling_rates: np.ndarray,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    show_activation_energy: bool = True,
    **kwargs
) -> plt.Figure:
    """
    Create Arrhenius plot for temperature-dependent swelling rate.

    Creates a semilog plot of ln(swelling_rate) vs 1/T to analyze
    activation energy for the swelling process.

    Args:
        temperatures: Array of temperature values (K)
        swelling_rates: Array of swelling rate values (%/time)
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        show_activation_energy: If True, display activation energy in title
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If temperatures and swelling_rates have different lengths

    Examples:
        >>> temps = np.array([600, 650, 700, 750, 800])
        >>> rates = np.array([0.01, 0.05, 0.2, 0.5, 0.8])
        >>> fig = plot_arrhenius_analysis(
        ...     temps, rates,
        ...     save_path='arrhenius.png'
        ... )
        >>> plt.close(fig)

    Notes:
        The Arrhenius equation: rate = A * exp(-Q/RT)
        Linear form: ln(rate) = ln(A) - Q/R * (1/T)
        Slope = -Q/R, where Q is activation energy, R is gas constant
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate input
    if len(temperatures) != len(swelling_rates):
        raise ValueError(f"temperatures and swelling_rates must have same length: "
                        f"{len(temperatures)} != {len(swelling_rates)}")

    # Filter out non-positive values
    valid_mask = (swelling_rates > 0) & (temperatures > 0)
    temps_valid = temperatures[valid_mask]
    rates_valid = swelling_rates[valid_mask]

    if len(temps_valid) < 2:
        raise ValueError("Need at least 2 valid data points for Arrhenius plot")

    # Calculate Arrhenius coordinates
    inv_T = 1000 / temps_valid  # 1000/T for better readability
    ln_rate = np.log(rates_valid)

    # Fit line to estimate activation energy
    R = 8.314  # Gas constant in J/(mol·K)
    coeffs = np.polyfit(inv_T, ln_rate, 1)
    slope = coeffs[0]
    Q_estimate = -slope * R / 1000  # Activation energy in kJ/mol

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot settings
    color = kwargs.get('color', 'red')
    linewidth = kwargs.get('linewidth', 2.0)
    marker = kwargs.get('marker', 'o')
    markersize = kwargs.get('markersize', 8)

    # Plot data
    ax.plot(inv_T, ln_rate,
            marker=marker,
            linestyle='None',
            color=color,
            markersize=markersize,
            label='Data')

    # Plot fit line
    inv_T_fit = np.linspace(inv_T.min(), inv_T.max(), 100)
    ln_rate_fit = np.polyval(coeffs, inv_T_fit)
    ax.plot(inv_T_fit, ln_rate_fit,
            linestyle='--',
            color='black',
            linewidth=1.5,
            label='Linear Fit')

    # Styling
    ax.set_xlabel('1000/T (K⁻¹)')
    ax.set_ylabel('ln(Swelling Rate)')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend()

    # Title with activation energy
    if show_activation_energy:
        ax.set_title(f'Arrhenius Plot (Q ≈ {Q_estimate:.1f} kJ/mol)')
    else:
        ax.set_title('Arrhenius Plot')

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
