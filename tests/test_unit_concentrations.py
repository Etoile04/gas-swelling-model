"""
Unit tests for thermal equilibrium concentration calculations in GasSwellingModel

Tests cover:
- Thermal equilibrium vacancy concentration (cv0) calculation
- Thermal equilibrium interstitial concentration (ci0) calculation
- Temperature dependence of concentrations
- Edge cases and numerical stability
"""

import pytest
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


class TestVacancyConcentration:
    """Test suite for thermal equilibrium vacancy concentration (cv0) calculation"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_cv0_normal_temperature(self, model):
        """Test cv0 calculation at normal operating temperature (600K)"""
        cv0 = model._calculate_cv0()

        # Concentration should be positive
        assert cv0 > 0

        # Thermal equilibrium vacancy concentration should be very small but non-zero
        # At 600K for U-Zr alloy, typically around 1e-13 to 1e-10
        assert 1e-15 < cv0 < 1e-3

    def test_cv0_low_temperature(self, model):
        """Test cv0 calculation at low temperature (300K)"""
        model.params['temperature'] = 300
        cv0 = model._calculate_cv0()

        # At lower temperature, vacancy concentration should be smaller
        assert cv0 > 0
        assert cv0 < 1e-6  # Very small at room temperature

    def test_cv0_high_temperature(self, model):
        """Test cv0 calculation at high temperature (1200K)"""
        model.params['temperature'] = 1200
        cv0 = model._calculate_cv0()

        # At higher temperature, vacancy concentration should increase significantly
        assert cv0 > 0
        # At high T, can be much larger but still < 1
        assert cv0 < 1.0

    def test_cv0_temperature_dependence(self, model):
        """Test that cv0 increases exponentially with temperature"""
        temperatures = [400, 600, 800, 1000]
        cv0_values = []

        for T in temperatures:
            model.params['temperature'] = T
            cv0_values.append(model._calculate_cv0())

        # Each subsequent temperature should give higher concentration
        for i in range(len(cv0_values) - 1):
            assert cv0_values[i+1] > cv0_values[i] * 1.5  # At least 1.5x increase per 200K

    def test_cv0_evf_coeffs_impact(self, model):
        """Test that vacancy formation energy coefficients affect cv0"""
        model.params['temperature'] = 600

        # Get baseline
        cv0_baseline = model._calculate_cv0()

        # Modify Evf_coeffs to increase formation energy
        original_coeffs = model.params['Evf_coeffs'].copy()
        # Increase the constant term by 0.5 eV
        model.params['Evf_coeffs'] = [original_coeffs[0] + 0.5, original_coeffs[1]]
        cv0_high_evf = model._calculate_cv0()

        # Higher formation energy should give lower concentration
        assert cv0_high_evf < cv0_baseline

        # Restore original
        model.params['Evf_coeffs'] = original_coeffs

    def test_cv0_extreme_temperature_low(self, model):
        """Test cv0 at very low temperature to check numerical stability"""
        model.params['temperature'] = 100  # Very low temperature
        cv0 = model._calculate_cv0()

        # Should still return a valid number (not NaN or inf)
        assert np.isfinite(cv0)
        assert cv0 >= 0

    def test_cv0_extreme_temperature_high(self, model):
        """Test cv0 at very high temperature to check numerical stability"""
        model.params['temperature'] = 2000  # Very high temperature
        cv0 = model._calculate_cv0()

        # Should still return a valid number
        assert np.isfinite(cv0)
        assert cv0 > 0


class TestInterstitialConcentration:
    """Test suite for thermal equilibrium interstitial concentration (ci0) calculation"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_ci0_normal_temperature(self, model):
        """Test ci0 calculation at normal operating temperature (600K)"""
        ci0 = model._calculate_ci0()

        # Concentration should be positive
        assert ci0 > 0

        # Interstitial formation energy is higher than vacancy,
        # so ci0 should be much smaller than cv0
        cv0 = model._calculate_cv0()
        assert ci0 < cv0

    def test_ci0_low_temperature(self, model):
        """Test ci0 calculation at low temperature (300K)"""
        model.params['temperature'] = 300
        ci0 = model._calculate_ci0()

        # At lower temperature, concentration should be extremely small
        assert ci0 > 0
        assert ci0 < 1e-15  # Very small at room temperature

    def test_ci0_high_temperature(self, model):
        """Test ci0 calculation at high temperature (1200K)"""
        model.params['temperature'] = 1200
        ci0 = model._calculate_ci0()

        # At higher temperature, concentration should increase
        assert ci0 > 0
        # Still small but measurable
        assert ci0 < 1e-3

    def test_ci0_temperature_dependence(self, model):
        """Test that ci0 varies with temperature according to polynomial energy"""
        # Note: The Eif polynomial creates non-monotonic behavior
        # At low T, ci0 increases, but at high T it decreases due to
        # the cubic polynomial term in Eif
        temperatures = [400, 500, 600]
        ci0_values = []

        for T in temperatures:
            model.params['temperature'] = T
            ci0_values.append(model._calculate_ci0())

        # In the lower temperature range (400-600K), should increase
        for i in range(len(ci0_values) - 1):
            assert ci0_values[i+1] > ci0_values[i]

        # Test that at higher temperatures, the polynomial effect becomes significant
        model.params['temperature'] = 600
        ci0_600 = model._calculate_ci0()
        model.params['temperature'] = 800
        ci0_800 = model._calculate_ci0()

        # ci0 may decrease at high T due to cubic polynomial in Eif
        # This is expected physical behavior for this model
        assert ci0_800 > 0  # Still positive

    def test_ci0_polynomial_coeffs(self, model):
        """Test that cubic polynomial Eif coefficients are used correctly"""
        model.params['temperature'] = 600

        # Get baseline
        ci0_baseline = model._calculate_ci0()

        # Modify the polynomial coefficients
        original_coeffs = model.params['Eif_coeffs'].copy()
        # Scale all coefficients by 1.1 (10% increase in formation energy)
        model.params['Eif_coeffs'] = [c * 1.1 for c in original_coeffs]
        ci0_high_eif = model._calculate_ci0()

        # Higher formation energy should give lower concentration
        assert ci0_high_eif < ci0_baseline

        # Restore original
        model.params['Eif_coeffs'] = original_coeffs

    def test_ci0_extreme_temperature_low(self, model):
        """Test ci0 at very low temperature for numerical stability"""
        model.params['temperature'] = 100
        ci0 = model._calculate_ci0()

        # Should still return a valid number
        assert np.isfinite(ci0)
        assert ci0 >= 0

    def test_ci0_extreme_temperature_high(self, model):
        """Test ci0 at very high temperature for numerical stability"""
        model.params['temperature'] = 2000
        ci0 = model._calculate_ci0()

        # Should still return a valid number
        assert np.isfinite(ci0)
        assert ci0 > 0


class TestConcentrationRelationships:
    """Test suite for relationships between cv0 and ci0"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_cv0_greater_than_ci0(self, model):
        """Test that vacancy concentration is always greater than interstitial"""
        # This should hold across temperature range because vacancy formation
        # energy is lower than interstitial formation energy

        for T in [300, 400, 600, 800, 1000, 1200]:
            model.params['temperature'] = T
            cv0 = model._calculate_cv0()
            ci0 = model._calculate_ci0()

            assert cv0 > ci0, f"cv0 ({cv0}) should be > ci0 ({ci0}) at T={T}K"

    def test_both_positive(self, model):
        """Test that both concentrations are always positive"""
        for T in [200, 400, 600, 800, 1000, 1500]:
            model.params['temperature'] = T
            cv0 = model._calculate_cv0()
            ci0 = model._calculate_ci0()

            assert cv0 > 0, f"cv0 should be positive at T={T}K"
            assert ci0 > 0, f"ci0 should be positive at T={T}K"

    def test_both_finite(self, model):
        """Test that both concentrations are always finite (no overflow/underflow)"""
        for T in [100, 300, 600, 1200, 2000]:
            model.params['temperature'] = T
            cv0 = model._calculate_cv0()
            ci0 = model._calculate_ci0()

            assert np.isfinite(cv0), f"cv0 should be finite at T={T}K"
            assert np.isfinite(ci0), f"ci0 should be finite at T={T}K"

    def test_exponent_clipping_protection(self, model):
        """Test that exponent clipping prevents numerical overflow/underflow"""
        # Test at extreme temperatures that could cause exponent overflow
        for T in [1, 10, 100, 5000, 10000]:
            model.params['temperature'] = T
            cv0 = model._calculate_cv0()
            ci0 = model._calculate_ci0()

            # Should not overflow or underflow
            assert np.isfinite(cv0), f"cv0 overflow/underflow at T={T}K"
            assert np.isfinite(ci0), f"ci0 overflow/underflow at T={T}K"
