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
