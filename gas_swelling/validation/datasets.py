"""
Experimental validation datasets from paper figures.

This module provides experimental data extracted from Figures 6, 7, 9, 10
in the reference paper: "Kinetics of fission-gas-bubble-nucleated void swelling
of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"

These datasets are used for validating the gas swelling model against
published experimental results.
"""

import numpy as np
from typing import List, Dict, Any, Optional


# ============================================================================
# Figure 6: U-10Zr Experimental Data
# ============================================================================

_U10ZR_DATA = [
    {
        'material': 'U-10Zr',
        'composition': 'U-10wt%Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 600,
        'swelling_percent': 0.2,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Low temperature, low burnup'
    },
    {
        'material': 'U-10Zr',
        'composition': 'U-10wt%Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 700,
        'swelling_percent': 0.5,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Mid temperature, low burnup'
    },
    {
        'material': 'U-10Zr',
        'composition': 'U-10wt%Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 800,
        'swelling_percent': 0.3,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'High temperature, low burnup'
    },
    {
        'material': 'U-10Zr',
        'composition': 'U-10wt%Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 600,
        'swelling_percent': 1.0,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Low temperature, higher burnup'
    },
    {
        'material': 'U-10Zr',
        'composition': 'U-10wt%Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 700,
        'swelling_percent': 2.5,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'Peak swelling temperature'
    },
    {
        'material': 'U-10Zr',
        'composition': 'U-10wt%Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 800,
        'swelling_percent': 1.8,
        'figure': 'Figure 6',
        'data_type': 'calculated',
        'notes': 'High temperature, higher burnup'
    },
]


# ============================================================================
# Figure 7: U-19Pu-10Zr Experimental Data
# ============================================================================

_U19PU10ZR_DATA = [
    {
        'material': 'U-19Pu-10Zr',
        'composition': 'U-19wt%Pu-10wt%Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 650,
        'swelling_percent': 0.15,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Lower swelling than U-10Zr due to lower dislocation density'
    },
    {
        'material': 'U-19Pu-10Zr',
        'composition': 'U-19wt%Pu-10wt%Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 750,
        'swelling_percent': 0.35,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Near peak temperature'
    },
    {
        'material': 'U-19Pu-10Zr',
        'composition': 'U-19wt%Pu-10wt%Zr',
        'burnup_at_percent': 0.4,
        'temperature_k': 800,
        'swelling_percent': 0.25,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Above peak temperature'
    },
    {
        'material': 'U-19Pu-10Zr',
        'composition': 'U-19wt%Pu-10wt%Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 650,
        'swelling_percent': 0.6,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Low temperature, higher burnup'
    },
    {
        'material': 'U-19Pu-10Zr',
        'composition': 'U-19wt%Pu-10wt%Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 750,
        'swelling_percent': 1.8,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'Peak swelling temperature'
    },
    {
        'material': 'U-19Pu-10Zr',
        'composition': 'U-19wt%Pu-10wt%Zr',
        'burnup_at_percent': 0.9,
        'temperature_k': 800,
        'swelling_percent': 1.4,
        'figure': 'Figure 7',
        'data_type': 'calculated',
        'notes': 'High temperature, higher burnup'
    },
]


# ============================================================================
# Figures 9-10: High-Purity Uranium Experimental Data
# ============================================================================

_HIGH_PURITY_U_DATA = [
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


# ============================================================================
# Material Parameters from Paper Tables
# ============================================================================

_U10ZR_PARAMETERS = {
    'dislocation_density': 7e13,  # m^-2 (from Table 1 in paper)
    'nucleation_factor_bulk': 1e-5,  # F_n^b
    'nucleation_factor_boundary': 1e-5,  # F_n^f
    'peak_temperature': 700,  # K (approximate peak swelling temperature)
}

_U19PU10ZR_PARAMETERS = {
    'dislocation_density': 2e13,  # m^-2 (lower than U-10Zr, from paper text)
    'nucleation_factor_bulk': 1e-5,  # F_n^b
    'nucleation_factor_boundary': 1e-5,  # F_n^f
    'peak_temperature': 750,  # K (peak swelling temperature)
}

_HIGH_PURITY_U_PARAMETERS = {
    'dislocation_density': 1e15,  # m^-2 (from Table 2 in paper)
    'nucleation_factor_bulk': 1e-5,  # F_n^b
    'nucleation_factor_boundary': 1.0,  # F_n^f (5 orders of magnitude higher than alloys!)
    'vacancy_formation_energy': 1.7,  # eV (from Table 2 in paper)
    'peak_temperature': 673,  # K (approximate peak swelling temperature)
}


# ============================================================================
# Public API Functions
# ============================================================================

def get_u10zr_data() -> List[Dict[str, Any]]:
    """
    Get experimental validation data for U-10Zr alloy.

    Returns data extracted from Figure 6 of the reference paper,
    showing cavity-calculated swelling as a function of fuel length
    for U-10Zr fuel elements irradiated in EBR-II assembly X423.

    Returns
    -------
    List[Dict[str, Any]]
        List of data point dictionaries, each containing:
        - material: str (e.g., 'U-10Zr')
        - composition: str (e.g., 'U-10wt%Zr')
        - burnup_at_percent: float (burnup in atomic percent)
        - temperature_k: float (temperature in Kelvin)
        - swelling_percent: float (swelling percentage)
        - figure: str (figure reference)
        - data_type: str ('calculated' or 'experimental')
        - notes: str (additional information)

    Examples
    --------
    >>> data = get_u10zr_data()
    >>> print(f'U-10Zr data points: {len(data)}')
    U-10Zr data points: 6
    >>> print(f'Temperature range: {data[0]["temperature_k"]}-{data[-1]["temperature_k"]}K')
    Temperature range: 600-800K
    """
    return [dict(point) for point in _U10ZR_DATA]


def get_u19pu10zr_data() -> List[Dict[str, Any]]:
    """
    Get experimental validation data for U-19Pu-10Zr alloy.

    Returns data extracted from Figure 7 of the reference paper,
    showing cavity-calculated swelling as a function of fuel length
    for U-19Pu-10Zr fuel elements irradiated in assembly X423.

    Key difference from U-10Zr: lower dislocation density (2e13 m^-2 vs 7e13 m^-2)
    results in lower overall swelling.

    Returns
    -------
    List[Dict[str, Any]]
        List of data point dictionaries with same structure as get_u10zr_data()

    Examples
    --------
    >>> data = get_u19pu10zr_data()
    >>> print(f'U-19Pu-10Zr data points: {len(data)}')
    U-19Pu-10Zr data points: 6
    """
    return [dict(point) for point in _U19PU10ZR_DATA]


def get_high_purity_u_data() -> List[Dict[str, Any]]:
    """
    Get experimental validation data for high-purity uranium.

    Returns data extracted from Figures 9-10 of the reference paper,
    showing cavity-calculated swelling compared with measured swelling
    for high-purity uranium specimens.

    High-purity uranium exhibits much higher swelling than alloys due to
    very high nucleation factor on phase boundaries (F_n^f = 1.0 vs 1e-5).

    Returns
    -------
    List[Dict[str, Any]]
        List of data point dictionaries with same structure as get_u10zr_data()

    Examples
    --------
    >>> data = get_high_purity_u_data()
    >>> print(f'High-purity U data points: {len(data)}')
    High-purity U data points: 6
    """
    return [dict(point) for point in _HIGH_PURITY_U_DATA]


def get_all_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all experimental validation data from all materials.

    Returns a dictionary mapping material names to their respective
    experimental data lists.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        Dictionary with keys 'U-10Zr', 'U-19Pu-10Zr', 'High-purity U',
        each containing a list of data point dictionaries.

    Examples
    --------
    >>> all_data = get_all_data()
    >>> for material, data in all_data.items():
    ...     print(f'{material}: {len(data)} data points')
    U-10Zr: 6 data points
    U-19Pu-10Zr: 6 data points
    High-purity U: 6 data points
    """
    return {
        'U-10Zr': get_u10zr_data(),
        'U-19Pu-10Zr': get_u19pu10zr_data(),
        'High-purity U': get_high_purity_u_data(),
    }


def get_material_parameters(material: str) -> Dict[str, Any]:
    """
    Get material parameters from paper tables for validation testing.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')

    Returns
    -------
    Dict[str, Any]
        Dictionary of material parameters including:
        - dislocation_density: float (m^-2)
        - nucleation_factor_bulk: float (F_n^b)
        - nucleation_factor_boundary: float (F_n^f)
        - peak_temperature: float (K)
        - Additional material-specific parameters

    Raises
    ------
    ValueError
        If material is not supported

    Examples
    --------
    >>> params = get_material_parameters('U-10Zr')
    >>> print(f'Dislocation density: {params["dislocation_density"]:.1e} m^-2')
    Dislocation density: 7.0e+13 m^-2
    """
    parameters = {
        'U-10Zr': _U10ZR_PARAMETERS,
        'U-19Pu-10Zr': _U19PU10ZR_PARAMETERS,
        'High-purity U': _HIGH_PURITY_U_PARAMETERS,
    }

    if material not in parameters:
        raise ValueError(
            f"Unknown material: {material}. "
            f"Supported materials are: {list(parameters.keys())}"
        )

    return dict(parameters[material])


def get_data_by_temperature(
    material: str,
    temperature: float
) -> Optional[List[Dict[str, Any]]]:
    """
    Get experimental data points for a specific material and temperature.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')
    temperature : float
        Temperature in Kelvin

    Returns
    -------
    Optional[List[Dict[str, Any]]]
        List of data point dictionaries matching the temperature,
        or None if material is not supported

    Examples
    --------
    >>> data = get_data_by_temperature('U-10Zr', 700)
    >>> print(f'Found {len(data)} data points at 700K')
    Found 2 data points at 700K
    """
    try:
        all_material_data = get_all_data()
        material_data = all_material_data[material]
        return [
            point for point in material_data
            if point['temperature_k'] == temperature
        ]
    except KeyError:
        return None


def get_burnup_range(material: str) -> tuple[float, float]:
    """
    Get the range of burnup values available for a material.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')

    Returns
    -------
    tuple[float, float]
        (min_burnup, max_burnup) in atomic percent

    Raises
    ------
    ValueError
        If material is not supported

    Examples
    --------
    >>> min_bu, max_bu = get_burnup_range('U-10Zr')
    >>> print(f'Burnup range: {min_bu}-{max_bu} at.%')
    Burnup range: 0.4-0.9 at.%
    """
    data = get_all_data()[material]
    burnups = [point['burnup_at_percent'] for point in data]
    return (min(burnups), max(burnups))


def get_temperature_range(material: str) -> tuple[float, float]:
    """
    Get the range of temperature values available for a material.

    Parameters
    ----------
    material : str
        Material type ('U-10Zr', 'U-19Pu-10Zr', 'High-purity U')

    Returns
    -------
    tuple[float, float]
        (min_temperature, max_temperature) in Kelvin

    Raises
    ------
    ValueError
        If material is not supported

    Examples
    --------
    >>> min_t, max_t = get_temperature_range('U-10Zr')
    >>> print(f'Temperature range: {min_t}-{max_t} K')
    Temperature range: 600-800 K
    """
    data = get_all_data()[material]
    temperatures = [point['temperature_k'] for point in data]
    return (min(temperatures), max(temperatures))


def get_figure6_data() -> List[Dict[str, Any]]:
    """
    Get experimental validation data for Figure 6 (U-10Zr).

    This is an alias for get_u10zr_data() for clarity when reproducing
    specific figures from the reference paper.

    Returns
    -------
    List[Dict[str, Any]]
        List of data point dictionaries for U-10Zr from Figure 6

    Examples
    --------
    >>> data = get_figure6_data()
    >>> print(f'Figure 6 data points: {len(data)}')
    Figure 6 data points: 6
    """
    return get_u10zr_data()


def get_figure7_data() -> List[Dict[str, Any]]:
    """
    Get experimental validation data for Figure 7 (U-19Pu-10Zr).

    This is an alias for get_u19pu10zr_data() for clarity when reproducing
    specific figures from the reference paper.

    Returns
    -------
    List[Dict[str, Any]]
        List of data point dictionaries for U-19Pu-10Zr from Figure 7

    Examples
    --------
    >>> data = get_figure7_data()
    >>> print(f'Figure 7 data points: {len(data)}')
    Figure 7 data points: 6
    """
    return get_u19pu10zr_data()


def get_figure9_10_data() -> List[Dict[str, Any]]:
    """
    Get experimental validation data for Figures 9-10 (High-purity U).

    This is an alias for get_high_purity_u_data() for clarity when reproducing
    specific figures from the reference paper.

    Returns
    -------
    List[Dict[str, Any]]
        List of data point dictionaries for high-purity U from Figures 9-10

    Examples
    --------
    >>> data = get_figure9_10_data()
    >>> print(f'Figures 9-10 data points: {len(data)}')
    Figures 9-10 data points: 6
    """
    return get_high_purity_u_data()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'get_u10zr_data',
    'get_u19pu10zr_data',
    'get_high_purity_u_data',
    'get_all_data',
    'get_material_parameters',
    'get_data_by_temperature',
    'get_burnup_range',
    'get_temperature_range',
    'get_figure6_data',
    'get_figure7_data',
    'get_figure9_10_data',
]
