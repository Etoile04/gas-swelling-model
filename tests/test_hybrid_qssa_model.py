"""
Smoke tests for the hybrid relaxed-QSSA gas swelling model.
"""

import numpy as np

from gas_swelling import HybridQSSAGasSwellingModel, create_default_parameters


def test_import_hybrid_qssa_model():
    assert HybridQSSAGasSwellingModel is not None


def test_hybrid_qssa_initialization():
    model = HybridQSSAGasSwellingModel()
    assert model is not None
    assert len(model.initial_state) == 11
    assert model.dynamic_pair in {'bulk', 'boundary'}
    assert model.eliminated_pair in {'bulk', 'boundary'}
    assert model.dynamic_pair != model.eliminated_pair


def test_hybrid_qssa_solve_smoke():
    params = create_default_parameters()
    model = HybridQSSAGasSwellingModel(params)
    t_eval = np.linspace(0.0, 100.0, 8)

    results = model.solve(t_span=(0.0, 100.0), t_eval=t_eval, method='LSODA')

    expected_keys = [
        'time', 'Cgb', 'Ccb', 'Ncb', 'Rcb',
        'Cgf', 'Ccf', 'Ncf', 'Rcf',
        'cvb', 'cib', 'cvf', 'cif',
        'kvb', 'kib', 'kvf', 'kif',
        'released_gas', 'swelling', 'y', 'y_reduced',
        'dynamic_pair', 'eliminated_pair', 'relaxation_tau'
    ]
    for key in expected_keys:
        assert key in results, f"Missing key: {key}"

    assert results['success'] is True
    assert len(results['time']) == len(t_eval)
    assert results['y'].shape == (17, len(t_eval))
    assert results['y_reduced'].shape == (11, len(t_eval))
    assert results['dynamic_pair'] in {'bulk', 'boundary'}
    assert results['eliminated_pair'] in {'bulk', 'boundary'}

    for key in [
        'Cgb', 'Ccb', 'Ncb', 'Rcb',
        'Cgf', 'Ccf', 'Ncf', 'Rcf',
        'cvb', 'cib', 'cvf', 'cif',
        'released_gas', 'swelling', 'relaxation_tau'
    ]:
        assert np.all(np.isfinite(results[key])), f"Non-finite values in {key}"
        assert len(results[key]) == len(t_eval), f"Wrong shape for {key}"

    assert np.all(results['relaxation_tau'] > 0.0)
    assert np.all(results['Rcb'] >= 0.0)
    assert np.all(results['Rcf'] >= 0.0)
    assert np.all(results['swelling'] >= 0.0)

