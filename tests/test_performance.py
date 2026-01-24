"""
Performance and benchmark tests for gas_swelling package
"""

import pytest
import time
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


def test_solver_performance():
    """Test that solver execution completes within acceptable time bounds"""
    # Create default parameters
    params = create_default_parameters()

    # Create model
    model = GasSwellingModel(params)

    # Define test parameters for performance measurement
    # Use moderate simulation time for quick but meaningful performance test
    sim_time = 1000  # seconds
    t_eval = np.linspace(0, sim_time, 50)

    # Measure solver execution time
    start_time = time.time()
    result = model.solve(
        t_span=(0, sim_time),
        t_eval=t_eval
    )
    execution_time = time.time() - start_time

    # Verify solver completed successfully
    assert result is not None
    assert isinstance(result, dict)
    assert 'time' in result

    # Performance assertion: should complete within 30 seconds
    # This is a generous timeout to account for CI/CD variability
    assert execution_time < 30.0, (
        f"Solver took {execution_time:.2f} seconds, "
        f"expected < 30.0 seconds"
    )

    # Verify results are valid despite performance focus
    assert len(result['time']) == len(t_eval)
    assert np.all(np.isfinite(result['Rcb']))
    assert np.all(np.isfinite(result['Rcf']))
    assert np.all(result['Rcb'] >= 0)
    assert np.all(result['Rcf'] >= 0)


def test_solver_performance_with_different_time_scales():
    """Test solver performance across different time scales"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Test three different time scales
    time_scales = [
        (100, 20),   # Short simulation
        (1000, 50),  # Medium simulation
        (5000, 100)  # Longer simulation
    ]

    for sim_time, num_points in time_scales:
        t_eval = np.linspace(0, sim_time, num_points)

        start_time = time.time()
        result = model.solve(
            t_span=(0, sim_time),
            t_eval=t_eval
        )
        execution_time = time.time() - start_time

        # Verify completion
        assert result is not None
        assert isinstance(result, dict)

        # Performance should scale reasonably with simulation time
        # Allow up to 60 seconds for the longest simulation
        max_allowed_time = min(sim_time / 100, 60.0)
        assert execution_time < max_allowed_time, (
            f"Solver took {execution_time:.2f} seconds for {sim_time}s simulation, "
            f"expected < {max_allowed_time:.2f} seconds"
        )

        # Verify results are valid
        assert len(result['time']) == num_points
        assert np.all(np.isfinite(result['Rcb']))
        assert np.all(np.isfinite(result['Rcf']))


def test_solver_performance_with_repeated_runs():
    """Test solver performance consistency across multiple runs"""
    params = create_default_parameters()

    # Run solver multiple times to measure consistency
    num_runs = 3
    execution_times = []

    for _ in range(num_runs):
        model = GasSwellingModel(params)
        sim_time = 1000
        t_eval = np.linspace(0, sim_time, 50)

        start_time = time.time()
        result = model.solve(
            t_span=(0, sim_time),
            t_eval=t_eval
        )
        execution_time = time.time() - start_time

        execution_times.append(execution_time)

        # Verify each run completed successfully
        assert result is not None
        assert isinstance(result, dict)

    # Check that performance is relatively consistent
    # (coefficient of variation should be < 50%)
    mean_time = np.mean(execution_times)
    std_time = np.std(execution_times)
    cv = std_time / mean_time if mean_time > 0 else 0

    assert cv < 0.5, (
        f"Solver performance inconsistent: "
        f"mean={mean_time:.2f}s, std={std_time:.2f}s, CV={cv:.2%}"
    )

    # All runs should complete within reasonable time
    assert mean_time < 30.0, (
        f"Average solver time {mean_time:.2f}s exceeds 30.0 seconds"
    )


def test_solver_performance_with_temperature_variation():
    """Test solver performance across different temperature conditions"""
    temperatures = [600, 700, 800]  # K

    for temp in temperatures:
        params = create_default_parameters()
        params['temperature'] = temp

        model = GasSwellingModel(params)
        sim_time = 1000
        t_eval = np.linspace(0, sim_time, 50)

        start_time = time.time()
        result = model.solve(
            t_span=(0, sim_time),
            t_eval=t_eval
        )
        execution_time = time.time() - start_time

        # Verify completion
        assert result is not None
        assert isinstance(result, dict)

        # Performance should be reasonable regardless of temperature
        assert execution_time < 30.0, (
            f"Solver at {temp}K took {execution_time:.2f} seconds, "
            f"expected < 30.0 seconds"
        )

        # Verify temperature-specific results are valid
        assert np.all(np.isfinite(result['Rcb']))
        assert np.all(np.isfinite(result['Rcf']))
        assert result['time'][-1] == sim_time


@pytest.mark.parametrize("sim_time,expected_max_time", [
    (100, 5.0),    # Very short simulation
    (1000, 30.0),  # Medium simulation
    (5000, 60.0),  # Longer simulation
])
def test_scalability(sim_time, expected_max_time):
    """Test solver performance scalability with problem size"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Adjust number of time points proportionally
    num_points = max(20, min(100, sim_time // 50))
    t_eval = np.linspace(0, sim_time, num_points)

    start_time = time.time()
    result = model.solve(
        t_span=(0, sim_time),
        t_eval=t_eval
    )
    execution_time = time.time() - start_time

    # Verify completion
    assert result is not None
    assert isinstance(result, dict)
    assert 'time' in result

    # Performance assertion
    assert execution_time < expected_max_time, (
        f"Solver for {sim_time}s simulation took {execution_time:.2f} seconds, "
        f"expected < {expected_max_time:.2f} seconds"
    )

    # Verify result quality
    assert len(result['time']) == num_points
    assert np.all(np.isfinite(result['Rcb']))
    assert np.all(np.isfinite(result['Rcf']))
    assert result['time'][-1] <= sim_time * 1.01  # Allow 1% tolerance
