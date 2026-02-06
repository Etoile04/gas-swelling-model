"""
Radial Mesh for 1D Spatial Discretization (一维空间离散化径向网格)

This module provides the RadialMesh class for creating 1D spatial meshes
in cylindrical or slab geometries. It supports uniform and non-uniform
node distributions for gas swelling simulations.

模块结构 (Module Structure):
- RadialMesh: Main class for 1D radial mesh generation
- Supports cylindrical and slab geometries
- Provides node positions, spacing, and geometry factors

主要类 (Main Classes):
- RadialMesh: 一维径向网格类 (1D radial mesh class)

使用示例 (Usage Example):
    >>> from gas_swelling.models.radial_mesh import RadialMesh
    >>>
    >>> # Create uniform cylindrical mesh
    >>> mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')
    >>> print(f'Number of nodes: {len(mesh.nodes)}')
    >>> print(f'Geometry: {mesh.geometry}')
    >>>
    >>> # Access node positions and spacing
    >>> r = mesh.nodes  # radial positions of nodes
    >>> dr = mesh.dr    # spacing between nodes
"""

import numpy as np
from typing import Optional, Literal, Tuple
from enum import Enum


class GeometryType(Enum):
    """
    Geometry type enumeration (几何类型枚举)

    支持的几何类型 (Supported geometry types):
    - cylindrical: Cylindrical geometry (圆柱坐标系)
    - slab: Slab/planar geometry (平板坐标系)
    """
    CYLINDRICAL = 'cylindrical'
    SLAB = 'slab'


class RadialMesh:
    """
    一维径向网格类 (1D Radial Mesh Class)

    This class provides a 1D spatial discretization mesh for radial gas
    swelling simulations. It supports both cylindrical and slab geometries
    with configurable node distributions.

    网格功能 (Mesh Features):
    - 均匀或非均匀节点分布 (uniform or non-uniform node distribution)
    - 支持圆柱和平板几何 (supports cylindrical and slab geometries)
    - 计算几何因子用于输运方程 (calculates geometry factors for transport)
    - 提供节点位置和间距信息 (provides node positions and spacing info)

    参数 (Parameters):
        n_nodes : int
            节点数量 (number of radial nodes)
            Must be >= 2 (至少2个节点)

        radius : float, optional
            燃料芯块半径 (fuel pellet radius) in meters
            Default: 0.003 m (3 mm, typical fuel pin radius)

        geometry : str or GeometryType, optional
            几何类型 (geometry type)
            Options: 'cylindrical' (default) or 'slab'

        spacing : str, optional
            节点间距类型 (node spacing type)
            Options: 'uniform' (default), 'geometric'

        growth_ratio : float, optional
            几何间距的增长比率 (growth ratio for geometric spacing)
            Only used when spacing='geometric'
            Default: 1.15 (creates 15% growth between adjacent intervals)
            Larger values create more refined boundary layer at centerline

    属性 (Attributes):
        n_nodes : int
            节点数量 (number of nodes)

        radius : float
            芯块半径 (pellet radius)

        geometry : str
            几何类型 (geometry type: 'cylindrical' or 'slab')

        nodes : np.ndarray
            节点径向位置数组 (radial positions of nodes), shape (n_nodes,)

        dr : np.ndarray
            节点间距数组 (spacing between nodes), shape (n_nodes-1,)

        node_centers : np.ndarray
            单元中心位置 (cell center positions), shape (n_nodes-1,)

        geometry_factor : float
            几何因子 (geometry factor): 1.0 for cylindrical, 0.0 for slab

    异常 (Raises):
        ValueError: If n_nodes < 2 or radius <= 0 or invalid geometry type

    示例 (Example):
        >>> # Create mesh for 3mm radius fuel pin with 10 nodes
        >>> mesh = RadialMesh(n_nodes=10, radius=0.003)
        >>> print(f'Nodes: {len(mesh.nodes)}, Geometry: {mesh.geometry}')
        Nodes: 10, Geometry: cylindrical

        >>> # Access radial positions
        >>> r = mesh.nodes
        >>> print(f'Centerline: {r[0]:.4f} m, Surface: {r[-1]:.4f} m')
        Centerline: 0.0000 m, Surface: 0.0030 m
    """

    # Default parameters (默认参数)
    DEFAULT_RADIUS = 0.003  # 3 mm (typical fuel pin radius, typical fuel pin radius)
    DEFAULT_N_NODES = 10    # Default number of nodes (默认节点数)
    DEFAULT_GEOMETRY = 'cylindrical'  # Default geometry (默认几何)
    DEFAULT_GROWTH_RATIO = 1.2  # Default growth ratio for geometric spacing (20% growth per interval)

    def __init__(
        self,
        n_nodes: Optional[int] = None,
        radius: Optional[float] = None,
        geometry: Optional[Literal['cylindrical', 'slab']] = None,
        spacing: Optional[Literal['uniform', 'geometric']] = None,
        growth_ratio: Optional[float] = None
    ):
        """
        初始化径向网格 (Initialize radial mesh)

        参数 (Parameters):
            n_nodes : int, optional
                节点数量 (number of radial nodes)
                Default: 10

            radius : float, optional
                芯块半径 (pellet radius) in meters
                Default: 0.003 m (3 mm)

            geometry : str, optional
                几何类型 (geometry type)
                Options: 'cylindrical' (default) or 'slab'

            spacing : str, optional
                节点间距类型 (node spacing type)
                Options: 'uniform' (default), 'geometric'

            growth_ratio : float, optional
                几何间距的增长比率 (growth ratio for geometric spacing)
                Only used when spacing='geometric'
                Default: 1.15 (creates 15% growth between adjacent intervals)

        异常 (Raises):
            ValueError: If parameters are invalid

        示例 (Example):
            >>> mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')
            >>> print(f'Mesh created with {len(mesh.nodes)} nodes')
            Mesh created with 10 nodes
        """
        # Set parameters with defaults (设置参数和默认值)
        self.n_nodes = n_nodes if n_nodes is not None else self.DEFAULT_N_NODES
        self.radius = radius if radius is not None else self.DEFAULT_RADIUS
        self._geometry_str = geometry if geometry is not None else self.DEFAULT_GEOMETRY
        self._spacing = spacing if spacing is not None else 'uniform'
        self._growth_ratio = growth_ratio if growth_ratio is not None else self.DEFAULT_GROWTH_RATIO

        # Validate parameters (验证参数)
        self._validate_parameters()

        # Generate mesh (生成网格)
        self._generate_mesh()

        # Set geometry factor (设置几何因子)
        self._set_geometry_factor()

    def _validate_parameters(self) -> None:
        """
        验证输入参数 (Validate input parameters)

        异常 (Raises):
            ValueError: If any parameter is invalid
        """
        if self.n_nodes < 2:
            raise ValueError(
                f'n_nodes must be >= 2, got {self.n_nodes}. '
                f'At least 2 nodes are required (centerline and surface).'
            )

        if self.radius <= 0:
            raise ValueError(
                f'radius must be > 0, got {self.radius}. '
                f'Radius must be a positive value in meters.'
            )

        valid_geometries = ['cylindrical', 'slab']
        if self._geometry_str not in valid_geometries:
            raise ValueError(
                f"geometry must be one of {valid_geometries}, got '{self._geometry_str}'"
            )

        valid_spacing = ['uniform', 'geometric']
        if self._spacing not in valid_spacing:
            raise ValueError(
                f"spacing must be one of {valid_spacing}, got '{self._spacing}'"
            )

        # Validate growth_ratio for geometric spacing
        if self._spacing == 'geometric':
            if self._growth_ratio <= 1.0:
                raise ValueError(
                    f'growth_ratio must be > 1.0 for geometric spacing, got {self._growth_ratio}. '
                    f'Values > 1.0 create increasing spacing from centerline to surface.'
                )
            if self._growth_ratio > 2.0:
                import warnings
                warnings.warn(
                    f"growth_ratio={self._growth_ratio} is very large. "
                    f"This may create extremely coarse spacing near the surface. "
                    f"Recommended range is 1.05 to 1.5.",
                    UserWarning
                )

    def _generate_mesh(self) -> None:
        """
        生成网格节点 (Generate mesh nodes)

        Creates the radial node positions based on the spacing strategy.
        - Uniform spacing: nodes evenly distributed from centerline (r=0) to surface (r=radius)
        - Geometric spacing: nodes use geometric progression for boundary layer refinement

        生成径向节点位置 (Generates radial node positions):
        - 均匀间距 (uniform spacing): 节点均匀分布在从中心线到表面
        - 几何间距 (geometric spacing): 节点使用几何级数以实现边界层细化
        - 节点位置包含中心线 (nodes include centerline at r=0)
        - 节点位置包含表面 (nodes include surface at r=radius)
        """
        if self._spacing == 'uniform':
            # Uniform spacing: nodes from 0 to radius
            # 均匀间距：节点从0到radius
            self._nodes = np.linspace(0, self.radius, self.n_nodes)
        elif self._spacing == 'geometric':
            # Geometric spacing: dr[i] = dr[0] * q^i
            # 几何间距：使用几何级数生成节点位置
            # This creates finer spacing near centerline (boundary layer refinement)
            # 这会在中心线附近创建更细的间距（边界层细化）
            q = self._growth_ratio
            n_intervals = self.n_nodes - 1

            # Calculate first interval using geometric series sum formula
            # radius = dr_0 * (1 - q^n) / (1 - q)
            # dr_0 = radius * (1 - q) / (1 - q^n)
            # 使用几何级数求和公式计算第一个间距
            dr_0 = self.radius * (1 - q) / (1 - q ** n_intervals)

            # Generate cumulative node positions
            # r[i] = sum(dr[0:i]) = dr_0 * (1 - q^i) / (1 - q)
            # 生成累积节点位置
            i = np.arange(self.n_nodes)
            self._nodes = dr_0 * (1 - q ** i) / (1 - q)

            # Ensure last node exactly at radius (fix floating point errors)
            # 确保最后一个节点精确位于半径处（修正浮点误差）
            self._nodes[-1] = self.radius
        else:
            # Fallback to uniform for unknown spacing types
            # 未知间距类型，回退到均匀间距
            self._nodes = np.linspace(0, self.radius, self.n_nodes)

        # Calculate spacing between nodes (计算节点间距)
        self._dr = np.diff(self._nodes)

    def _set_geometry_factor(self) -> None:
        """
        设置几何因子 (Set geometry factor)

        Geometry factor is used in transport equations to account for
        coordinate system:
        - cylindrical: factor = 1 (area scales with radius)
        - slab: factor = 0 (area is constant)

        几何因子用于输运方程以考虑坐标系:
        - 圆柱坐标系 (cylindrical): factor = 1 (面积随半径变化)
        - 平板坐标系 (slab): factor = 0 (面积恒定)
        """
        if self.geometry == 'cylindrical':
            self._geometry_factor = 1.0
        else:  # slab
            self._geometry_factor = 0.0

    @property
    def geometry(self) -> str:
        """
        获取几何类型 (Get geometry type)

        返回 (Returns):
            str: 'cylindrical' or 'slab'
        """
        return self._geometry_str

    @property
    def nodes(self) -> np.ndarray:
        """
        获取节点位置数组 (Get node positions array)

        返回 (Returns):
            np.ndarray: Radial positions of nodes, shape (n_nodes,)
                      单位: meters (单位: 米)
        """
        return self._nodes

    @property
    def dr(self) -> np.ndarray:
        """
        获取节点间距数组 (Get node spacing array)

        返回 (Returns):
            np.ndarray: Spacing between adjacent nodes, shape (n_nodes-1,)
                      单位: meters (单位: 米)
        """
        return self._dr

    @property
    def node_centers(self) -> np.ndarray:
        """
        获取单元中心位置 (Get cell center positions)

        Returns the midpoint positions between adjacent nodes, representing
        the centers of control volumes for finite volume discretization.

        返回相邻节点之间的中点位置，代表有限体积离散化的控制体中心。

        返回 (Returns):
            np.ndarray: Cell center positions, shape (n_nodes-1,)
                      单位: meters (单位: 米)
        """
        return (self._nodes[:-1] + self._nodes[1:]) / 2.0

    @property
    def geometry_factor(self) -> float:
        """
        获取几何因子 (Get geometry factor)

        几何因子用于输运方程 (Geometry factor for transport equations):
        - 1.0 for cylindrical geometry (圆柱几何)
        - 0.0 for slab geometry (平板几何)

        返回 (Returns):
            float: Geometry factor (1.0 or 0.0)
        """
        return self._geometry_factor

    def get_node_volume(self, node_index: int, height: float = 1.0) -> float:
        """
        计算节点的控制体体积 (Calculate control volume for a node)

        For cylindrical geometry, volume depends on radial position.
        For slab geometry, volume is simply the spacing times height.

        对于圆柱几何，体积取决于径向位置。
        对于平板几何，体积就是间距乘以高度。

        参数 (Parameters):
            node_index : int
                节点索引 (node index), 0 to n_nodes-2

            height : float, optional
                轴向高度 (axial height) in meters
                Default: 1.0 m (for per-meter calculations)

        返回 (Returns):
            float: Control volume in cubic meters (m³)

        异常 (Raises):
            IndexError: If node_index is out of range

        示例 (Example):
            >>> mesh = RadialMesh(n_nodes=10, radius=0.003)
            >>> volume = mesh.get_node_volume(0)  # First cell volume
            >>> print(f'First cell volume: {volume:.2e} m³')
        """
        if node_index < 0 or node_index >= self.n_nodes - 1:
            raise IndexError(
                f'node_index must be in [0, {self.n_nodes-2}], got {node_index}'
            )

        if self.geometry == 'cylindrical':
            # Cylindrical: volume of annular ring
            # 圆柱：环形体积
            r_inner = self._nodes[node_index]
            r_outer = self._nodes[node_index + 1]
            volume = np.pi * height * (r_outer**2 - r_inner**2)
        else:
            # Slab: volume = spacing * height * unit_depth
            # 平板：体积 = 间距 * 高度 * 单位深度
            volume = self._dr[node_index] * height * 1.0

        return volume

    def get_total_volume(self, height: float = 1.0) -> float:
        """
        计算总体积 (Calculate total volume)

        参数 (Parameters):
            height : float, optional
                轴向高度 (axial height) in meters
                Default: 1.0 m

        返回 (Returns):
            float: Total volume in cubic meters (m³)

        示例 (Example):
            >>> mesh = RadialMesh(n_nodes=10, radius=0.003)
            >>> total_vol = mesh.get_total_volume()
            >>> print(f'Total volume: {total_vol:.2e} m³')
        """
        if self.geometry == 'cylindrical':
            return np.pi * height * self.radius**2
        else:
            return self.radius * height * 1.0

    def __repr__(self) -> str:
        """
        字符串表示 (String representation)

        返回 (Returns):
            str: String representation of the mesh
        """
        return (
            f'RadialMesh(n_nodes={self.n_nodes}, '
            f'radius={self.radius:.3e} m, '
            f'geometry={self.geometry})'
        )

    def __len__(self) -> int:
        """
        返回节点数量 (Return number of nodes)

        返回 (Returns):
            int: Number of nodes in the mesh
        """
        return self.n_nodes
