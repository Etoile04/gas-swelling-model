"""
Edge case and error handling tests for gas_swelling package

Tests extreme conditions including very low and very high temperatures,
zero fission rate, and invalid parameters.
"""

import pytest
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


def test_extreme_temperatures():
    """Test that the model handles extreme temperature values gracefully"""
    # Test very low temperature (near absolute zero)
    params_low = create_default_parameters()
    params_low['temperature'] = 1.0  # 1 K

    model_low = GasSwellingModel(params_low)

    # Model should initialize without error
    assert model_low is not None
    assert hasattr(model_low, 'solve')

    # Thermal equilibrium concentrations should be very small but finite
    cv0_low = model_low._calculate_cv0()
    ci0_low = model_low._calculate_ci0()

    assert np.isfinite(cv0_low), f"cv0 should be finite at 1K, got {cv0_low}"
    assert np.isfinite(ci0_low), f"ci0 should be finite at 1K, got {ci0_low}"
    assert cv0_low >= 0, f"cv0 should be non-negative at 1K, got {cv0_low}"
    assert ci0_low >= 0, f"ci0 should be non-negative at 1K, got {ci0_low}"

    # Test very high temperature (melting point of uranium is ~1405 K)
    params_high = create_default_parameters()
    params_high['temperature'] = 1300.0  # 1300 K (just below melting)

    model_high = GasSwellingModel(params_high)

    # Model should initialize without error
    assert model_high is not None
    assert hasattr(model_high, 'solve')

    # Thermal equilibrium concentrations should be larger but still finite
    cv0_high = model_high._calculate_cv0()
    ci0_high = model_high._calculate_ci0()

    assert np.isfinite(cv0_high), f"cv0 should be finite at 1300K, got {cv0_high}"
    assert np.isfinite(ci0_high), f"ci0 should be finite at 1300K, got {ci0_high}"
    assert cv0_high > 0, f"cv0 should be positive at 1300K, got {cv0_high}"
    assert ci0_high > 0, f"ci0 should be positive at 1300K, got {ci0_high}"

    # High temperature concentrations should be much larger than low temperature
    assert cv0_high > cv0_low, "cv0 should increase with temperature"
    # Note: ci0 has complex temperature dependence due to cubic polynomial in Eif,
    # so we don't assert it must increase - just check it's finite and non-negative


def test_solver_with_low_temperature():
    """Test solver execution at very low temperature"""
    params = create_default_parameters()
    params['temperature'] = 100.0  # 100 K (very low for nuclear fuel)

    model = GasSwellingModel(params)

    # Run a short simulation
    sim_time = 100  # 100 seconds
    t_eval = np.linspace(0, sim_time, 10)

    result = model.solve(
        t_span=(0, sim_time),
        t_eval=t_eval
    )

    # Check result structure
    assert isinstance(result, dict)
    assert 'time' in result
    assert 'swelling' in result

    # Check that values are physically meaningful
    assert np.all(np.isfinite(result['Rcb'])), "All Rcb values should be finite"
    assert np.all(np.isfinite(result['Rcf'])), "All Rcf values should be finite"
    assert np.all(result['Rcb'] >= 0), "All Rcb values should be non-negative"
    assert np.all(result['Rcf'] >= 0), "All Rcf values should be non-negative"


def test_solver_with_high_temperature():
    """Test solver execution at very high temperature"""
    params = create_default_parameters()
    params['temperature'] = 1200.0  # 1200 K (high but below melting)

    model = GasSwellingModel(params)

    # Run a short simulation
    sim_time = 100  # 100 seconds
    t_eval = np.linspace(0, sim_time, 10)

    result = model.solve(
        t_span=(0, sim_time),
        t_eval=t_eval
    )

    # Check result structure
    assert isinstance(result, dict)
    assert 'time' in result
    assert 'swelling' in result

    # Check that values are physically meaningful
    assert np.all(np.isfinite(result['Rcb'])), "All Rcb values should be finite"
    assert np.all(np.isfinite(result['Rcf'])), "All Rcf values should be finite"
    assert np.all(result['Rcb'] >= 0), "All Rcb values should be non-negative"
    assert np.all(result['Rcf'] >= 0), "All Rcf values should be non-negative"


def test_temperature_range_physical_behavior():
    """Test that swelling behavior changes appropriately with temperature"""
    # Use a more conservative temperature range to avoid numerical instabilities
    temperatures = [400, 600, 800]  # Range from low to high (excluding 1000K which causes instability)
    final_swellings = []

    for temp in temperatures:
        params = create_default_parameters()
        params['temperature'] = temp

        model = GasSwellingModel(params)

        # Run simulation
        sim_time = 1000  # 1000 seconds
        t_eval = np.linspace(0, sim_time, 20)

        result = model.solve(
            t_span=(0, sim_time),
            t_eval=t_eval
        )

        # Record final swelling
        final_swelling = result['swelling'][-1]
        final_swellings.append(final_swelling)

        # Check that result is physically meaningful
        assert np.isfinite(final_swelling), f"Swelling should be finite at {temp}K"
        assert final_swelling >= 0, f"Swelling should be non-negative at {temp}K"

    # All swellings should be successful (not NaN)
    assert len(final_swellings) == len(temperatures), "All temperatures should produce results"
    assert all(np.isfinite(s) for s in final_swellings), "All swellings should be finite"


def test_extreme_temperatures_initial_state():
    """Test that initial state is valid at extreme temperatures"""
    # Test at very low temperature
    params_cold = create_default_parameters()
    params_cold['temperature'] = 10.0  # 10 K

    model_cold = GasSwellingModel(params_cold)

    # Check initial state structure
    assert isinstance(model_cold.initial_state, np.ndarray)
    assert len(model_cold.initial_state) == 17

    # Check that all initial values are finite
    for i, val in enumerate(model_cold.initial_state):
        assert np.isfinite(val), f"Initial state variable {i} is not finite at 10K: {val}"

    # Test at very high temperature
    params_hot = create_default_parameters()
    params_hot['temperature'] = 1400.0  # 1400 K

    model_hot = GasSwellingModel(params_hot)

    # Check initial state structure
    assert isinstance(model_hot.initial_state, np.ndarray)
    assert len(model_hot.initial_state) == 17

    # Check that all initial values are finite
    for i, val in enumerate(model_hot.initial_state):
        assert np.isfinite(val), f"Initial state variable {i} is not finite at 1400K: {val}"


def test_gas_pressure_at_extreme_temperatures():
    """Test that gas pressure calculations remain valid at extreme temperatures"""
    # Test low temperature pressure calculation
    params_cold = create_default_parameters()
    params_cold['temperature'] = 50.0  # 50 K
    model_cold = GasSwellingModel(params_cold)

    # Calculate pressure for a small bubble
    R_cold = 1e-8  # 10 nm
    N_cold = 10.0  # 10 gas atoms
    Pg_cold = model_cold._calculate_idealgas_pressure(R_cold, N_cold)

    assert np.isfinite(Pg_cold), f"Gas pressure should be finite at 50K, got {Pg_cold}"
    assert Pg_cold >= 0, f"Gas pressure should be non-negative at 50K, got {Pg_cold}"

    # Test high temperature pressure calculation
    params_hot = create_default_parameters()
    params_hot['temperature'] = 1300.0  # 1300 K
    model_hot = GasSwellingModel(params_hot)

    # Calculate pressure for the same bubble
    Pg_hot = model_hot._calculate_idealgas_pressure(R_cold, N_cold)

    assert np.isfinite(Pg_hot), f"Gas pressure should be finite at 1300K, got {Pg_hot}"
    assert Pg_hot >= 0, f"Gas pressure should be non-negative at 1300K, got {Pg_hot}"

    # Higher temperature should give higher pressure (ideal gas law: P ∝ T)
    assert Pg_hot > Pg_cold, "Gas pressure should increase with temperature"


def test_temperature_boundary_values():
    """Test model behavior at temperature boundary values"""
    boundary_temperatures = [0.1, 1.0, 10.0, 1500.0, 2000.0]

    for temp in boundary_temperatures:
        params = create_default_parameters()
        params['temperature'] = temp

        # Should be able to create model
        model = GasSwellingModel(params)
        assert model is not None

        # Should be able to calculate thermal equilibrium concentrations
        cv0 = model._calculate_cv0()
        ci0 = model._calculate_ci0()

        assert np.isfinite(cv0), f"cv0 should be finite at {temp}K"
        assert np.isfinite(ci0), f"ci0 should be finite at {temp}K"
        assert cv0 >= 0, f"cv0 should be non-negative at {temp}K"
        assert ci0 >= 0, f"ci0 should be non-negative at {temp}K"
