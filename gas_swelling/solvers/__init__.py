"""
Numerical Solvers Module for Gas Swelling Model

This module provides numerical solver wrappers for solving the gas swelling
ODE system using different integration methods.

Available Solvers:
- RK23Solver: Runge-Kutta 2(3) adaptive solver
- EulerSolver: Explicit Euler method solver

Example Usage:
    >>> from gas_swelling.solvers import RK23Solver, EulerSolver
    >>> from gas_swelling.ode import rate_equations
    >>>
    >>> # Setup solver
    >>> solver = RK23Solver(rate_equations, params)
    >>> results = solver.solve(t_span=(0, 1000), t_eval=time_points)
"""

from .rk23_solver import RK23Solver
from .euler_solver import EulerSolver

__all__ = ['RK23Solver', 'EulerSolver']
