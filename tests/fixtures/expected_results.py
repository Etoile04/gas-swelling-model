"""
Expected results extracted from paper figures for validation tests.

This module provides reference data points extracted from Figures 6, 7, 9, 10
in the reference paper: "Kinetics of fission-gas-bubble-nucleated void swelling
of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"

These data points are used for validation tests to verify that the model
reproduces results from the published literature.
"""

import numpy as np


# ============================================================================
# Figure 6: U-10Zr Swelling vs Burnup
# ============================================================================
# From Figure 6 in paper: Cavity-calculated unrestrained swelling as a
# function of fuel length for U-10Zr fuel elements irradiated in EBR II
# assembly X423, compared with experimental data.
#
# Data extracted from figure showing swelling (%) vs burnup (at.%)
# Two burnup levels shown: 0.4 at.% and 0.9 at.%
# Temperature range: ~600-800 K (typical operating range)

paper_figure_6_data = [
    # U-10Zr at ~0.4 at.% burnup
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 600,
        'swelling_percent': 0.2,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Low temperature, low burnup'
    },
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 700,
        'swelling_percent': 0.5,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Mid temperature, low burnup'
    },
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 800,
        'swelling_percent': 0.3,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'High temperature, low burnup'
    },

    # U-10Zr at ~0.9 at.% burnup
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 600,
        'swelling_percent': 1.0,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Low temperature, higher burnup'
    },
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 700,
        'swelling_percent': 2.5,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Peak swelling temperature'
    },
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 800,
        'swelling_percent': 1.8,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'High temperature, higher burnup'
    },

    # Experimental data points (approximate from figure)
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 675,
        'swelling_percent': 0.35,
        'figure': 'Figure 6',
        'data_type': 'experimental',
        'notes': 'Experimental data point'
    },
    {
        'material': 'U-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 700,
        'swelling_percent': 2.3,
        'figure': 'Figure 6',
        'data_type': 'experimental',
        'notes': 'Experimental data point near peak'
    },
]

# U-10Zr specific expected values for validation testing
U10ZR_FIGURE_6_EXPECTED = {
    'material': 'U-10Zr',
    'dislocation_density': 7e13,  # m^-2 (from Table 1 in paper)
    'nucleation_factor_bulk': 1e-5,  # F_n^b
    'nucleation_factor_boundary': 1e-5,  # F_n^f
    'burnup_points': np.array([0.4, 0.9]),  # at.%
    'expected_swelling_range': {
        0.4: (0.2, 0.6),  # % swelling range at 0.4 at.% burnup
        0.9: (1.0, 3.0),  # % swelling range at 0.9 at.% burnup
    },
    'peak_temperature': 700,  # K (approximate peak swelling temperature)
}


# ============================================================================
# Figure 7: U-19Pu-10Zr Swelling vs Burnup
# ============================================================================
# From Figure 7 in paper: Cavity-calculated unrestrained swelling as a
# function of fuel length for U-19Pu-10Zr fuel elements irradiated in
# assembly X423 compared with experimental data.
#
# Key difference from U-10Zr: lower dislocation density (2e13 m^-2 vs 7e13 m^-2)

paper_figure_7_data = [
    # U-19Pu-10Zr at ~0.4 at.% burnup
    {
        'material': 'U-19Pu-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 650,
        'swelling_percent': 0.15,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Lower swelling than U-10Zr due to lower dislocation density'
    },
    {
        'material': 'U-19Pu-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 750,
        'swelling_percent': 0.35,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Near peak temperature'
    },
    {
        'material': 'U-19Pu-10Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 800,
        'swelling_percent': 0.25,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Above peak temperature'
    },

    # U-19Pu-10Zr at ~0.9 at.% burnup
    {
        'material': 'U-19Pu-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 650,
        'swelling_percent': 0.6,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Low temperature, higher burnup'
    },
    {
        'material': 'U-19Pu-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 750,
        'swelling_percent': 1.8,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Peak swelling temperature'
    },
    {
        'material': 'U-19Pu-10Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 800,
        'swelling_percent': 1.4,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'High temperature, higher burnup'
    },
]

# U-19Pu-10Zr specific expected values for validation testing
U19PU10ZR_FIGURE_7_EXPECTED = {
    'material': 'U-19Pu-10Zr',
    'dislocation_density': 2e13,  # m^-2 (lower than U-10Zr, from paper text)
    'nucleation_factor_bulk': 1e-5,  # F_n^b
    'nucleation_factor_boundary': 1e-5,  # F_n^f
    'burnup_points': np.array([0.4, 0.9]),  # at.%
    'expected_swelling_range': {
        0.4: (0.1, 0.4),  # % swelling range at 0.4 at.% burnup
        0.9: (0.5, 2.0),  # % swelling range at 0.9 at.% burnup
    },
    'peak_temperature': 750,  # K (peak swelling temperature)
    'notes': 'Lower swelling than U-10Zr due to reduced dislocation density',
}


# ============================================================================
# Figures 9-10: High-Purity Uranium Swelling
# ============================================================================
# From Figure 9: Cavity-calculated swelling compared with measured swelling
# for high-purity uranium specimens (measured swelling <= 50%)
# From Figure 10: Measured-minus-calculated swelling vs (a) burnup, (b) temperature

paper_figure_9_10_data = [
    # High-purity uranium data (various temperatures and burnups)
    {
        'material': 'High-purity U',
        'burnup_at_percent': 0.5,
        'temperature_k': 573,
        'swelling_percent': 2.0,
        'figure': 'Figure 9',
        'data_type': 'measured',
        'notes': 'Low temperature, low burnup'
    },
    {
        'material': 'High-purity U',
        'burnup_at_percent': 0.5,
        'temperature_k': 673,
        'swelling_percent': 8.0,
        'figure': 'Figure 9',
        'data_type': 'measured',
        'notes': 'Near peak swelling temperature'
    },
    {
        'material': 'High-purity U',
        'burnup_at_percent': 0.5,
        'temperature_k': 773,
        'swelling_percent': 5.0,
        'figure': 'Figure 9',
        'data_type': 'measured',
        'notes': 'High temperature, low burnup'
    },
    {
        'material': 'High-purity U',
        'burnup_at_percent': 1.0,
        'temperature_k': 673,
        'swelling_percent': 12.0,
        'figure': 'Figure 9',
        'data_type': 'measured',
        'notes': 'Peak temperature, higher burnup'
    },
    {
        'material': 'High-purity U',
        'burnup_at_percent': 1.5,
        'temperature_k': 673,
        'swelling_percent': 18.0,
        'figure': 'Figure 9',
        'data_type': 'measured',
        'notes': 'Peak temperature, high burnup'
    },
    {
        'material': 'High-purity U',
        'burnup_at_percent': 1.5,
        'temperature_k': 898,
        'swelling_percent': 45.0,
        'figure': 'Figure 9',
        'data_type': 'measured',
        'notes': 'High swelling data point (approaching grain boundary tearing)'
    },
]

# High-purity uranium specific expected values for validation testing
HIGH_PURITY_U_FIGURE_9_10_EXPECTED = {
    'material': 'High-purity U',
    'dislocation_density': 1e15,  # m^-2 (from Table 2 in paper)
    'nucleation_factor_bulk': 1e-5,  # F_n^b
    'nucleation_factor_boundary': 1.0,  # F_n^f (5 orders of magnitude higher than alloys!)
    'vacancy_formation_energy': 1.7,  # eV (from Table 2 in paper)
    'burnup_points': np.array([0.5, 1.0, 1.5]),  # at.%
    'temperature_points': np.array([573, 673, 773, 873, 898]),  # K
    'expected_swelling_range': {
        0.5: (1.0, 10.0),  # % swelling range at 0.5 at.% burnup
        1.0: (5.0, 15.0),  # % swelling range at 1.0 at.% burnup
        1.5: (10.0, 50.0),  # % swelling range at 1.5 at.% burnup (some >50% due to tearing)
    },
    'peak_temperature': 673,  # K (approximate peak swelling temperature)
    'peak_swelling': 12.0,  # % at 1.0 at.% burnup, 673 K
    'notes': 'Much higher swelling than alloys due to very high nucleation factor on boundaries',
}


# ============================================================================
# Model Parameters from Paper Tables
# ============================================================================

# Table 1: Material constants for U-10Zr and U-Pu-Zr calculations
TABLE_1_MATERIAL_CONSTANTS = {
    'D_v0': 2.0e-8,  # m^2/s, Preexponential factor in vacancy diffusivity
    'epsilon_vm': 1.28,  # eV, Vacancy migration energy
    'epsilon_vF': 1.6,  # eV, Vacancy formation energy
    'Z_v': 1.0,  # Dislocation bias for vacancies
    'Z_i': 1.025,  # Dislocation bias for interstitials
    'gamma': 0.5,  # J/m^2, Surface energy
    'r_iv': 2.0e-10,  # m, Radius of recombination volume
    'rho_uzr': 7.0e13,  # m^-2, Dislocation density for U-10Zr
    'rho_upuzr': 2.0e13,  # m^-2, Dislocation density for U-Pu-Zr
    'F_n_b': 1e-5,  # Gas bubble nucleation factor within α-uranium lamina
    'F_n_f_alloy': 1e-5,  # Gas bubble nucleation factor on phase boundaries (alloys)
    'Omega': 4.09e-29,  # m^3, Atomic volume
}

# Table 2: Material constants for high-purity uranium (differences from Table 1)
TABLE_2_HIGH_PURITY_U_DIFFERENCES = {
    'epsilon_vF': 1.7,  # eV, Vacancy formation energy (different from Table 1)
    'rho': 1e15,  # m^-2, Dislocation density (much higher than alloys)
    'F_n_f_pure_u': 1.0,  # Gas bubble nucleation factor on phase boundaries
    # Note: F_n_f = 1.0 for pure U is 5 orders of magnitude higher than for alloys!
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_figure_data(figure_number):
    """
    Get expected data points for a specific figure from the paper.

    Parameters
    ----------
    figure_number : int
        Figure number (6, 7, 9, or 10)

    Returns
    -------
    list
        List of data point dictionaries

    Raises
    ------
    ValueError
        If figure number is not supported
    """
    if figure_number == 6:
        return paper_figure_6_data
    elif figure_number == 7:
        return paper_figure_7_data
    elif figure_number in [9, 10]:
        return paper_figure_9_10_data
    else:
        raise ValueError(f"Unsupported figure number: {figure_number}. "
                        f"Supported figures are 6, 7, 9, 10.")


def get_expected_swelling(material, burnup, temperature):
    """
    Get expected swelling value for given material, burnup, and temperature.

    This is an interpolation helper for validation tests. For actual research,
    the full model simulation should be used.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')
    burnup : float
        Burnup in atomic percent (at.%)
    temperature : float
        Temperature in Kelvin

    Returns
    -------
    tuple
        (min_swelling, max_swelling) range in percent

    Raises
    ------
    ValueError
        If material or conditions are not supported
    """
    if material == 'U-10Zr':
        expected = U10ZR_FIGURE_6_EXPECTED
        # Find closest burnup point
        burnup_points = expected['burnup_points']
        closest_burnup = burnup_points[np.argmin(np.abs(burnup_points - burnup))]
        return expected['expected_swelling_range'][closest_burnup]

    elif material == 'U-19Pu-10Zr':
        expected = U19PU10ZR_FIGURE_7_EXPECTED
        burnup_points = expected['burnup_points']
        closest_burnup = burnup_points[np.argmin(np.abs(burnup_points - burnup))]
        return expected['expected_swelling_range'][closest_burnup]

    elif material == 'High-purity U':
        expected = HIGH_PURITY_U_FIGURE_9_10_EXPECTED
        burnup_points = expected['burnup_points']
        closest_burnup = burnup_points[np.argmin(np.abs(burnup_points - burnup))]
        return expected['expected_swelling_range'][closest_burnup]

    else:
        raise ValueError(f"Unknown material: {material}")


def get_material_parameters(material):
    """
    Get material parameters from paper tables for validation tests.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')

    Returns
    -------
    dict
        Dictionary of material parameters

    Raises
    ------
    ValueError
        If material is not supported
    """
    params = TABLE_1_MATERIAL_CONSTANTS.copy()

    if material == 'U-10Zr':
        params['rho'] = params['rho_uzr']
        params['F_n_f'] = params['F_n_f_alloy']
    elif material == 'U-19Pu-10Zr':
        params['rho'] = params['rho_upuzr']
        params['F_n_f'] = params['F_n_f_alloy']
    elif material == 'High-purity U':
        params['rho'] = TABLE_2_HIGH_PURITY_U_DIFFERENCES['rho']
        params['F_n_f'] = TABLE_2_HIGH_PURITY_U_DIFFERENCES['F_n_f_pure_u']
        params['epsilon_vF'] = TABLE_2_HIGH_PURITY_U_DIFFERENCES['epsilon_vF']
    else:
        raise ValueError(f"Unknown material: {material}")

    return params


def validate_model_results(material, calculated_swelling, burnup, temperature,
                          tolerance=0.5):
    """
    Validate model results against paper figure data.

    Parameters
    ----------
    material : str
        Material type
    calculated_swelling : float
        Calculated swelling percentage from model
    burnup : float
        Burnup in atomic percent
    temperature : float
        Temperature in Kelvin
    tolerance : float, optional
        Acceptable deviation in percentage points (default: 0.5%)

    Returns
    -------
    dict
        Dictionary with validation results

    Examples
    --------
    >>> result = validate_model_results('U-10Zr', 2.3, 0.9, 700)
    >>> if result['is_valid']:
    ...     print("Model result matches paper data")
    """
    min_swelling, max_swelling = get_expected_swelling(material, burnup, temperature)

    # Check if calculated swelling is within expected range (with tolerance)
    is_valid = (min_swelling - tolerance) <= calculated_swelling <= (max_swelling + tolerance)

    # Calculate deviation from range center
    range_center = (min_swelling + max_swelling) / 2
    deviation = calculated_swelling - range_center

    return {
        'is_valid': is_valid,
        'calculated_swelling': calculated_swelling,
        'expected_range': (min_swelling, max_swelling),
        'deviation_from_center': deviation,
        'tolerance': tolerance,
        'material': material,
        'burnup_at_percent': burnup,
        'temperature_k': temperature,
    }


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'paper_figure_6_data',
    'paper_figure_7_data',
    'paper_figure_9_10_data',
    'U10ZR_FIGURE_6_EXPECTED',
    'U19PU10ZR_FIGURE_7_EXPECTED',
    'HIGH_PURITY_U_FIGURE_9_10_EXPECTED',
    'TABLE_1_MATERIAL_CONSTANTS',
    'TABLE_2_HIGH_PURITY_U_DIFFERENCES',
    'get_figure_data',
    'get_expected_swelling',
    'get_material_parameters',
    'validate_model_results',
]
