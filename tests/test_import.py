"""
Test basic import functionality of gas_swelling package
"""

import pytest


def test_import_package():
    """Test that the gas_swelling package can be imported"""
    import gas_swelling
    assert gas_swelling is not None
    assert hasattr(gas_swelling, '__version__')
    assert gas_swelling.__version__ == "0.1.0"


def test_import_gas_swelling_model():
    """Test that GasSwellingModel can be imported from package"""
    from gas_swelling import GasSwellingModel
    assert GasSwellingModel is not None


def test_import_from_models():
    """Test that GasSwellingModel can be imported from models submodule"""
    from gas_swelling.models import GasSwellingModel
    assert GasSwellingModel is not None


def test_import_parameters():
    """Test that parameter classes can be imported"""
    from gas_swelling import (
        MaterialParameters,
        SimulationParameters,
        create_default_parameters
    )
    assert MaterialParameters is not None
    assert SimulationParameters is not None
    assert create_default_parameters is not None


def test_import_constants():
    """Test that physical constants can be imported"""
    from gas_swelling import (
        BOLTZMANN_CONSTANT_EV,
        BOLTZMANN_CONSTANT_J,
        GAS_CONSTANT,
        AVOGADRO_CONSTANT
    )
    assert BOLTZMANN_CONSTANT_EV is not None
    assert BOLTZMANN_CONSTANT_J is not None
    assert GAS_CONSTANT is not None
    assert AVOGADRO_CONSTANT is not None


def test_create_default_parameters():
    """Test that create_default_parameters returns expected structure"""
    from gas_swelling import create_default_parameters

    params = create_default_parameters()
    assert isinstance(params, dict)
    assert 'temperature' in params
    assert 'fission_rate' in params
    assert 'time_step' in params


def test_gas_swelling_model_instantiation():
    """Test that GasSwellingModel can be instantiated"""
    from gas_swelling import GasSwellingModel, create_default_parameters

    params = create_default_parameters()
    model = GasSwellingModel(params)
    assert model is not None
    assert hasattr(model, 'solve')


def test_import_refactored_model():
    """Test that RefactoredGasSwellingModel can be imported"""
    from gas_swelling import RefactoredGasSwellingModel
    assert RefactoredGasSwellingModel is not None


def test_import_refactored_model_from_models():
    """Test that RefactoredGasSwellingModel can be imported from models submodule"""
    from gas_swelling.models import RefactoredGasSwellingModel
    assert RefactoredGasSwellingModel is not None


def test_import_physics_functions():
    """Test that physics functions can be imported"""
    from gas_swelling import (
        calculate_gas_pressure,
        calculate_gas_influx,
        calculate_gas_release_rate,
        calculate_cv0,
        calculate_ci0
    )
    assert calculate_gas_pressure is not None
    assert calculate_gas_influx is not None
    assert calculate_gas_release_rate is not None
    assert calculate_cv0 is not None
    assert calculate_ci0 is not None


def test_import_ode_system():
    """Test that ODE system can be imported"""
    from gas_swelling import swelling_ode_system
    assert swelling_ode_system is not None


def test_import_solvers():
    """Test that solver classes can be imported"""
    from gas_swelling import RK23Solver, EulerSolver
    assert RK23Solver is not None
    assert EulerSolver is not None


def test_import_io_utilities():
    """Test that I/O utilities can be imported"""
    from gas_swelling import (
        DebugConfig,
        DebugHistory,
        update_debug_history,
        print_simulation_summary
    )
    assert DebugConfig is not None
    assert DebugHistory is not None
    assert update_debug_history is not None
    assert print_simulation_summary is not None


def test_refactored_model_instantiation():
    """Test that RefactoredGasSwellingModel can be instantiated"""
    from gas_swelling import RefactoredGasSwellingModel

    model = RefactoredGasSwellingModel()
    assert model is not None
    assert hasattr(model, 'solve')
    assert hasattr(model, 'initial_state')
    assert len(model.initial_state) == 17
