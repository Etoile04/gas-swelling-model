"""
Euler Numerical Solver for Gas Swelling Model
欧拉数值求解器模块 (气体肿胀模型)

This module provides an explicit Euler method solver for solving the gas
swelling ODE system. Simple and easy to understand, but requires careful
choice of time step for stability.
本模块提供显式欧拉方法求解器，用于求解气体肿胀ODE系统。简单易懂，但需要仔细选择时间步长以保证稳定性。
"""

import numpy as np
from typing import Callable, Dict, Tuple, Optional


class EulerSolver:
    """
    Explicit Euler Method Solver for Gas Swelling Equations
    显式欧拉方法求解器 (气体肿胀方程)

    This solver implements the forward Euler method, a first-order numerical
    procedure for solving ODEs. Simple and computationally efficient per step,
    but requires small time steps for stability and accuracy.
    该求解器实现前向欧拉方法，一种用于求解ODE的一阶数值方法。
    每步计算简单高效，但需要小时间步长以保证稳定性和精度。

    Parameters
    ----------
    rate_equations : Callable
        Function that computes derivatives dy/dt = f(t, y, params)
        Signature: rate_equations(t: float, y: np.ndarray, params: Dict) -> np.ndarray
    params : Dict
        Dictionary containing material and simulation parameters

    Attributes
    ----------
    rate_equations : Callable
        The rate equations function
    params : Dict
        Model parameters
    success : bool
        Solver success status flag

    Examples
    --------
    >>> from gas_swelling.solvers import EulerSolver
    >>> from gas_swelling.ode import rate_equations
    >>> from gas_swelling.params import create_default_parameters
    >>>
    >>> # Setup solver
    >>> params = create_default_parameters()
    >>> solver = EulerSolver(rate_equations, params)
    >>>
    >>> # Define initial conditions and time span
    >>> y0 = np.ones(17) * 1e-6  # 17 state variables
    >>> t_span = (0, 1000)  # 0 to 1000 seconds
    >>> t_eval = np.linspace(0, 1000, 100)
    >>>
    >>> # Solve with small time step for stability
    >>> results = solver.solve(t_span, t_eval, y0, dt=0.1)
    """

    def __init__(self, rate_equations: Callable, params: Dict):
        """
        Initialize Euler solver with rate equations and parameters.

        Parameters
        ----------
        rate_equations : Callable
            Function that computes derivatives dy/dt = f(t, y, params)
        params : Dict
            Dictionary containing model parameters
        """
        self.rate_equations = rate_equations
        self.params = params
        self.success = True

    def solve(
        self,
        t_span: Tuple[float, float],
        y0: np.ndarray,
        t_eval: Optional[np.ndarray] = None,
        dt: float = 0.1,
        max_dt: float = 100.0,
        adaptive: bool = True,
        output_interval: int = 1000
    ) -> Dict:
        """
        Solve the ODE system using explicit Euler method.

        Parameters
        ----------
        t_span : Tuple[float, float]
            Integration interval (t_start, t_end) in seconds
        y0 : np.ndarray
            Initial state vector (17 components for gas swelling model)
        t_eval : Optional[np.ndarray]
            Time points at which to store solution. If None, uses 100 points.
        dt : float
            Initial time step size (default: 0.1 seconds)
        max_dt : float
            Maximum time step size for adaptive stepping (default: 100.0 seconds)
        adaptive : bool
            Enable adaptive time stepping (default: True)
        output_interval : int
            Store output every N steps (default: 1000)

        Returns
        -------
        Dict
            Dictionary containing solution results:
            - 'time': array of time points
            - 'success': boolean indicating solver success
            - 'message': solver status message
            - 'y': array of solution vectors (shape: [n_vars, n_points])
            - State variables indexed by name (Cgb, Ccb, Ncb, etc.)
            - 'n_steps': total number of steps taken

        Raises
        ------
        ValueError
            If initial conditions y0 has incorrect dimension
        """
        # Validate initial conditions
        if len(y0) != 17:
            raise ValueError(
                f"Initial condition y0 must have 17 components, "
                f"got {len(y0)}"
            )

        # Initialize time and state
        t_start, t_end = t_span
        t_current = t_start
        y_current = y0.copy().astype(float)

        # Clip initial conditions to avoid numerical issues
        y_current = np.clip(y_current, 1e-12, 1e30)

        # Setup time evaluation points
        if t_eval is None:
            n_eval_points = 100
            t_eval = np.linspace(t_start, t_end, n_eval_points)

        # Calculate number of steps
        total_time = t_end - t_start
        n_steps = int(np.ceil(total_time / dt))

        # Storage arrays
        n_vars = len(y0)
        n_output = len(t_eval)

        # Initialize storage for output at evaluation times
        results = {
            'time': t_eval.copy(),
            'success': True,
            'message': 'Euler solver completed successfully',
            'y': np.zeros((n_vars, n_output)),
            'n_steps': 0
        }

        # Initialize variable dictionaries
        var_names = [
            'Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf',
            'cvb', 'cib', 'cvf', 'cif', 'released_gas', 'kvb', 'kib', 'kvf', 'kif'
        ]

        for i, name in enumerate(var_names):
            results[name] = np.zeros(n_output)

        # Output storage index
        output_idx = 0
        next_output_time = t_eval[output_idx] if n_output > 0 else np.inf

        # Perform Euler integration
        current_dt = dt
        step_count = 0

        try:
            while t_current < t_end:
                # Store output at evaluation times
                while t_current >= next_output_time and output_idx < n_output:
                    results['y'][:, output_idx] = y_current
                    for i, name in enumerate(var_names):
                        results[name][output_idx] = y_current[i]
                    output_idx += 1
                    if output_idx < n_output:
                        next_output_time = t_eval[output_idx]
                    else:
                        next_output_time = np.inf

                # Check if we've reached the end
                if t_current >= t_end:
                    break

                # Adjust time step if we're close to the next output time
                if next_output_time < np.inf:
                    current_dt = min(dt, next_output_time - t_current, max_dt)
                else:
                    current_dt = min(dt, t_end - t_current, max_dt)

                # Compute derivatives
                dydt = self.rate_equations(t_current, y_current, self.params)

                # Euler step: y_{n+1} = y_n + dt * f(t_n, y_n)
                y_next = y_current + current_dt * dydt

                # Ensure non-negative values and reasonable bounds
                y_next = np.clip(y_next, 1e-12, 1e30)

                # Update time and state
                t_current += current_dt
                y_current = y_next
                step_count += 1

                # Safety check for runaway solutions
                if not np.all(np.isfinite(y_current)):
                    raise RuntimeError("Solver encountered non-finite values")

            # Store final output if needed
            while output_idx < n_output:
                results['y'][:, output_idx] = y_current
                for i, name in enumerate(var_names):
                    results[name][output_idx] = y_current[i]
                output_idx += 1

            self.success = True
            results['success'] = True
            results['message'] = 'Euler solver completed successfully'
            results['n_steps'] = step_count

        except Exception as e:
            self.success = False
            results['success'] = False
            results['message'] = str(e)
            results['n_steps'] = step_count

        # Add derived quantities
        self._add_derived_quantities(results)

        return results

    def _add_derived_quantities(self, results: Dict) -> None:
        """
        Add derived quantities to results dictionary.

        Parameters
        ----------
        results : Dict
            Results dictionary to modify in-place
        """
        # Calculate swelling volume fraction
        Rcb = results['Rcb']
        Rcf = results['Rcf']
        Ccb = results['Ccb']
        Ccf = results['Ccf']

        # Bubble volume fractions (bulk + boundary)
        V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf

        # Total swelling as percentage
        results['swelling'] = (V_bubble_b + V_bubble_f) * 100
