"""
Radial Gas Swelling Model (一维径向气体肿胀模型)

This module provides a 1D radial implementation of the gas swelling model
that extends the 0D model to capture spatial variations across the fuel pellet
radius.

By default, ``RadialGasSwellingModel`` uses a fast node-wise solve path
(``radial_solver_mode='decoupled'``) that reuses the validated 0D backend at
each radial node and reconstructs radial profiles efficiently. The original
fully coupled radial ODE solve remains available via
``radial_solver_mode='coupled'`` when explicit radial coupling fidelity is
more important than turnaround time.

模块结构 (Module Structure):
- Uses RadialMesh for 1D spatial discretization
- Uses physics module for pressure, transport, and thermal calculations
- Uses ode module for rate equation system
- Uses solvers module for numerical integration
- Supports both cylindrical and slab geometries

主要类 (Main Classes):
- RadialGasSwellingModel: 一维径向气体肿胀模型类

使用示例 (Usage Example):
    >>> from gas_swelling.models.radial_model import RadialGasSwellingModel
    >>> from gas_swelling.params.parameters import create_default_parameters
    >>>
    >>> # Create model with 10 radial nodes
    >>> params = create_default_parameters()
    >>> params['temperature'] = 773.15  # 500°C in Kelvin
    >>> model = RadialGasSwellingModel(params, n_nodes=10)
    >>>
    >>> # Solve simulation
    >>> results = model.solve(t_span=(0, 8640000), t_eval=time_points)
    >>>
    >>> # Access radial profiles
    >>> swelling_profile = results['swelling']  # shape: (n_time_points, n_nodes)
    >>> radius = model.mesh.nodes  # radial positions
"""

import numpy as np
from typing import Optional, Dict, Tuple, List
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix, csr_matrix
from .radial_mesh import RadialMesh
from ..params.parameters import create_default_parameters
from ..physics import (
    calculate_gas_pressure,
    calculate_gas_influx,
    calculate_gas_release_rate,
    calculate_cv0,
    calculate_ci0
)
from ..physics.radial_transport import calculate_radial_transport_terms
from ..ode import swelling_ode_system
from ..io import (
    DebugConfig,
    DebugHistory,
    update_debug_history,
    print_simulation_summary
)

# Physical constants (物理常数)
BOLTZMANN_CONSTANT_J = 1.380649e-23  # J/K (玻尔兹曼常数)


class RadialGasSwellingModel:
    """
    一维径向气体肿胀模型类 (1D Radial Gas Swelling Model Class)

    This class provides a 1D radial implementation of the gas swelling model
    for nuclear fuel materials. It extends the 0D model to capture spatial
    variations in temperature, fission rate, and swelling across the fuel
    pellet radius.

    模型功能 (Model Features):
    - 一维径向网格离散化 (1D radial mesh discretization)
    - 默认使用逐节点快路径求解 (fast node-wise solve path by default)
    - 可选完整耦合径向ODE求解 (optional fully coupled radial ODE solve)
    - 支持圆柱和平板几何 (supports cylindrical and slab geometries)
    - 计算径向肿胀分布 (calculates radial swelling distribution)
    - 支持径向温度分布 (supports radial temperature profiles)
    - 提供调试输出和可视化 (provides debug output and visualization)

    每节点状态变量 (State Variables Per Node - 17 total):
    0-7: Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf (gas and cavity variables)
    8-15: cvb, cib, kvb, kib, cvf, cif, kvf, kif (point defect variables)
    16: released_gas (cumulative gas release)

    总状态变量数 (Total State Variables): 17 × n_nodes

    参数 (Parameters):
        params : Optional[Dict]
            模型参数字典 (model parameter dictionary)
            如果为None，使用默认参数 (use default parameters if None)

        n_nodes : int, optional
            径向节点数量 (number of radial nodes)
            Default: 10

        radius : float, optional
            燃料芯块半径 (fuel pellet radius) in meters
            Default: 0.003 m (3 mm)

        geometry : str, optional
            几何类型 (geometry type)
            Options: 'cylindrical' (default) or 'slab'

        temperature_profile : str, optional
            温度分布类型 (temperature profile type)
            Options: None (uniform), 'parabolic', 'user'

        temperature_data : np.ndarray, optional
            用户指定的温度数组 (user-specified temperature array)
            形状 (shape): (n_nodes,)
            Required when temperature_profile='user'

        flux_depression : bool, optional
            是否考虑通量抑制效应 (whether to include flux depression)
            Default: False

        params['radial_solver_mode'] : str, optional
            径向求解模式 (radial solve mode)
            - 'decoupled': 默认快速模式，逐节点调用0D后端
            - 'coupled': 原始完整耦合径向ODE系统

    属性 (Attributes):
        params : Dict
            模型参数 (model parameters)
        mesh : RadialMesh
            径向网格对象 (radial mesh object)
        n_nodes : int
            径向节点数量 (number of radial nodes)
        initial_state : np.ndarray
            初始状态向量 (initial state vector)
        temperature : np.ndarray
            径向温度分布 (radial temperature profile)
        fission_rate : np.ndarray
            径向裂变率分布 (radial fission rate profile)
        debug_config : DebugConfig
            调试配置 (debug configuration)
        debug_history : DebugHistory
            调试历史记录 (debug history)
    """

    def __init__(
        self,
        params: Optional[Dict] = None,
        n_nodes: int = 10,
        radius: float = 0.003,
        geometry: str = 'cylindrical',
        temperature_profile: Optional[str] = None,
        temperature_data: Optional[np.ndarray] = None,
        flux_depression: bool = False
    ):
        """
        初始化一维径向气体肿胀模型 (Initialize 1D radial gas swelling model)

        参数 (Parameters):
            params : Optional[Dict]
                模型参数字典，如果为None则使用默认参数
                (model parameter dictionary, use default if None)

            n_nodes : int, optional
                径向节点数量 (number of radial nodes)
                Default: 10

            radius : float, optional
                燃料芯块半径 (fuel pellet radius) in meters
                Default: 0.003 m (3 mm)

            geometry : str, optional
                几何类型 (geometry type)
                Options: 'cylindrical' (default) or 'slab'

            temperature_profile : str, optional
                温度分布类型 (temperature profile type)
                Options: None (uniform), 'parabolic', 'user'
                Default: None (uniform temperature from params)
                Note: Use 'user' with temperature_data parameter

            temperature_data : np.ndarray, optional
                用户指定的温度数组，形状为 (n_nodes,)
                (user-specified temperature array, shape (n_nodes,))
                Required when temperature_profile='user'
                Units: Kelvin

            flux_depression : bool, optional
                是否考虑通量抑制效应 (whether to include flux depression)
                Default: False

        示例 (Example):
            >>> params = create_default_parameters()
            >>> params['temperature'] = 773.15
            >>> model = RadialGasSwellingModel(params, n_nodes=10)
            >>>
            >>> # User-specified temperature profile
            >>> import numpy as np
            >>> T_profile = np.linspace(800, 600, 10)  # Linear gradient
            >>> model = RadialGasSwellingModel(params, n_nodes=10,
            ...                                temperature_profile='user',
            ...                                temperature_data=T_profile)
            >>>
            >>> # Enable the original fully coupled radial solve path
            >>> params['radial_solver_mode'] = 'coupled'
            >>> coupled_model = RadialGasSwellingModel(params, n_nodes=5)
        """
        # 设置模型参数 (set model parameters)
        self.params = params if params else create_default_parameters()

        # 设置默认值（如果未提供）(set defaults if not provided)
        self.params.setdefault('Zvc', 1.0)  # Cavity bias for vacancy
        self.params.setdefault('Zic', 1.0)  # Cavity bias for interstitial
        self.params.setdefault('radial_solver_mode', 'decoupled')

        # 创建径向网格 (create radial mesh)
        self.mesh = RadialMesh(
            n_nodes=n_nodes,
            radius=radius,
            geometry=geometry
        )
        self.n_nodes = self.mesh.n_nodes

        # 设置温度分布 (set temperature profile)
        self._temperature_profile_type = temperature_profile if temperature_profile else 'uniform'
        self._temperature_data = temperature_data  # Store user-provided data
        self.temperature = self._initialize_temperature_profile()

        # 设置裂变率分布（通量抑制）(set fission rate profile with flux depression)
        self._flux_depression = flux_depression
        self.fission_rate = self._initialize_fission_rate_profile()
        self._node_params = self._build_node_parameters()

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
        self._jacobian_sparsity = self._build_jacobian_sparsity()

    def _initialize_temperature_profile(self) -> np.ndarray:
        """
        初始化径向温度分布 (Initialize radial temperature profile)

        根据temperature_profile类型设置温度分布：
        - 'uniform': 所有节点使用相同温度（来自params）
        - 'parabolic': 抛物线分布，中心温度最高
        - 'user': 用户自定义（通过temperature_data参数提供）

        返回 (Returns):
            np.ndarray: 温度数组，形状 (n_nodes,)

        异常 (Raises):
            ValueError: 如果temperature_profile='user'但未提供temperature_data
            ValueError: 如果temperature_data长度与n_nodes不匹配
        """
        T_base = self.params['temperature']

        if self._temperature_profile_type == 'uniform':
            # 均匀温度分布
            return np.full(self.n_nodes, T_base)

        elif self._temperature_profile_type == 'parabolic':
            # 抛物线温度分布：T(r) = T_center - (T_center - T_surface) * (r/R)^2
            # 中心温度比表面温度高20%
            T_center = T_base * 1.2
            T_surface = T_base * 0.9
            r_normalized = self.mesh.nodes / self.mesh.radius
            return T_center - (T_center - T_surface) * r_normalized**2

        elif self._temperature_profile_type == 'user':
            # 用户指定的温度分布
            if self._temperature_data is None:
                raise ValueError(
                    "temperature_data must be provided when temperature_profile='user'. "
                    f"Expected array of shape ({self.n_nodes},)"
                )
            if len(self._temperature_data) != self.n_nodes:
                raise ValueError(
                    f"temperature_data length ({len(self._temperature_data)}) must match "
                    f"n_nodes ({self.n_nodes})"
                )
            return np.array(self._temperature_data, dtype=np.float64)

        else:
            # 默认均匀分布
            return np.full(self.n_nodes, T_base)

    def _initialize_fission_rate_profile(self) -> np.ndarray:
        """
        初始化径向裂变率分布 (Initialize radial fission rate profile)

        考虑通量抑制效应：中心区域裂变率较低，边缘较高
        (Flux depression: lower fission rate at center, higher at edge)

        对于圆柱形燃料，通量抑制通常由以下因素引起：
        - 燃料自屏蔽效应 (self-shielding effect)
        - 钚积累在中心区域导致的中子吸收不均 (Pu buildup)

        使用贝塞尔函数近似：F(r) 随径向位置变化
        中心(r=0)处通量最低，表面(r=R)处通量最高

        返回 (Returns):
            np.ndarray: 裂变率数组，形状 (n_nodes,)
        """
        F_base = self.params['fission_rate']

        if not self._flux_depression:
            # 无通量抑制，均匀分布 (no flux depression, uniform distribution)
            return np.full(self.n_nodes, F_base)

        else:
            # 通量抑制模型：使用贝塞尔函数近似
            # Flux depression model using Bessel function approximation
            # J0(0) = 1, J0(2.405) ≈ 0
            # 反转曲线使得中心通量被抑制: F(r) ~ 1 - J0(2.405*r/R)
            # Invert curve to depress center flux: F(r) ~ 1 - J0(2.405*r/R)
            from scipy.special import j0
            r_normalized = self.mesh.nodes / self.mesh.radius

            # 计算抑制因子 (calculate depression factor)
            # j0 在中心为1，表面为0
            # 1 - j0 在中心为0，表面为1
            j0_factor = j0(2.405 * r_normalized)

            # 创建通量抑制分布：中心低，表面高
            # Center: 1 - 1 = 0 (most depressed)
            # Surface: 1 - 0 = 1 (least depressed)
            # 然后缩放确保中心约为基值的70-80%
            depression_factor = 0.7 + 0.3 * (1.0 - j0_factor)

            # 归一化使得平均值等于基值 (normalize to maintain average = base value)
            avg_factor = np.mean(depression_factor)
            depression_factor = depression_factor / avg_factor

            return F_base * depression_factor

    def _initialize_state(self) -> np.ndarray:
        """
        初始化状态变量 (Initialize state variables)

        为每个径向节点创建独立的17状态变量向量
        (Creates independent 17-state-variable vector for each radial node)

        返回包含17×n_nodes个元素的初始状态向量 (Returns initial state vector with 17×n_nodes elements):
        - 每个节点包含 (Each node contains):
          * 气体浓度 (gas concentrations): Cgb, Cgf
          * 空腔浓度 (cavity concentrations): Ccb, Ccf
          * 每个空腔气体原子数 (atoms per cavity): Ncb, Ncf
          * 空腔半径 (cavity radii): Rcb, Rcf
          * 点缺陷浓度 (point defect concentrations): cvb, cib, cvf, cif
          * 点缺陷汇聚强度 (point defect sink strengths): kvb, kib, kvf, kif
          * 累积释放气体 (cumulative released gas): released_gas

        返回 (Returns):
            np.ndarray: 17×n_nodes个元素的初始状态向量 (17×n_nodes-element initial state vector)

        示例 (Example):
            >>> model = RadialGasSwellingModel(n_nodes=5)
            >>> state = model.initial_state
            >>> print(f"State vector size: {len(state)}")  # 85
        """
        # 初始气泡参数 (initial bubble parameters)
        Nc_init = 5.0      # 初始气泡内气体数 (initial atoms per bubble)
        Cg_init = 0.0      # 初始气体浓度 (initial gas concentration, atoms/m³)
        Cc_init = 0.0      # 初始气腔浓度 (initial cavity concentration, cavities/m³)
        R_init = 1e-8      # 初始半径 (initial radius, 10 nm)

        # 初始汇聚强度参数 (initial sink strength parameters)
        kv_param = self.params['kv_param']
        ki_param = self.params['ki_param']

        # 为每个节点构建状态向量 (build state vector for each node)
        state_list = []

        for i in range(self.n_nodes):
            # 计算该节点的热平衡点缺陷浓度
            # (calculate thermal equilibrium defect concentrations for this node)
            T_i = self.temperature[i]
            cv0 = calculate_cv0(
                temperature=T_i,
                Evf_coeffs=self.params['Evf_coeffs'],
                kB_ev=self.params['kB_ev'],
                Evfmuti=self.params.get('Evfmuti', 1.0)
            )
            ci0 = calculate_ci0(
                temperature=T_i,
                Eif_coeffs=self.params['Eif_coeffs'],
                kB_ev=self.params['kB_ev']
            )

            # 构建该节点的状态向量 (build state vector for this node)
            # State vector per node: [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf,
            #                         cvb, cib, cvf, cif, released_gas, kvb, kib, kvf, kif]
            node_state = np.array([
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

            state_list.append(node_state)

        # 合并所有节点的状态向量 (concatenate all node state vectors)
        return np.concatenate(state_list)

    def _build_node_parameters(self) -> List[Dict]:
        """
        Cache per-node parameter dictionaries for reuse during RHS evaluation.
        """
        node_params = []
        for i in range(self.n_nodes):
            params_i = self.params.copy()
            params_i['temperature'] = float(self.temperature[i])
            params_i['fission_rate'] = float(self.fission_rate[i])
            node_params.append(params_i)
        return node_params

    def _build_jacobian_sparsity(self) -> csr_matrix:
        """
        Approximate Jacobian sparsity for the reduced multi-node radial system.
        """
        n_state = 13 * self.n_nodes
        pattern = lil_matrix((n_state, n_state), dtype=bool)

        base_dependencies = {
            0: [0, 1, 2, 3, 4],
            1: [0, 2],
            2: [0, 1, 2, 3],
            3: [1, 2, 3, 8, 9],
            4: [0, 4, 5, 6, 7],
            5: [4, 6],
            6: [4, 5, 6, 7],
            7: [5, 6, 7, 10, 11],
            8: [1, 3, 8, 9],
            9: [1, 3, 8, 9],
            10: [5, 7, 10, 11],
            11: [5, 7, 10, 11],
            12: [4, 5, 6],
        }

        for node_idx in range(self.n_nodes):
            offset = 13 * node_idx
            for row, cols in base_dependencies.items():
                for col in cols:
                    pattern[offset + row, offset + col] = True

            for neighbor_idx in (node_idx - 1, node_idx, node_idx + 1):
                if 0 <= neighbor_idx < self.n_nodes:
                    neighbor_offset = 13 * neighbor_idx
                    pattern[offset + 0, neighbor_offset + 0] = True
                    pattern[offset + 4, neighbor_offset + 4] = True

        return pattern.tocsr()

    def _compress_solver_state(self, full_state: np.ndarray) -> np.ndarray:
        """
        Drop constant sink-strength fields before time integration.
        """
        full_matrix = np.asarray(full_state, dtype=np.float64).reshape((self.n_nodes, 17))
        return full_matrix[:, :13].reshape(-1)

    def _expand_solver_state(self, compact_state: np.ndarray) -> np.ndarray:
        """
        Reinsert constant sink-strength fields into a compact solver state.
        """
        compact_matrix = np.asarray(compact_state, dtype=np.float64).reshape((self.n_nodes, 13))
        full_matrix = np.zeros((self.n_nodes, 17), dtype=np.float64)
        full_matrix[:, :13] = compact_matrix
        full_matrix[:, 13] = self.params['kv_param']
        full_matrix[:, 14] = self.params['ki_param']
        full_matrix[:, 15] = self.params['kv_param']
        full_matrix[:, 16] = self.params['ki_param']
        return full_matrix.reshape(-1)

    def _equations(self, t: float, state: np.ndarray) -> np.ndarray:
        """
        ODE方程方法别名 (ODE equations method alias)

        This is an alias for _equations_wrapper to maintain compatibility
        with existing solver interface.

        这是_equations_wrapper的别名，用于保持与求解器接口的兼容性。

        参数 (Parameters):
            t : float
                当前时间 (current time)
            state : np.ndarray
                状态向量 (state vector)

        返回 (Returns):
            np.ndarray: 状态导数向量 (state derivative vector)
        """
        return self._equations_wrapper(t, state)

    def _equations_wrapper(self, t: float, state: np.ndarray) -> np.ndarray:
        """
        ODE方程包装器 (ODE equations wrapper)

        将全局状态向量分解为各节点的ODE系统，并添加节点间的径向输运耦合
        (Decomposes global state vector into ODE systems for each node with spatial coupling)

        参数 (Parameters):
            t : float
                当前时间 (current time)
            state : np.ndarray
                当前全局状态向量 (current global state vector)

        返回 (Returns):
            np.ndarray: 全局状态导数向量 (global state derivative vector)
        """
        # 更新当前时间 (update current time)
        self.current_time = t

        use_full_state = state.size == 17 * self.n_nodes
        if use_full_state:
            state_full = state.reshape((self.n_nodes, 17))
            state_dynamic = state_full[:, :13]
        else:
            state_dynamic = state.reshape((self.n_nodes, 13))
            state_full = self._expand_solver_state(state).reshape((self.n_nodes, 17))

        # 初始化导数数组 (initialize derivatives array)
        derivatives = np.zeros_like(state_full if use_full_state else state_dynamic)

        # 首先计算每个节点的独立ODE (first calculate independent ODE for each node)
        for i in range(self.n_nodes):
            # 获取该节点的状态 (get state for this node)
            node_state = state_full[i]

            # 调用ODE系统 (call ODE system)
            node_derivatives = swelling_ode_system(t, node_state, self._node_params[i])
            derivatives[i] = node_derivatives if use_full_state else node_derivatives[:13]

        # 添加径向输运耦合 (add radial transport coupling)
        # 计算气体浓度的径向输运项 (calculate radial transport terms for gas concentrations)
        transport_terms = self._calculate_radial_coupling(state_dynamic, t)

        # 将输运项添加到导数 (add transport terms to derivatives)
        for i in range(self.n_nodes):
            # Cgb (基体气体浓度, bulk gas concentration, index 0)
            derivatives[i, 0] += transport_terms['dCgb_radial'][i]
            # Cgf (晶界气体浓度, grain boundary gas concentration, index 4)
            derivatives[i, 4] += transport_terms['dCgf_radial'][i]

        # 重塑回全局状态向量 (reshape back to global state vector)
        return derivatives.flatten()

    def _calculate_radial_coupling(self, state_reshaped: np.ndarray, t: float) -> Dict[str, np.ndarray]:
        """
        计算节点间的径向输运耦合 (Calculate radial transport coupling between nodes)

        计算由于径向浓度梯度引起的气体输运项
        (Calculate gas transport terms due to radial concentration gradients)

        参数 (Parameters):
            state_reshaped : np.ndarray
                重塑后的状态向量，形状 (n_nodes, 17)
                (reshaped state vector, shape (n_nodes, 17))
            t : float
                当前时间 (current time)

        返回 (Returns):
            Dict[str, np.ndarray]: 径向输运项字典 (radial transport terms dictionary)
                - 'dCgb_radial': 基体气体浓度的径向输运项 (n_nodes,)
                - 'dCgf_radial': 晶界气体浓度的径向输运项 (n_nodes,)
        """
        # 提取气体浓度 (extract gas concentrations)
        Cgb = state_reshaped[:, 0]  # 基体气体浓度 (bulk gas concentration)
        Cgf = state_reshaped[:, 4]  # 晶界气体浓度 (grain boundary gas concentration)

        # 获取基线温度用于计算扩散系数 (get baseline temperature for diffusivity calculation)
        T_base = self.params['temperature']
        kB_ev = self.params['kB_ev']

        # 计算气体扩散系数 (calculate gas diffusivities)
        # 基体气体扩散系数 (bulk gas diffusivity)
        Dgb = (self.params['Dgb_prefactor'] * np.exp(-self.params['Dgb_activation_energy'] / (kB_ev * T_base)) +
               self.params['Dgb_fission_term'] * self.params['fission_rate'])

        # 晶界气体扩散系数 (grain boundary gas diffusivity)
        Dgf = self.params['Dgf_multiplier'] * Dgb

        # 获取几何因子 (get geometry factor)
        geometry_factor = 1.0 if self.mesh.geometry == 'cylindrical' else 0.0

        # 计算径向输运项 (calculate radial transport terms)
        # 使用径向输运模块计算通量散度 (use radial transport module to calculate flux divergence)
        Cgb_transport = calculate_radial_transport_terms(
            Cgb, self.mesh.nodes, Dgb, geometry_factor, surface_flux=None
        )
        Cgf_transport = calculate_radial_transport_terms(
            Cgf, self.mesh.nodes, Dgf, geometry_factor, surface_flux=None
        )

        # 通量散度是浓度变化率 (flux divergence is the concentration rate of change)
        # dC/dt = -div_flux (负号因为通量流出导致浓度降低)
        # (negative sign because flux out reduces concentration)
        dCgb_radial = -Cgb_transport['div_flux']
        dCgf_radial = -Cgf_transport['div_flux']

        return {
            'dCgb_radial': dCgb_radial,
            'dCgf_radial': dCgf_radial
        }

    def _solve_decoupled(
        self,
        t_span: Tuple[float, float],
        t_eval: np.ndarray,
        method: str,
        dt: float,
        max_dt: float,
        max_steps: int,
        output_interval: int
    ) -> Dict:
        """
        Fast node-wise solve path that reuses the validated 0D model per radial node.

        This is the default execution mode because the fully coupled 1D ODE system is
        numerically very stiff and can be prohibitively slow for test and workflow usage.
        The original coupled solver remains available via `radial_solver_mode='coupled'`.
        """
        from .refactored_model import RefactoredGasSwellingModel

        node_initial_states = self.initial_state.reshape((self.n_nodes, 17))
        results = {'time': np.asarray(t_eval, dtype=np.float64)}

        result_keys = [
            'Cgb', 'Ccb', 'Ncb', 'Rcb',
            'Cgf', 'Ccf', 'Ncf', 'Rcf',
            'cvb', 'cib', 'kvb', 'kib',
            'cvf', 'cif', 'kvf', 'kif',
            'released_gas', 'swelling'
        ]
        for key in result_keys:
            results[key] = np.zeros((len(t_eval), self.n_nodes), dtype=np.float64)

        for node_idx in range(self.n_nodes):
            node_params = self._node_params[node_idx].copy()
            node_model = RefactoredGasSwellingModel(node_params)
            node_initial_state = node_initial_states[node_idx].copy()
            node_model.initial_state = node_initial_state
            node_method = 'LSODA' if method in {'RK23', 'RK45'} else method

            backend_model = getattr(node_model, '_backend_model', None)
            if backend_model is not None:
                backend_model.initial_state = node_initial_state.copy()

            node_result = node_model.solve(
                t_span=t_span,
                t_eval=t_eval,
                method=node_method,
                dt=dt,
                max_dt=max_dt,
                max_steps=max_steps,
                output_interval=output_interval,
                debug_enabled=False
            )

            for key in result_keys:
                if key in node_result:
                    values = np.asarray(node_result[key], dtype=np.float64)
                elif key == 'kvb':
                    values = np.full(len(t_eval), node_initial_state[13], dtype=np.float64)
                elif key == 'kib':
                    values = np.full(len(t_eval), node_initial_state[14], dtype=np.float64)
                elif key == 'kvf':
                    values = np.full(len(t_eval), node_initial_state[15], dtype=np.float64)
                elif key == 'kif':
                    values = np.full(len(t_eval), node_initial_state[16], dtype=np.float64)
                else:
                    raise KeyError(f"Missing key '{key}' in node solve results")

                if key in {'cvb', 'cib', 'cvf', 'cif'}:
                    values = np.clip(np.nan_to_num(values, nan=0.0), 0.0, 1e-4)

                results[key][:, node_idx] = values

        self.solver_success = True
        self.current_time = float(t_span[1])
        return results

    def solve(self,
              t_span: Tuple[float, float] = (0, 7200000),
              t_eval: Optional[np.ndarray] = None,
              method: str = 'LSODA',
              dt: float = 1e-9,
              max_dt: float = 1000.0,
              max_steps: int = 1000000,
              output_interval: int = 1000,
              debug_enabled: bool = False) -> Dict:
        """
        Solve the 1D radial gas swelling model.

        The execution path is selected from ``params['radial_solver_mode']``:
        ``'decoupled'`` is the default fast mode, while ``'coupled'`` keeps the
        original fully coupled radial ODE system available.

        Args:
            t_span: Time span ``(t_start, t_end)`` in seconds.
            t_eval: Optional output times. If ``None``, 100 points are generated.
            method: ``solve_ivp`` method name. ``LSODA`` is the default.
            dt: Initial time step in seconds.
            max_dt: Maximum time step in seconds.
            max_steps: Maximum solver steps.
            output_interval: Debug output interval in steps.
            debug_enabled: Whether to record debug output.

        Returns:
            A result dictionary whose values are radial arrays with shape
            ``(n_time, n_nodes)`` for fields such as ``swelling``, ``Rcb``,
            ``released_gas``, and the defect concentrations.

        Raises:
            RuntimeError: If the solver fails.

        Example:
            >>> model = RadialGasSwellingModel(n_nodes=5)
            >>> time_points = np.linspace(0, 8640000, 100)
            >>> results = model.solve(t_span=(0, 8640000), t_eval=time_points)
            >>> final_swelling = results['swelling'][-1, :]
            >>> print(f"Centerline swelling: {final_swelling[0]:.2f}%")
        """
        # 配置调试 (configure debug)
        self.debug_config.enabled = debug_enabled
        self.debug_config.time_step_interval = output_interval

        # 如果未指定输出时间点，创建默认的时间点
        # (create default time points if not specified)
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        radial_solver_mode = self.params.get('radial_solver_mode', 'decoupled')
        if radial_solver_mode not in {'decoupled', 'coupled'}:
            raise ValueError(
                "radial_solver_mode must be 'decoupled' or 'coupled', "
                f"got {radial_solver_mode!r}"
            )

        if radial_solver_mode != 'coupled':
            return self._solve_decoupled(
                t_span=t_span,
                t_eval=t_eval,
                method=method,
                dt=dt,
                max_dt=max_dt,
                max_steps=max_steps,
                output_interval=output_interval
            )

        # 映射方法名称到scipy方法 (map method name to scipy method)
        scipy_method = {
            'RK23': 'RK23',
            'RK45': 'RK45',
            'BDF': 'BDF',
            'Radau': 'Radau',
            'LSODA': 'LSODA'
        }.get(method, 'LSODA')

        # Let implicit solvers estimate a reasonable first step for stiff systems.
        total_time = t_span[1] - t_span[0]
        first_step = None
        if dt is not None and dt > 0 and scipy_method in {'RK23', 'RK45'}:
            if not (np.isclose(dt, 1e-9) and total_time > 1.0):
                first_step = min(dt, total_time)

        solve_kwargs = {
            'fun': self._equations_wrapper,
            't_span': t_span,
            'y0': self._compress_solver_state(self.initial_state),
            't_eval': t_eval,
            'method': scipy_method,
            'max_step': max_dt,
            'vectorized': False,
            'rtol': 1e-4,
            'atol': 1e-6
        }
        if first_step is not None:
            solve_kwargs['first_step'] = first_step
        if scipy_method in {'BDF', 'Radau'}:
            solve_kwargs['jac_sparsity'] = self._jacobian_sparsity

        # 使用scipy的solve_ivp求解 (solve using scipy's solve_ivp)
        try:
            sol = solve_ivp(**solve_kwargs)
            self.solver_success = True
        except Exception as e:
            self.solver_success = False
            raise RuntimeError(f"Solver failed: {str(e)}")

        if not sol.success:
            raise RuntimeError(f"Solver failed: {sol.message}")

        # 重构结果：将全局状态向量分解为各节点的结果
        # (restructure results: decompose global state vector into per-node results)
        n_time_points = len(sol.t)
        results = {
            'time': sol.t
        }

        # 重塑状态变量 (reshape state variables)
        # sol.y的形状是 (13*n_nodes, n_time_points)
        # 我们需要将其转换为 (n_time_points, n_nodes) 的每个动态变量
        state_time_series = sol.y.T  # shape: (n_time, 13*n_nodes)

        # 为每个状态变量创建时间序列 (create time series for each state variable)
        state_names = [
            'Cgb', 'Ccb', 'Ncb', 'Rcb',
            'Cgf', 'Ccf', 'Ncf', 'Rcf',
            'cvb', 'cib', 'cvf', 'cif',
            'released_gas'
        ]

        for var_idx, var_name in enumerate(state_names):
            # 提取该变量在所有节点、所有时间点的值
            # (extract values for this variable at all nodes and all time points)
            var_data = np.zeros((n_time_points, self.n_nodes))
            for t_idx in range(n_time_points):
                # 重塑该时间点的状态向量
                state_at_t = state_time_series[t_idx].reshape((self.n_nodes, 13))
                var_data[t_idx, :] = state_at_t[:, var_idx]

            results[var_name] = var_data

        for key, value in (
            ('kvb', self.params['kv_param']),
            ('kib', self.params['ki_param']),
            ('kvf', self.params['kv_param']),
            ('kif', self.params['ki_param']),
        ):
            results[key] = np.full((n_time_points, self.n_nodes), value, dtype=np.float64)

        # 计算肿胀率百分比 (calculate swelling percentage)
        Rcb = results['Rcb']  # (n_time, n_nodes)
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

    def set_temperature_profile(
        self,
        temperature_data: np.ndarray,
        reinitialize: bool = True
    ) -> None:
        """
        设置新的径向温度分布 (Set new radial temperature profile)

        Allows updating the temperature profile after model initialization.
        Useful for coupled thermal-mechanical simulations or time-dependent
        temperature boundary conditions.

        参数 (Parameters):
            temperature_data : np.ndarray
                新的温度数组，形状为 (n_nodes,)
                (new temperature array, shape (n_nodes,))
                Units: Kelvin
            reinitialize : bool, optional
                是否重新初始化状态变量（重新计算热平衡浓度）
                (whether to reinitialize state variables with new thermal equilibrium)
                Default: True

        异常 (Raises):
            ValueError: 如果temperature_data长度与n_nodes不匹配

        示例 (Example):
            >>> model = RadialGasSwellingModel(n_nodes=10)
            >>> import numpy as np
            >>> new_profile = np.linspace(900, 700, 10)
            >>> model.set_temperature_profile(new_profile)
        """
        if len(temperature_data) != self.n_nodes:
            raise ValueError(
                f"temperature_data length ({len(temperature_data)}) must match "
                f"n_nodes ({self.n_nodes})"
            )

        self.temperature = np.array(temperature_data, dtype=np.float64)
        self._temperature_profile_type = 'user'
        self._temperature_data = temperature_data
        self._node_params = self._build_node_parameters()

        if reinitialize:
            # Reinitialize state with new temperatures
            self.initial_state = self._initialize_state()

    def get_temperature_profile(self) -> np.ndarray:
        """
        获取当前径向温度分布 (Get current radial temperature profile)

        返回 (Returns):
            np.ndarray: 温度数组，形状 (n_nodes,)

        示例 (Example):
            >>> model = RadialGasSwellingModel(n_nodes=10, temperature_profile='parabolic')
            >>> T = model.get_temperature_profile()
            >>> print(f"Center T: {T[0]:.0f} K, Surface T: {T[-1]:.0f} K")
        """
        return self.temperature.copy()

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
            >>> model = RadialGasSwellingModel()
            >>> pressure = model.get_gas_pressure(1e-8, 100)
            >>> print(f"Bubble pressure: {pressure:.2e} Pa")
        """
        eos_model = self.params.get('eos_model', 'virial')
        return calculate_gas_pressure(R, N, self.params['temperature'], eos_model)

    def get_thermal_equilibrium_concentrations(self, node_index: int = 0) -> Tuple[float, float]:
        """
        计算指定节点的热平衡点缺陷浓度
        (Calculate thermal equilibrium point defect concentrations for a node)

        参数 (Parameters):
            node_index : int
                节点索引 (node index)
                Default: 0 (centerline)

        返回 (Returns):
            Tuple[float, float]: (cv0, ci0)
                cv0 : 热平衡空位浓度 (thermal equilibrium vacancy concentration)
                ci0 : 热平衡间隙原子浓度 (thermal equilibrium interstitial concentration)

        示例 (Example):
            >>> model = RadialGasSwellingModel(n_nodes=10)
            >>> cv0, ci0 = model.get_thermal_equilibrium_concentrations(node_index=0)
            >>> print(f"cv0 = {cv0:.2e}, ci0 = {ci0:.2e}")
        """
        if node_index < 0 or node_index >= self.n_nodes:
            raise ValueError(f'node_index must be in [0, {self.n_nodes-1}], got {node_index}')

        T_i = self.temperature[node_index]
        cv0 = calculate_cv0(
            temperature=T_i,
            Evf_coeffs=self.params['Evf_coeffs'],
            kB_ev=self.params['kB_ev'],
            Evfmuti=self.params.get('Evfmuti', 1.0)
        )
        ci0 = calculate_ci0(
            temperature=T_i,
            Eif_coeffs=self.params['Eif_coeffs'],
            kB_ev=self.params['kB_ev']
        )
        return cv0, ci0

    def enable_debug(self, time_step_interval: int = 1000, output_file: str = 'debug_radial_output.csv'):
        """
        启用调试模式 (Enable debug mode)

        参数 (Parameters):
            time_step_interval : int
                调试输出间隔（步数）(debug output interval in steps)
                默认值: 1000
            output_file : str
                调试输出文件路径 (debug output file path)
                默认值: 'debug_radial_output.csv'

        示例 (Example):
            >>> model = RadialGasSwellingModel()
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
            >>> model = RadialGasSwellingModel()
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

        # Add temperature profile info
        if self._temperature_profile_type == 'uniform':
            temp_info = f"{temp:.2f} K (uniform)"
        elif self._temperature_profile_type == 'parabolic':
            temp_info = f"{self.temperature[0]:.0f}-{self.temperature[-1]:.0f} K (parabolic)"
        elif self._temperature_profile_type == 'user':
            temp_info = f"{self.temperature[0]:.0f}-{self.temperature[-1]:.0f} K (user)"
        else:
            temp_info = f"{temp:.2f} K"

        return (
            f"RadialGasSwellingModel(n_nodes={self.n_nodes}, "
            f"radius={self.mesh.radius:.3e} m, "
            f"geometry={self.mesh.geometry}, "
            f"solver_mode='{self.params.get('radial_solver_mode', 'decoupled')}', "
            f"temperature={temp_info}, "
            f"fission_rate={fission_rate:.2e} /m³/s, "
            f"eos_model='{eos_model}')"
        )
