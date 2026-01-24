# Test Suite

Comprehensive test suite for the Gas Swelling Model, covering unit tests, integration tests, validation against experimental data, edge cases, and performance benchmarks.

## Overview

The test suite is designed to ensure the correctness, robustness, and performance of the gas swelling model implementation. It follows a multi-layered testing strategy:

- **Unit Tests**: Isolated testing of individual components and methods
- **Integration Tests**: Testing component interactions and solver behavior
- **Validation Tests**: Verification against experimental data from published research
- **Edge Case Tests**: Handling of boundary conditions and extreme parameter values
- **Performance Tests**: Benchmarking computational efficiency

### Test Coverage Goals

The test suite aims to achieve comprehensive coverage across:
- All public methods and classes
- Edge cases and boundary conditions
- Error handling and validation
- Numerical accuracy and precision
- Performance and scalability

## Test Organization

### Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── utils.py                    # Custom assertion utilities
├── fixtures/                   # Test fixtures and expected data
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures and configuration
│   ├── expected_results.py    # Expected results from paper data
│   └── test_data.py           # Test data for various scenarios
├── test_import.py             # Package import tests
├── test_unit_parameters.py    # MaterialParameters and SimulationParameters
├── test_unit_concentrations.py # Concentration calculations
├── test_unit_bubble_radius.py  # Bubble radius computations
├── test_unit_pressure.py       # Gas pressure calculations
├── test_unit_gas_transport.py  # Gas transport mechanisms
├── test_unit_model_methods.py  # Model helper methods
├── test_unit_equations.py      # Rate equations
├── test_unit_solve_method.py   # Solver integration
├── test_integration_solver.py  # Full solver integration tests
├── test_validation_paper_data.py # Validation against paper data
├── test_edge_cases.py          # Boundary conditions and edge cases
└── test_performance.py         # Performance benchmarks
```

## Running Tests

### Run All Tests

```bash
# Run all tests with default pytest settings
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=gas_swelling --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/test_unit_*.py

# Run only integration tests
pytest tests/test_integration_*.py

# Run only validation tests
pytest tests/test_validation_*.py

# Run only edge case tests
pytest tests/test_edge_cases.py

# Run only performance tests
pytest tests/test_performance.py
```

### Run Specific Test Files

```bash
# Test parameter handling
pytest tests/test_unit_parameters.py -v

# Test solver integration
pytest tests/test_integration_solver.py -v

# Test validation against paper data
pytest tests/test_validation_paper_data.py -v
```

### Run Specific Test Cases

```bash
# Run specific test function
pytest tests/test_unit_pressure.py::TestIdealGasPressure::test_pressure_calculation -v

# Run tests matching a pattern
pytest -k "pressure" -v

# Run tests marked with specific markers
pytest -m "slow" -v
pytest -m "validation" -v
```

### Advanced Options

```bash
# Run with detailed output (show print statements)
pytest -v -s

# Run until first failure
pytest -x

# Run failed tests only
pytest --lf

# Run with parallel execution (requires pytest-xdist)
pytest -n auto

# Generate coverage report
pytest --cov=gas_swelling --cov-report=term-missing
```

## Test Categories

### 1. Import Tests (`test_import.py`)

**Purpose**: Verify that the package can be imported correctly and all public APIs are accessible.

**Key Tests**:
- Package import and version check
- GasSwellingModel import
- Parameter class imports
- Physical constants imports
- Default parameter creation

**Example**:
```bash
pytest tests/test_import.py -v
```

### 2. Unit Tests for Parameters (`test_unit_parameters.py`)

**Purpose**: Test MaterialParameters and SimulationParameters dataclasses.

**Key Tests**:
- Default parameter instantiation
- Lattice parameters validation
- Diffusion coefficient calculations
- Temperature-dependent properties
- Parameter validation and constraints

**Example**:
```bash
pytest tests/test_unit_parameters.py -v
```

### 3. Unit Tests for Concentrations (`test_unit_concentrations.py`)

**Purpose**: Test gas and defect concentration calculations.

**Key Tests**:
- Bulk gas concentration (Cgb)
- Boundary gas concentration (Cgf)
- Cavity concentration calculations
- Equilibrium concentration validation
- Conservation laws

**Example**:
```bash
pytest tests/test_unit_concentrations.py -v
```

### 4. Unit Tests for Bubble Radius (`test_unit_bubble_radius.py`)

**Purpose**: Test cavity radius calculations based on mechanical equilibrium.

**Key Tests**:
- Radius calculation from gas atoms
- Surface tension effects
- Pressure-radius relationships
- Critical radius determination
- Boundary bubble radius (Rcf) vs bulk bubble radius (Rcb)

**Example**:
```bash
pytest tests/test_unit_bubble_radius.py -v
```

### 5. Unit Tests for Gas Pressure (`test_unit_pressure.py`)

**Purpose**: Test gas pressure calculations using different equations of state.

**Key Tests**:
- Ideal gas law pressure
- Van der Waals (Ronchi) EOS pressure
- Pressure-radius relationships
- Temperature dependence
- Phase transitions

**Example**:
```bash
pytest tests/test_unit_pressure.py -v
```

### 6. Unit Tests for Gas Transport (`test_unit_gas_transport.py`)

**Purpose**: Test gas transport mechanisms including diffusion and nucleation.

**Key Tests**:
- Gas diffusion rates
- Bubble nucleation
- Gas absorption/emission
- Boundary transport
- Temperature-dependent transport

**Example**:
```bash
pytest tests/test_unit_gas_transport.py -v
```

### 7. Unit Tests for Model Methods (`test_unit_model_methods.py`)

**Purpose**: Test helper methods and utility functions in the model.

**Key Tests**:
- Swelling calculation
- Gas release fraction
- Critical radius computation
- Derived quantities
- State variable updates

**Example**:
```bash
pytest tests/test_unit_model_methods.py -v
```

### 8. Unit Tests for Equations (`test_unit_equations.py`)

**Purpose**: Test the rate equations that drive the model.

**Key Tests**:
- Gas concentration rate equations
- Cavity growth rate equations
- Defect kinetics equations
- Boundary equations
- Conservation validation

**Example**:
```bash
pytest tests/test_unit_equations.py -v
```

### 9. Unit Tests for Solve Method (`test_unit_solve_method.py`)

**Purpose**: Test the ODE solver integration and method behavior.

**Key Tests**:
- Solver initialization
- Time step handling
- Error handling
- Convergence criteria
- Result formatting

**Example**:
```bash
pytest tests/test_unit_solve_method.py -v
```

### 10. Integration Tests (`test_integration_solver.py`)

**Purpose**: Test the full solver integration and end-to-end simulations.

**Key Tests**:
- Complete simulation runs
- Multi-physics coupling
- State variable evolution
- Result consistency
- Solver stability

**Example**:
```bash
pytest tests/test_integration_solver.py -v
```

### 11. Validation Tests (`test_validation_paper_data.py`)

**Purpose**: Validate model results against experimental data from published research.

**Key Tests**:
- U-10Zr fuel validation (Figure 6)
- U-19Pu-10Zr fuel validation (Figure 7)
- High-purity uranium validation (Figures 9-10)
- Temperature-dependent swelling
- Burnup-dependent swelling

**Validation Criteria**:
- Final swelling percent within 10% of experimental data
- Bubble radius evolution matches trends
- Gas release fraction consistent with measurements

**Example**:
```bash
pytest tests/test_validation_paper_data.py -v
```

### 12. Edge Case Tests (`test_edge_cases.py`)

**Purpose**: Test boundary conditions, extreme parameters, and error handling.

**Key Tests**:
- Zero temperature limits
- Extreme fission rates
- Negative concentrations (should be prevented)
- Singular matrix handling
- Division by zero prevention
- Invalid parameter rejection

**Example**:
```bash
pytest tests/test_edge_cases.py -v
```

### 13. Performance Tests (`test_performance.py`)

**Purpose**: Benchmark computational performance and identify bottlenecks.

**Key Tests**:
- Simulation execution time
- Memory usage profiling
- Scaling with time steps
- Solver efficiency
- Numerical method performance

**Performance Targets**:
- 100-day simulation in < 120 seconds
- Memory usage < 500 MB for standard runs
- Linear scaling with time points

**Example**:
```bash
pytest tests/test_performance.py -v
```

## Test Fixtures

### Fixtures Overview

Test fixtures are defined in `tests/fixtures/conftest.py` and provide reusable test data and configurations.

**Available Fixtures**:

1. **`default_params`**: Default MaterialParameters and SimulationParameters
2. **`model_instance`**: Pre-configured GasSwellingModel instance
3. **`sample_temperatures`**: Array of test temperatures
4. **`sample_fission_rates`**: Array of test fission rates
5. **`paper_data`**: Experimental data from reference paper
6. **`expected_results`**: Pre-computed expected results

**Using Fixtures in Tests**:

```python
def test_example(default_params, model_instance):
    """Example test using fixtures"""
    params = default_params
    model = model_instance
    # Test code here
```

### Expected Results

The `tests/fixtures/expected_results.py` file contains expected results for validation tests:

- **Paper Figure Data**: Experimental data points from published figures
- **Validation Thresholds**: Acceptable error tolerances
- **Expected Swelling Values**: Benchmarked swelling percentages
- **Material Parameters**: Parameter sets for different fuel types

## Test Utilities

The `tests/utils.py` module provides custom assertion functions for enhanced testing:

### `assert_allclose`

Enhanced array comparison with detailed error messages:

```python
from tests.utils import assert_allclose

assert_allclose(actual, desired, rtol=1e-7, atol=0.0)
```

### `assert_relative_close`

Relative tolerance assertion:

```python
from tests.utils import assert_relative_close

assert_relative_close(actual, desired, rel_tol=1e-7)
```

### `assert_absolute_close`

Absolute tolerance assertion:

```python
from tests.utils import assert_absolute_close

assert_absolute_close(actual, desired, abs_tol=1e-7)
```

### `assert_array_shape`

Array shape validation:

```python
from tests.utils import assert_array_shape

assert_array_shape(array, expected_shape=(10,))
```

### `assert_array_monotonic`

Monotonicity checking:

```python
from tests.utils import assert_array_monotonic

assert_array_monotonic(array, increasing=True)
```

## Writing New Tests

### Test Structure Template

```python
"""
Brief description of what this test file covers
"""

import pytest
import numpy as np
from gas_swelling import GasSwellingModel, create_default_parameters


class TestFeature:
    """Test class for specific feature"""

    def test_specific_behavior(self):
        """Test that specific behavior works correctly"""
        # Arrange
        params = create_default_parameters()
        model = GasSwellingModel(params)

        # Act
        result = model.some_method()

        # Assert
        assert result is not None
        assert result > 0


@pytest.mark.parametrize("input_param,expected", [
    (value1, expected1),
    (value2, expected2),
])
def test_parameterized(input_param, expected):
    """Test with multiple input combinations"""
    assert some_function(input_param) == expected
```

### Best Practices

1. **Arrange-Act-Assert Pattern**: Structure tests clearly
2. **Descriptive Names**: Use clear test and function names
3. **One Assertion Per Test**: Keep tests focused
4. **Use Fixtures**: Avoid code duplication
5. **Test Edge Cases**: Include boundary conditions
6. **Mock External Dependencies**: Isolate unit tests
7. **Parameterize Tests**: Use `@pytest.mark.parametrize` for multiple cases
8. **Add Docstrings**: Document what each test verifies

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_slow_simulation():
    """Test that takes a long time"""
    pass

@pytest.mark.validation
def test_paper_validation():
    """Test against paper data"""
    pass

@pytest.mark.unit
def test_unit_calculation():
    """Unit test for calculation"""
    pass
```

Run marked tests:
```bash
pytest -m slow
pytest -m "not slow"
```

## Continuous Integration

### CI Pipeline

The test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=gas_swelling --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v2
```

### Pre-commit Hooks

Run tests before committing:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
```

## Troubleshooting

### Common Issues

**Issue**: Tests fail with import errors
```bash
# Solution: Install package in development mode
pip install -e .
```

**Issue**: Validation tests fail unexpectedly
```bash
# Solution: Check for recent parameter changes
pytest tests/test_validation_paper_data.py -v --tb=short
```

**Issue**: Performance tests timeout
```bash
# Solution: Run performance tests separately
pytest tests/test_performance.py -v --timeout=300
```

**Issue**: Fixture not found
```bash
# Solution: Ensure tests/fixtures/__init__.py exists
# Check conftest.py for fixture definitions
pytest --fixtures
```

### Debug Mode

Run tests with debugging output:

```bash
# Show print statements
pytest -v -s tests/test_file.py

# Drop into debugger on failure
pytest --pdb

# Use Python debugger
pytest --trace
```

## Test Coverage

### Current Coverage Goals

- **Unit Tests**: > 90% code coverage
- **Integration Tests**: All major code paths
- **Edge Cases**: All boundary conditions
- **Validation**: All published data points

### Generating Coverage Reports

```bash
# HTML coverage report
pytest --cov=gas_swelling --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=gas_swelling --cov-report=term-missing

# XML coverage report (for CI)
pytest --cov=gas_swelling --cov-report=xml
```

### Interpreting Coverage

- **Lines Covered**: Percentage of code lines executed
- **Branches Covered**: Percentage of conditional branches tested
- **Missing Lines**: Specific lines not covered (shown in terminal report)

## Contributing Tests

When contributing new tests:

1. **Follow Naming Conventions**: `test_<module>_<feature>.py`
2. **Add Docstrings**: Explain what the test verifies
3. **Use Existing Fixtures**: Don't recreate test data
4. **Run Linting**: Ensure code style consistency
5. **Update Documentation**: Add to this README if adding new test categories

## Resources

- **[Pytest Documentation](https://docs.pytest.org/)**: Comprehensive pytest guide
- **[Main README](../README.md)**: Project overview
- **[CLAUDE.md](../CLAUDE.md)**: Development guidelines
- **[Parameter Reference](../docs/parameter_reference.md)**: Parameter documentation

## Test Metrics

### Summary Statistics

- **Total Test Files**: 13
- **Total Test Cases**: 200+
- **Test Categories**: 7
- **Fixtures**: 10+
- **Utility Functions**: 6

### Coverage Targets

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| Core Model | 95% | TBD |
| Parameters | 100% | TBD |
| Equations | 90% | TBD |
| Solver | 85% | TBD |
| Utilities | 90% | TBD |

---

**For questions or issues with the test suite, please refer to the main project documentation or open an issue on GitHub.**
