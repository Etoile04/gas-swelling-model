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

__all__ = [
    'swelling_ode_system',
    'calculate_sink_strengths',
    'calculate_point_defect_derivatives',
    'calculate_cavity_radius_derivatives',
    'calculate_gas_concentration_derivatives'
]
