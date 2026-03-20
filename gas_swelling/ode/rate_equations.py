"""
气体肿胀速率方程系统 (Gas Swelling Rate Equation System)

This module implements the complete system of ordinary differential equations (ODEs)
that describe gas swelling evolution in irradiated nuclear fuel materials.

状态变量 (State Variables - 17 components):
0: Cgb  - 基体气体原子浓度 (Bulk gas atom concentration, atoms/m³)
1: Ccb  - 基体空腔浓度 (Bulk cavity concentration, cavities/m³)
2: Ncb  - 每个基体空腔内的气体原子数 (Gas atoms per bulk cavity, atoms/cavity)
3: Rcb  - 基体空腔半径 (Bulk cavity radius, m)
4: Cgf  - 晶界气体原子浓度 (Grain boundary gas concentration, atoms/m³)
5: Ccf  - 晶界空腔浓度 (Grain boundary cavity concentration, cavities/m³)
6: Ncf  - 每个晶界空腔内的气体原子数 (Gas atoms per boundary cavity, atoms/cavity)
7: Rcf  - 晶界空腔半径 (Grain boundary cavity radius, m)
8: cvb  - 基体空位浓度 (Bulk vacancy concentration)
9: cib  - 基体间隙原子浓度 (Bulk interstitial concentration)
10: cvf  - 晶界空位浓度 (Grain boundary vacancy concentration)
11: cif  - 晶界间隙原子浓度 (Grain boundary interstitial concentration)
12: released_gas - 累积释放气体 (Cumulative released gas)
13: kvb  - 基体空位汇聚强度 (Bulk vacancy sink strength)
14: kib  - 基体间隙原子汇聚强度 (Bulk interstitial sink strength)
15: kvf  - 晶界空位汇聚强度 (Boundary vacancy sink strength)
16: kif  - 晶界间隙原子汇聚强度 (Boundary interstitial sink strength)

References
----------
- Rate theory for fission gas behavior in metallic fuel (Eqs. 1-25)
- Cavity growth kinetics (Eq. 14)
- Point defect kinetics (Eqs. 17-24)
- Gas transport and release (Eqs. 1-12)
"""

import numpy as np
from typing import Dict, Tuple

# Import physics calculation functions
from ..physics.pressure import calculate_gas_pressure
from ..physics.gas_transport import (
    calculate_gas_influx,
    calculate_gas_release_rate,
    calculate_nucleation_rate,
    calculate_gas_absorption_rate,
    calculate_gas_resolution_rate
)
from ..physics.thermal import calculate_cv0


def calculate_sink_strengths(
    Rcb: float,
    Rcf: float,
    Ccb: float,
    Ccf: float,
    Zv: float,
    Zi: float,
    rho: float
) -> Dict[str, float]:
    """
    计算基体和晶界处的点缺陷汇聚强度 (Calculate sink strengths for point defects)

    根据公式21和22计算空腔和位错对点缺陷的汇聚强度
    Calculate sink strengths according to Eqs. 21 and 22

    Parameters
    ----------
    Rcb : float
        基体空腔半径 (Bulk cavity radius, m)
    Rcf : float
        晶界空腔半径 (Boundary cavity radius, m)
    Ccb : float
        基体空腔浓度 (Bulk cavity concentration, cavities/m³)
    Ccf : float
        晶界空腔浓度 (Boundary cavity concentration, cavities/m³)
    Zv : float
        空位偏压因子 (Vacancy bias factor)
    Zi : float
        间隙原子偏压因子 (Interstitial bias factor)
    rho : float
        位错密度 (Dislocation density, m⁻²)

    Returns
    -------
    Dict[str, float]
        汇聚强度字典 (Dictionary of sink strengths):
        - kvc2_b: 基体空腔对空位的汇聚强度 (Bulk cavity vacancy sink strength)
        - kic2_b: 基体空腔对间隙原子的汇聚强度 (Bulk cavity interstitial sink strength)
        - kvc2_f: 晶界空腔对空位的汇聚强度 (Boundary cavity vacancy sink strength)
        - kic2_f: 晶界空腔对间隙原子的汇聚强度 (Boundary cavity interstitial sink strength)
        - kvb2_total: 基体空位总汇聚强度 (Bulk total vacancy sink strength)
        - kib2_total: 基体间隙原子总汇聚强度 (Bulk total interstitial sink strength)
        - kvf2_total: 晶界空位总汇聚强度 (Boundary total vacancy sink strength)
        - kif2_total: 晶界间隙原子总汇聚强度 (Boundary total interstitial sink strength)

    Notes
    -----
    公式21和22 (Eqs. 21 and 22):
    - k²_vc = 4πRCc(1 + kR): 空腔对空位的汇聚强度 (Cavity sink strength for vacancies)
    - k²_ic = 4πRCc(1 + kR): 空腔对间隙原子的汇聚强度 (Cavity sink strength for interstitials)
    - k²_vd = Zvρ: 位错对空位的汇聚强度 (Dislocation sink strength for vacancies)
    - k²_id = Ziρ: 位错对间隙原子的汇聚强度 (Dislocation sink strength for interstitials)
    """
    # 数值保护：避免半径为零或负值 (Numerical protection: avoid zero or negative radius)
    Rcb_safe = np.clip(Rcb, 1e-12, 1e-4)
    Rcf_safe = np.clip(Rcf, 1e-12, 1e-4)

    # 位错汇聚强度 (Dislocation sink strengths, Eqs. 23, 24)
    k_vd2 = Zv * rho
    k_id2 = Zi * rho

    # 空腔汇聚强度 (Cavity sink strengths, Eqs. 21, 22)
    # 基体 (Bulk)
    kvc2_b = 4 * np.pi * Rcb_safe * Ccb  # Simplified form
    kic2_b = 4 * np.pi * Rcb_safe * Ccb  # Simplified form

    # 晶界 (Boundary)
    kvc2_f = 4 * np.pi * Rcf_safe * Ccf  # Simplified form
    kic2_f = 4 * np.pi * Rcf_safe * Ccf  # Simplified form

    # 总汇聚强度 (Total sink strengths, Eqs. 19, 20)
    kvb2_total = kvc2_b + k_vd2
    kib2_total = kic2_b + k_id2
    kvf2_total = kvc2_f + k_vd2
    kif2_total = kic2_f + k_id2

    return {
        'kvc2_b': kvc2_b,
        'kic2_b': kic2_b,
        'kvc2_f': kvc2_f,
        'kic2_f': kic2_f,
        'kvb2_total': kvb2_total,
        'kib2_total': kib2_total,
        'kvf2_total': kvf2_total,
        'kif2_total': kif2_total
    }


def calculate_point_defect_derivatives(
    cvb: float,
    cib: float,
    cvf: float,
    cif: float,
    kvb2_total: float,
    kib2_total: float,
    kvf2_total: float,
    kif2_total: float,
    Dv: float,
    Di: float,
    phi: float,
    alpha: float
) -> Tuple[float, float, float, float]:
    """
    计算点缺陷浓度的变化率 (Calculate point defect concentration derivatives)

    根据公式17和18计算空位和间隙原子浓度的变化率
    Calculate derivatives of vacancy and interstitial concentrations according to Eqs. 17 and 18

    Parameters
    ----------
    cvb, cib : float
        基体空位和间隙原子浓度 (Bulk vacancy and interstitial concentrations)
    cvf, cif : float
        晶界空位和间隙原子浓度 (Boundary vacancy and interstitial concentrations)
    kvb2_total, kib2_total : float
        基体空位和间隙原子总汇聚强度 (Bulk total sink strengths)
    kvf2_total, kif2_total : float
        晶界空位和间隙原子总汇聚强度 (Boundary total sink strengths)
    Dv, Di : float
        空位和间隙原子扩散系数 (Vacancy and interstitial diffusivities, m²/s)
    phi : float
        点缺陷产生率 (Point defect production rate, defects/m³/s)
    alpha : float
        复合系数 (Recombination coefficient, m³/s)

    Returns
    -------
    Tuple[float, float, float, float]
        (dcvb_dt, dcib_dt, dcvf_dt, dcif_dt)
        基体和晶界处的空位、间隙原子浓度变化率 (Derivatives of vacancy and interstitial concentrations)

    Notes
    -----
    公式17和18 (Eqs. 17 and 18):
    dcv/dt = φ - k²_v D cv - α cv ci
    dci/dt = φ - k²_i D ci - α cv ci

    其中 (Where):
    - φ: 裂变产生率 (Fission production rate)
    - k²_v: 空位汇聚强度 (Vacancy sink strength)
    - k²_i: 间隙原子汇聚强度 (Interstitial sink strength)
    - D: 扩散系数 (Diffusion coefficient)
    - α: 复合系数 (Recombination coefficient)
    """
    # 基体点缺陷 (Bulk point defects, Eq. 17)
    dcvb_dt = phi - kvb2_total * Dv * cvb - alpha * cvb * cib
    dcib_dt = phi - kib2_total * Di * cib - alpha * cvb * cib

    # 晶界点缺陷 (Boundary point defects, Eq. 18)
    dcvf_dt = phi - kvf2_total * Dv * cvf - alpha * cvf * cif
    dcif_dt = phi - kif2_total * Di * cif - alpha * cvf * cif

    return dcvb_dt, dcib_dt, dcvf_dt, dcif_dt


def calculate_cavity_radius_derivatives(
    Rcb: float,
    Rcf: float,
    Ccb: float,
    Ccf: float,
    cvb: float,
    cib: float,
    cvf: float,
    cif: float,
    Ncb: float,
    Ncf: float,
    cv0: float,
    kvc2_b: float,
    kic2_b: float,
    kvc2_f: float,
    kic2_f: float,
    Dv: float,
    Di: float,
    temperature: float,
    kB: float,
    surface_energy: float,
    hydrostatic_pressure: float,
    atomic_volume: float,
    eos_model: str
) -> Tuple[float, float]:
    """
    计算空腔半径的变化率 (Calculate cavity radius derivatives)

    根据公式14计算空腔半径随时间的变化率，考虑空位吸收、间隙原子吸收和热发射
    Calculate cavity radius growth rate according to Eq. 14, considering vacancy absorption,
    interstitial absorption, and thermal emission

    Parameters
    ----------
    Rcb, Rcf : float
        基体和晶界空腔半径 (Bulk and boundary cavity radii, m)
    Ccb, Ccf : float
        基体和晶界空腔浓度 (Bulk and boundary cavity concentrations, cavities/m³)
    cvb, cib : float
        基体空位和间隙原子浓度 (Bulk vacancy and interstitial concentrations)
    cvf, cif : float
        晶界空位和间隙原子浓度 (Boundary vacancy and interstitial concentrations)
    Ncb, Ncf : float
        每个空腔内的气体原子数 (Gas atoms per cavity)
    cv0 : float
        热平衡空位浓度 (Thermal equilibrium vacancy concentration)
    kvc2_b, kic2_b : float
        基体空腔对空位和间隙原子的汇聚强度 (Bulk cavity sink strengths)
    kvc2_f, kic2_f : float
        晶界空腔对空位和间隙原子的汇聚强度 (Boundary cavity sink strengths)
    Dv, Di : float
        空位和间隙原子扩散系数 (Vacancy and interstitial diffusivities, m²/s)
    temperature : float
        温度 (Temperature, K)
    kB : float
        玻尔兹曼常数 (Boltzmann constant, J/K)
    surface_energy : float
        表面能 (Surface energy, J/m²)
    hydrostatic_pressure : float
        静水压力 (Hydrostatic pressure, Pa)
    atomic_volume : float
        原子体积 (Atomic volume, m³)
    eos_model : str
        气体状态方程模型 (Gas equation of state model: 'ideal', 'vdw', 'virial', 'ronchi')

    Returns
    -------
    Tuple[float, float, float, float]
        (dRcb_dt, dRcf_dt, cv_star_b, cv_star_f)
        空腔半径变化率和空腔附近的空位浓度 (Cavity radius derivatives and cavity-side vacancy concentrations)

    Notes
    -----
    公式14 (Eq. 14):
    dR/dt = (1/(4πR²Cc)) × [k²_vc D cv (1 - η - ξ)]

    其中 (Where):
    - η = (k²_i D ci) / (k²_v D cv): 间隙原子吸收项 (Interstitial absorption term)
    - ξ = cv*/cv: 热发射项 (Thermal emission term)
    - cv* = cv0 × exp(-ΔP × Ω / (kB × T)): 空腔附近的空位浓度 (Cavity-side vacancy concentration)
    - ΔP = Pg - 2γ/R - σ_ext: 有效压力差 (Effective pressure difference)

    空腔半径变化受三个因素影响 (Cavity radius growth is affected by three factors):
    1. 偏压驱动的空位吸收 (Bias-driven vacancy absorption)
    2. 间隙原子吸收导致的收缩 (Shrinkage due to interstitial absorption)
    3. 热发射导致的空位损失 (Vacancy loss due to thermal emission)
    """
    # 数值保护 (Numerical protection)
    Rcb_safe = np.clip(Rcb, 1e-12, 1e-4)
    Rcf_safe = np.clip(Rcf, 1e-12, 1e-4)

    # 计算气体压力 (Calculate gas pressure)
    Pg_b = calculate_gas_pressure(Rcb_safe, Ncb, temperature, eos_model,
                                  kB=kB, atomic_volume=atomic_volume)
    Pg_f = calculate_gas_pressure(Rcf_safe, Ncf, temperature, eos_model,
                                  kB=kB, atomic_volume=atomic_volume)

    # 最小压力保护 (Minimum pressure protection)
    Pg_b = max(Pg_b, 1.0)
    Pg_f = max(Pg_f, 1.0)

    # 计算有效压力 (毛细管压力 - 静水压力) (Calculate effective pressure)
    # 公式15 (Eq. 15): Pext = Pg - 2γ/R - σ_ext
    Pext_b = Pg_b - 2 * surface_energy / Rcb_safe - hydrostatic_pressure
    Pext_f = Pg_f - 2 * surface_energy / Rcf_safe - hydrostatic_pressure

    # 计算空腔附近的空位浓度 (Calculate cavity-side vacancy concentration, Eq. 15)
    # cv* = cv0 × exp(-ΔP × Ω / (kB × T))
    exponent_b = -Pext_b * atomic_volume / (kB * temperature)
    exponent_f = -Pext_f * atomic_volume / (kB * temperature)

    # 指数项数值保护 (Exponential term numerical protection)
    exponent_b = np.clip(exponent_b, -700, 700)
    exponent_f = np.clip(exponent_f, -700, 700)

    cv_star_b = cv0 * np.exp(exponent_b)
    cv_star_f = cv0 * np.exp(exponent_f)

    # 计算半径变化率 (公式14) (Calculate radius derivative, Eq. 14)
    # dR/dt = (1/(4πR²Cc)) × k²_vc D cv × (1 - η - ξ)
    # 其中 η = (k²_i D ci)/(k²_v D cv), ξ = cv*/cv

    # 基体空腔 (Bulk cavity)
    if Ccb > 0 and cvb > 0:
        vacancy_influx_b = kvc2_b * Dv * cvb
        interstitial_influx_b = kic2_b * Di * cib
        eta_b = interstitial_influx_b / vacancy_influx_b if vacancy_influx_b > 0 else 0
        xi_b = cv_star_b / cvb
        dRcb_dt = (1 / (4 * np.pi * Rcb_safe**2 * Ccb)) * vacancy_influx_b * (1 - eta_b - xi_b)
    else:
        dRcb_dt = 0.0

    # 晶界空腔 (Boundary cavity)
    if Ccf > 0 and cvf > 0:
        vacancy_influx_f = kvc2_f * Dv * cvf
        interstitial_influx_f = kic2_f * Di * cif
        eta_f = interstitial_influx_f / vacancy_influx_f if vacancy_influx_f > 0 else 0
        xi_f = cv_star_f / cvf
        dRcf_dt = (1 / (4 * np.pi * Rcf_safe**2 * Ccf)) * vacancy_influx_f * (1 - eta_f - xi_f)
    else:
        dRcf_dt = 0.0

    # 半径只能增长不能收缩（在空腔稳定后）(Radius can only grow after cavity stabilization)
    dRcb_dt = max(dRcb_dt, 0.0)
    dRcf_dt = max(dRcf_dt, 0.0)

    return dRcb_dt, dRcf_dt, cv_star_b, cv_star_f


def calculate_gas_concentration_derivatives(
    Cgb: float,
    Ccb: float,
    Ncb: float,
    Cgf: float,
    Ccf: float,
    Ncf: float,
    Rcb: float,
    Rcf: float,
    grain_diameter: float,
    Dgb: float,
    Dgf: float,
    fission_rate: float,
    gas_production_rate: float,
    resolution_rate: float,
    Fnb: float,
    Fnf: float,
    Xe_radii: float,
    eos_model: str,
    temperature: float,
    kB: float,
    atomic_volume: float
) -> Tuple[float, float, float, float, float, float]:
    """
    计算气体浓度的变化率 (Calculate gas concentration derivatives)

    根据公式1-7计算气体原子浓度、空腔浓度和每个空腔内气体原子数的变化率
    Calculate derivatives of gas concentrations according to Eqs. 1-7

    Parameters
    ----------
    Cgb, Cgf : float
        基体和晶界气体原子浓度 (Bulk and boundary gas concentrations, atoms/m³)
    Ccb, Ccf : float
        基体和晶界空腔浓度 (Bulk and boundary cavity concentrations, cavities/m³)
    Ncb, Ncf : float
        每个空腔内的气体原子数 (Gas atoms per cavity)
    Rcb, Rcf : float
        基体和晶界空腔半径 (Bulk and boundary cavity radii, m)
    grain_diameter : float
        晶粒直径 (Grain diameter, m)
    Dgb, Dgf : float
        基体和晶界气体扩散系数 (Bulk and boundary gas diffusivities, m²/s)
    fission_rate : float
        裂变率 (Fission rate, fissions/m³/s)
    gas_production_rate : float
        气体产生率因子 (Gas production rate factor)
    resolution_rate : float
        重溶率 (Resolution rate, s⁻¹)
    Fnb, Fnf : float
        基体和晶界成核因子 (Bulk and boundary nucleation factors)
    Xe_radii : float
        氙原子半径 (Xenon atomic radius, m)
    eos_model : str
        气体状态方程模型 (Gas equation of state model)
    temperature : float
        温度 (Temperature, K)
    kB : float
        玻尔兹曼常数 (Boltzmann constant, J/K)
    atomic_volume : float
        原子体积 (Atomic volume, m³)

    Returns
    -------
    Tuple[float, float, float, float, float, float, float]
        (dCgb_dt, dCcb_dt, dNcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dh_dt)
        气体浓度变化率和气体释放率 (Gas concentration derivatives and release rate)

    Notes
    -----
    气体输运方程 (Gas transport equations):
    - dCgb/dt (Eq. 1): 基体气体原子浓度变化率
      = 气体产生 - 气泡成核 - 气泡吸收 - 扩散到晶界 + 重溶
      = Yφ - 16πFrXDgCg² - 4πRDgCgCc - J + bCcNc

    - dCcb/dt (Eq. 3): 基体气泡浓度变化率
      = 气泡成核率 / 每个气泡的气体原子数
      = (16πFrXDgCg²) / Nc

    - dNcb/dt (Eq. 5): 每个基体气泡内气体原子数变化率
      = 气体吸收率 - 重溶率
      = 4πRDgCg - bNc

    - dCgf/dt (Eq. 6): 晶界气体浓度变化率
      = 扩散从基体 - 气泡成核 - 气泡吸收 - 气体释放
      = J - 16πFrXDgCg² - 4πRDgCgCc - hCg

    - dCcf/dt (Eq. 7): 晶界气泡浓度变化率
      = 晶界成核率 / 每个气泡的气体原子数
      = (16πFrXDgCg²) / Nc

    - dNcf/dt (Eq. 13): 每个晶界气泡内气体原子数变化率
      = 气体吸收率 - 气体释放率
      = 4πRDgCg - hNc

    - dh/dt (Eq. 12): 累积气体释放率
      = h × (Cgf + Ccf×Ncf)
      即从晶界游离气体和晶界气泡中释放出去的总气体通量
    """
    # 数值保护 (Numerical protection)
    Rcb_safe = np.clip(Rcb, 1e-12, 1e-4)
    Rcf_safe = np.clip(Rcf, 1e-12, 1e-4)

    # 计算气体输运项 (Calculate gas transport terms)
    g0 = calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)
    h0 = calculate_gas_release_rate(Rcf_safe, Ncf, Cgf, Ccf, grain_diameter)

    # 气体产生率 (Gas production rate)
    gas_production = gas_production_rate * fission_rate

    # 1. 基体气体原子浓度变化率 (公式1) (Bulk gas concentration derivative, Eq. 1)
    # dCgb/dt = Yφ - nucleation - absorption - diffusion_to_boundary + resolution
    nucleation_b = calculate_nucleation_rate(Fnb, Xe_radii, Dgb, Cgb)
    absorption_b = calculate_gas_absorption_rate(Rcb_safe, Dgb, Cgb, Ccb)
    resolution_b = calculate_gas_resolution_rate(resolution_rate, Ccb, Ncb)

    dCgb_dt = gas_production - nucleation_b - absorption_b - g0 + resolution_b

    # 2. 基体空腔浓度变化率 (公式3) (Bulk cavity concentration derivative, Eq. 3)
    # dCcb/dt = nucleation_rate / Nc
    Ncb_safe = max(Ncb, 2.0)  # 避免除零 (Avoid division by zero)
    dCcb_dt = nucleation_b / Ncb_safe

    # 3. 每个基体空腔内气体原子数变化率 (公式5) (Gas atoms per bulk cavity derivative, Eq. 5)
    # dNcb/dt = absorption - resolution
    dNcb_dt = absorption_b / Ccb - resolution_rate * Ncb if Ccb > 0 else 0

    # 4. 晶界气体浓度变化率 (公式6) (Boundary gas concentration derivative, Eq. 6)
    # dCgf/dt = diffusion_from_bulk - nucleation - absorption - release
    nucleation_f = calculate_nucleation_rate(Fnf, Xe_radii, Dgf, Cgf)
    absorption_f = calculate_gas_absorption_rate(Rcf_safe, Dgf, Cgf, Ccf)

    dCgf_dt = g0 - nucleation_f - absorption_f - h0 * Cgf

    # 5. 晶界空腔浓度变化率 (公式7) (Boundary cavity concentration derivative, Eq. 7)
    # dCcf/dt = nucleation_rate / Nc
    Ncf_safe = max(Ncf, 2.0)  # 避免除零 (Avoid division by zero)
    dCcf_dt = nucleation_f / Ncf_safe

    # 6. 每个晶界空腔内气体原子数变化率 (公式13) (Gas atoms per boundary cavity derivative, Eq. 13)
    # dNcf/dt = absorption - release
    dNcf_dt = absorption_f / Ccf - h0 * Ncf if Ccf > 0 else 0

    # 7. 累积气体释放率 (Cumulative gas release rate)
    # Released gas must track the gas removed from the boundary gas pool and
    # boundary bubbles, otherwise total gas inventory appears to "disappear".
    dh_dt = h0 * (max(Cgf, 0.0) + max(Ccf, 0.0) * max(Ncf, 0.0))

    return dCgb_dt, dCcb_dt, dNcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dh_dt


def swelling_ode_system(
    t: float,
    state: np.ndarray,
    params: Dict
) -> np.ndarray:
    """
    气体肿胀常微分方程系统 (Gas Swelling ODE System)

    完整的速率方程系统，描述气体肿胀演化过程中的所有状态变量变化
    Complete system of rate equations describing the evolution of all state variables
    during gas swelling in irradiated nuclear fuel materials.

    Parameters
    ----------
    t : float
        时间 (Time, s) - 未在微分方程中显式使用，但scipy.solve_ivp需要此参数
        (Not explicitly used in differential equations, but required by scipy.solve_ivp)
    state : np.ndarray
        状态变量向量 (State variable vector, 17 components):
        [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, cvf, cif,
         released_gas, kvb, kib, kvf, kif]
    params : Dict
        模型参数字典 (Model parameters dictionary):
        - temperature: 温度 (Temperature, K)
        - fission_rate: 裂变率 (Fission rate, fissions/m³/s)
        - displacement_rate: 离位率 (Displacement rate)
        - gas_production_rate: 气体产生率因子 (Gas production rate factor)
        - resolution_rate: 重溶率 (Resolution rate, s⁻¹)
        - grain_diameter: 晶粒直径 (Grain diameter, m)
        - Dgb_prefactor: 基体气体扩散系数前因子 (Bulk gas diffusivity prefactor)
        - Dgb_activation_energy: 基体气体扩散激活能 (Bulk gas activation energy, eV)
        - Dgb_fission_term: 裂变相关项系数 (Fission-related term coefficient)
        - Dgf_multiplier: 相界扩散系数倍数 (Boundary diffusivity multiplier)
        - Dv0: 空位扩散系数前因子 (Vacancy diffusivity prefactor, m²/s)
        - Evm: 空位迁移能 (Vacancy migration energy, eV)
        - Di0: 间隙原子扩散系数前因子 (Interstitial diffusivity prefactor, m²/s)
        - Eim: 间隙原子迁移能 (Interstitial migration energy, eV)
        - Zv, Zi: 空位和间隙原子偏压因子 (Vacancy and interstitial bias factors)
        - dislocation_density: 位错密度 (Dislocation density, m⁻²)
        - surface_energy: 表面能 (Surface energy, J/m²)
        - hydrastatic_pressure: 静水压力 (Hydrostatic pressure, Pa)
        - Fnb, Fnf: 基体和晶界成核因子 (Bulk and boundary nucleation factors)
        - Xe_radii: 氙原子半径 (Xenon atomic radius, m)
        - recombination_radius: 复合半径 (Recombination radius, m)
        - Omega: 原子体积 (Atomic volume, m³)
        - kB: 玻尔兹曼常数 (Boltzmann constant, J/K)
        - kB_ev: 玻尔兹曼常数 (Boltzmann constant, eV/K)
        - eos_model: 气体状态方程模型 (Gas equation of state model)
        - Evf_coeffs: 空位形成能系数 (Vacancy formation energy coefficients)

    Returns
    -------
    np.ndarray
        导数向量 (Derivative vector, 17 components):
        [dCgb_dt, dCcb_dt, dNcb_dt, dRcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dRcf_dt,
         dcvb_dt, dcib_dt, dcvf_dt, dcif_dt, dh_dt, 0, 0, 0, 0]
        其中汇聚强度参数的导数为零 (Derivatives of sink strength parameters are zero)

    Examples
    --------
    >>> from scipy.integrate import solve_ivp
    >>> from gas_swelling.params.parameters import create_default_parameters
    >>> from gas_swelling.ode.rate_equations import swelling_ode_system
    >>>
    >>> # 创建参数 (Create parameters)
    >>> params = create_default_parameters()
    >>>
    >>> # 初始状态 (Initial state)
    >>> y0 = np.array([
    ...     1e20, 1e20,  # Cgb, Cgf (gas concentrations)
    ...     1e18, 1e18,  # Ccb, Ccf (cavity concentrations)
    ...     4.0, 4.0,     # Ncb, Ncf (gas atoms per cavity)
    ...     1e-9, 1e-9,   # Rcb, Rcf (cavity radii)
    ...     1e-6, 1e-6,   # cvb, cib (vacancy and interstitial)
    ...     1e-6, 1e-6,   # cvf, cif (vacancy and interstitial at boundary)
    ...     0.0,          # released_gas
    ...     0.0, 0.0, 0.0, 0.0  # kvb, kib, kvf, kif (sink strengths)
    ... ])
    >>>
    >>> # 求解ODE (Solve ODE)
    >>> sol = solve_ivp(
    ...     fun=lambda t, y: swelling_ode_system(t, y, params),
    ...     t_span=(0, 86400),  # 1 day
    ...     y0=y0,
    ...     method='BDF'
    ... )

    Notes
    -----
    该ODE系统实现了以下物理过程 (This ODE system implements the following physical processes):

    1. 气体原子输运 (Gas atom transport, Eqs. 1-7)
       - 基体和晶界气体浓度的演化 (Evolution of bulk and boundary gas concentrations)
       - 气泡成核和生长 (Bubble nucleation and growth)
       - 气体原子在基体和晶界之间的扩散 (Diffusion between bulk and boundary)

    2. 点缺陷动力学 (Point defect kinetics, Eqs. 17-24)
       - 空位和间隙原子的产生、复合和湮灭 (Production, recombination, and annihilation)
       - 位错和空腔作为缺陷汇 (Dislocations and cavities as defect sinks)

    3. 空腔生长动力学 (Cavity growth kinetics, Eq. 14)
       - 偏压驱动的空位吸收 (Bias-driven vacancy absorption)
       - 间隙原子吸收导致的收缩 (Shrinkage from interstitial absorption)
       - 热发射导致的空位损失 (Vacancy loss from thermal emission)

    4. 气体释放 (Gas release, Eqs. 9-12)
       - 气泡互连和气体释放 (Bubble interconnection and gas release)

    数值稳定性考虑 (Numerical stability considerations):
    - 使用np.clip限制指数项的范围，防止溢出 (Use np.clip to limit exponential terms)
    - 使用max避免除零错误 (Use max to avoid division by zero)
    - 对导数进行范围限制，防止数值爆炸 (Limit derivative ranges to prevent numerical explosion)

    References
    ----------
    Rate theory for fission gas behavior in metallic nuclear fuels:
    - Eqs. 1-8: Gas transport and bubble evolution
    - Eqs. 9-12: Gas release from interconnected bubbles
    - Eq. 13: Gas atoms per cavity evolution
    - Eq. 14: Cavity growth kinetics
    - Eqs. 15-16: Thermal equilibrium and effective pressure
    - Eqs. 17-24: Point defect production and annihilation
    """
    # 解包状态变量 (Unpack state vector, 17 variables)
    Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, cvf, cif, \
        released_gas, kvb, kib, kvf, kif = state

    # 数值保护：避免半径为零或负值 (Numerical protection: avoid zero or negative radius)
    Rcb_safe = np.clip(Rcb, 1e-12, 1e-4)
    Rcf_safe = np.clip(Rcf, 1e-12, 1e-4)

    # 提取温度相关参数 (Extract temperature-related parameters)
    T = params['temperature']
    kB_ev = params['kB_ev']
    kB_J = params['kB']

    # 计算扩散系数 (Calculate diffusivities)
    # 空位扩散系数 (Vacancy diffusivity)
    Dv = params['Dv0'] * np.exp(-params['Evm'] / (kB_ev * T))

    # 间隙原子扩散系数 (Interstitial diffusivity)
    Di = params['Di0'] * np.exp(-params['Eim'] / (kB_ev * T))

    # 气体扩散系数 (Gas diffusivity in bulk and boundary)
    Dgb = (params['Dgb_prefactor'] * np.exp(-params['Dgb_activation_energy'] / (kB_ev * T)) +
           params['Dgb_fission_term'] * params['fission_rate'])
    Dgf = params['Dgf_multiplier'] * Dgb

    # 点缺陷参数 (Point defect parameters)
    Zv = params['Zv']
    Zi = params['Zi']
    rho = params['dislocation_density']

    # 点缺陷产生率 (Point defect production rate)
    phi = params['fission_rate'] * params['displacement_rate']

    # 复合系数 (Recombination coefficient, from Eqs. 17-18)
    alpha = 4 * np.pi * params['recombination_radius'] * (Dv + Di) / params['Omega']

    # 计算汇聚强度 (Calculate sink strengths)
    sink_strengths = calculate_sink_strengths(
        Rcb_safe, Rcf_safe, Ccb, Ccf, Zv, Zi, rho
    )

    # 计算点缺陷浓度变化率 (Calculate point defect derivatives)
    dcvb_dt, dcib_dt, dcvf_dt, dcif_dt = calculate_point_defect_derivatives(
        cvb, cib, cvf, cif,
        sink_strengths['kvb2_total'], sink_strengths['kib2_total'],
        sink_strengths['kvf2_total'], sink_strengths['kif2_total'],
        Dv, Di, phi, alpha
    )

    # 计算热平衡空位浓度 (Calculate thermal equilibrium vacancy concentration, Eq. 16)
    cv0 = calculate_cv0(
        temperature=T,
        Evf_coeffs=params['Evf_coeffs'],
        kB_ev=kB_ev,
        Evfmuti=params.get('Evfmuti', 1.0),
    )

    # 计算空腔半径变化率 (Calculate cavity radius derivatives)
    dRcb_dt, dRcf_dt, cv_star_b, cv_star_f = calculate_cavity_radius_derivatives(
        Rcb_safe, Rcf_safe, Ccb, Ccf, cvb, cib, cvf, cif,
        Ncb, Ncf, cv0,
        sink_strengths['kvc2_b'], sink_strengths['kic2_b'],
        sink_strengths['kvc2_f'], sink_strengths['kic2_f'],
        Dv, Di,
        T, kB_J,
        params['surface_energy'],
        params['hydrastatic_pressure'],
        params['Omega'],
        params.get('eos_model', 'ideal')
    )

    # 计算气体浓度变化率 (Calculate gas concentration derivatives)
    dCgb_dt, dCcb_dt, dNcb_dt, dCgf_dt, dCcf_dt, dNcf_dt, dh_dt = \
        calculate_gas_concentration_derivatives(
            Cgb, Ccb, Ncb, Cgf, Ccf, Ncf, Rcb_safe, Rcf_safe,
            params['grain_diameter'], Dgb, Dgf,
            params['fission_rate'],
            params['gas_production_rate'],
            params['resolution_rate'],
            params['Fnb'], params['Fnf'],
            params['Xe_radii'],
            params.get('eos_model', 'ideal'),
            T, kB_J, params['Omega']
        )

    # 组装导数数组 (Assemble derivative array, 17 components)
    # 汇聚强度参数的导数为零 (Sink strength derivatives are zero)
    derivatives = np.array([
        np.clip(dCgb_dt, -1e20, 1e20),     # 0: dCgb_dt
        np.clip(dCcb_dt, -1e20, 1e20),     # 1: dCcb_dt
        np.clip(dNcb_dt, -1e8, 1e8),       # 2: dNcb_dt
        np.clip(dRcb_dt, 0, 1e5),          # 3: dRcb_dt (只能增长, can only grow)
        np.clip(dCgf_dt, -1e20, 5e20),     # 4: dCgf_dt
        np.clip(dCcf_dt, -1e20, 5e20),     # 5: dCcf_dt
        np.clip(dNcf_dt, -1e8, 1e8),       # 6: dNcf_dt
        np.clip(dRcf_dt, 0, 1e5),          # 7: dRcf_dt (只能增长, can only grow)
        np.clip(dcvb_dt, -1e8, 5e20),      # 8: dcvb_dt
        np.clip(dcib_dt, -1e8, 5e20),      # 9: dcib_dt
        np.clip(dcvf_dt, -1e8, 1e8),       # 10: dcvf_dt
        np.clip(dcif_dt, -1e8, 1e8),       # 11: dcif_dt
        np.clip(dh_dt, -1e30, 1e30),       # 12: dh_dt (released_gas)
        0.0,                                # 13: dkvb_dt (常数, constant)
        0.0,                                # 14: dkib_dt (常数, constant)
        0.0,                                # 15: dkvf_dt (常数, constant)
        0.0                                 # 16: dkif_dt (常数, constant)
    ])

    # 处理NaN和Inf (Handle NaN and Inf)
    derivatives = np.where(np.isnan(derivatives), 0.0, derivatives)
    derivatives = np.where(np.isinf(derivatives), 1e10 * np.sign(derivatives), derivatives)

    return derivatives


if __name__ == '__main__':
    """测试ODE系统 (Test ODE system)"""
    from ..params.parameters import create_default_parameters

    # 创建参数 (Create parameters)
    params = create_default_parameters()

    # 初始状态 (Initial state, 17 variables)
    y0 = np.array([
        1e20,   # Cgb: 基体气体浓度 (bulk gas concentration)
        1e18,   # Ccb: 基体空腔浓度 (bulk cavity concentration)
        4.0,    # Ncb: 每个基体空腔气体原子数 (gas atoms per bulk cavity)
        1e-9,   # Rcb: 基体空腔半径 (bulk cavity radius)
        1e20,   # Cgf: 晶界气体浓度 (boundary gas concentration)
        1e18,   # Ccf: 晶界空腔浓度 (boundary cavity concentration)
        4.0,    # Ncf: 每个晶界空腔气体原子数 (gas atoms per boundary cavity)
        1e-9,   # Rcf: 晶界空腔半径 (boundary cavity radius)
        1e-6,   # cvb: 基体空位浓度 (bulk vacancy concentration)
        1e-10,  # cib: 基体间隙原子浓度 (bulk interstitial concentration)
        1e-6,   # cvf: 晶界空位浓度 (boundary vacancy concentration)
        1e-10,  # cif: 晶界间隙原子浓度 (boundary interstitial concentration)
        0.0,    # released_gas: 累积释放气体 (cumulative released gas)
        0.0, 0.0, 0.0, 0.0  # kvb, kib, kvf, kif: 汇聚强度 (sink strengths)
    ])

    # 计算导数 (Calculate derivatives)
    t = 0.0
    dydt = swelling_ode_system(t, y0, params)

    print("ODE系统测试 (ODE System Test)")
    print("=" * 60)
    print(f"时间 (Time): {t} s")
    print(f"温度 (Temperature): {params['temperature']} K")
    print("\n状态变量 (State Variables):")
    print(f"  Cgb: {y0[0]:.3e} atoms/m³")
    print(f"  Ccb: {y0[1]:.3e} cavities/m³")
    print(f"  Ncb: {y0[2]:.3f} atoms/cavity")
    print(f"  Rcb: {y0[3]:.3e} m")
    print(f"  Cgf: {y0[4]:.3e} atoms/m³")
    print(f"  Ccf: {y0[5]:.3e} cavities/m³")
    print(f"  Ncf: {y0[6]:.3f} atoms/cavity")
    print(f"  Rcf: {y0[7]:.3e} m")
    print("\n导数 (Derivatives):")
    print(f"  dCgb/dt: {dydt[0]:.3e} atoms/m³/s")
    print(f"  dCcb/dt: {dydt[1]:.3e} cavities/m³/s")
    print(f"  dNcb/dt: {dydt[2]:.3e} atoms/cavity/s")
    print(f"  dRcb/dt: {dydt[3]:.3e} m/s")
    print(f"  dCgf/dt: {dydt[4]:.3e} atoms/m³/s")
    print(f"  dCcf/dt: {dydt[5]:.3e} cavities/m³/s")
    print(f"  dNcf/dt: {dydt[6]:.3e} atoms/cavity/s")
    print(f"  dRcf/dt: {dydt[7]:.3e} m/s")
    print("=" * 60)
    print("ODE模块测试通过！(ODE module test passed!)")
