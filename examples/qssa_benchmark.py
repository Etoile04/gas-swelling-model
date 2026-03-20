"""
Benchmark the experimental QSSA gas swelling model against the refactored model.
"""

from __future__ import annotations

import time

import numpy as np

from gas_swelling import (
    HybridQSSAGasSwellingModel,
    QSSAGasSwellingModel,
    RefactoredGasSwellingModel,
    create_default_parameters,
)


def run_case(sim_time: float = 3600.0, n_points: int = 40, method: str = 'LSODA') -> None:
    params = create_default_parameters()
    t_eval = np.linspace(0.0, sim_time, n_points)

    runs = [
        ('Refactored', RefactoredGasSwellingModel(params)),
        ('QSSA', QSSAGasSwellingModel(params)),
        ('HybridQSSA', HybridQSSAGasSwellingModel(params)),
    ]

    results = {}
    timings = {}

    for label, model in runs:
        t0 = time.perf_counter()
        result = model.solve(t_span=(0.0, sim_time), t_eval=t_eval, method=method)
        timings[label] = time.perf_counter() - t0
        results[label] = result

    baseline_swelling = results['Refactored']['swelling'][-1]
    qssa_swelling = results['QSSA']['swelling'][-1]
    hybrid_swelling = results['HybridQSSA']['swelling'][-1]
    qssa_abs_diff = abs(qssa_swelling - baseline_swelling)
    qssa_rel_diff = qssa_abs_diff / max(abs(baseline_swelling), abs(qssa_swelling), 1e-30)
    hybrid_abs_diff = abs(hybrid_swelling - baseline_swelling)
    hybrid_rel_diff = hybrid_abs_diff / max(abs(baseline_swelling), abs(hybrid_swelling), 1e-30)

    print("QSSA benchmark")
    print("=" * 60)
    print(f"Simulation time: {sim_time:.1f} s")
    print(f"Output points: {n_points}")
    print(f"Method: {method}")
    print()
    print(f"Refactored model: {timings['Refactored']:.4f} s, nfev={results['Refactored'].get('nfev', 'N/A')}")
    print(f"QSSA model      : {timings['QSSA']:.4f} s, nfev={results['QSSA'].get('nfev', 'N/A')}")
    print(f"Hybrid QSSA     : {timings['HybridQSSA']:.4f} s, nfev={results['HybridQSSA'].get('nfev', 'N/A')}, dynamic_pair={results['HybridQSSA'].get('dynamic_pair')}")
    print(f"QSSA speedup    : {timings['Refactored'] / max(timings['QSSA'], 1e-12):.2f}x")
    print(f"Hybrid speedup  : {timings['Refactored'] / max(timings['HybridQSSA'], 1e-12):.2f}x")
    print()
    print(f"Final swelling (refactored): {baseline_swelling:.6e} %")
    print(f"Final swelling (QSSA)      : {qssa_swelling:.6e} %")
    print(f"QSSA absolute difference   : {qssa_abs_diff:.6e}")
    print(f"QSSA relative difference   : {qssa_rel_diff:.6e}")
    print(f"Final swelling (Hybrid)    : {hybrid_swelling:.6e} %")
    print(f"Hybrid absolute difference : {hybrid_abs_diff:.6e}")
    print(f"Hybrid relative difference : {hybrid_rel_diff:.6e}")


if __name__ == '__main__':
    run_case()
