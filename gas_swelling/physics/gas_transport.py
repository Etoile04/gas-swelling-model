"""
气体输运与释放计算模块 (Gas Transport and Release Calculation Module)

This module provides calculations for gas transport and release in nuclear fuel materials,
including gas diffusion, release rate, and bubble interconnectivity.
Based on the theoretical framework from rate theory of fission gas behavior.
References: Eqs. 1-12 in the swelling rate theory paper.
"""

import numpy as np
from typing import Dict, Tuple

# Physical constants (物理常数)
ATOMIC_VOLUME = 4.09e-29  # m³, atomic volume (原子体积)


def calculate_gas_influx(
    Cgb: float,
    Cgf: float,
    grain_diameter: float,
    Dgb: float
) -> float:
    """
    计算从基体扩散到相界面的气体原子通量 (公式2)

    Calculate gas atom flux from bulk matrix to phase boundaries due to diffusion gradient.
    This represents the transport of gas atoms from the grain interior (bulk) to grain boundaries.

    Parameters
    ----------
    Cgb : float
        Gas atom concentration in bulk matrix (atoms/m³)
    Cgf : float
        Gas atom concentration at phase boundaries (atoms/m³)
    grain_diameter : float
        Grain diameter (m)
    Dgb : float
        Gas diffusion coefficient in bulk (m²/s)

    Returns
    -------
    float
        Gas influx rate from bulk to phase boundaries (atoms/m³/s)

    Notes
    -----
    Formula: g0 = (12.0 / grain_diameter²) × Dgb × (Cgb - Cgf)

    The flux is driven by the concentration gradient between bulk and boundary gas concentrations.
    Grain size influences the diffusion path length - smaller grains have larger surface-to-volume
    ratios, leading to faster gas transport to boundaries.

    References
    ----------
    Eq. 2 in the rate theory paper
    """
    if grain_diameter <= 0:
        raise ValueError("grain_diameter must be positive")

    influx = (12.0 / grain_diameter**2) * Dgb * (Cgb - Cgf)
    return influx


def calculate_gas_release_rate(
    Cgf: float,
    Ccf: float,
    Rcf: float,
    Ncf: float,
    grain_diameter: float
) -> float:
    """
    计算气体释放率 (公式9-12)

    Calculate the rate of gas release from interconnected bubbles at grain boundaries.
    Gas release occurs when bubble coverage on grain faces reaches a critical threshold
    for interconnection (tunnel formation).

    Parameters
    ----------
    Cgf : float
        Gas atom concentration at phase boundaries (atoms/m³)
    Ccf : float
        Cavity/bubble concentration at phase boundaries (cavities/m³)
    Rcf : float
        Radius of boundary cavities (m)
    Ncf : float
        Gas atoms per boundary cavity (atoms/cavity)
    grain_diameter : float
        Grain diameter (m)

    Returns
    -------
    float
        Gas release rate coefficient h0 (1/s), where the actual release rate is h0 × Cgf

    Notes
    -----
    The gas release mechanism involves several steps:

    1. **Bubble Coverage Area (Eq. 10)**:
       Af = π × Rcf² × Ccf × ff_θ
       where ff_θ is the geometric factor for spherical cap bubbles

    2. **Maximum Coverage (Eq. 11)**:
       Af_max = 0.907 × Sv_aa
       where Sv_aa = 6 / grain_diameter is the grain-face area per unit volume

    3. **Interconnectivity Coefficient (Eq. 12)**:
       - χ = 0.0 when Af_ratio ≤ 0.25 (no release)
       - χ = Af_ratio when 0.25 < Af_ratio < 1.0 (partial release)
       - χ = 1.0 when Af_ratio ≥ 1.0 (full release)

    4. **Release Rate**:
       h0 = χ × (Cgf + Ccf × Ncf)

    The geometric factor ff_θ accounts for bubble shape at grain boundaries:
    - θ = 50° (typical dihedral angle for U-Zr alloys)
    - ff_θ = 1 - 1.5×cos(θ) + 0.5×cos(θ)³

    References
    ----------
    Eqs. 9-12 in the rate theory paper
    White and Tucker, JNM 118 (1983) for grain boundary gas release models

    Examples
    --------
    >>> Cgf = 1e25  # atoms/m³
    >>> Ccf = 1e20  # cavities/m³
    >>> Rcf = 1e-7  # m
    >>> Ncf = 1000  # atoms/cavity
    >>> grain_diameter = 5e-7  # m
    >>> h0 = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)
    """
    if grain_diameter <= 0:
        raise ValueError("grain_diameter must be positive")
    # Clip negative values to zero for intermediate ODE states
    Rcf = max(0.0, Rcf)
    Ccf = max(0.0, Ccf)
    Ncf = max(0.0, Ncf)
    Cgf = max(0.0, Cgf)

    # Geometric factor for spherical cap bubbles at grain boundaries
    # 晶界球冠状气泡的几何因子
    # θ = 50° is the typical dihedral angle for U-Zr alloys
    # θ = 50° 是U-Zr合金的典型二面角
    theta = 50.0 / 180.0 * np.pi  # Convert to radians (转换为弧度)
    ff_theta = 1.0 - 1.5 * np.cos(theta) + 0.5 * np.cos(theta)**3

    # Bubble coverage area on grain faces (Eq. 10)
    # 晶面上的气泡覆盖面积 (公式10)
    Af = np.pi * Rcf**2 * Ccf * ff_theta  # m⁻¹

    # Grain-face area per unit volume (m⁻¹)
    # 单位体积的晶界面积 (m⁻¹)
    Sv_aa = 6.0 / grain_diameter

    # Maximum bubble coverage for interconnection (Eq. 11)
    # 发生连通时的最大气泡覆盖 (公式11)
    Af_max = 0.907 * Sv_aa

    # Calculate coverage ratio (计算覆盖比)
    if Af_max <= 0:
        Af_ratio = 0.0
    else:
        Af_ratio = Af / Af_max

    # Calculate interconnectivity coefficient (Eq. 12)
    # 计算连通性系数 (公式12)
    if Af_ratio <= 0.25:
        # No gas release - bubbles are isolated
        # 无气体释放 - 气泡孤立
        chi = 0.0
    elif Af_ratio >= 1.0:
        # Full gas release - complete interconnection
        # 完全气体释放 - 完全连通
        chi = 1.0
    else:
        # Partial release - linear transition region
        # 部分释放 - 线性过渡区
        chi = Af_ratio

    # Calculate gas release rate coefficient
    # h0 represents the fraction of gas released per unit time
    # 计算气体释放率系数
    # h0 表示单位时间内释放的气体分数
    h0 = chi * (Cgf + Ccf * Ncf)

    return h0


def calculate_nucleation_rate(
    Cg: float,
    Dg: float,
    Fn: float,
    Xe_radii: float
) -> float:
    """
    计算气泡成核速率

    Calculate the nucleation rate of gas bubbles in the material.
    Bubble nucleation occurs when gas atoms cluster to form stable embryos.

    Parameters
    ----------
    Cg : float
        Gas atom concentration (atoms/m³)
    Dg : float
        Gas diffusion coefficient (m²/s)
    Fn : float
        Bubble nucleation factor (dimensionless)
        - Typical values: 1e-5 for both bulk and boundary nucleation
    Xe_radii : float
        Xenon atom radius (m)

    Returns
    -------
    float
        Nucleation rate (nucleation events/m³/s)

    Notes
    -----
    The nucleation rate is proportional to:
    - Gas concentration squared (Cg²) - representing two gas atoms meeting
    - Diffusion coefficient (Dg) - controlling atom mobility
    - Nucleation factor (Fn) - material-specific parameter
    - Atomic size (Xe_radii) - related to critical nucleus size

    Formula: J = 16π × Fn × Xe_radii × Dg × Cg²

    This is used in both bulk (Eq. 1 term1) and boundary (Eq. 6 term1) gas balance equations.

    References
    ----------
    Eqs. 1 and 6 in the rate theory paper
    Gruber's classical nucleation theory for fission gas bubbles
    """
    # Clip negative values to zero for intermediate ODE states
    Cg = max(0.0, Cg)
    Dg = max(0.0, Dg)
    Fn = max(0.0, Fn)
    Xe_radii = max(0.0, Xe_radii)

    nucleation_rate = 16.0 * np.pi * Fn * Xe_radii * Dg * Cg**2
    return nucleation_rate


def calculate_gas_absorption_rate(
    Cg: float,
    Cc: float,
    Rc: float,
    Dg: float
) -> float:
    """
    计算气泡对气体原子的吸收速率

    Calculate the rate at which existing bubbles absorb gas atoms from the surrounding matrix.

    Parameters
    ----------
    Cg : float
        Gas atom concentration in matrix (atoms/m³)
    Cc : float
        Cavity/bubble concentration (cavities/m³)
    Rc : float
        Cavity radius (m)
    Dg : float
        Gas diffusion coefficient (m²/s)

    Returns
    -------
    float
        Gas absorption rate (atoms/m³/s)

    Notes
    -----
    The absorption rate is driven by diffusion of gas atoms to bubble surfaces:
    - Each bubble acts as a sink with absorption rate ~ 4πRc×Dg×Cg
    - Total absorption = absorption per bubble × bubble concentration

    Formula: Rate = 4π × Rc × Dg × Cg × Cc

    This appears in:
    - Bulk gas balance (Eq. 1 term2): absorption by bulk bubbles
    - Boundary gas balance (Eq. 6 term2): absorption by boundary bubbles

    References
    ----------
    Eqs. 1 and 6 in the rate theory paper
    """
    # Clip negative values to zero for intermediate ODE states
    Cg = max(0.0, Cg)
    Cc = max(0.0, Cc)
    Rc = max(0.0, Rc)
    Dg = max(0.0, Dg)

    absorption_rate = 4.0 * np.pi * Rc * Dg * Cg * Cc
    return absorption_rate


def calculate_gas_resolution_rate(
    Cc: float,
    Nc: float,
    resolution_rate: float
) -> float:
    """
    计算气泡气体原子重溶速率

    Calculate the rate at which fission fragments knock gas atoms out of bubbles back into solution.
    This is the reverse process of gas absorption into bubbles.

    Parameters
    ----------
    Cc : float
        Cavity/bubble concentration (cavities/m³)
    Nc : float
        Gas atoms per cavity (atoms/cavity)
    resolution_rate : float
        Fission resolution rate (s⁻¹)
        - Typical value: 2e-5 s⁻¹

    Returns
    -------
    float
        Gas resolution rate (atoms/m³/s)

    Notes
    -----
    Fission fragments passing through bubbles can knock gas atoms back into the matrix.
    The rate is proportional to:
    - Number of bubbles (Cc)
    - Gas atoms in each bubble (Nc)
    - Fission rate (implicitly in resolution_rate parameter)

    Formula: Rate = resolution_rate × Cc × Nc

    This appears in the bulk gas balance (Eq. 1 term5) as a source term.

    The resolution rate parameter accounts for:
    - Fission rate density
    - Cross-section for fission fragment-bubble interactions
    - Energy transfer efficiency

    References
    ----------
    Eq. 1 in the rate theory paper
    Rest and Zawadzki, JNM 160 (1989) for fission gas resolution models
    """
    # Clip negative values to zero for intermediate ODE states
    Cc = max(0.0, Cc)
    Nc = max(0.0, Nc)
    resolution_rate = max(0.0, resolution_rate)

    resolution = resolution_rate * Cc * Nc
    return resolution


def calculate_gas_production_rate(
    fission_rate: float,
    gas_yield: float = 0.25
) -> float:
    """
    计算裂变气体产生速率

    Calculate the production rate of fission gas atoms (Xe, Kr) from fission reactions.

    Parameters
    ----------
    fission_rate : float
        Fission rate density (fissions/m³/s)
    gas_yield : float, optional
        Fission gas yield per fission (atoms/fission), default 0.25
        - Typical value: 0.25 for U-Pu-Zr alloys
        - Represents combined yield of Xe and Kr

    Returns
    -------
    float
        Gas production rate (atoms/m³/s)

    Notes
    -----
    Each fission event produces approximately 0.25 atoms of fission gas (Xe + Kr).
    The production rate is:
    - Proportional to fission rate
    - Independent of temperature
    - Constant throughout irradiation (for constant fission rate)

    Formula: Rate = gas_yield × fission_rate

    This appears as a source term in both bulk (Eq. 1 term4) and boundary
    gas balance equations after gas atoms diffuse to boundaries.

    References
    ----------
    Eq. 1 in the rate theory paper
    Typical fission gas yields from nuclear data tables
    """
    # Clip negative values to zero for intermediate ODE states
    fission_rate = max(0.0, fission_rate)
    gas_yield = max(0.0, gas_yield)

    production = gas_yield * fission_rate
    return production


# Convenience function combining all gas transport terms
def calculate_gas_transport_terms(
    Cgb: float,
    Cgf: float,
    Ccb: float,
    Ccf: float,
    Rcb: float,
    Rcf: float,
    Ncb: float,
    Ncf: float,
    params: Dict
) -> Dict[str, float]:
    """
    计算所有气体输运项的便捷函数

    Convenience function that calculates all gas transport terms for a given state.
    Useful for debugging and understanding the contributions of different processes.

    Parameters
    ----------
    Cgb : float
        Gas atom concentration in bulk (atoms/m³)
    Cgf : float
        Gas atom concentration at boundaries (atoms/m³)
    Ccb : float
        Bulk cavity concentration (cavities/m³)
    Ccf : float
        Boundary cavity concentration (cavities/m³)
    Rcb : float
        Bulk cavity radius (m)
    Rcf : float
        Boundary cavity radius (m)
    Ncb : float
        Gas atoms per bulk cavity (atoms/cavity)
    Ncf : float
        Gas atoms per boundary cavity (atoms/cavity)
    params : dict
        Dictionary of material and simulation parameters containing:
        - grain_diameter: Grain size (m)
        - Dgb: Bulk gas diffusion coefficient (m²/s)
        - Dgf: Boundary gas diffusion coefficient (m²/s)
        - Fnb: Bulk nucleation factor
        - Fnf: Boundary nucleation factor
        - Xe_radii: Xenon atomic radius (m)
        - resolution_rate: Fission resolution rate (s⁻¹)
        - fission_rate: Fission rate density (fissions/m³/s)
        - gas_production_rate: Gas yield per fission

    Returns
    -------
    dict
        Dictionary containing all calculated transport terms:
        - 'bulk_nucleation': Bulk bubble nucleation rate
        - 'bulk_absorption': Bulk bubble gas absorption rate
        - 'boundary_nucleation': Boundary bubble nucleation rate
        - 'boundary_absorption': Boundary bubble gas absorption rate
        - 'gas_influx': Gas transport from bulk to boundary
        - 'gas_release': Gas release rate coefficient
        - 'gas_resolution': Gas atom resolution from bubbles
        - 'gas_production': Fission gas production rate

    Examples
    --------
    >>> params = create_default_parameters()
    >>> terms = calculate_gas_transport_terms(
    ...     Cgb=1e25, Cgf=1e24, Ccb=1e20, Ccf=1e19,
    ...     Rcb=1e-7, Rcf=2e-7, Ncb=100, Ncf=500,
    ...     params=params
    ... )
    >>> print(f"Gas release rate: {terms['gas_release']:.2e} 1/s")
    """
    # Extract parameters
    grain_diameter = params['grain_diameter']
    Dgb = params['Dgb']
    Dgf = params['Dgf']
    Fnb = params['Fnb']
    Fnf = params['Fnf']
    Xe_radii = params['Xe_radii']
    resolution_rate = params['resolution_rate']
    fission_rate = params['fission_rate']
    gas_yield = params['gas_production_rate']

    # Calculate all transport terms
    terms = {
        'bulk_nucleation': calculate_nucleation_rate(Cgb, Dgb, Fnb, Xe_radii),
        'bulk_absorption': calculate_gas_absorption_rate(Cgb, Ccb, Rcb, Dgb),
        'boundary_nucleation': calculate_nucleation_rate(Cgf, Dgf, Fnf, Xe_radii),
        'boundary_absorption': calculate_gas_absorption_rate(Cgf, Ccf, Rcf, Dgf),
        'gas_influx': calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb),
        'gas_release': calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter),
        'gas_resolution': calculate_gas_resolution_rate(Ccb, Ncb, resolution_rate),
        'gas_production': calculate_gas_production_rate(fission_rate, gas_yield)
    }

    return terms


if __name__ == '__main__':
    """Test gas transport calculations with default parameters"""
    from ..params.parameters import create_default_parameters

    # Create default parameters
    params = create_default_parameters()

    # Define a test state
    Cgb = 1e25  # Bulk gas concentration (atoms/m³)
    Cgf = 1e24  # Boundary gas concentration (atoms/m³)
    Ccb = 1e20  # Bulk cavity concentration (cavities/m³)
    Ccf = 1e19  # Boundary cavity concentration (cavities/m³)
    Rcb = 1e-7  # Bulk cavity radius (m)
    Rcf = 2e-7  # Boundary cavity radius (m)
    Ncb = 100   # Gas atoms per bulk cavity
    Ncf = 500   # Gas atoms per boundary cavity

    # Calculate transport terms
    terms = calculate_gas_transport_terms(
        Cgb, Cgf, Ccb, Ccf, Rcb, Rcf, Ncb, Ncf, params
    )

    print("Gas Transport Calculations:")
    print("-" * 50)
    for key, value in terms.items():
        print(f"{key:25s}: {value:12.4e}")

    # Test individual functions
    print("\nIndividual Function Tests:")
    print("-" * 50)
    influx = calculate_gas_influx(Cgb, Cgf, params['grain_diameter'], params['Dgb'])
    print(f"Gas influx (bulk→boundary): {influx:.4e} atoms/m³/s")

    h0 = calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, params['grain_diameter'])
    print(f"Gas release rate coefficient: {h0:.4e} 1/s")

    print("\nGas transport module OK")
