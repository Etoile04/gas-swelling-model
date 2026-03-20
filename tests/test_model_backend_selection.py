"""
Tests for selecting reduced-order model backends through the main model entrypoint.
"""

import numpy as np
import pytest

from gas_swelling import GasSwellingModel, RefactoredGasSwellingModel, create_default_parameters
from gas_swelling.params.parameters import SimulationParameters


def test_simulation_parameters_backend_defaults():
    params = SimulationParameters()
    assert params.model_backend == 'full'
    assert params.hybrid_dynamic_pair == 'auto'
    assert params.hybrid_relaxation_factor == 5.0


def test_create_default_parameters_includes_backend_keys():
    params = create_default_parameters()
    assert params['model_backend'] == 'full'
    assert params['hybrid_dynamic_pair'] == 'auto'
    assert params['hybrid_relaxation_factor'] == 5.0


@pytest.mark.parametrize(
    ("backend", "expected_reduced_dim"),
    [
        ('qssa', 9),
        ('hybrid_qssa', 11),
    ],
)
def test_gas_swelling_model_can_select_backend(backend, expected_reduced_dim):
    params = create_default_parameters()
    params['model_backend'] = backend
    model = GasSwellingModel(params)
    t_eval = np.linspace(0.0, 100.0, 8)

    results = model.solve(t_span=(0.0, 100.0), t_eval=t_eval, method='LSODA')

    assert results['success'] is True
    assert 'y_reduced' in results
    assert results['y_reduced'].shape == (expected_reduced_dim, len(t_eval))


def test_refactored_model_backend_delegation_uses_hybrid_settings():
    params = create_default_parameters()
    params['model_backend'] = 'hybrid_qssa'
    params['hybrid_dynamic_pair'] = 'boundary'
    model = RefactoredGasSwellingModel(params)

    assert len(model.initial_state) == 11

    results = model.solve(t_span=(0.0, 100.0), t_eval=np.linspace(0.0, 100.0, 8), method='LSODA')

    assert results['success'] is True
    assert results['dynamic_pair'] == 'boundary'
    assert results['y_reduced'].shape[0] == 11


def test_invalid_model_backend_raises():
    params = create_default_parameters()
    params['model_backend'] = 'not_a_backend'

    with pytest.raises(ValueError, match="Invalid model_backend"):
        RefactoredGasSwellingModel(params)
