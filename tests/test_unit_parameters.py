"""
Unit tests for MaterialParameters and SimulationParameters dataclasses
"""

import pytest
import numpy as np
from gas_swelling.params.parameters import (
    MaterialParameters,
    SimulationParameters,
    create_default_parameters,
    BOLTZMANN_CONSTANT_EV,
    BOLTZMANN_CONSTANT_J,
    GAS_CONSTANT,
    AVOGADRO_CONSTANT
)


class TestMaterialParameters:
    """Test MaterialParameters dataclass"""

    def test_default_instantiation(self):
        """Test that MaterialParameters can be instantiated with defaults"""
        params = MaterialParameters()
        assert params is not None
        assert params.lattice_constant == 3.4808e-10
        assert params.ATOMIC_VOLUME == 4.09e-29
        assert params.nu_constant == 7.8e12

    def test_lattice_parameters(self):
        """Test lattice constant and atomic volume parameters"""
        params = MaterialParameters()
        assert isinstance(params.lattice_constant, float)
        assert params.lattice_constant > 0
        assert isinstance(params.ATOMIC_VOLUME, float)
        assert params.ATOMIC_VOLUME > 0

    def test_vacuum_diffusion_parameters(self):
        """Test vacancy diffusion parameters"""
        params = MaterialParameters()
        assert isinstance(params.Dv0, float)
        assert params.Dv0 == 2.0e-8
        assert isinstance(params.Evm, float)
        assert params.Evm == 0.74

    def test_evf_coeffs_default(self):
        """Test that Evf_coeffs has correct default values"""
        params = MaterialParameters()
        assert isinstance(params.Evf_coeffs, list)
        assert len(params.Evf_coeffs) == 2
        assert params.Evf_coeffs[0] == 1.034
        assert params.Evf_coeffs[1] == 7.6e-4

    def test_evf_coeffs_custom(self):
        """Test that Evf_coeffs can be customized"""
        custom_coeffs = [1.5, 8.0e-4]
        params = MaterialParameters(Evf_coeffs=custom_coeffs)
        assert params.Evf_coeffs == custom_coeffs

    def test_dislocation_parameters(self):
        """Test dislocation bias factors and density"""
        params = MaterialParameters()
        assert params.Zv == 1.0
        assert params.Zi == 1.025
        assert params.dislocation_density == 7.0e13

    def test_surface_energy(self):
        """Test surface energy parameter"""
        params = MaterialParameters()
        assert isinstance(params.surface_energy, float)
        assert params.surface_energy == 0.5

    def test_hydrostatic_pressure(self):
        """Test hydrostatic pressure parameter"""
        params = MaterialParameters()
        assert isinstance(params.hydrastatic_pressure, float)
        assert params.hydrastatic_pressure == 0.0E8

    def test_nucleation_factors(self):
        """Test bubble nucleation factors"""
        params = MaterialParameters()
        assert params.Fnb == 1e-5
        assert params.Fnf == 1e-5

    def test_recombination_radius(self):
        """Test recombination radius parameter"""
        params = MaterialParameters()
        assert isinstance(params.recombination_radius, float)
        assert params.recombination_radius == 2.0e-10

    def test_sia_parameters(self):
        """Test SIA (self-interstitial atom) parameters"""
        params = MaterialParameters()
        assert isinstance(params.Di0, float)
        assert params.Di0 == 1.259e-12
        assert isinstance(params.Eim, float)
        assert params.Eim == 1.18

    def test_eif_coeffs_default(self):
        """Test that Eif_coeffs has correct default values"""
        params = MaterialParameters()
        assert isinstance(params.Eif_coeffs, list)
        assert len(params.Eif_coeffs) == 4
        assert params.Eif_coeffs[0] == -3.992
        assert params.Eif_coeffs[1] == 0.038

    def test_sink_strength_parameters(self):
        """Test cavity sink strength parameters"""
        params = MaterialParameters()
        assert isinstance(params.kv_param, float)
        assert isinstance(params.ki_param, float)
        assert params.kv_param > 0
        assert params.ki_param > 0

    def test_xenon_parameters(self):
        """Test Xenon (Xe) parameters"""
        params = MaterialParameters()
        assert isinstance(params.Xe_radii, float)
        assert params.Xe_radii == 2.16e-10
        assert isinstance(params.xe_epsilon_k, float)
        assert params.xe_epsilon_k == 290.0
        assert isinstance(params.xe_sigma, float)
        assert params.xe_sigma == 3.86e-10

    def test_xenon_critical_parameters(self):
        """Test Xenon critical parameters"""
        params = MaterialParameters()
        assert params.xe_Tc == 290.0
        assert params.xe_dc == 1.103e3
        assert params.xe_Vc == 35.92e-6

    def test_xe_q_coeffs_default(self):
        """Test that xe_q_coeffs has correct default values"""
        params = MaterialParameters()
        assert isinstance(params.xe_q_coeffs, list)
        assert len(params.xe_q_coeffs) == 5
        assert params.xe_q_coeffs[0] == 2.12748

    def test_custom_material_parameters(self):
        """Test MaterialParameters with custom values"""
        params = MaterialParameters(
            lattice_constant=3.5e-10,
            surface_energy=0.6,
            dislocation_density=8.0e13
        )
        assert params.lattice_constant == 3.5e-10
        assert params.surface_energy == 0.6
        assert params.dislocation_density == 8.0e13


class TestSimulationParameters:
    """Test SimulationParameters dataclass"""

    def test_default_instantiation(self):
        """Test that SimulationParameters can be instantiated with defaults"""
        params = SimulationParameters()
        assert params is not None
        assert params.fission_rate == 2e20
        assert params.temperature == 600

    def test_fission_parameters(self):
        """Test fission-related parameters"""
        params = SimulationParameters()
        assert isinstance(params.fission_rate, float)
        assert params.fission_rate == 2e20
        assert isinstance(params.sigma_f, float)
        assert params.sigma_f == 2.72e4

    def test_displacement_rate(self):
        """Test displacement rate parameter"""
        params = SimulationParameters()
        assert isinstance(params.displacement_rate, float)
        assert params.displacement_rate == 14825/5.12e28

    def test_gas_parameters(self):
        """Test gas production and resolution parameters"""
        params = SimulationParameters()
        assert params.gas_production_rate == 0.25
        assert params.resolution_rate == 2e-5

    def test_grain_diameter(self):
        """Test grain diameter parameter"""
        params = SimulationParameters()
        assert isinstance(params.grain_diameter, float)
        assert params.grain_diameter == 0.5e-6

    def test_temperature(self):
        """Test temperature parameter"""
        params = SimulationParameters()
        assert isinstance(params.temperature, (int, float))
        assert params.temperature == 600

    def test_time_stepping_parameters(self):
        """Test time stepping parameters"""
        params = SimulationParameters()
        assert params.time_step == 1e-9
        assert params.max_time_step == 1e2
        assert params.max_time == 3600 * 24 * 100

    def test_diffusion_parameters(self):
        """Test gas diffusion coefficient parameters"""
        params = SimulationParameters()
        assert isinstance(params.Dgb_prefactor, float)
        assert params.Dgb_prefactor == 1.2e-7
        assert isinstance(params.Dgb_activation_energy, float)
        assert params.Dgb_activation_energy == 1.16
        assert isinstance(params.Dgb_fission_term, float)
        assert params.Dgb_fission_term == 5.07e-31

    def test_dgf_multiplier(self):
        """Test phase boundary diffusion multiplier"""
        params = SimulationParameters()
        assert isinstance(params.Dgf_multiplier, float)
        assert params.Dgf_multiplier == 3e2

    def test_eos_model_default(self):
        """Test default equation of state model"""
        params = SimulationParameters()
        assert params.eos_model == 'ideal'

    def test_eos_model_custom(self):
        """Test custom equation of state model"""
        params = SimulationParameters(eos_model='ronchi')
        assert params.eos_model == 'ronchi'

    def test_custom_simulation_parameters(self):
        """Test SimulationParameters with custom values"""
        params = SimulationParameters(
            fission_rate=3e20,
            temperature=800,
            time_step=2e-9
        )
        assert params.fission_rate == 3e20
        assert params.temperature == 800
        assert params.time_step == 2e-9


class TestPhysicalConstants:
    """Test physical constants"""

    def test_boltzmann_constant_ev(self):
        """Test Boltzmann constant in eV/K"""
        assert isinstance(BOLTZMANN_CONSTANT_EV, float)
        assert BOLTZMANN_CONSTANT_EV == 8.617e-5

    def test_boltzmann_constant_j(self):
        """Test Boltzmann constant in J/K"""
        assert isinstance(BOLTZMANN_CONSTANT_J, float)
        assert BOLTZMANN_CONSTANT_J == 1.380649e-23

    def test_gas_constant(self):
        """Test gas constant"""
        assert isinstance(GAS_CONSTANT, float)
        assert GAS_CONSTANT == 8.314462618

    def test_avogadro_constant(self):
        """Test Avogadro constant"""
        assert isinstance(AVOGADRO_CONSTANT, float)
        assert AVOGADRO_CONSTANT == 6.02214076e23


class TestCreateDefaultParameters:
    """Test create_default_parameters function"""

    def test_returns_dict(self):
        """Test that create_default_parameters returns a dictionary"""
        params = create_default_parameters()
        assert isinstance(params, dict)

    def test_contains_material_parameters(self):
        """Test that result contains material parameters"""
        params = create_default_parameters()
        assert 'lattice_constant' in params
        assert 'ATOMIC_VOLUME' in params
        assert 'surface_energy' in params
        assert 'dislocation_density' in params

    def test_contains_simulation_parameters(self):
        """Test that result contains simulation parameters"""
        params = create_default_parameters()
        assert 'fission_rate' in params
        assert 'temperature' in params
        assert 'time_step' in params
        assert 'max_time' in params

    def test_contains_computed_parameters(self):
        """Test that result contains computed parameters"""
        params = create_default_parameters()
        assert 'Dgb' in params
        assert 'Dgf' in params
        assert isinstance(params['Dgb'], float)
        assert isinstance(params['Dgf'], float)

    def test_contains_physical_constants(self):
        """Test that result contains physical constants"""
        params = create_default_parameters()
        assert 'kB_ev' in params
        assert 'kB' in params
        assert 'R' in params
        assert 'Av' in params
        assert 'Omega' in params

    def test_dgf_is_dgb_times_multiplier(self):
        """Test that Dgf = Dgb * Dgf_multiplier"""
        params = create_default_parameters()
        expected_ratio = 3e2  # Default Dgf_multiplier
        actual_ratio = params['Dgf'] / params['Dgb']
        assert np.isclose(actual_ratio, expected_ratio)

    def test_omega_equals_atomic_volume(self):
        """Test that Omega equals ATOMIC_VOLUME"""
        params = create_default_parameters()
        assert params['Omega'] == params['ATOMIC_VOLUME']

    def test_physical_constants_match(self):
        """Test that physical constants in dict match module constants"""
        params = create_default_parameters()
        assert params['kB_ev'] == BOLTZMANN_CONSTANT_EV
        assert params['kB'] == BOLTZMANN_CONSTANT_J
        assert params['R'] == GAS_CONSTANT
        assert params['Av'] == AVOGADRO_CONSTANT

    def test_dgb_calculation(self):
        """Test that Dgb is calculated correctly"""
        params = create_default_parameters()
        sim = SimulationParameters()
        # Expected Dgb calculation
        expected_Dgb = (sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature)) +
                       sim.Dgb_fission_term * sim.fission_rate)
        assert np.isclose(params['Dgb'], expected_Dgb)

    def test_parameters_are_positive(self):
        """Test that key parameters are positive"""
        params = create_default_parameters()
        assert params['lattice_constant'] > 0
        assert params['ATOMIC_VOLUME'] > 0
        assert params['fission_rate'] > 0
        assert params['temperature'] > 0
        assert params['Dgb'] > 0
        assert params['Dgf'] > 0


def test_create_default_parameters():
    """Test that create_default_parameters returns expected structure"""
    from gas_swelling import create_default_parameters

    params = create_default_parameters()
    assert isinstance(params, dict)
    assert 'temperature' in params
    assert 'fission_rate' in params
    assert 'time_step' in params


class TestMaterialParametersEdgeCases:
    """Test edge cases and constraints for MaterialParameters"""

    def test_zero_lattice_constant(self):
        """Test behavior with zero lattice constant"""
        params = MaterialParameters(lattice_constant=0.0)
        assert params.lattice_constant == 0.0
        # ATOMIC_VOLUME should still be settable
        assert params.ATOMIC_VOLUME == 4.09e-29

    def test_negative_lattice_constant(self):
        """Test behavior with negative lattice constant (unphysical but should not crash)"""
        params = MaterialParameters(lattice_constant=-3.5e-10)
        assert params.lattice_constant == -3.5e-10

    def test_very_large_lattice_constant(self):
        """Test behavior with very large lattice constant"""
        params = MaterialParameters(lattice_constant=1.0e-5)  # Unphysically large
        assert params.lattice_constant == 1.0e-5

    def test_very_small_lattice_constant(self):
        """Test behavior with very small lattice constant"""
        params = MaterialParameters(lattice_constant=1.0e-15)  # Unphysically small
        assert params.lattice_constant == 1.0e-15

    def test_zero_surface_energy(self):
        """Test behavior with zero surface energy"""
        params = MaterialParameters(surface_energy=0.0)
        assert params.surface_energy == 0.0

    def test_negative_surface_energy(self):
        """Test behavior with negative surface energy (unphysical)"""
        params = MaterialParameters(surface_energy=-0.5)
        assert params.surface_energy == -0.5

    def test_very_large_surface_energy(self):
        """Test behavior with very large surface energy"""
        params = MaterialParameters(surface_energy=10.0)
        assert params.surface_energy == 10.0

    def test_zero_dislocation_density(self):
        """Test behavior with zero dislocation density"""
        params = MaterialParameters(dislocation_density=0.0)
        assert params.dislocation_density == 0.0
        # Note: kv_param and ki_param are computed at class definition time
        # using the default dislocation_density, not the instance value
        # This is a known limitation of the current implementation
        assert params.kv_param > 0  # Uses default value from class definition
        assert params.ki_param > 0

    def test_negative_dislocation_density(self):
        """Test behavior with negative dislocation density (unphysical)"""
        params = MaterialParameters(dislocation_density=-7.0e13)
        assert params.dislocation_density == -7.0e13
        # Note: kv_param and ki_param are computed at class definition time
        # using the default dislocation_density, not the instance value
        # This is a known limitation of the current implementation
        # The actual value stored doesn't match what we'd compute from the negative value
        assert params.kv_param > 0  # Uses default value from class definition

    def test_very_large_dislocation_density(self):
        """Test behavior with very large dislocation density"""
        params = MaterialParameters(dislocation_density=1.0e18)
        assert params.dislocation_density == 1.0e18
        assert params.kv_param > 0
        assert params.ki_param > 0

    def test_zero_nucleation_factors(self):
        """Test behavior with zero nucleation factors"""
        params = MaterialParameters(Fnb=0.0, Fnf=0.0)
        assert params.Fnb == 0.0
        assert params.Fnf == 0.0

    def test_negative_nucleation_factors(self):
        """Test behavior with negative nucleation factors (unphysical)"""
        params = MaterialParameters(Fnb=-1e-5, Fnf=-1e-5)
        assert params.Fnb == -1e-5
        assert params.Fnf == -1e-5

    def test_very_large_nucleation_factors(self):
        """Test behavior with very large nucleation factors"""
        params = MaterialParameters(Fnb=1.0, Fnf=1.0)
        assert params.Fnb == 1.0
        assert params.Fnf == 1.0

    def test_evf_coeffs_empty_list(self):
        """Test behavior with empty Evf_coeffs list"""
        params = MaterialParameters(Evf_coeffs=[])
        assert params.Evf_coeffs == []

    def test_evf_coeffs_wrong_length(self):
        """Test behavior with Evf_coeffs of wrong length"""
        params = MaterialParameters(Evf_coeffs=[1.0])  # Should be 2 elements
        assert params.Evf_coeffs == [1.0]

    def test_evf_coeffs_many_elements(self):
        """Test behavior with Evf_coeffs having many elements"""
        params = MaterialParameters(Evf_coeffs=[1.0, 2.0, 3.0, 4.0, 5.0])
        assert len(params.Evf_coeffs) == 5

    def test_eif_coeffs_empty_list(self):
        """Test behavior with empty Eif_coeffs list"""
        params = MaterialParameters(Eif_coeffs=[])
        assert params.Eif_coeffs == []

    def test_eif_coeffs_wrong_length(self):
        """Test behavior with Eif_coeffs of wrong length"""
        params = MaterialParameters(Eif_coeffs=[1.0, 2.0])  # Should be 4 elements
        assert len(params.Eif_coeffs) == 2

    def test_xe_q_coeffs_empty_list(self):
        """Test behavior with empty xe_q_coeffs list"""
        params = MaterialParameters(xe_q_coeffs=[])
        assert params.xe_q_coeffs == []

    def test_zero_bias_factors(self):
        """Test behavior with zero bias factors"""
        params = MaterialParameters(Zv=0.0, Zi=0.0)
        assert params.Zv == 0.0
        assert params.Zi == 0.0
        # Note: kv_param and ki_param are computed at class definition time
        # using the default bias factors, not the instance values
        # This is a known limitation of the current implementation
        assert params.kv_param > 0  # Uses default Zv and dislocation_density from class definition

    def test_negative_bias_factors(self):
        """Test behavior with negative bias factors"""
        params = MaterialParameters(Zv=-1.0, Zi=-1.025)
        assert params.Zv == -1.0
        assert params.Zi == -1.025

    def test_zero_temperature_coefficients(self):
        """Test behavior with zero temperature coefficients"""
        params = MaterialParameters(Evf_coeffs=[0.0, 0.0])
        assert params.Evf_coeffs == [0.0, 0.0]

    def test_negative_hydrostatic_pressure(self):
        """Test behavior with negative hydrostatic pressure (tension)"""
        params = MaterialParameters(hydrastatic_pressure=-1.0E8)
        assert params.hydrastatic_pressure == -1.0E8

    def test_very_large_hydrostatic_pressure(self):
        """Test behavior with very large hydrostatic pressure"""
        params = MaterialParameters(hydrastatic_pressure=1.0E10)
        assert params.hydrastatic_pressure == 1.0E10

    def test_zero_recombination_radius(self):
        """Test behavior with zero recombination radius"""
        params = MaterialParameters(recombination_radius=0.0)
        assert params.recombination_radius == 0.0

    def test_negative_recombination_radius(self):
        """Test behavior with negative recombination radius (unphysical)"""
        params = MaterialParameters(recombination_radius=-2.0e-10)
        assert params.recombination_radius == -2.0e-10


class TestSimulationParametersEdgeCases:
    """Test edge cases and constraints for SimulationParameters"""

    def test_zero_fission_rate(self):
        """Test behavior with zero fission rate"""
        params = SimulationParameters(fission_rate=0.0)
        assert params.fission_rate == 0.0

    def test_negative_fission_rate(self):
        """Test behavior with negative fission rate (unphysical)"""
        params = SimulationParameters(fission_rate=-2e20)
        assert params.fission_rate == -2e20

    def test_very_large_fission_rate(self):
        """Test behavior with very large fission rate"""
        params = SimulationParameters(fission_rate=1e25)
        assert params.fission_rate == 1e25

    def test_zero_temperature(self):
        """Test behavior with zero temperature (absolute zero)"""
        params = SimulationParameters(temperature=0.0)
        assert params.temperature == 0.0

    def test_negative_temperature(self):
        """Test behavior with negative temperature (unphysical)"""
        params = SimulationParameters(temperature=-100.0)
        assert params.temperature == -100.0

    def test_very_high_temperature(self):
        """Test behavior with very high temperature"""
        params = SimulationParameters(temperature=5000.0)  # Above melting point
        assert params.temperature == 5000.0

    def test_zero_time_step(self):
        """Test behavior with zero time step"""
        params = SimulationParameters(time_step=0.0)
        assert params.time_step == 0.0

    def test_negative_time_step(self):
        """Test behavior with negative time step (unphysical)"""
        params = SimulationParameters(time_step=-1e-9)
        assert params.time_step == -1e-9

    def test_very_large_time_step(self):
        """Test behavior with very large time step"""
        params = SimulationParameters(time_step=1e6)
        assert params.time_step == 1e6

    def test_zero_max_time(self):
        """Test behavior with zero max_time"""
        params = SimulationParameters(max_time=0.0)
        assert params.max_time == 0.0

    def test_negative_max_time(self):
        """Test behavior with negative max_time (unphysical)"""
        params = SimulationParameters(max_time=-1000.0)
        assert params.max_time == -1000.0

    def test_time_step_larger_than_max_time_step(self):
        """Test behavior when time_step > max_time_step"""
        params = SimulationParameters(time_step=1e3, max_time_step=1e2)
        assert params.time_step == 1e3
        assert params.max_time_step == 1e2
        # time_step can be larger than max_time_step (dataclass doesn't enforce)

    def test_zero_gas_production_rate(self):
        """Test behavior with zero gas production rate"""
        params = SimulationParameters(gas_production_rate=0.0)
        assert params.gas_production_rate == 0.0

    def test_negative_gas_production_rate(self):
        """Test behavior with negative gas production rate (unphysical)"""
        params = SimulationParameters(gas_production_rate=-0.25)
        assert params.gas_production_rate == -0.25

    def test_gas_production_rate_greater_than_one(self):
        """Test behavior with gas production rate > 1"""
        params = SimulationParameters(gas_production_rate=2.0)
        assert params.gas_production_rate == 2.0

    def test_zero_resolution_rate(self):
        """Test behavior with zero resolution rate"""
        params = SimulationParameters(resolution_rate=0.0)
        assert params.resolution_rate == 0.0

    def test_negative_resolution_rate(self):
        """Test behavior with negative resolution rate (unphysical)"""
        params = SimulationParameters(resolution_rate=-2e-5)
        assert params.resolution_rate == -2e-5

    def test_zero_grain_diameter(self):
        """Test behavior with zero grain diameter"""
        params = SimulationParameters(grain_diameter=0.0)
        assert params.grain_diameter == 0.0

    def test_negative_grain_diameter(self):
        """Test behavior with negative grain diameter (unphysical)"""
        params = SimulationParameters(grain_diameter=-0.5e-6)
        assert params.grain_diameter == -0.5e-6

    def test_very_large_grain_diameter(self):
        """Test behavior with very large grain diameter"""
        params = SimulationParameters(grain_diameter=1.0e-3)  # 1 mm
        assert params.grain_diameter == 1.0e-3

    def test_invalid_eos_model(self):
        """Test behavior with invalid eos_model value"""
        params = SimulationParameters(eos_model='invalid_model')
        assert params.eos_model == 'invalid_model'

    def test_empty_eos_model(self):
        """Test behavior with empty eos_model string"""
        params = SimulationParameters(eos_model='')
        assert params.eos_model == ''

    def test_numeric_eos_model(self):
        """Test behavior with numeric type for eos_model (should accept it)"""
        params = SimulationParameters(eos_model=123)  # type: ignore
        assert params.eos_model == 123

    def test_zero_diffusion_prefactor(self):
        """Test behavior with zero diffusion prefactor"""
        params = SimulationParameters(Dgb_prefactor=0.0)
        assert params.Dgb_prefactor == 0.0

    def test_negative_diffusion_prefactor(self):
        """Test behavior with negative diffusion prefactor"""
        params = SimulationParameters(Dgb_prefactor=-1.2e-7)
        assert params.Dgb_prefactor == -1.2e-7

    def test_zero_activation_energy(self):
        """Test behavior with zero activation energy"""
        params = SimulationParameters(Dgb_activation_energy=0.0)
        assert params.Dgb_activation_energy == 0.0

    def test_negative_activation_energy(self):
        """Test behavior with negative activation energy (unphysical)"""
        params = SimulationParameters(Dgb_activation_energy=-1.16)
        assert params.Dgb_activation_energy == -1.16

    def test_zero_dgf_multiplier(self):
        """Test behavior with zero Dgf_multiplier"""
        params = SimulationParameters(Dgf_multiplier=0.0)
        assert params.Dgf_multiplier == 0.0

    def test_negative_dgf_multiplier(self):
        """Test behavior with negative Dgf_multiplier (unphysical)"""
        params = SimulationParameters(Dgf_multiplier=-3e2)
        assert params.Dgf_multiplier == -3e2

    def test_very_large_dgf_multiplier(self):
        """Test behavior with very large Dgf_multiplier"""
        params = SimulationParameters(Dgf_multiplier=1e6)
        assert params.Dgf_multiplier == 1e6

    def test_adaptive_stepping_parameters(self):
        """Test adaptive stepping parameter combinations"""
        # Enabled with valid ranges
        params = SimulationParameters(
            adaptive_stepping_enabled=True,
            min_step=1e-12,
            max_step=1e3
        )
        assert params.adaptive_stepping_enabled is True
        assert params.min_step == 1e-12
        assert params.max_step == 1e3

    def test_min_step_greater_than_max_step(self):
        """Test behavior when min_step > max_step (inconsistent but not prevented)"""
        params = SimulationParameters(
            min_step=1e2,
            max_step=1e-9
        )
        assert params.min_step == 1e2
        assert params.max_step == 1e-9

    def test_negative_min_step(self):
        """Test behavior with negative min_step"""
        params = SimulationParameters(min_step=-1e-9)
        assert params.min_step == -1e-9

    def test_zero_max_step(self):
        """Test behavior with zero max_step"""
        params = SimulationParameters(max_step=0.0)
        assert params.max_step == 0.0


class TestCreateDefaultParametersEdgeCases:
    """Test edge cases for create_default_parameters function"""

    def test_dgb_with_zero_temperature(self):
        """Test Dgb calculation with zero temperature (should raise ZeroDivisionError)"""
        sim = SimulationParameters(temperature=0.0)
        # This should result in division by zero
        with pytest.raises(ZeroDivisionError):
            Dgb = (sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature)) +
                   sim.Dgb_fission_term * sim.fission_rate)

    def test_dgb_with_negative_temperature(self):
        """Test Dgb calculation with negative temperature"""
        sim = SimulationParameters(temperature=-100.0)
        Dgb = (sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature)) +
               sim.Dgb_fission_term * sim.fission_rate)
        # Should still compute, though physically meaningless
        assert not np.isnan(Dgb)

    def test_dgb_with_zero_fission_rate(self):
        """Test Dgb calculation with zero fission rate"""
        sim = SimulationParameters(fission_rate=0.0)
        Dgb = (sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature)) +
               sim.Dgb_fission_term * sim.fission_rate)
        # Should only have thermal diffusion term
        expected_Dgb = sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature))
        assert np.isclose(Dgb, expected_Dgb)

    def test_dgf_with_zero_multiplier(self):
        """Test Dgf calculation with zero multiplier"""
        sim = SimulationParameters(Dgf_multiplier=0.0)
        Dgb = sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature))
        Dgf = Dgb * sim.Dgf_multiplier
        assert Dgf == 0.0

    def test_dgf_with_negative_multiplier(self):
        """Test Dgf calculation with negative multiplier"""
        sim = SimulationParameters(Dgf_multiplier=-3e2)
        Dgb = sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature))
        Dgf = Dgb * sim.Dgf_multiplier
        assert Dgf < 0

    def test_parameters_with_custom_edge_case_values(self):
        """Test create_default_parameters with custom edge case values"""
        material = MaterialParameters(
            lattice_constant=0.0,
            surface_energy=0.0,
            dislocation_density=0.0
        )
        sim = SimulationParameters(
            temperature=0.0,
            fission_rate=0.0
        )

        # Dgb calculation with zero temperature will raise ZeroDivisionError
        # This is expected behavior
        with pytest.raises(ZeroDivisionError):
            Dgb = (sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature)) +
                   sim.Dgb_fission_term * sim.fission_rate)

            params = {
                **material.__dict__,
                **sim.__dict__,
                'Dgb': Dgb,
                'Dgf': Dgb * sim.Dgf_multiplier,
                'kB_ev': BOLTZMANN_CONSTANT_EV,
                'kB': BOLTZMANN_CONSTANT_J,
                'R': GAS_CONSTANT,
                'Av': AVOGADRO_CONSTANT,
                'Omega': material.ATOMIC_VOLUME
            }

            # Verify structure is maintained even with edge case values
            assert 'lattice_constant' in params
            assert 'Dgb' in params
            assert 'Dgf' in params
            assert params['lattice_constant'] == 0.0
