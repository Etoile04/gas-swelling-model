"""
气体物理计算模块 (Gas Physics Calculation Module)

This module provides physics calculations for gas behavior in nuclear fuel materials,
including pressure calculations using various equations of state.
"""

from .pressure import (
    calculate_ideal_gas_pressure,
    calculate_modified_vdw_pressure,
    calculate_virial_eos_pressure,
    calculate_ronchi_pressure,
    calculate_gas_pressure
)

__all__ = [
    'calculate_ideal_gas_pressure',
    'calculate_modified_vdw_pressure',
    'calculate_virial_eos_pressure',
    'calculate_ronchi_pressure',
    'calculate_gas_pressure'
]
