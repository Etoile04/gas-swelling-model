"""
I/O Module for Gas Swelling Model

This module handles input/output operations for the gas swelling model,
including debug output and visualization utilities.
"""

from .debug_output import (
    DebugConfig,
    DebugHistory,
    format_debug_output,
    log_debug_message,
    save_debug_history,
    load_debug_history,
    update_debug_history,
    print_simulation_summary
)

from .visualization import (
    check_matplotlib_available,
    setup_chinese_font,
    plot_time_series,
    plot_dual_axis,
    plot_debug_history,
    plot_swelling_comparison
)

__all__ = [
    # Debug output
    'DebugConfig',
    'DebugHistory',
    'format_debug_output',
    'log_debug_message',
    'save_debug_history',
    'load_debug_history',
    'update_debug_history',
    'print_simulation_summary',
    # Visualization
    'check_matplotlib_available',
    'setup_chinese_font',
    'plot_time_series',
    'plot_dual_axis',
    'plot_debug_history',
    'plot_swelling_comparison'
]
