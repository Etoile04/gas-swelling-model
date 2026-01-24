"""
Adaptive ODE solver with error estimation and step size control.

This module implements an adaptive time-stepping solver that automatically adjusts
integration step size based on local truncation error estimates. It provides
efficient integration for stiff systems with both rapid and slow dynamics.
"""

import numpy as np
from typing import Callable, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class AdaptiveSolver:
    """Adaptive ODE solver with error-based step size control.

    This solver uses embedded Runge-Kutta methods (RK23/RK45) to estimate
    local truncation error and adjust step size accordingly. It provides
    automatic step size control with user-specified tolerances and limits.

    The solver maintains accuracy by taking smaller steps during rapid
    changes and larger steps during quasi-steady periods, optimizing
    computational efficiency.

    Attributes:
        fun: System of ODEs to solve: dy/dt = fun(t, y)
        t_span: Integration interval (t_start, t_end)
        y0: Initial conditions
        rtol: Relative tolerance for error control
        atol: Absolute tolerance for error control
        min_step: Minimum allowed step size
        max_step: Maximum allowed step size
        safety_factor: Safety factor for step size adjustment
        max_steps: Maximum number of steps allowed

    Example:
        >>> from gas_swelling.models.adaptive_solver import AdaptiveSolver
        >>> def my_ode(t, y):
        ...     return -y  # Simple decay
        >>> solver = AdaptiveSolver(fun=my_ode, t_span=(0, 10), y0=np.array([1.0]))
        >>> result = solver.solve()
        >>> print(result['time'], result['y'])
    """

    def __init__(
        self,
        fun: Callable[[float, np.ndarray], np.ndarray],
        t_span: Tuple[float, float],
        y0: np.ndarray,
        rtol: float = 1e-4,
        atol: float = 1e-6,
        min_step: float = 1e-12,
        max_step: float = 100.0,
        safety_factor: float = 0.9,
        max_steps: int = 1000000,
        first_step: Optional[float] = None,
        method: str = 'RK23',
        progress_interval: int = 100,
        show_progress: bool = True
    ):
        """Initialize the adaptive solver.

        Args:
            fun: ODE right-hand side function: dy/dt = fun(t, y)
            t_span: Integration interval (t_start, t_end)
            y0: Initial state vector
            rtol: Relative tolerance for error control (default: 1e-4)
            atol: Absolute tolerance for error control (default: 1e-6)
            min_step: Minimum allowed step size (default: 1e-12)
            max_step: Maximum allowed step size (default: 100.0)
            safety_factor: Safety factor for step size adjustment (default: 0.9)
            max_steps: Maximum number of steps allowed (default: 1000000)
            first_step: Initial step size (optional, auto-estimated if None)
            method: Integration method ('RK23' or 'RK45', default: 'RK23')
            progress_interval: Print progress every N accepted steps (default: 100)
            show_progress: Whether to display progress indicator (default: True)
        """
        self.fun = fun
        self.t_start = t_span[0]
        self.t_end = t_span[1]
        self.y0 = np.asarray(y0, dtype=np.float64)
        self.rtol = rtol
        self.atol = atol
        self.min_step = min_step
        self.max_step = max_step
        self.safety_factor = safety_factor
        self.max_steps = max_steps
        self.first_step = first_step
        self.method = method
        self.progress_interval = progress_interval
        self.show_progress = show_progress

        # Statistics tracking
        self.n_steps = 0
        self.n_accepted = 0
        self.n_rejected = 0
        self.last_step_size = None

        # Validate inputs
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Validate solver parameters."""
        if self.t_start >= self.t_end:
            raise ValueError(f"t_span[0] must be less than t_span[1], got {self.t_start} >= {self.t_end}")

        if self.rtol <= 0:
            raise ValueError(f"rtol must be positive, got {self.rtol}")

        if self.atol <= 0:
            raise ValueError(f"atol must be positive, got {self.atol}")

        if self.min_step <= 0:
            raise ValueError(f"min_step must be positive, got {self.min_step}")

        if self.max_step <= self.min_step:
            raise ValueError(f"max_step must be greater than min_step, got {self.max_step} <= {self.min_step}")

        if not 0 < self.safety_factor < 1:
            raise ValueError(f"safety_factor must be in (0, 1), got {self.safety_factor}")

        if self.method not in ['RK23', 'RK45']:
            raise ValueError(f"method must be 'RK23' or 'RK45', got {self.method}")

    def _estimate_initial_step(self, t0: float, y0: np.ndarray) -> float:
        """Estimate initial step size based on system dynamics.

        Uses a simple heuristic to estimate the initial step size by
        evaluating the derivative and scale of the problem.

        Args:
            t0: Initial time
            y0: Initial state

        Returns:
            Estimated initial step size
        """
        # Evaluate derivative at initial point
        f0 = self.fun(t0, y0)

        # Scale based on norm of derivative and state
        scale = self.atol + self.rtol * np.abs(y0)
        norm_y = np.sqrt(np.mean((y0 / scale) ** 2))
        norm_f = np.sqrt(np.mean((f0 / scale) ** 2))

        if norm_f == 0:
            # Derivative is zero, use a conservative step
            dt = self.max_step
        else:
            # Initial step based on derivative and desired accuracy
            dt = 0.01 * norm_y / norm_f if norm_y > 0 else 0.01

        # Constrain to allowable range
        dt = np.clip(dt, self.min_step, self.max_step)

        return dt

    def _rk23_step(
        self,
        t: float,
        y: np.ndarray,
        dt: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Perform a single RK23 (Bogacki-Shampine) step.

        Uses the embedded 2nd and 3rd order Runge-Kutta method to
        compute solution and error estimate.

        Args:
            t: Current time
            y: Current state
            dt: Step size

        Returns:
            y_new: Solution at t + dt (3rd order)
            y_error: Error estimate (difference between 2nd and 3rd order)
            dt_new: Suggested new step size
        """
        # Bogacki-Shampine RK23 coefficients
        # k1 = f(t, y)
        k1 = self.fun(t, y)

        # k2 = f(t + 1/2*dt, y + 1/2*dt*k1)
        k2 = self.fun(t + 0.5 * dt, y + 0.5 * dt * k1)

        # k3 = f(t + 3/4*dt, y + 3/4*dt*k2)
        k3 = self.fun(t + 0.75 * dt, y + 0.75 * dt * k2)

        # 4th stage for error estimation
        # k4 = f(t + dt, y + 2/9*dt*k1 + 1/3*dt*k2 + 4/9*dt*k3)
        k4 = self.fun(t + dt,
                     y + dt * (2.0/9.0 * k1 + 1.0/3.0 * k2 + 4.0/9.0 * k3))

        # 3rd order solution (FSAL property)
        y_new = y + dt * (7.0/24.0 * k1 + 1.0/4.0 * k2 + 1.0/3.0 * k3 + 1.0/8.0 * k4)

        # 2nd order solution for error estimation
        y_low = y + dt * (2.0/9.0 * k1 + 1.0/3.0 * k2 + 4.0/9.0 * k3)

        # Error estimate
        y_error = y_new - y_low

        return y_new, y_error

    def _rk45_step(
        self,
        t: float,
        y: np.ndarray,
        dt: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Perform a single RK45 (Cash-Karp) step.

        Uses the embedded 4th and 5th order Runge-Kutta method to
        compute solution and error estimate.

        Args:
            t: Current time
            y: Current state
            dt: Step size

        Returns:
            y_new: Solution at t + dt (5th order)
            y_error: Error estimate (difference between 4th and 5th order)
        """
        # Cash-Karp RK45 coefficients
        k1 = self.fun(t, y)

        k2 = self.fun(t + 0.2 * dt, y + dt * 0.2 * k1)

        k3 = self.fun(t + 0.3 * dt,
                      y + dt * (0.075 * k1 + 0.225 * k2))

        k4 = self.fun(t + 0.6 * dt,
                      y + dt * (0.3 * k1 - 0.9 * k2 + 1.8 * k3))

        k5 = self.fun(t + dt,
                      y + dt * (-11.0/54.0 * k1 + 2.5 * k2 - 70.0/27.0 * k3 + 35.0/27.0 * k4))

        k6 = self.fun(t + 0.875 * dt,
                      y + dt * (1631.0/55296.0 * k1 + 175.0/512.0 * k2 +
                               575.0/13824.0 * k3 + 44275.0/110592.0 * k4 +
                               253.0/4096.0 * k5))

        # 5th order solution
        y_new = y + dt * (37.0/378.0 * k1 + 250.0/621.0 * k3 +
                          125.0/594.0 * k4 + 512.0/1771.0 * k6)

        # 4th order solution for error estimation
        y_low = y + dt * (2825.0/27648.0 * k1 + 18575.0/48384.0 * k3 +
                          13525.0/55296.0 * k4 + 277.0/14336.0 * k5 +
                          0.25 * k6)

        # Error estimate
        y_error = y_new - y_low

        return y_new, y_error

    def _compute_error_norm(
        self,
        y_error: np.ndarray,
        y: np.ndarray
    ) -> float:
        """Compute weighted error norm for step size control.

        Args:
            y_error: Error estimate
            y: Current state

        Returns:
            Normalized error measure
        """
        scale = self.atol + self.rtol * np.abs(y)
        error_norm = np.sqrt(np.mean((y_error / scale) ** 2))
        return error_norm

    def _print_progress(self, t: float, dt: float) -> None:
        """Print progress indicator to console.

        Args:
            t: Current time
            dt: Current step size
        """
        percent_complete = (t - self.t_start) / (self.t_end - self.t_start) * 100
        print(f"\rProgress: {percent_complete:5.1f}% | t = {t:10.2f} s | dt = {dt:10.2e} s", end='', flush=True)

    def _adjust_step_size(
        self,
        dt: float,
        error_norm: float
    ) -> float:
        """Adjust step size based on error estimate.

        Args:
            dt: Current step size
            error_norm: Normalized error measure

        Returns:
            New step size
        """
        if error_norm == 0:
            # No error, increase step size
            factor = 2.0
        elif error_norm < 1.0:
            # Error acceptable, modestly increase step size
            factor = self.safety_factor * (1.0 / error_norm) ** (0.5 if self.method == 'RK23' else 0.2)
        else:
            # Error too large, decrease step size
            factor = self.safety_factor * (1.0 / error_norm) ** (0.5 if self.method == 'RK23' else 0.2)

        # Limit step size changes
        factor = np.clip(factor, 0.1, 5.0)

        # Compute new step size
        dt_new = dt * factor

        # Constrain to allowable range
        dt_new = np.clip(dt_new, self.min_step, self.max_step)

        return dt_new

    def solve(
        self,
        t_eval: Optional[np.ndarray] = None,
        dense_output: bool = False
    ) -> Dict:
        """Solve the ODE system with adaptive stepping.

        Args:
            t_eval: Time points at which to store solution (optional)
            dense_output: If True, return interpolation function (not yet implemented)

        Returns:
            Dictionary containing:
                - 'time': Array of time points
                - 'y': Array of solution states (shape: len(t_eval) x len(y0))
                - 'success': Boolean indicating if integration succeeded
                - 'message': Status message
                - 'n_steps': Total number of steps taken
                - 'n_accepted': Number of accepted steps
                - 'n_rejected': Number of rejected steps
        """
        # Initialize
        t = self.t_start
        y = self.y0.copy()

        # Determine initial step size
        if self.first_step is not None:
            dt = self.first_step
        else:
            dt = self._estimate_initial_step(t, y)
        dt = np.clip(dt, self.min_step, self.max_step)

        # Storage for solution
        t_points = [t]
        y_points = [y.copy()]

        # Reset statistics
        self.n_steps = 0
        self.n_accepted = 0
        self.n_rejected = 0

        # Main integration loop
        try:
            while t < self.t_end and self.n_steps < self.max_steps:
                # Don't overshoot the end time
                if t + dt > self.t_end:
                    dt = self.t_end - t

                # Perform integration step
                if self.method == 'RK23':
                    y_new, y_error = self._rk23_step(t, y, dt)
                else:  # RK45
                    y_new, y_error = self._rk45_step(t, y, dt)

                # Compute error norm
                error_norm = self._compute_error_norm(y_error, y)

                # Check if step is acceptable
                if error_norm <= 1.0:
                    # Accept step
                    t += dt
                    y = y_new
                    t_points.append(t)
                    y_points.append(y.copy())
                    self.n_accepted += 1

                    # Print progress to console
                    if self.show_progress and self.n_accepted % self.progress_interval == 0:
                        self._print_progress(t, dt)
                else:
                    # Reject step
                    self.n_rejected += 1
                    if self.n_rejected % 100 == 0:
                        logger.warning(
                            f"Step rejected at t={t:.2f}, "
                            f"error={error_norm:.2e}, "
                            f"reducing step"
                        )

                # Adjust step size for next iteration
                dt = self._adjust_step_size(dt, error_norm)
                self.n_steps += 1

            # Check completion status
            if t >= self.t_end:
                success = True
                message = f"Integration completed successfully in {self.n_steps} steps"
                # Print final progress
                if self.show_progress:
                    self._print_progress(t, dt)
                    print()  # Newline after progress indicator
            elif self.n_steps >= self.max_steps:
                success = False
                message = f"Maximum number of steps ({self.max_steps}) exceeded"
                if self.show_progress:
                    print()  # Newline after progress indicator
            else:
                success = False
                message = "Integration terminated prematurely"
                if self.show_progress:
                    print()  # Newline after progress indicator

        except Exception as e:
            success = False
            message = f"Integration failed with error: {str(e)}"
            logger.error(message)
            if self.show_progress:
                print()  # Newline after progress indicator

        # Convert to arrays
        t_array = np.array(t_points)
        y_array = np.array(y_points)

        # Interpolate to requested time points if specified
        if t_eval is not None:
            y_array = self._interpolate_results(t_array, y_array, t_eval)
            t_array = t_eval

        # Store final step size
        self.last_step_size = dt

        return {
            'time': t_array,
            'y': y_array,
            'success': success,
            'message': message,
            'n_steps': self.n_steps,
            'n_accepted': self.n_accepted,
            'n_rejected': self.n_rejected
        }

    def _interpolate_results(
        self,
        t_computed: np.ndarray,
        y_computed: np.ndarray,
        t_eval: np.ndarray
    ) -> np.ndarray:
        """Interpolate computed solution to requested time points.

        Uses linear interpolation to provide solution at user-requested
        time points, which may not coincide with adaptive step points.

        Args:
            t_computed: Time points from adaptive stepping
            y_computed: Solution at computed time points
            t_eval: Requested time points for output

        Returns:
            Interpolated solution at t_eval points
        """
        n_states = y_computed.shape[1]
        y_eval = np.zeros((len(t_eval), n_states))

        for i in range(n_states):
            y_eval[:, i] = np.interp(t_eval, t_computed, y_computed[:, i])

        return y_eval
