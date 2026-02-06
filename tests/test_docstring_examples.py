"""
Test module for docstring examples

This module contains tests that verify the code examples in docstrings
are runnable and produce the expected results.

Usage:
    python3 -m doctest parameters.py -v
    python3 tests/test_docstring_examples.py
"""

import sys
import doctest
import os

# Add parent directory to path to import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add user site-packages to path if needed for macOS
user_site = os.path.expanduser('~/Library/Python/3.9/lib/python/site-packages')
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

import numpy as np


def test_create_default_parameters_example():
    """Test the example from create_default_parameters docstring

    This test verifies that the code example in the create_default_parameters
    function docstring runs correctly and produces the expected values.

    Example from docstring:
    >>> from gas_swelling.params.parameters import create_default_parameters
    >>> params = create_default_parameters()
    >>> temperature = params['temperature']  # 运行温度 (K)
    >>> fission_rate = params['fission_rate']  # 裂变率 (fissions/m³/s)
    >>> Dgb = params['Dgb']  # 晶内气体扩散系数 (m²/s)
    >>> Dgf = params['Dgf']  # 相界气体扩散系数 (m²/s)
    >>> kB = params['kB']  # 玻尔兹曼常数 (J/K)
    """
    from gas_swelling.params.parameters import create_default_parameters

    # Execute the example code
    params = create_default_parameters()

    # Test that all expected keys exist
    assert 'temperature' in params
    assert 'fission_rate' in params
    assert 'Dgb' in params
    assert 'Dgf' in params
    assert 'kB' in params

    # Test the values match expected defaults
    temperature = params['temperature']
    fission_rate = params['fission_rate']
    Dgb = params['Dgb']
    Dgf = params['Dgf']
    kB = params['kB']

    # Verify temperature is default (600 K)
    assert temperature == 600.0

    # Verify fission rate is default (2e20)
    assert fission_rate == 2e20

    # Verify Dgf is Dgb * multiplier (300x)
    assert Dgf == Dgb * 300.0

    # Verify Boltzmann constant
    assert kB == 1.380649e-23

    # Verify diffusion coefficient is reasonable (positive and non-zero)
    assert Dgb > 0
    assert Dgf > 0

    # Verify Dgf > Dgb (phase boundary diffusion is faster)
    assert Dgf > Dgb

    print(f"温度: {temperature} K, 扩散系数: {Dgb:.2e} m²/s")


def test_gas_swelling_model_basic_usage():
    """Test basic usage of GasSwellingModel

    This test verifies that a model can be instantiated with default
    parameters and basic operations work correctly.
    """
    from gas_swelling.models.refactored_model import RefactoredGasSwellingModel

    # Create model with default parameters
    model = RefactoredGasSwellingModel()

    # Verify model is initialized
    assert model.params is not None
    assert model.initial_state is not None
    assert model.debug_history is not None
    assert model.solver_success is True
    assert model.current_time == 0.0

    # Verify initial state has correct shape
    assert len(model.initial_state) == 17

    # Verify all state values are non-negative
    assert all(x >= 0 for x in model.initial_state)

    print("✓ GasSwellingModel basic usage test passed")


def test_gas_swelling_model_with_custom_params():
    """Test GasSwellingModel with custom parameters

    Verifies that the model can be instantiated with custom parameters
    and the parameters are properly set.
    """
    from gas_swelling.params.parameters import create_default_parameters
    from gas_swelling.models.refactored_model import RefactoredGasSwellingModel

    # Create custom parameters
    custom_params = create_default_parameters()
    custom_params['temperature'] = 700  # Modify temperature
    custom_params['fission_rate'] = 3e20  # Modify fission rate

    # Create model with custom parameters
    model = RefactoredGasSwellingModel(params=custom_params)

    # Verify custom parameters are set
    assert model.params['temperature'] == 700
    assert model.params['fission_rate'] == 3e20

    print("✓ GasSwellingModel with custom params test passed")


def test_parameters_dict_completeness():
    """Test that create_default_parameters returns a complete dictionary

    Verifies that the parameters dictionary contains all expected
    material and simulation parameters.
    """
    from gas_swelling.params.parameters import create_default_parameters

    params = create_default_parameters()

    # Check for key material parameters
    material_params = [
        'lattice_constant', 'ATOMIC_VOLUME', 'nu_constant',
        'Dv0', 'Evm', 'surface_energy', 'Zv', 'Zi',
        'dislocation_density', 'Fnb', 'Fnf'
    ]

    for param in material_params:
        assert param in params, f"Missing parameter: {param}"

    # Check for simulation parameters
    sim_params = [
        'temperature', 'fission_rate', 'gas_production_rate',
        'grain_diameter', 'time_step', 'max_time_step'
    ]

    for param in sim_params:
        assert param in params, f"Missing parameter: {param}"

    # Check for physical constants
    constants = ['kB_ev', 'kB', 'R', 'Av', 'Omega']
    for const in constants:
        assert const in params, f"Missing constant: {const}"

    print("✓ Parameters dict completeness test passed")


def test_parameter_types_and_ranges():
    """Test that parameters have correct types and valid ranges

    Verifies that all parameters are of the correct type and
    within physically reasonable ranges.
    """
    from gas_swelling.params.parameters import create_default_parameters

    params = create_default_parameters()

    # Temperature should be positive (in Kelvin)
    assert params['temperature'] > 0
    assert params['temperature'] < 5000  # Below melting point

    # Fission rate should be positive
    assert params['fission_rate'] > 0

    # Diffusion coefficients should be positive
    assert params['Dgb'] > 0
    assert params['Dgf'] > 0

    # Physical constants should match known values
    assert np.isclose(params['kB'], 1.380649e-23)
    assert np.isclose(params['R'], 8.314462618)
    assert np.isclose(params['Av'], 6.02214076e23)

    # Lattice constant should be on order of Angstroms
    assert 1e-10 < params['lattice_constant'] < 1e-9

    # Surface energy should be positive
    assert params['surface_energy'] > 0

    print("✓ Parameter types and ranges test passed")


def run_doctest_on_parameters():
    """Run doctest on parameters module

    This function uses Python's doctest module to test the examples
    in the parameters.py docstrings.
    """
    from gas_swelling.params import parameters

    # Run doctest on the parameters module
    result = doctest.testmod(parameters, verbose=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Doctest Results for gas_swelling.params.parameters:")
    print(f"  Attempted: {result.attempted} tests")
    print(f"  Failed: {result.failed} tests")

    if result.failed == 0:
        print(f"  Status: ✓ ALL TESTS PASSED")
    else:
        print(f"  Status: ✗ SOME TESTS FAILED")
        print(f"{'='*60}\n")
        # Run again with verbose output to show failures
        doctest.testmod(parameters, verbose=True)
        return False

    print(f"{'='*60}\n")
    return True


def test_radial_mesh_docstring():
    """Test radial mesh docstring examples

    Verifies that the RadialMesh class examples work correctly.
    Example from docstring:
    >>> from gas_swelling.models.radial_mesh import RadialMesh
    >>> mesh = RadialMesh(n_nodes=10, radius=0.003)
    >>> print(f'Nodes: {len(mesh.nodes)}, Geometry: {mesh.geometry}')
    Nodes: 10, Geometry: cylindrical
    """
    from gas_swelling.models.radial_mesh import RadialMesh

    # Create mesh
    mesh = RadialMesh(n_nodes=10, radius=0.003)

    # Verify basic properties
    assert len(mesh.nodes) == 10
    assert mesh.geometry == 'cylindrical'
    assert mesh.radius == 0.003
    assert mesh.n_nodes == 10

    # Verify node positions
    assert mesh.nodes[0] == 0.0
    assert mesh.nodes[-1] == 0.003

    # Verify geometry factor
    assert mesh.geometry_factor == 1.0

    print("✓ RadialMesh docstring examples test passed")


def test_radial_model_docstring():
    """Test radial gas swelling model docstring examples

    Verifies that the RadialGasSwellingModel examples work correctly.
    Example from docstring:
    >>> from gas_swelling.models.radial_model import RadialGasSwellingModel
    >>> from gas_swelling.params.parameters import create_default_parameters
    >>> params = create_default_parameters()
    >>> params['temperature'] = 773.15
    >>> model = RadialGasSwellingModel(params, n_nodes=10)
    """
    from gas_swelling.models.radial_model import RadialGasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters

    # Create model
    params = create_default_parameters()
    params['temperature'] = 773.15
    model = RadialGasSwellingModel(params, n_nodes=10)

    # Verify basic properties
    assert model.n_nodes == 10
    assert model.mesh is not None
    assert model.params is not None
    assert model.initial_state is not None

    # Verify state size
    assert len(model.initial_state) == 17 * 10  # 17 vars per node

    # Verify temperature profile
    assert len(model.temperature) == 10

    print("✓ RadialGasSwellingModel docstring examples test passed")


def test_radial_transport_docstring():
    """Test radial transport docstring examples

    Verifies that the radial transport functions work correctly.
    Example from docstring:
    >>> import numpy as np
    >>> from gas_swelling.physics.radial_transport import calculate_radial_flux
    >>> concentration = np.array([1e25, 0.9e25, 0.8e25, 0.7e25])
    >>> diffusion_coeff = 1e-15
    >>> mesh_nodes = np.array([0.0, 0.001, 0.002, 0.003])
    >>> flux = calculate_radial_flux(concentration, diffusion_coeff, mesh_nodes, geometry_factor=1.0)
    """
    import numpy as np
    from gas_swelling.physics.radial_transport import calculate_radial_flux

    # Test radial flux calculation
    concentration = np.array([1e25, 0.9e25, 0.8e25, 0.7e25])
    diffusion_coeff = 1e-15
    mesh_nodes = np.array([0.0, 0.001, 0.002, 0.003])
    flux = calculate_radial_flux(concentration, diffusion_coeff, mesh_nodes, geometry_factor=1.0)

    # Verify flux shape
    assert len(flux) == 3  # n_nodes - 1

    # Verify flux is positive (flowing from high to low concentration)
    assert flux[0] > 0

    print("✓ Radial transport docstring examples test passed")


def test_radial_plotter_docstring():
    """Test radial plotter docstring examples

    Verifies that the RadialProfilePlotter can be initialized.
    Example from docstring:
    >>> from gas_swelling.visualization.radial_plots import RadialProfilePlotter
    >>> plotter = RadialProfilePlotter()
    """
    from gas_swelling.visualization.radial_plots import RadialProfilePlotter

    # Create plotter
    plotter = RadialProfilePlotter()

    # Verify basic properties
    assert plotter.time_index == -1
    assert plotter.radius_unit == 'mm'

    print("✓ RadialProfilePlotter docstring examples test passed")


def test_radial_geometric_spacing_docstring():
    """Test radial mesh geometric spacing docstring examples

    Verifies that geometric spacing works correctly.
    """
    from gas_swelling.models.radial_mesh import RadialMesh

    # Create mesh with geometric spacing
    mesh = RadialMesh(n_nodes=20, radius=0.003, spacing='geometric')

    # Verify nodes
    assert len(mesh.nodes) == 20
    assert mesh.nodes[0] == 0.0
    assert mesh.nodes[-1] == 0.003

    # Verify spacing increases
    dr = mesh.dr
    for i in range(len(dr) - 1):
        assert dr[i+1] > dr[i], "Spacing should increase for geometric spacing"

    print("✓ Radial mesh geometric spacing test passed")


def test_radial_slab_geometry_docstring():
    """Test radial slab geometry docstring examples

    Verifies that slab geometry works correctly.
    """
    from gas_swelling.models.radial_mesh import RadialMesh

    # Create slab mesh
    mesh = RadialMesh(n_nodes=10, radius=0.003, geometry='slab')

    # Verify geometry
    assert mesh.geometry == 'slab'
    assert mesh.geometry_factor == 0.0

    print("✓ Radial slab geometry test passed")


def test_radial_temperature_profile_docstring():
    """Test radial temperature profile docstring examples

    Verifies that user-specified temperature profiles work.
    """
    import numpy as np
    from gas_swelling.models.radial_model import RadialGasSwellingModel
    from gas_swelling.params.parameters import create_default_parameters

    # Create model with user temperature profile
    params = create_default_parameters()
    T_profile = np.linspace(800, 600, 10)
    model = RadialGasSwellingModel(
        params, n_nodes=10,
        temperature_profile='user',
        temperature_data=T_profile
    )

    # Verify temperature profile
    assert len(model.temperature) == 10
    assert np.isclose(model.temperature[0], 800)
    assert np.isclose(model.temperature[-1], 600)

    print("✓ Radial temperature profile test passed")


def main():
    """Run all tests"""
    print("="*60)
    print("Testing Docstring Examples")
    print("="*60)

    tests = [
        ("create_default_parameters example", test_create_default_parameters_example),
        ("GasSwellingModel basic usage", test_gas_swelling_model_basic_usage),
        ("GasSwellingModel custom params", test_gas_swelling_model_with_custom_params),
        ("Parameters completeness", test_parameters_dict_completeness),
        ("Parameter types and ranges", test_parameter_types_and_ranges),
        ("RadialMesh docstring examples", test_radial_mesh_docstring),
        ("RadialGasSwellingModel docstring examples", test_radial_model_docstring),
        ("Radial transport docstring examples", test_radial_transport_docstring),
        ("RadialProfilePlotter docstring examples", test_radial_plotter_docstring),
        ("Radial geometric spacing docstring", test_radial_geometric_spacing_docstring),
        ("Radial slab geometry docstring", test_radial_slab_geometry_docstring),
        ("Radial temperature profile docstring", test_radial_temperature_profile_docstring),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}...")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    # Run doctest
    print(f"\nRunning: doctest on parameters.py...")
    if run_doctest_on_parameters():
        passed += 1
    else:
        failed += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"  Total: {passed + failed} tests")
    print(f"  Passed: {passed} tests")
    print(f"  Failed: {failed} tests")

    if failed == 0:
        print(f"  Status: ✓ ALL TESTS PASSED")
        print(f"{'='*60}")
        return 0
    else:
        print(f"  Status: ✗ SOME TESTS FAILED")
        print(f"{'='*60}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
