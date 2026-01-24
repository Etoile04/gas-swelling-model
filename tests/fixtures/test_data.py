"""
Test data and validation constants for gas swelling model tests.

This module provides reference data from experimental results,
literature values, and extreme condition test cases.
"""

import numpy as np


# ============================================================================
# Validation Data from Reference Paper
# ============================================================================

# U-10Zr alloy validation data (Figure 6 in paper)
# Temperature: 600-800 K, Fission rate: ~2e20 fissions/m^3/s
VALIDATION_DATA_U10ZR = {
    'composition': 'U-10wt%Zr',
    'temperature_range': [600, 700, 800],  # K
    'fission_rate': 2e20,  # fissions/m^3/s
    'burnup_points': np.array([1, 3, 5, 7, 10]),  # at.%
    'swelling_data': {
        600: np.array([0.5, 1.8, 3.2, 4.5, 6.0]),  # % swelling
        700: np.array([1.2, 3.5, 5.8, 7.5, 9.2]),
        800: np.array([0.8, 2.5, 4.2, 5.8, 7.5])
    },
    'bubble_radius_data': {
        600: np.array([20, 35, 45, 52, 60]),  # nm
        700: np.array([25, 42, 55, 65, 75]),
        800: np.array([18, 30, 40, 48, 55])
    }
}

# U-19Pu-10Zr alloy validation data (Figure 7 in paper)
VALIDATION_DATA_U19PU10ZR = {
    'composition': 'U-19wt%Pu-10wt%Zr',
    'temperature_range': [650, 700, 750, 800],  # K
    'fission_rate': 2e20,  # fissions/m^3/s
    'burnup_points': np.array([1, 3, 5, 7, 10]),  # at.%
    'swelling_data': {
        650: np.array([0.3, 1.2, 2.5, 3.8, 5.2]),  # % swelling
        700: np.array([0.6, 2.0, 3.8, 5.5, 7.0]),
        750: np.array([0.8, 2.8, 4.8, 6.5, 8.2]),
        800: np.array([0.7, 2.3, 4.0, 5.8, 7.5])
    },
    'gas_release_fraction': {
        650: 0.05,  # ~5% gas release at 10 at.% burnup
        700: 0.08,
        750: 0.12,
        800: 0.15
    }
}

# High-purity uranium validation data (Figures 9-10 in paper)
VALIDATION_DATA_HIGH_PURITY_U = {
    'material': 'High-purity U',
    'temperature_range': [573, 673, 773, 873],  # K
    'fission_rate': 2e20,  # fissions/m^3/s
    'swelling_peak_temperature': 673,  # K (approximately)
    'peak_swelling': 12.0,  # % at peak temperature
    'activation_energy_swelling': 0.8,  # eV (approximate)
    'activation_energy_diffusion': 1.16  # eV
}


# ============================================================================
# Extreme Condition Test Cases
# ============================================================================

EXTREME_CONDITIONS = {
    'zero_fission_rate': {
        'fission_rate': 0.0,
        'expected_behavior': 'No swelling, no gas production',
        'expected_swelling': 0.0
    },
    'very_low_temperature': {
        'temperature': 100,  # K
        'expected_behavior': 'Very slow diffusion, minimal swelling',
        'expected_swelling_range': (0.0, 0.1)  # %
    },
    'very_high_temperature': {
        'temperature': 1500,  # K
        'expected_behavior': 'Rapid diffusion, significant gas release',
        'expected_gas_release': 0.5  # >50% release
    },
    'extremely_high_fission': {
        'fission_rate': 1e22,  # fissions/m^3/s
        'expected_behavior': 'Rapid gas production, high swelling',
        'expected_swelling_range': (10.0, 20.0)  # %
    },
    'zero_dislocation_density': {
        'dislocation_density': 0.0,  # m^-2
        'expected_behavior': 'Altered defect kinetics, changed swelling rate'
    },
    'very_high_dislocation_density': {
        'dislocation_density': 1e15,  # m^-2
        'expected_behavior': 'Enhanced defect absorption, modified swelling'
    },
    'zero_surface_energy': {
        'surface_energy': 0.0,  # J/m^2
        'expected_behavior': 'Unstable cavities (physical limit case)'
    },
    'very_high_surface_energy': {
        'surface_energy': 2.0,  # J/m^2
        'expected_behavior': 'Suppressed cavity growth, reduced swelling'
    }
}


# ============================================================================
# Physical Constants and Reference Values
# ============================================================================

PHYSICAL_CONSTANTS = {
    'boltzmann_constant_ev': 8.617e-5,  # eV/K
    'boltzmann_constant_j': 1.380649e-23,  # J/K
    'gas_constant': 8.314462618,  # J/(mol·K)
    'avogadro_constant': 6.02214076e23,  # mol^-1
    'atomic_volume_uranium': 4.09e-29,  # m^3
    'lattice_constant_uzr': 3.4808e-10,  # m
}

XENON_PROPERTIES = {
    'atomic_mass': 0.131293,  # kg/mol
    'atomic_radius': 2.16e-10,  # m
    'critical_temperature': 290.0,  # K
    'critical_density': 1.103e3,  # kg/m^3
    'critical_volume': 35.92e-6,  # m^3/mol
    'sigma': 3.86e-10,  # m (L-J collision diameter)
    'epsilon_k': 290.0  # K (L-J potential depth)
}

# Reference values for material parameters
MATERIAL_PARAMETER_RANGES = {
    'diffusion_coefficient': {
        'Dgb_600K': (1e-20, 1e-18),  # m^2/s at 600K
        'Dgb_800K': (1e-18, 1e-16),  # m^2/s at 800K
        'Dgf_multiplier': (100, 10000)  # Dgf/Dgb ratio
    },
    'dislocation_density': {
        'annealed': (1e12, 1e13),  # m^-2
        'cold_worked': (1e14, 1e15),  # m^-2
        'irradiated': (5e13, 5e14)  # m^-2
    },
    'surface_energy': {
        'uranium': (0.5, 1.0),  # J/m^2
        'uzr_alloy': (0.4, 0.8)  # J/m^2
    },
    'bias_factors': {
        'Zv': (0.9, 1.1),  # Vacancy bias
        'Zi': (1.01, 1.05)  # Interstitial bias
    }
}


# ============================================================================
# Test Configuration
# ============================================================================

TOLERANCE_CONFIG = {
    # ODE solver tolerances
    'solver': {
        'rtol': 1e-5,
        'atol': 1e-10
    },
    # Value comparison tolerances
    'values': {
        'rtol': 1e-3,
        'atol': 1e-10
    },
    # Swelling comparison tolerances (%)
    'swelling': {
        'rtol': 1e-2,  # 1% relative
        'atol': 0.1    # 0.1% absolute
    },
    # Pressure comparison tolerances
    'pressure': {
        'rtol': 1e-2,
        'atol': 1e5  # Pa
    },
    # Radius comparison tolerances
    'radius': {
        'rtol': 1e-2,
        'atol': 1e-10  # m
    },
    # Concentration comparison tolerances
    'concentration': {
        'rtol': 1e-3,
        'atol': 1e10  # atoms/m^3 or cavities/m^3
    }
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    'solve_time_100_days': {
        'target': 120,  # seconds
        'max_acceptable': 300  # seconds
    },
    'memory_usage_max': {
        'target': 500,  # MB
        'max_acceptable': 1000  # MB
    },
    'time_steps_total': {
        'typical_range': (1000, 100000)  # number of steps
    }
}


# ============================================================================
# Analytical Test Cases
# ============================================================================

# Simple test cases where analytical solutions are available
ANALYTICAL_TEST_CASES = {
    'no_fission_no_growth': {
        'description': 'With zero fission rate, state variables remain at initial values',
        'fission_rate': 0.0,
        'initial_state': np.zeros(10),
        'final_state': np.zeros(10),  # Should remain zero
        'time': 3600  # 1 hour
    },
    'steady_state_defects': {
        'description': 'At constant temperature and fission rate, defects approach steady state',
        'temperature': 600,  # K
        'fission_rate': 2e20,  # fissions/m^3/s
        'steady_state_time': 3600  # s (approximate time to reach steady state)
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_validation_data(material='U-10Zr', temperature=None):
    """
    Retrieve validation data for a specific material and temperature.

    Parameters
    ----------
    material : str
        Material composition ('U-10Zr', 'U-19Pu-10Zr', 'high-purity-U')
    temperature : float, optional
        Temperature in K. If None, returns all temperatures.

    Returns
    -------
    dict
        Validation data including swelling, bubble radius, gas release, etc.
    """
    if material == 'U-10Zr':
        data = VALIDATION_DATA_U10ZR.copy()
    elif material == 'U-19Pu-10Zr':
        data = VALIDATION_DATA_U19PU10ZR.copy()
    elif material == 'high-purity-U':
        data = VALIDATION_DATA_HIGH_PURITY_U.copy()
    else:
        raise ValueError(f"Unknown material: {material}")

    if temperature is not None and 'swelling_data' in data:
        if temperature in data['swelling_data']:
            data['swelling'] = data['swelling_data'][temperature]
            if 'bubble_radius_data' in data and temperature in data['bubble_radius_data']:
                data['bubble_radius'] = data['bubble_radius_data'][temperature]
        else:
            raise ValueError(f"Temperature {temperature}K not available for {material}")

    return data


def calculate_expected_swelling(temperature, burnup, material='U-10Zr'):
    """
    Calculate expected swelling based on empirical correlations.

    This is a simplified interpolation/extrapolation based on validation data.
    For actual research, use the full model simulation.

    Parameters
    ----------
    temperature : float
        Temperature in K
    burnup : float
        Burnup in at.%
    material : str
        Material composition

    Returns
    -------
    float
        Expected swelling in %
    """
    data = get_validation_data(material)

    # Simple linear interpolation in log-log space
    # This is a rough approximation - use the actual model for accurate results
    if material == 'U-10Zr':
        # Temperature-dependent scaling (peak around 700K)
        temp_factor = np.exp(-((temperature - 700) / 150) ** 2)
        # Burnup-dependent scaling
        burnup_factor = burnup ** 0.8
        return 9.2 * temp_factor * (burnup_factor / 10 ** 0.8)
    else:
        raise NotImplementedError(f"Swelling correlation not implemented for {material}")


def verify_physical_quantities(result):
    """
    Verify that calculated physical quantities are within reasonable bounds.

    Parameters
    ----------
    result : dict
        Simulation result dictionary from model.solve()

    Returns
    -------
    dict
        Dictionary with verification status for each quantity
    """
    verification = {}

    # Check swelling (should be between 0 and 100%)
    if 'swelling' in result:
        swelling = np.array(result['swelling'])
        verification['swelling'] = {
            'is_positive': np.all(swelling >= 0),
            'is_reasonable': np.all(swelling < 100),  # < 100%
            'is_monotonic': np.all(np.diff(swelling) >= -1e-6)  # Generally increasing
        }

    # Check cavity radius (should be between atomic scale and micron scale)
    if 'Rcb' in result:
        Rcb = np.array(result['Rcb'])
        verification['Rcb'] = {
            'is_positive': np.all(Rcb >= 0),
            'is_reasonable': np.all((Rcb >= 1e-12) & (Rcb < 1e-6))  # 1 pm to 1 μm
        }

    # Check gas pressure (should be positive)
    if 'Pg' in result:
        Pg = np.array(result['Pg'])
        verification['Pg'] = {
            'is_positive': np.all(Pg >= 0),
            'is_reasonable': np.all((Pg > 0) & (Pg < 1e10))  # Pa
        }

    return verification
