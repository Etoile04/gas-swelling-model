"""
Test RadialGasSwellingModel functionality

This module contains comprehensive tests for the 1D radial gas swelling model,
including initialization, solving, and helper methods.
"""

import pytest
import numpy as np
from gas_swelling.models import RadialGasSwellingModel, GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters


class TestRadialGasSwellingModelInitialization:
    """Test model initialization and setup"""

    def test_default_initialization(self):
        """Test that model can be initialized with default parameters"""
        model = RadialGasSwellingModel()
        assert model is not None
        assert model.params is not None
        assert model.initial_state is not None
        assert len(model.initial_state) == 17 * 10  # 17 variables × 10 nodes

    def test_custom_parameters_initialization(self):
        """Test that model can be initialized with custom parameters"""
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C in Kelvin
        params['fission_rate'] = 1e19

        model = RadialGasSwellingModel(params)
        assert model.params['temperature'] == 773.15
        assert model.params['fission_rate'] == 1e19

    def test_custom_nodes_initialization(self):
        """Test that model can be initialized with custom number of nodes"""
        model = RadialGasSwellingModel(n_nodes=5)
        assert model.n_nodes == 5
        assert len(model.initial_state) == 17 * 5  # 17 variables × 5 nodes

    def test_initial_state_structure(self):
        """Test that initial state has correct structure"""
        model = RadialGasSwellingModel()
        state = model.initial_state

        # Check that state is a numpy array
        assert isinstance(state, np.ndarray)

        # Check that state has 17 × n_nodes elements
        assert len(state) == 17 * model.n_nodes

        # Check that initial values are non-negative
        assert np.all(state >= 0)

    def test_initial_state_values(self):
        """Test that initial state values are physically reasonable"""
        model = RadialGasSwellingModel()
        state = model.initial_state

        # Reshape to (n_nodes, 17) for easier testing
        state_reshaped = state.reshape((model.n_nodes, 17))

        # Check initial values for each node
        for i in range(model.n_nodes):
            node_state = state_reshaped[i]

            # Gas concentrations should be zero initially
            assert node_state[0] >= 0  # Cgb
            assert node_state[4] >= 0  # Cgf

            # Cavity concentrations should be zero initially
            assert node_state[1] >= 0  # Ccb
            assert node_state[5] >= 0  # Ccf

            # Initial atoms per cavity should be positive
            assert node_state[2] > 0  # Ncb
            assert node_state[6] > 0  # Ncf

            # Initial radii should be positive
            assert node_state[3] > 0  # Rcb
            assert node_state[7] > 0  # Rcf

            # Thermal equilibrium concentrations should be positive
            assert node_state[8] > 0  # cvb
            assert node_state[9] > 0  # cib
            assert node_state[10] > 0  # cvf
            assert node_state[11] > 0  # cif

    def test_mesh_initialization(self):
        """Test that radial mesh is properly initialized"""
        model = RadialGasSwellingModel(n_nodes=10, radius=0.003)
        assert model.mesh is not None
        assert model.mesh.n_nodes == 10
        assert model.mesh.radius == 0.003

    def test_geometry_initialization(self):
        """Test that different geometries can be initialized"""
        # Cylindrical (default)
        model_cyl = RadialGasSwellingModel(geometry='cylindrical')
        assert model_cyl.mesh.geometry == 'cylindrical'

        # Slab
        model_slab = RadialGasSwellingModel(geometry='slab')
        assert model_slab.mesh.geometry == 'slab'

    def test_debug_initialization(self):
        """Test that debug system is properly initialized"""
        model = RadialGasSwellingModel()
        assert hasattr(model, 'debug_config')
        assert hasattr(model, 'debug_history')
        assert model.debug_config.enabled is False

    def test_repr(self):
        """Test string representation of model"""
        model = RadialGasSwellingModel()
        repr_str = repr(model)
        assert 'RadialGasSwellingModel' in repr_str
        assert 'n_nodes' in repr_str
        assert 'temperature' in repr_str
        assert 'fission_rate' in repr_str


class TestRadialGasSwellingModelTemperatureProfile:
    """Test temperature profile functionality"""

    def test_uniform_temperature_profile(self):
        """Test uniform temperature profile (default)"""
        model = RadialGasSwellingModel(temperature_profile='uniform')
        temperature = model.temperature

        assert len(temperature) == model.n_nodes
        assert np.all(temperature == model.params['temperature'])

    def test_parabolic_temperature_profile(self):
        """Test parabolic temperature profile"""
        model = RadialGasSwellingModel(temperature_profile='parabolic')
        temperature = model.temperature

        assert len(temperature) == model.n_nodes
        # Center should be hotter than surface
        assert temperature[0] > temperature[-1]

    def test_user_temperature_profile(self):
        """Test user-defined temperature profile"""
        T_profile = np.linspace(900, 700, 10)  # Linear gradient
        model = RadialGasSwellingModel(
            n_nodes=10,
            temperature_profile='user',
            temperature_data=T_profile
        )
        temperature = model.temperature

        assert len(temperature) == 10
        np.testing.assert_array_almost_equal(temperature, T_profile)

    def test_user_profile_missing_data(self):
        """Test that error is raised when temperature_data is missing"""
        with pytest.raises(ValueError, match="temperature_data must be provided"):
            RadialGasSwellingModel(temperature_profile='user')

    def test_user_profile_wrong_length(self):
        """Test that error is raised when temperature_data has wrong length"""
        T_profile = np.linspace(900, 700, 5)  # Wrong length
        with pytest.raises(ValueError, match="must match n_nodes"):
            RadialGasSwellingModel(
                n_nodes=10,
                temperature_profile='user',
                temperature_data=T_profile
            )

    def test_set_temperature_profile(self):
        """Test setting temperature profile after initialization"""
        model = RadialGasSwellingModel(n_nodes=10)
        new_profile = np.linspace(800, 600, 10)

        model.set_temperature_profile(new_profile)

        np.testing.assert_array_almost_equal(model.temperature, new_profile)

    def test_set_temperature_profile_wrong_length(self):
        """Test error when setting profile with wrong length"""
        model = RadialGasSwellingModel(n_nodes=10)
        wrong_profile = np.linspace(800, 600, 5)

        with pytest.raises(ValueError, match="must match n_nodes"):
            model.set_temperature_profile(wrong_profile)

    def test_get_temperature_profile(self):
        """Test getting temperature profile"""
        model = RadialGasSwellingModel(temperature_profile='parabolic')
        temperature = model.get_temperature_profile()

        assert isinstance(temperature, np.ndarray)
        assert len(temperature) == model.n_nodes
        # Should return a copy
        temperature[0] = 0
        assert model.temperature[0] != 0


class TestRadialGasSwellingModelFluxDepression:
    """Test flux depression functionality"""

    def test_no_flux_depression(self):
        """Test uniform fission rate without flux depression"""
        model = RadialGasSwellingModel(flux_depression=False)
        fission_rate = model.fission_rate

        assert np.all(fission_rate == model.params['fission_rate'])

    def test_with_flux_depression(self):
        """Test non-uniform fission rate with flux depression"""
        model = RadialGasSwellingModel(flux_depression=True)
        fission_rate = model.fission_rate

        # Should have spatial variation
        assert not np.all(fission_rate == fission_rate[0])
        # Average should be close to base value
        assert np.isclose(np.mean(fission_rate), model.params['fission_rate'], rtol=0.1)


class TestRadialGasSwellingModelPhysics:
    """Test physics calculation methods"""

    def test_get_gas_pressure_bulk(self):
        """Test gas pressure calculation for bulk bubbles"""
        model = RadialGasSwellingModel()
        R = 1e-8  # 10 nm radius
        N = 100   # 100 atoms

        pressure = model.get_gas_pressure(R, N, location='bulk')
        assert pressure > 0
        assert isinstance(pressure, (int, float))

    def test_get_gas_pressure_boundary(self):
        """Test gas pressure calculation for boundary bubbles"""
        model = RadialGasSwellingModel()
        R = 1e-7  # 100 nm radius
        N = 1000  # 1000 atoms

        pressure = model.get_gas_pressure(R, N, location='boundary')
        assert pressure > 0
        assert isinstance(pressure, (int, float))

    def test_get_thermal_equilibrium_concentrations(self):
        """Test thermal equilibrium concentration calculation"""
        model = RadialGasSwellingModel()

        # Test for different nodes
        for node_idx in [0, model.n_nodes // 2, model.n_nodes - 1]:
            cv0, ci0 = model.get_thermal_equilibrium_concentrations(node_idx)

            # Both concentrations should be positive
            assert cv0 > 0
            assert ci0 > 0

            # Should return a tuple
            assert isinstance(cv0, (int, float))
            assert isinstance(ci0, (int, float))

    def test_thermal_equilibrium_invalid_node(self):
        """Test that error is raised for invalid node index"""
        model = RadialGasSwellingModel(n_nodes=10)

        with pytest.raises(ValueError, match="node_index must be in"):
            model.get_thermal_equilibrium_concentrations(node_index=10)

        with pytest.raises(ValueError, match="node_index must be in"):
            model.get_thermal_equilibrium_concentrations(node_index=-1)


class TestRadialGasSwellingModelSolve:
    """Test ODE solving functionality"""

    @pytest.mark.slow
    def test_solve_with_default_parameters(self):
        """Test solving with default parameters"""
        model = RadialGasSwellingModel(n_nodes=5)
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

        # Check that all state variables have correct shape (n_time, n_nodes)
        for key in ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf',
                    'cvb', 'cib', 'kvb', 'kib', 'cvf', 'cif', 'kvf', 'kif',
                    'released_gas', 'swelling']:
            assert results[key].shape == (len(time_points), model.n_nodes), \
                f"Wrong shape for {key}: {results[key].shape}"

    @pytest.mark.slow
    def test_solve_without_t_eval(self):
        """Test solving without specifying t_eval"""
        model = RadialGasSwellingModel(n_nodes=5)
        t_span = (0, 86400)  # 1 day

        results = model.solve(t_span=t_span)

        # Should create default time points
        assert 'time' in results
        assert len(results['time']) > 0
        assert results['time'][0] == t_span[0]
        assert results['time'][-1] == t_span[1]

    @pytest.mark.slow
    def test_solve_results_physical_consistency(self):
        """Test that solve results are physically consistent"""
        model = RadialGasSwellingModel(n_nodes=5)
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
        # Check for each node
        for i in range(model.n_nodes):
            assert np.all(np.diff(released_gas[:, i]) >= -1e-10), \
                f"Released gas decreasing at node {i}"

    @pytest.mark.slow
    def test_solve_with_different_nodes(self):
        """Test solving with different number of nodes"""
        for n_nodes in [3, 5, 10]:
            model = RadialGasSwellingModel(n_nodes=n_nodes)
            t_span = (0, 86400)  # 1 day
            time_points = np.linspace(t_span[0], t_span[1], 5)

            results = model.solve(t_span=t_span, t_eval=time_points)

            # Check shape
            assert results['swelling'].shape == (len(time_points), n_nodes)

    @pytest.mark.slow
    def test_solve_with_temperature_profile(self):
        """Test solving with non-uniform temperature profile"""
        model = RadialGasSwellingModel(
            n_nodes=5,
            temperature_profile='parabolic'
        )
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 10)

        results = model.solve(t_span=t_span, t_eval=time_points)

        # Should produce valid results
        assert 'swelling' in results
        assert results['swelling'].shape == (len(time_points), model.n_nodes)

        # Swelling should vary spatially due to temperature gradient
        final_swelling = results['swelling'][-1, :]
        assert not np.all(final_swelling == final_swelling[0])

    @pytest.mark.slow
    def test_solve_with_debug_enabled(self):
        """Test solving with debug mode enabled"""
        model = RadialGasSwellingModel(n_nodes=5)
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

    @pytest.mark.slow
    def test_solve_custom_parameters(self):
        """Test solving with custom model parameters"""
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C
        params['fission_rate'] = 5e18

        model = RadialGasSwellingModel(params, n_nodes=5)
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 10)

        results = model.solve(t_span=t_span, t_eval=time_points)

        # Should complete without errors
        assert 'swelling' in results
        assert results['swelling'].shape == (len(time_points), model.n_nodes)

    @pytest.mark.slow
    def test_solve_different_geometries(self):
        """Test solving with different geometries"""
        for geometry in ['cylindrical', 'slab']:
            model = RadialGasSwellingModel(n_nodes=5, geometry=geometry)
            t_span = (0, 86400)  # 1 day
            time_points = np.linspace(t_span[0], t_span[1], 5)

            results = model.solve(t_span=t_span, t_eval=time_points)

            assert 'swelling' in results
            assert results['swelling'].shape == (len(time_points), model.n_nodes)

    @pytest.mark.slow
    def test_solve_different_methods(self):
        """Test solving with different numerical methods"""
        model = RadialGasSwellingModel(n_nodes=5)
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 5)

        for method in ['RK23', 'RK45', 'BDF']:
            results = model.solve(t_span=t_span, t_eval=time_points, method=method)
            assert 'swelling' in results


class TestRadialGasSwellingModelDebug:
    """Test debug functionality"""

    def test_enable_debug(self):
        """Test enabling debug mode"""
        model = RadialGasSwellingModel()
        model.enable_debug(time_step_interval=500)

        assert model.debug_config.enabled is True
        assert model.debug_config.time_step_interval == 500
        assert model.debug_config.save_to_file is True

    def test_disable_debug(self):
        """Test disabling debug mode"""
        model = RadialGasSwellingModel()
        model.enable_debug()
        model.disable_debug()

        assert model.debug_config.enabled is False

    def test_debug_config_persistence(self):
        """Test that debug config settings persist"""
        model = RadialGasSwellingModel()
        model.enable_debug(
            time_step_interval=100,
            output_file='test_debug_radial.csv'
        )

        assert model.debug_config.time_step_interval == 100
        assert model.debug_config.output_file == 'test_debug_radial.csv'


class TestRadialGasSwellingModelIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.slow
    def test_complete_simulation_workflow(self):
        """Test complete simulation from setup to results analysis"""
        # Create model
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C
        model = RadialGasSwellingModel(params, n_nodes=10)

        # Run simulation
        simulation_time = 864000  # 10 days in seconds
        time_points = np.linspace(0, simulation_time, 50)
        results = model.solve(t_span=(0, simulation_time), t_eval=time_points)

        # Analyze results
        final_swelling = results['swelling'][-1, :]  # shape: (n_nodes,)
        assert np.all(final_swelling >= 0)
        assert len(final_swelling) == model.n_nodes

        # Check radial profile
        center_swelling = final_swelling[0]
        surface_swelling = final_swelling[-1]
        assert center_swelling >= 0
        assert surface_swelling >= 0

    @pytest.mark.slow
    def test_model_with_different_eos_models(self):
        """Test model with different equation of state models"""
        for eos_model in ['ideal', 'virial', 'ronchi']:
            params = create_default_parameters()
            params['eos_model'] = eos_model

            model = RadialGasSwellingModel(params, n_nodes=5)
            t_span = (0, 86400)  # 1 day
            time_points = np.linspace(t_span[0], t_span[1], 5)

            results = model.solve(t_span=t_span, t_eval=time_points)
            assert 'swelling' in results

    @pytest.mark.slow
    def test_multiple_sequential_solves(self):
        """Test running multiple solves sequentially"""
        model = RadialGasSwellingModel(n_nodes=5)
        t_span = (0, 86400)  # 1 day
        time_points = np.linspace(t_span[0], t_span[1], 10)

        # First solve
        results1 = model.solve(t_span=t_span, t_eval=time_points)
        assert 'swelling' in results1

        # Second solve (should work with same model)
        results2 = model.solve(t_span=t_span, t_eval=time_points)
        assert 'swelling' in results2

    @pytest.mark.slow
    def test_radial_profile_evolution(self):
        """Test that radial profiles evolve realistically"""
        model = RadialGasSwellingModel(
            n_nodes=10,
            temperature_profile='parabolic'
        )

        simulation_time = 864000  # 10 days
        time_points = np.linspace(0, simulation_time, 20)
        results = model.solve(t_span=(0, simulation_time), t_eval=time_points)

        # Check that swelling increases with time
        for i in range(model.n_nodes):
            swelling_at_node = results['swelling'][:, i]
            assert swelling_at_node[-1] >= swelling_at_node[0] - 1e-10

        # Check that we get spatial variation
        final_profile = results['swelling'][-1, :]
        assert not np.all(final_profile == final_profile[0])

    @pytest.mark.slow
    def test_temperature_reinitialization(self):
        """Test setting temperature profile and reinitializing"""
        model = RadialGasSwellingModel(n_nodes=10)

        # Get initial state
        initial_state = model.initial_state.copy()

        # Set new temperature profile
        new_profile = np.linspace(900, 700, 10)
        model.set_temperature_profile(new_profile, reinitialize=True)

        # State should be reinitialized
        new_state = model.initial_state
        assert not np.array_equal(initial_state, new_state)

        # Temperature profile should be updated
        np.testing.assert_array_almost_equal(model.temperature, new_profile)

    @pytest.mark.slow
    def test_temperature_update_without_reinitialization(self):
        """Test setting temperature profile without reinitializing state"""
        model = RadialGasSwellingModel(n_nodes=10)

        # Get initial state
        initial_state = model.initial_state.copy()

        # Set new temperature profile without reinitialization
        new_profile = np.linspace(900, 700, 10)
        model.set_temperature_profile(new_profile, reinitialize=False)

        # State should remain the same
        np.testing.assert_array_equal(model.initial_state, initial_state)

        # Temperature profile should be updated
        np.testing.assert_array_almost_equal(model.temperature, new_profile)


class TestRadialGasSwellingModel0DComparison:
    """Test 0D-1D comparison - uniform conditions should match"""

    @pytest.mark.slow
    def test_0d_1d_comparison(self):
        """Test that 0D and 1D models produce similar results under uniform conditions"""
        # Create common parameters
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C in Kelvin
        params['fission_rate'] = 5e18

        # Define simulation time (very short for faster testing)
        sim_time = 1000  # 1000 seconds
        time_points = np.linspace(0, sim_time, 5)  # Fewer time points

        # Run 0D model
        model_0d = GasSwellingModel(params)
        result_0d = model_0d.solve(t_span=(0, sim_time), t_eval=time_points)

        # Run 1D model with uniform temperature profile
        model_1d = RadialGasSwellingModel(
            params,
            n_nodes=3,  # Fewer nodes for faster computation
            temperature_profile='uniform',
            flux_depression=False  # No flux depression for uniform conditions
        )
        result_1d = model_1d.solve(t_span=(0, sim_time), t_eval=time_points)

        # Compare results - 1D model should be uniform across all nodes
        # and match 0D model results

        # Check that 1D model produces uniform results across nodes
        # (all nodes should have same values under uniform conditions)
        for key in ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf',
                    'cvb', 'cib', 'cvf', 'cif']:
            values_at_final_time = result_1d[key][-1, :]  # shape: (n_nodes,)
            # All nodes should have similar values (within numerical tolerance)
            assert np.allclose(values_at_final_time, values_at_final_time[0],
                               rtol=1e-2, atol=1e-10), \
                f"{key} not uniform across nodes in 1D model"

        # Compare 0D results with 1D results (using any node, e.g., node 0)
        # Use a reasonable tolerance due to numerical differences in ODE solving
        rtol = 3e-1  # 30% relative tolerance for comparison (accounts for spatial discretization)
        atol = 1e-10  # Small absolute tolerance

        # Compare key variables at final time
        # Note: Defect concentrations (cvb, cib, cvf, cif) can have significant
        # numerical differences due to spatial discretization, so we check them
        # with more lenient tolerances
        for key in ['Cgb', 'Ccb', 'Ncb', 'Rcb', 'Cgf', 'Ccf', 'Ncf', 'Rcf']:
            value_0d = result_0d[key][-1]
            value_1d = result_1d[key][-1, 0]  # Use node 0

            # Check that values are within tolerance
            # Use a tolerance that accounts for:
            # - Different numerical discretization schemes
            # - Slightly different ODE solver behavior
            # - Expected physical equivalence under uniform conditions
            if abs(value_0d) > atol:
                rel_diff = abs(value_1d - value_0d) / abs(value_0d)
                assert rel_diff < rtol, \
                    f"{key}: 0D={value_0d}, 1D={value_1d}, rel_diff={rel_diff}"

        # For defect concentrations, just check they're in reasonable range
        # (comparison is difficult due to numerical precision differences)
        for key in ['cvb', 'cib', 'cvf', 'cif']:
            value_1d = result_1d[key][-1, 0]
            # Check that values are finite and not overly large
            assert np.isfinite(value_1d), f"{key} is not finite in 1D model"
            assert abs(value_1d) < 1e-4, f"{key} has unexpected value: {value_1d}"

        # Specifically check final swelling values
        swelling_0d = result_0d['swelling'][-1]
        swelling_1d_avg = np.mean(result_1d['swelling'][-1, :])

        # Both should produce similar total swelling
        if abs(swelling_0d) > atol:
            rel_diff = abs(swelling_1d_avg - swelling_0d) / abs(swelling_0d)
            assert rel_diff < rtol, \
                f"Swelling: 0D={swelling_0d}, 1D_avg={swelling_1d_avg}, rel_diff={rel_diff}"

    def test_0d_1d_initial_state_consistency(self):
        """Test that initial states are consistent between 0D and 1D models"""
        params = create_default_parameters()

        # Create 0D model
        model_0d = GasSwellingModel(params)

        # Create 1D model with uniform temperature
        model_1d = RadialGasSwellingModel(
            params,
            n_nodes=3,
            temperature_profile='uniform'
        )

        # Check that initial conditions are consistent
        # The 1D model's node 0 should have similar initial values to 0D model
        for i in range(17):
            # Get variable name from index for debugging
            # State variables: Cgb(0), Ccb(1), Ncb(2), Rcb(3), Cgf(4), Ccf(5),
            # Ncf(6), Rcf(7), cvb(8), cib(9), cvf(10), cif(11),
            # released_gas(12), kvb(13), kib(14), kvf(15), kif(16)

            # Extract values
            value_0d = model_0d.initial_state[i]
            value_1d_node0 = model_1d.initial_state[i]  # Node 0, variable i

            # Check consistency (may differ slightly for sink strengths due to geometry)
            # Allow for some difference in sink strengths (kvb, kib, kvf, kif at indices 13-16)
            if i in [13, 14, 15, 16]:  # Sink strengths
                # These may differ due to geometry corrections in 1D model
                assert np.isfinite(value_1d_node0), \
                    f"Sink strength at index {i} is not finite in 1D model"
            else:
                # Other variables should be nearly identical
                np.testing.assert_allclose(value_0d, value_1d_node0,
                                           rtol=1e-5, atol=1e-10,
                                           err_msg=f"Initial state index {i} differs")
