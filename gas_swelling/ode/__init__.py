"""
常微分方程系统模块 (ODE System Module)

This module provides the rate equation system for gas swelling in nuclear fuel materials.
The ODE system describes the evolution of gas bubbles, point defects, and cavity growth
in irradiated metallic fuel materials.

主要功能 (Main Functions):
- swelling_ode_system: 完整的速率方程系统 (complete rate equation system)
  用于求解气体肿胀演化的常微分方程组 (ODE system for gas swelling evolution)
"""

from .rate_equations import (
    swelling_ode_system,
    calculate_sink_strengths,
    calculate_point_defect_derivatives,
    calculate_cavity_radius_derivatives,
    calculate_gas_concentration_derivatives
)
from .qssa_rate_equations import (
    swelling_qssa_ode_system,
    calculate_qssa_point_defect_concentrations,
    calculate_qssa_auxiliary_fields,
    calculate_hybrid_qssa_auxiliary_fields,
    calculate_relaxed_qssa_pair,
    select_dynamic_pair,
    swelling_hybrid_qssa_ode_system,
)

__all__ = [
    'swelling_ode_system',
    'swelling_qssa_ode_system',
    'swelling_hybrid_qssa_ode_system',
    'calculate_sink_strengths',
    'calculate_point_defect_derivatives',
    'calculate_cavity_radius_derivatives',
    'calculate_gas_concentration_derivatives',
    'calculate_qssa_point_defect_concentrations',
    'calculate_qssa_auxiliary_fields',
    'calculate_hybrid_qssa_auxiliary_fields',
    'calculate_relaxed_qssa_pair',
    'select_dynamic_pair',
]
