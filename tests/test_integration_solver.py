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
