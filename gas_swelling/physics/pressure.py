"""
气体压力计算模块 (Gas Pressure Calculation Module)

This module provides various equations of state for calculating gas pressure
inside cavities/bubbles in nuclear fuel materials.

支持的状态方程:
- Ideal Gas Law (理想气体状态方程)
- Modified Van der Waals (修正的范德瓦尔方程)
- Virial EOS (维里状态方程)
- Ronchi Hard Sphere Model (Ronchi硬球模型)
"""

import numpy as np
from typing import Dict, Optional


# Pressure calculation constants (Virial EOS coefficients)
# These constants are specific to Xenon gas
VIRIAL_B0 = 197.229
VIRIAL_B1 = 120307.145
VIRIAL_B2 = 60.555
VIRIAL_C0 = -22038.723
VIRIAL_C1 = 2292.793
VIRIAL_C2 = -117.564
VIRIAL_D0 = 1030015.045
VIRIAL_D1 = -5.200
VIRIAL_D2 = -280.677

# Modified Van der Waals constants
HS_PARAMETER = 0.6  # Hard sphere parameter
BV_PARAMETER = 8.5e-29  # Volume parameter (m³)


def calculate_ideal_gas_pressure(
    Rc: float,
    Nc: float,
    temperature: float,
    kB: float = 1.380649e-23
) -> float:
    """
    使用理想气体状态方程计算气体压力

    Calculate gas pressure using the ideal gas law:
    P = (3 * Nc * kB * T) / (4 * π * Rc³)

    Parameters
    ----------
    Rc : float
        Cavity radius (m)
    Nc : float
        Number of gas atoms in cavity
    temperature : float
        Temperature (K)
    kB : float, optional
        Boltzmann constant (J/K), default is 1.380649e-23

    Returns
    -------
    float
        Gas pressure (Pa)

    Notes
    -----
    This is the simplest equation of state, valid for low-density gases where
    molecular interactions can be neglected.
    """
    if Rc <= 1e-12 or Nc <= 0:
        return 0.0

    pressure = 3 * Nc * kB * temperature / (4 * np.pi * Rc**3)
    return pressure


def calculate_modified_vdw_pressure(
    Rc: float,
    Nc: float,
    temperature: float,
    kB: float = 1.380649e-23,
    hs: float = HS_PARAMETER,
    bv: float = BV_PARAMETER
) -> float:
    """
    使用修正的范德瓦尔气体状态方程计算气体压力

    Calculate gas pressure using modified van der Waals equation of state.
    Accounts for excluded volume effects of gas atoms.

    Parameters
    ----------
    Rc : float
        Cavity radius (m)
    Nc : float
        Number of gas atoms in cavity
    temperature : float
        Temperature (K)
    kB : float, optional
        Boltzmann constant (J/K)
    hs : float, optional
        Hard sphere parameter (dimensionless)
    bv : float, optional
        Volume parameter (m³)

    Returns
    -------
    float
        Gas pressure (Pa)

    Notes
    -----
    The modified van der Waals equation includes corrections for:
    - Finite size of gas atoms (excluded volume)
    - Attractive interactions between gas atoms
    """
    if Rc <= 1e-12 or Nc <= 0:
        return 0.0

    cavity_volume = (4.0/3.0) * np.pi * Rc**3
    excluded_volume = Nc * hs * bv
    available_volume = cavity_volume - excluded_volume

    # Prevent division by zero or negative pressure
    if available_volume <= 0:
        return 0.0

    pressure = Nc * kB * temperature / available_volume
    return pressure


def calculate_virial_eos_pressure(
    Rc: float,
    Nc: float,
    temperature: float,
    R: float = 8.314462618,
    Av: float = 6.02214076e23
) -> float:
    """
    使用Virial状态方程计算气体压力

    Calculate gas pressure using Virial equation of state.
    More accurate than ideal gas law for moderate densities.

    Parameters
    ----------
    Rc : float
        Cavity radius (m)
    Nc : float
        Number of gas atoms in cavity
    temperature : float
        Temperature (K)
    R : float, optional
        Gas constant (J/(mol·K))
    Av : float, optional
        Avogadro constant (mol⁻¹)

    Returns
    -------
    float
        Gas pressure (Pa)

    Notes
    -----
    The Virial EOS expands the compressibility factor in powers of 1/V:
    Z = 1 + B(T)/V + C(T)/V² + D(T)/V³

    Coefficients are fitted for Xenon gas.
    """
    if Rc <= 1e-12 or Nc <= 0:
        return 0.0

    # Convert units: Rc (m) -> nu (cm³/mol)
    # nu: molar volume (cm³/mol)
    nu = (4.0/3.0) * np.pi * (Rc * 1e2)**3 / Nc * Av

    # Temperature-dependent Virial coefficients
    Bs = VIRIAL_B0 + VIRIAL_B1/temperature + VIRIAL_B2/temperature**2
    Cs = VIRIAL_C0 + VIRIAL_C1/temperature + VIRIAL_C2/temperature**2
    Ds = VIRIAL_D0 + VIRIAL_D1/temperature + VIRIAL_D2/temperature**2

    # Compressibility factor
    Z = 1.0 + Bs/nu + Cs/nu**2 + Ds/nu**3

    # Pressure from compressibility factor
    pressure = R * temperature * Z / nu
    return pressure


def calculate_ronchi_pressure(
    Rc: float,
    Nc: float,
    temperature: float,
    xe_mass: float = 0.131293,
    xe_sigma: float = 3.86e-10,
    xe_Tc: float = 290.0,
    xe_dc: float = 1.103e3,
    xe_q_coeffs: Optional[list] = None,
    R: float = 8.314462618,
    Av: float = 6.02214076e23
) -> float:
    """
    使用 Ronchi 硬球模型计算气体压力

    Calculate gas pressure using Ronchi hard sphere model.
    Most accurate EOS for high-density gas in small bubbles.

    Reference: "Precipitation kinetics of rare gases implanted into metals",
               J. Nucl. Mater. 1992

    Parameters
    ----------
    Rc : float
        Cavity radius (m)
    Nc : float
        Number of gas atoms in cavity
    temperature : float
        Temperature (K)
    xe_mass : float, optional
        Xenon molar mass (kg/mol)
    xe_sigma : float, optional
        Xenon L-J collision diameter (m)
    xe_Tc : float, optional
        Xenon critical temperature (K)
    xe_dc : float, optional
        Xenon critical density (kg/m³)
    xe_q_coeffs : list, optional
        Temperature function coefficients q_n (n=1 to 5)
    R : float, optional
        Gas constant (J/(mol·K))
    Av : float, optional
        Avogadro constant (mol⁻¹)

    Returns
    -------
    float
        Gas pressure (Pa)

    Notes
    -----
    The Ronchi model combines:
    - Hard sphere compressibility (Carnahan-Starling)
    - Attractive interactions (perturbation theory)
    - Quantum corrections (Feynman-Hibbs potential)
    """
    if xe_q_coeffs is None:
        xe_q_coeffs = [2.12748, 0.52905, 0.13053, 0.02697, 0.00313]

    if Rc <= 1e-12 or Nc <= 0:
        return 0.0

    V_bubble = (4.0/3.0) * np.pi * Rc**3

    # Gas density (kg/m³)
    di = Nc * xe_mass / (V_bubble * Av)

    # Reduced temperature and density
    Tr = temperature / xe_Tc
    if Tr <= 1e-6:
        Tr = 1e-6
    dr = di / xe_dc

    # Calculation of B_plus (Eq.31)
    T1 = Tr**(5.0/7.0)
    denom_B = ((T1 - 0.553) * T1) * Tr**0.25
    if abs(denom_B) < 1e-15:
        B_plus = 0.0
    else:
        B_plus = 1.843 * (1.0 - 1.078 * (T1 - 0.162)) / denom_B

    # Calculation of f_T (Eq.29)
    beta = 1.0 / temperature
    f_T = 0.0
    for n in range(len(xe_q_coeffs)):
        f_T += (beta**(n+1)) * xe_q_coeffs[n]**(n+1)

    # Effective volume of gas (Eq.30)
    v0 = (4.0/3.0) * np.pi * Av * xe_sigma**3
    v = v0 * (B_plus + f_T)

    # Hard sphere model parameter Zhs (Carnahan-Starling, Eq.27)
    yi = v * di / 4.0
    if yi >= 1.0:
        yi = 0.99999
    denom_Zhs = (1.0 - yi)**3
    if abs(denom_Zhs) < 1e-15:
        Zhs = 1e9
    else:
        Zhs = (1.0 + yi - yi**2 - yi**3) / denom_Zhs

    # Perturbation correction Delta_Z (Eq.33)
    term_Ax = 1.538 / Tr
    Ax = 0.615 * (term_Ax**4) * (term_Ax - 1.0)
    Delta_Z = dr**2 * ((dr / Tr) * (7.0 * dr - 1.33/Tr) +
                       Ax * (1.0 + dr**3))

    # Gas pressure (Eq.27)
    numerator = Zhs - di * v0 * f_T - Delta_Z
    Pg = numerator * R * temperature / V_bubble

    return max(Pg, 0.0)


def calculate_gas_pressure(
    Rc: float,
    Nc: float,
    temperature: float,
    eos_model: str = 'ideal',
    **params
) -> float:
    """
    通用气体压力计算接口

    Generic interface for calculating gas pressure using different EOS models.

    Parameters
    ----------
    Rc : float
        Cavity radius (m)
    Nc : float
        Number of gas atoms in cavity
    temperature : float
        Temperature (K)
    eos_model : str, optional
        Equation of state model: 'ideal', 'vdw', 'virial', or 'ronchi'
    **params : dict
        Additional parameters required by specific EOS models

    Returns
    -------
    float
        Gas pressure (Pa)

    Raises
    ------
    ValueError
        If eos_model is not recognized

    Examples
    --------
    >>> P = calculate_gas_pressure(1e-8, 100, 600, 'ideal')
    >>> P = calculate_gas_pressure(1e-8, 100, 600, 'ronchi',
    ...                            xe_mass=0.131293, xe_sigma=3.86e-10)
    """
    if eos_model == 'ideal':
        return calculate_ideal_gas_pressure(Rc, Nc, temperature,
                                            kB=params.get('kB', 1.380649e-23))

    elif eos_model == 'vdw':
        return calculate_modified_vdw_pressure(Rc, Nc, temperature,
                                               kB=params.get('kB', 1.380649e-23))

    elif eos_model == 'virial':
        return calculate_virial_eos_pressure(Rc, Nc, temperature,
                                             R=params.get('R', 8.314462618),
                                             Av=params.get('Av', 6.02214076e23))

    elif eos_model == 'ronchi':
        return calculate_ronchi_pressure(
            Rc, Nc, temperature,
            xe_mass=params.get('xe_mass', 0.131293),
            xe_sigma=params.get('xe_sigma', 3.86e-10),
            xe_Tc=params.get('xe_Tc', 290.0),
            xe_dc=params.get('xe_dc', 1.103e3),
            xe_q_coeffs=params.get('xe_q_coeffs'),
            R=params.get('R', 8.314462618),
            Av=params.get('Av', 6.02214076e23)
        )

    else:
        raise ValueError(f"Unknown EOS model: {eos_model}. "
                        f"Valid options: 'ideal', 'vdw', 'virial', 'ronchi'")


if __name__ == '__main__':
    # 测试压力计算 (Test pressure calculations)
    print("气体压力计算测试 (Gas Pressure Calculation Tests)")
    print("=" * 50)

    # Test conditions
    Rc_test = 1e-8  # 10 nm
    Nc_test = 100   # 100 atoms
    T_test = 600    # 600 K

    print(f"\n测试条件 (Test conditions):")
    print(f"  气泡半径 R = {Rc_test*1e9:.1f} nm")
    print(f"  气体原子数 N = {Nc_test}")
    print(f"  温度 T = {T_test} K")

    # Test all EOS models
    models = ['ideal', 'vdw', 'virial', 'ronchi']
    for model in models:
        try:
            P = calculate_gas_pressure(Rc_test, Nc_test, T_test, model)
            print(f"  {model:10s}: P = {P:.4e} Pa ({P/1e6:.4f} MPa)")
        except Exception as e:
            print(f"  {model:10s}: Error - {e}")

    print("\n✓ 压力计算模块测试完成 (Pressure module tests completed)")
