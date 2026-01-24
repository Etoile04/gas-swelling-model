"""
Configuration Module

This module handles loading, validation, and management of simulation
configuration from YAML files. It merges user-provided configurations
with default parameters and validates them.

Functions:
    load_config: Load and merge YAML configuration with defaults
    validate_params: Validate parameter types and ranges
    get_defaults: Get default parameter values
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import sys
import os

# Add parent directory to path to import parameters module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from params.parameters import create_default_parameters
except ImportError:
    # Fallback if parameters.py is not available
    def create_default_parameters() -> Dict[str, Any]:
        """Fallback default parameters"""
        return {
            'temperature': 773.0,
            'fission_rate': 5e19,
            'max_time': 8640000,
        }


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file and merge with defaults.

    This function loads a YAML configuration file and merges it with default
    parameters. User-provided values override defaults. The merged configuration
    includes all material parameters, simulation parameters, and computed values.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary containing merged configuration parameters

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails

    Example:
        >>> params = load_config('config.yaml')
        >>> print(params['temperature'])
        773.0
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        user_config = yaml.safe_load(f) or {}

    # Get defaults and merge with user config
    # User config values take precedence over defaults
    defaults = get_defaults()
    config = {**defaults, **user_config}

    return config


def validate_params(params: Dict[str, Any]) -> bool:
    """
    Validate simulation parameters.

    This function validates that required parameters are present, that
    parameter values have correct types, and that values are within
    acceptable physical ranges.

    Args:
        params: Dictionary of parameters to validate

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails with descriptive error message
        TypeError: If parameter has incorrect type

    Example:
        >>> validate_params({'temperature': 773.0, 'fission_rate': 5e19})
        True
    """
    # Define validation rules for key parameters
    validation_rules = {
        # Required simulation parameters
        'temperature': {
            'type': (int, float),
            'required': True,
            'min': 0.0,
            'max': 5000.0,
            'description': 'Operating temperature (K)'
        },
        'fission_rate': {
            'type': (int, float),
            'required': True,
            'min': 0.0,
            'max': 1e22,
            'description': 'Fission rate (fissions/m³/s)'
        },
        'max_time': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'description': 'Maximum simulation time (s)'
        },
        'time_step': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'description': 'Initial time step (s)'
        },
        'max_time_step': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'description': 'Maximum time step (s)'
        },

        # Material parameters
        'dislocation_density': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'max': 1e16,
            'description': 'Dislocation density (m⁻²)'
        },
        'surface_energy': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'max': 10.0,
            'description': 'Surface energy (J/m²)'
        },
        'grain_diameter': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'max': 1e-3,
            'description': 'Grain diameter (m)'
        },

        # Gas equation of state model
        'eos_model': {
            'type': str,
            'required': False,
            'allowed_values': ['ideal', 'ronchi'],
            'description': 'Gas equation of state model'
        },

        # Nucleation factors
        'Fnb': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'max': 1.0,
            'description': 'Bulk nucleation factor'
        },
        'Fnf': {
            'type': (int, float),
            'required': False,
            'min': 0.0,
            'max': 1.0,
            'description': 'Boundary nucleation factor'
        },
    }

    # Validate each parameter according to its rules
    for param_name, rules in validation_rules.items():
        # Check if required parameter is present
        if rules.get('required', False) and param_name not in params:
            raise ValueError(
                f"Missing required parameter: '{param_name}' "
                f"({rules['description']})"
            )

        # Skip validation if parameter is not present and not required
        if param_name not in params:
            continue

        value = params[param_name]

        # Type checking
        expected_type = rules['type']
        if not isinstance(value, expected_type):
            raise TypeError(
                f"Parameter '{param_name}' has incorrect type. "
                f"Expected {expected_type}, got {type(value).__name__}"
            )

        # Range checking for numeric types
        if isinstance(value, (int, float)):
            # Check minimum value
            if 'min' in rules and value < rules['min']:
                raise ValueError(
                    f"Parameter '{param_name}' = {value} is below minimum {rules['min']}"
                )

            # Check maximum value
            if 'max' in rules and value > rules['max']:
                raise ValueError(
                    f"Parameter '{param_name}' = {value} exceeds maximum {rules['max']}"
                )

        # Allowed values checking for string types
        if isinstance(value, str) and 'allowed_values' in rules:
            if value not in rules['allowed_values']:
                raise ValueError(
                    f"Parameter '{param_name}' = '{value}' is not allowed. "
                    f"Must be one of: {rules['allowed_values']}"
                )

    # Validate logical relationships between parameters
    if 'time_step' in params and 'max_time_step' in params:
        if params['time_step'] > params['max_time_step']:
            raise ValueError(
                f"Parameter 'time_step' ({params['time_step']}) cannot be greater than "
                f"'max_time_step' ({params['max_time_step']})"
            )

    if 'time_step' in params and 'max_time' in params:
        if params['time_step'] > params['max_time']:
            raise ValueError(
                f"Parameter 'time_step' ({params['time_step']}) cannot be greater than "
                f"'max_time' ({params['max_time']})"
            )

    return True


def get_defaults() -> Dict[str, Any]:
    """
    Get default parameter values.

    This function returns the complete set of default parameters for the
    gas swelling simulation, including:
    - Material parameters (lattice constants, diffusion coefficients, etc.)
    - Simulation parameters (fission rate, temperature, time stepping)
    - Computed parameters (gas diffusivities, physical constants)

    Returns:
        Dictionary of default parameters (typically 50+ parameters)

    Example:
        >>> defaults = get_defaults()
        >>> print(f'Temperature: {defaults["temperature"]} K')
        Temperature: 600 K
    """
    return create_default_parameters()
