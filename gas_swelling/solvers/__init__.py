"""
Numerical Solvers Module for Gas Swelling Model
数值求解器模块 (气体肿胀模型)

This module provides numerical solver wrappers for solving the gas swelling
ODE system using different integration methods.
本模块提供使用不同积分方法求解气体肿胀ODE系统的数值求解器包装器。

Available Solvers (可用求解器):
- RK23Solver: Runge-Kutta 2(3) adaptive solver (龙格-库塔2(3)自适应求解器)
- EulerSolver: Explicit Euler method solver (显式欧拉方法求解器)

Example Usage (使用示例):
    >>> from gas_swelling.solvers import RK23Solver, EulerSolver
    >>> from gas_swelling.ode import rate_equations
    >>>
    >>> # Setup solver (设置求解器)
    >>> solver = RK23Solver(rate_equations, params)
    >>> results = solver.solve(t_span=(0, 1000), t_eval=time_points)
"""

from .rk23_solver import RK23Solver
from .euler_solver import EulerSolver

__all__ = ['RK23Solver', 'EulerSolver']
