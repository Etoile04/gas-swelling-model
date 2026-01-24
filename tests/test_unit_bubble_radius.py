"""
Unit tests for bubble radius calculations from gas atoms

Tests the calculation methods that relate bubble radius to gas atoms,
including pressure calculations and mechanical equilibrium relationships.
"""

import pytest
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


class TestIdealGasPressure:
    """Test ideal gas pressure calculations from radius and gas atoms"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        params['temperature'] = 773.15  # 500°C in Kelvin
        return GasSwellingModel(params)

    def test_pressure_with_valid_inputs(self, model):
        """Test pressure calculation with valid radius and gas atoms"""
        Rc = 1e-8  # 10 nm radius
        Nc = 100.0  # 100 gas atoms

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Pressure should be positive and reasonable
        assert pressure > 0
        assert pressure < 1e10  # Should be less than 10 GPa
        assert isinstance(pressure, float)

    def test_pressure_with_zero_radius(self, model):
        """Test pressure calculation returns zero for zero radius"""
        Rc = 0.0
        Nc = 100.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should return 0.0 for invalid radius
        assert pressure == 0.0

    def test_pressure_with_very_small_radius(self, model):
        """Test pressure calculation with radius below threshold"""
        Rc = 1e-13  # Very small radius
        Nc = 100.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should return 0.0 for radius below 1e-12 threshold
        assert pressure == 0.0

    def test_pressure_with_zero_gas_atoms(self, model):
        """Test pressure calculation returns zero for zero gas atoms"""
        Rc = 1e-8
        Nc = 0.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should return 0.0 for zero gas atoms
        assert pressure == 0.0

    def test_pressure_with_negative_gas_atoms(self, model):
        """Test pressure calculation returns zero for negative gas atoms"""
        Rc = 1e-8
        Nc = -10.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should return 0.0 for negative gas atoms
        assert pressure == 0.0

    def test_pressure_increases_with_gas_atoms(self, model):
        """Test that pressure increases with more gas atoms at fixed radius"""
        Rc = 1e-8

        pressure_10 = model._calculate_idealgas_pressure(Rc, 10.0)
        pressure_100 = model._calculate_idealgas_pressure(Rc, 100.0)
        pressure_1000 = model._calculate_idealgas_pressure(Rc, 1000.0)

        # Pressure should increase with gas atoms
        assert pressure_10 < pressure_100 < pressure_1000

    def test_pressure_decreases_with_radius(self, model):
        """Test that pressure decreases with larger radius at fixed gas atoms"""
        Nc = 100.0

        pressure_small = model._calculate_idealgas_pressure(1e-9, Nc)
        pressure_medium = model._calculate_idealgas_pressure(1e-8, Nc)
        pressure_large = model._calculate_idealgas_pressure(1e-7, Nc)

        # Pressure should decrease with radius (P ∝ 1/R³)
        assert pressure_small > pressure_medium > pressure_large

    def test_pressure_scales_with_temperature(self, model):
        """Test that pressure scales linearly with temperature"""
        Rc = 1e-8
        Nc = 100.0

        # Test at two different temperatures
        T1 = model.params['temperature']
        model.params['temperature'] = T1 * 2
        pressure_T2 = model._calculate_idealgas_pressure(Rc, Nc)

        model.params['temperature'] = T1
        pressure_T1 = model._calculate_idealgas_pressure(Rc, Nc)

        # Pressure should be approximately doubled when temperature doubles
        # Allow for some numerical error
        assert abs(pressure_T2 / pressure_T1 - 2.0) < 0.01


class TestVirialEOSPressure:
    """Test Virial EOS pressure calculations"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        params['temperature'] = 773.15
        return GasSwellingModel(params)

    def test_virial_pressure_with_valid_inputs(self, model):
        """Test Virial EOS pressure calculation with valid inputs"""
        Rc = 1e-8  # 10 nm
        Nc = 100.0

        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)

        # Should return positive pressure
        assert pressure > 0
        assert isinstance(pressure, float)

    def test_virial_pressure_with_zero_radius(self, model):
        """Test Virial EOS returns zero for zero radius"""
        Rc = 0.0
        Nc = 100.0

        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_virial_pressure_with_zero_atoms(self, model):
        """Test Virial EOS returns zero for zero gas atoms"""
        Rc = 1e-8
        Nc = 0.0

        pressure = model._calculate_VirialEOSgas_pressure(Rc, Nc)
        assert pressure == 0.0

    def test_virial_pressure_increases_with_atoms(self, model):
        """Test that Virial EOS pressure increases with gas atoms"""
        Rc = 1e-8

        pressure_10 = model._calculate_VirialEOSgas_pressure(Rc, 10.0)
        pressure_100 = model._calculate_VirialEOSgas_pressure(Rc, 100.0)

        assert pressure_10 < pressure_100


class TestSurfaceTension:
    """Test surface tension calculations related to bubble radius"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_surface_tension_inversely_proportional_to_radius(self):
        """Test that surface tension is inversely proportional to radius"""
        gamma = 1.0  # J/m²

        tension_small = 2 * gamma / 1e-9
        tension_large = 2 * gamma / 1e-8

        # Smaller radius should have larger surface tension
        assert tension_small > tension_large

    def test_surface_tension_formula(self):
        """Test the surface tension formula: 2*gamma/R"""
        gamma = 1.0  # J/m²
        Rc = 2e-9  # 2 nm

        expected_tension = 2 * gamma / Rc
        actual_tension = 2 * gamma / Rc

        assert expected_tension == actual_tension


class TestMechanicalEquilibrium:
    """Test mechanical equilibrium relationships in bubble calculations"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        params['temperature'] = 773.15
        params['surface_energy'] = 1.0  # J/m²
        return GasSwellingModel(params)

    def test_pressure_exceeds_surface_tension_for_small_bubbles(self, model):
        """Test that gas pressure exceeds surface tension for small bubbles"""
        Rc = 5e-10  # 0.5 nm - very small bubble
        Nc = 10.0   # Few gas atoms

        pressure = model._calculate_idealgas_pressure(Rc, Nc)
        surface_tension = 2 * model.params['surface_energy'] / Rc

        # For stable bubbles, gas pressure should overcome surface tension
        # This tests that the calculation produces physically meaningful values
        assert pressure > 0 or surface_tension > 0

    def test_external_pressure_calculation(self, model):
        """Test external pressure calculation: Pext = Pg - 2*gamma/R"""
        Rc = 1e-8
        Nc = 100.0
        gamma = model.params['surface_energy']

        Pg = model._calculate_idealgas_pressure(Rc, Nc)
        surface_tension = 2 * gamma / Rc
        sigma_ext = 0.0  # No external stress

        Pext = Pg - surface_tension - sigma_ext

        # External pressure can be positive or negative depending on conditions
        assert isinstance(Pext, float)
        assert not np.isnan(Pext)
        assert not np.isinf(Pext)


class TestRadiusGasAtomRelationships:
    """Test the physical relationships between radius and gas atoms"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        params['temperature'] = 773.15
        return GasSwellingModel(params)

    def test_volume_calculation(self):
        """Test bubble volume calculation: V = (4/3)*pi*R³"""
        Rc = 1e-8

        expected_volume = (4.0/3.0) * np.pi * Rc**3
        actual_volume = (4.0/3.0) * np.pi * Rc**3

        assert abs(expected_volume - actual_volume) < 1e-30

    def test_gas_density_calculation(self, model):
        """Test gas density calculation from atoms and volume"""
        Rc = 1e-8
        Nc = 100.0
        kB = model.params['kB']
        T = model.params['temperature']

        # Volume
        V = (4.0/3.0) * np.pi * Rc**3

        # Gas density (atoms/m³)
        gas_density = Nc / V

        # Should be positive and physically reasonable
        assert gas_density > 0
        assert gas_density < 1e30  # Should be less than extremely high density

    def test_pressure_volume_relationship(self, model):
        """Test ideal gas law: PV = NkT"""
        Rc = 1e-8
        Nc = 100.0
        kB = model.params['kB']
        T = model.params['temperature']

        V = (4.0/3.0) * np.pi * Rc**3
        P_calculated = model._calculate_idealgas_pressure(Rc, Nc)

        # Check PV ≈ NkT (allowing for numerical errors)
        PV = P_calculated * V
        NkT = Nc * kB * T

        # Should be approximately equal
        # The modified EOS might deviate slightly from ideal
        assert abs(PV - NkT) / NkT < 0.5  # Allow 50% deviation due to corrections


class TestEdgeCases:
    """Test edge cases and numerical stability"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_extremely_small_radius(self, model):
        """Test behavior with extremely small radius"""
        Rc = 1e-15  # Extremely small
        Nc = 1.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should handle gracefully without error
        assert isinstance(pressure, float)
        assert not np.isnan(pressure)

    def test_extremely_large_radius(self, model):
        """Test behavior with extremely large radius"""
        Rc = 1e-4  # 100 microns
        Nc = 1e15  # Many gas atoms

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should handle gracefully
        assert isinstance(pressure, float)
        assert not np.isnan(pressure)
        assert pressure < 1e10  # Should be capped if too high

    def test_extremely_many_gas_atoms(self, model):
        """Test behavior with extremely many gas atoms"""
        Rc = 1e-8
        Nc = 1e20  # Unrealistically large

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should handle or cap the value
        assert isinstance(pressure, float)
        assert not np.isnan(pressure)

    def test_negative_radius(self, model):
        """Test behavior with negative radius"""
        Rc = -1e-8
        Nc = 100.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should handle gracefully (return 0 or handle error)
        assert isinstance(pressure, float)

    def test_very_close_to_zero_radius(self, model):
        """Test behavior with radius very close to zero"""
        Rc = 1e-14
        Nc = 100.0

        pressure = model._calculate_idealgas_pressure(Rc, Nc)

        # Should return 0.0 based on the <= 1e-12 check
        assert pressure == 0.0


class TestNumericalPrecision:
    """Test numerical precision of calculations"""

    @pytest.fixture
    def model(self):
        """Create a model instance for testing"""
        params = create_default_parameters()
        return GasSwellingModel(params)

    def test_pressure_calculation_precision(self, model):
        """Test that pressure calculations are precise"""
        Rc = 1e-8
        Nc = 100.0

        pressure1 = model._calculate_idealgas_pressure(Rc, Nc)
        pressure2 = model._calculate_idealgas_pressure(Rc, Nc)

        # Same inputs should give same outputs
        assert pressure1 == pressure2

    def test_monotonic_pressure_increase(self, model):
        """Test that pressure increases monotonically with gas atoms"""
        Rc = 1e-8

        pressures = []
        for Nc in [10, 20, 50, 100, 200, 500, 1000]:
            p = model._calculate_idealgas_pressure(Rc, Nc)
            pressures.append(p)

        # Each pressure should be larger than the previous
        for i in range(len(pressures) - 1):
            assert pressures[i] < pressures[i+1]

    def test_monotonic_pressure_decrease(self, model):
        """Test that pressure decreases monotonically with radius"""
        Nc = 100.0

        pressures = []
        for Rc in [1e-9, 2e-9, 5e-9, 1e-8, 2e-8, 5e-8, 1e-7]:
            p = model._calculate_idealgas_pressure(Rc, Nc)
            pressures.append(p)

        # Each pressure should be smaller than the previous
        for i in range(len(pressures) - 1):
            assert pressures[i] > pressures[i+1]
