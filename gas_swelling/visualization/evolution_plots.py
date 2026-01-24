"""
Evolution Plots Module

Provides time-series plotting functions for gas swelling simulation results.
This module implements functions to visualize the evolution of key variables
over time, including swelling, bubble radius, gas pressure, and more.

Functions:
    plot_swelling_evolution: Plot swelling rate vs time/burnup
    plot_bubble_radius_evolution: Plot bubble radius (Rcb, Rcf) vs time
    plot_gas_concentration_evolution: Plot gas concentration (Cgb, Cgf) vs time
    plot_bubble_concentration_evolution: Plot bubble concentration vs time
    plot_gas_atoms_evolution: Plot gas atoms per bubble (Ncb, Ncf) vs time
    plot_gas_pressure_evolution: Plot gas pressure (Pg_b, Pg_f) vs time
    plot_defect_concentration_evolution: Plot vacancy and interstitial concentrations
    plot_released_gas_evolution: Plot released gas vs time
    plot_multi_panel_evolution: Create comprehensive multi-panel evolution plot

Examples:
    >>> from gas_swelling.visualization.evolution_plots import plot_swelling_evolution
    >>> result = model.solve(...)
    >>> fig = plot_swelling_evolution(result, save_path='swelling.png')
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


def plot_swelling_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot swelling rate evolution over time or burnup.

    Creates a publication-quality plot showing the swelling rate percentage
    as a function of time or burnup. The swelling rate is calculated from
    the bubble volume fraction.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Rcb': Bulk bubble radius (m)
               - 'Rcf': Interface bubble radius (m)
               - 'Ccb': Bulk bubble concentration (cavities/m³)
               - 'Ccf': Interface bubble concentration (cavities/m³)
        params: Optional dictionary of simulation parameters (for burnup calculation)
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs (color, linewidth, etc.)

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing from result

    Examples:
        >>> fig = plot_swelling_evolution(
        ...     result, params,
        ...     time_unit='hours',
        ...     save_path='swelling_evolution.png'
        ... )
        >>> plt.close(fig)

    Notes:
        Swelling rate is calculated as:
        V_bubble = (4/3) * π * R³ * Cc
        Swelling (%) = (V_bubble_bulk + V_bubble_interface) * 100
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Calculate swelling rate
    Rcb = result['Rcb']
    Rcf = result['Rcf']
    Ccb = result['Ccb']
    Ccf = result['Ccf']

    V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
    V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
    total_V_bubble = V_bubble_b + V_bubble_f
    swelling = total_V_bubble * 100  # Convert to percentage

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot swelling
    color = kwargs.get('color', 'red')
    linewidth = kwargs.get('linewidth', 2.0)
    ax.plot(x_data, swelling, color=color, linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Swelling Rate (%)')
    ax.set_title('Swelling Rate Evolution')
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


def plot_bubble_radius_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    length_unit: str = 'nm',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot bubble radius evolution over time or burnup.

    Creates a plot showing the evolution of bubble radius for both
    bulk (Rcb) and interface (Rcf) bubbles.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Rcb': Bulk bubble radius (m)
               - 'Rcf': Interface bubble radius (m)
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        length_unit: Unit for radius ('m', 'mm', 'um', 'nm')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_bubble_radius_evolution(
        ...     result, params,
        ...     time_unit='hours',
        ...     length_unit='nm',
        ...     save_path='radius_evolution.png'
        ... )
        >>> plt.close(fig)
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Rcb', 'Rcf']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Convert radius to desired unit
    Rcb = convert_length_units(result['Rcb'], length_unit)
    Rcf = convert_length_units(result['Rcf'], length_unit)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot radii
    linewidth = kwargs.get('linewidth', 2.0)
    ax.plot(x_data, Rcb, label='Bulk Bubble',
            color=colors[0], linewidth=linewidth)
    ax.plot(x_data, Rcf, label='Interface Bubble',
            color=colors[1], linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f'Bubble Radius ({length_unit})')
    ax.set_title('Bubble Radius Evolution')
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


def plot_gas_concentration_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot gas concentration evolution over time or burnup.

    Creates a plot showing the evolution of gas atom concentration
    in both bulk (Cgb) and interface (Cgf) regions.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Cgb': Bulk gas concentration (atoms/m³)
               - 'Cgf': Interface gas concentration (atoms/m³)
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_gas_concentration_evolution(
        ...     result, params,
        ...     save_path='gas_concentration.png'
        ... )
        >>> plt.close(fig)
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Cgb', 'Cgf']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot gas concentrations
    linewidth = kwargs.get('linewidth', 2.0)
    ax.plot(x_data, result['Cgb'], label='Bulk Gas',
            color=colors[0], linewidth=linewidth)
    ax.plot(x_data, result['Cgf'], label='Interface Gas',
            color=colors[1], linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Gas Concentration (atoms/m³)')
    ax.set_title('Gas Concentration Evolution')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

    # Use scientific notation if values are very large
    max_conc = max(np.max(result['Cgb']), np.max(result['Cgf']))
    if max_conc > 1e20:
        format_axis_scientific(ax, axis='y')

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


def plot_bubble_concentration_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot bubble concentration evolution over time or burnup.

    Creates a plot showing the evolution of bubble cavity concentration
    in both bulk (Ccb) and interface (Ccf) regions.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Ccb': Bulk bubble concentration (cavities/m³)
               - 'Ccf': Interface bubble concentration (cavities/m³)
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_bubble_concentration_evolution(
        ...     result, params,
        ...     save_path='bubble_concentration.png'
        ... )
        >>> plt.close(fig)
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Ccb', 'Ccf']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot bubble concentrations
    linewidth = kwargs.get('linewidth', 2.0)
    ax.plot(x_data, result['Ccb'], label='Bulk Bubbles',
            color=colors[0], linewidth=linewidth)
    ax.plot(x_data, result['Ccf'], label='Interface Bubbles',
            color=colors[1], linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Bubble Concentration (cavities/m³)')
    ax.set_title('Bubble Concentration Evolution')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

    # Use scientific notation if values are very large
    max_conc = max(np.max(result['Ccb']), np.max(result['Ccf']))
    if max_conc > 1e20:
        format_axis_scientific(ax, axis='y')

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


def plot_gas_atoms_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot gas atoms per bubble evolution over time or burnup.

    Creates a semilog plot showing the evolution of gas atoms per cavity
    for both bulk (Ncb) and interface (Ncf) bubbles.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Ncb': Gas atoms per bulk bubble
               - 'Ncf': Gas atoms per interface bubble
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_gas_atoms_evolution(
        ...     result, params,
        ...     save_path='gas_atoms.png'
        ... )
        >>> plt.close(fig)

    Notes:
        Uses semilog y-axis because Ncb and Ncf can vary over orders of magnitude.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Ncb', 'Ncf']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot gas atoms per bubble (semilog)
    linewidth = kwargs.get('linewidth', 2.0)
    ax.semilogy(x_data, result['Ncb'], label='Gas Atoms in Bulk Bubble',
                color=colors[0], linewidth=linewidth)
    ax.semilogy(x_data, result['Ncf'], label='Gas Atoms in Interface Bubble',
                color=colors[1], linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Gas Atoms (atoms/cavity)')
    ax.set_title('Gas Atoms per Bubble')
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


def plot_gas_pressure_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    pressure_unit: str = 'Pa',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot gas pressure evolution over time or burnup.

    Creates a plot showing the evolution of gas pressure inside bubbles
    for both bulk (Pg_b) and interface (Pg_f) bubbles.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'Pg_b': Bulk bubble gas pressure (Pa)
               - 'Pg_f': Interface bubble gas pressure (Pa)
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        pressure_unit: Unit for pressure ('Pa', 'kPa', 'MPa', 'GPa')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Raises:
        ValueError: If required keys are missing from result

    Examples:
        >>> fig = plot_gas_pressure_evolution(
        ...     result, params,
        ...     time_unit='hours',
        ...     pressure_unit='MPa',
        ...     save_path='gas_pressure.png'
        ... )
        >>> plt.close(fig)

    Notes:
        Gas pressure is calculated from the Virial equation of state based on
        the number of gas atoms per bubble and the bubble radius.
        Pressure can vary over several orders of magnitude.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Pg_b', 'Pg_f']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Convert pressure to desired unit
    Pg_b = result['Pg_b']
    Pg_f = result['Pg_f']

    # Pressure unit conversion factors
    pressure_conversions = {
        'Pa': 1.0,
        'kPa': 1e-3,
        'MPa': 1e-6,
        'GPa': 1e-9
    }

    if pressure_unit not in pressure_conversions:
        raise ValueError(f"Unsupported pressure unit: {pressure_unit}. "
                        f"Supported units: {list(pressure_conversions.keys())}")

    scale = pressure_conversions[pressure_unit]
    Pg_b_scaled = Pg_b * scale
    Pg_f_scaled = Pg_f * scale

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot gas pressure
    linewidth = kwargs.get('linewidth', 2.0)
    ax.plot(x_data, Pg_b_scaled, label='Bulk Bubble Pressure',
            color=colors[0], linewidth=linewidth)
    ax.plot(x_data, Pg_f_scaled, label='Interface Bubble Pressure',
            color=colors[1], linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f'Gas Pressure ({pressure_unit})')
    ax.set_title('Gas Pressure Evolution')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)

    # Use scientific notation if values are large
    if np.max(Pg_b_scaled) > 1000 or np.max(Pg_f_scaled) > 1000:
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

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


def plot_defect_concentration_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    defect_type: str = 'both',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot defect concentration evolution over time or burnup.

    Creates semilog plots showing the evolution of vacancy and/or
    interstitial concentrations in bulk and interface regions.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'cvb': Bulk vacancy concentration
               - 'cvf': Interface vacancy concentration
               - 'cib': Bulk interstitial concentration
               - 'cif': Interface interstitial concentration
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        defect_type: Type of defect to plot ('vacancy', 'interstitial', 'both')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_defect_concentration_evolution(
        ...     result, params,
        ...     defect_type='both',
        ...     save_path='defect_concentration.png'
        ... )
        >>> plt.close(fig)

    Notes:
        - Uses semilog y-axis because defect concentrations vary over orders of magnitude
        - When defect_type='both', creates two subplots side by side
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'cvb', 'cvf', 'cib', 'cif']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Create figure
    if defect_type == 'both':
        fig, axes = plt.subplots(1, 2, figsize=(figsize[0]*2, figsize[1]))
    else:
        fig, ax = plt.subplots(figsize=figsize)
        axes = [ax]

    linewidth = kwargs.get('linewidth', 2.0)

    # Plot vacancy concentrations
    if defect_type in ['vacancy', 'both']:
        ax = axes[0] if defect_type == 'both' else axes[0]
        ax.semilogy(x_data, result['cvb'], label='Bulk Vacancy',
                    color=colors[0], linewidth=linewidth)
        ax.semilogy(x_data, result['cvf'], label='Interface Vacancy',
                    color=colors[1], linewidth=linewidth)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Vacancy Concentration')
        ax.set_title('Vacancy Concentration Evolution')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)

    # Plot interstitial concentrations
    if defect_type in ['interstitial', 'both']:
        ax = axes[1] if defect_type == 'both' else axes[0]
        ax.semilogy(x_data, result['cib'], label='Bulk Interstitial',
                    color=colors[0], linewidth=linewidth)
        ax.semilogy(x_data, result['cif'], label='Interface Interstitial',
                    color=colors[1], linewidth=linewidth)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Interstitial Concentration')
        ax.set_title('Interstitial Concentration Evolution')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)

    # Set axis limits if provided
    if 'xlim' in kwargs:
        for ax in axes:
            ax.set_xlim(kwargs['xlim'])
    if 'ylim' in kwargs:
        for ax in axes:
            ax.set_ylim(kwargs['ylim'])

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig


def plot_released_gas_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (10, 6),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Plot released gas evolution over time or burnup.

    Creates a plot showing the cumulative amount of gas released
    from the fuel matrix over time.

    Args:
        result: Dictionary containing simulation results with keys:
               - 'time': Time array (seconds)
               - 'released_gas': Released gas (atoms/m³)
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_released_gas_evolution(
        ...     result, params,
        ...     save_path='released_gas.png'
        ... )
        >>> plt.close(fig)
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'released_gas']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot released gas
    color = kwargs.get('color', 'purple')
    linewidth = kwargs.get('linewidth', 2.0)
    ax.plot(x_data, result['released_gas'], color=color, linewidth=linewidth)

    # Styling
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Released Gas (atoms/m³)')
    ax.set_title('Released Gas Evolution')
    ax.grid(True, linestyle='--', alpha=0.3)

    # Use scientific notation if values are very large
    if np.max(result['released_gas']) > 1e20:
        format_axis_scientific(ax, axis='y')

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


def plot_multi_panel_evolution(
    result: Dict[str, np.ndarray],
    params: Optional[Dict[str, Any]] = None,
    time_unit: str = 'minutes',
    length_unit: str = 'nm',
    use_burnup: bool = False,
    save_path: Optional[str] = None,
    dpi: int = 300,
    figsize: Tuple[float, float] = (30, 10),
    style: str = 'default',
    **kwargs
) -> plt.Figure:
    """
    Create a comprehensive multi-panel evolution plot.

    Creates a 2x4 subplot grid showing all key variables from the simulation:
    - Bubble radius (Rcb, Rcf)
    - Swelling rate
    - Gas concentration (Cgb, Cgf)
    - Bubble concentration (Ccb, Ccf)
    - Gas atoms per bubble (Ncb, Ncf)
    - Vacancy concentration (cvb, cvf)
    - Interstitial concentration (cib, cif)
    - Released gas

    Args:
        result: Dictionary containing simulation results with all standard keys
        params: Optional dictionary of simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        length_unit: Unit for length ('m', 'mm', 'um', 'nm')
        use_burnup: If True, use burnup (%FIMA) instead of time for x-axis
        save_path: Optional path to save the figure
        dpi: Resolution in dots per inch for saved figure
        figsize: Figure size (width, height) in inches
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')
        **kwargs: Additional matplotlib kwargs

    Returns:
        Matplotlib figure object

    Examples:
        >>> fig = plot_multi_panel_evolution(
        ...     result, params,
        ...     time_unit='hours',
        ...     save_path='multi_panel.png'
        ... )
        >>> plt.close(fig)

    Notes:
        This function creates the same layout as the plot_results function
        in test4_run_rk23.py, providing a comprehensive overview of all
        key simulation variables.
    """
    # Apply publication style
    apply_publication_style(style)

    # Validate required keys
    required_keys = ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf', 'Cgb', 'Cgf',
                    'Ncb', 'Ncf', 'cvb', 'cvf', 'cib', 'cif', 'released_gas']
    validate_result_data(result, required_keys)

    # Calculate time/burnup data
    time_seconds = result['time']
    if use_burnup and params is not None:
        fission_rate = params.get('fission_rate', 5e19)
        x_data = calculate_burnup(time_seconds, fission_rate)
        xlabel = VARIABLE_LABELS['burnup']
    else:
        x_data = convert_time_units(time_seconds, time_unit)
        xlabel = get_time_unit_label(time_unit)

    # Create figure grid
    fig, axes = create_figure_grid(2, 4, figsize=figsize, style=style)

    # Get color palette
    colors = get_color_palette('bulk_interface')

    # Calculate derived quantities
    Rcb = convert_length_units(result['Rcb'], length_unit)
    Rcf = convert_length_units(result['Rcf'], length_unit)
    V_bubble_b = (4.0 / 3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0 / 3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    linewidth = kwargs.get('linewidth', 2.0)

    # Plot 1: Bubble radius
    axes[0, 0].plot(x_data, Rcb, label='Bulk Bubble',
                    color=colors[0], linewidth=linewidth)
    axes[0, 0].plot(x_data, Rcf, label='Interface Bubble',
                    color=colors[1], linewidth=linewidth)
    axes[0, 0].set_xlabel(xlabel)
    axes[0, 0].set_ylabel(f'Bubble Radius ({length_unit})')
    axes[0, 0].set_title('Bubble Radius Evolution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Plot 2: Swelling rate
    axes[0, 1].plot(x_data, swelling, color='red', linewidth=linewidth)
    axes[0, 1].set_xlabel(xlabel)
    axes[0, 1].set_ylabel('Swelling Rate (%)')
    axes[0, 1].set_title('Swelling Rate Evolution')
    axes[0, 1].grid(True, alpha=0.3)

    # Plot 3: Gas concentration
    axes[1, 0].plot(x_data, result['Cgb'], label='Bulk Gas',
                    color=colors[0], linewidth=linewidth)
    axes[1, 0].plot(x_data, result['Cgf'], label='Interface Gas',
                    color=colors[1], linewidth=linewidth)
    axes[1, 0].set_xlabel(xlabel)
    axes[1, 0].set_ylabel('Gas Concentration (atoms/m³)')
    axes[1, 0].set_title('Gas Concentration Evolution')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Plot 4: Bubble concentration
    axes[1, 1].plot(x_data, result['Ccb'], label='Bulk Bubbles',
                    color=colors[0], linewidth=linewidth)
    axes[1, 1].plot(x_data, result['Ccf'], label='Interface Bubbles',
                    color=colors[1], linewidth=linewidth)
    axes[1, 1].set_xlabel(xlabel)
    axes[1, 1].set_ylabel('Bubble Concentration (cavities/m³)')
    axes[1, 1].set_title('Bubble Concentration Evolution')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    # Plot 5: Gas atoms per bubble (semilog)
    axes[0, 2].semilogy(x_data, result['Ncb'], label='Gas Atoms in Bulk Bubble',
                        color=colors[0], linewidth=linewidth)
    axes[0, 2].semilogy(x_data, result['Ncf'], label='Gas Atoms in Interface Bubble',
                        color=colors[1], linewidth=linewidth)
    axes[0, 2].set_xlabel(xlabel)
    axes[0, 2].set_ylabel('Gas Atoms (atoms/cavity)')
    axes[0, 2].set_title('Gas Atoms per Bubble')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    # Plot 6: Vacancy concentration (semilog)
    axes[0, 3].semilogy(x_data, result['cvb'], label='Bulk Vacancy',
                        color=colors[0], linewidth=linewidth)
    axes[0, 3].semilogy(x_data, result['cvf'], label='Interface Vacancy',
                        color=colors[1], linewidth=linewidth)
    axes[0, 3].set_xlabel(xlabel)
    axes[0, 3].set_ylabel('Vacancy Concentration')
    axes[0, 3].set_title('Vacancy Concentration Evolution')
    axes[0, 3].legend()
    axes[0, 3].grid(True, alpha=0.3)

    # Plot 7: Interstitial concentration (semilog)
    axes[1, 2].semilogy(x_data, result['cib'], label='Bulk Interstitial',
                        color=colors[0], linewidth=linewidth)
    axes[1, 2].semilogy(x_data, result['cif'], label='Interface Interstitial',
                        color=colors[1], linewidth=linewidth)
    axes[1, 2].set_xlabel(xlabel)
    axes[1, 2].set_ylabel('Interstitial Concentration')
    axes[1, 2].set_title('Interstitial Concentration Evolution')
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)

    # Plot 8: Released gas
    axes[1, 3].plot(x_data, result['released_gas'],
                    color='purple', linewidth=linewidth)
    axes[1, 3].set_xlabel(xlabel)
    axes[1, 3].set_ylabel('Released Gas (atoms/m³)')
    axes[1, 3].set_title('Released Gas Evolution')
    axes[1, 3].grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    if save_path:
        save_figure(fig, save_path, dpi=dpi, close=False)

    return fig
