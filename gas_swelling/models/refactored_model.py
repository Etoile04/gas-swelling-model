"""
Refactored Gas Swelling Model (重构的气体肿胀模型)

This module provides a refactored implementation of the gas swelling model
that uses modular components for better maintainability and testability.

模块结构 (Module Structure):
- Uses physics module for pressure, transport, and thermal calculations
- Uses ode module for rate equation system
- Uses solvers module for numerical integration
- Uses io module for debug output and visualization

主要类 (Main Classes):
- RefactoredGasSwellingModel: 重构的气体肿胀模型类

使用示例 (Usage Example):
    >>> from gas_swelling.models.refactored_model import RefactoredGasSwellingModel
    >>> from gas_swelling.params.parameters import create_default_parameters
    >>>
    >>> # Create model with custom parameters
    >>> params = create_default_parameters()
    >>> params['temperature'] = 773.15  # 500°C in Kelvin
    >>> model = RefactoredGasSwellingModel(params)
    >>>
    >>> # Solve simulation
    >>> results = model.solve(t_span=(0, 8640000), t_eval=time_points)
    >>>
    >>> # Access results
    >>> swelling = results['swelling']
    >>> bubble_radius = results['Rcb']
"""

import numpy as np
from typing import Optional, Dict, Tuple
from ..params.parameters import create_default_parameters
from ..physics import (
    calculate_gas_pressure,
    calculate_gas_influx,
    calculate_gas_release_rate,
    calculate_cv0,
    calculate_ci0
)
from ..ode import swelling_ode_system
from ..solvers import RK23Solver
from ..io import (
    DebugConfig,
    DebugHistory,
    update_debug_history,
    print_simulation_summary
)

# Physical constants (物理常数)
BOLTZMANN_CONSTANT_J = 1.380649e-23  # J/K (玻尔兹曼常数)


class RefactoredGasSwellingModel:
    """
    重构的气体肿胀模型类 (Refactored Gas Swelling Model Class)

    This class provides a modular implementation of the gas swelling model
    for nuclear fuel materials. It uses separated physics calculations,
    ODE system, numerical solvers, and I/O utilities.

    模型功能 (Model Features):
    - 求解17个状态变量的常微分方程组 (solves 17-state-variable ODE system)
    - 计算气体气泡演化 (calculates gas bubble evolution)
    - 计算肿胀率 (calculates swelling rate)
    - 支持多种气体状态方程 (supports multiple gas EOS models)
    - 提供调试输出和可视化 (provides debug output and visualization)

    状态变量 (State Variables - 17 total):
    0-7: Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf (gas and cavity variables)
    8-15: cvb, cib, kvb, kib, cvf, cif, kvf, kif (point defect variables)
    16: released_gas (cumulative gas release)

    参数 (Parameters):
        params : Optional[Dict]
            模型参数字典 (model parameter dictionary)
            如果为None，使用默认参数 (use default parameters if None)

    属性 (Attributes):
        params : Dict
            模型参数 (model parameters)
        initial_state : np.ndarray
            初始状态向量 (initial state vector)
        debug_config : DebugConfig
            调试配置 (debug configuration)
        debug_history : DebugHistory
            调试历史记录 (debug history)
    """

    def __init__(self, params: Optional[Dict] = None):
        """
        初始化重构的气体肿胀模型 (Initialize refactored gas swelling model)

        参数 (Parameters):
            params : Optional[Dict]
                模型参数字典，如果为None则使用默认参数
                (model parameter dictionary, use default if None)

        示例 (Example):
            >>> params = create_default_parameters()
            >>> params['temperature'] = 773.15
            >>> model = RefactoredGasSwellingModel(params)
        """
        # 设置模型参数 (set model parameters)
        self.params = params if params else create_default_parameters()

        # 设置默认值（如果未提供）(set defaults if not provided)
        self.params.setdefault('Zvc', 1.0)  # Cavity bias for vacancy
        self.params.setdefault('Zic', 1.0)  # Cavity bias for interstitial

        # 初始化状态向量 (initialize state vector)
        self.initial_state = self._initialize_state()

        # 初始化调试系统 (initialize debug system)
        self.debug_config = DebugConfig(
            enabled=False,
            time_step_interval=1000,
            save_to_file=False,
            output_file=None
        )
        self.debug_history = DebugHistory()

        # 求解器状态标志 (solver status flags)
        self.solver_success = True
        self.current_time = 0.0

    def _equations(self, t: float, state: np.ndarray) -> np.ndarray:
        """
        ODE方程方法别名 (ODE equations method alias)

        This is an alias for _equations_wrapper to maintain backward compatibility
        with existing tests.

        这是_equations_wrapper的别名，用于保持与现有测试的向后兼容性。

        参数 (Parameters):
            t : float
                当前时间 (current time)
            state : np.ndarray
                状态向量 (state vector)

        返回 (Returns):
            np.ndarray: 状态导数向量 (state derivative vector)
        """
        return self._equations_wrapper(t, state)

    def _initialize_state(self) -> np.ndarray:
        """
        初始化状态变量 (Initialize state variables)

        返回包含17个元素的初始状态向量 (Returns initial state vector with 17 elements):
        - 气体浓度 (gas concentrations): Cgb, Cgf
        - 空腔浓度 (cavity concentrations): Ccb, Ccf
        - 每个空腔气体原子数 (atoms per cavity): Ncb, Ncf
        - 空腔半径 (cavity radii): Rcb, Rcf
        - 点缺陷浓度 (point defect concentrations): cvb, cib, cvf, cif
        - 点缺陷汇聚强度 (point defect sink strengths): kvb, kib, kvf, kif
        - 累积释放气体 (cumulative released gas): released_gas

        返回 (Returns):
            np.ndarray: 17个元素的初始状态向量 (17-element initial state vector)

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> state = model.initial_state
            >>> print(f"Initial bulk gas concentration: {state[0]}")
        """
        # 初始气泡参数 (initial bubble parameters)
        Nc_init = 5.0      # 初始气泡内气体数 (initial atoms per bubble)
        Cg_init = 0.0      # 初始气体浓度 (initial gas concentration, atoms/m³)
        Cc_init = 0.0      # 初始气腔浓度 (initial cavity concentration, cavities/m³)
        R_init = 1e-8      # 初始半径 (initial radius, 10 nm)

        # 计算热平衡点缺陷浓度 (calculate thermal equilibrium defect concentrations)
        cv0 = calculate_cv0(
            temperature=self.params['temperature'],
            Evf_coeffs=self.params['Evf_coeffs'],
            kB_ev=self.params['kB_ev'],
            Evfmuti=self.params.get('Evfmuti', 1.0)
        )
        ci0 = calculate_ci0(
            temperature=self.params['temperature'],
            Eif_coeffs=self.params['Eif_coeffs'],
            kB_ev=self.params['kB_ev']
        )

        # 初始汇聚强度参数 (initial sink strength parameters)
        kv_param = self.params['kv_param']
        ki_param = self.params['ki_param']

        # 构建状态向量 (construct state vector)
        # State vector: [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf,
        #                 cvb, cib, cvf, cif, released_gas, kvb, kib, kvf, kif]
        return np.array([
            Cg_init,     # 0: Cgb - 基体气体浓度 (bulk gas concentration)
            Cc_init,     # 1: Ccb - 基体气腔浓度 (bulk cavity concentration)
            Nc_init,     # 2: Ncb - 基体每个气腔气体原子数 (atoms per bulk cavity)
            R_init,      # 3: Rcb - 基体气腔半径 (bulk cavity radius)
            Cg_init,     # 4: Cgf - 晶界气体浓度 (grain boundary gas concentration)
            Cc_init,     # 5: Ccf - 晶界气腔浓度 (grain boundary cavity concentration)
            Nc_init,     # 6: Ncf - 晶界每个气腔气体原子数 (atoms per boundary cavity)
            R_init,      # 7: Rcf - 晶界气腔半径 (boundary cavity radius)
            cv0,         # 8: cvb - 基体空位浓度 (bulk vacancy concentration)
            ci0,         # 9: cib - 基体间隙原子浓度 (bulk interstitial concentration)
            cv0,         # 10: cvf - 晶界空位浓度 (boundary vacancy concentration)
            ci0,         # 11: cif - 晶界间隙原子浓度 (boundary interstitial concentration)
            0.0,         # 12: released_gas - 累积释放气体 (cumulative gas release)
            kv_param,    # 13: kvb - 基体空位汇聚强度 (bulk vacancy sink strength)
            ki_param,    # 14: kib - 基体间隙原子汇聚强度 (bulk interstitial sink strength)
            kv_param,    # 15: kvf - 晶界空位汇聚强度 (boundary vacancy sink strength)
            ki_param     # 16: kif - 晶界间隙原子汇聚强度 (boundary interstitial sink strength)
        ])

    def _equations_wrapper(self, t: float, state: np.ndarray, params: Dict = None) -> np.ndarray:
        """
        ODE方程包装器 (ODE equations wrapper)

        将内部状态向量转换为模块化ODE系统所需的格式
        (Converts internal state vector to format required by modular ODE system)

        参数 (Parameters):
            t : float
                当前时间 (current time)
            state : np.ndarray
                当前状态向量 (current state vector)
            params : Dict, optional
                参数字典（用于兼容RK23Solver接口）
                (parameter dictionary for RK23Solver compatibility)

        返回 (Returns):
            np.ndarray: 状态导数向量 (state derivative vector)

        注意 (Note):
            此方法作为适配器，连接模型的内部状态表示与模块化ODE系统
            (This method serves as an adapter, connecting model's internal state
             representation with the modular ODE system)
        """
        # 更新当前时间 (update current time)
        self.current_time = t

        # 使用模型参数（忽略传入的params参数）
        # (use model parameters, ignore passed params argument)
        model_params = self.params

        # 调用模块化ODE系统 (call modular ODE system)
        derivatives = swelling_ode_system(t, state, model_params)

        # 如果启用调试，记录调试信息 (record debug info if enabled)
        if self.debug_config.enabled:
            self._record_debug_info(t, state, derivatives)

        return derivatives

    def _record_debug_info(self, t: float, state: np.ndarray, derivatives: np.ndarray):
        """
        记录调试信息 (Record debug information)

        参数 (Parameters):
            t : float
                当前时间 (current time)
            state : np.ndarray
                当前状态向量 (current state vector)
            derivatives : np.ndarray
                状态导数向量 (state derivative vector)
        """
        # 解包状态变量 (unpack state variables)
        Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, kvb, kib, cvf, cif, kvf, kif, released_gas = state

        # 计算气体压力 (calculate gas pressures)
        eos_model = self.params.get('eos_model', 'virial')
        Pg_b = calculate_gas_pressure(Rcb, Ncb, self.params['temperature'], eos_model)
        Pg_f = calculate_gas_pressure(Rcf, Ncf, self.params['temperature'], eos_model)

        # 计算肿胀率 (calculate swelling)
        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        swelling = (V_bubble_b + V_bubble_f) * 100  # 百分比 (percentage)

        # 更新调试历史 (update debug history)
        update_debug_history(
            self.debug_history,
            time=t,
            Rcb=Rcb,
            Rcf=Rcf,
            Ncb=Ncb,
            Ncf=Ncf,
            Pg_b=Pg_b,
            Pg_f=Pg_f,
            swelling=swelling
        )

    def solve(self,
              t_span: Tuple[float, float] = (0, 7200000),
              t_eval: Optional[np.ndarray] = None,
              method: str = 'RK23',
              dt: float = 1e-9,
              max_dt: float = 100.0,
              max_steps: int = 1000000,
              output_interval: int = 1000,
              debug_enabled: bool = False) -> Dict:
        """
        求解气体肿胀微分方程组 (Solve gas swelling ODE system)

        使用数值方法求解气体肿胀演化的常微分方程组
        (Solves the ODE system for gas swelling evolution using numerical methods)

        参数 (Parameters):
            t_span : Tuple[float, float]
                时间跨度 (时间开始，时间结束)，单位：秒
                (time span (start, end) in seconds)
                默认值: (0, 7200000) = 0 to 83.33 days
            t_eval : Optional[np.ndarray]
                需要输出解的时间点 (time points for solution output)
                如果为None，求解器将自动选择输出点
                (if None, solver will automatically select output points)
            method : str
                求解方法 (solver method)
                - 'RK23': Runge-Kutta 2(3) 自适应方法 (default)
                - 'BDF': 适用于刚性系统 (suitable for stiff systems)
                默认值: 'RK23'
            dt : float
                初始时间步长，单位：秒 (initial time step in seconds)
                默认值: 1e-9
            max_dt : float
                最大时间步长，单位：秒 (maximum time step in seconds)
                默认值: 100.0
            max_steps : int
                最大步数 (maximum number of steps)
                默认值: 1000000
            output_interval : int
                调试输出间隔（步数）(debug output interval in steps)
                默认值: 1000
            debug_enabled : bool
                是否启用调试模式 (enable debug mode)
                默认值: False

        返回 (Returns):
            Dict: 包含求解结果的字典 (dictionary containing solution results)
                {
                    'time': np.ndarray,         # 时间点 (time points)
                    'Cgb': np.ndarray,          # 基体气体浓度 (bulk gas concentration)
                    'Ccb': np.ndarray,          # 基体气腔浓度 (bulk cavity concentration)
                    'Ncb': np.ndarray,          # 基体每个气腔气体原子数 (atoms per bulk cavity)
                    'Rcb': np.ndarray,          # 基体气腔半径 (bulk cavity radius)
                    'Cgf': np.ndarray,          # 晶界气体浓度 (boundary gas concentration)
                    'Ccf': np.ndarray,          # 晶界气腔浓度 (boundary cavity concentration)
                    'Ncf': np.ndarray,          # 晶界每个气腔气体原子数 (atoms per boundary cavity)
                    'Rcf': np.ndarray,          # 晶界气腔半径 (boundary cavity radius)
                    'cvb': np.ndarray,          # 基体空位浓度 (bulk vacancy concentration)
                    'cib': np.ndarray,          # 基体间隙原子浓度 (bulk interstitial concentration)
                    'kvb': np.ndarray,          # 基体空位汇聚强度 (bulk vacancy sink strength)
                    'kib': np.ndarray,          # 基体间隙原子汇聚强度 (bulk interstitial sink strength)
                    'cvf': np.ndarray,          # 晶界空位浓度 (boundary vacancy concentration)
                    'cif': np.ndarray,          # 晶界间隙原子浓度 (boundary interstitial concentration)
                    'kvf': np.ndarray,          # 晶界空位汇聚强度 (boundary vacancy sink strength)
                    'kif': np.ndarray,          # 晶界间隙原子汇聚强度 (boundary interstitial sink strength)
                    'released_gas': np.ndarray, # 累积释放气体 (cumulative gas release)
                    'swelling': np.ndarray      # 肿胀率百分比 (swelling percentage)
                }

        异常 (Raises):
            RuntimeError: 如果求解失败 (if solver fails)

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> # Simulate 100 days
            >>> time_points = np.linspace(0, 8640000, 100)
            >>> results = model.solve(t_span=(0, 8640000), t_eval=time_points)
            >>> print(f"Final swelling: {results['swelling'][-1]:.2f}%")
        """
        # 配置调试 (configure debug)
        self.debug_config.enabled = debug_enabled
        self.debug_config.time_step_interval = output_interval

        # 如果未指定输出时间点，创建默认的时间点 (create default time points if not specified)
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        # 创建求解器 (create solver)
        if method == 'RK23':
            solver = RK23Solver(self._equations_wrapper, self.params)
        else:
            # 对于其他方法，使用RK23但可以通过参数调整
            solver = RK23Solver(self._equations_wrapper, self.params)

        # 使用模块化求解器求解 (solve using modular solver)
        try:
            results = solver.solve(
                t_span=t_span,
                y0=self.initial_state,
                t_eval=t_eval,
                dt=dt,
                max_dt=max_dt
            )
            self.solver_success = True
        except Exception as e:
            self.solver_success = False
            raise RuntimeError(f"Solver failed: {str(e)}")

        # 计算并添加肿胀率 (calculate and add swelling percentage)
        Rcb = results['Rcb']
        Rcf = results['Rcf']
        Ccb = results['Ccb']
        Ccf = results['Ccf']
        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        results['swelling'] = (V_bubble_b + V_bubble_f) * 100

        # 如果启用调试，打印摘要 (print summary if debug enabled)
        if debug_enabled:
            print_simulation_summary(results, self.params)

        return results

    def get_gas_pressure(self, R: float, N: float, location: str = 'bulk') -> float:
        """
        计算气泡内的气体压力 (Calculate gas pressure inside bubble)

        参数 (Parameters):
            R : float
                气泡半径，单位：米 (bubble radius in meters)
            N : float
                气泡内气体原子数 (number of gas atoms in bubble)
            location : str
                位置标识 ('bulk' 或 'boundary')
                (location identifier: 'bulk' or 'boundary')
                默认值: 'bulk'

        返回 (Returns):
            float: 气体压力，单位：帕斯卡 (gas pressure in Pascals)

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> pressure = model.get_gas_pressure(1e-8, 100)
            >>> print(f"Bubble pressure: {pressure:.2e} Pa")
        """
        eos_model = self.params.get('eos_model', 'virial')
        return calculate_gas_pressure(R, N, self.params['temperature'], eos_model)

    def get_gas_influx(self, Cgb: float, Cgf: float) -> float:
        """
        计算从基体到相界面的气体原子通量
        (Calculate gas atom flux from bulk to phase boundary)

        参数 (Parameters):
            Cgb : float
                基体气体浓度，单位：原子/立方米
                (bulk gas concentration in atoms/m³)
            Cgf : float
                相界面气体浓度，单位：原子/立方米
                (phase boundary gas concentration in atoms/m³)

        返回 (Returns):
            float: 气体通量，单位：原子/(立方米·秒)
                   (gas flux in atoms/(m³·s))

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> influx = model.get_gas_influx(1e20, 1e19)
            >>> print(f"Gas influx: {influx:.2e} atoms/(m³·s)")
        """
        grain_diameter = self.params['grain_diameter']
        Dgb = self.params['Dgb']
        return calculate_gas_influx(Cgb, Cgf, grain_diameter, Dgb)

    def get_gas_release_rate(self, Cgf: float, Ccf: float,
                            Rcf: float, Ncf: float) -> float:
        """
        计算气体释放率 (Calculate gas release rate)

        基于气泡互连模型计算气体释放到晶界和自由表面的速率
        (Calculates gas release rate based on bubble interconnection model)

        参数 (Parameters):
            Cgf : float
                晶界气体浓度，单位：原子/立方米
                (grain boundary gas concentration in atoms/m³)
            Ccf : float
                晶界气腔浓度，单位：气腔/立方米
                (grain boundary cavity concentration in cavities/m³)
            Rcf : float
                晶界气腔半径，单位：米 (grain boundary cavity radius in meters)
            Ncf : float
                晶界每个气腔气体原子数 (atoms per grain boundary cavity)

        返回 (Returns):
            float: 气体释放率，单位：1/秒 (gas release rate in 1/s)

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> release_rate = model.get_gas_release_rate(1e20, 1e15, 1e-7, 50)
            >>> print(f"Gas release rate: {release_rate:.2e} /s")
        """
        grain_diameter = self.params['grain_diameter']
        return calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf, grain_diameter)

    def get_thermal_equilibrium_concentrations(self) -> Tuple[float, float]:
        """
        计算热平衡点缺陷浓度
        (Calculate thermal equilibrium point defect concentrations)

        返回 (Returns):
            Tuple[float, float]: (cv0, ci0)
                cv0 : 热平衡空位浓度 (thermal equilibrium vacancy concentration)
                ci0 : 热平衡间隙原子浓度 (thermal equilibrium interstitial concentration)

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> cv0, ci0 = model.get_thermal_equilibrium_concentrations()
            >>> print(f"cv0 = {cv0:.2e}, ci0 = {ci0:.2e}")
        """
        cv0 = calculate_cv0(
            temperature=self.params['temperature'],
            Evf_coeffs=self.params['Evf_coeffs'],
            kB_ev=self.params['kB_ev'],
            Evfmuti=self.params.get('Evfmuti', 1.0)
        )
        ci0 = calculate_ci0(
            temperature=self.params['temperature'],
            Eif_coeffs=self.params['Eif_coeffs'],
            kB_ev=self.params['kB_ev']
        )
        return cv0, ci0

    def enable_debug(self, time_step_interval: int = 1000, output_file: str = 'debug_output.csv'):
        """
        启用调试模式 (Enable debug mode)

        参数 (Parameters):
            time_step_interval : int
                调试输出间隔（步数）(debug output interval in steps)
                默认值: 1000
            output_file : str
                调试输出文件路径 (debug output file path)
                默认值: 'debug_output.csv'

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> model.enable_debug(time_step_interval=500)
            >>> results = model.solve(debug_enabled=True)
        """
        self.debug_config.enabled = True
        self.debug_config.time_step_interval = time_step_interval
        self.debug_config.save_to_file = True
        self.debug_config.output_file = output_file

    def disable_debug(self):
        """
        禁用调试模式 (Disable debug mode)

        示例 (Example):
            >>> model = RefactoredGasSwellingModel()
            >>> model.disable_debug()
        """
        self.debug_config.enabled = False

    def __repr__(self) -> str:
        """
        模型的字符串表示 (String representation of the model)

        返回 (Returns):
            str: 模型描述字符串 (model description string)
        """
        temp = self.params.get('temperature', 0)
        fission_rate = self.params.get('fission_rate', 0)
        eos_model = self.params.get('eos_model', 'virial')

        return (f"RefactoredGasSwellingModel(temperature={temp:.2f} K, "
                f"fission_rate={fission_rate:.2e} /m³/s, "
                f"eos_model='{eos_model}')")
