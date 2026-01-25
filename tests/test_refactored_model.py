"""
Test RefactoredGasSwellingModel functionality

This module contains comprehensive tests for the refactored gas swelling model,
including initialization, solving, and helper methods.
"""

import pytest
import numpy as np
from gas_swelling.models import RefactoredGasSwellingModel
from gas_swelling.params.parameters import create_default_parameters


class TestRefactoredGasSwellingModelInitialization:
    """Test model initialization and setup"""

    def test_default_initialization(self):
        """Test that model can be initialized with default parameters"""
        model = RefactoredGasSwellingModel()
        assert model is not None
        assert model.params is not None
        assert model.initial_state is not None
        assert len(model.initial_state) == 17

    def test_custom_parameters_initialization(self):
        """Test that model can be initialized with custom parameters"""
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C in Kelvin
        params['fission_rate'] = 1e19

        model = RefactoredGasSwellingModel(params)
        assert model.params['temperature'] == 773.15
        assert model.params['fission_rate'] == 1e19

    def test_initial_state_structure(self):
        """Test that initial state has correct structure"""
        model = RefactoredGasSwellingModel()
        state = model.initial_state

        # Check that state is a numpy array
        assert isinstance(state, np.ndarray)

        # Check that state has 17 elements
        assert len(state) == 17

        # Check that initial values are non-negative
        assert np.all(state >= 0)

    def test_initial_state_values(self):
        """Test that initial state values are physically reasonable"""
        model = RefactoredGasSwellingModel()
        state = model.initial_state

        # Gas concentrations should be small or zero initially
        assert state[0] >= 0  # Cgb
        assert state[4] >= 0  # Cgf

        # Cavity concentrations should be small or zero initially
        assert state[1] >= 0  # Ccb
        assert state[5] >= 0  # Ccf

        # Initial atoms per cavity should be positive
        assert state[2] > 0  # Ncb
        assert state[6] > 0  # Ncf

        # Initial radii should be positive
        assert state[3] > 0  # Rcb
        assert state[7] > 0  # Rcf

    def test_debug_initialization(self):
        """Test that debug system is properly initialized"""
        model = RefactoredGasSwellingModel()
        assert hasattr(model, 'debug_config')
        assert hasattr(model, 'debug_history')
        assert model.debug_config.enabled is False

    def test_repr(self):
        """Test string representation of model"""
        model = RefactoredGasSwellingModel()
        repr_str = repr(model)
        assert 'RefactoredGasSwellingModel' in repr_str
        assert 'temperature' in repr_str
        assert 'fission_rate' in repr_str


class TestRefactoredGasSwellingModelPhysics:
    """Test physics calculation methods"""

    def test_get_gas_pressure_bulk(self):
        """Test gas pressure calculation for bulk bubbles"""
        model = RefactoredGasSwellingModel()
        R = 1e-8  # 10 nm radius
        N = 100   # 100 atoms

        pressure = model.get_gas_pressure(R, N, location='bulk')
        assert pressure > 0
        assert isinstance(pressure, (int, float))

    def test_get_gas_pressure_boundary(self):
        """Test gas pressure calculation for boundary bubbles"""
        model = RefactoredGasSwellingModel()
        R = 1e-7  # 100 nm radius
        N = 1000  # 1000 atoms

        pressure = model.get_gas_pressure(R, N, location='boundary')
        assert pressure > 0
        assert isinstance(pressure, (int, float))

    def test_get_gas_influx(self):
        """Test gas influx calculation"""
        model = RefactoredGasSwellingModel()
        Cgb = 1e20  # Bulk gas concentration
        Cgf = 1e19  # Boundary gas concentration

        influx = model.get_gas_influx(Cgb, Cgf)
        assert influx >= 0  # Should be non-negative
        assert isinstance(influx, (int, float))

    def test_get_gas_release_rate(self):
        """Test gas release rate calculation"""
        model = RefactoredGasSwellingModel()
        Cgf = 1e20  # Boundary gas concentration
        Ccf = 1e15  # Boundary cavity concentration
        Rcf = 1e-7  # Boundary cavity radius
        Ncf = 50    # Atoms per boundary cavity

        release_rate = model.get_gas_release_rate(Cgf, Ccf, Rcf, Ncf)
        assert release_rate >= 0
        assert isinstance(release_rate, (int, float))

    def test_get_thermal_equilibrium_concentrations(self):
        """Test thermal equilibrium concentration calculation"""
        model = RefactoredGasSwellingModel()
        cv0, ci0 = model.get_thermal_equilibrium_concentrations()

        # Both concentrations should be positive
        assert cv0 > 0
        assert ci0 > 0

        # Should return a tuple
        assert isinstance(cv0, (int, float))
        assert isinstance(ci0, (int, float))


class TestRefactoredGasSwellingModelSolve:
    """Test ODE solving functionality"""

    def test_solve_with_default_parameters(self):
        """Test solving with default parameters"""
        model = RefactoredGasSwellingModel()
        t_span = (0, 86400)  # 1 day in seconds
        time_points = np.linspace(t_span[0], t_span[1], 10)

        results = model.solve(t_span=t_span, t_eval=time_points)

        # Check that results contain expected keys
        expected_keys = [
            'time', 'Cgb', 'Ccb', 'Ncb', 'Rcb',
            'Cgf', 'Ccf', 'Ncf', 'Rcf',
            'cvb', 'cib', 'kvb', 'kib',
            'cvf', 'cif', 'kvf', 'kif',
            'released_gas', 'swelling'
        ]
        for key in expected_keys:
            assert key in results, f"Missing key: {key}"

        # Check that time array has correct length
        assert len(results['time']) == len(time_points)

        # Check that all state variables have correct shape
        for key in ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf',
                    'cvb', 'cib', 'kvb', 'kib', 'cvf', 'cif', 'kvf', 'kif',
                    'released_gas', 'swelling']:
            assert len(results[key]) == len(time_points), f"Wrong shape for {key}"

    def test_solve_without_t_eval(self):
        """Test solving without specifying t_eval"""
        model = RefactoredGasSwellingModel()
        t_span = (0, 86400)  # 1 day

        results = model.solve(t_span=t_span)

        # Should create default time points
        assert 'time' in results
        assert len(results['time']) > 0
        assert results['time'][0] == t_span[0]
        assert results['time'][-1] == t_span[1]

    def test_solve_results_physical_consistency(self):
        """Test that solve results are physically consistent"""
        model = RefactoredGasSwellingModel()
        t_span = (0, 864000)  # 10 days
        time_points = np.linspace(t_span[0], t_span[1], 20)

        results = model.solve(t_span=t_span, t_eval=time_points)

        # All concentrations should be non-negative
        for key in ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf',
                    'cvb', 'cib', 'cvf', 'cif']:
            assert np.all(results[key] >= 0), f"Negative values found in {key}"

        # Radii should be positive
        assert np.all(results['Rcb'] > 0)
        assert np.all(results['Rcf'] > 0)

        # Swelling should be non-negative
        assert np.all(results['swelling'] >= 0)

        # Released gas should be non-decreasing
        released_gas = results['released_gas']
        assert np.all(np.diff(released_gas) >= -1e-10)  # Allow small numerical errors

    def test_solve_with_debug_enabled(self):
        """Test solving with debug mode enabled"""
        model = RefactoredGasSwellingModel()
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 10)

        # Enable debug mode
        model.enable_debug(time_step_interval=5)

        results = model.solve(t_span=t_span, t_eval=time_points, debug_enabled=True)

        # Check that results are still valid
        assert 'time' in results
        assert 'swelling' in results

        # Clean up - disable debug
        model.disable_debug()

    def test_solve_custom_parameters(self):
        """Test solving with custom model parameters"""
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C
        params['fission_rate'] = 5e18

        model = RefactoredGasSwellingModel(params)
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 10)

        results = model.solve(t_span=t_span, t_eval=time_points)

        # Should complete without errors
        assert 'swelling' in results
        assert len(results['time']) == len(time_points)


class TestRefactoredGasSwellingModelDebug:
    """Test debug functionality"""

    def test_enable_debug(self):
        """Test enabling debug mode"""
        model = RefactoredGasSwellingModel()
        model.enable_debug(time_step_interval=500)

        assert model.debug_config.enabled is True
        assert model.debug_config.time_step_interval == 500
        assert model.debug_config.save_to_file is True

    def test_disable_debug(self):
        """Test disabling debug mode"""
        model = RefactoredGasSwellingModel()
        model.enable_debug()
        model.disable_debug()

        assert model.debug_config.enabled is False

    def test_debug_config_persistence(self):
        """Test that debug config settings persist"""
        model = RefactoredGasSwellingModel()
        model.enable_debug(time_step_interval=100, output_file='test_debug.csv')

        assert model.debug_config.time_step_interval == 100
        assert model.debug_config.output_file == 'test_debug.csv'


class TestRefactoredGasSwellingModelIntegration:
    """Integration tests for complete workflows"""

    def test_complete_simulation_workflow(self):
        """Test complete simulation from setup to results analysis"""
        # Create model
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C
        model = RefactoredGasSwellingModel(params)

        # Run simulation
        simulation_time = 864000  # 10 days in seconds
        time_points = np.linspace(0, simulation_time, 50)
        results = model.solve(t_span=(0, simulation_time), t_eval=time_points)

        # Analyze results
        final_swelling = results['swelling'][-1]
        assert final_swelling >= 0

        final_radius_bulk = results['Rcb'][-1]
        assert final_radius_bulk > 0

        final_radius_boundary = results['Rcf'][-1]
        assert final_radius_boundary > 0

    def test_model_with_different_eos_models(self):
        """Test model with different equation of state models"""
        for eos_model in ['ideal', 'virial', 'ronchi']:
            params = create_default_parameters()
            params['eos_model'] = eos_model

            model = RefactoredGasSwellingModel(params)
            t_span = (0, 86400)  # 1 day
            time_points = np.linspace(t_span[0], t_span[1], 5)

            results = model.solve(t_span=t_span, t_eval=time_points)
            assert 'swelling' in results

    def test_multiple_sequential_solves(self):
        """Test running multiple solves sequentially"""
        model = RefactoredGasSwellingModel()
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 10)

        # First solve
        results1 = model.solve(t_span=t_span, t_eval=time_points)
        assert 'swelling' in results1

        # Second solve (should work with same model)
        results2 = model.solve(t_span=t_span, t_eval=time_points)
        assert 'swelling' in results2
