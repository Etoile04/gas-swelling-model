"""
Parameters module for gas swelling model configuration.

This module contains parameter definitions and configuration for the gas swelling model.
"""

from .parameters import (
    MaterialParameters,
    SimulationParameters,
    create_default_parameters,
    BOLTZMANN_CONSTANT_EV,
    BOLTZMANN_CONSTANT_J,
    GAS_CONSTANT,
    AVOGADRO_CONSTANT
)

__all__ = [
    'MaterialParameters',
    'SimulationParameters',
    'create_default_parameters',
    'BOLTZMANN_CONSTANT_EV',
    'BOLTZMANN_CONSTANT_J',
    'GAS_CONSTANT',
    'AVOGADRO_CONSTANT'
]
