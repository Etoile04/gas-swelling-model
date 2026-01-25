"""
Gas Swelling Model Package

A scientific computing package for modeling fission gas bubble evolution
and void swelling behavior in irradiated metallic fuels (U-Zr and U-Pu-Zr alloys).

This package implements rate theory models based on:
"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium
phase of irradiated U-Zr and U-Pu-Zr fuel."

Package Structure:
- models: Core model implementations (original and refactored)
- physics: Physics calculations (pressure, transport, thermal)
- ode: Rate equation system
- solvers: Numerical integration methods
- params: Parameter definitions and defaults
- io: Debug output and visualization
"""

__version__ = "0.1.0"

# Original model (deprecated - use RefactoredGasSwellingModel)
from .models.modelrk23 import GasSwellingModel

# Refactored model (recommended)
from .models.refactored_model import RefactoredGasSwellingModel

# Parameters
from .params.parameters import (
    MaterialParameters,
    SimulationParameters,
    create_default_parameters,
    BOLTZMANN_CONSTANT_EV,
    BOLTZMANN_CONSTANT_J,
    GAS_CONSTANT,
    AVOGADRO_CONSTANT
)
from .analysis import SensitivityAnalyzer

# Physics calculations
from .physics import (
    calculate_gas_pressure,
    calculate_gas_influx,
    calculate_gas_release_rate,
    calculate_cv0,
    calculate_ci0
)

# ODE system
from .ode import swelling_ode_system

# Solvers
from .solvers import RK23Solver, EulerSolver

# I/O utilities
from .io import (
    DebugConfig,
    DebugHistory,
    update_debug_history,
    print_simulation_summary
)

__all__ = [
    # Models
    'GasSwellingModel',
    'RefactoredGasSwellingModel',

    # Parameters
    'MaterialParameters',
    'SimulationParameters',
    'create_default_parameters',
    'BOLTZMANN_CONSTANT_EV',
    'BOLTZMANN_CONSTANT_J',
    'GAS_CONSTANT',
    'AVOGADRO_CONSTANT',
    'SensitivityAnalyzer',

    # Physics
    'calculate_gas_pressure',
    'calculate_gas_influx',
    'calculate_gas_release_rate',
    'calculate_cv0',
    'calculate_ci0',

    # ODE
    'swelling_ode_system',

    # Solvers
    'RK23Solver',
    'EulerSolver',

    # I/O
    'DebugConfig',
    'DebugHistory',
    'update_debug_history',
    'print_simulation_summary'
]
