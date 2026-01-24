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
    >>> from parameters import create_default_parameters
    >>> params = create_default_parameters()
    >>> temperature = params['temperature']  # 运行温度 (K)
    >>> fission_rate = params['fission_rate']  # 裂变率 (fissions/m³/s)
    >>> Dgb = params['Dgb']  # 晶内气体扩散系数 (m²/s)
    >>> Dgf = params['Dgf']  # 相界气体扩散系数 (m²/s)
    >>> kB = params['kB']  # 玻尔兹曼常数 (J/K)
    """
    from parameters import create_default_parameters

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
    from modelrk23 import GasSwellingModel

    # Create model with default parameters
    model = GasSwellingModel()

    # Verify model is initialized
    assert model.params is not None
    assert model.initial_state is not None
    assert model.debug_history is not None
    assert model.step_count == 0
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
    from parameters import create_default_parameters
    from modelrk23 import GasSwellingModel

    # Create custom parameters
    custom_params = create_default_parameters()
    custom_params['temperature'] = 700  # Modify temperature
    custom_params['fission_rate'] = 3e20  # Modify fission rate

    # Create model with custom parameters
    model = GasSwellingModel(params=custom_params)

    # Verify custom parameters are set
    assert model.params['temperature'] == 700
    assert model.params['fission_rate'] == 3e20

    print("✓ GasSwellingModel with custom params test passed")


def test_parameters_dict_completeness():
    """Test that create_default_parameters returns a complete dictionary

    Verifies that the parameters dictionary contains all expected
    material and simulation parameters.
    """
    from parameters import create_default_parameters

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
    from parameters import create_default_parameters

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
    import parameters

    # Run doctest on the parameters module
    result = doctest.testmod(parameters, verbose=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Doctest Results for parameters.py:")
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
