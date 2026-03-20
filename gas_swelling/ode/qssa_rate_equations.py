"""
Reduced-order QSSA rate equations for the gas swelling model.

This module removes the fast point-defect ODEs from the integrated state and
reconstructs vacancy/interstitial concentrations algebraically using a
quasi-steady-state approximation (QSSA). The remaining integrated state keeps
the slower gas-transport and cavity-growth variables:

0: Cgb  - bulk gas concentration
1: Ccb  - bulk cavity concentration
2: Ncb  - gas atoms per bulk cavity
3: Rcb  - bulk cavity radius
4: Cgf  - boundary gas concentration
5: Ccf  - boundary cavity concentration
6: Ncf  - gas atoms per boundary cavity
7: Rcf  - boundary cavity radius
8: released_gas - cumulative released gas
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from ..physics.thermal import calculate_ci0, calculate_cv0
from .rate_equations import (
    calculate_cavity_radius_derivatives,
    calculate_gas_concentration_derivatives,
    calculate_point_defect_derivatives,
    calculate_sink_strengths,
)


def _calculate_qssa_pair(A_v: float, A_i: float, phi: float, alpha: float) -> Tuple[float, float]:
    """
    Solve the positive steady-state pair for vacancy/interstitial concentrations.

    The fast subsystem is:
        dcv/dt = phi - A_v * cv - alpha * cv * ci
        dci/dt = phi - A_i * ci - alpha * cv * ci

    Setting both derivatives to zero gives the stable positive branch:
        cv = 2 phi / (A_v * (1 + sqrt(1 + 4 alpha phi / (A_v A_i))))
        ci = 2 phi / (A_i * (1 + sqrt(1 + 4 alpha phi / (A_v A_i))))

    The stable form above avoids cancellation when coupling is weak.
    """
    A_v = max(float(A_v), 1e-30)
    A_i = max(float(A_i), 1e-30)
    phi = max(float(phi), 0.0)
    alpha = max(float(alpha), 0.0)

    if phi == 0.0:
        return 0.0, 0.0

    if alpha <= 1e-30:
        return phi / A_v, phi / A_i

    coupling = np.clip(4.0 * alpha * phi / (A_v * A_i), 0.0, 1e300)
    sqrt_term = np.sqrt(1.0 + coupling)
    denominator = 1.0 + sqrt_term

    cv_ss = 2.0 * phi / (A_v * denominator)
    ci_ss = 2.0 * phi / (A_i * denominator)

    return float(cv_ss), float(ci_ss)


def calculate_qssa_point_defect_concentrations(
    kvb2_total: float,
    kib2_total: float,
    kvf2_total: float,
    kif2_total: float,
    Dv: float,
    Di: float,
    phi: float,
    alpha: float
) -> Tuple[float, float, float, float]:
    """
    Reconstruct bulk/boundary point-defect concentrations using QSSA.
    """
    cvb, cib = _calculate_qssa_pair(kvb2_total * Dv, kib2_total * Di, phi, alpha)
    cvf, cif = _calculate_qssa_pair(kvf2_total * Dv, kif2_total * Di, phi, alpha)
    return cvb, cib, cvf, cif


def _calculate_pair_relaxation_rates(
    A_v: float,
    A_i: float,
    cv: float,
    ci: float,
    alpha: float
) -> Tuple[float, float]:
    """
    Estimate fast/slow decay rates from the local linearized defect subsystem.
    """
    A_v = max(float(A_v), 0.0)
    A_i = max(float(A_i), 0.0)
    cv = max(float(cv), 0.0)
    ci = max(float(ci), 0.0)
    alpha = max(float(alpha), 0.0)

    m11 = A_v + alpha * ci
    m22 = A_i + alpha * cv
    off12 = alpha * cv
    off21 = alpha * ci

    trace = m11 + m22
    det = max(m11 * m22 - off12 * off21, 0.0)
    disc = max(trace * trace - 4.0 * det, 0.0)
    root = np.sqrt(disc)

    lambda_fast = 0.5 * (trace + root)
    lambda_slow = max(0.5 * (trace - root), 0.0)
    return float(lambda_fast), float(lambda_slow)


def calculate_relaxed_qssa_pair(
    A_v: float,
    A_i: float,
    phi: float,
    alpha: float,
    time: float,
    cv_initial: float,
    ci_initial: float,
    relaxation_factor: float = 5.0,
    min_tau: float = 1e-6,
    max_tau: float = 1e4
) -> Tuple[float, float, float, float]:
    """
    Blend thermal-initial and QSSA defect concentrations during early transients.

    The eliminated pair is not snapped to its steady-state value at t=0.
    Instead we use an exponential relaxation toward the QSSA target:

        c_eff(t) = c_ss + exp(-t / tau) * (c_init - c_ss)

    where tau is derived from the local linearized defect decay rate and then
    widened by `relaxation_factor` to make the initial transition less abrupt.
    """
    cv_ss, ci_ss = _calculate_qssa_pair(A_v, A_i, phi, alpha)
    lambda_fast, lambda_slow = _calculate_pair_relaxation_rates(A_v, A_i, cv_ss, ci_ss, alpha)

    reference_rate = max(lambda_fast, lambda_slow, 1e-30)
    relaxation_factor = max(float(relaxation_factor), 1.0)
    tau = np.clip(relaxation_factor / reference_rate, min_tau, max_tau)

    weight = np.exp(-max(float(time), 0.0) / tau)
    cv_relaxed = cv_ss + weight * (max(float(cv_initial), 0.0) - cv_ss)
    ci_relaxed = ci_ss + weight * (max(float(ci_initial), 0.0) - ci_ss)

    return float(cv_relaxed), float(ci_relaxed), float(tau), float(lambda_fast)


def select_dynamic_pair(
    params: Dict,
    tie_preference: str = 'boundary'
) -> str:
    """
    Choose which defect pair remains dynamic in the hybrid-QSSA model.

    The pair with the larger linearized relaxation rate is treated as the
    "harder" pair and is therefore eliminated algebraically. If both pairs are
    effectively tied, we keep the boundary pair dynamic. Empirically this gives
    a much closer match to the full model while still reducing the state size.
    """
    if tie_preference not in {'bulk', 'boundary'}:
        raise ValueError("tie_preference must be 'bulk' or 'boundary'")

    probe_state = np.array([0.0, 0.0, 5.0, 1e-8, 0.0, 0.0, 5.0, 1e-8, 0.0], dtype=float)
    fields = calculate_qssa_auxiliary_fields(probe_state, params)
    sink_strengths = fields['sink_strengths']

    bulk_fast, _ = _calculate_pair_relaxation_rates(
        sink_strengths['kvb2_total'] * fields['Dv'],
        sink_strengths['kib2_total'] * fields['Di'],
        fields['cvb'],
        fields['cib'],
        fields['alpha'],
    )
    boundary_fast, _ = _calculate_pair_relaxation_rates(
        sink_strengths['kvf2_total'] * fields['Dv'],
        sink_strengths['kif2_total'] * fields['Di'],
        fields['cvf'],
        fields['cif'],
        fields['alpha'],
    )

    if np.isclose(bulk_fast, boundary_fast, rtol=1e-3, atol=1e-12):
        return tie_preference

    # Keep the less stiff pair dynamic, eliminate the harder pair.
    return 'boundary' if bulk_fast > boundary_fast else 'bulk'


def calculate_qssa_auxiliary_fields(state: np.ndarray, params: Dict) -> Dict[str, float]:
    """
    Build auxiliary quantities needed by the reduced-order model.

    This helper is shared by the RHS and result reconstruction so the
    experimental model uses one consistent QSSA closure everywhere.
    """
    Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, released_gas = state

    Rcb_safe = float(np.clip(Rcb, 1e-12, 1e-4))
    Rcf_safe = float(np.clip(Rcf, 1e-12, 1e-4))
    Ccb_safe = max(float(Ccb), 0.0)
    Ccf_safe = max(float(Ccf), 0.0)

    T = params['temperature']
    kB_ev = params['kB_ev']
    Dv = params['Dv0'] * np.exp(-params['Evm'] / (kB_ev * T))
    Di = params['Di0'] * np.exp(-params['Eim'] / (kB_ev * T))
    Dgb = (
        params['Dgb_prefactor'] * np.exp(-params['Dgb_activation_energy'] / (kB_ev * T))
        + params['Dgb_fission_term'] * params['fission_rate']
    )
    Dgf = params['Dgf_multiplier'] * Dgb

    phi = params['fission_rate'] * params['displacement_rate']
    alpha = 4.0 * np.pi * params['recombination_radius'] * (Dv + Di) / params['Omega']

    sink_strengths = calculate_sink_strengths(
        Rcb_safe,
        Rcf_safe,
        Ccb_safe,
        Ccf_safe,
        params['Zv'],
        params['Zi'],
        params['dislocation_density'],
    )

    cvb, cib, cvf, cif = calculate_qssa_point_defect_concentrations(
        sink_strengths['kvb2_total'],
        sink_strengths['kib2_total'],
        sink_strengths['kvf2_total'],
        sink_strengths['kif2_total'],
        Dv,
        Di,
        phi,
        alpha,
    )

    # Preserve the current legacy argument order used by the full model so the
    # experimental QSSA path differs numerically mainly because of the closure,
    # not because of unrelated physics changes.
    cv0 = calculate_cv0(
        temperature=T,
        Evf_coeffs=params['Evf_coeffs'],
        kB_ev=kB_ev,
        Evfmuti=params.get('Evfmuti', 1.0),
    )

    return {
        'Cgb': float(Cgb),
        'Ccb': Ccb_safe,
        'Ncb': max(float(Ncb), 0.0),
        'Rcb': Rcb_safe,
        'Cgf': float(Cgf),
        'Ccf': Ccf_safe,
        'Ncf': max(float(Ncf), 0.0),
        'Rcf': Rcf_safe,
        'released_gas': max(float(released_gas), 0.0),
        'T': T,
        'Dv': float(Dv),
        'Di': float(Di),
        'Dgb': float(Dgb),
        'Dgf': float(Dgf),
        'phi': float(phi),
        'alpha': float(alpha),
        'cv0': float(cv0),
        'cvb': cvb,
        'cib': cib,
        'cvf': cvf,
        'cif': cif,
        'sink_strengths': sink_strengths,
    }


def calculate_hybrid_qssa_auxiliary_fields(
    state: np.ndarray,
    params: Dict,
    time: float,
    dynamic_pair: str = 'bulk',
    relaxation_factor: float = 5.0,
    min_relaxation_time: float = 1e-6,
    max_relaxation_time: float = 1e4
) -> Dict[str, float]:
    """
    Auxiliary fields for the hybrid-QSSA model.

    State layout:
    - if dynamic_pair == 'bulk':
      [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, released_gas]
    - if dynamic_pair == 'boundary':
      [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvf, cif, released_gas]
    """
    if dynamic_pair not in {'bulk', 'boundary'}:
        raise ValueError("dynamic_pair must be 'bulk' or 'boundary'")

    Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, defect_1, defect_2, released_gas = state

    base_fields = calculate_qssa_auxiliary_fields(
        np.array([Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, released_gas], dtype=float),
        params,
    )
    sink_strengths = base_fields['sink_strengths']

    ci0 = calculate_ci0(params['temperature'], params['Eif_coeffs'], params['kB_ev'])

    if dynamic_pair == 'bulk':
        cvb = max(float(defect_1), 0.0)
        cib = max(float(defect_2), 0.0)
        cvf, cif, tau, lambda_fast = calculate_relaxed_qssa_pair(
            sink_strengths['kvf2_total'] * base_fields['Dv'],
            sink_strengths['kif2_total'] * base_fields['Di'],
            base_fields['phi'],
            base_fields['alpha'],
            time,
            base_fields['cv0'],
            ci0,
            relaxation_factor=relaxation_factor,
            min_tau=min_relaxation_time,
            max_tau=max_relaxation_time,
        )
        eliminated_pair = 'boundary'
    else:
        cvf = max(float(defect_1), 0.0)
        cif = max(float(defect_2), 0.0)
        cvb, cib, tau, lambda_fast = calculate_relaxed_qssa_pair(
            sink_strengths['kvb2_total'] * base_fields['Dv'],
            sink_strengths['kib2_total'] * base_fields['Di'],
            base_fields['phi'],
            base_fields['alpha'],
            time,
            base_fields['cv0'],
            ci0,
            relaxation_factor=relaxation_factor,
            min_tau=min_relaxation_time,
            max_tau=max_relaxation_time,
        )
        eliminated_pair = 'bulk'

    fields = dict(base_fields)
    fields.update(
        {
            'cvb': cvb,
            'cib': cib,
            'cvf': cvf,
            'cif': cif,
            'dynamic_pair': dynamic_pair,
            'eliminated_pair': eliminated_pair,
            'relaxation_tau': tau,
            'relaxation_rate_fast': lambda_fast,
        }
    )
    return fields


def swelling_qssa_ode_system(t: float, state: np.ndarray, params: Dict) -> np.ndarray:
    """
    Reduced-order gas swelling ODE system with algebraic point-defect closure.
    """
    _ = t
    fields = calculate_qssa_auxiliary_fields(state, params)
    sink_strengths = fields['sink_strengths']

    dRcb_dt, dRcf_dt, _, _ = calculate_cavity_radius_derivatives(
        fields['Rcb'],
        fields['Rcf'],
        fields['Ccb'],
        fields['Ccf'],
        fields['cvb'],
        fields['cib'],
        fields['cvf'],
        fields['cif'],
        fields['Ncb'],
        fields['Ncf'],
        fields['cv0'],
        sink_strengths['kvc2_b'],
        sink_strengths['kic2_b'],
        sink_strengths['kvc2_f'],
        sink_strengths['kic2_f'],
        fields['Dv'],
        fields['Di'],
        fields['T'],
        params['kB'],
        params['surface_energy'],
        params['hydrastatic_pressure'],
        params['Omega'],
        params.get('eos_model', 'ideal'),
    )

    dCgb_dt, dCcb_dt, dNcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dh_dt = (
        calculate_gas_concentration_derivatives(
            fields['Cgb'],
            fields['Ccb'],
            fields['Ncb'],
            fields['Cgf'],
            fields['Ccf'],
            fields['Ncf'],
            fields['Rcb'],
            fields['Rcf'],
            params['grain_diameter'],
            fields['Dgb'],
            fields['Dgf'],
            params['fission_rate'],
            params['gas_production_rate'],
            params['resolution_rate'],
            params['Fnb'],
            params['Fnf'],
            params['Xe_radii'],
            params.get('eos_model', 'ideal'),
            fields['T'],
            params['kB'],
            params['Omega'],
        )
    )

    derivatives = np.array(
        [
            np.clip(dCgb_dt, -1e20, 1e20),
            np.clip(dCcb_dt, -1e20, 1e20),
            np.clip(dNcb_dt, -1e8, 1e8),
            np.clip(dRcb_dt, 0.0, 1e5),
            np.clip(dCgf_dt, -1e20, 5e20),
            np.clip(dCcf_dt, -1e20, 5e20),
            np.clip(dNcf_dt, -1e8, 1e8),
            np.clip(dRcf_dt, 0.0, 1e5),
            np.clip(dh_dt, -1e30, 1e30),
        ],
        dtype=float,
    )

    derivatives = np.where(np.isnan(derivatives), 0.0, derivatives)
    derivatives = np.where(np.isinf(derivatives), 1e10 * np.sign(derivatives), derivatives)
    return derivatives


def swelling_hybrid_qssa_ode_system(
    t: float,
    state: np.ndarray,
    params: Dict,
    dynamic_pair: str = 'bulk',
    relaxation_factor: float = 5.0,
    min_relaxation_time: float = 1e-6,
    max_relaxation_time: float = 1e4
) -> np.ndarray:
    """
    Hybrid reduced-order gas swelling ODE system.

    One defect pair is integrated explicitly while the stiffer pair is replaced
    by a relaxed algebraic closure.
    """
    fields = calculate_hybrid_qssa_auxiliary_fields(
        state,
        params,
        t,
        dynamic_pair=dynamic_pair,
        relaxation_factor=relaxation_factor,
        min_relaxation_time=min_relaxation_time,
        max_relaxation_time=max_relaxation_time,
    )
    sink_strengths = fields['sink_strengths']

    dcvb_dt, dcib_dt, dcvf_dt, dcif_dt = calculate_point_defect_derivatives(
        fields['cvb'],
        fields['cib'],
        fields['cvf'],
        fields['cif'],
        sink_strengths['kvb2_total'],
        sink_strengths['kib2_total'],
        sink_strengths['kvf2_total'],
        sink_strengths['kif2_total'],
        fields['Dv'],
        fields['Di'],
        fields['phi'],
        fields['alpha'],
    )

    dRcb_dt, dRcf_dt, _, _ = calculate_cavity_radius_derivatives(
        fields['Rcb'],
        fields['Rcf'],
        fields['Ccb'],
        fields['Ccf'],
        fields['cvb'],
        fields['cib'],
        fields['cvf'],
        fields['cif'],
        fields['Ncb'],
        fields['Ncf'],
        fields['cv0'],
        sink_strengths['kvc2_b'],
        sink_strengths['kic2_b'],
        sink_strengths['kvc2_f'],
        sink_strengths['kic2_f'],
        fields['Dv'],
        fields['Di'],
        fields['T'],
        params['kB'],
        params['surface_energy'],
        params['hydrastatic_pressure'],
        params['Omega'],
        params.get('eos_model', 'ideal'),
    )

    dCgb_dt, dCcb_dt, dNcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dh_dt = (
        calculate_gas_concentration_derivatives(
            fields['Cgb'],
            fields['Ccb'],
            fields['Ncb'],
            fields['Cgf'],
            fields['Ccf'],
            fields['Ncf'],
            fields['Rcb'],
            fields['Rcf'],
            params['grain_diameter'],
            fields['Dgb'],
            fields['Dgf'],
            params['fission_rate'],
            params['gas_production_rate'],
            params['resolution_rate'],
            params['Fnb'],
            params['Fnf'],
            params['Xe_radii'],
            params.get('eos_model', 'ideal'),
            fields['T'],
            params['kB'],
            params['Omega'],
        )
    )

    if dynamic_pair == 'bulk':
        defect_terms = [
            np.clip(dcvb_dt, -1e8, 5e20),
            np.clip(dcib_dt, -1e8, 5e20),
        ]
    else:
        defect_terms = [
            np.clip(dcvf_dt, -1e8, 1e8),
            np.clip(dcif_dt, -1e8, 1e8),
        ]

    derivatives = np.array(
        [
            np.clip(dCgb_dt, -1e20, 1e20),
            np.clip(dCcb_dt, -1e20, 1e20),
            np.clip(dNcb_dt, -1e8, 1e8),
            np.clip(dRcb_dt, 0.0, 1e5),
            np.clip(dCgf_dt, -1e20, 5e20),
            np.clip(dCcf_dt, -1e20, 5e20),
            np.clip(dNcf_dt, -1e8, 1e8),
            np.clip(dRcf_dt, 0.0, 1e5),
            defect_terms[0],
            defect_terms[1],
            np.clip(dh_dt, -1e30, 1e30),
        ],
        dtype=float,
    )

    derivatives = np.where(np.isnan(derivatives), 0.0, derivatives)
    derivatives = np.where(np.isinf(derivatives), 1e10 * np.sign(derivatives), derivatives)
    return derivatives
