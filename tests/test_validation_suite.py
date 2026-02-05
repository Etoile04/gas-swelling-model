"""
Fast-running validation test suite for CI/CD

This test suite provides quick validation tests that can run in CI/CD pipelines
without requiring long simulation times. It focuses on:

1. Validation module structure and availability
2. Validation datasets accessibility
3. Validation metrics correctness
4. Validation scripts importability
5. Short sanity-check simulations

Tests marked with @pytest.mark.slow are excluded from default CI runs.
Use: pytest tests/test_validation_suite.py -v -m 'not slow'
"""

import pytest
import numpy as np
from pathlib import Path

from gas_swelling import GasSwellingModel, create_default_parameters
from gas_swelling.validation.metrics import (
    calculate_rmse,
    calculate_mae,
    calculate_max_error,
    calculate_r2
)
from gas_swelling.validation.datasets import (
    get_u10zr_data,
    get_u19pu10zr_data,
    get_high_purity_u_data
)

# ============================================================================
# Validation Module Structure Tests
# ============================================================================

def test_validation_module_exists():
    """Test that validation module can be imported"""
    import gas_swelling.validation
    assert gas_swelling.validation is not None


def test_validation_metrics_module_exists():
    """Test that validation.metrics module can be imported"""
    import gas_swelling.validation.metrics
    assert gas_swelling.validation.metrics is not None


def test_validation_datasets_module_exists():
    """Test that validation.datasets module can be imported"""
    import gas_swelling.validation.datasets
    assert gas_swelling.validation.datasets is not None


def test_validation_reporting_module_exists():
    """Test that validation.reporting module can be imported"""
    import gas_swelling.validation.reporting
    assert gas_swelling.validation.reporting is not None


def test_validation_scripts_module_exists():
    """Test that validation.scripts module can be imported"""
    import gas_swelling.validation.scripts
    assert gas_swelling.validation.scripts is not None


# ============================================================================
# Validation Metrics Tests (Fast)
# ============================================================================

def test_metrics_functions_exist():
    """Test that all metric functions are available"""
    assert callable(calculate_rmse)
    assert callable(calculate_mae)
    assert callable(calculate_max_error)
    assert callable(calculate_r2)


def test_metrics_basic_functionality():
    """Test basic functionality of all metrics"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 3.1])

    rmse = calculate_rmse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    max_err = calculate_max_error(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)

    # All metrics should return floats
    assert isinstance(rmse, float)
    assert isinstance(mae, float)
    assert isinstance(max_err, float)
    assert isinstance(r2, float)

    # All metrics should be non-negative
    assert rmse >= 0
    assert mae >= 0
    assert max_err >= 0

    # R² should be close to 1 for good fit
    assert r2 > 0.9


def test_metrics_perfect_prediction():
    """Test metrics with perfect prediction"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])

    assert calculate_rmse(y_true, y_pred) == 0.0
    assert calculate_mae(y_true, y_pred) == 0.0
    assert calculate_max_error(y_true, y_pred) == 0.0
    assert calculate_r2(y_true, y_pred) == 1.0


def test_metrics_error_handling():
    """Test that metrics handle invalid inputs correctly"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred_wrong_length = np.array([1.1, 2.1])

    # All metrics should raise ValueError for length mismatch
    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_rmse(y_true, y_pred_wrong_length)

    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_mae(y_true, y_pred_wrong_length)

    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_max_error(y_true, y_pred_wrong_length)

    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_r2(y_true, y_pred_wrong_length)


# ============================================================================
# Validation Datasets Tests (Fast)
# ============================================================================

def test_u10zr_data_accessible():
    """Test that U-10Zr validation data is accessible"""
    data = get_u10zr_data()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check structure of first data point
    point = data[0]
    assert 'material' in point
    assert 'burnup_at_percent' in point
    assert 'temperature_k' in point
    assert 'swelling_percent' in point
    assert 'figure' in point


def test_u19pu10zr_data_accessible():
    """Test that U-19Pu-10Zr validation data is accessible"""
    data = get_u19pu10zr_data()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check structure of first data point
    point = data[0]
    assert 'material' in point
    assert 'burnup_at_percent' in point
    assert 'temperature_k' in point
    assert 'swelling_percent' in point
    assert 'figure' in point


def test_high_purity_u_data_accessible():
    """Test that high-purity uranium validation data is accessible"""
    data = get_high_purity_u_data()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check structure of first data point
    point = data[0]
    assert 'material' in point
    assert 'burnup_at_percent' in point
    assert 'temperature_k' in point
    assert 'swelling_percent' in point
    assert 'figure' in point


def test_dataset_material_names():
    """Test that datasets have correct material names"""
    u10zr_data = get_u10zr_data()
    u19pu10zr_data = get_u19pu10zr_data()
    high_purity_u_data = get_high_purity_u_data()

    # Check material names
    assert all(point['material'] == 'U-10Zr' for point in u10zr_data)
    assert all(point['material'] == 'U-19Pu-10Zr' for point in u19pu10zr_data)
    assert all(point['material'] == 'High-purity U' for point in high_purity_u_data)


def test_dataset_value_ranges():
    """Test that dataset values are in reasonable ranges"""
    u10zr_data = get_u10zr_data()

    for point in u10zr_data:
        # Burnup should be positive
        assert point['burnup_at_percent'] > 0

        # Temperature should be in reasonable range (400-1000K)
        assert 400 < point['temperature_k'] < 1000

        # Swelling should be non-negative
        assert point['swelling_percent'] >= 0


# ============================================================================
# Validation Scripts Import Tests (Fast)
# ============================================================================

def test_figure6_script_importable():
    """Test that Figure 6 reproduction script can be imported"""
    from gas_swelling.validation.scripts import reproduce_figure6
    assert reproduce_figure6 is not None
    assert hasattr(reproduce_figure6, 'main')


def test_figure7_script_importable():
    """Test that Figure 7 reproduction script can be imported"""
    from gas_swelling.validation.scripts import reproduce_figure7
    assert reproduce_figure7 is not None
    assert hasattr(reproduce_figure7, 'main')


def test_figures9_10_script_importable():
    """Test that Figures 9-10 reproduction script can be imported"""
    from gas_swelling.validation.scripts import reproduce_figures9_10
    assert reproduce_figures9_10 is not None
    assert hasattr(reproduce_figures9_10, 'main')


# ============================================================================
# Model Sanity Checks with Short Simulations (Fast)
# ============================================================================

def test_model_runs_with_u10zr_parameters():
    """Test that model runs successfully with U-10Zr parameters (short sim)"""
    params = create_default_parameters()
    params['temperature'] = 700  # K
    params['dislocation_density'] = 7.0e13  # m^-2
    params['Fnb'] = 1e-5
    params['Fnf'] = 1e-5
    params['fission_rate'] = 5.0e19  # fissions/m^3/s

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    sim_time = 1000  # Short simulation for CI
    t_eval = np.linspace(0, sim_time, 10)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Check result structure
    assert 'time' in result
    assert 'swelling' in result
    assert 'Cgb' in result
    assert 'Ccb' in result

    # Check that simulation produced results
    assert len(result['time']) == 10
    assert len(result['swelling']) == 10

    # Check that all values are finite
    assert np.all(np.isfinite(result['swelling']))
    assert np.all(np.isfinite(result['Cgb']))
    assert np.all(np.isfinite(result['Ccb']))


def test_model_runs_with_upuzr_parameters():
    """Test that model runs successfully with U-19Pu-10Zr parameters (short sim)"""
    params = create_default_parameters()
    params['temperature'] = 750  # K
    params['dislocation_density'] = 2.0e13  # m^-2 (lower than U-10Zr)
    params['Fnb'] = 1e-5
    params['Fnf'] = 1e-5
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    sim_time = 1000  # Short simulation for CI
    t_eval = np.linspace(0, sim_time, 10)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Check result structure
    assert 'swelling' in result
    assert len(result['swelling']) == 10

    # Check that all values are finite
    assert np.all(np.isfinite(result['swelling']))


def test_model_runs_with_high_purity_u_parameters():
    """Test that model runs successfully with high-purity U parameters (short sim)"""
    params = create_default_parameters()
    params['temperature'] = 673  # K
    params['dislocation_density'] = 1e15  # m^-2 (much higher than alloys)
    params['Fnb'] = 1e-5
    params['Fnf'] = 1.0  # Much higher than alloys!
    params['Evf'] = 1.7  # eV (higher than alloys)
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    sim_time = 1000  # Short simulation for CI
    t_eval = np.linspace(0, sim_time, 10)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Check result structure
    assert 'swelling' in result
    assert len(result['swelling']) == 10

    # Check that all values are finite
    assert np.all(np.isfinite(result['swelling']))


def test_model_provides_all_state_variables():
    """Test that model provides all expected state variables"""
    params = create_default_parameters()
    params['temperature'] = 700
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 500), t_eval=np.linspace(0, 500, 5))

    # Check for all expected state variables
    expected_keys = [
        'time', 'swelling',
        'Cgb', 'Ccb', 'Ncb', 'cvb', 'cib', 'Rcb',
        'Cgf', 'Ccf', 'Ncf', 'cvf', 'cif', 'Rcf'
    ]

    for key in expected_keys:
        assert key in result, f"Missing state variable: {key}"
        assert len(result[key]) == 5, f"Incorrect length for {key}"


# ============================================================================
# Physical Reasonableness Tests (Fast)
# ============================================================================

def test_swelling_is_non_negative():
    """Test that swelling remains non-negative during simulation"""
    params = create_default_parameters()
    params['temperature'] = 700
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 10))

    # All swelling values should be non-negative
    assert np.all(result['swelling'] >= 0), "Swelling should be non-negative"


def test_concentrations_are_non_negative():
    """Test that concentrations remain non-negative during simulation"""
    params = create_default_parameters()
    params['temperature'] = 700
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 10))

    # All concentrations should be non-negative
    for key in ['Cgb', 'Ccb', 'Ncb', 'Cgf', 'Ccf', 'Ncf']:
        assert np.all(result[key] >= 0), f"{key} should be non-negative"


def test_bubble_radius_is_positive():
    """Test that bubble radius is positive during simulation"""
    params = create_default_parameters()
    params['temperature'] = 700
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 10))

    # Bubble radius should be positive (or zero initially)
    for key in ['Rcb', 'Rcf']:
        assert np.all(result[key] >= 0), f"{key} should be non-negative"


# ============================================================================
# Integration Tests (Fast)
# ============================================================================

def test_validation_metrics_with_model_output():
    """Test that validation metrics work with actual model output"""
    params = create_default_parameters()
    params['temperature'] = 700
    params['fission_rate'] = 5.0e19

    # Add gas diffusion parameters
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-8
    params['gas_production_rate'] = 0.5
    params['resolution_rate'] = 2.0e-5

    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 10))

    # Use swelling data for metrics calculation
    swelling = result['swelling']
    # Create synthetic "expected" values (just slightly different)
    expected = swelling * 1.1

    # Test all metrics
    rmse = calculate_rmse(expected, swelling)
    mae = calculate_mae(expected, swelling)
    max_err = calculate_max_error(expected, swelling)
    r2 = calculate_r2(expected, swelling)

    # All should return valid numbers
    assert np.isfinite(rmse)
    assert np.isfinite(mae)
    assert np.isfinite(max_err)
    assert np.isfinite(r2)

    # All should be non-negative
    assert rmse >= 0
    assert mae >= 0
    assert max_err >= 0


def test_validation_data_structure_consistency():
    """Test that all validation datasets have consistent structure"""
    u10zr_data = get_u10zr_data()
    u19pu10zr_data = get_u19pu10zr_data()
    high_purity_u_data = get_high_purity_u_data()

    # All datasets should have the same keys
    required_keys = [
        'material', 'burnup_at_percent', 'temperature_k',
        'swelling_percent', 'figure', 'data_type'
    ]

    for dataset in [u10zr_data, u19pu10zr_data, high_purity_u_data]:
        for point in dataset:
            for key in required_keys:
                assert key in point, f"Missing key {key} in data point"


# ============================================================================
# Slow Tests (marked for exclusion from CI)
# ============================================================================

@pytest.mark.slow
def test_validation_report_module_importable():
    """Test that validation report module can be imported (slow due to complex imports)"""
    from gas_swelling.validation.reporting import (
        generate_validation_report,
        run_simulation_for_material
    )
    assert callable(generate_validation_report)
    assert callable(run_simulation_for_material)


@pytest.mark.slow
def test_model_runs_multiple_temperatures():
    """Test model at multiple temperatures (slower test)"""
    temperatures = [600, 650, 700, 750, 800, 850]

    for temp in temperatures:
        params = create_default_parameters()
        params['temperature'] = temp
        params['fission_rate'] = 5.0e19

        # Add gas diffusion parameters
        params['Dgb_prefactor'] = 8.55e-12
        params['Dgb_fission_term'] = 1.0e-40
        params['Dgf_multiplier'] = 1.0
        params['Dv0'] = 7.767e-8
        params['gas_production_rate'] = 0.5
        params['resolution_rate'] = 2.0e-5

        model = GasSwellingModel(params)
        result = model.solve(t_span=(0, 500), t_eval=np.linspace(0, 500, 5))

        # Check that simulation completed successfully
        assert 'swelling' in result
        assert np.all(np.isfinite(result['swelling']))


@pytest.mark.slow
def test_all_materials_with_correct_parameters():
    """Test all three materials with their correct parameters (slower)"""
    materials = [
        {
            'name': 'U-10Zr',
            'rho': 7.0e13,
            'temp': 700
        },
        {
            'name': 'U-19Pu-10Zr',
            'rho': 2.0e13,
            'temp': 750
        },
        {
            'name': 'High-purity U',
            'rho': 1e15,
            'temp': 673,
            'Fnf': 1.0,
            'Evf': 1.7
        }
    ]

    for mat in materials:
        params = create_default_parameters()
        params['temperature'] = mat['temp']
        params['dislocation_density'] = mat['rho']
        params['Fnb'] = 1e-5
        params['Fnf'] = mat.get('Fnf', 1e-5)
        if 'Evf' in mat:
            params['Evf'] = mat['Evf']
        params['fission_rate'] = 5.0e19

        # Add gas diffusion parameters
        params['Dgb_prefactor'] = 8.55e-12
        params['Dgb_fission_term'] = 1.0e-40
        params['Dgf_multiplier'] = 1.0
        params['Dv0'] = 7.767e-8
        params['gas_production_rate'] = 0.5
        params['resolution_rate'] = 2.0e-5

        model = GasSwellingModel(params)
        result = model.solve(t_span=(0, 1000), t_eval=np.linspace(0, 1000, 10))

        # Check that simulation completed successfully
        assert 'swelling' in result
        assert np.all(np.isfinite(result['swelling']))
