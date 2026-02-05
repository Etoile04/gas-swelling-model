"""
Validation module for gas swelling model.

This module provides tools for validating model predictions against experimental data,
including error metrics, datasets, and reporting capabilities.
"""

from .metrics import (
    calculate_rmse,
    calculate_r2,
    calculate_max_error,
    calculate_mae
)

# Note: datasets and reporting modules require numpy/matplotlib
# and are imported separately to avoid import errors when dependencies are not available.
# Import as:
# from gas_swelling.validation import datasets, reporting
# or
# from gas_swelling.validation.datasets import get_u10zr_data
# from gas_swelling.validation.reporting import generate_validation_report

__all__ = [
    'calculate_rmse',
    'calculate_r2',
    'calculate_max_error',
    'calculate_mae'
]
