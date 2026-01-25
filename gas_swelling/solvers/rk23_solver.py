"""
RK23 Numerical Solver for Gas Swelling Model

This module provides a wrapper around scipy's RK23 (Runge-Kutta 2(3)) adaptive
solver for solving the gas swelling ODE system.
"""

import numpy as np
from typing import Callable, Dict, Tuple, Optional
from scipy.integrate import solve_ivp


class RK23Solver:
    """
    Runge-Kutta 2(3) adaptive solver wrapper for gas swelling equations.

    This solver uses scipy's solve_ivp with the 'RK23' method, which is an
    explicit Runge-Kutta method of order 3 with error control and adaptive
    step sizing. Suitable for non-stiff to moderately stiff ODE systems.

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
    >>> from gas_swelling.solvers import RK23Solver
    >>> from gas_swelling.ode import rate_equations
    >>> from gas_swelling.params import create_default_parameters
    >>>
    >>> # Setup solver
    >>> params = create_default_parameters()
    >>> solver = RK23Solver(rate_equations, params)
    >>>
    >>> # Define initial conditions and time span
    >>> y0 = np.ones(17) * 1e-6  # 17 state variables
    >>> t_span = (0, 1000)  # 0 to 1000 seconds
    >>> t_eval = np.linspace(0, 1000, 100)
    >>>
    >>> # Solve
    >>> results = solver.solve(t_span, t_eval, y0)
    """

    def __init__(self, rate_equations: Callable, params: Dict):
        """
        Initialize RK23 solver with rate equations and parameters.

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

    def _equations_wrapper(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        Wrapper function for rate equations in scipy format.

        Parameters
        ----------
        t : float
            Current time
        y : np.ndarray
            Current state vector

        Returns
        -------
        np.ndarray
            Time derivatives dy/dt
        """
        return self.rate_equations(t, y, self.params)

    def solve(
        self,
        t_span: Tuple[float, float],
        y0: np.ndarray,
        t_eval: Optional[np.ndarray] = None,
        dt: float = 1e-9,
        max_dt: float = 100.0,
        rtol: float = 1e-4,
        atol: float = 1e-6,
        max_steps: int = 1000000
    ) -> Dict:
        """
        Solve the ODE system using RK23 method.

        Parameters
        ----------
        t_span : Tuple[float, float]
            Integration interval (t_start, t_end) in seconds
        y0 : np.ndarray
            Initial state vector (17 components for gas swelling model)
        t_eval : Optional[np.ndarray]
            Time points at which to store solution. If None, uses 100 points.
        dt : float
            Initial time step size (default: 1e-9 seconds)
        max_dt : float
            Maximum time step size (default: 100.0 seconds)
        rtol : float
            Relative tolerance for error control (default: 1e-4)
        atol : float
            Absolute tolerance for error control (default: 1e-6)
        max_steps : int
            Maximum number of internal steps (default: 1000000)

        Returns
        -------
        Dict
            Dictionary containing solution results:
            - 'time': array of time points
            - 'success': boolean indicating solver success
            - 'message': solver status message
            - 'y': array of solution vectors (shape: [n_vars, n_points])
            - State variables indexed by name (Cgb, Ccb, Ncb, etc.)

        Raises
        ------
        ValueError
            If initial conditions y0 has incorrect dimension
        RuntimeError
            If solver fails and raises an exception
        """
        # Validate initial conditions
        if len(y0) != 17:
            raise ValueError(
                f"Initial condition y0 must have 17 components, "
                f"got {len(y0)}"
            )

        # Set up time evaluation points
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        # Clip initial conditions to avoid numerical issues
        y0_clipped = np.clip(y0, 1e-12, 1e30)

        # Solve ODE system with error handling
        try:
            sol = solve_ivp(
                fun=self._equations_wrapper,
                t_span=t_span,
                y0=y0_clipped,
                t_eval=t_eval,
                method='RK23',
                rtol=rtol,
                atol=atol,
                first_step=dt,
                max_step=max_dt,
                max_steps=max_steps
            )
            self.success = sol.success

        except Exception as e:
            self.success = False
            # Return empty results on failure
            return {
                'time': np.array([]),
                'success': False,
                'message': str(e),
                'y': np.array([]),
                'nfev': 0,
                'njev': 0,
                'nlu': 0
            }

        # Map solution to dictionary with variable names
        # State variables (17 components):
        # 0: Cgb, 1: Ccb, 2: Ncb, 3: Rcb, 4: Cgf, 5: Ccf,
        # 6: Ncf, 7: Rcf, 8: cvb, 9: cib, 10: cvf, 11: cif,
        # 12: released_gas, 13: kvb, 14: kib, 15: kvf, 16: kif

        results_dict = {
            'time': sol.t,
            'success': sol.success,
            'message': sol.message,
            'y': sol.y,
            'nfev': sol.nfev,
            'njev': sol.njev,
            'nlu': sol.nlu,
            # State variables
            'Cgb': sol.y[0],
            'Ccb': sol.y[1],
            'Ncb': sol.y[2],
            'Rcb': sol.y[3],
            'Cgf': sol.y[4],
            'Ccf': sol.y[5],
            'Ncf': sol.y[6],
            'Rcf': sol.y[7],
            'cvb': sol.y[8],
            'cib': sol.y[9],
            'cvf': sol.y[10],
            'cif': sol.y[11],
            'released_gas': sol.y[12],
            'kvb': sol.y[13],
            'kib': sol.y[14],
            'kvf': sol.y[15],
            'kif': sol.y[16]
        }

        # Calculate derived quantities
        self._add_derived_quantities(results_dict)

        return results_dict

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
