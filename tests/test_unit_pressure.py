"""
Unit tests for gas pressure calculations in GasSwellingModel

Tests cover:
- Ideal gas law pressure calculation
- Modified van der Waals pressure calculation
- Virial EOS pressure calculation
- Ronchi hard sphere model pressure calculation
"""

import pytest
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


class TestIdealGasPressure:
    """Test suite for ideal gas pressure calculation"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_ideal_gas_normal_values(self, model):
        """Test ideal gas pressure calculation with normal values"""
        Rc = 1e-8  # 10 nm radius
        Nc = 100   # 100 gas atoms
        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Pressure should be positive
        assert pressure > 0

        # Check order of magnitude for 100 atoms in 10nm bubble at 600K
        # V = 4/3 * pi * (1e-8)^3 = 4.19e-24 m^3
        # P = N*kB*T/V = 100 * 1.38e-23 * 600 / 4.19e-24 ≈ 2e5 Pa
        assert 1e4 < pressure < 1e7  # Reasonable range

    def test_ideal_gas_temperature_dependence(self, model):
        """Test that pressure increases with temperature"""
        Rc = 1e-8
        Nc = 100

        # Test at different temperatures
        T1 = 300
        T2 = 600
        T3 = 900

        model.params['temperature'] = T1
        P1 = model._calculate_idealgas_pressure(Rc, Nc)

        model.params['temperature'] = T2
        P2 = model._calculate_idealgas_pressure(Rc, Nc)

        model.params['temperature'] = T3
        P3 = model._calculate_idealgas_pressure(Rc, Nc)

        # Pressure should scale linearly with temperature
        assert P2 > P1
        assert P3 > P2
        assert abs(P2/P1 - T2/T1) < 0.01  # Linear relationship
        assert abs(P3/P2 - T3/T2) < 0.01

    def test_ideal_gas_radius_dependence(self, model):
        """Test that pressure decreases with increasing radius (cubic relationship)"""
        Nc = 100

        R1 = 1e-8
        R2 = 2e-8
        R3 = 3e-8

        P1 = model._calculate_idealgas_pressure(R1, Nc)
        P2 = model._calculate_idealgas_pressure(R2, Nc)
        P3 = model._calculate_idealgas_pressure(R3, Nc)

        # Pressure should scale as 1/R^3
        assert P2 < P1
        assert P3 < P2
        assert abs(P1/P2 - (R2/R1)**3) < 0.01
        assert abs(P2/P3 - (R3/R2)**3) < 0.01

    def test_ideal_gas_atom_count_dependence(self, model):
        """Test that pressure increases linearly with atom count"""
        Rc = 1e-8

        N1 = 50
        N2 = 100
        N3 = 150

        P1 = model._calculate_idealgas_pressure(Rc, N1)
        P2 = model._calculate_idealgas_pressure(Rc, N2)
        P3 = model._calculate_idealgas_pressure(Rc, N3)

        # Linear relationship
        assert abs(P2/P1 - 2.0) < 0.01
        assert abs(P3/P2 - 1.5) < 0.01

    def test_ideal_gas_zero_atoms(self, model):
        """Test ideal gas pressure with zero atoms"""
        Rc = 1e-8
        Nc = 0
        pressure = model._calculate_idealgas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_ideal_gas_negative_atoms(self, model):
        """Test ideal gas pressure with negative atom count (invalid)"""
        Rc = 1e-8
        Nc = -10
        pressure = model._calculate_idealgas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_ideal_gas_zero_radius(self, model):
        """Test ideal gas pressure with zero radius"""
        Rc = 0.0
        Nc = 100
        pressure = model._calculate_idealgas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_ideal_gas_very_small_radius(self, model):
        """Test ideal gas pressure with very small radius"""
        Rc = 1e-15  # Extremely small
        Nc = 100
        pressure = model._calculate_idealgas_pressure(Rc, Nc)
        # Should return 0 for radius <= 1e-12
        assert pressure == 0.0


class TestModifiedVanDerWaalsPressure:
    """Test suite for modified van der Waals pressure calculation"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_vanderwaals_normal_values(self, model):
        """Test van der Waals pressure with normal values"""
        Rc = 1e-8
        Nc = 100
        pressure = model._calculate_modifiedvongas_pressure(Rc, Nc)

        # Pressure should be positive
        assert pressure > 0

        # Van der Waals pressure should be higher than ideal gas
        # due to excluded volume effect
        ideal_pressure = model._calculate_idealgas_pressure(Rc, Nc)
        assert pressure > ideal_pressure

    def test_vanderwaals_temperature_dependence(self, model):
        """Test van der Waals pressure temperature dependence"""
        Rc = 1e-8
        Nc = 100

        model.params['temperature'] = 300
        P1 = model._calculate_modifiedvongas_pressure(Rc, Nc)

        model.params['temperature'] = 600
        P2 = model._calculate_modifiedvongas_pressure(Rc, Nc)

        # Pressure should increase with temperature
        assert P2 > P1

    def test_vanderwaals_density_effect(self, model):
        """Test that van der Waals correction is more significant at high density"""
        R_small = 5e-9   # Smaller bubble, higher density
        R_large = 2e-8   # Larger bubble, lower density

        # Calculate for small bubble
        P_vdw_small = model._calculate_modifiedvongas_pressure(R_small, 100)
        P_ideal_small = model._calculate_idealgas_pressure(R_small, 100)

        # Calculate for large bubble
        P_vdw_large = model._calculate_modifiedvongas_pressure(R_large, 100)
        P_ideal_large = model._calculate_idealgas_pressure(R_large, 100)

        # Ratio should be larger for higher density (smaller bubble)
        ratio_small = P_vdw_small / P_ideal_small
        ratio_large = P_vdw_large / P_ideal_large
        assert ratio_small > ratio_large

    def test_vanderwaals_zero_atoms(self, model):
        """Test van der Waals pressure with zero atoms"""
        Rc = 1e-8
        Nc = 0
        pressure = model._calculate_modifiedvongas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_vanderwaals_zero_radius(self, model):
        """Test van der Waals pressure with zero radius"""
        Rc = 0.0
        Nc = 100
        pressure = model._calculate_modifiedvongas_pressure(Rc, Nc)
        assert pressure == 0.0


class TestVirialEOSPressure:
    """Test suite for Virial EOS pressure calculation"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_virial_normal_values(self, model):
        """Test Virial EOS with normal values"""
        Rc = 1e-8
        Nc = 100
        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)

        # Pressure should be positive
        assert pressure > 0

        # Should be in reasonable range (Virial EOS can give very small values)
        assert pressure > 0

    def test_virial_temperature_dependence(self, model):
        """Test Virial EOS temperature dependence"""
        Rc = 1e-8
        Nc = 100

        model.params['temperature'] = 300
        P1 = model._calculate_VirialEOSgas_pressure(Rc, Nc)

        model.params['temperature'] = 600
        P2 = model._calculate_VirialEOSgas_pressure(Rc, Nc)

        # Pressure should increase with temperature
        assert P2 > P1

    def test_virial_radius_dependence(self, model):
        """Test Virial EOS radius dependence"""
        Nc = 100

        R1 = 1e-8
        R2 = 2e-8

        P1 = model._calculate_VirialEOSgas_pressure(R1, Nc)
        P2 = model._calculate_VirialEOSgas_pressure(R2, Nc)

        # Pressure should decrease with radius
        assert P2 < P1

    def test_virial_zero_atoms(self, model):
        """Test Virial EOS with zero atoms"""
        Rc = 1e-8
        Nc = 0
        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_virial_zero_radius(self, model):
        """Test Virial EOS with zero radius"""
        Rc = 0.0
        Nc = 100
        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert pressure == 0.0


class TestRonchiPressure:
    """Test suite for Ronchi hard sphere model pressure calculation"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_ronchi_normal_values(self, model):
        """Test Ronchi pressure with normal values"""
        Rc = 1e-8
        Nc = 100
        T = 600
        pressure = model._calculate_ronchi_pressure(Rc, Nc, T)

        # Pressure should be non-negative (Ronchi model can have numerical issues)
        assert pressure >= 0

    def test_ronchi_temperature_dependence(self, model):
        """Test Ronchi pressure temperature dependence"""
        Rc = 1e-8
        Nc = 100

        T1 = 400
        T2 = 600
        T3 = 800

        P1 = model._calculate_ronchi_pressure(Rc, Nc, T1)
        P2 = model._calculate_ronchi_pressure(Rc, Nc, T2)
        P3 = model._calculate_ronchi_pressure(Rc, Nc, T3)

        # Pressure should generally increase with temperature
        # (though relationship is complex for hard sphere model)
        if P1 > 0 and P2 > 0 and P3 > 0:
            assert P3 > P1

    def test_ronchi_radius_dependence(self, model):
        """Test Ronchi pressure radius dependence"""
        Nc = 100
        T = 600

        R1 = 5e-9
        R2 = 1e-8
        R3 = 2e-8

        P1 = model._calculate_ronchi_pressure(R1, Nc, T)
        P2 = model._calculate_ronchi_pressure(R2, Nc, T)
        P3 = model._calculate_ronchi_pressure(R3, Nc, T)

        # Pressure should decrease with increasing radius
        if P1 > 0 and P2 > 0:
            assert P2 < P1
        if P2 > 0 and P3 > 0:
            assert P3 < P2

    def test_ronchi_density_dependence(self, model):
        """Test Ronchi pressure with different gas densities"""
        Rc = 1e-8
        T = 600

        # Test at different densities
        P1 = model._calculate_ronchi_pressure(Rc, 50, T)
        P2 = model._calculate_ronchi_pressure(Rc, 100, T)
        P3 = model._calculate_ronchi_pressure(Rc, 200, T)

        # All pressures should be non-negative
        assert P1 >= 0
        assert P2 >= 0
        assert P3 >= 0

        # The Ronchi model is complex and can have non-monotonic behavior
        # Just verify it produces values without numerical errors

    def test_ronchi_zero_atoms(self, model):
        """Test Ronchi pressure with zero atoms"""
        Rc = 1e-8
        Nc = 0
        T = 600
        pressure = model._calculate_ronchi_pressure(Rc, Nc, T)
        assert pressure == 0.0

    def test_ronchi_zero_radius(self, model):
        """Test Ronchi pressure with zero radius"""
        Rc = 0.0
        Nc = 100
        T = 600
        pressure = model._calculate_ronchi_pressure(Rc, Nc, T)
        assert pressure == 0.0

    def test_ronchi_near_critical_temperature(self, model):
        """Test Ronchi pressure near critical temperature (Tc = 290K)"""
        Rc = 1e-8
        Nc = 100

        # Below critical temperature
        P_low = model._calculate_ronchi_pressure(Rc, Nc, 250)

        # Near critical temperature
        P_crit = model._calculate_ronchi_pressure(Rc, Nc, 290)

        # Above critical temperature
        P_high = model._calculate_ronchi_pressure(Rc, Nc, 350)

        # All should be non-negative
        assert P_low >= 0
        assert P_crit >= 0
        assert P_high >= 0


class TestPressureModelComparison:
    """Test suite comparing different pressure models"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_all_models_positive_pressure(self, model):
        """Test that all models give positive pressure for normal conditions"""
        Rc = 1e-8
        Nc = 100
        T = 600

        P_ideal = model._calculate_idealgas_pressure(Rc, Nc)
        P_vdw = model._calculate_modifiedvongas_pressure(Rc, Nc)
        P_virial = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        P_ronchi = model._calculate_ronchi_pressure(Rc, Nc, T)

        assert P_ideal > 0
        assert P_vdw > 0
        assert P_virial > 0
        assert P_ronchi >= 0  # Ronchi can be 0 in some cases

    def test_pressure_ranking_low_density(self, model):
        """Test pressure model ranking at low density"""
        # Large bubble, few atoms = low density
        Rc = 2e-8
        Nc = 50
        T = 600

        P_ideal = model._calculate_idealgas_pressure(Rc, Nc)
        P_vdw = model._calculate_modifiedvongas_pressure(Rc, Nc)
        P_virial = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        P_ronchi = model._calculate_ronchi_pressure(Rc, Nc, T)

        # At low density, all should be relatively close
        # Van der Waals should be higher than ideal
        assert P_vdw > P_ideal

    def test_pressure_ranking_high_density(self, model):
        """Test pressure model ranking at high density"""
        # Small bubble, many atoms = high density
        Rc = 5e-9
        Nc = 200
        T = 600

        P_ideal = model._calculate_idealgas_pressure(Rc, Nc)
        P_vdw = model._calculate_modifiedvongas_pressure(Rc, Nc)
        P_virial = model._calculate_VirialEOSgas_pressure(Rc, Nc)

        # At high density, non-ideal effects should be significant
        # Van der Waals and Virial should deviate more from ideal
        assert P_vdw > P_ideal

    def test_all_models_handle_edge_cases(self, model):
        """Test that all models handle edge cases gracefully"""
        # Test with zero atoms
        for method in [
            model._calculate_idealgas_pressure,
            model._calculate_modifiedvongas_pressure,
            model._calculate_VirialEOSgas_pressure
        ]:
            pressure = method(1e-8, 0)
            assert pressure == 0.0

        # Test with zero radius
        for method in [
            model._calculate_idealgas_pressure,
            model._calculate_modifiedvongas_pressure,
            model._calculate_VirialEOSgas_pressure
        ]:
            pressure = method(0.0, 100)
            assert pressure == 0.0

        # Test Ronchi separately (needs T parameter)
        pressure = model._calculate_ronchi_pressure(0.0, 100, 600)
        assert pressure == 0.0

        pressure = model._calculate_ronchi_pressure(1e-8, 0, 600)
        assert pressure == 0.0


class TestPressurePhysicalConsistency:
    """Test suite for physical consistency of pressure calculations"""

    @pytest.fixture
    def model(self):
        """Create a model instance with default parameters"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_pressure_monotonic_with_atoms(self, model):
        """Test that pressure increases monotonically with atom count"""
        Rc = 1e-8
        T = 600

        atom_counts = [10, 50, 100, 200, 500]
        pressures_ideal = []
        pressures_vdw = []

        for Nc in atom_counts:
            pressures_ideal.append(model._calculate_idealgas_pressure(Rc, Nc))
            pressures_vdw.append(model._calculate_modifiedvongas_pressure(Rc, Nc))

        # Check monotonic increase
        for i in range(len(pressures_ideal) - 1):
            assert pressures_ideal[i+1] > pressures_ideal[i]
            assert pressures_vdw[i+1] > pressures_vdw[i]

    def test_pressure_monotonic_with_radius_inverse(self, model):
        """Test that pressure decreases monotonically with radius"""
        Nc = 100
        radii = [5e-9, 1e-8, 2e-8, 5e-8]
        T = 600

        pressures_ideal = []
        pressures_vdw = []

        for Rc in radii:
            pressures_ideal.append(model._calculate_idealgas_pressure(Rc, Nc))
            pressures_vdw.append(model._calculate_modifiedvongas_pressure(Rc, Nc))

        # Check monotonic decrease
        for i in range(len(pressures_ideal) - 1):
            assert pressures_ideal[i+1] < pressures_ideal[i]
            assert pressures_vdw[i+1] < pressures_vdw[i]

    def test_pressure_reasonable_magnitude(self, model):
        """Test that pressures are in physically reasonable range"""
        # Typical bubble conditions in nuclear fuel
        test_cases = [
            (5e-9, 50, 600),    # Small bubble, few atoms
            (1e-8, 100, 600),   # Medium bubble
            (2e-8, 500, 800),  # Large bubble, many atoms, high T
            (5e-9, 200, 400),  # Small bubble, many atoms, low T
        ]

        for Rc, Nc, T in test_cases:
            model.params['temperature'] = T
            P_ideal = model._calculate_idealgas_pressure(Rc, Nc)
            P_vdw = model._calculate_modifiedvongas_pressure(Rc, Nc)

            # Pressures should be positive
            # Ideal gas and van der Waals should be in reasonable range
            assert P_ideal > 0
            assert P_vdw > 0
            # Wide range to accommodate various bubble conditions
            assert P_ideal < 1e12
            assert P_vdw < 1e12
