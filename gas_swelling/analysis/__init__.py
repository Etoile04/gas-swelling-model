"""
Analysis module for gas swelling model sensitivity analysis.

This module contains tools for parameter sensitivity analysis,
uncertainty quantification, and statistical analysis of model outputs.
"""

from .sensitivity import (
    SensitivityAnalyzer,
    ParameterRange,
    create_default_parameter_ranges,
    OATAnalyzer,
    OATResult,
    MorrisAnalyzer,
    MorrisResult,
    SobolAnalyzer,
    SobolResult
)
from .metrics import (
    calculate_normalized_sensitivity,
    calculate_elasticity,
    calculate_absolute_sensitivity,
    calculate_relative_sensitivity,
    calculate_sensitivity_coefficient,
    calculate_sensitivity_metrics
)
from .visualization import (
    plot_tornado,
    plot_tornado_multi_output,
    plot_oat_variation,
    plot_sensitivity_heatmap
)

__all__ = [
    'SensitivityAnalyzer',
    'ParameterRange',
    'create_default_parameter_ranges',
    'OATAnalyzer',
    'OATResult',
    'MorrisAnalyzer',
    'MorrisResult',
    'SobolAnalyzer',
    'SobolResult',
    'calculate_normalized_sensitivity',
    'calculate_elasticity',
    'calculate_absolute_sensitivity',
    'calculate_relative_sensitivity',
    'calculate_sensitivity_coefficient',
    'calculate_sensitivity_metrics',
    'plot_tornado',
    'plot_tornado_multi_output',
    'plot_oat_variation',
    'plot_sensitivity_heatmap'
]
