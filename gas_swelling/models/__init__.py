"""
Models module for gas swelling simulations.

This module contains the core gas swelling model implementations:
- GasSwellingModel: Original monolithic implementation (deprecated)
- RefactoredGasSwellingModel: Modular implementation following new architecture (recommended)
- RadialGasSwellingModel: 1D radial discretization model for spatial variations
"""

# Original model (deprecated - use RefactoredGasSwellingModel)
from .modelrk23 import GasSwellingModel

# Refactored model (recommended)
from .refactored_model import RefactoredGasSwellingModel

# Radial model (1D spatial discretization)
from .radial_model import RadialGasSwellingModel

__all__ = [
    'GasSwellingModel',
    'RefactoredGasSwellingModel',
    'RadialGasSwellingModel'
]
