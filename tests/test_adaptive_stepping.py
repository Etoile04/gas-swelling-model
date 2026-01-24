"""
Test adaptive solver components

This module tests the AdaptiveSolver class and its methods,
including error estimation, step size control, and integration methods.
"""

import pytest
import numpy as np
from gas_swelling.models.adaptive_solver import AdaptiveSolver


class TestAdaptiveSolverImport:
    """Test importing and basic setup of AdaptiveSolver"""

    def test_import_adaptive_solver(self):
        """Test that AdaptiveSolver can be imported"""
        from gas_swelling.models.adaptive_solver import AdaptiveSolver
        assert AdaptiveSolver is not None

    def test_adaptive_solver_is_class(self):
        """Test that AdaptiveSolver is a class"""
        from gas_swelling.models.adaptive_solver import AdaptiveSolver
        assert isinstance(AdaptiveSolver, type)


class TestAdaptiveSolverInitialization:
    """Test AdaptiveSolver initialization and validation"""

    def test_basic_initialization(self):
        """Test basic solver initialization with minimal parameters"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0])
        )
        assert solver.fun == simple_ode
        assert solver.t_start == 0
        assert solver.t_end == 10
        assert np.array_equal(solver.y0, np.array([1.0]))

    def test_default_parameters(self):
        """Test that default parameters are set correctly"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0])
        )
        assert solver.rtol == 1e-4
        assert solver.atol == 1e-6
        assert solver.min_step == 1e-12
        assert solver.max_step == 100.0
        assert solver.safety_factor == 0.9
        assert solver.method == 'RK23'

    def test_custom_parameters(self):
        """Test initialization with custom parameters"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            rtol=1e-5,
            atol=1e-8,
            min_step=1e-10,
            max_step=50.0,
            safety_factor=0.8,
            method='RK45'
        )
        assert solver.rtol == 1e-5
        assert solver.atol == 1e-8
        assert solver.min_step == 1e-10
        assert solver.max_step == 50.0
        assert solver.safety_factor == 0.8
        assert solver.method == 'RK45'

    def test_invalid_t_span_raises_error(self):
        """Test that invalid t_span raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="t_span\\[0\\] must be less than t_span\\[1\\]"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(10, 0),  # Invalid: t_start > t_end
                y0=np.array([1.0])
            )

    def test_invalid_rtol_raises_error(self):
        """Test that non-positive rtol raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="rtol must be positive"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(0, 10),
                y0=np.array([1.0]),
                rtol=0  # Invalid: rtol must be positive
            )

    def test_invalid_atol_raises_error(self):
        """Test that non-positive atol raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="atol must be positive"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(0, 10),
                y0=np.array([1.0]),
                atol=-1e-6  # Invalid: atol must be positive
            )

    def test_invalid_min_step_raises_error(self):
        """Test that non-positive min_step raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="min_step must be positive"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(0, 10),
                y0=np.array([1.0]),
                min_step=0  # Invalid: min_step must be positive
            )

    def test_invalid_max_step_raises_error(self):
        """Test that max_step less than min_step raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="max_step must be greater than min_step"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(0, 10),
                y0=np.array([1.0]),
                min_step=1.0,
                max_step=0.5  # Invalid: max_step < min_step
            )

    def test_invalid_safety_factor_raises_error(self):
        """Test that safety_factor outside (0, 1) raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="safety_factor must be in \\(0, 1\\)"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(0, 10),
                y0=np.array([1.0]),
                safety_factor=1.5  # Invalid: safety_factor > 1
            )

    def test_invalid_method_raises_error(self):
        """Test that invalid method raises ValueError"""

        def simple_ode(t, y):
            return -y

        with pytest.raises(ValueError, match="method must be 'RK23' or 'RK45'"):
            AdaptiveSolver(
                fun=simple_ode,
                t_span=(0, 10),
                y0=np.array([1.0]),
                method='RK78'  # Invalid method
            )

    def test_statistics_initialization(self):
        """Test that statistics are initialized to zero"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0])
        )
        assert solver.n_steps == 0
        assert solver.n_accepted == 0
        assert solver.n_rejected == 0
        assert solver.last_step_size is None


class TestInitialStepEstimation:
    """Test initial step size estimation"""

    def test_estimate_initial_step_nonzero_derivative(self):
        """Test initial step estimation with non-zero derivative"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            atol=1e-6,
            rtol=1e-4
        )
        dt = solver._estimate_initial_step(0.0, np.array([1.0]))
        assert dt > 0
        assert solver.min_step <= dt <= solver.max_step

    def test_estimate_initial_step_zero_derivative(self):
        """Test initial step estimation with zero derivative"""

        def constant_ode(t, y):
            return np.zeros_like(y)

        solver = AdaptiveSolver(
            fun=constant_ode,
            t_span=(0, 10),
            y0=np.array([1.0])
        )
        dt = solver._estimate_initial_step(0.0, np.array([1.0]))
        assert dt > 0
        # With zero derivative, should use conservative step (max_step)
        assert dt == solver.max_step

    def test_estimate_initial_step_clipping(self):
        """Test that estimated step is clipped to [min_step, max_step]"""

        def fast_ode(t, y):
            return -1e10 * y  # Very fast dynamics

        solver = AdaptiveSolver(
            fun=fast_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            min_step=1e-3,
            max_step=1.0
        )
        dt = solver._estimate_initial_step(0.0, np.array([1.0]))
        assert solver.min_step <= dt <= solver.max_step


class TestRK23StepMethod:
    """Test RK23 integration step method"""

    def test_rk23_step_basic(self):
        """Test basic RK23 step"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0])
        )
        y_new, y_error = solver._rk23_step(0.0, np.array([1.0]), 0.1)

        # Check that solution is returned
        assert isinstance(y_new, np.ndarray)
        assert isinstance(y_error, np.ndarray)
        assert y_new.shape == (1,)
        assert y_error.shape == (1,)

    def test_rk23_step_multiple_variables(self):
        """Test RK23 step with multiple variables"""

        def coupled_ode(t, y):
            return np.array([-y[0], y[1]])

        solver = AdaptiveSolver(
            fun=coupled_ode,
            t_span=(0, 10),
            y0=np.array([1.0, 1.0])
        )
        y_new, y_error = solver._rk23_step(0.0, np.array([1.0, 1.0]), 0.1)

        # Check that solution is returned
        assert y_new.shape == (2,)
        assert y_error.shape == (2,)


class TestRK45StepMethod:
    """Test RK45 integration step method"""

    def test_rk45_step_basic(self):
        """Test basic RK45 step"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0])
        )
        y_new, y_error = solver._rk45_step(0.0, np.array([1.0]), 0.1)

        # Check that solution is returned
        assert isinstance(y_new, np.ndarray)
        assert isinstance(y_error, np.ndarray)
        assert y_new.shape == (1,)
        assert y_error.shape == (1,)

    def test_rk45_step_multiple_variables(self):
        """Test RK45 step with multiple variables"""

        def coupled_ode(t, y):
            return np.array([-y[0], y[1]])

        solver = AdaptiveSolver(
            fun=coupled_ode,
            t_span=(0, 10),
            y0=np.array([1.0, 1.0])
        )
        y_new, y_error = solver._rk45_step(0.0, np.array([1.0, 1.0]), 0.1)

        # Check that solution is returned
        assert y_new.shape == (2,)
        assert y_error.shape == (2,)


class TestErrorComputation:
    """Test error norm computation"""

    def test_compute_error_norm_basic(self):
        """Test basic error norm computation"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            rtol=1e-4,
            atol=1e-6
        )
        y_error = np.array([1e-5])
        y = np.array([1.0])
        error_norm = solver._compute_error_norm(y_error, y)

        assert error_norm >= 0
        assert isinstance(error_norm, float)

    def test_compute_error_norm_multiple_variables(self):
        """Test error norm computation with multiple variables"""

        def coupled_ode(t, y):
            return np.array([-y[0], y[1]])

        solver = AdaptiveSolver(
            fun=coupled_ode,
            t_span=(0, 10),
            y0=np.array([1.0, 1.0])
        )
        y_error = np.array([1e-5, 1e-6])
        y = np.array([1.0, 1.0])
        error_norm = solver._compute_error_norm(y_error, y)

        assert error_norm >= 0
        assert isinstance(error_norm, float)


class TestStepSizeAdjustment:
    """Test step size adjustment logic"""

    def test_adjust_step_size_zero_error(self):
        """Test step size adjustment with zero error"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            safety_factor=0.9
        )
        dt_new = solver._adjust_step_size(0.1, 0.0)

        # With zero error, step size should increase
        assert dt_new > 0.1
        assert dt_new <= solver.max_step

    def test_adjust_step_size_small_error(self):
        """Test step size adjustment with small error"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            safety_factor=0.9
        )
        dt_new = solver._adjust_step_size(0.1, 0.5)

        # With error < 1, step size should increase modestly
        assert dt_new >= 0.1

    def test_adjust_step_size_large_error(self):
        """Test step size adjustment with large error"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            safety_factor=0.9
        )
        dt_new = solver._adjust_step_size(0.1, 2.0)

        # With error > 1, step size should decrease
        assert dt_new < 0.1
        assert dt_new >= solver.min_step

    def test_adjust_step_size_clipping(self):
        """Test that adjusted step size is clipped to [min_step, max_step]"""

        def simple_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=simple_ode,
            t_span=(0, 10),
            y0=np.array([1.0]),
            min_step=1e-3,
            max_step=1.0
        )
        # Very small error should try to increase step
        dt_new = solver._adjust_step_size(0.5, 0.01)
        assert solver.min_step <= dt_new <= solver.max_step

        # Very large error should try to decrease step
        dt_new = solver._adjust_step_size(0.5, 100.0)
        assert solver.min_step <= dt_new <= solver.max_step


class TestSolverIntegration:
    """Test full solver integration"""

    def test_solve_simple_decay_rk23(self):
        """Test solving simple decay equation with RK23"""

        def decay_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0]),
            method='RK23',
            show_progress=False
        )
        result = solver.solve()

        # Check result structure
        assert 'time' in result
        assert 'y' in result
        assert 'success' in result
        assert 'message' in result
        assert 'n_steps' in result
        assert 'n_accepted' in result
        assert 'n_rejected' in result

        # Check that solution was computed
        assert result['success'] is True
        assert len(result['time']) > 0
        assert len(result['y']) > 0
        assert result['time'][-1] >= solver.t_end

    def test_solve_simple_decay_rk45(self):
        """Test solving simple decay equation with RK45"""

        def decay_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0]),
            method='RK45',
            show_progress=False
        )
        result = solver.solve()

        # Check result structure
        assert result['success'] is True
        assert len(result['time']) > 0
        assert len(result['y']) > 0
        assert result['time'][-1] >= solver.t_end

    def test_solve_coupled_equations(self):
        """Test solving coupled ODEs"""

        def coupled_ode(t, y):
            # y[0] decays, y[1] grows
            return np.array([-y[0], y[1]])

        solver = AdaptiveSolver(
            fun=coupled_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0, 1.0]),
            method='RK23',
            show_progress=False
        )
        result = solver.solve()

        # Check that solution was computed
        assert result['success'] is True
        assert result['y'].shape[1] == 2  # Two variables
        assert result['time'][-1] >= solver.t_end

    def test_solve_with_t_eval(self):
        """Test solving with specific output time points"""

        def decay_ode(t, y):
            return -y

        t_eval = np.linspace(0, 1.0, 11)
        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0]),
            show_progress=False
        )
        result = solver.solve(t_eval=t_eval)

        # Check that output is at requested time points
        assert len(result['time']) == len(t_eval)
        assert np.allclose(result['time'], t_eval)

    def test_solve_statistics_tracking(self):
        """Test that solve correctly tracks statistics"""

        def decay_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0]),
            show_progress=False
        )
        result = solver.solve()

        # Check statistics
        assert result['n_steps'] == solver.n_steps
        assert result['n_accepted'] == solver.n_accepted
        assert result['n_rejected'] == solver.n_rejected
        assert result['n_accepted'] + result['n_rejected'] == result['n_steps']
        assert result['n_accepted'] > 0  # At least some steps should be accepted
        assert solver.last_step_size is not None

    def test_solution_accuracy_simple_decay(self):
        """Test that solution is reasonably accurate for simple decay"""

        def decay_ode(t, y):
            return -y

        # Exact solution: y(t) = y0 * exp(-t)
        t_end = 1.0
        y0 = 1.0

        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, t_end),
            y0=np.array([y0]),
            rtol=1e-6,
            atol=1e-8,
            show_progress=False
        )
        result = solver.solve()

        # Check final value against exact solution
        y_exact = y0 * np.exp(-t_end)
        y_computed = result['y'][-1, 0]

        # Should be within 0.1% of exact solution
        relative_error = abs(y_computed - y_exact) / y_exact
        assert relative_error < 1e-3

    def test_solve_stiff_system(self):
        """Test solving a stiff system (fast and slow dynamics)"""

        def stiff_ode(t, y):
            # Fast mode: -1000*y[0], Slow mode: -y[1]
            return np.array([-1000.0 * y[0], -y[1]])

        solver = AdaptiveSolver(
            fun=stiff_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0, 1.0]),
            method='RK23',
            min_step=1e-12,
            max_step=1.0,
            show_progress=False
        )
        result = solver.solve()

        # Check that solution was computed
        assert result['success'] is True
        assert result['y'].shape[1] == 2
        assert result['time'][-1] >= solver.t_end

    def test_solve_with_custom_first_step(self):
        """Test solving with custom initial step size"""

        def decay_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0]),
            first_step=0.01,
            show_progress=False
        )
        result = solver.solve()

        # Check that solution was computed
        assert result['success'] is True
        assert result['n_accepted'] > 0


class TestInterpolation:
    """Test result interpolation"""

    def test_interpolate_results(self):
        """Test interpolation of results to requested time points"""

        def decay_ode(t, y):
            return -y

        solver = AdaptiveSolver(
            fun=decay_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0]),
            show_progress=False
        )

        # Create some dummy computed results
        t_computed = np.array([0.0, 0.5, 1.0])
        y_computed = np.array([[1.0], [0.6], [0.36]])

        # Request interpolation at different points
        t_eval = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        y_eval = solver._interpolate_results(t_computed, y_computed, t_eval)

        # Check interpolated values
        assert y_eval.shape == (5, 1)
        assert np.allclose(y_eval[0], [1.0])  # t = 0.0
        assert np.allclose(y_eval[2], [0.6])  # t = 0.5
        assert np.allclose(y_eval[4], [0.36])  # t = 1.0

    def test_interpolate_results_multiple_variables(self):
        """Test interpolation with multiple variables"""

        def coupled_ode(t, y):
            return np.array([-y[0], y[1]])

        solver = AdaptiveSolver(
            fun=coupled_ode,
            t_span=(0, 1.0),
            y0=np.array([1.0, 1.0]),
            show_progress=False
        )

        # Create some dummy computed results
        t_computed = np.array([0.0, 0.5, 1.0])
        y_computed = np.array([[1.0, 1.0], [0.6, 1.6], [0.36, 2.56]])

        # Request interpolation at different points
        t_eval = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        y_eval = solver._interpolate_results(t_computed, y_computed, t_eval)

        # Check interpolated values
        assert y_eval.shape == (5, 2)
        assert np.allclose(y_eval[0], [1.0, 1.0])  # t = 0.0
        assert np.allclose(y_eval[2], [0.6, 1.6])  # t = 0.5
        assert np.allclose(y_eval[4], [0.36, 2.56])  # t = 1.0
