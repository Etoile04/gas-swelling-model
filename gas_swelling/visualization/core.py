"""
Core Plotting Module

Provides base classes and common functionality for all visualization tools.
This module defines the abstract base class for plotters and implements
shared plotting logic used across different visualization types.

Classes:
    GasSwellingPlotter: Base class for all gas swelling model plotters

Examples:
    >>> from gas_swelling.visualization.core import GasSwellingPlotter
    >>> plotter = GasSwellingPlotter()
    >>> plotter.load_result(result)
    >>> plotter.plot_all(save_path='results.png')
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from abc import ABC, abstractmethod
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


class GasSwellingPlotter(ABC):
    """
    Base class for all gas swelling model visualization plotters.

    This class provides common functionality for plotting simulation results,
    including data validation, unit conversions, figure styling, and saving.

    Attributes:
        result: Dictionary containing simulation results
        params: Dictionary containing simulation parameters
        time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
        length_unit: Unit for length axis ('m', 'mm', 'um', 'nm')
        use_burnup: Whether to use burnup instead of time for x-axis
        style: Matplotlib style preset ('default', 'presentation', 'poster', 'grayscale')

    Examples:
        >>> plotter = GasSwellingPlotter()
        >>> plotter.load_result(result_dict)
        >>> plotter.plot_all('results.png')

    Notes:
        Subclasses should implement the plot() method to define specific
        visualization logic while inheriting common functionality from this base class.
    """

    def __init__(self,
                 time_unit: str = 'minutes',
                 length_unit: str = 'nm',
                 use_burnup: bool = False,
                 style: str = 'default'):
        """
        Initialize the plotter with default settings.

        Args:
            time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
            length_unit: Unit for length axis ('m', 'mm', 'um', 'nm')
            use_burnup: Use burnup (%FIMA) instead of time for x-axis
            style: Matplotlib style preset name
        """
        self.result: Optional[Dict[str, np.ndarray]] = None
        self.params: Optional[Dict[str, Any]] = None
        self.time_unit = time_unit
        self.length_unit = length_unit
        self.use_burnup = use_burnup
        self.style = style

        # Apply global style
        apply_publication_style(style)

        # Color palette
        self.colors = get_color_palette('bulk_interface')

    def load_result(self,
                   result: Dict[str, np.ndarray],
                   params: Optional[Dict[str, Any]] = None) -> None:
        """
        Load simulation results for plotting.

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
                   - 'released_gas': Released gas (atoms/m³)
            params: Optional dictionary of simulation parameters

        Raises:
            ValueError: If required keys are missing from result

        Examples:
            >>> plotter.load_result(result, params)
        """
        # Validate required keys
        required_keys = ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf', 'Cgb', 'Cgf',
                        'Ncb', 'Ncf', 'cvb', 'cvf', 'cib', 'cif', 'released_gas']
        validate_result_data(result, required_keys)

        self.result = result
        self.params = params

    def get_time_data(self) -> np.ndarray:
        """
        Get time data in the configured unit.

        Returns:
            Time array in configured unit

        Examples:
            >>> time = plotter.get_time_data()
        """
        if self.result is None:
            raise ValueError("No result data loaded. Call load_result() first.")

        time_seconds = self.result['time']

        if self.use_burnup and self.params is not None:
            # Calculate burnup
            fission_rate = self.params.get('fission_rate', 5e19)
            return calculate_burnup(time_seconds, fission_rate)
        else:
            # Convert time units
            return convert_time_units(time_seconds, self.time_unit)

    def get_time_label(self) -> str:
        """
        Get label for time axis based on configuration.

        Returns:
            Formatted time axis label

        Examples:
            >>> label = plotter.get_time_label()
        """
        if self.use_burnup:
            return VARIABLE_LABELS['burnup']
        else:
            return get_time_unit_label(self.time_unit)

    def get_length_data(self, length_array: np.ndarray) -> np.ndarray:
        """
        Convert length data to configured unit.

        Args:
            length_array: Length values in meters

        Returns:
            Length values in configured unit

        Examples:
            >>> radius_nm = plotter.get_length_data(result['Rcb'])
        """
        return convert_length_units(length_array, self.length_unit)

    def get_length_label(self) -> str:
        """
        Get label for length axis based on configuration.

        Returns:
            Formatted length axis label

        Examples:
            >>> label = plotter.get_length_label()
        """
        return get_length_unit_label(self.length_unit)

    def calculate_swelling(self) -> np.ndarray:
        """
        Calculate swelling rate from bubble data.

        Returns:
            Swelling rate as percentage

        Examples:
            >>> swelling = plotter.calculate_swelling()
        """
        if self.result is None:
            raise ValueError("No result data loaded. Call load_result() first.")

        Rcb = self.result['Rcb']
        Rcf = self.result['Rcf']
        Ccb = self.result['Ccb']
        Ccf = self.result['Ccf']

        V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf
        total_V_bubble = V_bubble_b + V_bubble_f

        return total_V_bubble * 100  # Convert to percentage

    def create_standard_plot(self,
                           xlabel: str,
                           ylabel: str,
                           title: str,
                           figsize: Tuple[float, float] = (10, 6),
                           grid: bool = True,
                           legend: bool = True) -> Tuple[plt.Figure, plt.Axes]:
        """
        Create a standard single plot with consistent styling.

        Args:
            xlabel: X-axis label
            ylabel: Y-axis label
            title: Plot title
            figsize: Figure size (width, height) in inches
            grid: Whether to show grid
            legend: Whether to show legend

        Returns:
            Tuple of (figure, axes)

        Examples:
            >>> fig, ax = plotter.create_standard_plot(
            ...     'Time (min)', 'Swelling (%)', 'Swelling vs Time'
            ... )
            >>> ax.plot(time, swelling)
            >>> plt.savefig('swelling.png')
        """
        fig, ax = plt.subplots(figsize=figsize)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        if grid:
            ax.grid(True, linestyle='--', alpha=0.3)

        if legend:
            ax.legend()

        return fig, ax

    def plot_multiple_series(self,
                            ax: plt.Axes,
                            x_data: np.ndarray,
                            y_data_list: List[np.ndarray],
                            labels: List[str],
                            colors: Optional[List[str]] = None,
                            linewidths: Optional[List[float]] = None,
                            yscale: str = 'linear') -> None:
        """
        Plot multiple data series on the same axes.

        Args:
            ax: Matplotlib axes object
            x_data: X-axis data
            y_data_list: List of y-axis data arrays
            labels: List of legend labels
            colors: Optional list of colors
            linewidths: Optional list of line widths
            yscale: Y-axis scale ('linear' or 'log')

        Examples:
            >>> plotter.plot_multiple_series(
            ...     ax, time, [Rcb, Rcf],
            ...     ['Bulk', 'Interface'], yscale='linear'
            ... )
        """
        if colors is None:
            colors = self.colors

        if linewidths is None:
            linewidths = [2.0] * len(y_data_list)

        for y_data, label, color, lw in zip(y_data_list, labels, colors, linewidths):
            if yscale == 'log':
                ax.semilogy(x_data, y_data, label=label, color=color, linewidth=lw)
            else:
                ax.plot(x_data, y_data, label=label, color=color, linewidth=lw)

        ax.legend()

    def save_and_close(self,
                      fig: plt.Figure,
                      filepath: str,
                      dpi: int = 300,
                      close: bool = True) -> None:
        """
        Save figure to file with publication-quality settings.

        Args:
            fig: Matplotlib figure object
            filepath: Output file path
            dpi: Resolution in dots per inch
            close: Whether to close the figure after saving

        Examples:
            >>> plotter.save_and_close(fig, 'results/figure.pdf')
        """
        save_figure(fig, filepath, dpi=dpi, close=close)

    @abstractmethod
    def plot(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create the main visualization for this plotter.

        This method must be implemented by subclasses to define
        the specific visualization logic.

        Args:
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure object

        Examples:
            >>> fig = plotter.plot('results/plot.png')
        """
        pass

    def plot_all(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create all standard plots for the loaded result.

        This is a convenience method that creates a comprehensive
        multi-panel figure showing all key variables.

        Args:
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure object

        Examples:
            >>> fig = plotter.plot_all('results/all_plots.png')
        """
        if self.result is None:
            raise ValueError("No result data loaded. Call load_result() first.")

        # Create 2x4 subplot grid
        fig, axes = create_figure_grid(2, 4, figsize=(30, 10), style=self.style)

        time = self.get_time_data()
        Rcb = self.get_length_data(self.result['Rcb'])
        Rcf = self.get_length_data(self.result['Rcf'])
        swelling = self.calculate_swelling()

        # Plot 1: Bubble radius
        self._plot_bubble_radius(axes[0, 0], time, Rcb, Rcf)

        # Plot 2: Swelling rate
        self._plot_swelling_rate(axes[0, 1], time, swelling)

        # Plot 3: Gas concentration
        self._plot_gas_concentration(axes[1, 0], time)

        # Plot 4: Bubble concentration
        self._plot_bubble_concentration(axes[1, 1], time)

        # Plot 5: Gas atoms per bubble
        self._plot_gas_atoms_per_bubble(axes[0, 2], time)

        # Plot 6: Vacancy concentration
        self._plot_vacancy_concentration(axes[0, 3], time)

        # Plot 7: Interstitial concentration
        self._plot_interstitial_concentration(axes[1, 2], time)

        # Plot 8: Released gas
        self._plot_released_gas(axes[1, 3], time)

        plt.tight_layout()

        if save_path:
            self.save_and_close(fig, save_path)

        return fig

    def _plot_bubble_radius(self,
                           ax: plt.Axes,
                           time: np.ndarray,
                           Rcb: np.ndarray,
                           Rcf: np.ndarray) -> None:
        """Plot bubble radius vs time."""
        ax.plot(time, Rcb, label='Bulk Bubble', color=self.colors[0])
        ax.plot(time, Rcf, label='Interface Bubble', color=self.colors[1])
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel(f'Bubble Radius ({self.length_unit})')
        ax.set_title('Bubble Radius Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_swelling_rate(self,
                           ax: plt.Axes,
                           time: np.ndarray,
                           swelling: np.ndarray) -> None:
        """Plot swelling rate vs time."""
        ax.plot(time, swelling, color='red')
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Swelling Rate (%)')
        ax.set_title('Swelling Rate Evolution')
        ax.grid(True, alpha=0.3)

    def _plot_gas_concentration(self,
                               ax: plt.Axes,
                               time: np.ndarray) -> None:
        """Plot gas concentration vs time."""
        ax.plot(time, self.result['Cgb'], label='Bulk Gas',
                color=self.colors[0])
        ax.plot(time, self.result['Cgf'], label='Interface Gas',
                color=self.colors[1])
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Gas Concentration (atoms/m³)')
        ax.set_title('Gas Concentration Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_bubble_concentration(self,
                                  ax: plt.Axes,
                                  time: np.ndarray) -> None:
        """Plot bubble concentration vs time."""
        ax.plot(time, self.result['Ccb'], label='Bulk Bubbles',
                color=self.colors[0])
        ax.plot(time, self.result['Ccf'], label='Interface Bubbles',
                color=self.colors[1])
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Bubble Concentration (cavities/m³)')
        ax.set_title('Bubble Concentration Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_gas_atoms_per_bubble(self,
                                   ax: plt.Axes,
                                   time: np.ndarray) -> None:
        """Plot gas atoms per bubble vs time."""
        ax.semilogy(time, self.result['Ncb'], label='Gas Atoms in Bulk Bubble',
                    color=self.colors[0])
        ax.semilogy(time, self.result['Ncf'], label='Gas Atoms in Interface Bubble',
                    color=self.colors[1])
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Gas Atoms (atoms/cavity)')
        ax.set_title('Gas Atoms per Bubble')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_vacancy_concentration(self,
                                   ax: plt.Axes,
                                   time: np.ndarray) -> None:
        """Plot vacancy concentration vs time."""
        ax.semilogy(time, self.result['cvb'], label='Bulk Vacancy',
                    color=self.colors[0])
        ax.semilogy(time, self.result['cvf'], label='Interface Vacancy',
                    color=self.colors[1])
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Vacancy Concentration')
        ax.set_title('Vacancy Concentration Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_interstitial_concentration(self,
                                        ax: plt.Axes,
                                        time: np.ndarray) -> None:
        """Plot interstitial concentration vs time."""
        ax.semilogy(time, self.result['cib'], label='Bulk Interstitial',
                    color=self.colors[0])
        ax.semilogy(time, self.result['cif'], label='Interface Interstitial',
                    color=self.colors[1])
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Interstitial Concentration')
        ax.set_title('Interstitial Concentration Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_released_gas(self,
                          ax: plt.Axes,
                          time: np.ndarray) -> None:
        """Plot released gas vs time."""
        ax.plot(time, self.result['released_gas'], color='purple')
        ax.set_xlabel(self.get_time_label())
        ax.set_ylabel('Released Gas (atoms/m³)')
        ax.set_title('Released Gas Evolution')
        ax.grid(True, alpha=0.3)


def create_standard_plotter(result: Dict[str, np.ndarray],
                           params: Optional[Dict[str, Any]] = None,
                           **kwargs) -> GasSwellingPlotter:
    """
    Factory function to create a standard plotter with loaded data.

    Args:
        result: Simulation result dictionary
        params: Optional simulation parameters dictionary
        **kwargs: Additional arguments passed to GasSwellingPlotter.__init__

    Returns:
        GasSwellingPlotter instance with loaded data

    Examples:
        >>> plotter = create_standard_plotter(result, params, time_unit='hours')
        >>> fig = plotter.plot_all('results.png')
    """
    plotter = GasSwellingPlotter(**kwargs)
    plotter.load_result(result, params)
    return plotter
