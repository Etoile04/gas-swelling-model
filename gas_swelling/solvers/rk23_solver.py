"""
Flexible ODE Solver for Gas Swelling Model
灵活ODE求解器模块 (气体肿胀模型)

This module provides a flexible wrapper around scipy's solve_ivp supporting
multiple solver methods for stiff and non-stiff ODE systems.
本模块提供scipy的solve_ivp的灵活包装器，支持刚性和非刚性ODE系统的多种求解器方法。

Supported Methods:
- 'RK23': Explicit Runge-Kutta 2(3) - For non-stiff problems (fast)
- 'RK45': Explicit Runge-Kutta 4(5) - For non-stiff problems (accurate)
- 'LSODA': Adams/BDF method with automatic stiffness detection (RECOMMENDED)
- 'BDF': Implicit Backward Differentiation Formula - For stiff problems
- 'Radau': Implicit Runge-Kutta method - For stiff problems
- 'BDF': Backward Differentiation Formula - For stiff problems

支持的方法:
- 'RK23': 显式龙格-库塔2(3) - 用于非刚性问题 (快速)
- 'RK45': 显式龙格-库塔4(5) - 用于非刚性问题 (精确)
- 'LSODA': Adams/BDF方法，自动检测刚性 (推荐)
- 'BDF': 隐式向后微分公式 - 用于刚性问题
- 'Radau': 隐式龙格-库塔方法 - 用于刚性问题
"""

import numpy as np
from typing import Callable, Dict, Tuple, Optional
from scipy.integrate import solve_ivp
from scipy.sparse import csr_matrix


class RK23Solver:
    """
    Flexible ODE Solver for Gas Swelling Equations
    灵活ODE求解器 (气体肿胀方程)

    This solver uses scipy's solve_ivp with configurable method selection.
    It supports both explicit methods (RK23, RK45) for non-stiff problems
    and implicit methods (BDF, Radau, LSODA) for stiff systems.
    该求解器使用scipy的solve_ivp函数，可配置方法选择。支持显式方法（RK23、RK45）
    用于非刚性问题，以及隐式方法（BDF、Radau、LSODA）用于刚性系统。

    **Default method 'LSODA'** automatically detects stiffness and switches
    between Adams (non-stiff) and BDF (stiff) methods, providing optimal
    performance for both cases.
    **默认方法'LSODA'** 自动检测刚性并在Adams（非刚性）和BDF（刚性）
    方法之间切换，为两种情况提供最佳性能。

    Parameters
    ----------
    rate_equations : Callable
        Function that computes derivatives dy/dt = f(t, y, params)
        Signature: rate_equations(t: float, y: np.ndarray, params: Dict) -> np.ndarray
    params : Dict
        Dictionary containing material and simulation parameters
    method : str, optional
        Solver method to use (default: 'LSODA')
        Options: 'RK23', 'RK45', 'LSODA', 'BDF', 'Radau'

    Attributes
    ----------
    rate_equations : Callable
        The rate equations function
    params : Dict
        Model parameters
    method : str
        The solver method being used
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

    def __init__(self, rate_equations: Callable, params: Dict, method: str = 'LSODA'):
        """
        Initialize ODE solver with rate equations, parameters, and method.

        Parameters
        ----------
        rate_equations : Callable
            Function that computes derivatives dy/dt = f(t, y, params)
        params : Dict
            Dictionary containing model parameters
        method : str, optional
            Solver method to use (default: 'LSODA')
            Options:
            - 'RK23': Explicit Runge-Kutta 2(3) - Fast for non-stiff
            - 'RK45': Explicit Runge-Kutta 4(5) - Accurate for non-stiff
            - 'LSODA': Adams/BDF with auto stiffness detection (RECOMMENDED)
            - 'BDF': Backward Differentiation Formula - For stiff systems
            - 'Radau': Implicit Runge-Kutta - For stiff systems
        """
        self.rate_equations = rate_equations
        self.params = params
        self.method = method
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

    def _select_first_step(
        self,
        dt: Optional[float],
        t_span: Tuple[float, float],
        solver_method: str
    ) -> Optional[float]:
        """
        Choose a physically sensible first step.

        The legacy default `dt=1e-9` is appropriate for old fixed-step logic,
        but it can severely slow adaptive stiff solvers. For implicit/stiff
        methods we usually let solve_ivp estimate its own first step.
        """
        if dt is None or dt <= 0:
            return None

        total_time = t_span[1] - t_span[0]
        if total_time <= 0:
            return None

        if solver_method in {'LSODA', 'BDF', 'Radau'}:
            return None

        if np.isclose(dt, 1e-9) and total_time > 1.0:
            return None

        return min(dt, total_time)

    def _build_jacobian_sparsity(self) -> csr_matrix:
        """
        Approximate Jacobian sparsity for the 17-variable rate system.

        This does not need to be exact; a conservative sparsity pattern is still
        useful for Radau/BDF finite-difference Jacobian assembly.
        """
        pattern = np.zeros((17, 17), dtype=bool)

        dependencies = {
            0: [0, 1, 2, 3, 4],          # Cgb
            1: [0, 2],                   # Ccb
            2: [0, 1, 2, 3],             # Ncb
            3: [1, 2, 3, 8, 9],          # Rcb
            4: [0, 4, 5, 6, 7],          # Cgf
            5: [4, 6],                   # Ccf
            6: [4, 5, 6, 7],             # Ncf
            7: [5, 6, 7, 10, 11],        # Rcf
            8: [1, 3, 8, 9],             # cvb
            9: [1, 3, 8, 9],             # cib
            10: [5, 7, 10, 11],          # cvf
            11: [5, 7, 10, 11],          # cif
            12: [4, 5, 6, 7],            # released_gas
            13: [13],
            14: [14],
            15: [15],
            16: [16],
        }

        for row, cols in dependencies.items():
            pattern[row, cols] = True

        return csr_matrix(pattern)

    def solve(
        self,
        t_span: Tuple[float, float],
        y0: np.ndarray,
        t_eval: Optional[np.ndarray] = None,
        dt: float = 1e-9,
        max_dt: float = 100.0,
        rtol: float = 1e-4,
        atol: float = 1e-6,
        max_steps: int = 1000000,
        method: Optional[str] = None
    ) -> Dict:
        """
        Solve the ODE system using the specified method.

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
        method : Optional[str]
            Solver method to use. If None, uses the method from __init__ (default: 'LSODA')
            Options: 'RK23', 'RK45', 'LSODA', 'BDF', 'Radau'

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
        # Validate initial conditions (验证初始条件)
        if len(y0) != 17:
            raise ValueError(
                f"Initial condition y0 must have 17 components, "
                f"got {len(y0)}"
            )

        # Set up time evaluation points (设置时间评估点)
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        # Clip initial conditions to avoid numerical issues (裁剪初始条件以避免数值问题)
        y0_clipped = np.clip(y0, 1e-12, 1e30)

        # Determine which method to use (确定使用哪种方法)
        solver_method = method if method is not None else self.method

        # Validate method (验证方法)
        valid_methods = ['RK23', 'RK45', 'LSODA', 'BDF', 'Radau', 'BDF']
        if solver_method not in valid_methods:
            raise ValueError(
                f"Invalid method '{solver_method}'. "
                f"Valid methods: {', '.join(valid_methods)}"
            )

        # Solve ODE system with error handling (求解ODE系统，带错误处理)
        first_step = self._select_first_step(dt, t_span, solver_method)
        jac_sparsity = self._build_jacobian_sparsity() if solver_method in {'BDF', 'Radau'} else None

        solve_kwargs = {
            'fun': self._equations_wrapper,
            't_span': t_span,
            'y0': y0_clipped,
            't_eval': t_eval,
            'method': solver_method,
            'rtol': rtol,
            'atol': atol,
            'max_step': max_dt,
        }
        if first_step is not None:
            solve_kwargs['first_step'] = first_step
        if jac_sparsity is not None:
            solve_kwargs['jac_sparsity'] = jac_sparsity

        try:
            sol = solve_ivp(**solve_kwargs)
            self.success = sol.success

        except Exception as e:
            self.success = False
            # Return empty results on failure (失败时返回空结果)
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
        # 将解映射到带变量名的字典
        # State variables (状态变量 - 17 components):
        # 0: Cgb, 1: Ccb, 2: Ncb, 3: Rcb, 4: Cgf, 5: Ccf,
        # 6: Ncf, 7: Rcf, 8: cvb, 9: cib, 10: cvf, 11: cif,
        # 12: released_gas, 13: kvb, 14: kib, 15: kvf, 16: kif

        # Check if solver succeeded before accessing solution data
        # 检查求解器是否成功，再访问解数据
        if not sol.success:
            # Solver failed - return minimal results with error message
            # 求解器失败 - 返回包含错误消息的最小结果
            return {
                'time': sol.t,
                'success': sol.success,
                'message': sol.message,
                'y': sol.y if sol.y.size > 0 else np.zeros((17, len(t_eval))),
                'nfev': sol.nfev,
                'njev': sol.njev,
                'nlu': sol.nlu,
                # Add empty state variables for consistency
                # 添加空状态变量以保持一致性
                'Cgb': np.array([]), 'Ccb': np.array([]), 'Ncb': np.array([]),
                'Rcb': np.array([]), 'Cgf': np.array([]), 'Ccf': np.array([]),
                'Ncf': np.array([]), 'Rcf': np.array([]), 'cvb': np.array([]),
                'cib': np.array([]), 'cvf': np.array([]), 'cif': np.array([]),
                'released_gas': np.array([]), 'kvb': np.array([]), 'kib': np.array([]),
                'kvf': np.array([]), 'kif': np.array([]),
                'swelling': np.array([])
            }

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

        # Calculate derived quantities (计算导出量)
        self._add_derived_quantities(results_dict)

        return results_dict

    def _add_derived_quantities(self, results: Dict) -> None:
        """
        Add derived quantities to results dictionary.
        将导出量添加到结果字典

        Parameters
        ----------
        results : Dict
            Results dictionary to modify in-place (要就地修改的结果字典)
        """
        # Calculate swelling volume fraction (计算肿胀体积分数)
        Rcb = results['Rcb']
        Rcf = results['Rcf']
        Ccb = results['Ccb']
        Ccf = results['Ccf']

        # Bubble volume fractions (bulk + boundary)
        # 气泡体积分数 (基体 + 晶界)
        V_bubble_b = (4.0 / 3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0 / 3.0) * np.pi * Rcf**3 * Ccf

        # Total swelling as percentage (总肿胀百分比)
        results['swelling'] = (V_bubble_b + V_bubble_f) * 100
