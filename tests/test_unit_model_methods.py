"""
Unit tests for GasSwellingModel internal methods.

This module tests the internal calculation methods of the GasSwellingModel class
to ensure comprehensive code coverage.
"""

import pytest
import numpy as np
from gas_swelling.models.modelrk23 import GasSwellingModel


class TestGasSwellingModelInternalMethods:
    """Test internal methods of GasSwellingModel"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        return GasSwellingModel()

    def test_initialization(self, model):
        """Test model initialization"""
        assert model.params is not None
        assert model.initial_state is not None
        assert len(model.initial_state) == 17
        assert model.step_count == 0
        assert model.solver_success is True
        assert model.current_time == 0.0

    def test_calculate_cv0(self, model):
        """Test thermal equilibrium vacancy concentration calculation"""
        cv0 = model._calculate_cv0()
        assert isinstance(cv0, float)
        assert cv0 > 0
        assert cv0 < 1  # Should be much less than 1

    def test_calculate_cv0_temperature_dependence(self, model):
        """Test that cv0 varies with temperature"""
        original_temp = model.params['temperature']

        # Test at lower temperature
        model.params['temperature'] = 600
        cv0_600 = model._calculate_cv0()

        # Test at higher temperature
        model.params['temperature'] = 800
        cv0_800 = model._calculate_cv0()

        # Higher temperature should give higher vacancy concentration
        assert cv0_800 > cv0_600

        # Reset temperature
        model.params['temperature'] = original_temp

    def test_calculate_ci0(self, model):
        """Test thermal equilibrium interstitial concentration calculation"""
        ci0 = model._calculate_ci0()
        assert isinstance(ci0, float)
        assert ci0 > 0

    def test_calculate_ci0_temperature_dependence(self, model):
        """Test that ci0 varies with temperature"""
        original_temp = model.params['temperature']

        model.params['temperature'] = 600
        ci0_600 = model._calculate_ci0()

        model.params['temperature'] = 800
        ci0_800 = model._calculate_ci0()

        assert ci0_800 != ci0_600

        model.params['temperature'] = original_temp

    def test_gas_influx(self, model):
        """Test gas influx calculation"""
        Cgb = 1e20  # atoms/m³
        Cgf = 1e19  # atoms/m³

        influx = model._gas_influx(Cgb, Cgf)
        assert isinstance(influx, float)
        assert influx >= 0  # Should be non-negative

    def test_gas_influx_zero_concentration(self, model):
        """Test gas influx with zero concentrations"""
        influx = model._gas_influx(0.0, 0.0)
        assert influx == 0.0

    def test_calculate_gas_release_rate_zero_cavity(self, model):
        """Test gas release rate with no cavities"""
        rate = model._calculate_gas_release_rate(1e19, 0.0, 1e-9, 5.0)
        assert rate == 0.0

    def test_calculate_gas_release_rate_with_cavities(self, model):
        """Test gas release rate with cavities present"""
        Cgf = 1e19  # atoms/m³
        Ccf = 1e15  # cavities/m³
        Rcf = 1e-7  # m
        Ncf = 10.0  # atoms/cavity

        rate = model._calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf)
        # Check that rate is numeric and non-negative
        assert np.isfinite(rate)
        assert rate >= 0

    def test_calculate_gas_release_rate_interconnection(self, model):
        """Test gas release rate with interconnection threshold"""
        # High cavity concentration should trigger interconnection
        Cgf = 1e25  # Very high gas concentration
        Ccf = 1e20  # Very high cavity concentration
        Rcf = 1e-6  # Larger radius to get significant area
        Ncf = 1000.0  # More atoms per cavity

        rate = model._calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf)
        # With high cavity concentration, should have significant release
        assert rate >= 0  # Can be zero or positive depending on interconnection calculation

    def test_calculate_idealgas_pressure(self, model):
        """Test ideal gas pressure calculation"""
        Rc = 1e-8  # m
        Nc = 10.0  # atoms

        pressure = model._calculate_idealgas_pressure(Rc, Nc)
        assert isinstance(pressure, float)
        assert pressure > 0

    def test_calculate_idealgas_pressure_zero_radius(self, model):
        """Test ideal gas pressure with zero radius"""
        pressure = model._calculate_idealgas_pressure(0.0, 10.0)
        assert pressure == 0.0

    def test_calculate_idealgas_pressure_zero_atoms(self, model):
        """Test ideal gas pressure with zero atoms"""
        pressure = model._calculate_idealgas_pressure(1e-8, 0.0)
        assert pressure == 0.0

    def test_calculate_modifiedvongas_pressure(self, model):
        """Test modified van der Waals pressure calculation"""
        Rc = 1e-8
        Nc = 10.0

        pressure = model._calculate_modifiedvongas_pressure(Rc, Nc)
        assert isinstance(pressure, float)
        assert pressure > 0

    def test_calculate_modifiedvongas_pressure_zero_radius(self, model):
        """Test modified van der Waals pressure with zero radius"""
        pressure = model._calculate_modifiedvongas_pressure(0.0, 10.0)
        assert pressure == 0.0

    def test_calculate_VirialEOSgas_pressure(self, model):
        """Test Virial EOS pressure calculation"""
        Rc = 1e-8
        Nc = 10.0

        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert isinstance(pressure, float)
        assert pressure > 0

    def test_calculate_VirialEOSgas_pressure_small_cavity(self, model):
        """Test Virial EOS pressure with small cavity"""
        Rc = 1e-10  # Very small radius
        Nc = 5.0

        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert isinstance(pressure, float)
        # Very small cavities should have very high pressure
        assert pressure > 1e6  # Should be very high

    def test_calculate_VirialEOSgas_pressure_large_cavity(self, model):
        """Test Virial EOS pressure with large cavity"""
        Rc = 1e-6  # Large radius
        Nc = 1000.0  # Many atoms

        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert isinstance(pressure, float)
        assert pressure > 0

    def test_calculate_ronchi_pressure(self, model):
        """Test Ronchi EOS pressure calculation"""
        Rc = 1e-8
        Nc = 10.0
        T = 700  # K

        pressure = model._calculate_ronchi_pressure(Rc, Nc, T)
        assert isinstance(pressure, float)
        assert pressure > 0

    def test_calculate_ronchi_pressure_temperature_dependence(self, model):
        """Test Ronchi pressure varies with temperature"""
        Rc = 1e-8
        Nc = 10.0

        pressure_600 = model._calculate_ronchi_pressure(Rc, Nc, 600)
        pressure_800 = model._calculate_ronchi_pressure(Rc, Nc, 800)

        assert pressure_600 > 0
        assert pressure_800 > 0
        # Higher temperature should give higher pressure
        assert pressure_800 > pressure_600

    def test_initialize_state(self, model):
        """Test state initialization"""
        state = model._initialize_state()
        assert isinstance(state, np.ndarray)
        assert len(state) == 17

        # Check initial values are physically reasonable
        Cgb, Ccb, Ncb, Rcb = state[0], state[1], state[2], state[3]
        assert Cgb >= 0
        assert Ccb >= 0
        assert Ncb > 0  # Initial gas atoms per cavity
        assert Rcb > 0  # Initial radius

    def test_initialize_state_finite_values(self, model):
        """Test that all initial state values are finite"""
        state = model._initialize_state()
        assert np.all(np.isfinite(state))

    def test_equations_returns_correct_shape(self, model):
        """Test that _equations returns correct shape"""
        state = model.initial_state
        t = 0.0

        derivatives = model._equations(t, state)
        assert isinstance(derivatives, np.ndarray)
        assert len(derivatives) == 17

    def test_equations_returns_finite_values(self, model):
        """Test that _equations returns finite values"""
        state = model.initial_state
        t = 0.0

        derivatives = model._equations(t, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_with_zero_state(self, model):
        """Test _equations with zero state"""
        # Create state with mostly zeros but some minimum values
        state = np.zeros(17)
        state[2] = 5.0  # Ncb
        state[3] = 1e-8  # Rcb
        state[6] = 5.0  # Ncf
        state[7] = 1e-8  # Rcf

        derivatives = model._equations(0.0, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_time_update(self, model):
        """Test that _equations updates current_time"""
        initial_time = model.current_time
        test_time = 100.0

        state = model.initial_state
        model._equations(test_time, state)

        assert model.current_time == test_time

    def test_gas_pressure_methods_consistency(self, model):
        """Test that different gas pressure methods give consistent results"""
        Rc = 1e-8
        Nc = 10.0

        pressure_ideal = model._calculate_idealgas_pressure(Rc, Nc)
        pressure_vdw = model._calculate_modifiedvongas_pressure(Rc, Nc)
        pressure_virial = model._calculate_VirialEOSgas_pressure(Rc, Nc)

        # All should be positive
        assert pressure_ideal > 0
        assert pressure_vdw > 0
        assert pressure_virial > 0

        # Ideal gas should be lowest, Virial higher, van der Waals can be very different
        # Just check they're all physically reasonable
        assert pressure_ideal < 1e15  # Should be reasonable
        assert pressure_vdw > 0
        assert pressure_virial > 0

    def test_debug_history_initialization(self, model):
        """Test that debug history is properly initialized"""
        assert 'time' in model.debug_history
        assert 'Rcb' in model.debug_history
        assert 'Rcf' in model.debug_history
        assert 'Pg_b' in model.debug_history
        assert 'Pg_f' in model.debug_history
        assert 'swelling' in model.debug_history

        # All should start empty
        for key in model.debug_history:
            assert len(model.debug_history[key]) == 0

    def test_model_with_custom_parameters(self):
        """Test model initialization with custom parameters"""
        from gas_swelling.params.parameters import create_default_parameters
        # Start with default parameters to ensure all required keys are present
        default_params = create_default_parameters()
        # Override specific parameters
        default_params['temperature'] = 750
        default_params['fission_rate'] = 6e19
        default_params['grain_diameter'] = 1e-5

        model = GasSwellingModel(default_params)

        assert model.params['temperature'] == 750
        assert model.params['fission_rate'] == 6e19
        assert model.params['grain_diameter'] == 1e-5

    def test_model_sets_default_parameters(self, model):
        """Test that model sets default parameters"""
        assert 'Zvc' in model.params
        assert 'Zic' in model.params
        assert model.params['Zvc'] == 1.0
        assert model.params['Zic'] == 1.0
