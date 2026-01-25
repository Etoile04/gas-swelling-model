"""
Models module for gas swelling simulations.

This module contains the core gas swelling model implementations:
- GasSwellingModel: Original monolithic implementation (deprecated)
- RefactoredGasSwellingModel: Modular implementation following new architecture (recommended)
"""

# Original model (deprecated - use RefactoredGasSwellingModel)
from .modelrk23 import GasSwellingModel

# Refactored model (recommended)
from .refactored_model import RefactoredGasSwellingModel

__all__ = [
    'GasSwellingModel',
    'RefactoredGasSwellingModel'
]
