"""
Experimental reduced-order gas swelling model using QSSA for point defects.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csr_matrix

from ..io import print_simulation_summary, update_debug_history
from ..ode import calculate_qssa_auxiliary_fields, swelling_qssa_ode_system
from .refactored_model import RefactoredGasSwellingModel


class QSSAGasSwellingModel(RefactoredGasSwellingModel):
    """
    Reduced-order variant that algebraically closes the fast point-defect fields.

    The integrated state is reduced from 17 variables to 9 slower variables.
    Point-defect concentrations are reconstructed at each RHS evaluation with a
    quasi-steady-state approximation.
    """

    reduced_state_size = 9
    full_state_size = 17

    def _initialize_state(self) -> np.ndarray:
        Nc_init = 5.0
        Cg_init = 0.0
        Cc_init = 0.0
        R_init = 1e-8

        return np.array(
            [
                Cg_init,
                Cc_init,
                Nc_init,
                R_init,
                Cg_init,
                Cc_init,
                Nc_init,
                R_init,
                0.0,
            ],
            dtype=float,
        )

    def _equations(self, t: float, state: np.ndarray) -> np.ndarray:
        return self._equations_wrapper(t, state)

    def _equations_wrapper(self, t: float, state: np.ndarray, params: Dict = None) -> np.ndarray:
        _ = params
        self.current_time = t
        derivatives = swelling_qssa_ode_system(t, state, self.params)

        if self.debug_config.enabled:
            self._record_debug_info(t, state, derivatives)

        return derivatives

    def _record_debug_info(self, t: float, state: np.ndarray, derivatives: np.ndarray):
        _ = derivatives
        fields = calculate_qssa_auxiliary_fields(state, self.params)

        Pg_b = self.get_gas_pressure(fields['Rcb'], fields['Ncb'], location='bulk')
        Pg_f = self.get_gas_pressure(fields['Rcf'], fields['Ncf'], location='boundary')
        V_bubble_b = (4.0 / 3.0) * np.pi * fields['Rcb'] ** 3 * fields['Ccb']
        V_bubble_f = (4.0 / 3.0) * np.pi * fields['Rcf'] ** 3 * fields['Ccf']
        swelling = (V_bubble_b + V_bubble_f) * 100.0

        update_debug_history(
            self.debug_history,
            time=t,
            Rcb=fields['Rcb'],
            Rcf=fields['Rcf'],
            Ncb=fields['Ncb'],
            Ncf=fields['Ncf'],
            Pg_b=Pg_b,
            Pg_f=Pg_f,
            swelling=swelling,
        )

    def _select_first_step(
        self,
        dt: Optional[float],
        t_span: Tuple[float, float],
        solver_method: str
    ) -> Optional[float]:
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
        pattern = np.zeros((self.reduced_state_size, self.reduced_state_size), dtype=bool)
        dependencies = {
            0: [0, 1, 2, 3, 4],
            1: [0, 2],
            2: [0, 1, 2, 3],
            3: [1, 2, 3],
            4: [0, 4, 5, 6, 7],
            5: [4, 6],
            6: [4, 5, 6, 7],
            7: [5, 6, 7],
            8: [4, 5, 6, 7],
        }

        for row, cols in dependencies.items():
            pattern[row, cols] = True

        return csr_matrix(pattern)

    def _reconstruct_results(self, reduced_y: np.ndarray) -> Dict[str, np.ndarray]:
        reduced_y = np.maximum(reduced_y, 0.0)
        n_points = reduced_y.shape[1]

        cvb = np.empty(n_points, dtype=float)
        cib = np.empty(n_points, dtype=float)
        cvf = np.empty(n_points, dtype=float)
        cif = np.empty(n_points, dtype=float)

        for idx in range(n_points):
            fields = calculate_qssa_auxiliary_fields(reduced_y[:, idx], self.params)
            cvb[idx] = fields['cvb']
            cib[idx] = fields['cib']
            cvf[idx] = fields['cvf']
            cif[idx] = fields['cif']

        kvb = np.full(n_points, self.params['kv_param'], dtype=float)
        kib = np.full(n_points, self.params['ki_param'], dtype=float)
        kvf = np.full(n_points, self.params['kv_param'], dtype=float)
        kif = np.full(n_points, self.params['ki_param'], dtype=float)

        results = {
            'Cgb': reduced_y[0],
            'Ccb': reduced_y[1],
            'Ncb': reduced_y[2],
            'Rcb': reduced_y[3],
            'Cgf': reduced_y[4],
            'Ccf': reduced_y[5],
            'Ncf': reduced_y[6],
            'Rcf': reduced_y[7],
            'cvb': cvb,
            'cib': cib,
            'cvf': cvf,
            'cif': cif,
            'released_gas': reduced_y[8],
            'kvb': kvb,
            'kib': kib,
            'kvf': kvf,
            'kif': kif,
        }

        results['swelling'] = (
            (4.0 / 3.0) * np.pi * results['Rcb'] ** 3 * results['Ccb']
            + (4.0 / 3.0) * np.pi * results['Rcf'] ** 3 * results['Ccf']
        ) * 100.0

        results['y'] = np.vstack(
            [
                results['Cgb'],
                results['Ccb'],
                results['Ncb'],
                results['Rcb'],
                results['Cgf'],
                results['Ccf'],
                results['Ncf'],
                results['Rcf'],
                results['cvb'],
                results['cib'],
                results['cvf'],
                results['cif'],
                results['released_gas'],
                results['kvb'],
                results['kib'],
                results['kvf'],
                results['kif'],
            ]
        )
        results['y_reduced'] = reduced_y
        return results

    def solve(
        self,
        t_span: Tuple[float, float] = (0, 7200000),
        t_eval: Optional[np.ndarray] = None,
        method: str = 'LSODA',
        dt: float = 1e-9,
        max_dt: float = 100.0,
        max_steps: int = 1000000,
        output_interval: int = 1000,
        debug_enabled: bool = False
    ) -> Dict:
        self.debug_config.enabled = debug_enabled
        self.debug_config.time_step_interval = output_interval

        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        valid_methods = {'RK23', 'RK45', 'LSODA', 'BDF', 'Radau'}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Valid methods: {', '.join(sorted(valid_methods))}")

        solve_kwargs = {
            'fun': lambda t, y: self._equations_wrapper(t, y),
            't_span': t_span,
            'y0': np.clip(self.initial_state, 1e-12, 1e30),
            't_eval': t_eval,
            'method': method,
            'rtol': self.params.get('rtol', 1e-4),
            'atol': self.params.get('atol', 1e-6),
            'max_step': max_dt,
        }

        first_step = self._select_first_step(dt, t_span, method)
        if first_step is not None:
            solve_kwargs['first_step'] = first_step

        if method in {'BDF', 'Radau'}:
            solve_kwargs['jac_sparsity'] = self._build_jacobian_sparsity()

        sol = solve_ivp(**solve_kwargs)
        self.solver_success = sol.success

        if not sol.success:
            return {
                'time': sol.t,
                'success': False,
                'message': sol.message,
                'y': np.array([]),
                'y_reduced': sol.y if sol.y.size > 0 else np.array([]),
                'nfev': sol.nfev,
                'njev': sol.njev,
                'nlu': sol.nlu,
                'n_steps': max(len(sol.t) - 1, 0),
                'n_accepted': max(len(sol.t) - 1, 0),
                'n_rejected': 0,
            }

        results = self._reconstruct_results(sol.y)
        results.update(
            {
                'time': sol.t,
                'success': sol.success,
                'message': sol.message,
                'nfev': sol.nfev,
                'njev': sol.njev,
                'nlu': sol.nlu,
                'n_steps': max(len(sol.t) - 1, 0),
                'n_accepted': max(len(sol.t) - 1, 0),
                'n_rejected': 0,
            }
        )
        self.step_count = results['n_steps']

        if debug_enabled:
            print_simulation_summary(results, self.params)

        return results

    def __repr__(self) -> str:
        temp = self.params.get('temperature', 0)
        fission_rate = self.params.get('fission_rate', 0)
        eos_model = self.params.get('eos_model', 'virial')
        return (
            f"QSSAGasSwellingModel(temperature={temp:.2f} K, "
            f"fission_rate={fission_rate:.2e} /m³/s, "
            f"eos_model='{eos_model}')"
        )

