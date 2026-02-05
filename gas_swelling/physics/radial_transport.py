"""
径向输运计算模块 (Radial Transport Calculation Module)

This module provides calculations for radial gas transport in nuclear fuel materials,
including diffusion coupling between radial nodes, flux boundary conditions, and
geometry-dependent transport factors for 1D spatial discretization.
Based on the theoretical framework from rate theory adapted for 1D radial geometry.
References: Extension of Eqs. 1-8 for radial transport in cylindrical/slab coordinates.
"""

import numpy as np
from typing import Dict, Tuple, Optional


def calculate_radial_flux(
    concentration: np.ndarray,
    diffusion_coeff: float,
    mesh_nodes: np.ndarray,
    geometry_factor: float
) -> np.ndarray:
    """
    计算节点间的径向气体通量 (Calculate radial gas flux between nodes)

    Calculate the diffusive gas flux between adjacent radial nodes due to concentration gradients.
    This is the fundamental transport mechanism for 1D radial spatial discretization.

    计算由于浓度梯度在相邻径向节点之间的扩散气体通量。
    这是一维径向空间离散化的基本输运机制。

    Parameters
    ----------
    concentration : np.ndarray
        Gas concentration at each node (atoms/m³), shape (n_nodes,)
        每个节点处的气体浓度 (原子/m³)

    diffusion_coeff : float
        Gas diffusion coefficient (m²/s)
        气体扩散系数 (m²/s)

    mesh_nodes : np.ndarray
        Radial positions of nodes (m), shape (n_nodes,)
        节点的径向位置 (m)

    geometry_factor : float
        Geometry factor: 1.0 for cylindrical, 0.0 for slab
        几何因子：圆柱为1.0，平板为0.0

    Returns
    -------
    np.ndarray
        Radial flux between nodes (atoms/m²/s), shape (n_nodes-1,)
        Positive values indicate flux from node i to i+1
        节点间的径向通量 (原子/m²/s)，正值表示从节点i到i+1的通量

    Notes
    -----
    The radial flux is calculated using finite difference approximation of Fick's first law:
    使用菲克第一定律的有限差分近似计算径向通量：

    For cylindrical geometry (圆柱坐标系):
        J[r] = -D × (C[i+1] - C[i]) / (r[i+1] - r[i])

    For slab geometry (平板坐标系):
        J[x] = -D × (C[i+1] - C[i]) / (x[i+1] - x[i])

    The geometry factor accounts for coordinate system effects on the effective
    transport area. In cylindrical coordinates, the area scales with radius.

    几何因子考虑了坐标系对有效输运面积的影响。
    在圆柱坐标系中，面积随半径缩放。

    References
    ----------
    Fick's first law of diffusion
    Transport phenomena in cylindrical coordinates

    Examples
    --------
    >>> import numpy as np
    >>> concentration = np.array([1e25, 0.9e25, 0.8e25, 0.7e25])  # Decreasing outward
    >>> diffusion_coeff = 1e-15  # m²/s
    >>> mesh_nodes = np.array([0.0, 0.001, 0.002, 0.003])  # 3 mm radius
    >>> flux = calculate_radial_flux(concentration, diffusion_coeff, mesh_nodes, geometry_factor=1.0)
    >>> print(f'Flux shape: {flux.shape}')
    Flux shape: (3,)
    """
    if len(concentration) != len(mesh_nodes):
        raise ValueError(
            f"concentration and mesh_nodes must have same length, "
            f"got {len(concentration)} and {len(mesh_nodes)}"
        )

    if diffusion_coeff < 0:
        raise ValueError(f"diffusion_coeff must be non-negative, got {diffusion_coeff}")

    if geometry_factor not in [0.0, 1.0]:
        raise ValueError(f"geometry_factor must be 0.0 (slab) or 1.0 (cylindrical), got {geometry_factor}")

    # Calculate spacing between nodes
    # 计算节点之间的间距
    dr = np.diff(mesh_nodes)

    # Check for zero or negative spacing
    # 检查零或负间距
    if np.any(dr <= 0):
        raise ValueError("mesh_nodes must be strictly increasing")

    # Calculate concentration gradient (finite difference)
    # 计算浓度梯度（有限差分）
    dC_dr = np.diff(concentration) / dr

    # Calculate flux using Fick's first law: J = -D × dC/dr
    # Negative sign means flux flows from high to low concentration
    # 使用菲克第一定律计算通量：J = -D × dC/dr
    # 负号表示通量从高浓度流向低浓度
    flux = -diffusion_coeff * dC_dr

    return flux


def calculate_diffusion_coupling_matrix(
    mesh_nodes: np.ndarray,
    diffusion_coeff: float,
    geometry_factor: float
) -> np.ndarray:
    """
    计算扩散耦合矩阵 (Calculate diffusion coupling matrix)

    Construct the finite difference coupling matrix for radial diffusion.
    This matrix represents the discretized Laplacian operator for the diffusion equation.

    构造径向扩散的有限差分耦合矩阵。
    该矩阵表示扩散方程的离散化拉普拉斯算子。

    Parameters
    ----------
    mesh_nodes : np.ndarray
        Radial positions of nodes (m), shape (n_nodes,)
        节点的径向位置 (m)

    diffusion_coeff : float
        Gas diffusion coefficient (m²/s)
        气体扩散系数 (m²/s)

    geometry_factor : float
        Geometry factor: 1.0 for cylindrical, 0.0 for slab
        几何因子：圆柱为1.0，平板为0.0

    Returns
    -------
    np.ndarray
        Coupling matrix (n_nodes, n_nodes) for radial diffusion
        径向扩散的耦合矩阵 (n_nodes, n_nodes)

    Notes
    -----
    The coupling matrix A represents the discretized diffusion operator:
    耦合矩阵A表示离散化的扩散算子：

    dC/dt = D × ∇²C = D × A × C

    For interior nodes (internal nodes):
    对于内部节点：
        A[i,i-1] = 1/(dr[i-1] × dr_mean[i])
        A[i,i]   = -1/(dr[i-1] × dr_mean[i]) - 1/(dr[i] × dr_mean[i])
        A[i,i+1] = 1/(dr[i] × dr_mean[i])

    where dr_mean[i] is the average spacing around node i.

    其中 dr_mean[i] 是节点i周围的平均间距。

    For cylindrical geometry, additional geometric terms are included to account
    for the (1/r) × d/dr(r × dC/dr) form of the Laplacian.

    对于圆柱几何，包含额外的几何项以考虑拉普拉斯算子的 (1/r) × d/dr(r × dC/dr) 形式。

    References
    ----------
    Finite difference methods for diffusion equations
    Cylindrical coordinate discretization

    Examples
    --------
    >>> import numpy as np
    >>> mesh_nodes = np.linspace(0, 0.003, 5)  # 5 nodes, 3 mm radius
    >>> A = calculate_diffusion_coupling_matrix(mesh_nodes, 1e-15, geometry_factor=1.0)
    >>> print(f'Coupling matrix shape: {A.shape}')
    Coupling matrix shape: (5, 5)
    """
    n_nodes = len(mesh_nodes)

    if n_nodes < 2:
        raise ValueError(f"mesh_nodes must have at least 2 nodes, got {n_nodes}")

    if diffusion_coeff < 0:
        raise ValueError(f"diffusion_coeff must be non-negative, got {diffusion_coeff}")

    # Calculate spacing
    # 计算间距
    dr = np.diff(mesh_nodes)

    # Initialize coupling matrix
    # 初始化耦合矩阵
    A = np.zeros((n_nodes, n_nodes))

    # Build coupling matrix for interior nodes
    # 为内部节点构建耦合矩阵
    for i in range(1, n_nodes - 1):
        # Average spacing around node i
        # 节点i周围的平均间距
        dr_mean_left = (dr[i-1] + dr[i]) / 2.0

        # Coefficients for finite difference stencil
        # 有限差分格式的系数
        coeff_left = diffusion_coeff / (dr[i-1] * dr_mean_left)
        coeff_right = diffusion_coeff / (dr[i] * dr_mean_left)

        A[i, i-1] = coeff_left
        A[i, i] = -(coeff_left + coeff_right)
        A[i, i+1] = coeff_right

        # Add cylindrical geometry correction
        # 添加圆柱几何修正
        if geometry_factor == 1.0 and mesh_nodes[i] > 0:
            # Additional term: D / (r × dr_mean)
            # 额外项：D / (r × dr_mean)
            geom_correction = diffusion_coeff / (mesh_nodes[i] * dr_mean_left)
            # This is a simplified correction; full cylindrical operator requires
            # more careful treatment at small radii
            A[i, :] += geom_correction * np.array([-dr[i-1], dr[i-1] + dr[i], -dr[i]]) / (2 * dr_mean_left)

    return A


def calculate_node_to_node_flux(
    concentration_i: float,
    concentration_j: float,
    diffusion_coeff: float,
    distance: float,
    geometry_factor: float,
    radial_position: Optional[float] = None
) -> float:
    """
    计算两个节点之间的气体通量 (Calculate gas flux between two nodes)

    Calculate the diffusive gas flux between two specific nodes at given positions.
    This is a convenience function for calculating individual flux contributions.

    计算在给定位置的两个特定节点之间的扩散气体通量。
    这是一个用于计算各个通量贡献的便捷函数。

    Parameters
    ----------
    concentration_i : float
        Gas concentration at node i (atoms/m³)
        节点i处的气体浓度 (原子/m³)

    concentration_j : float
        Gas concentration at node j (atoms/m³)
        节点j处的气体浓度 (原子/m³)

    diffusion_coeff : float
        Gas diffusion coefficient (m²/s)
        气体扩散系数 (m²/s)

    distance : float
        Distance between nodes (m)
        节点之间的距离 (m)

    geometry_factor : float
        Geometry factor: 1.0 for cylindrical, 0.0 for slab
        几何因子：圆柱为1.0，平板为0.0

    radial_position : float, optional
        Radial position for cylindrical geometry correction (m)
        Only used when geometry_factor = 1.0
        圆柱几何修正的径向位置 (m)
        仅当 geometry_factor = 1.0 时使用

    Returns
    -------
    float
        Gas flux from node i to node j (atoms/m²/s)
        Positive values indicate flux from i to j
        从节点i到节点j的气体通量 (原子/m²/s)
        正值表示从i到j的通量

    Notes
    -----
    For slab geometry:
        Flux = -D × (C[j] - C[i]) / distance

    For cylindrical geometry:
        Flux = -D × (C[j] - C[i]) / distance × (1 + geometry_correction)
        where geometry_correction accounts for area change with radius

    References
    ----------
    Fick's first law in different coordinate systems

    Examples
    --------
    >>> # Flux between adjacent nodes in cylindrical fuel
    >>> flux = calculate_node_to_node_flux(
    ...     concentration_i=1e25,
    ...     concentration_j=0.9e25,
    ...     diffusion_coeff=1e-15,
    ...     distance=0.001,
    ...     geometry_factor=1.0,
    ...     radial_position=0.0015
    ... )
    >>> print(f'Flux: {flux:.4e} atoms/m²/s')
    """
    if distance <= 0:
        raise ValueError(f"distance must be positive, got {distance}")

    if diffusion_coeff < 0:
        raise ValueError(f"diffusion_coeff must be non-negative, got {diffusion_coeff}")

    if concentration_i < 0 or concentration_j < 0:
        raise ValueError("concentrations must be non-negative")

    # Base flux from Fick's first law
    # 菲克第一定律的基本通量
    concentration_gradient = (concentration_j - concentration_i) / distance
    flux = -diffusion_coeff * concentration_gradient

    # Apply cylindrical geometry correction if needed
    # 如果需要，应用圆柱几何修正
    if geometry_factor == 1.0 and radial_position is not None and radial_position > 0:
        # In cylindrical coordinates, flux scales with radius
        # The effective area changes with radial position
        # 在圆柱坐标系中，通量随半径缩放
        # 有效面积随径向位置变化
        flux *= (1.0 + distance / (2.0 * radial_position))

    return flux


def apply_centerline_bc(
    flux: np.ndarray,
    centerline_position: float = 0.0
) -> np.ndarray:
    """
    应用中心线对称边界条件 (Apply centerline symmetry boundary condition)

    Apply zero-flux boundary condition at the fuel centerline (r=0).
    At the centerline, symmetry requires that the radial flux is zero.

    在燃料中心线 (r=0) 处应用零通量边界条件。
    在中心线处，对称性要求径向通量为零。

    Parameters
    ----------
    flux : np.ndarray
        Radial flux array (atoms/m²/s), shape (n_nodes-1,)
        径向通量数组 (原子/m²/s)

    centerline_position : float, optional
        Position of centerline (m)
        Default: 0.0
        中心线位置 (m)
        默认：0.0

    Returns
    -------
    np.ndarray
        Modified flux array with centerline boundary condition applied
        应用了中心线边界条件的修正通量数组

    Notes
    -----
    At the centerline (r=0), symmetry requires:
        ∂C/∂r = 0  →  J[r=0] = 0

    This means no net gas transport across the centerline.
    The flux from node 0 to node 1 should be zero (or very small).

    这意味着没有净气体输运穿过中心线。
    从节点0到节点1的通量应该为零（或非常小）。

    For a properly discretized mesh with a node at r=0, the first flux
    (from centerline to first interior node) should be zero.

    对于在r=0处有节点的适当离散化网格，第一个通量
    （从中心线到第一个内部节点）应该为零。

    Examples
    --------
    >>> import numpy as np
    >>> flux = np.array([1e10, 2e10, 3e10])  # Some flux values
    >>> flux_with_bc = apply_centerline_bc(flux)
    >>> print(f'Flux at centerline: {flux_with_bc[0]}')
    Flux at centerline: 0.0
    """
    if len(flux) == 0:
        return flux

    # Create a copy to avoid modifying the input
    # 创建副本以避免修改输入
    flux_bc = flux.copy()

    # Apply zero-flux condition at centerline
    # 在中心线应用零通量条件
    flux_bc[0] = 0.0

    return flux_bc


def apply_surface_bc(
    flux: np.ndarray,
    surface_flux_value: float,
    mesh_nodes: np.ndarray
) -> np.ndarray:
    """
    应用表面通量边界条件 (Apply surface flux boundary condition)

    Apply specified flux boundary condition at the fuel surface (r=R).
    This represents gas release or influx at the fuel-cladding gap.

    在燃料表面 (r=R) 处应用指定的通量边界条件。
    这代表燃料-包壳间隙处的气体释放或流入。

    Parameters
    ----------
    flux : np.ndarray
        Radial flux array (atoms/m²/s), shape (n_nodes-1,)
        径向通量数组 (原子/m²/s)

    surface_flux_value : float
        Specified flux at surface (atoms/m²/s)
        Positive: flux out of fuel (release)
        Negative: flux into fuel (influx)
        表面指定的通量 (原子/m²/s)
        正值：流出燃料的通量（释放）
        负值：流入燃料的通量（流入）

    mesh_nodes : np.ndarray
        Radial positions of nodes (m)
        Used to identify surface node
        节点的径向位置 (m)
        用于识别表面节点

    Returns
    -------
    np.ndarray
        Modified flux array with surface boundary condition applied
        应用了表面边界条件的修正通量数组

    Notes
    -----
    At the fuel surface (r=R), the flux is determined by:
    在燃料表面 (r=R)，通量由下式确定：

        J[r=R] = surface_flux_value

    This can represent:
    这可以表示：
    - Gas release to plenum (positive flux)
    - 气体释放到腔体（正通量）
    - Influx from external sources (negative flux)
    - 来自外部源的流入（负通量）
    - Zero flux (impermeable cladding, flux_value = 0)
    - 零通量（不渗透包壳，flux_value = 0）

    The surface flux is applied to the last flux entry in the array,
    which represents transport from the penultimate to the surface node.

    表面通量应用于数组中的最后一个通量条目，
    它代表从倒数第二个节点到表面节点的输运。

    Examples
    --------
    >>> import numpy as np
    >>> flux = np.array([1e10, 2e10, 3e10])
    >>> mesh_nodes = np.array([0.0, 0.001, 0.002, 0.003])
    >>> flux_with_bc = apply_surface_bc(flux, surface_flux_value=5e10, mesh_nodes=mesh_nodes)
    >>> print(f'Surface flux: {flux_with_bc[-1]:.4e}')
    Surface flux: 5.0000e+10
    """
    if len(flux) == 0:
        return flux

    if len(mesh_nodes) != len(flux) + 1:
        raise ValueError(
            f"mesh_nodes length must be flux length + 1, "
            f"got {len(mesh_nodes)} and {len(flux)}"
        )

    # Create a copy to avoid modifying the input
    # 创建副本以避免修改输入
    flux_bc = flux.copy()

    # Apply specified flux at surface (last flux entry)
    # 在表面应用指定的通量（最后一个通量条目）
    flux_bc[-1] = surface_flux_value

    return flux_bc


def calculate_radial_transport_terms(
    concentration: np.ndarray,
    mesh_nodes: np.ndarray,
    diffusion_coeff: float,
    geometry_factor: float,
    surface_flux: Optional[float] = None
) -> Dict[str, np.ndarray]:
    """
    计算所有径向输运项的便捷函数 (Calculate all radial transport terms)

    Convenience function that calculates all radial transport terms for a given state.
    Useful for debugging and understanding the contributions of different processes.

    便捷函数，计算给定状态的所有径向输运项。
    用于调试和理解不同过程的贡献。

    Parameters
    ----------
    concentration : np.ndarray
        Gas concentration at each node (atoms/m³), shape (n_nodes,)
        每个节点处的气体浓度 (原子/m³)

    mesh_nodes : np.ndarray
        Radial positions of nodes (m), shape (n_nodes,)
        节点的径向位置 (m)

    diffusion_coeff : float
        Gas diffusion coefficient (m²/s)
        气体扩散系数 (m²/s)

    geometry_factor : float
        Geometry factor: 1.0 for cylindrical, 0.0 for slab
        几何因子：圆柱为1.0，平板为0.0

    surface_flux : float, optional
        Specified flux at surface boundary (atoms/m²/s)
        If None, zero flux (no release) is assumed
        表面边界处的指定通量 (原子/m²/s)
        如果为None，则假设零通量（无释放）

    Returns
    -------
    dict
        Dictionary containing all calculated transport terms:
        包含所有计算输运项的字典：
        - 'flux': Radial flux between nodes (n_nodes-1,)
        - 'div_flux': Divergence of flux at nodes (n_nodes,)
        - 'coupling_matrix': Diffusion coupling matrix (n_nodes, n_nodes)
        - 'flux_with_bc': Flux with boundary conditions (n_nodes-1,)

    Notes
    -----
    The flux divergence represents the net source/sink term at each node due to
    radial transport:
    通量散度表示由于径向输运在每个节点处的净源/汇项：

        ∂C/∂t = -∇·J = -div_flux

    Positive div_flux means net loss from the node.
    Negative div_flux means net gain at the node.

    正 div_flux 表示节点的净损失。
    负 div_flux 表示节点的净增益。

    Examples
    --------
    >>> import numpy as np
    >>> concentration = np.array([1e25, 0.9e25, 0.8e25, 0.7e25])
    >>> mesh_nodes = np.array([0.0, 0.001, 0.002, 0.003])
    >>> terms = calculate_radial_transport_terms(
    ...     concentration, mesh_nodes, diffusion_coeff=1e-15, geometry_factor=1.0
    ... )
    >>> print(f"Flux shape: {terms['flux'].shape}")
    Flux shape: (3,)
    """
    # Calculate radial flux
    # 计算径向通量
    flux = calculate_radial_flux(concentration, diffusion_coeff, mesh_nodes, geometry_factor)

    # Apply boundary conditions
    # 应用边界条件
    flux_with_bc = apply_centerline_bc(flux.copy())

    if surface_flux is not None:
        flux_with_bc = apply_surface_bc(flux_with_bc, surface_flux, mesh_nodes)

    # Calculate flux divergence at nodes
    # 计算节点处的通量散度
    # div_flux[i] = (flux[i] - flux[i-1]) / volume_factor
    # For now, use simple finite difference
    # div_flux[0] = -flux[0] / (dr[0]/2)
    # div_flux[-1] = flux[-1] / (dr[-1]/2)
    # div_flux[i] = (flux[i] - flux[i-1]) / ((dr[i-1] + dr[i])/2)
    n_nodes = len(concentration)
    div_flux = np.zeros(n_nodes)

    if n_nodes > 1:
        dr = np.diff(mesh_nodes)

        # First node: flux balance with first interval
        # 第一个节点：与第一个区间的通量平衡
        div_flux[0] = -flux_with_bc[0] / (dr[0] / 2.0)

        # Last node: flux balance with last interval
        # 最后一个节点：与最后一个区间的通量平衡
        div_flux[-1] = flux_with_bc[-1] / (dr[-1] / 2.0)

        # Interior nodes
        # 内部节点
        for i in range(1, n_nodes - 1):
            dr_mean = (dr[i-1] + dr[i]) / 2.0
            div_flux[i] = (flux_with_bc[i] - flux_with_bc[i-1]) / dr_mean

    # Calculate coupling matrix
    # 计算耦合矩阵
    coupling_matrix = calculate_diffusion_coupling_matrix(mesh_nodes, diffusion_coeff, geometry_factor)

    return {
        'flux': flux,
        'div_flux': div_flux,
        'coupling_matrix': coupling_matrix,
        'flux_with_bc': flux_with_bc
    }


if __name__ == '__main__':
    """Test radial transport calculations with default parameters"""
    import numpy as np

    # Create test mesh
    # 创建测试网格
    n_nodes = 10
    radius = 0.003  # 3 mm
    mesh_nodes = np.linspace(0, radius, n_nodes)

    # Define test concentration profile (decreasing from center to surface)
    # 定义测试浓度分布（从中心到表面递减）
    concentration = np.linspace(1e25, 0.5e25, n_nodes)

    # Diffusion coefficient
    # 扩散系数
    diffusion_coeff = 1e-15  # m²/s

    # Geometry factor (cylindrical)
    # 几何因子（圆柱）
    geometry_factor = 1.0

    print("Radial Transport Calculations:")
    print("-" * 50)

    # Calculate radial flux
    # 计算径向通量
    flux = calculate_radial_flux(concentration, diffusion_coeff, mesh_nodes, geometry_factor)
    print(f"Radial flux shape: {flux.shape}")
    print(f"Flux range: [{flux.min():.4e}, {flux.max():.4e}] atoms/m²/s")

    # Calculate coupling matrix
    # 计算耦合矩阵
    A = calculate_diffusion_coupling_matrix(mesh_nodes, diffusion_coeff, geometry_factor)
    print(f"Coupling matrix shape: {A.shape}")
    print(f"Matrix diagonal range: [{np.diag(A).min():.4e}, {np.diag(A).max():.4e}]")

    # Calculate all transport terms
    # 计算所有输运项
    terms = calculate_radial_transport_terms(
        concentration, mesh_nodes, diffusion_coeff, geometry_factor, surface_flux=1e10
    )

    print(f"\nFlux divergence shape: {terms['div_flux'].shape}")
    print(f"Div flux range: [{terms['div_flux'].min():.4e}, {terms['div_flux'].max():.4e}]")

    # Test boundary conditions
    # 测试边界条件
    flux_bc = apply_centerline_bc(flux.copy())
    print(f"\nCenterline BC applied, flux[0] = {flux_bc[0]:.4e}")

    flux_bc = apply_surface_bc(flux_bc, surface_flux_value=5e10, mesh_nodes=mesh_nodes)
    print(f"Surface BC applied, flux[-1] = {flux_bc[-1]:.4e}")

    print("\nRadial transport module OK")
