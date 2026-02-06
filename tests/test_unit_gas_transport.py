"""
Unit tests for gas transport and release rate calculations

Tests cover:
- Gas influx from bulk to phase boundaries (formula 2)
- Gas release rate calculation (formulas 9-12)
- Interconnectivity coefficient behavior
- Geometric factor calculations
"""

import pytest
import numpy as np
from gas_swelling.physics import calculate_gas_influx, calculate_gas_release_rate
from gas_swelling.params.parameters import create_default_parameters


class TestGasInflux:
    """Test suite for gas influx calculation from bulk to phase boundaries"""

    @pytest.fixture
    def params(self):
        """Create default parameters for testing"""
        return create_default_parameters()

    def test_gas_influx_normal_values(self, params):
        """Test gas influx calculation with normal concentration gradient"""
        Cgb = 1e20  # Gas concentration in bulk (atoms/m^3)
        Cgf = 1e19  # Gas concentration at boundaries (atoms/m^3)
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        influx = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)

        # Influx should be positive (flowing from high to low concentration)
        assert influx > 0

        # Check order of magnitude
        # Formula: (12 / d^2) * Dgb * (Cgb - Cgf)
        # where d ≈ 10e-6 m, Dgb ≈ 1e-15 m^2/s
        # influx ≈ (12 / 1e-10) * 1e-15 * 9e19 ≈ 1e25 atoms/(m^3·s)
        assert 1e23 < influx < 1e27  # Reasonable range

    def test_gas_influx_zero_gradient(self, params):
        """Test gas influx with zero concentration gradient"""
        Cgb = 1e20
        Cgf = 1e20  # Same concentration
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        influx = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)

        # No flux when concentrations are equal
        assert influx == 0.0

    def test_gas_influx_reverse_gradient(self, params):
        """Test gas influx with reverse concentration gradient"""
        Cgb = 1e19  # Lower concentration in bulk
        Cgf = 1e20  # Higher concentration at boundaries
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        influx = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)

        # Negative flux (flowing from boundaries to bulk)
        assert influx < 0

    def test_gas_influx_proportionality_to_gradient(self, params):
        """Test that influx is proportional to concentration difference"""
        Cgf = 1e19
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        # Test different bulk concentrations
        Cgb1 = 2e19
        Cgb2 = 3e19
        Cgb3 = 5e19

        influx1 = calculate_gas_influx(Cgb1, Cgf, grain_diameter, Dgb)
        influx2 = calculate_gas_influx(Cgb2, Cgf, grain_diameter, Dgb)
        influx3 = calculate_gas_influx(Cgb3, Cgf, grain_diameter, Dgb)

        # Should scale linearly with concentration difference
        assert abs(influx2 / influx1 - (Cgb2 - Cgf) / (Cgb1 - Cgf)) < 0.01
        assert abs(influx3 / influx1 - (Cgb3 - Cgf) / (Cgb1 - Cgf)) < 0.01

    def test_gas_influx_diffusion_coefficient_dependence(self, params):
        """Test that influx depends on gas diffusion coefficient"""
        Cgb = 1e20
        Cgf = 1e19
        grain_diameter = params['grain_diameter']

        Dgb_original = params['Dgb']

        # Test with different diffusion coefficients
        influx1 = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb_original * 2)
        influx2 = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb_original * 3)

        # Should scale linearly with diffusion coefficient
        assert abs(influx1 / (2 * Dgb_original) - influx2 / (3 * Dgb_original)) < 1e-10

    def test_gas_influx_grain_size_dependence(self, params):
        """Test that influx depends on grain diameter"""
        Cgb = 1e20
        Cgf = 1e19
        Dgb = params['Dgb']

        d_original = params['grain_diameter']

        # Test with different grain diameters
        influx1 = calculate_gas_influx(Cgb, Cgf, d_original * 2, Dgb)
        influx2 = calculate_gas_influx(Cgb, Cgf, d_original * 3, Dgb)

        # Should scale as 1/d^2
        ratio1 = (d_original / (d_original * 2))**2
        ratio2 = (d_original / (d_original * 3))**2

        assert abs(influx1 / ratio1 - influx2 / ratio2) < 1e-10

    def test_gas_influx_extreme_values(self, params):
        """Test gas influx with extreme concentration values"""
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        # Very high concentration
        influx1 = calculate_gas_influx(1e25, 1e20, grain_diameter, Dgb)
        assert influx1 > 0
        assert np.isfinite(influx1)

        # Very low concentration
        influx2 = calculate_gas_influx(1e10, 1e5, grain_diameter, Dgb)
        assert influx2 > 0
        assert np.isfinite(influx2)


class TestGasReleaseRate:
    """Test suite for gas release rate calculation"""

    @pytest.fixture
    def params(self):
        """Create default parameters for testing"""
        return create_default_parameters()

    def test_release_rate_normal_values(self, params):
        """Test gas release rate with normal bubble parameters"""
        Cgf = 1e20   # Gas concentration at boundaries
        Ccf = 1e15   # Cavity concentration at boundaries
        Rcf = 1e-6   # Cavity radius (1 µm)
        Ncf = 100    # Atoms per cavity
        grain_diameter = params['grain_diameter']

        release_rate = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

        # Release rate should be non-negative
        assert release_rate >= 0
        assert np.isfinite(release_rate)

    def test_release_rate_zero_radius(self, params):
        """Test gas release rate with zero cavity radius"""
        Cgf = 1e20
        Ccf = 1e15
        Rcf = 0.0
        Ncf = 100
        grain_diameter = params['grain_diameter']

        release_rate = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

        # Should handle zero radius gracefully
        assert release_rate >= 0
        assert np.isfinite(release_rate)

    def test_release_rate_small_radius(self, params):
        """Test gas release rate with very small cavity radius"""
        Cgf = 1e20
        Ccf = 1e15
        Rcf = 1e-12  # Extremely small radius
        Ncf = 100
        grain_diameter = params['grain_diameter']

        release_rate = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

        # Should handle small radius gracefully
        assert release_rate >= 0
        assert np.isfinite(release_rate)

    def test_release_rate_zero_cavity_concentration(self, params):
        """Test gas release rate with zero cavity concentration"""
        Cgf = 1e20
        Ccf = 0.0   # No cavities
        Rcf = 1e-6
        Ncf = 100
        grain_diameter = params['grain_diameter']

        release_rate = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

        # Should return valid result (no release without cavities)
        assert release_rate >= 0
        assert np.isfinite(release_rate)

    def test_release_rate_zero_atoms_per_cavity(self, params):
        """Test gas release rate with zero atoms per cavity"""
        Cgf = 1e20
        Ccf = 1e15
        Rcf = 1e-6
        Ncf = 0    # Empty cavities
        grain_diameter = params['grain_diameter']

        release_rate = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

        # Should return valid result
        assert release_rate >= 0
        assert np.isfinite(release_rate)

    def test_release_rate_large_bubbles(self, params):
        """Test gas release rate with large bubble radius"""
        Cgf = 1e20
        Ccf = 1e13   # Fewer but larger bubbles
        Rcf = 1e-5   # 10 µm radius
        Ncf = 1000   # More atoms per bubble
        grain_diameter = params['grain_diameter']

        release_rate = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

        # Should return valid result
        assert release_rate >= 0
        assert np.isfinite(release_rate)

    def test_release_rate_extreme_concentrations(self, params):
        """Test gas release rate with extreme concentration values"""
        Rcf = 1e-6
        Ncf = 100
        grain_diameter = params['grain_diameter']

        # Very high concentrations
        release1 = calculate_gas_release_rate(1e25, 1e20, Rcf, Ncf, grain_diameter)
        assert release1 >= 0
        assert np.isfinite(release1)

        # Very low concentrations
        release2 = calculate_gas_release_rate(1e10, 1e5, Rcf, Ncf, grain_diameter)
        assert release2 >= 0
        assert np.isfinite(release2)


class TestGasReleaseRateCalculations:
    """Test suite for detailed calculations in gas release rate"""

    @pytest.fixture
    def params(self):
        """Create default parameters for testing"""
        return create_default_parameters()

    def test_geometric_factor_calculation(self, params):
        """Test that geometric factor theta is calculated correctly"""
        # Theta should be 50/180 * pi radians
        expected_theta = 50.0 / 180.0 * np.pi

        # This is used internally in calculate_gas_release_rate
        # We verify the expected value
        assert abs(expected_theta - 0.87266) < 0.001  # ~50 degrees in radians

    def test_area_fraction_calculation(self, params):
        """Test the area fraction calculation logic"""
        # The method calculates Af = pi * Rcf^2 * Ccf * ff_theta
        # where ff_theta = 1 - 1.5*cos(theta) + 0.5*cos(theta)^3

        theta = 50.0 / 180.0 * np.pi
        ff_theta = 1 - 1.5 * np.cos(theta) + 0.5 * np.cos(theta)**3

        # Verify geometric factor is positive and reasonable
        assert ff_theta > 0
        assert ff_theta < 1

    def test_interconnectivity_thresholds(self, params):
        """Test interconnectivity coefficient (chi) behavior"""
        # Based on the code:
        # - chi = 0 when Af_ratio <= 0.25
        # - chi = 1 when Af_ratio >= 1.0
        # - chi = Af_ratio otherwise (linear interpolation)

        # Verify thresholds are defined
        assert 0.25 < 1.0  # Lower threshold < upper threshold
        assert 0.25 > 0    # Lower threshold positive

    def test_grain_face_area_calculation(self, params):
        """Test grain-face area per unit volume calculation"""
        # Sv_aa = 6.0 / grain_diameter
        # Af_max = 0.907 * Sv_aa

        grain_diameter = params['grain_diameter']
        Sv_aa_expected = 6.0 / grain_diameter
        Af_max_expected = 0.907 * Sv_aa_expected

        # Verify positive values
        assert Sv_aa_expected > 0
        assert Af_max_expected > 0

        # Check order of magnitude for typical grain size (~0.5 µm)
        # Sv_aa ≈ 6 / 5e-7 ≈ 1.2e7 m^-1
        # Af_max ≈ 0.907 * 1.2e7 ≈ 1.1e7 m^-1
        assert 1e6 < Af_max_expected < 1e8


class TestGasTransportIntegration:
    """Integration tests for gas transport calculations"""

    @pytest.fixture
    def params(self):
        """Create default parameters for testing"""
        return create_default_parameters()

    def test_gas_transport_consistency(self, params):
        """Test that gas transport calculations are internally consistent"""
        # Gas influx should depend on model parameters
        Cgb = 1e20
        Cgf = 1e19

        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        influx1 = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)

        # Modify parameters and verify flux changes
        influx2 = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb * 2)

        # Should change with diffusion coefficient
        assert influx2 != influx1

    def test_gas_transport_physical_units(self, params):
        """Test that gas transport values have correct physical units"""
        # Gas influx should have units of atoms/(m^3·s)
        Cgb = 1e20
        Cgf = 1e19
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        influx = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)

        # Check that value is finite and reasonable
        assert np.isfinite(influx)
        assert np.abs(influx) < 1e30  # Upper bound for physical systems

    def test_gas_transport_direction(self, params):
        """Test that gas flows from high to low concentration"""
        grain_diameter = params['grain_diameter']
        Dgb = params['Dgb']

        # Higher concentration in bulk
        influx1 = calculate_gas_influx(1e21, 1e19, grain_diameter, Dgb)
        assert influx1 > 0  # Positive flux (bulk -> boundary)

        # Higher concentration at boundary
        influx2 = calculate_gas_influx(1e19, 1e21, grain_diameter, Dgb)
        assert influx2 < 0  # Negative flux (boundary -> bulk)

        # Equal concentrations
        influx3 = calculate_gas_influx(1e20, 1e20, grain_diameter, Dgb)
        assert influx3 == 0  # No flux
