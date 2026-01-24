"""
Integration tests for gas_swelling ODE solver

Tests model initialization, solver execution, and result processing.
"""

import pytest
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


def test_model_initialization():
    """Test that GasSwellingModel initializes correctly with default parameters"""
    # Create model with default parameters
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Check that model was created
    assert model is not None
    assert hasattr(model, 'initial_state')
    assert hasattr(model, 'params')
    assert hasattr(model, 'solve')

    # Check initial state structure
    assert isinstance(model.initial_state, np.ndarray)
    assert len(model.initial_state) == 17  # 17 state variables

    # Check that initial values are finite and non-negative where expected
    for i, val in enumerate(model.initial_state):
        assert np.isfinite(val), f"State variable {i} is not finite: {val}"
        assert val >= 0, f"State variable {i} is negative: {val}"

    # Check specific initial values
    # Cgb (gas atom concentration in bulk matrix) - should be 0 initially
    assert model.initial_state[0] == 0.0

    # Ccb (cavity concentration in bulk) - should be 0 initially
    assert model.initial_state[1] == 0.0

    # Ncb (gas atoms per bulk cavity) - should be 5.0 initially
    assert model.initial_state[2] == 5.0

    # Rcb (radius of bulk bubble) - should be positive
    assert model.initial_state[3] > 0
    assert model.initial_state[3] == 1e-8

    # Cgf (gas atom concentration at phase boundaries) - should be 0 initially
    assert model.initial_state[4] == 0.0

    # Ccf (cavity concentration at phase boundaries) - should be 0 initially
    assert model.initial_state[5] == 0.0

    # Ncf (gas atoms per boundary cavity) - should be 5.0 initially
    assert model.initial_state[6] == 5.0

    # Rcf (radius of boundary bubble) - should be positive
    assert model.initial_state[7] > 0
    assert model.initial_state[7] == 1e-8

    # cvb and cib (vacancy and interstitial concentrations) - should be positive
    assert model.initial_state[8] > 0  # cvb
    assert model.initial_state[9] > 0  # cib

    # cvf and cif (vacancy and interstitial at boundaries) - should be positive
    assert model.initial_state[12] > 0  # cvf
    assert model.initial_state[13] > 0  # cif

    # released_gas - should be 0 initially
    assert model.initial_state[16] == 0.0


def test_basic_solver_execution():
    """Test that the solver executes successfully with default parameters"""
    # Create model with default parameters
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Define simple time span for testing
    sim_time = 1000  # 1000 seconds
    t_eval = np.linspace(0, sim_time, 10)  # 10 time points

    # Run solver
    result = model.solve(
        t_span=(0, sim_time),
        t_eval=t_eval
    )

    # Check that result is a dictionary
    assert isinstance(result, dict), "Result should be a dictionary"

    # Check that result contains expected keys
    expected_keys = [
        'time', 'Cgb', 'Ccb', 'Ncb', 'Rcb', 'cvb', 'cib',
        'Cgf', 'Ccf', 'Ncf', 'Rcf', 'cvf', 'cif',
        'released_gas'
    ]
    for key in expected_keys:
        assert key in result, f"Result should contain key '{key}'"

    # Check that time array has correct length
    assert len(result['time']) == len(t_eval), \
        f"Time array should have {len(t_eval)} points"

    # Check that all result arrays have the same length as time
    for key in expected_keys:
        if key != 'time':
            assert len(result[key]) == len(result['time']), \
                f"Result key '{key}' should have same length as time array"

    # Check that final values are finite and non-negative where expected
    assert np.isfinite(result['Cgb'][-1])
    assert np.isfinite(result['Cgf'][-1])
    assert result['Cgb'][-1] >= 0
    assert result['Cgf'][-1] >= 0

    # Check bubble concentrations are non-negative
    assert result['Ccb'][-1] >= 0
    assert result['Ccf'][-1] >= 0

    # Check bubble radii are positive
    assert result['Rcb'][-1] > 0
    assert result['Rcf'][-1] > 0

    # Check gas atoms per cavity are positive
    assert result['Ncb'][-1] > 0
    assert result['Ncf'][-1] > 0

    # Check that simulation progressed (time increased)
    assert result['time'][0] == 0.0
    assert result['time'][-1] > 0

    # Check that released_gas is non-negative
    assert result['released_gas'][-1] >= 0
