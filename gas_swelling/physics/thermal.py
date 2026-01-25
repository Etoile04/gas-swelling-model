"""
热平衡计算模块 (Thermal Equilibrium Calculation Module)

This module provides thermal equilibrium calculations for point defects
in nuclear fuel materials, including vacancy and interstitial concentrations
at thermal equilibrium.
"""

import numpy as np
from typing import List, Optional


def calculate_cv0(
    temperature: float,
    Evf_coeffs: List[float],
    kB_ev: float = 8.617e-5,
    Evfmuti: float = 1.0
) -> float:
    """
    计算无缺陷时的热平衡空位浓度 (公式16)

    Calculate thermal equilibrium vacancy concentration in the absence of defects.

    热平衡空位浓度遵循Arrhenius关系:
    cv0 = exp(-Evf / (kB * T))

    其中空位形成能是温度的函数:
    Evf(T) = (C0 + C1*T) * Evfmuti

    Parameters
    ----------
    temperature : float
        Temperature (K)
    Evf_coeffs : list of float
        Coefficients for vacancy formation energy [C0, C1] in eV
        where Evf = C0 + C1*T (eV)
    kB_ev : float, optional
        Boltzmann constant in eV/K, default is 8.617e-5
    Evfmuti : float, optional
        Multiplier for vacancy formation energy, default is 1.0

    Returns
    -------
    float
        Thermal equilibrium vacancy concentration (dimensionless atomic fraction)

    Notes
    -----
    公式16: 空位形成能是温度的线性函数
    - 典型值: C0 = 1.034 eV, C1 = 7.6e-4 eV/K
    - 在600K时: Evf ≈ 1.034 + 7.6e-4 * 600 ≈ 1.49 eV
    - 指数参数被限制在[-700, 700]范围内以防止数值溢出

    Examples
    --------
    >>> cv0 = calculate_cv0(600, [1.034, 7.6e-4])
    >>> print(f"Thermal equilibrium vacancy concentration at 600K: {cv0:.2e}")
    """
    if temperature <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature} K")

    if len(Evf_coeffs) < 2:
        raise ValueError(f"Evf_coeffs must have at least 2 elements [C0, C1], got {Evf_coeffs}")

    # Calculate vacancy formation energy (eV)
    # 计算空位形成能 (eV)
    Evf = (Evf_coeffs[0] + Evf_coeffs[1] * temperature) * Evfmuti

    # Calculate exponent argument with clipping to prevent overflow
    # 计算指数参数，限制范围以防止溢出
    exponent_arg = -Evf / (kB_ev * temperature)
    exponent_arg = np.clip(exponent_arg, -700, 700)

    # Thermal equilibrium vacancy concentration
    # 热平衡空位浓度
    cv0 = np.exp(exponent_arg)

    return cv0


def calculate_ci0(
    temperature: float,
    Eif_coeffs: List[float],
    kB_ev: float = 8.617e-5
) -> float:
    """
    计算无缺陷时的热平衡间隙原子浓度

    Calculate thermal equilibrium interstitial concentration in the absence of defects.

    热平衡间隙原子浓度遵循Arrhenius关系:
    ci0 = exp(-Eif / (kB * T))

    其中间隙原子形成能是温度的三次多项式函数:
    Eif(T) = C0 + C1*T + C2*T² + C3*T³

    Parameters
    ----------
    temperature : float
        Temperature (K)
    Eif_coeffs : list of float
        Coefficients for interstitial formation energy [C0, C1, C2, C3] in eV
        where Eif = C0 + C1*T + C2*T² + C3*T³ (eV)
    kB_ev : float, optional
        Boltzmann constant in eV/K, default is 8.617e-5

    Returns
    -------
    float
        Thermal equilibrium interstitial concentration (dimensionless atomic fraction)

    Notes
    -----
    间隙原子形成能是温度的三次多项式函数
    - 典型值: C0 = -3.992 eV, C1 = 0.038 eV/K, C2 = -7.645e-5 eV/K², C3 = 5.213e-8 eV/K³
    - 由于形成能可能是负值,间隙原子在高温下浓度显著
    - 指数参数被限制在[-700, 700]范围内以防止数值溢出

    Examples
    --------
    >>> ci0 = calculate_ci0(600, [-3.992, 0.038, -7.645e-5, 5.213e-8])
    >>> print(f"Thermal equilibrium interstitial concentration at 600K: {ci0:.2e}")
    """
    if temperature <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature} K")

    if len(Eif_coeffs) < 4:
        raise ValueError(f"Eif_coeffs must have at least 4 elements [C0, C1, C2, C3], got {Eif_coeffs}")

    # Calculate interstitial formation energy (eV) - cubic polynomial in T
    Eif = (Eif_coeffs[0] +
           Eif_coeffs[1] * temperature +
           Eif_coeffs[2] * temperature**2 +
           Eif_coeffs[3] * temperature**3)

    # Calculate exponent argument with clipping to prevent overflow
    exponent_arg = -Eif / (kB_ev * temperature)
    exponent_arg = np.clip(exponent_arg, -700, 700)

    # Thermal equilibrium interstitial concentration
    ci0 = np.exp(exponent_arg)

    return ci0


def calculate_thermal_equilibrium_concentrations(
    temperature: float,
    Evf_coeffs: List[float],
    Eif_coeffs: List[float],
    kB_ev: float = 8.617e-5,
    Evfmuti: float = 1.0
) -> tuple:
    """
    计算热平衡空位和间隙原子浓度

    Calculate both thermal equilibrium vacancy and interstitial concentrations.

    Parameters
    ----------
    temperature : float
        Temperature (K)
    Evf_coeffs : list of float
        Coefficients for vacancy formation energy [C0, C1] in eV
    Eif_coeffs : list of float
        Coefficients for interstitial formation energy [C0, C1, C2, C3] in eV
    kB_ev : float, optional
        Boltzmann constant in eV/K, default is 8.617e-5
    Evfmuti : float, optional
        Multiplier for vacancy formation energy, default is 1.0

    Returns
    -------
    tuple (cv0, ci0)
        cv0 : float
            Thermal equilibrium vacancy concentration
        ci0 : float
            Thermal equilibrium interstitial concentration

    Examples
    --------
    >>> cv0, ci0 = calculate_thermal_equilibrium_concentrations(
    ...     600, [1.034, 7.6e-4], [-3.992, 0.038, -7.645e-5, 5.213e-8]
    ... )
    >>> print(f"cv0 = {cv0:.2e}, ci0 = {ci0:.2e}")
    """
    cv0 = calculate_cv0(temperature, Evf_coeffs, kB_ev, Evfmuti)
    ci0 = calculate_ci0(temperature, Eif_coeffs, kB_ev)
    return cv0, ci0


if __name__ == '__main__':
    # 测试热平衡计算 (Test thermal equilibrium calculations)
    print("热平衡计算测试 (Thermal Equilibrium Calculation Tests)")
    print("=" * 60)

    # Test parameters (测试参数)
    T_test = 600  # K (温度)
    Evf_coeffs_test = [1.034, 7.6e-4]  # Vacancy formation energy coefficients (空位形成能系数)
    Eif_coeffs_test = [-3.992, 0.038, -7.645e-5, 5.213e-8]  # Interstitial formation energy coefficients (间隙原子形成能系数)
    kB_ev_test = 8.617e-5  # eV/K (玻尔兹曼常数)

    print(f"\n测试条件 (Test conditions):")
    print(f"  温度 Temperature T = {T_test} K")
    print(f"  空位形成能系数 Evf_coeffs = {Evf_coeffs_test} eV")
    print(f"  间隙形成能系数 Eif_coeffs = {Eif_coeffs_test} eV")
    print(f"  玻尔兹曼常数 Boltzmann Constant kB = {kB_ev_test} eV/K")

    # Test vacancy concentration (测试空位浓度)
    print(f"\n空位浓度测试 (Vacancy Concentration Test):")
    cv0 = calculate_cv0(T_test, Evf_coeffs_test, kB_ev_test)
    print(f"  cv0 = {cv0:.6e}")

    # Test interstitial concentration (测试间隙原子浓度)
    print(f"\n间隙原子浓度测试 (Interstitial Concentration Test):")
    ci0 = calculate_ci0(T_test, Eif_coeffs_test, kB_ev_test)
    print(f"  ci0 = {ci0:.6e}")

    # Test combined calculation (测试联合计算)
    print(f"\n联合计算测试 (Combined Calculation Test):")
    cv0_combined, ci0_combined = calculate_thermal_equilibrium_concentrations(
        T_test, Evf_coeffs_test, Eif_coeffs_test, kB_ev_test
    )
    print(f"  cv0 = {cv0_combined:.6e}")
    print(f"  ci0 = {ci0_combined:.6e}")

    # Temperature sweep test (温度扫描测试)
    print(f"\n温度扫描测试 (Temperature Sweep Test):")
    print(f"  {'T (K)':<10} {'cv0':<15} {'ci0':<15}")
    print(f"  {'-'*40}")
    for T in [400, 500, 600, 700, 800, 900, 1000]:
        cv0_T, ci0_T = calculate_thermal_equilibrium_concentrations(
            T, Evf_coeffs_test, Eif_coeffs_test, kB_ev_test
        )
        print(f"  {T:<10} {cv0_T:<15.6e} {ci0_T:<15.6e}")

    print("\n✓ 热平衡计算模块测试完成 (Thermal module tests completed)")
