"""
Visualization Utilities Module

Provides style configuration, helper functions, and utilities for creating
publication-quality visualizations of gas swelling simulation results.

This module includes:
- Publication-quality matplotlib style configuration
- Figure saving utilities with multiple format support
- Unit conversion functions
- Common plot formatting helpers
- Color schemes and styling presets
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Union
import warnings
from scipy import stats


def get_publication_style(style: str = 'default') -> Dict[str, Any]:
    """
    Get publication-quality matplotlib style configuration.

    Args:
        style: Style preset name ('default', 'presentation', 'poster', 'grayscale')

    Returns:
        Dictionary of matplotlib rcParams

    Examples:
        >>> style = get_publication_style()
        >>> plt.rcParams.update(style)

    Notes:
        Style configurations are optimized for scientific publications:
        - High DPI (300) for figure saving
        - Clear, readable fonts
        - Professional color schemes
        - Proper figure sizing
    """
    styles = {
        'default': {
            # Figure settings
            'figure.figsize': (10, 6),
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1,

            # Font settings
            'font.family': 'serif',
            'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'sans-serif'],
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 11,
            'ytick.labelsize': 11,
            'legend.fontsize': 11,

            # Line settings
            'lines.linewidth': 2.0,
            'lines.markersize': 8,
            'lines.markeredgewidth': 1.5,

            # Axes settings
            'axes.linewidth': 1.5,
            'axes.grid': True,
            'axes.grid.which': 'major',
            'axes.facecolor': 'white',
            'axes.edgecolor': 'black',
            'axes.unicode_minus': False,

            # Tick settings
            'xtick.major.width': 1.5,
            'ytick.major.width': 1.5,
            'xtick.minor.width': 1.0,
            'ytick.minor.width': 1.0,
            'xtick.major.size': 6,
            'ytick.major.size': 6,
            'xtick.minor.size': 4,
            'ytick.minor.size': 4,
            'xtick.direction': 'in',
            'ytick.direction': 'in',

            # Legend settings
            'legend.frameon': True,
            'legend.framealpha': 0.9,
            'legend.edgecolor': 'gray',
            'legend.fancybox': False,

            # Grid settings
            'grid.alpha': 0.3,
            'grid.linestyle': '--',
            'grid.linewidth': 0.8,
        },

        'presentation': {
            'figure.figsize': (12, 7),
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'font.family': 'sans-serif',
            'font.size': 14,
            'axes.titlesize': 16,
            'axes.labelsize': 14,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'legend.fontsize': 12,
            'lines.linewidth': 2.5,
            'lines.markersize': 10,
            'axes.linewidth': 2.0,
            'axes.grid': True,
            'grid.alpha': 0.4,
        },

        'poster': {
            'figure.figsize': (16, 10),
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'font.family': 'sans-serif',
            'font.size': 18,
            'axes.titlesize': 20,
            'axes.labelsize': 18,
            'xtick.labelsize': 16,
            'ytick.labelsize': 16,
            'legend.fontsize': 16,
            'lines.linewidth': 3.0,
            'lines.markersize': 12,
            'axes.linewidth': 2.5,
            'axes.grid': True,
            'grid.alpha': 0.4,
        },

        'grayscale': {
            'figure.figsize': (10, 6),
            'figure.dpi': 100,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'font.family': 'serif',
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'lines.linewidth': 2.0,
            'axes.linewidth': 1.5,
            'axes.grid': True,
            'axes.prop_cycle': plt.cycler('color', ['black', 'gray', 'silver', 'dimgray']),
        }
    }

    return styles.get(style, styles['default'])


def apply_publication_style(style: str = 'default') -> None:
    """
    Apply publication-quality style to matplotlib.

    Args:
        style: Style preset name ('default', 'presentation', 'poster', 'grayscale')

    Examples:
        >>> apply_publication_style()
        >>> plt.plot(x, y)
        >>> plt.savefig('figure.pdf')
    """
    style_dict = get_publication_style(style)
    plt.rcParams.update(style_dict)


def get_color_palette(name: str = 'default') -> List[str]:
    """
    Get color palette for plotting.

    Args:
        name: Color palette name ('default', 'viridis', 'plasma', 'bulk_interface',
              'temperature', 'grayscale')

    Returns:
        List of color hex codes or names

    Examples:
        >>> colors = get_color_palette('bulk_interface')
        >>> plt.plot(x1, y1, color=colors[0], label='Bulk')
        >>> plt.plot(x2, y2, color=colors[1], label='Interface')
    """
    palettes = {
        'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                   '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],

        'bulk_interface': ['#1f77b4', '#ff7f0e'],  # Blue for bulk, orange for interface

        'temperature': ['#d62728', '#ff7f0e', '#ffd700', '#2ca02c', '#1f77b4',
                       '#9467bd'],  # Red (hot) to blue (cold)

        'grayscale': ['#000000', '#404040', '#808080', '#a0a0a0', '#c0c0c0'],

        'viridis': ['#440154', '#482878', '#3e4a89', '#31688e', '#26838f',
                   '#1f9d8a', '#35b779', '#6dcd59', '#b4de2c', '#fde725'],

        'plasma': ['#0d0887', '#46039f', '#7201a8', '#9c179e', '#bd3786',
                  '#d8576b', '#ed7953', '#fb9f3a', '#fdca26', '#f0f921'],
    }

    return palettes.get(name, palettes['default'])


def save_figure(fig: plt.Figure,
               filepath: str,
               format: Optional[str] = None,
               dpi: int = 300,
               close: bool = True) -> None:
    """
    Save figure to file with publication-quality settings.

    Args:
        fig: Matplotlib figure object
        filepath: Output file path (extension determines format if not specified)
        format: File format ('png', 'pdf', 'svg', 'eps', 'ps', 'tiff')
        dpi: Resolution in dots per inch (default 300 for publication quality)
        close: Whether to close the figure after saving (default True)

    Raises:
        ValueError: If format is not supported

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(x, y)
        >>> save_figure(fig, 'results/figure.pdf')
        >>> save_figure(fig, 'results/figure.png', dpi=600)

    Notes:
        Supported formats: PNG, PDF, SVG, EPS, PS, TIFF
        PDF and SVG are recommended for publications (vector graphics)
        PNG is recommended for presentations and web (raster graphics)
    """
    filepath = Path(filepath)

    # Auto-detect format from extension if not specified
    if format is None:
        format = filepath.suffix.lstrip('.').lower()

    # Validate format
    supported_formats = ['png', 'pdf', 'svg', 'eps', 'ps', 'tiff']
    if format not in supported_formats:
        raise ValueError(f"Unsupported format '{format}'. "
                        f"Supported formats: {', '.join(supported_formats)}")

    # Create directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Save figure
    try:
        fig.savefig(
            filepath,
            format=format,
            dpi=dpi,
            bbox_inches='tight',
            pad_inches=0.1,
            facecolor='white',
            edgecolor='none'
        )
    except Exception as e:
        raise IOError(f"Failed to save figure to {filepath}: {str(e)}")

    if close:
        plt.close(fig)


def convert_time_units(time_seconds: np.ndarray,
                       target_unit: str = 'minutes') -> np.ndarray:
    """
    Convert time from seconds to specified unit.

    Args:
        time_seconds: Time values in seconds
        target_unit: Target unit ('seconds', 'minutes', 'hours', 'days')

    Returns:
        Time values in target unit

    Examples:
        >>> time_sec = np.array([0, 60, 3600, 86400])
        >>> convert_time_units(time_sec, 'minutes')
        array([0., 1., 60., 1440.])
        >>> convert_time_units(time_sec, 'days')
        array([0., 0.00069444, 0.04166667, 1.])
    """
    conversions = {
        'seconds': 1.0,
        'minutes': 1.0 / 60.0,
        'hours': 1.0 / 3600.0,
        'days': 1.0 / 86400.0,
    }

    if target_unit not in conversions:
        raise ValueError(f"Unsupported unit '{target_unit}'. "
                        f"Supported units: {', '.join(conversions.keys())}")

    return time_seconds * conversions[target_unit]


def convert_length_units(length_meters: np.ndarray,
                        target_unit: str = 'nm') -> np.ndarray:
    """
    Convert length from meters to specified unit.

    Args:
        length_meters: Length values in meters
        target_unit: Target unit ('m', 'mm', 'um', 'nm', 'A')

    Returns:
        Length values in target unit

    Examples:
        >>> length = np.array([1e-9, 1e-6, 1e-3])
        >>> convert_length_units(length, 'nm')
        array([1., 1000., 1000000.])
        >>> convert_length_units(length, 'um')
        array([0.001, 1., 1000.])
    """
    conversions = {
        'm': 1.0,
        'mm': 1e3,
        'um': 1e6,
        'nm': 1e9,
        'A': 1e10,  # Angstroms
    }

    if target_unit not in conversions:
        raise ValueError(f"Unsupported unit '{target_unit}'. "
                        f"Supported units: {', '.join(conversions.keys())}")

    return length_meters * conversions[target_unit]


def calculate_burnup(time_seconds: np.ndarray,
                    fission_rate: float,
                    conversion_factor: float = 0.9 / 4176980) -> np.ndarray:
    """
    Convert simulation time to burnup (% FIMA).

    Args:
        time_seconds: Time values in seconds
        fission_rate: Fission rate (fissions/m³/s)
        conversion_factor: Conversion factor (default based on U-10Zr fuel)

    Returns:
        Burnup values in % FIMA (Fissions per Initial Metal Atom)

    Examples:
        >>> time = np.array([0, 3600, 7200])
        >>> burnup = calculate_burnup(time, fission_rate=5e19)
        >>> # Returns burnup in % FIMA

    Notes:
        The default conversion factor is based on U-10Zr fuel density.
        Adjust for different fuel compositions.
    """
    # Convert time to minutes first
    time_minutes = time_seconds / 60.0

    # Calculate burnup
    burnup = conversion_factor * time_minutes * 60

    return burnup


def format_axis_scientific(ax: plt.Axes,
                           axis: str = 'both',
                           limit_precision: int = 1) -> None:
    """
    Format axis tick labels in scientific notation.

    Args:
        ax: Matplotlib axes object
        axis: Which axis to format ('x', 'y', 'both')
        limit_precision: Number of decimal places

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(x, y)
        >>> format_axis_scientific(ax, 'y')
    """
    if axis in ['x', 'both']:
        ax.ticklabel_format(axis='x', style='scientific', scilimits=(-3, 4))
    if axis in ['y', 'both']:
        ax.ticklabel_format(axis='y', style='scientific', scilimits=(-3, 4))


def set_axis_limits(ax: plt.Axes,
                   xlim: Optional[Tuple[float, float]] = None,
                   ylim: Optional[Tuple[float, float]] = None,
                   padding: float = 0.05) -> None:
    """
    Set axis limits with optional padding.

    Args:
        ax: Matplotlib axes object
        xlim: X-axis limits (min, max)
        ylim: Y-axis limits (min, max)
        padding: Fraction to pad limits if not specified (default 0.05 = 5%)

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(x, y)
        >>> set_axis_limits(ax, xlim=(0, 100), padding=0.1)
    """
    if xlim is not None:
        ax.set_xlim(xlim)
    else:
        xlim = ax.get_xlim()
        x_range = xlim[1] - xlim[0]
        ax.set_xlim(xlim[0] - padding * x_range, xlim[1] + padding * x_range)

    if ylim is not None:
        ax.set_ylim(ylim)
    else:
        ylim = ax.get_ylim()
        y_range = ylim[1] - ylim[0]
        ax.set_ylim(ylim[0] - padding * y_range, ylim[1] + padding * y_range)


def create_figure_grid(n_rows: int,
                      n_cols: int,
                      figsize: Optional[Tuple[float, float]] = None,
                      style: str = 'default') -> Tuple[plt.Figure, np.ndarray]:
    """
    Create a figure grid with publication-quality styling.

    Args:
        n_rows: Number of rows in the grid
        n_cols: Number of columns in the grid
        figsize: Figure size (width, height) in inches
        style: Style preset name

    Returns:
        Tuple of (figure, axes_array)

    Examples:
        >>> fig, axes = create_figure_grid(2, 2)
        >>> axes[0, 0].plot(x, y)
        >>> plt.savefig('grid_plot.pdf')
    """
    # Apply style
    apply_publication_style(style)

    # Calculate default figure size if not specified
    if figsize is None:
        # Base size: 10 inches for single column, scale with grid
        width = 5 * n_cols
        height = 4 * n_rows
        figsize = (width, height)

    # Create figure and axes
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)

    # Ensure axes is always 2D array
    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1 or n_cols == 1:
        axes = axes.reshape(n_rows, n_cols)

    return fig, axes


def add_subfigure_labels(fig: plt.Figure,
                         axes_array: np.ndarray,
                         label_format: str = '({})',
                         offset_x: float = -0.1,
                         offset_y: float = 1.05) -> None:
    """
    Add labels (a, b, c, ...) to subfigures for publications.

    Args:
        fig: Matplotlib figure object
        axes_array: Array of axes objects
        label_format: Format string for labels (default '({})' -> (a), (b), etc.)
        offset_x: X offset relative to axes (default -0.1)
        offset_y: Y offset relative to axes (default 1.05)

    Examples:
        >>> fig, axes = create_figure_grid(2, 2)
        >>> add_subfigure_labels(fig, axes)
    """
    labels = 'abcdefghijklmnopqrstuvwxyz'

    for i, ax in enumerate(axes_array.flat):
        if i < len(labels):
            ax.text(offset_x, offset_y, label_format.format(labels[i]),
                   transform=ax.transAxes,
                   fontsize=14, fontweight='bold',
                   verticalalignment='bottom',
                   horizontalalignment='right')


def validate_result_data(result: Dict[str, np.ndarray],
                        required_keys: List[str]) -> None:
    """
    Validate that simulation result contains required data keys.

    Args:
        result: Result dictionary from model.solve()
        required_keys: List of required keys

    Raises:
        ValueError: If required keys are missing

    Examples:
        >>> validate_result_data(result, ['time', 'Rcb', 'Rcf', 'swelling'])
    """
    missing_keys = [key for key in required_keys if key not in result]

    if missing_keys:
        raise ValueError(f"Missing required keys in result data: {missing_keys}")


def get_time_unit_label(unit: str) -> str:
    """
    Get formatted label for time unit.

    Args:
        unit: Time unit ('seconds', 'minutes', 'hours', 'days')

    Returns:
        Formatted label string

    Examples:
        >>> get_time_unit_label('minutes')
        'Time (min)'
        >>> get_time_unit_label('hours')
        'Time (h)'
    """
    labels = {
        'seconds': 'Time (s)',
        'minutes': 'Time (min)',
        'hours': 'Time (h)',
        'days': 'Time (days)',
    }

    return labels.get(unit, 'Time')


def get_length_unit_label(unit: str) -> str:
    """
    Get formatted label for length unit.

    Args:
        unit: Length unit ('m', 'mm', 'um', 'nm', 'A')

    Returns:
        Formatted label string

    Examples:
        >>> get_length_unit_label('nm')
        'Length (nm)'
        >>> get_length_unit_label('um')
        'Length (μm)'
    """
    labels = {
        'm': 'Length (m)',
        'mm': 'Length (mm)',
        'um': 'Length (μm)',
        'nm': 'Length (nm)',
        'A': 'Length (Å)',
    }

    return labels.get(unit, 'Length')


def calculate_confidence_interval(data: Union[np.ndarray, List[np.ndarray]],
                                 confidence: float = 0.95,
                                 axis: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate confidence interval for data.

    Args:
        data: Input data array or list of arrays (multiple runs)
        confidence: Confidence level (default 0.95 for 95% confidence interval)
        axis: Axis along which to calculate statistics (default None for flattened array)

    Returns:
        Tuple of (mean, lower_bound, upper_bound) arrays

    Raises:
        ValueError: If data is empty or confidence is not in (0, 1)

    Examples:
        >>> data = np.random.randn(100, 10)  # 10 variables, 100 samples each
        >>> mean, lower, upper = calculate_confidence_interval(data, confidence=0.95)
        >>> # Or with list of runs
        >>> runs = [np.random.randn(50) for _ in range(5)]
        >>> mean, lower, upper = calculate_confidence_interval(runs, axis=0)

    Notes:
        Uses scipy.stats.sem for standard error calculation and t-distribution
        for confidence intervals. Suitable for small sample sizes.
        For large samples (n > 30), normal distribution would be similar.
    """
    # Convert list of arrays to single array if needed
    if isinstance(data, list):
        if len(data) == 0:
            raise ValueError("Data list is empty")
        data = np.array(data)

    # Validate confidence level
    if not 0 < confidence < 1:
        raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")

    # Calculate mean
    mean = np.mean(data, axis=axis)

    # Calculate standard error
    sem = stats.sem(data, axis=axis)

    # Calculate degrees of freedom
    if axis is None:
        n = data.size
    else:
        n = data.shape[axis]

    # Calculate t-value for confidence interval
    t_value = stats.t.ppf((1 + confidence) / 2, n - 1)

    # Calculate confidence interval
    margin_of_error = t_value * sem
    lower_bound = mean - margin_of_error
    upper_bound = mean + margin_of_error

    return mean, lower_bound, upper_bound


def extract_error_bands(results: List[Dict[str, np.ndarray]],
                        variable: str,
                        confidence: float = 0.95) -> Dict[str, np.ndarray]:
    """
    Extract error bands from multiple simulation runs for uncertainty visualization.

    Args:
        results: List of result dictionaries from model.solve() runs
        variable: Variable name to extract (e.g., 'swelling', 'Rcb', 'Rcf')
        confidence: Confidence level for error bands (default 0.95)

    Returns:
        Dictionary containing:
            - 'mean': Mean values across runs
            - 'lower': Lower confidence bound
            - 'upper': Upper confidence bound
            - 'std': Standard deviation across runs
            - 'time': Time points (assumed consistent across runs)

    Raises:
        ValueError: If results list is empty or variable not found in results

    Examples:
        >>> # Run multiple simulations with parameter variations
        >>> results = []
        >>> for temp in [700, 750, 800]:
        ...     model.set_temperature(temp)
        ...     result = model.solve(...)
        ...     results.append(result)
        >>> # Extract error bands for swelling
        >>> error_bands = extract_error_bands(results, 'swelling')
        >>> ax.fill_between(error_bands['time'],
        ...                 error_bands['lower'],
        ...                 error_bands['upper'],
        ...                 alpha=0.3, label='95% CI')

    Notes:
        - Assumes all results have the same time points
        - Uses calculate_confidence_interval internally
        - Suitable for parameter uncertainty studies
        - Can be used with plot_error_band function for visualization
    """
    # Validate inputs
    if not results:
        raise ValueError("Results list is empty")

    # Extract variable data from all runs
    data_arrays = []
    time_points = None

    for i, result in enumerate(results):
        if variable not in result:
            raise ValueError(f"Variable '{variable}' not found in result {i}")

        if 'time' not in result:
            raise ValueError(f"'time' not found in result {i}")

        # Check time points consistency
        if time_points is None:
            time_points = result['time']
        elif not np.allclose(time_points, result['time']):
            warnings.warn("Time points differ across runs. Using first run's time points.")

        data_arrays.append(result[variable])

    # Stack data arrays
    stacked_data = np.vstack(data_arrays)

    # Calculate confidence interval
    mean, lower, upper = calculate_confidence_interval(stacked_data, confidence=confidence, axis=0)

    # Calculate standard deviation
    std = np.std(stacked_data, axis=0)

    return {
        'mean': mean,
        'lower': lower,
        'upper': upper,
        'std': std,
        'time': time_points
    }


# Common variable names and labels for plotting
VARIABLE_LABELS = {
    'time': 'Time',
    'burnup': 'Burnup (%FIMA)',
    'Rcb': 'Bulk Bubble Radius',
    'Rcf': 'Interface Bubble Radius',
    'swelling': 'Swelling Rate',
    'Cgb': 'Bulk Gas Concentration',
    'Cgf': 'Interface Gas Concentration',
    'Ccb': 'Bulk Bubble Concentration',
    'Ccf': 'Interface Bubble Concentration',
    'Ncb': 'Gas Atoms per Bulk Bubble',
    'Ncf': 'Gas Atoms per Interface Bubble',
    'cvb': 'Bulk Vacancy Concentration',
    'cvf': 'Interface Vacancy Concentration',
    'cib': 'Bulk Interstitial Concentration',
    'cif': 'Interface Interstitial Concentration',
    'Pg_b': 'Bulk Bubble Pressure',
    'Pg_f': 'Interface Bubble Pressure',
    'released_gas': 'Released Gas',
}
