"""
Test progress indicator functionality for adaptive solver
"""

import pytest


def test_adaptive_solver_has_progress_params():
    """Test that AdaptiveSolver accepts progress-related parameters"""
    from gas_swelling.models.adaptive_solver import AdaptiveSolver
    import numpy as np

    def simple_ode(t, y):
        return -y

    # Create solver with progress parameters
    solver = AdaptiveSolver(
        fun=simple_ode,
        t_span=(0, 1),
        y0=np.array([1.0]),
        show_progress=True,
        progress_interval=10
    )

    assert solver.show_progress == True
    assert solver.progress_interval == 10


def test_adaptive_solver_progress_disabled():
    """Test that progress can be disabled"""
    from gas_swelling.models.adaptive_solver import AdaptiveSolver
    import numpy as np

    def simple_ode(t, y):
        return -y

    # Create solver with progress disabled
    solver = AdaptiveSolver(
        fun=simple_ode,
        t_span=(0, 1),
        y0=np.array([1.0]),
        show_progress=False
    )

    assert solver.show_progress == False


def test_adaptive_solver_has_print_progress_method():
    """Test that _print_progress method exists"""
    from gas_swelling.models.adaptive_solver import AdaptiveSolver
    import numpy as np

    def simple_ode(t, y):
        return -y

    solver = AdaptiveSolver(
        fun=simple_ode,
        t_span=(0, 1),
        y0=np.array([1.0])
    )

    assert hasattr(solver, '_print_progress')
    assert callable(solver._print_progress)


def test_gas_swelling_model_progress_params():
    """Test that GasSwellingModel supports progress parameters"""
    from gas_swelling import GasSwellingModel, create_default_parameters

    params = create_default_parameters()
    params['adaptive_stepping_enabled'] = True
    params['show_progress'] = True
    params['progress_interval'] = 50

    model = GasSwellingModel(params)

    assert model.params.get('show_progress') == True
    assert model.params.get('progress_interval') == 50


def test_progress_output_format():
    """Test that _print_progress produces correct format"""
    from gas_swelling.models.adaptive_solver import AdaptiveSolver
    import numpy as np
    from io import StringIO
    import sys

    def simple_ode(t, y):
        return -y

    solver = AdaptiveSolver(
        fun=simple_ode,
        t_span=(0, 100),
        y0=np.array([1.0])
    )

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    try:
        # Call _print_progress
        solver._print_progress(50.0, 1.5)
        output = captured_output.getvalue()

        # Verify output contains expected elements
        assert 'Progress:' in output
        assert '50.0%' in output
        assert 't = ' in output
        assert 'dt = ' in output
    finally:
        sys.stdout = old_stdout
