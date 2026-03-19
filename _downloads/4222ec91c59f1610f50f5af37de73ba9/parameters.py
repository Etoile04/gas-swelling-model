import numpy as np
from dataclasses import dataclass, field # Import field
from typing import Dict, List

# 物理常数
BOLTZMANN_CONSTANT_EV = 8.617e-5  # eV/K - 保留用于原始能量单位计算
BOLTZMANN_CONSTANT_J = 1.380649e-23 # J/K - 用于EOS计算
GAS_CONSTANT = 8.314462618 # J/(mol·K)
AVOGADRO_CONSTANT = 6.02214076e23 # mol^-1


@dataclass
class MaterialParameters:
    """材料参数（表1和表2中的参数）"""
    # 晶格常数
    lattice_constant: float = 3.4808e-10  # m, 铀锆合金晶格常数
    ATOMIC_VOLUME: float = 4.09e-29  # m^3, volume of Uranium atoms
    # 跃迁频率
    nu_constant: float = 7.8e12  # s^-1
    # 空位扩散参数
    Dv0: float = 2.0e-8  # m^2/s
    Evm: float = 0.74 # eV, 空位迁移能
    # Evf = C0 + C1*T (eV)
    Evf_coeffs: List[float] = field(default_factory=lambda: [1.034, 7.6e-4]) # 空位形成能系数
    Evfmuti: float = 1.0

    # 位错参数
    Zv: float = 1.0  # 空位偏压因子
    Zi: float = 1.025  # 间隙原子偏压因子
    dislocation_density: float = 7.0e13  # m^-2
    
    # 表面能
    surface_energy: float = 0.5  # J/m^2, Ref. Rest, FissionGasBubble(1992)

    # 静水压
    hydrastatic_pressure: float = 0.0E8  # Pa
    
    # 气泡成核因子
    Fnb: float = 1e-5  # 晶内成核因子, 调整为推荐值
    Fnf: float = 1e-5  # 相界成核因子, 调整为推荐值
    
    # 复合参数
    recombination_radius: float = 2.0e-10  # m

    # Interstitial (SIA) 参数
    Di0: float = 1.259e-12 # m^2/s, SIA 扩散系数前因子(人为调整到1/10)
    Eim: float = 1.18    # eV, SIA 迁移能
    # SIA 形成能系数 Eif = C0 + C1*T + C2*T^2 + C3*T^3 (eV)
    Eif_coeffs: List[float] = field(default_factory=lambda: [-3.992, 0.038, -7.645e-5, 5.213e-8])

    # Cavity sink strength parameters (公式21,22中的k_v, k_i)
    kv_param: float = np.sqrt(Zv* dislocation_density)  # 默认为0，忽略二阶项
    ki_param: float = np.sqrt(Zi* dislocation_density) 

    # Xenon (Xe) 参数
    Xe_radii: float = 2.16e-10  # Xe 原子半径,m
    xe_epsilon_k: float = 290.0 # K, L-J 势阱深度
    xe_sigma: float = 3.86e-10 # m, L-J 碰撞直径
    xe_mass: float = 0.131293  # kg/mol, Xe 原子质量
    xe_Tc: float = 290.0 # K, 临界温度
    xe_dc: float = 1.103e3 # kg/m^3, 临界密度
    xe_Vc: float = 35.92e-6 # m^3/mol, 临界体积
    xe_q_coeffs: List[float] = field(default_factory=lambda: [2.12748, 0.52905, 0.13053, 0.02697, 0.00313]) # f(T) 系数 q_n (n=1 to 5)


@dataclass
class SimulationParameters:
    """模拟参数"""
    # 用户提供的参数
    fission_rate: float = 2e20  # 2e20, fissions/m^3/s, Ref. JNM 583 (2023) 154542
    displacement_rate: float = 14825/5.12e28   # frankel pairs per fissions/m^3   
    sigma_f: float = 2.72e4  # m^-1
    gas_production_rate: float = 0.25  # 气体生成率因子
    resolution_rate: float = 2e-5  # 重溶率，s^-1
    grain_diameter: float = 0.5e-6  # m, 晶粒直径
    
    # 运行温度
    temperature: float = 600  # K
    
    # 计算参数
    time_step: float = 1e-9  # s, 调整为推荐的初始步长
    max_time_step: float = 1e2  # s, 调整为推荐的最大步长
    max_time: float = 3600 * 24 *100  # s, 最大模拟时间, 100天

    # 自适应步长控制参数
    adaptive_stepping_enabled: bool = False  # 是否启用自适应步长控制
    min_step: float = 1e-9  # s, 最小时间步长
    max_step: float = 1e2  # s, 最大时间步长
    show_progress: bool = True  # 是否显示进度指示器
    progress_interval: int = 100  # 每N步输出一次进度

    # 气体扩散系数参数
    Dgb_prefactor: float = 1.2e-7  # 晶内扩散系数前因子
    Dgb_activation_energy: float = 1.16  # eV, 晶内扩散激活能
    Dgb_fission_term: float = 5.07e-31  # 裂变相关项系数
    
    # 相界扩散系数是晶内的30000倍 (Dgf = Dgb * 3e4)
    Dgf_multiplier: float = 3e2

    # Gas Equation of State Model ('ideal' or 'ronchi')
    eos_model: str = 'ideal' # Default to ideal gas law

def create_default_parameters() -> Dict:
    """创建默认参数集合"""
    material = MaterialParameters()
    sim = SimulationParameters()
    
    # 计算气体扩散系数 (使用 eV/K 的 kB)
    Dgb = (sim.Dgb_prefactor * np.exp(-sim.Dgb_activation_energy / (BOLTZMANN_CONSTANT_EV * sim.temperature)) + \
          sim.Dgb_fission_term * sim.fission_rate)

    return {
        # 材料参数
        **material.__dict__,

        # 模拟参数
        **sim.__dict__,

        # 计算参数
        'Dgb': Dgb,  # 晶内气体扩散系数
        'Dgf': Dgb * sim.Dgf_multiplier,  # 相界气体扩散系数

        # 物理常数
        'kB_ev': BOLTZMANN_CONSTANT_EV, # Boltzmann constant in eV/K
        'kB': BOLTZMANN_CONSTANT_J,     # Boltzmann constant in J/K
        'R': GAS_CONSTANT,              # Gas constant in J/(mol·K)
        'Av': AVOGADRO_CONSTANT,        # Avogadro constant in mol^-1
        'Omega': material.ATOMIC_VOLUME 
    }

if __name__ == '__main__':
    # 测试参数生成
    params = create_default_parameters()
    print("默认参数:")
    for key, value in params.items():
        print(f"{key}: {value}")
