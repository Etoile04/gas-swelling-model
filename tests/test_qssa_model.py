"""
Smoke tests for the experimental QSSA gas swelling model.
"""

import numpy as np

from gas_swelling import QSSAGasSwellingModel, create_default_parameters


def test_import_qssa_model():
    assert QSSAGasSwellingModel is not None


def test_qssa_model_initialization():
    model = QSSAGasSwellingModel()
    assert model is not None
    assert len(model.initial_state) == 9
    assert model.reduced_state_size == 9
    assert model.full_state_size == 17


def test_qssa_solve_smoke():
    params = create_default_parameters()
    model = QSSAGasSwellingModel(params)
    t_eval = np.linspace(0.0, 100.0, 8)

    results = model.solve(t_span=(0.0, 100.0), t_eval=t_eval, method='LSODA')

    expected_keys = [
        'time', 'Cgb', 'Ccb', 'Ncb', 'Rcb',
        'Cgf', 'Ccf', 'Ncf', 'Rcf',
        'cvb', 'cib', 'cvf', 'cif',
        'kvb', 'kib', 'kvf', 'kif',
        'released_gas', 'swelling', 'y', 'y_reduced'
    ]
    for key in expected_keys:
        assert key in results, f"Missing key: {key}"

    assert results['success'] is True
    assert len(results['time']) == len(t_eval)
    assert results['y'].shape == (17, len(t_eval))
    assert results['y_reduced'].shape == (9, len(t_eval))

    for key in [
        'Cgb', 'Ccb', 'Ncb', 'Rcb',
        'Cgf', 'Ccf', 'Ncf', 'Rcf',
        'cvb', 'cib', 'cvf', 'cif',
        'released_gas', 'swelling'
    ]:
        assert np.all(np.isfinite(results[key])), f"Non-finite values in {key}"
        assert len(results[key]) == len(t_eval), f"Wrong shape for {key}"

    assert np.all(results['Rcb'] >= 0.0)
    assert np.all(results['Rcf'] >= 0.0)
    assert np.all(results['swelling'] >= 0.0)

