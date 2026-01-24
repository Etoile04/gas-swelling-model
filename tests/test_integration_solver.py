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


def test_solver_time_parameters():
    """Test solver with different time spans and t_eval parameters"""
    # Create model with default parameters
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Test case 1: Short time span with few time points
    sim_time_short = 100
    t_eval_short = np.linspace(0, sim_time_short, 5)

    result_short = model.solve(
        t_span=(0, sim_time_short),
        t_eval=t_eval_short
    )

    # Verify short simulation results
    assert isinstance(result_short, dict)
    assert len(result_short['time']) == 5
    assert result_short['time'][0] == 0.0
    assert result_short['time'][-1] == sim_time_short
    assert np.all(np.isfinite(result_short['Cgb']))
    assert np.all(np.isfinite(result_short['Rcb']))
    assert np.all(result_short['Rcb'] > 0)

    # Test case 2: Medium time span with medium time points
    sim_time_medium = 1000
    t_eval_medium = np.linspace(0, sim_time_medium, 20)

    result_medium = model.solve(
        t_span=(0, sim_time_medium),
        t_eval=t_eval_medium
    )

    # Verify medium simulation results
    assert isinstance(result_medium, dict)
    assert len(result_medium['time']) == 20
    assert result_medium['time'][0] == 0.0
    assert result_medium['time'][-1] == sim_time_medium
    assert np.all(np.isfinite(result_medium['Cgb']))
    assert np.all(np.isfinite(result_medium['Rcb']))
    assert np.all(result_medium['Rcb'] > 0)

    # Test case 3: Long time span with many time points
    sim_time_long = 5000
    t_eval_long = np.linspace(0, sim_time_long, 50)

    result_long = model.solve(
        t_span=(0, sim_time_long),
        t_eval=t_eval_long
    )

    # Verify long simulation results
    assert isinstance(result_long, dict)
    assert len(result_long['time']) == 50
    assert result_long['time'][0] == 0.0
    assert result_long['time'][-1] == sim_time_long
    assert np.all(np.isfinite(result_long['Cgb']))
    assert np.all(np.isfinite(result_long['Rcb']))
    assert np.all(result_long['Rcb'] > 0)

    # Test case 4: Verify consistency - final time should match regardless of t_eval density
    # Create a new model for consistency check
    model_consistency = GasSwellingModel(create_default_parameters())
    sim_time_consistency = 2000

    # Run with sparse t_eval
    t_eval_sparse = np.linspace(0, sim_time_consistency, 10)
    result_sparse = model_consistency.solve(
        t_span=(0, sim_time_consistency),
        t_eval=t_eval_sparse
    )

    # Run with dense t_eval
    model_consistency2 = GasSwellingModel(create_default_parameters())
    t_eval_dense = np.linspace(0, sim_time_consistency, 100)
    result_dense = model_consistency2.solve(
        t_span=(0, sim_time_consistency),
        t_eval=t_eval_dense
    )

    # Both should have same final time
    assert result_sparse['time'][-1] == result_dense['time'][-1]
    assert result_sparse['time'][-1] == sim_time_consistency

    # Results should be approximately similar (allowing for small numerical differences)
    # Compare key variables at the final time point
    assert np.isclose(result_sparse['Cgb'][-1], result_dense['Cgb'][-1], rtol=1e-3)
    assert np.isclose(result_sparse['Rcb'][-1], result_dense['Rcb'][-1], rtol=1e-3)
    assert np.isclose(result_sparse['Ncb'][-1], result_dense['Ncb'][-1], rtol=1e-3)
