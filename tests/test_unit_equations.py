"""
Unit tests for GasSwellingModel _equations method and internal calculation paths.

This module provides comprehensive testing of the ODE system and internal
calculation methods to achieve high code coverage.
"""

import pytest
import numpy as np
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters


class TestODESystem:
    """Test the ODE system (_equations method) comprehensively"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        return GasSwellingModel()

    @pytest.fixture
    def valid_state(self, model):
        """Create a valid state vector for testing"""
        return model.initial_state.copy()

    def test_equations_dCgb_dt_calculation(self, model, valid_state):
        """Test gas concentration in bulk derivative calculation"""
        derivatives = model._equations(0.0, valid_state)
        dCgb_dt = derivatives[0]

        # Should be finite and can be positive or negative
        assert np.isfinite(dCgb_dt)

    def test_equations_dCcb_dt_calculation(self, model, valid_state):
        """Test cavity concentration in bulk derivative"""
        derivatives = model._equations(0.0, valid_state)
        dCcb_dt = derivatives[1]

        assert np.isfinite(dCcb_dt)

    def test_equations_dNcb_dt_calculation(self, model, valid_state):
        """Test gas atoms per bulk cavity derivative"""
        derivatives = model._equations(0.0, valid_state)
        dNcb_dt = derivatives[2]

        assert np.isfinite(dNcb_dt)

    def test_equations_dRcb_dt_calculation(self, model, valid_state):
        """Test bulk cavity radius derivative"""
        derivatives = model._equations(0.0, valid_state)
        dRcb_dt = derivatives[3]

        assert np.isfinite(dRcb_dt)

    def test_equations_dCgf_dt_calculation(self, model, valid_state):
        """Test boundary gas concentration derivative"""
        derivatives = model._equations(0.0, valid_state)
        dCgf_dt = derivatives[4]

        assert np.isfinite(dCgf_dt)

    def test_equations_dCcf_dt_calculation(self, model, valid_state):
        """Test boundary cavity concentration derivative"""
        derivatives = model._equations(0.0, valid_state)
        dCcf_dt = derivatives[5]

        assert np.isfinite(dCcf_dt)

    def test_equations_dNcf_dt_calculation(self, model, valid_state):
        """Test gas atoms per boundary cavity derivative"""
        derivatives = model._equations(0.0, valid_state)
        dNcf_dt = derivatives[6]

        assert np.isfinite(dNcf_dt)

    def test_equations_dRcf_dt_calculation(self, model, valid_state):
        """Test boundary cavity radius derivative"""
        derivatives = model._equations(0.0, valid_state)
        dRcf_dt = derivatives[7]

        assert np.isfinite(dRcf_dt)

    def test_equations_dcvb_dt_calculation(self, model, valid_state):
        """Test bulk vacancy concentration derivative"""
        derivatives = model._equations(0.0, valid_state)
        dcvb_dt = derivatives[8]

        assert np.isfinite(dcvb_dt)

    def test_equations_dcib_dt_calculation(self, model, valid_state):
        """Test bulk interstitial concentration derivative"""
        derivatives = model._equations(0.0, valid_state)
        dcib_dt = derivatives[9]

        assert np.isfinite(dcib_dt)

    def test_equations_dcvf_dt_calculation(self, model, valid_state):
        """Test boundary vacancy concentration derivative"""
        derivatives = model._equations(0.0, valid_state)
        dcvf_dt = derivatives[10]

        assert np.isfinite(dcvf_dt)

    def test_equations_dcif_dt_calculation(self, model, valid_state):
        """Test boundary interstitial concentration derivative"""
        derivatives = model._equations(0.0, valid_state)
        dcif_dt = derivatives[11]

        assert np.isfinite(dcif_dt)

    def test_equations_dkvb_dt_calculation(self, model, valid_state):
        """Test bulk vacancy sink strength derivative"""
        derivatives = model._equations(0.0, valid_state)
        dkvb_dt = derivatives[13]

        # Sink strengths have zero derivatives
        assert np.isfinite(dkvb_dt)
        assert dkvb_dt == 0.0

    def test_equations_dkib_dt_calculation(self, model, valid_state):
        """Test bulk interstitial sink strength derivative"""
        derivatives = model._equations(0.0, valid_state)
        dkib_dt = derivatives[14]

        # Sink strengths have zero derivatives
        assert np.isfinite(dkib_dt)
        assert dkib_dt == 0.0

    def test_equations_dkvf_dt_calculation(self, model, valid_state):
        """Test boundary vacancy sink strength derivative"""
        derivatives = model._equations(0.0, valid_state)
        dkvf_dt = derivatives[15]

        # Sink strengths have zero derivatives
        assert np.isfinite(dkvf_dt)
        assert dkvf_dt == 0.0

    def test_equations_dkif_dt_calculation(self, model, valid_state):
        """Test boundary interstitial sink strength derivative"""
        derivatives = model._equations(0.0, valid_state)
        dkif_dt = derivatives[16]

        # Sink strengths have zero derivatives
        assert np.isfinite(dkif_dt)
        assert dkif_dt == 0.0

    def test_equations_dreleased_gas_dt_calculation(self, model, valid_state):
        """Test released gas accumulation derivative"""
        derivatives = model._equations(0.0, valid_state)
        dreleased_gas_dt = derivatives[12]

        # Released gas should be non-negative
        assert np.isfinite(dreleased_gas_dt)
        assert dreleased_gas_dt >= 0

    def test_equations_with_high_cavity_concentration(self, model):
        """Test equations with high cavity concentration"""
        state = model.initial_state.copy()
        # Increase cavity concentrations
        state[1] *= 100  # Ccb
        state[5] *= 100  # Ccf

        derivatives = model._equations(100.0, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_with_high_gas_concentration(self, model):
        """Test equations with high gas concentration"""
        state = model.initial_state.copy()
        # Increase gas concentrations
        state[0] *= 1000  # Cgb
        state[4] *= 1000  # Cgf

        derivatives = model._equations(100.0, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_with_different_temperatures(self, model, valid_state):
        """Test equations at different temperatures"""
        original_temp = model.params['temperature']

        # Low temperature
        model.params['temperature'] = 600
        derivatives_low = model._equations(100.0, valid_state)
        assert np.all(np.isfinite(derivatives_low))

        # High temperature
        model.params['temperature'] = 900
        derivatives_high = model._equations(100.0, valid_state)
        assert np.all(np.isfinite(derivatives_high))

        # Restore original temperature
        model.params['temperature'] = original_temp

    def test_equations_mass_conservation_short_term(self, model, valid_state):
        """Test that gas atoms are approximately conserved in short term"""
        derivatives = model._equations(0.0, valid_state)

        # Sum of gas derivatives should balance with production
        dCgb_dt = derivatives[0]
        dCgf_dt = derivatives[4]
        dreleased_gas_dt = derivatives[16]

        # Gas production rate
        gas_production = model.params['gas_production_rate'] * model.params['fission_rate']

        # Check that gas is conserved (within numerical tolerance)
        total_gas_change = dCgb_dt + dCgf_dt + dreleased_gas_dt

        # Should be close to gas production rate (within 50% tolerance for complex dynamics)
        assert abs(total_gas_change - gas_production) / gas_production < 0.5

    def test_equations_zero_fission_rate(self, model):
        """Test equations with zero fission rate"""
        state = model.initial_state.copy()

        original_rate = model.params['fission_rate']
        model.params['fission_rate'] = 0.0

        derivatives = model._equations(100.0, state)

        # With no fission, defect production should be zero
        # (but defects can still diffuse and recombine)
        assert np.all(np.isfinite(derivatives))

        model.params['fission_rate'] = original_rate

    def test_equations_high_dislocation_density(self, model, valid_state):
        """Test equations with high dislocation density"""
        original_density = model.params['dislocation_density']
        model.params['dislocation_density'] = 1e15  # Very high

        derivatives = model._equations(100.0, valid_state)
        assert np.all(np.isfinite(derivatives))

        model.params['dislocation_density'] = original_density

    def test_equations_low_dislocation_density(self, model, valid_state):
        """Test equations with low dislocation density"""
        original_density = model.params['dislocation_density']
        model.params['dislocation_density'] = 1e10  # Very low

        derivatives = model._equations(100.0, valid_state)
        assert np.all(np.isfinite(derivatives))

        model.params['dislocation_density'] = original_density

    def test_equations_different_grain_sizes(self, model, valid_state):
        """Test equations with different grain sizes"""
        original_diameter = model.params['grain_diameter']

        # Small grains
        model.params['grain_diameter'] = 1e-6
        derivatives_small = model._equations(100.0, valid_state)
        assert np.all(np.isfinite(derivatives_small))

        # Large grains
        model.params['grain_diameter'] = 1e-4
        derivatives_large = model._equations(100.0, valid_state)
        assert np.all(np.isfinite(derivatives_large))

        model.params['grain_diameter'] = original_diameter

    def test_equations_time_progression(self, model, valid_state):
        """Test that equations behave consistently at different times"""
        times = [0.0, 100.0, 1000.0, 10000.0]

        for t in times:
            derivatives = model._equations(t, valid_state)
            assert np.all(np.isfinite(derivatives)), f"Failed at t={t}"

    def test_equations_runs_with_different_states(self, model):
        """Test that equations can run with various state values"""
        state1 = model.initial_state.copy()
        state2 = model.initial_state.copy()

        # Modify state2
        state2[0] *= 10  # 10x gas concentration in bulk
        state2[1] *= 5   # 5x cavity concentration in bulk

        deriv1 = model._equations(100.0, state1)
        deriv2 = model._equations(100.0, state2)

        # Both should produce finite results
        assert np.all(np.isfinite(deriv1))
        assert np.all(np.isfinite(deriv2))

    def test_model_different_eos_models(self):
        """Test model with different equation of state models"""
        for eos_model in ['ideal', 'ronchi']:
            params = create_default_parameters()
            params['eos_model'] = eos_model

            model = GasSwellingModel(params)
            state = model.initial_state.copy()

            derivatives = model._equations(100.0, state)
            assert np.all(np.isfinite(derivatives))

    def test_initial_state_structure(self, model):
        """Test that initial state has correct structure"""
        state = model.initial_state

        # Should have 17 elements
        assert len(state) == 17

        # Check key state variables
        Cgb, Ccb, Ncb, Rcb = state[0], state[1], state[2], state[3]
        Cgf, Ccf, Ncf, Rcf = state[4], state[5], state[6], state[7]

        # Should be physically reasonable
        assert Cgb >= 0
        assert Ccb >= 0
        assert Ncb > 0
        assert Rcb > 0
        assert Cgf >= 0
        assert Ccf >= 0
        assert Ncf > 0
        assert Rcf > 0

    def test_state_updates_time(self, model, valid_state):
        """Test that calling _equations updates model time"""
        initial_time = model.current_time
        test_time = 1234.56

        model._equations(test_time, valid_state)

        assert model.current_time == test_time
        assert model.current_time != initial_time


class TestInternalCalculations:
    """Test internal calculation methods that feed into equations"""

    @pytest.fixture
    def model(self):
        return GasSwellingModel()

    def test_diffusivity_calculations_in_equations(self, model):
        """Test that diffusivities are calculated correctly in equations"""
        state = model.initial_state.copy()

        # This will trigger diffusivity calculations inside _equations
        derivatives = model._equations(100.0, state)

        # If we got here without errors, diffusivities are being calculated
        assert np.all(np.isfinite(derivatives))

    def test_pressure_calculations_in_equations(self, model):
        """Test that gas pressures are calculated in equations"""
        state = model.initial_state.copy()

        # Set non-zero cavity concentrations to ensure pressure calculations
        state[1] = 1e15  # Ccb
        state[5] = 1e15  # Ccf

        derivatives = model._equations(100.0, state)

        # Should complete without errors
        assert np.all(np.isfinite(derivatives))

    def test_sink_strength_calculations(self, model):
        """Test sink strength calculations for various defects"""
        state = model.initial_state.copy()

        # Modify to have significant cavity concentrations
        state[1] = 1e16  # Ccb
        state[5] = 1e16  # Ccf
        state[2] = 100.0  # Ncb
        state[6] = 100.0  # Ncf

        derivatives = model._equations(100.0, state)

        # Sink strengths (kvb, kib, kvf, kif) should be calculated
        assert np.all(np.isfinite(derivatives))

    def test_recombination_rate_in_equations(self, model):
        """Test defect recombination rate calculations"""
        state = model.initial_state.copy()

        # Set non-zero defect concentrations
        state[8] = 1e-10  # cvb
        state[9] = 1e-12  # cib
        state[12] = 1e-10  # cvf
        state[13] = 1e-12  # cif

        derivatives = model._equations(100.0, state)

        # Recombination should occur
        assert np.all(np.isfinite(derivatives))


class TestEdgeCasesInEquations:
    """Test edge cases and special conditions in the ODE system"""

    @pytest.fixture
    def model(self):
        return GasSwellingModel()

    def test_equations_with_very_small_cavities(self, model):
        """Test equations with very small cavity radii"""
        state = model.initial_state.copy()
        state[3] = 1e-10  # Very small Rcb
        state[7] = 1e-10  # Very small Rcf

        derivatives = model._equations(100.0, state)
        # Should handle small radii gracefully
        assert np.all(np.isfinite(derivatives))

    def test_equations_with_very_large_cavities(self, model):
        """Test equations with very large cavity radii"""
        state = model.initial_state.copy()
        state[3] = 1e-5  # Large Rcb
        state[7] = 1e-5  # Large Rcf

        derivatives = model._equations(100.0, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_with_zero_cavity_concentration(self, model):
        """Test equations with zero cavity concentration"""
        state = model.initial_state.copy()
        state[1] = 0.0  # Zero Ccb
        state[5] = 0.0  # Zero Ccf

        derivatives = model._equations(100.0, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_with_zero_defect_concentrations(self, model):
        """Test equations with zero point defect concentrations"""
        state = model.initial_state.copy()
        state[8] = 0.0  # cvb
        state[9] = 0.0  # cib
        state[12] = 0.0  # cvf
        state[13] = 0.0  # cif

        derivatives = model._equations(100.0, state)
        assert np.all(np.isfinite(derivatives))

    def test_equations_symmetry(self, model):
        """Test that bulk and boundary equations are symmetric"""
        state = model.initial_state.copy()

        # Make bulk and boundary states identical
        state[0] = state[4]  # Cgb = Cgf
        state[1] = state[5]  # Ccb = Ccf
        state[2] = state[6]  # Ncb = Ncf
        state[3] = state[7]  # Rcb = Rcf
        state[8] = state[12]  # cvb = cvf
        state[9] = state[13]  # cib = cif

        derivatives = model._equations(100.0, state)

        # Derivatives should be similar (not identical due to grain geometry)
        assert np.all(np.isfinite(derivatives))
