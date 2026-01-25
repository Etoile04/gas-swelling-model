"""
I/O Module for Gas Swelling Model
输入输出模块 (气体肿胀模型)

This module handles input/output operations for the gas swelling model,
including debug output and visualization utilities.
本模块处理气体肿胀模型的输入/输出操作，包括调试输出和可视化工具。
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
    # Debug output (调试输出)
    'DebugConfig',
    'DebugHistory',
    'format_debug_output',
    'log_debug_message',
    'save_debug_history',
    'load_debug_history',
    'update_debug_history',
    'print_simulation_summary',
    # Visualization (可视化)
    'check_matplotlib_available',
    'setup_chinese_font',
    'plot_time_series',
    'plot_dual_axis',
    'plot_debug_history',
    'plot_swelling_comparison'
]
