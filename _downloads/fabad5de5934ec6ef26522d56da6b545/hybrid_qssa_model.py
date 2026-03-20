"""
Hybrid relaxed-QSSA gas swelling model.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csr_matrix

from ..io import print_simulation_summary, update_debug_history
from ..ode import (
    calculate_relaxed_qssa_pair,
    select_dynamic_pair,
)
from ..ode.rate_equations import (
    calculate_cavity_radius_derivatives,
    calculate_gas_concentration_derivatives,
)
from ..physics.thermal import calculate_ci0, calculate_cv0
from .refactored_model import RefactoredGasSwellingModel


FOUR_PI = 4.0 * np.pi
FOUR_THIRDS_PI = (4.0 / 3.0) * np.pi


class HybridQSSAGasSwellingModel(RefactoredGasSwellingModel):
    """
    Hybrid reduced-order model.

    One vacancy-interstitial pair remains dynamic while the harder pair is
    eliminated through a relaxed algebraic closure during early transients.
    """

    reduced_state_size = 11
    full_state_size = 17

    def __init__(
        self,
        params: Optional[Dict] = None,
        dynamic_pair: str = 'auto',
        relaxation_factor: float = 5.0,
        min_relaxation_time: float = 1e-6,
        max_relaxation_time: float = 1e4
    ):
        self.requested_dynamic_pair = dynamic_pair
        self.relaxation_factor = relaxation_factor
        self.min_relaxation_time = min_relaxation_time
        self.max_relaxation_time = max_relaxation_time
        self.dynamic_pair = 'bulk'
        self.eliminated_pair = 'boundary'
        super().__init__(params)
        self._refresh_runtime_constants()

    def _initialize_state(self) -> np.ndarray:
        Nc_init = 5.0
        Cg_init = 0.0
        Cc_init = 0.0
        R_init = 1e-8

        if self.requested_dynamic_pair == 'auto':
            self.dynamic_pair = select_dynamic_pair(self.params, tie_preference='boundary')
        elif self.requested_dynamic_pair in {'bulk', 'boundary'}:
            self.dynamic_pair = self.requested_dynamic_pair
        else:
            raise ValueError("dynamic_pair must be 'auto', 'bulk', or 'boundary'")

        self.eliminated_pair = 'boundary' if self.dynamic_pair == 'bulk' else 'bulk'
        cv0, ci0 = self.get_thermal_equilibrium_concentrations()

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
                cv0,
                ci0,
                0.0,
            ],
            dtype=float,
        )

    def _equations(self, t: float, state: np.ndarray) -> np.ndarray:
        return self._equations_wrapper(t, state)

    @staticmethod
    def _clamp_scalar(value: float, lower: float, upper: float) -> float:
        if value < lower:
            return lower
        if value > upper:
            return upper
        return value

    def _refresh_runtime_constants(self) -> None:
        temperature = self.params['temperature']
        kB_ev = self.params['kB_ev']

        self._temperature = temperature
        self._kB = self.params['kB']
        self._kB_ev = kB_ev
        self._surface_energy = self.params['surface_energy']
        self._hydrastatic_pressure = self.params['hydrastatic_pressure']
        self._omega = self.params['Omega']
        self._grain_diameter = self.params['grain_diameter']
        self._fission_rate = self.params['fission_rate']
        self._gas_production_rate = self.params['gas_production_rate']
        self._resolution_rate = self.params['resolution_rate']
        self._Fnb = self.params['Fnb']
        self._Fnf = self.params['Fnf']
        self._Xe_radii = self.params['Xe_radii']
        self._eos_model = self.params.get('eos_model', 'ideal')
        self._kv_param = self.params['kv_param']
        self._ki_param = self.params['ki_param']

        self._Dv = self.params['Dv0'] * np.exp(-self.params['Evm'] / (kB_ev * temperature))
        self._Di = self.params['Di0'] * np.exp(-self.params['Eim'] / (kB_ev * temperature))
        self._Dgb = (
            self.params['Dgb_prefactor'] * np.exp(-self.params['Dgb_activation_energy'] / (kB_ev * temperature))
            + self.params['Dgb_fission_term'] * self._fission_rate
        )
        self._Dgf = self.params['Dgf_multiplier'] * self._Dgb
        self._phi = self._fission_rate * self.params['displacement_rate']
        self._alpha = 4.0 * np.pi * self.params['recombination_radius'] * (self._Dv + self._Di) / self._omega
        self._cv0, self._ci0 = self.get_thermal_equilibrium_concentrations()
        # Preserve the historical argument order used by the ODE module so the
        # optimized fast path matches current baseline behavior.
        self._cv0_ode = calculate_cv0(
            self._temperature,
            self.params['Evf_coeffs'],
            self.params.get('Evfmuti', 1.0),
            self._kB_ev,
        )
        self._ci0_ode = calculate_ci0(
            self._temperature,
            self.params['Eif_coeffs'],
            self._kB_ev,
        )
        self._k_vd2 = self.params['Zv'] * self.params['dislocation_density']
        self._k_id2 = self.params['Zi'] * self.params['dislocation_density']

    def _compute_sink_strengths(
        self,
        Rcb: float,
        Ccb: float,
        Rcf: float,
        Ccf: float
    ) -> Tuple[float, float, float, float, float, float, float, float]:
        kvc2_b = FOUR_PI * Rcb * Ccb
        kic2_b = kvc2_b
        kvc2_f = FOUR_PI * Rcf * Ccf
        kic2_f = kvc2_f

        kvb2_total = kvc2_b + self._k_vd2
        kib2_total = kic2_b + self._k_id2
        kvf2_total = kvc2_f + self._k_vd2
        kif2_total = kic2_f + self._k_id2

        return (
            kvc2_b,
            kic2_b,
            kvc2_f,
            kic2_f,
            kvb2_total,
            kib2_total,
            kvf2_total,
            kif2_total,
        )

    def _compute_defect_fields(
        self,
        t: float,
        state: np.ndarray
    ) -> Tuple[Tuple[float, float, float, float], Tuple[float, float, float, float, float, float, float, float], Tuple[float, float, float, float, float, float, float, float, float]]:
        Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, defect_1, defect_2, released_gas = state

        Rcb_safe = self._clamp_scalar(float(Rcb), 1e-12, 1e-4)
        Rcf_safe = self._clamp_scalar(float(Rcf), 1e-12, 1e-4)
        Ccb_safe = max(float(Ccb), 0.0)
        Ccf_safe = max(float(Ccf), 0.0)
        Ncb_safe = max(float(Ncb), 0.0)
        Ncf_safe = max(float(Ncf), 0.0)
        released_gas_safe = max(float(released_gas), 0.0)

        sink_strengths = self._compute_sink_strengths(Rcb_safe, Ccb_safe, Rcf_safe, Ccf_safe)
        _, _, _, _, kvb2_total, kib2_total, kvf2_total, kif2_total = sink_strengths

        if self.dynamic_pair == 'bulk':
            cvb = max(float(defect_1), 0.0)
            cib = max(float(defect_2), 0.0)
            cvf, cif, relaxation_tau, relaxation_rate_fast = calculate_relaxed_qssa_pair(
                kvf2_total * self._Dv,
                kif2_total * self._Di,
                self._phi,
                self._alpha,
                t,
                self._cv0_ode,
                self._ci0_ode,
                relaxation_factor=self.relaxation_factor,
                min_tau=self.min_relaxation_time,
                max_tau=self.max_relaxation_time,
            )
        else:
            cvf = max(float(defect_1), 0.0)
            cif = max(float(defect_2), 0.0)
            cvb, cib, relaxation_tau, relaxation_rate_fast = calculate_relaxed_qssa_pair(
                kvb2_total * self._Dv,
                kib2_total * self._Di,
                self._phi,
                self._alpha,
                t,
                self._cv0_ode,
                self._ci0_ode,
                relaxation_factor=self.relaxation_factor,
                min_tau=self.min_relaxation_time,
                max_tau=self.max_relaxation_time,
            )

        geometry = (
            float(Cgb),
            Ccb_safe,
            Ncb_safe,
            Rcb_safe,
            float(Cgf),
            Ccf_safe,
            Ncf_safe,
            Rcf_safe,
            released_gas_safe,
        )
        defects = (cvb, cib, cvf, cif)
        relaxation = (
            relaxation_tau,
            relaxation_rate_fast,
            kvb2_total,
            kib2_total,
            kvf2_total,
            kif2_total,
            sink_strengths[0],
            sink_strengths[1],
            sink_strengths[2],
            sink_strengths[3],
        )
        return geometry, defects, relaxation

    def _equations_wrapper(self, t: float, state: np.ndarray, params: Dict = None) -> np.ndarray:
        _ = params
        self.current_time = t
        geometry, defects, relaxation = self._compute_defect_fields(t, state)
        Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, _ = geometry
        cvb, cib, cvf, cif = defects
        _, _, kvb2_total, kib2_total, kvf2_total, kif2_total, kvc2_b, kic2_b, kvc2_f, kic2_f = relaxation

        recombination_b = self._alpha * cvb * cib
        recombination_f = self._alpha * cvf * cif
        dcvb_dt = self._phi - kvb2_total * self._Dv * cvb - recombination_b
        dcib_dt = self._phi - kib2_total * self._Di * cib - recombination_b
        dcvf_dt = self._phi - kvf2_total * self._Dv * cvf - recombination_f
        dcif_dt = self._phi - kif2_total * self._Di * cif - recombination_f

        dRcb_dt, dRcf_dt, _, _ = calculate_cavity_radius_derivatives(
            Rcb,
            Rcf,
            Ccb,
            Ccf,
            cvb,
            cib,
            cvf,
            cif,
            Ncb,
            Ncf,
            self._cv0_ode,
            kvc2_b,
            kic2_b,
            kvc2_f,
            kic2_f,
            self._Dv,
            self._Di,
            self._temperature,
            self._kB,
            self._surface_energy,
            self._hydrastatic_pressure,
            self._omega,
            self._eos_model,
        )

        dCgb_dt, dCcb_dt, dNcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dh_dt = calculate_gas_concentration_derivatives(
            Cgb,
            Ccb,
            Ncb,
            Cgf,
            Ccf,
            Ncf,
            Rcb,
            Rcf,
            self._grain_diameter,
            self._Dgb,
            self._Dgf,
            self._fission_rate,
            self._gas_production_rate,
            self._resolution_rate,
            self._Fnb,
            self._Fnf,
            self._Xe_radii,
            self._eos_model,
            self._temperature,
            self._kB,
            self._omega,
        )

        if self.dynamic_pair == 'bulk':
            defect_terms = (
                self._clamp_scalar(dcvb_dt, -1e8, 5e20),
                self._clamp_scalar(dcib_dt, -1e8, 5e20),
            )
        else:
            defect_terms = (
                self._clamp_scalar(dcvf_dt, -1e8, 1e8),
                self._clamp_scalar(dcif_dt, -1e8, 1e8),
            )

        derivatives = np.array(
            [
                self._clamp_scalar(dCgb_dt, -1e20, 1e20),
                self._clamp_scalar(dCcb_dt, -1e20, 1e20),
                self._clamp_scalar(dNcb_dt, -1e8, 1e8),
                self._clamp_scalar(dRcb_dt, 0.0, 1e5),
                self._clamp_scalar(dCgf_dt, -1e20, 5e20),
                self._clamp_scalar(dCcf_dt, -1e20, 5e20),
                self._clamp_scalar(dNcf_dt, -1e8, 1e8),
                self._clamp_scalar(dRcf_dt, 0.0, 1e5),
                defect_terms[0],
                defect_terms[1],
                self._clamp_scalar(dh_dt, -1e30, 1e30),
            ],
            dtype=float,
        )
        derivatives = np.where(np.isnan(derivatives), 0.0, derivatives)
        derivatives = np.where(np.isinf(derivatives), 1e10 * np.sign(derivatives), derivatives)

        if self.debug_config.enabled:
            self._record_debug_info(t, state, derivatives)

        return derivatives

    def _record_debug_info(self, t: float, state: np.ndarray, derivatives: np.ndarray):
        _ = derivatives
        geometry, defects, _ = self._compute_defect_fields(t, state)
        _, Ccb, Ncb, Rcb, _, Ccf, Ncf, Rcf, _ = geometry

        Pg_b = self.get_gas_pressure(Rcb, Ncb, location='bulk')
        Pg_f = self.get_gas_pressure(Rcf, Ncf, location='boundary')
        V_bubble_b = FOUR_THIRDS_PI * Rcb ** 3 * Ccb
        V_bubble_f = FOUR_THIRDS_PI * Rcf ** 3 * Ccf
        swelling = (V_bubble_b + V_bubble_f) * 100.0

        update_debug_history(
            self.debug_history,
            time=t,
            Rcb=Rcb,
            Rcf=Rcf,
            Ncb=Ncb,
            Ncf=Ncf,
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
            3: [1, 2, 3, 8, 9],
            4: [0, 4, 5, 6, 7],
            5: [4, 6],
            6: [4, 5, 6, 7],
            7: [5, 6, 7, 8, 9],
            8: [1, 3, 5, 7, 8, 9],
            9: [1, 3, 5, 7, 8, 9],
            10: [4, 5, 6, 7],
        }

        for row, cols in dependencies.items():
            pattern[row, cols] = True

        return csr_matrix(pattern)

    def _reconstruct_results(self, reduced_y: np.ndarray, time: np.ndarray) -> Dict[str, np.ndarray]:
        reduced_y = np.maximum(reduced_y, 0.0)
        n_points = reduced_y.shape[1]

        cvb = np.empty(n_points, dtype=float)
        cib = np.empty(n_points, dtype=float)
        cvf = np.empty(n_points, dtype=float)
        cif = np.empty(n_points, dtype=float)
        relaxation_tau = np.empty(n_points, dtype=float)

        for idx in range(n_points):
            _, defects, relaxation = self._compute_defect_fields(float(time[idx]), reduced_y[:, idx])
            cvb[idx], cib[idx], cvf[idx], cif[idx] = defects
            relaxation_tau[idx] = relaxation[0]

        kvb = np.full(n_points, self._kv_param, dtype=float)
        kib = np.full(n_points, self._ki_param, dtype=float)
        kvf = np.full(n_points, self._kv_param, dtype=float)
        kif = np.full(n_points, self._ki_param, dtype=float)

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
            'released_gas': reduced_y[10],
            'kvb': kvb,
            'kib': kib,
            'kvf': kvf,
            'kif': kif,
            'relaxation_tau': relaxation_tau,
        }

        results['swelling'] = (
            FOUR_THIRDS_PI * results['Rcb'] ** 3 * results['Ccb']
            + FOUR_THIRDS_PI * results['Rcf'] ** 3 * results['Ccf']
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
        _ = max_steps
        self._refresh_runtime_constants()
        self.debug_config.enabled = debug_enabled
        self.debug_config.time_step_interval = output_interval

        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        valid_methods = {'RK23', 'RK45', 'LSODA', 'BDF', 'Radau'}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Valid methods: {', '.join(sorted(valid_methods))}")

        solve_kwargs = {
            'fun': self._equations,
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

        results = self._reconstruct_results(sol.y, sol.t)
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
                'dynamic_pair': self.dynamic_pair,
                'eliminated_pair': self.eliminated_pair,
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
            f"HybridQSSAGasSwellingModel(dynamic_pair='{self.dynamic_pair}', "
            f"temperature={temp:.2f} K, "
            f"fission_rate={fission_rate:.2e} /m³/s, "
            f"eos_model='{eos_model}')"
        )
