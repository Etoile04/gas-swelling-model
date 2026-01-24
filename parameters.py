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
    """材料参数数据类（表1和表2中的参数）

    该数据类包含模拟U-Zr和U-Pu-Zr核燃料材料裂变气体气泡演化所需的
    所有材料物理参数。参数涵盖了晶体结构、扩散性质、缺陷动力学、
    表面能和气体状态方程等方面。

    属性:
        lattice_constant: 晶格常数，用于计算原子间距和扩散距离。
            单位: m (米)，默认值: 3.4808e-10 m (铀锆合金)

        ATOMIC_VOLUME: 铀原子的体积，用于计算原子密度和浓度转换。
            单位: m³ (立方米)，默认值: 4.09e-29 m³

        nu_constant: 原子跃迁尝试频率，表示原子尝试跃迁到相邻位置的频率。
            单位: s⁻¹ (每秒)，默认值: 7.8e12 s⁻¹
            物理意义: 决定扩散系数的前指数因子

        Dv0: 空位扩散系数的前指数因子，用于计算温度依赖的空位扩散系数。
            单位: m²/s，默认值: 2.0e-8 m²/s
            物理意义: 空位在晶格中的迁移能力

        Evm: 空位迁移能，空位从一个位置跃迁到相邻位置所需的能量。
            单位: eV (电子伏特)，默认值: 0.74 eV
            物理意义: 控制空位扩散的阿伦尼乌斯温度依赖性

        Evf_coeffs: 空位形成能的温度系数数组，用于计算温度依赖的空位形成能。
            公式: Evf = C0 + C1*T (eV)
            单位: eV 和 eV/K，默认值: [1.034, 7.6e-4]
            物理意义: 在不同温度下形成空位所需的能量

        Evfmuti: 空位形成能的修正因子，用于调整空位形成能以匹配实验数据。
            无量纲，默认值: 1.0
            物理意义: 经验修正参数，用于模型校准

        Zv: 空位的位错偏压因子，表示位错对空位的吸引强度。
            无量纲，默认值: 1.0
            物理意义: 决定位错作为空位汇的效率，影响空位浓度分布

        Zi: 间隙原子(SIA)的位错偏压因子，表示位错对间隙原子的吸引强度。
            无量纲，默认值: 1.025
            物理意义: 通常Zi > Zv，导致间隙原子更倾向于被位错吸收，
                     这是驱动空位肿胀的偏压机制基础

        dislocation_density: 位错密度，单位体积内的位错线长度。
            单位: m⁻²，默认值: 7.0e13 m⁻²
            物理意义: 位错作为缺陷汇的强度，直接影响缺陷复合和气泡生长速率

        surface_energy: 材料的表面能，气泡-基体界面的能量密度。
            单位: J/m²，默认值: 0.5 J/m²
            参考文献: Rest, FissionGasBubble(1992)
            物理意义: 控制气泡的临界半径和稳定性，表面能越大，
                     气泡越难生长，对抑制肿胀有重要作用

        hydrastatic_pressure: 外部施加的静水压力。
            单位: Pa (帕斯卡)，默认值: 0.0 Pa
            物理意义: 外部压力会抑制气泡生长，实际燃料棒中存在
                     冷却剂压力和裂变气体压力的竞争

        Fnb: 基体(bulk)中的气泡成核因子，控制新气泡在晶粒内部形成的速率。
            无量纲，默认值: 1e-5
            物理意义: 较小的Fnb值意味着成核受到抑制，气泡倾向于
                     在已存在的气泡上生长而非形成新气泡

        Fnf: 相界面(phase boundary)处的气泡成核因子，控制新气泡在
             晶界和相界形成的速率。
            无量纲，默认值: 1e-5
            物理意义: 晶界通常是气泡优先成核位置，Fnf影响晶界气泡
                     的数量和气体在晶界的富集程度

        recombination_radius: 空位-间隙原子复合的反应半径。
            单位: m，默认值: 2.0e-10 m (约2埃)
            物理意义: 当空位和间隙原子距离小于此值时发生复合消失，
                     是控制缺陷浓度的关键参数

        Di0: 间隙原子(SIA)扩散系数的前指数因子。
            单位: m²/s，默认值: 1.259e-12 m²/s
            注: 已人为调整到原始值的1/10以匹配实验数据
            物理意义: 间隙原子迁移极快，扩散系数远大于空位

        Eim: 间隙原子迁移能，SIA跃迁所需的能量。
            单位: eV，默认值: 1.18 eV
            物理意义: 虽然迁移能较高，但前指数因子大，使得SIA扩散
                     仍比空位快得多

        Eif_coeffs: 间隙原子形成能的温度系数数组，用于计算温度依赖的SIA形成能。
            公式: Eif = C0 + C1*T + C2*T² + C3*T³ (eV)
            单位: eV, eV/K, eV/K², eV/K³
            默认值: [-3.992, 0.038, -7.645e-5, 5.213e-8]
            物理意义: SIA形成能随温度非线性变化，影响热平衡浓度

        kv_param: 空位的位错汇强度参数。
            单位: m⁻¹，计算公式: √(Zv × ρ)，其中ρ为位错密度
            物理意义: 出现在速率方程中，表征位错吸收空位的效率
                     (公式21, 22)

        ki_param: 间隙原子的位错汇强度参数。
            单位: m⁻¹，计算公式: √(Zi × ρ)，其中ρ为位错密度
            物理意义: 出现在速率方程中，表征位错吸收间隙原子的效率
                     (公式21, 22)

        Xe_radii: 氙(Xe)原子的原子半径。
            单位: m，默认值: 2.16e-10 m
            物理意义: 用于计算气泡内气体原子的体积占有和硬球模型

        xe_epsilon_k: 氙气Lennard-Jones势函数的势阱深度。
            单位: K (开尔文温度)，默认值: 290.0 K
            物理意义: 表征Xe原子间的分子间作用力强度，用于范德华
                     状态方程计算

        xe_sigma: 氙气Lennard-Jones势函数的碰撞直径(零势能距离)。
            单位: m，默认值: 3.86e-10 m
            物理意义: Xe原子的有效直径，用于硬球模型和分子间作用力计算

        xe_mass: 氙原子的摩尔质量。
            单位: kg/mol，默认值: 0.131293 kg/mol
            物理意义: 用于计算气泡内气体的质量和状态方程

        xe_Tc: 氙气的临界温度(气体液化的最高温度)。
            单位: K，默认值: 290.0 K
            物理意义: 在Ronchi状态方程中作为参考温度，用于计算
                     压缩因子

        xe_dc: 氙气的临界密度(临界点处的密度)。
            单位: kg/m³，默认值: 1.103e3 kg/m³
            物理意义: 在Ronchi状态方程中用于无量纲化密度

        xe_Vc: 氙气的临界摩尔体积(临界点处的摩尔体积)。
            单位: m³/mol，默认值: 35.92e-6 m³/mol
            物理意义: 在状态方程中作为参考体积

        xe_q_coeffs: Ronchi状态方程中温度函数f(T)的系数数组。
            公式: f(T) = Σ(q_n × τ^n)，其中τ = Tc/T
            单位: 无量纲系数，默认值: [2.12748, 0.52905, 0.13053, 0.02697, 0.00313]
            物理意义: 这些经验系数使得Ronchi状态方程能够准确描述
                     高压下氙气的非理想气体行为
    """
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
    """模拟参数数据类

    该数据类包含控制气体肿胀模型数值模拟过程的所有参数。
    这些参数定义了裂变反应条件、材料辐照环境、时间积分策略、
    气体输运性质以及气体状态方程模型选择。

    属性:
        fission_rate: 裂变率密度，单位体积内每秒发生的裂变事件数。
            单位: fissions/(m³·s)，默认值: 2×10²⁰ fissions/(m³·s)
            参考文献: JNM 583 (2023) 154542
            物理意义: 决定气体原子产生速率和缺陷产生速率的核心参数，
                     直接影响气泡成核和生长速率

        displacement_rate: 置换率密度，每次裂变产生的弗兰克尔缺陷对数量。
            单位: dpa/(fission·m³)，默认值: 14825/5.12×10²⁸
            物理意义: 每次裂变事件产生的空位和间隙原子数量，
                     控制辐照缺陷的总量

        sigma_f: 宏观裂变截面，中子与材料发生裂变反应的概率度量。
            单位: m⁻¹，默认值: 2.72×10⁴ m⁻¹
            物理意义: 材料对裂变中子的反应截面，影响裂变率计算

        gas_production_rate: 气体原子产生率因子，每次裂变产生的气体原子数。
            无量纲，默认值: 0.25 (每次裂变产生0.25个气体原子)
            物理意义: 典型铀燃料中，每次裂变约产生0.25-0.30个氙/氪原子，
                     是气体肿胀的源头

        resolution_rate: 气泡重溶率，裂变碎片穿过气泡使气体原子重新回到基体的速率。
            单位: s⁻¹，默认值: 2×10⁻⁵ s⁻¹
            物理意义: 裂变碎片撞击气泡会将气体原子"踢"回基体，
                     抑制气泡过度生长，是重要的负反馈机制

        grain_diameter: 燃料晶粒的平均直径。
            单位: m，默认值: 0.5 μm (5×10⁻⁷ m)
            物理意义: 晶粒尺寸影响晶界面积和气体在晶界的富集程度，
                     较小的晶粒提供更多晶界汇，促进气体释放

        temperature: 燃料运行温度。
            单位: K (开尔文)，默认值: 600 K
            物理意义: 温度通过阿伦尼乌斯关系强烈影响扩散系数，
                     控制气体迁移、缺陷复合和气泡生长速率，
                     肿胀率在700-800K附近呈现峰值

        time_step: 数值积分的初始时间步长。
            单位: s (秒)，默认值: 1×10⁻⁹ s
            注: 使用自适应RK23方法，步长会自动调整
            物理意义: 初始步长需要足够小以捕捉快速过程(缺陷复合)，
                     自适应算法会在稳定过程中增大步长以提高效率

        max_time_step: 数值积分的最大允许时间步长。
            单位: s，默认值: 1×10² s (100秒)
            物理意义: 限制步长上限以确保数值稳定性，
                     防止在缓慢变化过程中步长过大导致精度损失

        max_time: 模拟的总时长。
            单位: s，默认值: 3600×24×100 s (100天)
            物理意义: 定义模拟的燃料燃耗时间，
                     100天对应约5-10 at.%燃耗(取决于裂变率)

        Dgb_prefactor: 基体(bulk)中气体原子扩散系数的前指数因子。
            单位: m²/s，默认值: 1.2×10⁻⁷ m²/s
            物理意义: 扩散系数 D = D0 × exp(-Q/kT) 中的D0项，
                     控制扩散的绝对速率

        Dgb_activation_energy: 基体中气体原子扩散的激活能。
            单位: eV (电子伏特)，默认值: 1.16 eV
            物理意义: 气体原子在晶格中迁移需要克服的能量势垒，
                     与温度共同决定扩散系数的温度依赖性

        Dgb_fission_term: 裂变对气体扩散的增强项系数。
            单位: (fissions·m²)⁻¹，默认值: 5.07×10⁻³¹ (fissions·m²)⁻¹
            物理意义: 裂变碎片产生的级联碰撞会额外增强气体扩散，
                     该项正比于裂变率，在高中子通量下显著

        Dgf_multiplier: 相界面(phase boundary)扩散系数相对于基体的倍数。
            无量纲，默认值: 300 (Dgf = Dgb × 300)
            物理意义: 晶界和相界处的原子排列更开放，气体扩散速度
                     显著快于晶内，促进气体向晶界富集和释放

        eos_model: 气体状态方程模型，用于计算气泡内气体压力。
            类型: str，可选值: 'ideal' 或 'ronchi'，默认值: 'ideal'
            物理意义:
                - 'ideal': 理想气体状态方程 P = nRT/V，适用于低压气泡
                - 'ronchi': Ronchi修正状态方程，考虑高密度氙气的
                            非理想行为，适用于高压小气泡
    """
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

    # 气体扩散系数参数
    Dgb_prefactor: float = 1.2e-7  # 晶内扩散系数前因子
    Dgb_activation_energy: float = 1.16  # eV, 晶内扩散激活能
    Dgb_fission_term: float = 5.07e-31  # 裂变相关项系数

    # 相界扩散系数是晶内的30000倍 (Dgf = Dgb * 3e4)
    Dgf_multiplier: float = 3e2

    # Gas Equation of State Model ('ideal' or 'ronchi')
    eos_model: str = 'ideal' # Default to ideal gas law

def create_default_parameters() -> Dict:
    """创建默认参数集合

    该函数初始化并返回包含所有材料参数、模拟参数、计算参数和物理常数的
    完整参数字典。默认参数基于U-Zr和U-Pu-Zr核燃料材料的典型实验值和文献数据，
    适用于裂变气体气泡演化和肿胀模拟的标准场景。

    函数执行以下操作:
        1. 创建MaterialParameters实例，包含晶体结构、扩散性质、缺陷动力学等
           材料物理参数(表1和表2参数)
        2. 创建SimulationParameters实例，包含裂变条件、温度、时间步长等
           模拟控制参数
        3. 根据温度计算温度依赖的气体扩散系数Dgb，包含晶格扩散和裂变增强项
        4. 计算相界气体扩散系数Dgf = Dgb × Dgf_multiplier
        5. 将所有参数合并为单一字典，便于传递给GasSwellingModel

    Returns:
        Dict: 包含以下类别的参数字典:

            **材料参数** (来自MaterialParameters):
                - lattice_constant, ATOMIC_VOLUME, nu_constant
                - Dv0, Evm, Evf_coeffs, Evfmuti (空位参数)
                - Zv, Zi, dislocation_density (位错参数)
                - surface_energy, hydrastatic_pressure
                - Fnb, Fnf (成核因子)
                - recombination_radius
                - Di0, Eim, Eif_coeffs (SIA参数)
                - kv_param, ki_param (位错汇强度)
                - Xe_radii, xe_epsilon_k, xe_sigma, xe_mass (氙气参数)
                - xe_Tc, xe_dc, xe_Vc, xe_q_coeffs (状态方程参数)

            **模拟参数** (来自SimulationParameters):
                - fission_rate, displacement_rate, sigma_f
                - gas_production_rate, resolution_rate
                - grain_diameter, temperature
                - time_step, max_time_step, max_time
                - Dgb_prefactor, Dgb_activation_energy, Dgb_fission_term
                - Dgf_multiplier, eos_model

            **计算参数** (温度相关):
                - Dgb (float): 晶内气体扩散系数，单位: m²/s
                  计算公式: Dgb = Dgb_prefactor × exp(-Q/kT) + Dgb_fission_term × fission_rate
                  物理意义: 气体原子在晶格内的迁移能力，控制气泡生长速率

                - Dgf (float): 相界气体扩散系数，单位: m²/s
                  计算公式: Dgf = Dgb × Dgf_multiplier
                  物理意义: 气体原子在晶界和相界的迁移速度，通常远大于晶内扩散

            **物理常数**:
                - kB_ev (float): 玻尔兹曼常数，单位: eV/K，用于能量计算
                - kB (float): 玻尔兹曼常数，单位: J/K，用于状态方程
                - R (float): 气体常数，单位: J/(mol·K)，用于摩尔气体计算
                - Av (float): 阿伏伽德罗常数，单位: mol⁻¹，用于单位转换
                - Omega (float): 铀原子体积，单位: m³，用于浓度-体积转换

    Examples:
        >>> from parameters import create_default_parameters
        >>> params = create_default_parameters()
        >>> # 访问材料参数
        >>> temperature = params['temperature']  # 运行温度 (K)
        >>> fission_rate = params['fission_rate']  # 裂变率 (fissions/m³/s)
        >>> # 访问计算参数
        >>> Dgb = params['Dgb']  # 晶内气体扩散系数 (m²/s)
        >>> Dgf = params['Dgf']  # 相界气体扩散系数 (m²/s)
        >>> # 访问物理常数
        >>> kB = params['kB']  # 玻尔兹曼常数 (J/K)
        >>> print(f"温度: {temperature} K, 扩散系数: {Dgb:.2e} m²/s")
        温度: 600 K, 扩散系数: 1.01e-10 m²/s

    Notes:
        - 默认参数适用于U-10Zr合金在600 K、中等裂变率条件下的标准模拟
        - 气体扩散系数包含裂变增强项，在高裂变率下显著
        - 如需修改参数，可在返回字典后直接修改，或创建自定义MaterialParameters
          和SimulationParameters实例
        - 参数值主要来源于以下文献:
            * Rest, J. Fission Gas Bubble (1992) - 表面能参数
            * JNM 583 (2023) 154542 - 裂变率和气体产生数据
            * 原始论文 Table 1, 2 - 扩散和缺陷参数
    """
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
