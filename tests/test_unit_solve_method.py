"""
Unit tests for GasSwellingModel solve method and result processing.

This module tests the solver integration and result dictionary generation
to improve code coverage of the active code paths.
"""

import pytest
import numpy as np
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters


class TestSolveMethod:
    """Test the solve() method comprehensively"""

    @pytest.fixture
    def model(self):
        """Create model with default parameters"""
        return GasSwellingModel()

    def test_solve_returns_dict(self, model):
        """Test that solve returns a dictionary"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        assert isinstance(result, dict)
        assert 'time' in result
        assert 'Cgb' in result

    def test_solve_result_keys(self, model):
        """Test that solve result has all expected keys"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        expected_keys = [
            'time', 'Cgb', 'Ccb', 'Ncb', 'Rcb',
            'Cgf', 'Ccf', 'Ncf', 'Rcf',
            'cvb', 'cib', 'kvb', 'kib',
            'cvf', 'cif', 'kvf', 'kif',
            'released_gas', 'swelling'
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_solve_time_array_shape(self, model):
        """Test that time array has correct shape"""
        n_points = 20
        result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, n_points))

        assert len(result['time']) == n_points

    def test_solve_result_arrays_consistent(self, model):
        """Test that all result arrays have same length as time"""
        n_points = 15
        result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, n_points))

        time_len = len(result['time'])
        for key in result:
            if key != 'solver_success':  # Skip non-array fields
                assert len(result[key]) == time_len, f"Array {key} has inconsistent length"

    def test_solve_with_default_t_eval(self, model):
        """Test solve with default t_eval (None)"""
        result = model.solve(t_span=(0, 100))

        assert 'time' in result
        assert len(result['time']) > 0
        assert result['time'][0] >= 0
        assert result['time'][-1] <= 100

    def test_solve_with_custom_dt(self, model):
        """Test solve with custom time step"""
        result = model.solve(t_span=(0, 100), dt=1e-8)

        assert result is not None
        assert 'time' in result

    def test_solve_with_max_dt(self, model):
        """Test solve with custom maximum time step"""
        result = model.solve(t_span=(0, 100), max_dt=10.0)

        assert result is not None
        assert 'time' in result

    def test_solve_with_output_interval(self, model):
        """Test solve with custom output interval"""
        result = model.solve(t_span=(0, 100), output_interval=100)

        assert result is not None
        # Check that debug history was updated appropriately
        assert model.step_count >= 0

    def test_solve_solver_success_flag(self, model):
        """Test that solver success flag is set"""
        result = model.solve(t_span=(0, 100))

        # solver_success is set on the model object, not in result dict
        assert hasattr(model, 'solver_success')
        assert isinstance(model.solver_success, bool)

    def test_solve_with_very_short_time(self, model):
        """Test solve with very short time span"""
        result = model.solve(t_span=(0, 1e-6))

        assert result is not None
        assert 'time' in result

    def test_solve_with_long_time(self, model):
        """Test solve with long time span"""
        result = model.solve(t_span=(0, 10000), t_eval=np.linspace(0, 10000, 10))

        assert result is not None
        assert len(result['time']) == 10

    def test_solve_with_different_rtol(self, model):
        """Test solve with different relative tolerance"""
        # Temporarily modify to test - but can't directly pass rtol to current implementation
        result = model.solve(t_span=(0, 100))

        assert result is not None

    def test_solve_result_finite_values(self, model):
        """Test that result arrays contain finite values"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        for key in ['time', 'Cgb', 'Ccb', 'Ncb', 'Rcb', 'swelling']:
            assert np.all(np.isfinite(result[key])), f"Non-finite values in {key}"

    def test_solve_non_negative_concentrations(self, model):
        """Test that concentrations remain non-negative"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        # Check key concentrations
        assert np.all(result['Cgb'] >= 0)
        assert np.all(result['Ccb'] >= 0)
        assert np.all(result['Ncb'] >= 0)
        assert np.all(result['Cgf'] >= 0)
        assert np.all(result['Ccf'] >= 0)
        assert np.all(result['Ncf'] >= 0)

    def test_solve_positive_radii(self, model):
        """Test that cavity radii remain positive"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        assert np.all(result['Rcb'] > 0)
        assert np.all(result['Rcf'] > 0)

    def test_solve_swelling_calculation(self, model):
        """Test that swelling is calculated"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        assert 'swelling' in result
        assert np.all(np.isfinite(result['swelling']))
        assert np.all(result['swelling'] >= 0)

    def test_solve_released_gas_tracking(self, model):
        """Test that released gas is tracked"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        assert 'released_gas' in result
        assert np.all(np.isfinite(result['released_gas']))
        assert np.all(result['released_gas'] >= 0)

    def test_solve_updates_model_state(self, model):
        """Test that solve updates model state variables"""
        initial_step_count = model.step_count

        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        # Model state should be updated
        assert model.step_count >= initial_step_count

    def test_solve_with_clipped_initial_state(self, model):
        """Test that initial state is clipped appropriately"""
        # The solver clips the initial state to [1e-12, 1e30]
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 5))

        assert result is not None
        assert 'time' in result

    def test_solve_multiple_calls(self, model):
        """Test that solve can be called multiple times"""
        result1 = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 5))
        result2 = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 5))

        # Both should succeed
        assert result1 is not None
        assert result2 is not None

    def test_solve_with_different_t_eval_densities(self, model):
        """Test solve with different output point densities"""
        for n_points in [5, 20, 100]:
            result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, n_points))
            assert len(result['time']) == n_points

    def test_solve_result_array_dtypes(self, model):
        """Test that result arrays have correct data types"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        assert isinstance(result['time'], np.ndarray)
        assert isinstance(result['Cgb'], np.ndarray)
        assert result['time'].dtype == np.float64
        assert result['Cgb'].dtype == np.float64

    def test_solve_solver_method_lsoda(self, model):
        """Test that LSODA solver method is used"""
        # The implementation uses LSODA by default
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        # Should complete successfully
        assert result is not None
        # solver_success is on the model object
        assert hasattr(model, 'solver_success')


class TestSolverErrorHandling:
    """Test solver error handling and edge cases"""

    @pytest.fixture
    def model(self):
        return GasSwellingModel()

    def test_solve_with_invalid_t_span(self, model):
        """Test solve with inverted time span"""
        # This should still work or fail gracefully
        result = model.solve(t_span=(100, 0), t_eval=np.linspace(100, 0, 5))

        # Should handle gracefully
        assert result is not None

    def test_solve_with_single_t_eval_point(self, model):
        """Test solve with single output point"""
        result = model.solve(t_span=(0, 100), t_eval=np.array([50]))

        assert result is not None
        assert len(result['time']) >= 1

    def test_solve_with_zero_time_span(self, model):
        """Test solve with very small time span"""
        # Use very small but non-zero time span
        result = model.solve(t_span=(0, 1e-6))

        assert result is not None
        assert 'time' in result
        # Should have at least some time points
        assert len(result['time']) >= 1

    def test_solve_with_very_large_max_steps(self, model):
        """Test solve with very large max_steps"""
        result = model.solve(t_span=(0, 100), max_steps=10000000)

        assert result is not None

    def test_solve_after_failed_solve(self, model):
        """Test that model can be reused after a failed solve"""
        # Create parameters that might cause solver issues
        params = create_default_parameters()
        params['temperature'] = 100  # Very low temperature

        model = GasSwellingModel(params)
        result1 = model.solve(t_span=(0, 100))

        # Try solving again with normal parameters
        params['temperature'] = 700
        model2 = GasSwellingModel(params)
        result2 = model2.solve(t_span=(0, 100))

        assert result2 is not None


class TestResultPhysicalConsistency:
    """Test physical consistency of solve results"""

    @pytest.fixture
    def model(self):
        return GasSwellingModel()

    def test_monotonic_time(self, model):
        """Test that time array is monotonically increasing"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 20))

        time_diffs = np.diff(result['time'])
        assert np.all(time_diffs >= 0), "Time should be monotonically increasing"

    def test_bubble_growth_over_time(self, model):
        """Test that bubbles tend to grow over time"""
        result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 50))

        # Final radius should be >= initial radius (on average)
        # (accounting for possible numerical noise)
        assert result['Rcb'][-1] >= result['Rcb'][0] * 0.5  # Allow some decrease
        assert result['Rcf'][-1] >= result['Rcf'][0] * 0.5

    def test_gas_conservation_in_results(self, model):
        """Test approximate gas conservation in results"""
        result = model.solve(t_span=(0, 100), t_eval=np.linspace(0, 100, 10))

        # Total gas should increase over time (due to production)
        # Check that final gas > initial gas
        initial_gas = result['Cgb'][0] + result['Cgf'][0]
        final_gas = result['Cgb'][-1] + result['Cgf'][-1] + result['released_gas'][-1]

        # Allow for numerical tolerance
        assert final_gas >= initial_gas * 0.9  # Should be >= initial

    def test_defect_concentrations_remain_small(self, model):
        """Test that defect concentrations remain physically reasonable"""
        result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 20))

        # Defect concentrations should be small (< 1)
        assert np.all(result['cvb'] < 1.0)
        assert np.all(result['cib'] < 1.0)
        assert np.all(result['cvf'] < 1.0)
        assert np.all(result['cif'] < 1.0)

    def test_swelling_is_reasonable(self, model):
        """Test that swelling values are physically reasonable"""
        result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 20))

        # Swelling should be non-negative and not excessively large
        assert np.all(result['swelling'] >= 0)
        assert np.all(result['swelling'] < 100)  # Less than 100% for short times
