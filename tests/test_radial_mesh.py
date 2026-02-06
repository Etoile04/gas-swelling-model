"""
Test RadialMesh functionality

This module contains comprehensive tests for the RadialMesh class,
including initialization, geometry calculations, and volume computations.
"""

import pytest
import numpy as np
from gas_swelling.models.radial_mesh import RadialMesh, GeometryType


class TestRadialMeshInitialization:
    """Test mesh initialization and setup"""

    def test_default_initialization(self):
        """Test that mesh can be initialized with default parameters"""
        mesh = RadialMesh()
        assert mesh is not None
        assert mesh.n_nodes == 10  # DEFAULT_N_NODES
        assert mesh.radius == 0.003  # DEFAULT_RADIUS
        assert mesh.geometry == 'cylindrical'  # DEFAULT_GEOMETRY

    def test_custom_parameters_initialization(self):
        """Test that mesh can be initialized with custom parameters"""
        mesh = RadialMesh(n_nodes=20, radius=0.005, geometry='slab')
        assert mesh.n_nodes == 20
        assert mesh.radius == 0.005
        assert mesh.geometry == 'slab'

    def test_cylindrical_geometry_initialization(self):
        """Test initialization with cylindrical geometry"""
        mesh = RadialMesh(n_nodes=15, radius=0.004, geometry='cylindrical')
        assert mesh.geometry == 'cylindrical'
        assert mesh.geometry_factor == 1.0

    def test_slab_geometry_initialization(self):
        """Test initialization with slab geometry"""
        mesh = RadialMesh(n_nodes=15, radius=0.004, geometry='slab')
        assert mesh.geometry == 'slab'
        assert mesh.geometry_factor == 0.0

    def test_uniform_spacing_initialization(self):
        """Test initialization with uniform spacing"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, spacing='uniform')
        assert len(mesh.nodes) == 10
        # Check uniform spacing
        dr = mesh.dr
        assert np.allclose(dr, dr[0])  # All spacings should be equal

    def test_geometric_spacing_initialization(self):
        """Test initialization with geometric spacing"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, spacing='geometric', growth_ratio=1.2)
        assert len(mesh.nodes) == 10
        # Check geometric spacing (should increase)
        dr = mesh.dr
        # Each spacing should be larger than the previous
        assert np.all(np.diff(dr) > 0)

    def test_invalid_n_nodes_too_small(self):
        """Test that n_nodes < 2 raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(n_nodes=1)
        assert 'n_nodes must be >= 2' in str(excinfo.value)

    def test_invalid_n_nodes_zero(self):
        """Test that n_nodes = 0 raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(n_nodes=0)
        assert 'n_nodes must be >= 2' in str(excinfo.value)

    def test_invalid_radius_negative(self):
        """Test that negative radius raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(radius=-0.001)
        assert 'radius must be > 0' in str(excinfo.value)

    def test_invalid_radius_zero(self):
        """Test that zero radius raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(radius=0)
        assert 'radius must be > 0' in str(excinfo.value)

    def test_invalid_geometry(self):
        """Test that invalid geometry raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(geometry='spherical')
        assert 'geometry must be one of' in str(excinfo.value)

    def test_invalid_spacing(self):
        """Test that invalid spacing raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(spacing='exponential')
        assert 'spacing must be one of' in str(excinfo.value)

    def test_invalid_growth_ratio_geometric(self):
        """Test that growth_ratio <= 1.0 for geometric spacing raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(spacing='geometric', growth_ratio=1.0)
        assert 'growth_ratio must be > 1.0' in str(excinfo.value)

    def test_invalid_growth_ratio_too_small(self):
        """Test that growth_ratio < 1.0 for geometric spacing raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            RadialMesh(spacing='geometric', growth_ratio=0.9)
        assert 'growth_ratio must be > 1.0' in str(excinfo.value)

    def test_large_growth_ratio_warning(self):
        """Test that large growth_ratio raises warning"""
        with pytest.warns(UserWarning) as warning_list:
            RadialMesh(spacing='geometric', growth_ratio=2.5)
        assert len(warning_list) == 1
        assert 'growth_ratio' in str(warning_list[0].message)

    def test_len(self):
        """Test __len__ returns correct number of nodes"""
        mesh = RadialMesh(n_nodes=15)
        assert len(mesh) == 15


class TestRadialMeshProperties:
    """Test mesh properties"""

    def test_geometry_property(self):
        """Test geometry property"""
        mesh_cyl = RadialMesh(geometry='cylindrical')
        assert mesh_cyl.geometry == 'cylindrical'

        mesh_slab = RadialMesh(geometry='slab')
        assert mesh_slab.geometry == 'slab'

    def test_nodes_property(self):
        """Test nodes property"""
        mesh = RadialMesh(n_nodes=10, radius=0.003)
        nodes = mesh.nodes

        # Check that nodes is a numpy array
        assert isinstance(nodes, np.ndarray)

        # Check that nodes has correct length
        assert len(nodes) == 10

        # Check that nodes are monotonically increasing
        assert np.all(np.diff(nodes) > 0)

        # Check first node is at centerline (r=0)
        assert nodes[0] == 0.0

        # Check last node is at surface (r=radius)
        assert np.isclose(nodes[-1], mesh.radius)

    def test_nodes_uniform_spacing(self):
        """Test nodes are evenly distributed for uniform spacing"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, spacing='uniform')
        nodes = mesh.nodes

        # Expected uniform spacing
        expected_dr = mesh.radius / (mesh.n_nodes - 1)
        expected_nodes = np.linspace(0, mesh.radius, mesh.n_nodes)

        assert np.allclose(nodes, expected_nodes)

    def test_nodes_geometric_spacing(self):
        """Test nodes follow geometric progression for geometric spacing"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, spacing='geometric', growth_ratio=1.2)
        nodes = mesh.nodes
        dr = mesh.dr

        # Check that spacing increases geometrically
        # dr[i] should be approximately dr[0] * q^i
        q = mesh._growth_ratio
        dr_0 = dr[0]

        for i in range(len(dr)):
            expected_dr = dr_0 * (q ** i)
            # Allow some tolerance due to the normalization at the last node
            assert abs(dr[i] - expected_dr) / expected_dr < 0.01

    def test_dr_property(self):
        """Test dr property"""
        mesh = RadialMesh(n_nodes=10, radius=0.003)
        dr = mesh.dr

        # Check that dr is a numpy array
        assert isinstance(dr, np.ndarray)

        # Check that dr has correct length (n_nodes - 1)
        assert len(dr) == 9

        # Check that all spacings are positive
        assert np.all(dr > 0)

    def test_dr_uniform(self):
        """Test dr is constant for uniform spacing"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, spacing='uniform')
        dr = mesh.dr

        # All spacings should be equal
        assert np.allclose(dr, dr[0])

        # Expected spacing
        expected_dr = mesh.radius / (mesh.n_nodes - 1)
        assert np.isclose(dr[0], expected_dr)

    def test_dr_geometric(self):
        """Test dr increases for geometric spacing"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, spacing='geometric', growth_ratio=1.2)
        dr = mesh.dr

        # Each spacing should be larger than the previous
        assert np.all(np.diff(dr) > 0)

        # First spacing should be smallest
        assert dr[0] == dr.min()

        # Last spacing should be largest
        assert dr[-1] == dr.max()

    def test_node_centers_property(self):
        """Test node_centers property"""
        mesh = RadialMesh(n_nodes=10, radius=0.003)
        nodes = mesh.nodes
        centers = mesh.node_centers

        # Check that centers is a numpy array
        assert isinstance(centers, np.ndarray)

        # Check that centers has correct length (n_nodes - 1)
        assert len(centers) == 9

        # Check that centers are at midpoints
        expected_centers = (nodes[:-1] + nodes[1:]) / 2.0
        assert np.allclose(centers, expected_centers)

        # Check that centers are between nodes
        assert np.all(centers > nodes[:-1])
        assert np.all(centers < nodes[1:])

    def test_geometry_factor_cylindrical(self):
        """Test geometry_factor for cylindrical geometry"""
        mesh = RadialMesh(geometry='cylindrical')
        assert mesh.geometry_factor == 1.0

    def test_geometry_factor_slab(self):
        """Test geometry_factor for slab geometry"""
        mesh = RadialMesh(geometry='slab')
        assert mesh.geometry_factor == 0.0


class TestRadialMeshVolume:
    """Test volume calculation methods"""

    def test_get_node_volume_cylindrical_center(self):
        """Test node volume at centerline for cylindrical geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')

        # First node (near centerline)
        volume = mesh.get_node_volume(0)
        assert volume > 0

        # Expected volume: pi * h * (r_1^2 - r_0^2) where r_0 = 0
        r_1 = mesh.nodes[1]
        expected_volume = np.pi * 1.0 * (r_1**2 - 0)
        assert np.isclose(volume, expected_volume)

    def test_get_node_volume_cylindrical_middle(self):
        """Test node volume in middle for cylindrical geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')

        # Middle node
        node_idx = 5
        volume = mesh.get_node_volume(node_idx)
        assert volume > 0

        # Expected volume: pi * h * (r_outer^2 - r_inner^2)
        r_inner = mesh.nodes[node_idx]
        r_outer = mesh.nodes[node_idx + 1]
        expected_volume = np.pi * 1.0 * (r_outer**2 - r_inner**2)
        assert np.isclose(volume, expected_volume)

    def test_get_node_volume_cylindrical_with_custom_height(self):
        """Test node volume with custom height for cylindrical geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')
        height = 0.5  # 0.5 meters

        volume = mesh.get_node_volume(0, height=height)
        assert volume > 0

        # Volume should scale with height
        volume_default_height = mesh.get_node_volume(0, height=1.0)
        assert np.isclose(volume, volume_default_height * height)

    def test_get_node_volume_slab(self):
        """Test node volume for slab geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='slab')

        # Slab volume: dr * height * unit_depth
        volume = mesh.get_node_volume(0)
        expected_volume = mesh.dr[0] * 1.0 * 1.0
        assert np.isclose(volume, expected_volume)

    def test_get_node_volume_invalid_index(self):
        """Test that invalid node_index raises IndexError"""
        mesh = RadialMesh(n_nodes=10)

        # Negative index
        with pytest.raises(IndexError) as excinfo:
            mesh.get_node_volume(-1)
        assert 'node_index must be in' in str(excinfo.value)

        # Index too large (max is n_nodes - 2)
        with pytest.raises(IndexError) as excinfo:
            mesh.get_node_volume(9)  # n_nodes - 1 = 9, but max valid is 8
        assert 'node_index must be in' in str(excinfo.value)

    def test_get_total_volume_cylindrical(self):
        """Test total volume for cylindrical geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')

        total_volume = mesh.get_total_volume()
        expected_volume = np.pi * 1.0 * mesh.radius**2
        assert np.isclose(total_volume, expected_volume)

    def test_get_total_volume_cylindrical_with_height(self):
        """Test total volume with custom height for cylindrical geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')
        height = 0.5

        total_volume = mesh.get_total_volume(height=height)
        expected_volume = np.pi * height * mesh.radius**2
        assert np.isclose(total_volume, expected_volume)

    def test_get_total_volume_slab(self):
        """Test total volume for slab geometry"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='slab')

        total_volume = mesh.get_total_volume()
        expected_volume = mesh.radius * 1.0 * 1.0
        assert np.isclose(total_volume, expected_volume)

    def test_volume_sum_equals_total_cylindrical(self):
        """Test that sum of node volumes equals total volume for cylindrical"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')

        # Sum all node volumes
        node_volumes = np.array([
            mesh.get_node_volume(i) for i in range(mesh.n_nodes - 1)
        ])
        sum_volumes = np.sum(node_volumes)

        total_volume = mesh.get_total_volume()

        # Sum should equal total volume
        assert np.isclose(sum_volumes, total_volume, rtol=1e-10)

    def test_volume_sum_equals_total_slab(self):
        """Test that sum of node volumes equals total volume for slab"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='slab')

        # Sum all node volumes
        node_volumes = np.array([
            mesh.get_node_volume(i) for i in range(mesh.n_nodes - 1)
        ])
        sum_volumes = np.sum(node_volumes)

        total_volume = mesh.get_total_volume()

        # Sum should equal total volume
        assert np.isclose(sum_volumes, total_volume, rtol=1e-10)


class TestRadialMeshRepr:
    """Test string representation"""

    def test_repr_default_parameters(self):
        """Test string representation with default parameters"""
        mesh = RadialMesh()
        repr_str = repr(mesh)

        assert 'RadialMesh' in repr_str
        assert 'n_nodes=10' in repr_str
        assert 'radius=' in repr_str
        assert 'geometry=cylindrical' in repr_str

    def test_repr_custom_parameters(self):
        """Test string representation with custom parameters"""
        mesh = RadialMesh(n_nodes=20, radius=0.005, geometry='slab')
        repr_str = repr(mesh)

        assert 'RadialMesh' in repr_str
        assert 'n_nodes=20' in repr_str
        assert 'radius=' in repr_str
        assert 'geometry=slab' in repr_str


class TestRadialMeshEdgeCases:
    """Test edge cases and special scenarios"""

    def test_minimum_nodes(self):
        """Test mesh with minimum allowed nodes (2)"""
        mesh = RadialMesh(n_nodes=2, radius=0.003)

        assert len(mesh.nodes) == 2
        assert mesh.nodes[0] == 0.0
        assert np.isclose(mesh.nodes[-1], mesh.radius)
        assert len(mesh.dr) == 1

    def test_large_number_of_nodes(self):
        """Test mesh with large number of nodes"""
        mesh = RadialMesh(n_nodes=1000, radius=0.003)

        assert len(mesh.nodes) == 1000
        assert len(mesh.dr) == 999
        assert np.all(mesh.nodes >= 0)
        assert np.all(mesh.nodes <= mesh.radius)

    def test_very_small_radius(self):
        """Test mesh with very small radius"""
        mesh = RadialMesh(n_nodes=10, radius=1e-6)  # 1 micron

        assert mesh.radius == 1e-6
        assert mesh.nodes[0] == 0.0
        assert np.isclose(mesh.nodes[-1], 1e-6)

    def test_very_large_radius(self):
        """Test mesh with large radius"""
        mesh = RadialMesh(n_nodes=10, radius=0.1)  # 10 cm

        assert mesh.radius == 0.1
        assert mesh.nodes[0] == 0.0
        assert np.isclose(mesh.nodes[-1], 0.1)

    def test_geometric_spacing_with_small_growth_ratio(self):
        """Test geometric spacing with small growth ratio"""
        mesh = RadialMesh(
            n_nodes=10,
            radius=0.003,
            spacing='geometric',
            growth_ratio=1.05
        )

        # Spacing should increase but not too drastically
        dr = mesh.dr
        assert np.all(np.diff(dr) > 0)
        assert dr[-1] / dr[0] < 2.5  # Last spacing less than 2.5x first

    def test_geometric_spacing_sum_consistency(self):
        """Test that geometric spacing sums to total radius"""
        mesh = RadialMesh(
            n_nodes=10,
            radius=0.003,
            spacing='geometric',
            growth_ratio=1.2
        )

        # Sum of all dr should equal radius
        assert np.isclose(np.sum(mesh.dr), mesh.radius, rtol=1e-10)

    def test_nodes_boundary_values(self):
        """Test that boundary nodes are exactly at 0 and radius"""
        for n_nodes in [5, 10, 20, 50]:
            for spacing in ['uniform', 'geometric']:
                mesh = RadialMesh(
                    n_nodes=n_nodes,
                    radius=0.003,
                    spacing=spacing,
                    growth_ratio=1.15
                )

                # First node should be exactly at 0
                assert mesh.nodes[0] == 0.0

                # Last node should be exactly at radius (within floating precision)
                assert np.isclose(mesh.nodes[-1], mesh.radius, rtol=1e-12)


class TestRadialMeshIntegration:
    """Integration tests for common workflows"""

    def test_create_and_access_mesh(self):
        """Test creating mesh and accessing all properties"""
        mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='cylindrical')

        # Access all properties without errors
        _ = mesh.n_nodes
        _ = mesh.radius
        _ = mesh.geometry
        _ = mesh.nodes
        _ = mesh.dr
        _ = mesh.node_centers
        _ = mesh.geometry_factor

    def test_iterate_over_nodes(self):
        """Test iterating over all nodes"""
        mesh = RadialMesh(n_nodes=10, radius=0.003)

        # Iterate over all valid node indices
        volumes = []
        for i in range(mesh.n_nodes - 1):
            volume = mesh.get_node_volume(i)
            volumes.append(volume)

        assert len(volumes) == 9
        assert all(v > 0 for v in volumes)

    def test_mesh_with_different_geometries(self):
        """Test creating meshes with different geometries"""
        geometries = ['cylindrical', 'slab']

        for geom in geometries:
            mesh = RadialMesh(n_nodes=10, radius=0.003, geometry=geom)

            # Check basic properties
            assert mesh.geometry == geom
            assert len(mesh.nodes) == 10
            assert mesh.nodes[0] == 0.0
            assert np.isclose(mesh.nodes[-1], mesh.radius)

            # Check volume calculation works
            volume = mesh.get_node_volume(0)
            assert volume > 0

            total_volume = mesh.get_total_volume()
            assert total_volume > 0

    def test_mesh_with_different_spacing_strategies(self):
        """Test creating meshes with different spacing strategies"""
        spacing_types = ['uniform', 'geometric']

        for spacing in spacing_types:
            mesh = RadialMesh(
                n_nodes=10,
                radius=0.003,
                spacing=spacing,
                growth_ratio=1.15 if spacing == 'geometric' else None
            )

            # Check basic properties
            assert len(mesh.nodes) == 10
            assert mesh.nodes[0] == 0.0
            assert np.isclose(mesh.nodes[-1], mesh.radius)

            # Check dr array
            assert len(mesh.dr) == 9
            assert np.all(mesh.dr > 0)
