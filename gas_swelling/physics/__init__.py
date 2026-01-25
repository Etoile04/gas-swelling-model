"""
气体物理计算模块 (Gas Physics Calculation Module)

This module provides physics calculations for gas behavior in nuclear fuel materials,
including pressure calculations, gas transport, and release rate calculations.
"""

from .pressure import (
    calculate_ideal_gas_pressure,
    calculate_modified_vdw_pressure,
    calculate_virial_eos_pressure,
    calculate_ronchi_pressure,
    calculate_gas_pressure
)

from .gas_transport import (
    calculate_gas_influx,
    calculate_gas_release_rate,
    calculate_nucleation_rate,
    calculate_gas_absorption_rate,
    calculate_gas_resolution_rate,
    calculate_gas_production_rate,
    calculate_gas_transport_terms
)

__all__ = [
    'calculate_ideal_gas_pressure',
    'calculate_modified_vdw_pressure',
    'calculate_virial_eos_pressure',
    'calculate_ronchi_pressure',
    'calculate_gas_pressure',
    'calculate_gas_influx',
    'calculate_gas_release_rate',
    'calculate_nucleation_rate',
    'calculate_gas_absorption_rate',
    'calculate_gas_resolution_rate',
    'calculate_gas_production_rate',
    'calculate_gas_transport_terms'
]
