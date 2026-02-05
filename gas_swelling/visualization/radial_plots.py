"""
Radial Plots Module

Provides visualization tools for radial profile simulation results.
This module implements the RadialProfilePlotter class for visualizing
spatially-resolved gas swelling simulations across fuel pellet radius.

Classes:
    RadialProfilePlotter: Plotter for 1D radial profile visualization

Examples:
    >>> from gas_swelling.visualization.radial_plots import RadialProfilePlotter
    >>> from gas_swelling.models import RadialGasSwellingModel
    >>>
    >>> model = RadialGasSwellingModel(params, n_nodes=10)
    >>> result = model.solve(t_span=(0, 8640000), t_eval=time_points)
    >>>
    >>> plotter = RadialProfilePlotter()
    >>> plotter.load_radial_result(result, model)
    >>> fig = plotter.plot_radial_profile('swelling', time_index=-1)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import warnings

from .core import GasSwellingPlotter
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


class RadialProfilePlotter(GasSwellingPlotter):
    """
    Plotter for 1D radial profile visualization.

    This class extends GasSwellingPlotter to handle spatially-resolved
    simulation results from RadialGasSwellingModel. It provides methods
    for visualizing radial profiles of temperature, swelling, gas pressure,
    and other variables across the fuel pellet radius.

    Attributes:
        radial_result: Dictionary containing radial simulation results
        mesh: RadialMesh object with node positions
        radius_unit: Unit for radius axis ('m', 'mm', 'um', 'nm')
        time_index: Index of time point to plot (default: -1 for final time)
        n_nodes: Number of radial nodes

    Examples:
        >>> plotter = RadialProfilePlotter()
        >>> plotter.load_radial_result(result, model)
        >>> fig = plotter.plot_radial_profile('swelling')
        >>> plotter.save_and_close(fig, 'swelling_profile.png')
    """

    def __init__(self,
                 time_unit: str = 'minutes',
                 length_unit: str = 'mm',
                 radius_unit: str = 'mm',
                 use_burnup: bool = False,
                 style: str = 'default'):
        """
        Initialize the radial plotter with default settings.

        Args:
            time_unit: Unit for time axis ('seconds', 'minutes', 'hours', 'days')
            length_unit: Unit for length quantities ('m', 'mm', 'um', 'nm')
            radius_unit: Unit for radius axis ('m', 'mm', 'um', 'nm')
            use_burnup: Use burnup (%FIMA) instead of time for x-axis
            style: Matplotlib style preset name
        """
        super().__init__(time_unit=time_unit, length_unit=length_unit,
                        use_burnup=use_burnup, style=style)
        self.radial_result: Optional[Dict[str, np.ndarray]] = None
        self.mesh: Optional[Any] = None
        self.radius_unit = radius_unit
        self.time_index: int = -1
        self.n_nodes: Optional[int] = None

        # Additional color palettes for radial visualization
        self.temperature_colors = get_color_palette('temperature')

    def load_radial_result(self,
                          result: Dict[str, np.ndarray],
                          mesh: Any) -> None:
        """
        Load radial simulation results for plotting.

        Args:
            result: Dictionary containing simulation results with keys:
                   - 'time': Time array (seconds)
                   - Radial profile arrays with shape (n_time, n_nodes) for:
                     'Cgb', 'Cgf', 'Ccb', 'Ccf', 'Ncb', 'Ncf',
                     'Rcb', 'Rcf', 'cvb', 'cvf', 'cib', 'cif',
                     'released_gas', 'swelling', 'Pg_b', 'Pg_f', 'temperature'
            mesh: RadialMesh object containing node positions

        Raises:
            ValueError: If required keys are missing from result

        Examples:
            >>> plotter.load_radial_result(result, model.mesh)
        """
        # Validate basic structure
        if 'time' not in result:
            raise ValueError("Missing 'time' key in result data")

        # Check that at least one radial variable exists
        radial_keys = [k for k in result.keys() if k != 'time']
        if not radial_keys:
            raise ValueError("No radial variables found in result data")

        # Check shape consistency
        time_points = len(result['time'])
        for key in radial_keys:
            data = result[key]
            if isinstance(data, np.ndarray) and data.ndim == 2:
                if data.shape[0] != time_points:
                    raise ValueError(
                        f"Inconsistent shape for '{key}': "
                        f"expected ({time_points}, n_nodes), got {data.shape}"
                    )

        self.radial_result = result
        self.mesh = mesh
        self.n_nodes = mesh.n_nodes if hasattr(mesh, 'n_nodes') else result[radial_keys[0]].shape[1]

    def get_radius_data(self) -> np.ndarray:
        """
        Get radius data in the configured unit.

        Returns:
            Radius array in configured unit

        Examples:
            >>> radius = plotter.get_radius_data()
        """
        if self.mesh is None:
            raise ValueError("No mesh data loaded. Call load_radial_result() first.")

        radius_meters = self.mesh.nodes
        return convert_length_units(radius_meters, self.radius_unit)

    def get_radius_label(self) -> str:
        """
        Get label for radius axis based on configuration.

        Returns:
            Formatted radius axis label

        Examples:
            >>> label = plotter.get_radius_label()
        """
        if self.radius_unit == 'um':
            return 'Radius (μm)'
        elif self.radius_unit == 'nm':
            return 'Radius (nm)'
        else:
            return f'Radius ({self.radius_unit})'

    def get_radial_profile(self, variable: str,
                          time_index: Optional[int] = None) -> np.ndarray:
        """
        Get radial profile for a specific variable at a given time.

        Args:
            variable: Variable name (e.g., 'swelling', 'temperature', 'Pg_b')
            time_index: Time index (default: use self.time_index)

        Returns:
            Radial profile array

        Raises:
            ValueError: If variable not found or time_index is invalid

        Examples:
            >>> swelling_profile = plotter.get_radial_profile('swelling', time_index=-1)
        """
        if self.radial_result is None:
            raise ValueError("No result data loaded. Call load_radial_result() first.")

        if variable not in self.radial_result:
            raise ValueError(f"Variable '{variable}' not found in result data. "
                           f"Available variables: {list(self.radial_result.keys())}")

        data = self.radial_result[variable]

        if time_index is None:
            time_index = self.time_index

        if time_index < -len(data) or time_index >= len(data):
            raise ValueError(f"time_index {time_index} out of range [0, {len(data)-1}]")

        return data[time_index]

    def plot(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create the main visualization for this plotter.

        This method creates a multi-panel radial profile plot showing
        key variables at the configured time index.

        Args:
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure object

        Examples:
            >>> fig = plotter.plot('results/radial_profile.png')
        """
        if self.radial_result is None:
            raise ValueError("No result data loaded. Call load_radial_result() first.")

        # Create 2x2 subplot grid
        fig, axes = create_figure_grid(2, 2, figsize=(14, 10), style=self.style)

        radius = self.get_radius_data()
        time_idx = self.time_index

        # Plot 1: Temperature profile
        if 'temperature' in self.radial_result:
            temp_profile = self.get_radial_profile('temperature', time_idx)
            axes[0, 0].plot(radius, temp_profile, color='red', linewidth=2)
            axes[0, 0].set_xlabel(self.get_radius_label())
            axes[0, 0].set_ylabel('Temperature (K)')
            axes[0, 0].set_title('Temperature Profile')
            axes[0, 0].grid(True, alpha=0.3)

        # Plot 2: Swelling profile
        if 'swelling' in self.radial_result:
            swelling_profile = self.get_radial_profile('swelling', time_idx)
            axes[0, 1].plot(radius, swelling_profile, color='blue', linewidth=2)
            axes[0, 1].set_xlabel(self.get_radius_label())
            axes[0, 1].set_ylabel('Swelling (%)')
            axes[0, 1].set_title('Swelling Profile')
            axes[0, 1].grid(True, alpha=0.3)

        # Plot 3: Gas pressure profile
        if 'Pg_b' in self.radial_result:
            pg_profile = self.get_radial_profile('Pg_b', time_idx)
            axes[1, 0].plot(radius, pg_profile, color='green', linewidth=2)
            axes[1, 0].set_xlabel(self.get_radius_label())
            axes[1, 0].set_ylabel('Gas Pressure (Pa)')
            axes[1, 0].set_title('Gas Pressure Profile')
            axes[1, 0].grid(True, alpha=0.3)
            # Use scientific notation for large values
            format_axis_scientific(axes[1, 0], axis='y')

        # Plot 4: Bubble radius profile
        if 'Rcb' in self.radial_result:
            rcb_profile = self.get_radial_profile('Rcb', time_idx)
            rcb_profile = convert_length_units(rcb_profile, self.length_unit)
            axes[1, 1].plot(radius, rcb_profile, color='purple', linewidth=2)
            axes[1, 1].set_xlabel(self.get_radius_label())
            axes[1, 1].set_ylabel(f'Bubble Radius ({self.length_unit})')
            axes[1, 1].set_title('Bubble Radius Profile')
            axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            self.save_and_close(fig, save_path)

        return fig

    def plot_radial_profile(self,
                           variable: str,
                           time_index: Optional[int] = None,
                           save_path: Optional[str] = None,
                           dpi: int = 300,
                           figsize: Tuple[float, float] = (10, 6),
                           **kwargs) -> plt.Figure:
        """
        Plot radial profile for a single variable.

        Args:
            variable: Variable name to plot
            time_index: Time index (default: use self.time_index)
            save_path: Optional path to save the figure
            dpi: Resolution for saved figure
            figsize: Figure size (width, height) in inches
            **kwargs: Additional matplotlib kwargs (color, linewidth, etc.)

        Returns:
            Matplotlib figure object

        Examples:
            >>> fig = plotter.plot_radial_profile('swelling', time_index=-1)
            >>> plotter.save_and_close(fig, 'swelling_profile.png')
        """
        apply_publication_style(self.style)

        radius = self.get_radius_data()
        profile = self.get_radial_profile(variable, time_index)

        fig, ax = plt.subplots(figsize=figsize)

        # Plot profile
        color = kwargs.get('color', 'blue')
        linewidth = kwargs.get('linewidth', 2.0)
        ax.plot(radius, profile, color=color, linewidth=linewidth)

        # Styling
        ax.set_xlabel(self.get_radius_label())
        ax.set_ylabel(self._get_variable_label(variable))
        ax.set_title(f'{self._get_variable_label(variable)} Profile')
        ax.grid(True, linestyle='--', alpha=0.3)

        # Set axis limits if provided
        if 'xlim' in kwargs:
            ax.set_xlim(kwargs['xlim'])
        if 'ylim' in kwargs:
            ax.set_ylim(kwargs['ylim'])

        # Use scientific notation for large values
        if np.max(np.abs(profile)) > 1000:
            format_axis_scientific(ax, axis='y')

        plt.tight_layout()

        if save_path:
            self.save_and_close(fig, save_path, dpi=dpi)

        return fig

    def plot_radial_comparison(self,
                              variables: List[str],
                              time_index: Optional[int] = None,
                              save_path: Optional[str] = None,
                              dpi: int = 300,
                              figsize: Tuple[float, float] = (12, 6),
                              **kwargs) -> plt.Figure:
        """
        Plot multiple variables on the same radial axis.

        This method creates overlay plots of multiple radial profiles on the
        same axes. For variables with significantly different scales, consider
        using normalization or separate axes.

        Args:
            variables: List of variable names to plot (e.g., ['temperature', 'swelling'])
            time_index: Time index (default: use self.time_index)
            save_path: Optional path to save the figure
            dpi: Resolution for saved figure
            figsize: Figure size (width, height) in inches
            **kwargs: Additional options:
                - colors: List of color names for each variable
                - linewidth: Line width for all plots (default 2.0)
                - normalize: If True, normalize profiles to [0, 1] for comparison
                - secondary_axis: If True, use twin y-axis for last variable

        Returns:
            Matplotlib figure object

        Raises:
            ValueError: If variables list is empty or contains unknown variables

        Examples:
            >>> fig = plotter.plot_radial_comparison(
            ...     ['temperature', 'swelling', 'Pg_b'], time_index=-1
            ... )
            >>> plotter.save_and_close(fig, 'radial_comparison.png')

            # With normalized profiles for shape comparison
            >>> fig = plotter.plot_radial_comparison(
            ...     ['swelling', 'Pg_b'], normalize=True
            ... )

            # With secondary y-axis for pressure (different scale)
            >>> fig = plotter.plot_radial_comparison(
            ...     ['temperature', 'Pg_b'], secondary_axis=True
            ... )
        """
        if not variables:
            raise ValueError("variables list cannot be empty")

        apply_publication_style(self.style)

        radius = self.get_radius_data()
        time_idx = time_index if time_index is not None else self.time_index

        # Get colors for multiple variables
        colors = kwargs.get('colors', get_color_palette('default'))

        fig, ax = plt.subplots(figsize=figsize)

        # Plot each variable
        linewidth = kwargs.get('linewidth', 2.0)
        normalize = kwargs.get('normalize', False)
        use_secondary = kwargs.get('secondary_axis', False)

        for i, var in enumerate(variables):
            profile = self.get_radial_profile(var, time_idx)
            color = colors[i % len(colors)]
            label = self._get_variable_label(var)

            # Normalize if requested (for shape comparison)
            if normalize:
                profile_min = np.min(profile)
                profile_max = np.max(profile)
                if profile_max > profile_min:
                    profile = (profile - profile_min) / (profile_max - profile_min)
                label = f'{label} (normalized)'

            # Determine which axis to use
            if use_secondary and i == len(variables) - 1:
                # Last variable on secondary axis
                if i == 0:
                    current_ax = ax  # First variable on primary axis
                else:
                    # Create secondary axis
                    current_ax = ax.twinx()
                    current_ax.spines['right'].set_position(('outward', 0))
            else:
                current_ax = ax

            # Plot on appropriate axis
            current_ax.plot(radius, profile, label=label,
                           color=color, linewidth=linewidth,
                           linestyle='--' if use_secondary and i == len(variables) - 1 else '-')

        # Styling
        ax.set_xlabel(self.get_radius_label())

        if normalize:
            ax.set_ylabel('Normalized Value [0, 1]')
        elif len(variables) == 1:
            ax.set_ylabel(self._get_variable_label(variables[0]))
        else:
            ax.set_ylabel('Value')

        ax.set_title('Radial Profile Comparison')
        ax.grid(True, linestyle='--', alpha=0.3)

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        if use_secondary and len(variables) > 1:
            # Get secondary axis
            for other_ax in fig.get_axes():
                if other_ax != ax:
                    lines2, labels2 = other_ax.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='best')
                    break
        else:
            ax.legend(lines1, labels1, loc='best')

        plt.tight_layout()

        if save_path:
            self.save_and_close(fig, save_path, dpi=dpi)

        return fig

    def plot_radial_evolution(self,
                             variable: str,
                             time_indices: Optional[List[int]] = None,
                             save_path: Optional[str] = None,
                             dpi: int = 300,
                             figsize: Tuple[float, float] = (10, 6),
                             **kwargs) -> plt.Figure:
        """
        Plot radial profile evolution over multiple time points.

        Args:
            variable: Variable name to plot
            time_indices: List of time indices to plot
                         (default: [0, 25%, 50%, 75%, 100%] of time points)
            save_path: Optional path to save the figure
            dpi: Resolution for saved figure
            figsize: Figure size (width, height) in inches
            **kwargs: Additional matplotlib kwargs

        Returns:
            Matplotlib figure object

        Examples:
            >>> fig = plotter.plot_radial_evolution('swelling')
            >>> plt.close(fig)
        """
        apply_publication_style(self.style)

        if self.radial_result is None:
            raise ValueError("No result data loaded. Call load_radial_result() first.")

        radius = self.get_radius_data()

        # Default time indices: 0, 25%, 50%, 75%, 100%
        if time_indices is None:
            n_time = len(self.radial_result['time'])
            time_indices = [0, n_time//4, n_time//2, 3*n_time//4, n_time-1]

        fig, ax = plt.subplots(figsize=figsize)

        # Get color palette for time evolution
        colors = kwargs.get('colors', self.temperature_colors)
        linewidth = kwargs.get('linewidth', 2.0)

        # Plot profile at each time point
        for i, t_idx in enumerate(time_indices):
            profile = self.get_radial_profile(variable, t_idx)
            color = colors[i % len(colors)]

            # Get time value for label
            time_value = self.radial_result['time'][t_idx]
            if self.use_burnup and self.params is not None:
                fission_rate = self.params.get('fission_rate', 5e19)
                time_label = f'{calculate_burnup(np.array([time_value]), fission_rate)[0]:.2f} %FIMA'
            else:
                time_min = convert_time_units(np.array([time_value]), self.time_unit)[0]
                time_label = f'{time_min:.1f} {self.time_unit}'

            ax.plot(radius, profile, label=time_label,
                   color=color, linewidth=linewidth)

        # Styling
        ax.set_xlabel(self.get_radius_label())
        ax.set_ylabel(self._get_variable_label(variable))
        ax.set_title(f'{self._get_variable_label(variable)} Evolution')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)

        plt.tight_layout()

        if save_path:
            self.save_and_close(fig, save_path, dpi=dpi)

        return fig

    def _get_variable_label(self, variable: str) -> str:
        """
        Get formatted label for a variable.

        Args:
            variable: Variable name

        Returns:
            Formatted label string
        """
        # Check standard labels
        if variable in VARIABLE_LABELS:
            return VARIABLE_LABELS[variable]

        # Custom labels for radial variables
        labels = {
            'temperature': 'Temperature (K)',
            'swelling': 'Swelling (%)',
            'Pg_b': 'Bulk Bubble Pressure (Pa)',
            'Pg_f': 'Interface Bubble Pressure (Pa)',
            'Rcb': f'Bulk Bubble Radius ({self.length_unit})',
            'Rcf': f'Interface Bubble Radius ({self.length_unit})',
            'Cgb': 'Bulk Gas Concentration (atoms/m³)',
            'Cgf': 'Interface Gas Concentration (atoms/m³)',
        }

        return labels.get(variable, variable)


def create_radial_plotter(result: Dict[str, np.ndarray],
                         mesh: Any,
                         **kwargs) -> RadialProfilePlotter:
    """
    Factory function to create a radial plotter with loaded data.

    Args:
        result: Radial simulation result dictionary
        mesh: RadialMesh object
        **kwargs: Additional arguments passed to RadialProfilePlotter.__init__

    Returns:
        RadialProfilePlotter instance with loaded data

    Examples:
        >>> plotter = create_radial_plotter(result, model.mesh, radius_unit='mm')
        >>> fig = plotter.plot()
    """
    plotter = RadialProfilePlotter(**kwargs)
    plotter.load_radial_result(result, mesh)
    return plotter
