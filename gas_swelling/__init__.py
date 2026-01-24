"""
Gas Swelling Model Package

A scientific computing package for modeling fission gas bubble evolution
and void swelling behavior in irradiated metallic fuels (U-Zr and U-Pu-Zr alloys).

This package implements rate theory models based on:
"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium
phase of irradiated U-Zr and U-Pu-Zr fuel."
"""

__version__ = "0.1.0"

from .models.modelrk23 import GasSwellingModel
from .params.parameters import (
    MaterialParameters,
    SimulationParameters,
    create_default_parameters,
    BOLTZMANN_CONSTANT_EV,
    BOLTZMANN_CONSTANT_J,
    GAS_CONSTANT,
    AVOGADRO_CONSTANT
)

__all__ = [
    'GasSwellingModel',
    'MaterialParameters',
    'SimulationParameters',
    'create_default_parameters',
    'BOLTZMANN_CONSTANT_EV',
    'BOLTZMANN_CONSTANT_J',
    'GAS_CONSTANT',
    'AVOGADRO_CONSTANT'
]
