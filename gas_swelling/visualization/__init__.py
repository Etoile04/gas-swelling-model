"""
Gas Swelling Visualization Module

A visualization toolkit for the Gas Swelling Model package.
Provides plotting and visualization capabilities for fission gas bubble evolution
and void swelling behavior in irradiated metallic fuels.

This module provides tools for:
- Time series visualization of state variables
- Bubble size distribution plots
- Swelling rate analysis
- Temperature and parameter sweep visualizations
- Radial profile visualization for spatially-resolved simulations
"""

__version__ = "0.1.0"

from .core import GasSwellingPlotter, create_standard_plotter
from .evolution_plots import (
    plot_swelling_evolution,
    plot_bubble_radius_evolution,
    plot_gas_concentration_evolution,
    plot_bubble_concentration_evolution,
    plot_gas_atoms_evolution,
    plot_gas_pressure_evolution,
    plot_defect_concentration_evolution,
    plot_released_gas_evolution,
    plot_multi_panel_evolution,
)
from .parameter_sweeps import (
    plot_temperature_sweep,
    plot_multi_param_temperature_sweep,
    plot_parameter_sensitivity,
    plot_arrhenius_analysis,
)
from .comparison_plots import (
    compare_bulk_interface,
    plot_bulk_interface_ratio,
    plot_gas_distribution_pie,
    plot_gas_distribution_evolution,
    plot_correlation_matrix,
    plot_phase_comparison,
)
from .radial_plots import (
    RadialProfilePlotter,
    create_radial_plotter,
)
from .utils import (
    # Style configuration
    get_publication_style,
    apply_publication_style,
    get_color_palette,

    # Figure utilities
    save_figure,
    create_figure_grid,
    add_subfigure_labels,

    # Unit conversions
    convert_time_units,
    convert_length_units,
    calculate_burnup,

    # Axis formatting
    format_axis_scientific,
    set_axis_limits,

    # Labels
    get_time_unit_label,
    get_length_unit_label,
    VARIABLE_LABELS,
)

__all__ = [
    # Core classes
    'GasSwellingPlotter',
    'create_standard_plotter',

    # Evolution plots
    'plot_swelling_evolution',
    'plot_bubble_radius_evolution',
    'plot_gas_concentration_evolution',
    'plot_bubble_concentration_evolution',
    'plot_gas_atoms_evolution',
    'plot_gas_pressure_evolution',
    'plot_defect_concentration_evolution',
    'plot_released_gas_evolution',
    'plot_multi_panel_evolution',

    # Parameter sweep plots
    'plot_temperature_sweep',
    'plot_multi_param_temperature_sweep',
    'plot_parameter_sensitivity',
    'plot_arrhenius_analysis',

    # Comparison plots
    'compare_bulk_interface',
    'plot_bulk_interface_ratio',
    'plot_gas_distribution_pie',
    'plot_gas_distribution_evolution',
    'plot_correlation_matrix',
    'plot_phase_comparison',

    # Radial plots
    'RadialProfilePlotter',
    'create_radial_plotter',

    # Style configuration
    'get_publication_style',
    'apply_publication_style',
    'get_color_palette',

    # Figure utilities
    'save_figure',
    'create_figure_grid',
    'add_subfigure_labels',

    # Unit conversions
    'convert_time_units',
    'convert_length_units',
    'calculate_burnup',

    # Axis formatting
    'format_axis_scientific',
    'set_axis_limits',

    # Labels
    'get_time_unit_label',
    'get_length_unit_label',
    'VARIABLE_LABELS',
]
