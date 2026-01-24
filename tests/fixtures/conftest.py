"""
Shared pytest fixtures for gas swelling model tests.

This module provides reusable fixtures for creating model instances,
parameter configurations, and test utilities.
"""

import pytest
import numpy as np
from pathlib import Path

from gas_swelling import GasSwellingModel, create_default_parameters


@pytest.fixture
def default_params():
    """Default parameter configuration."""
    return create_default_parameters()


@pytest.fixture
def default_model(default_params):
    """GasSwellingModel instance with default parameters."""
    model = GasSwellingModel(default_params)
    return model


@pytest.fixture
def custom_model():
    """GasSwellingModel instance with custom parameters for testing."""
    params = create_default_parameters()
    # Modify some parameters for testing
    params['temperature'] = 700  # K
    params['fission_rate'] = 3e20  # fissions/m^3/s
    params['time_step'] = 1e-8  # s
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def low_temperature_model():
    """Model with low temperature configuration (300 K)."""
    params = create_default_parameters()
    params['temperature'] = 300  # K
    params['fission_rate'] = 2e20  # fissions/m^3/s
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def high_temperature_model():
    """Model with high temperature configuration (1000 K)."""
    params = create_default_parameters()
    params['temperature'] = 1000  # K
    params['fission_rate'] = 2e20  # fissions/m^3/s
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def high_fission_rate_model():
    """Model with high fission rate configuration."""
    params = create_default_parameters()
    params['temperature'] = 600  # K
    params['fission_rate'] = 5e20  # fissions/m^3/s (higher than default)
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def low_fission_rate_model():
    """Model with low fission rate configuration."""
    params = create_default_parameters()
    params['temperature'] = 600  # K
    params['fission_rate'] = 1e19  # fissions/m^3/s (lower than default)
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def ideal_gas_model():
    """Model configured to use ideal gas equation of state."""
    params = create_default_parameters()
    params['eos_model'] = 'ideal'
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def ronchi_gas_model():
    """Model configured to use Ronchi equation of state."""
    params = create_default_parameters()
    params['eos_model'] = 'ronchi'
    model = GasSwellingModel(params)
    return model


@pytest.fixture
def short_simulation_params():
    """Parameters for short simulation time (for faster tests)."""
    params = create_default_parameters()
    params['max_time'] = 3600  # 1 hour instead of 100 days
    return params


@pytest.fixture
def time_points():
    """Standard time points for simulation evaluation."""
    # Generate time points from 0 to 100 days
    return np.linspace(0, 3600 * 24 * 100, 100)


@pytest.fixture
def short_time_points():
    """Time points for short simulation (for faster tests)."""
    return np.linspace(0, 3600, 10)


@pytest.fixture
def initial_state():
    """Initial state vector for the ODE system.

    Returns initial values for the 10 state variables:
    [Cgb, Ccb, Ncb, cvb, cib, Cgf, Ccf, Ncf, cvf, cif]
    """
    return np.zeros(10)


@pytest.fixture
def state_variable_names():
    """Names of the 10 state variables in order."""
    return [
        'Cgb',  # Gas atom concentration in bulk
        'Ccb',  # Cavity concentration in bulk
        'Ncb',  # Gas atoms per bulk cavity
        'cvb',  # Vacancy concentration in bulk
        'cib',  # Interstitial concentration in bulk
        'Cgf',  # Gas atom concentration at boundaries
        'Ccf',  # Cavity concentration at boundaries
        'Ncf',  # Gas atoms per boundary cavity
        'cvf',  # Vacancy concentration at boundaries
        'cif'   # Interstitial concentration at boundaries
    ]


@pytest.fixture
def temperature_sweep_range():
    """Temperature range for temperature sweep studies."""
    return np.linspace(400, 1000, 13)  # From 400K to 1000K in 50K increments


@pytest.fixture
def fission_rate_sweep_range():
    """Fission rate range for parametric studies."""
    return np.logspace(18, 21, 10)  # From 1e18 to 1e21 fissions/m^3/s


@pytest.fixture
def tolerance_config():
    """Configuration for numerical tolerances in tests."""
    return {
        'rtol': 1e-5,      # Relative tolerance for ODE solver
        'atol': 1e-10,     # Absolute tolerance for ODE solver
        'value_rtol': 1e-3,  # Relative tolerance for value comparisons
        'value_atol': 1e-10,  # Absolute tolerance for value comparisons
        'swelling_rtol': 1e-2,  # Relative tolerance for swelling values
        'pressure_rtol': 1e-2,  # Relative tolerance for pressure values
        'radius_rtol': 1e-2     # Relative tolerance for radius values
    }


@pytest.fixture
def output_dir():
    """Temporary directory for test output files."""
    return Path(__file__).parent.parent / 'test_outputs'


@pytest.fixture
def sample_result(default_model, time_points):
    """Sample simulation result for testing derived quantities."""
    result = default_model.solve(
        t_span=(0, time_points[-1]),
        t_eval=time_points
    )
    return result
