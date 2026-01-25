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
"""

__version__ = "0.1.0"

from .core import GasSwellingPlotter, create_standard_plotter
from .evolution_plots import (
    plot_swelling_evolution,
    plot_swelling_with_uncertainty,
    plot_bubble_radius_evolution,
    plot_bubble_radius_with_uncertainty,
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
from .contour_plots import (
    plot_temperature_contour,
    plot_2d_parameter_sweep,
    plot_swelling_heatmap,
)
from .comparison_plots import (
    compare_bulk_interface,
    plot_bulk_interface_ratio,
    plot_gas_distribution_pie,
    plot_gas_distribution_evolution,
    plot_correlation_matrix,
    plot_phase_comparison,
)
from .distribution_plots import (
    plot_bubble_size_distribution,
    plot_bubble_radius_distribution,
    plot_gas_distribution_histogram,
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
    'plot_swelling_with_uncertainty',
    'plot_bubble_radius_evolution',
    'plot_bubble_radius_with_uncertainty',
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

    # Contour plots
    'plot_temperature_contour',
    'plot_2d_parameter_sweep',
    'plot_swelling_heatmap',

    # Comparison plots
    'compare_bulk_interface',
    'plot_bulk_interface_ratio',
    'plot_gas_distribution_pie',
    'plot_gas_distribution_evolution',
    'plot_correlation_matrix',
    'plot_phase_comparison',

    # Distribution plots
    'plot_bubble_size_distribution',
    'plot_bubble_radius_distribution',
    'plot_gas_distribution_histogram',

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
