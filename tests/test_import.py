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


def test_import_gas_pressure_evolution_plot():
    """Test that plot_gas_pressure_evolution can be imported"""
    from gas_swelling import plot_gas_pressure_evolution
    assert plot_gas_pressure_evolution is not None
    assert callable(plot_gas_pressure_evolution)


def test_import_all_evolution_plots():
    """Test that all evolution plot functions can be imported"""
    from gas_swelling import (
        plot_swelling_evolution,
        plot_bubble_radius_evolution,
        plot_gas_concentration_evolution,
        plot_bubble_concentration_evolution,
        plot_gas_atoms_evolution,
        plot_gas_pressure_evolution,
        plot_defect_concentration_evolution,
        plot_released_gas_evolution,
        plot_multi_panel_evolution,
    )

    assert plot_swelling_evolution is not None
    assert plot_bubble_radius_evolution is not None
    assert plot_gas_concentration_evolution is not None
    assert plot_bubble_concentration_evolution is not None
    assert plot_gas_atoms_evolution is not None
    assert plot_gas_pressure_evolution is not None
    assert plot_defect_concentration_evolution is not None
    assert plot_released_gas_evolution is not None
    assert plot_multi_panel_evolution is not None

