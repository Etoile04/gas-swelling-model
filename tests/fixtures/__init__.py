"""
Test fixtures for gas swelling model test suite.

This package provides shared fixtures, test data, and utilities for testing
the gas swelling model implementation.

Note: conftest.py is auto-loaded by pytest and should not be imported directly.
Import test_data for validation data and constants.
"""

from . import test_data

__all__ = [
    # Test data from test_data.py
    'VALIDATION_DATA_U10ZR',
    'VALIDATION_DATA_U19PU10ZR',
    'VALIDATION_DATA_HIGH_PURITY_U',
    'EXTREME_CONDITIONS',
    'TOLERANCE_CONFIG',
    'PHYSICAL_CONSTANTS',
    'XENON_PROPERTIES',
    'MATERIAL_PARAMETER_RANGES',
    'PERFORMANCE_BENCHMARKS',
    'get_validation_data',
    'calculate_expected_swelling',
    'verify_physical_quantities'
]
