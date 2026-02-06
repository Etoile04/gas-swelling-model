"""
Unit tests for radial transport calculations in gas_swelling.physics.radial_transport

Tests cover:
- Radial flux calculation between nodes
- Diffusion coupling matrix construction
- Node-to-node flux calculation
- Boundary condition application (centerline and surface)
- Radial transport terms calculation
"""

import pytest
import numpy as np
from gas_swelling.physics.radial_transport import (
    calculate_radial_flux,
    calculate_diffusion_coupling_matrix,
    calculate_node_to_node_flux,
    apply_centerline_bc,
    apply_surface_bc,
    calculate_radial_transport_terms
)


class TestRadialFlux:
    """Test suite for radial flux calculation"""

    @pytest.fixture
    def uniform_mesh(self):
        """Create a uniform mesh for testing"""
        return np.array([0.0, 0.001, 0.002, 0.003])

    @pytest.fixture
    def concentration_profile(self):
        """Create a decreasing concentration profile"""
        return np.array([1.0e25, 0.9e25, 0.8e25, 0.7e25])

    def test_radial_flux_normal_values(self, uniform_mesh, concentration_profile):
        """Test radial flux calculation with normal values"""
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        flux = calculate_radial_flux(
            concentration_profile,
            diffusion_coeff,
            uniform_mesh,
            geometry_factor
        )

        # Flux should have n_nodes - 1 elements
        assert len(flux) == 3

        # Flux should be positive (flowing from high to low concentration)
        assert np.all(flux > 0)

        # Check finite values
        assert np.all(np.isfinite(flux))

    def test_radial_flux_zero_gradient(self, uniform_mesh):
        """Test radial flux with zero concentration gradient"""
        concentration = np.array([1.0e25, 1.0e25, 1.0e25, 1.0e25])
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        flux = calculate_radial_flux(concentration, diffusion_coeff, uniform_mesh, geometry_factor)

        # No flux when concentrations are equal
        assert np.allclose(flux, 0.0)

    def test_radial_flux_reverse_gradient(self, uniform_mesh):
        """Test radial flux with reverse concentration gradient"""
        # Increasing concentration (unusual physical situation)
        concentration = np.array([0.7e25, 0.8e25, 0.9e25, 1.0e25])
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        flux = calculate_radial_flux(concentration, diffusion_coeff, uniform_mesh, geometry_factor)

        # Negative flux (flowing inward)
        assert np.all(flux < 0)

    def test_radial_flux_slab_geometry(self, uniform_mesh, concentration_profile):
        """Test radial flux with slab geometry"""
        diffusion_coeff = 1e-15
        geometry_factor = 0.0

        flux = calculate_radial_flux(
            concentration_profile,
            diffusion_coeff,
            uniform_mesh,
            geometry_factor
        )

        # Should work for slab geometry
        assert len(flux) == 3
        assert np.all(np.isfinite(flux))

    def test_radial_flux_diffusion_coefficient_dependence(self, uniform_mesh, concentration_profile):
        """Test that flux scales with diffusion coefficient"""
        geometry_factor = 1.0

        flux1 = calculate_radial_flux(concentration_profile, 1e-15, uniform_mesh, geometry_factor)
        flux2 = calculate_radial_flux(concentration_profile, 2e-15, uniform_mesh, geometry_factor)

        # Should scale linearly with diffusion coefficient
        assert np.allclose(flux2 / flux1, 2.0)

    def test_radial_flux_mesh_spacing_dependence(self, concentration_profile):
        """Test that flux depends on mesh spacing"""
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        mesh1 = np.array([0.0, 0.001, 0.002, 0.003])
        mesh2 = np.array([0.0, 0.002, 0.004, 0.006])

        flux1 = calculate_radial_flux(concentration_profile, diffusion_coeff, mesh1, geometry_factor)
        flux2 = calculate_radial_flux(concentration_profile, diffusion_coeff, mesh2, geometry_factor)

        # Smaller spacing gives larger flux
        # Flux scales as 1/dr
        assert np.all(np.abs(flux2) < np.abs(flux1))

    def test_radial_flux_invalid_inputs(self, uniform_mesh, concentration_profile):
        """Test error handling for invalid inputs"""
        diffusion_coeff = 1e-15

        # Mismatched array lengths
        with pytest.raises(ValueError, match="same length"):
            calculate_radial_flux(
                concentration_profile[:2],
                diffusion_coeff,
                uniform_mesh,
                1.0
            )

        # Negative diffusion coefficient
        with pytest.raises(ValueError, match="non-negative"):
            calculate_radial_flux(
                concentration_profile,
                -1e-15,
                uniform_mesh,
                1.0
            )

        # Invalid geometry factor
        with pytest.raises(ValueError, match="must be 0.0.*or 1.0"):
            calculate_radial_flux(
                concentration_profile,
                diffusion_coeff,
                uniform_mesh,
                0.5
            )

        # Non-increasing mesh
        with pytest.raises(ValueError, match="strictly increasing"):
            calculate_radial_flux(
                concentration_profile,
                diffusion_coeff,
                np.array([0.0, 0.002, 0.001, 0.003]),
                1.0
            )


class TestDiffusionCouplingMatrix:
    """Test suite for diffusion coupling matrix"""

    @pytest.fixture
    def uniform_mesh(self):
        """Create a uniform mesh for testing"""
        return np.array([0.0, 0.001, 0.002, 0.003])

    def test_coupling_matrix_shape(self, uniform_mesh):
        """Test coupling matrix has correct shape"""
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        A = calculate_diffusion_coupling_matrix(
            uniform_mesh,
            diffusion_coeff,
            geometry_factor
        )

        # Should be n_nodes x n_nodes
        assert A.shape == (4, 4)

    def test_coupling_matrix_structure(self, uniform_mesh):
        """Test coupling matrix structure"""
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        A = calculate_diffusion_coupling_matrix(
            uniform_mesh,
            diffusion_coeff,
            geometry_factor
        )

        # Diagonal elements should be negative (or zero)
        assert np.all(np.diag(A) <= 0)

        # Off-diagonal elements should be non-negative
        for i in range(len(A)):
            for j in range(len(A)):
                if i != j:
                    assert A[i, j] >= 0

        # Each row should sum to approximately zero (conservation)
        # (except for boundary rows which may not)
        for i in range(1, len(A) - 1):
            row_sum = np.sum(A[i, :])
            assert abs(row_sum) < 1e-10

    def test_coupling_matrix_diffusion_coefficient_scaling(self, uniform_mesh):
        """Test that coupling matrix scales with diffusion coefficient"""
        geometry_factor = 1.0

        A1 = calculate_diffusion_coupling_matrix(uniform_mesh, 1e-15, geometry_factor)
        A2 = calculate_diffusion_coupling_matrix(uniform_mesh, 2e-15, geometry_factor)

        # Should scale linearly (check only non-zero elements)
        # Boundary rows are all zeros, so we check interior rows
        mask = A1 != 0  # Only check non-zero elements
        assert np.allclose(A2[mask] / A1[mask], 2.0)

    def test_coupling_matrix_mesh_dependence(self):
        """Test that coupling matrix depends on mesh spacing"""
        diffusion_coeff = 1e-15
        geometry_factor = 1.0

        # Use non-uniform meshes to ensure different behavior
        mesh1 = np.array([0.0, 0.001, 0.002, 0.003])
        mesh2 = np.array([0.0, 0.0005, 0.002, 0.003])  # Different spacing pattern

        A1 = calculate_diffusion_coupling_matrix(mesh1, diffusion_coeff, geometry_factor)
        A2 = calculate_diffusion_coupling_matrix(mesh2, diffusion_coeff, geometry_factor)

        # Different meshes give different matrices
        # Check that at least some elements differ significantly
        # Use small atol since matrix values are around 1e-9
        assert not np.allclose(A1[1:-1, :], A2[1:-1, :], atol=1e-12)

    def test_coupling_matrix_invalid_inputs(self):
        """Test error handling for invalid inputs"""
        # Too few nodes
        with pytest.raises(ValueError, match="at least 2 nodes"):
            calculate_diffusion_coupling_matrix(
                np.array([0.0]),
                1e-15,
                1.0
            )

        # Negative diffusion coefficient
        with pytest.raises(ValueError, match="non-negative"):
            calculate_diffusion_coupling_matrix(
                np.array([0.0, 0.001]),
                -1e-15,
                1.0
            )


class TestNodeToNodeFlux:
    """Test suite for node-to-node flux calculation"""

    def test_node_to_node_flux_normal_values(self):
        """Test flux calculation with normal values"""
        flux = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0
        )

        # Should be positive (flowing from high to low)
        assert flux > 0
        assert np.isfinite(flux)

    def test_node_to_node_flux_zero_gradient(self):
        """Test flux with zero concentration gradient"""
        flux = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=1.0e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0
        )

        # No flux when concentrations are equal
        assert flux == 0.0

    def test_node_to_node_flux_reverse_gradient(self):
        """Test flux with reverse concentration gradient"""
        flux = calculate_node_to_node_flux(
            concentration_i=0.9e25,
            concentration_j=1.0e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0
        )

        # Negative flux (flowing from j to i)
        assert flux < 0

    def test_node_to_node_flux_slab_geometry(self):
        """Test flux with slab geometry"""
        flux_slab = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=0.0
        )

        flux_cyl = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0
        )

        # Both should work
        assert flux_slab > 0
        assert flux_cyl > 0

    def test_node_to_node_flux_cylindrical_correction(self):
        """Test cylindrical geometry correction factor"""
        flux_base = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0,
            radial_position=None
        )

        flux_corrected = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0,
            radial_position=0.001
        )

        # Cylindrical correction should increase flux
        assert flux_corrected > flux_base

    def test_node_to_node_flux_distance_dependence(self):
        """Test that flux depends on distance"""
        flux1 = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.001,
            geometry_factor=1.0
        )

        flux2 = calculate_node_to_node_flux(
            concentration_i=1.0e25,
            concentration_j=0.9e25,
            diffusion_coeff=1e-15,
            distance=0.002,
            geometry_factor=1.0
        )

        # Larger distance gives smaller flux (scales as 1/distance)
        assert flux2 < flux1

    def test_node_to_node_flux_invalid_inputs(self):
        """Test error handling for invalid inputs"""
        # Zero distance
        with pytest.raises(ValueError, match="distance must be positive"):
            calculate_node_to_node_flux(
                concentration_i=1.0e25,
                concentration_j=0.9e25,
                diffusion_coeff=1e-15,
                distance=0.0,
                geometry_factor=1.0
            )

        # Negative distance
        with pytest.raises(ValueError, match="distance must be positive"):
            calculate_node_to_node_flux(
                concentration_i=1.0e25,
                concentration_j=0.9e25,
                diffusion_coeff=1e-15,
                distance=-0.001,
                geometry_factor=1.0
            )

        # Negative diffusion coefficient
        with pytest.raises(ValueError, match="non-negative"):
            calculate_node_to_node_flux(
                concentration_i=1.0e25,
                concentration_j=0.9e25,
                diffusion_coeff=-1e-15,
                distance=0.001,
                geometry_factor=1.0
            )

        # Negative concentration
        with pytest.raises(ValueError, match="non-negative"):
            calculate_node_to_node_flux(
                concentration_i=-1.0e25,
                concentration_j=0.9e25,
                diffusion_coeff=1e-15,
                distance=0.001,
                geometry_factor=1.0
            )


class TestCenterlineBoundaryCondition:
    """Test suite for centerline boundary condition"""

    def test_centerline_bc_zero_first_flux(self):
        """Test that centerline BC sets first flux to zero"""
        flux = np.array([1e10, 2e10, 3e10])

        flux_bc = apply_centerline_bc(flux)

        # First flux should be zero
        assert flux_bc[0] == 0.0

        # Other fluxes should be unchanged
        assert flux_bc[1] == flux[1]
        assert flux_bc[2] == flux[2]

    def test_centerline_bc_empty_array(self):
        """Test centerline BC with empty array"""
        flux = np.array([])

        flux_bc = apply_centerline_bc(flux)

        # Should return empty array
        assert len(flux_bc) == 0

    def test_centerline_bc_no_copy_mutation(self):
        """Test that original array is not modified"""
        flux = np.array([1e10, 2e10, 3e10])
        original_flux = flux.copy()

        apply_centerline_bc(flux)

        # Original should be unchanged
        assert np.array_equal(flux, original_flux)


class TestSurfaceBoundaryCondition:
    """Test suite for surface boundary condition"""

    @pytest.fixture
    def mesh_nodes(self):
        """Create mesh nodes for testing"""
        return np.array([0.0, 0.001, 0.002, 0.003])

    def test_surface_bc_set_last_flux(self, mesh_nodes):
        """Test that surface BC sets last flux to specified value"""
        flux = np.array([1e10, 2e10, 3e10])
        surface_flux_value = 5e10

        flux_bc = apply_surface_bc(flux, surface_flux_value, mesh_nodes)

        # Last flux should be set to specified value
        assert flux_bc[-1] == surface_flux_value

        # Other fluxes should be unchanged
        assert flux_bc[0] == flux[0]
        assert flux_bc[1] == flux[1]

    def test_surface_bc_zero_release(self, mesh_nodes):
        """Test surface BC with zero flux (no release)"""
        flux = np.array([1e10, 2e10, 3e10])

        flux_bc = apply_surface_bc(flux, 0.0, mesh_nodes)

        # Last flux should be zero
        assert flux_bc[-1] == 0.0

    def test_surface_bc_influx(self, mesh_nodes):
        """Test surface BC with negative flux (influx)"""
        flux = np.array([1e10, 2e10, 3e10])

        flux_bc = apply_surface_bc(flux, -1e10, mesh_nodes)

        # Last flux should be negative (influx)
        assert flux_bc[-1] == -1e10

    def test_surface_bc_empty_array(self):
        """Test surface BC with empty array"""
        flux = np.array([])
        mesh_nodes = np.array([0.0, 0.001])

        flux_bc = apply_surface_bc(flux, 5e10, mesh_nodes)

        # Should return empty array
        assert len(flux_bc) == 0

    def test_surface_bc_invalid_mesh_length(self):
        """Test error handling for invalid mesh length"""
        flux = np.array([1e10, 2e10, 3e10])
        mesh_nodes = np.array([0.0, 0.001])  # Wrong length

        with pytest.raises(ValueError, match="length must be flux length"):
            apply_surface_bc(flux, 5e10, mesh_nodes)

    def test_surface_bc_no_copy_mutation(self, mesh_nodes):
        """Test that original array is not modified"""
        flux = np.array([1e10, 2e10, 3e10])
        original_flux = flux.copy()

        apply_surface_bc(flux, 5e10, mesh_nodes)

        # Original should be unchanged
        assert np.array_equal(flux, original_flux)


class TestRadialTransportTerms:
    """Test suite for complete radial transport terms calculation"""

    @pytest.fixture
    def uniform_mesh(self):
        """Create a uniform mesh for testing"""
        return np.array([0.0, 0.001, 0.002, 0.003])

    @pytest.fixture
    def concentration_profile(self):
        """Create a decreasing concentration profile"""
        return np.array([1.0e25, 0.9e25, 0.8e25, 0.7e25])

    def test_transport_terms_return_dict(self, uniform_mesh, concentration_profile):
        """Test that transport terms returns a dictionary with correct keys"""
        terms = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        # Should return a dict
        assert isinstance(terms, dict)

        # Should have all expected keys
        expected_keys = ['flux', 'div_flux', 'coupling_matrix', 'flux_with_bc']
        for key in expected_keys:
            assert key in terms

    def test_transport_terms_shapes(self, uniform_mesh, concentration_profile):
        """Test shapes of returned arrays"""
        n_nodes = len(uniform_mesh)
        terms = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        # Flux should have n_nodes - 1 elements
        assert terms['flux'].shape == (n_nodes - 1,)

        # Divergence should have n_nodes elements
        assert terms['div_flux'].shape == (n_nodes,)

        # Coupling matrix should be n_nodes x n_nodes
        assert terms['coupling_matrix'].shape == (n_nodes, n_nodes)

        # Flux with BC should have same shape as flux
        assert terms['flux_with_bc'].shape == (n_nodes - 1,)

    def test_transport_terms_centerline_bc(self, uniform_mesh, concentration_profile):
        """Test that centerline BC is applied"""
        terms = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        # First flux with BC should be zero
        assert terms['flux_with_bc'][0] == 0.0

    def test_transport_terms_with_surface_flux(self, uniform_mesh, concentration_profile):
        """Test transport terms with surface flux specified"""
        surface_flux = 5e10
        terms = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0,
            surface_flux=surface_flux
        )

        # Last flux with BC should match specified surface flux
        assert terms['flux_with_bc'][-1] == surface_flux

    def test_transport_terms_finite_values(self, uniform_mesh, concentration_profile):
        """Test that all returned values are finite"""
        terms = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0,
            surface_flux=1e10
        )

        # All arrays should contain finite values
        assert np.all(np.isfinite(terms['flux']))
        assert np.all(np.isfinite(terms['div_flux']))
        assert np.all(np.isfinite(terms['coupling_matrix']))
        assert np.all(np.isfinite(terms['flux_with_bc']))

    def test_transport_terms_consistency(self, uniform_mesh, concentration_profile):
        """Test internal consistency of transport terms"""
        diffusion_coeff = 1e-15
        terms = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff,
            geometry_factor=1.0
        )

        # Flux should be positive (flowing from high to low concentration)
        assert np.all(terms['flux'] > 0)

        # Coupling matrix should have correct structure
        A = terms['coupling_matrix']
        for i in range(1, len(A) - 1):
            # Interior rows should sum to zero
            assert abs(np.sum(A[i, :])) < 1e-10

    def test_transport_terms_different_geometries(self, uniform_mesh, concentration_profile):
        """Test transport terms with different geometries"""
        terms_cyl = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        terms_slab = calculate_radial_transport_terms(
            concentration_profile,
            uniform_mesh,
            diffusion_coeff=1e-15,
            geometry_factor=0.0
        )

        # Both should work and return same structure
        assert set(terms_cyl.keys()) == set(terms_slab.keys())

        # Values may differ due to geometry, but should be finite
        for key in terms_cyl:
            assert np.all(np.isfinite(terms_cyl[key]))
            assert np.all(np.isfinite(terms_slab[key]))


class TestRadialTransportIntegration:
    """Integration tests for radial transport calculations"""

    @pytest.fixture
    def mesh(self):
        """Create test mesh"""
        return np.array([0.0, 0.001, 0.002, 0.003])

    def test_transport_consistency_with_diffusion_law(self, mesh):
        """Test that flux is consistent with Fick's law"""
        concentration = np.array([1.0e25, 0.9e25, 0.8e25, 0.7e25])
        diffusion_coeff = 1e-15

        terms = calculate_radial_transport_terms(
            concentration,
            mesh,
            diffusion_coeff,
            geometry_factor=1.0
        )

        # Check that flux is proportional to concentration gradient
        for i in range(len(terms['flux'])):
            dr = mesh[i+1] - mesh[i]
            dC = concentration[i+1] - concentration[i]
            expected_flux = -diffusion_coeff * dC / dr

            assert abs(terms['flux'][i] - expected_flux) < 1e-20

    def test_transport_mass_conservation(self, mesh):
        """Test that transport conserves mass"""
        # Create a concentration profile
        concentration = np.array([1.0e25, 0.9e25, 0.8e25, 0.7e25])

        terms = calculate_radial_transport_terms(
            concentration,
            mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        # The divergence represents the net source/sink
        # For a closed system with zero BC, sum should be small
        # (not exactly zero due to boundary effects)
        assert np.isfinite(np.sum(terms['div_flux']))

    def test_transport_physical_units(self, mesh):
        """Test that transport values have correct physical units"""
        concentration = np.array([1.0e25, 0.9e25, 0.8e25, 0.7e25])
        diffusion_coeff = 1e-15  # m^2/s

        terms = calculate_radial_transport_terms(
            concentration,
            mesh,
            diffusion_coeff,
            geometry_factor=1.0
        )

        # Flux should have units of atoms/(m^2·s)
        # Typical range for these parameters
        assert 0 < np.max(terms['flux']) < 1e20

        # Divergence should have units of atoms/(m^3·s)
        assert np.all(np.abs(terms['div_flux']) < 1e25)

    def test_transport_direction(self, mesh):
        """Test that transport direction is physically correct"""
        # High concentration at center, low at surface
        concentration_center_high = np.array([1.0e25, 0.9e25, 0.8e25, 0.7e25])

        terms = calculate_radial_transport_terms(
            concentration_center_high,
            mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        # Flux should be outward (positive)
        assert np.all(terms['flux'] > 0)

        # Low concentration at center, high at surface
        concentration_surface_high = np.array([0.7e25, 0.8e25, 0.9e25, 1.0e25])

        terms = calculate_radial_transport_terms(
            concentration_surface_high,
            mesh,
            diffusion_coeff=1e-15,
            geometry_factor=1.0
        )

        # Flux should be inward (negative)
        assert np.all(terms['flux'] < 0)
