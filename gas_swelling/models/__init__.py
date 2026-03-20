"""
Models module for gas swelling simulations.

This module contains the core gas swelling model implementations:
- GasSwellingModel: Original monolithic implementation (deprecated)
- RefactoredGasSwellingModel: Modular implementation following new architecture (recommended)
- QSSAGasSwellingModel: Experimental reduced-order model with algebraic defect closure
- HybridQSSAGasSwellingModel: Reduced-order model with partial defect elimination
- RadialGasSwellingModel: 1D radial discretization model for spatial variations
"""

# Original model (deprecated - use RefactoredGasSwellingModel)
from .modelrk23 import GasSwellingModel

# Refactored model (recommended)
from .refactored_model import RefactoredGasSwellingModel

# Experimental reduced-order model
from .qssa_model import QSSAGasSwellingModel
from .hybrid_qssa_model import HybridQSSAGasSwellingModel

# Radial model (1D spatial discretization)
from .radial_model import RadialGasSwellingModel

__all__ = [
    'GasSwellingModel',
    'RefactoredGasSwellingModel',
    'QSSAGasSwellingModel',
    'HybridQSSAGasSwellingModel',
    'RadialGasSwellingModel'
]
