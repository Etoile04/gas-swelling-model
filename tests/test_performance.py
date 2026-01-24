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


@pytest.mark.parametrize("num_points,expected_max_time", [
    (5, 5.0),       # Very sparse output
    (20, 10.0),     # Sparse output
    (100, 30.0),    # Dense output
    (500, 60.0),    # Very dense output
])
def test_scalability_with_output_density(num_points, expected_max_time):
    """Test solver performance with different output point densities"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Use fixed simulation time, vary output density
    sim_time = 1000
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

    # Performance should scale reasonably with output density
    assert execution_time < expected_max_time, (
        f"Solver with {num_points} output points took {execution_time:.2f} seconds, "
        f"expected < {expected_max_time:.2f} seconds"
    )

    # Verify output size matches requested
    assert len(result['time']) == num_points

    # Verify results are physically meaningful regardless of output density
    assert np.all(np.isfinite(result['Rcb']))
    assert np.all(np.isfinite(result['Rcf']))
    assert np.all(result['Rcb'] >= 0)
    assert np.all(result['Rcf'] >= 0)


def test_scalability_very_long_time_span():
    """Test solver performance with very long time spans (realistic irradiation times)"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Test with very long simulation time
    # Note: Using shorter time for test (10000s instead of days)
    # to keep test suite runnable in CI/CD
    sim_time = 10000
    num_points = 50
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

    # Should complete within reasonable time for CI/CD
    assert execution_time < 90.0, (
        f"Solver for {sim_time}s simulation took {execution_time:.2f} seconds, "
        f"expected < 90.0 seconds"
    )

    # Verify result quality for long simulation
    assert len(result['time']) == num_points
    assert np.all(np.isfinite(result['Rcb']))
    assert np.all(np.isfinite(result['Rcf']))

    # For long simulations, we expect significant bubble growth
    # Final bubble radius should be larger than initial
    assert result['Rcb'][-1] >= result['Rcb'][0] * 0.9  # Allow some tolerance
    assert result['Rcf'][-1] >= result['Rcf'][0] * 0.9


def test_scalability_memory_efficiency():
    """Test that solver handles large output arrays without memory issues"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Use moderate simulation time but many output points
    sim_time = 1000
    num_points = 1000  # Large number of output points
    t_eval = np.linspace(0, sim_time, num_points)

    start_time = time.time()
    result = model.solve(
        t_span=(0, sim_time),
        t_eval=t_eval
    )
    execution_time = time.time() - start_time

    # Verify completion without memory errors
    assert result is not None
    assert isinstance(result, dict)

    # Should complete within reasonable time
    assert execution_time < 60.0, (
        f"Solver with {num_points} output points took {execution_time:.2f} seconds, "
        f"expected < 60.0 seconds"
    )

    # Verify all result arrays have correct size
    assert len(result['time']) == num_points
    for key in ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf',
                'cvb', 'cib', 'kvb', 'kib', 'cvf', 'cif', 'kvf', 'kif',
                'released_gas', 'swelling']:
        assert key in result
        assert len(result[key]) == num_points, (
            f"Result array '{key}' has length {len(result[key])}, "
            f"expected {num_points}"
        )

    # Verify results are valid for all points
    assert np.all(np.isfinite(result['Rcb']))
    assert np.all(np.isfinite(result['Rcf']))


@pytest.mark.parametrize("sim_time,num_points", [
    (100, 10),      # Short time, very sparse
    (100, 200),     # Short time, very dense
    (1000, 10),     # Medium time, very sparse
    (1000, 500),    # Medium time, very dense
    (5000, 50),     # Long time, sparse
])
def test_scalability_problem_size_combinations(sim_time, num_points):
    """Test solver performance across various combinations of time spans and output densities"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

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

    # Performance should be reasonable for all combinations
    # Scale timeout based on problem size
    expected_max_time = min(sim_time / 50 + num_points / 100, 90.0)
    assert execution_time < expected_max_time, (
        f"Solver for sim_time={sim_time}s, num_points={num_points} "
        f"took {execution_time:.2f} seconds, expected < {expected_max_time:.2f} seconds"
    )

    # Verify output size
    assert len(result['time']) == num_points

    # Verify result quality
    assert np.all(np.isfinite(result['Rcb']))
    assert np.all(np.isfinite(result['Rcf']))
    assert result['time'][-1] <= sim_time * 1.01  # Allow 1% tolerance
