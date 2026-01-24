"""
Test sensitivity analyzers (OAT, Morris, Sobol)
"""

import pytest
import numpy as np
from gas_swelling.analysis.sensitivity import (
    ParameterRange,
    SensitivityAnalyzer,
    OATAnalyzer,
    OATResult,
    MorrisAnalyzer,
    MorrisResult,
    SobolAnalyzer,
    SobolResult,
    create_default_parameter_ranges
)
from gas_swelling.params.parameters import create_default_parameters


# =============================================================================
# ParameterRange Tests
# =============================================================================

def test_parameter_range_creation():
    """Test basic ParameterRange creation"""
    pr = ParameterRange('temperature', 600, 800, nominal_value=700)
    assert pr.name == 'temperature'
    assert pr.min_value == 600
    assert pr.max_value == 800
    assert pr.nominal_value == 700
    assert pr.distribution == 'uniform'


def test_parameter_range_default_nominal():
    """Test that nominal value defaults to midpoint"""
    pr = ParameterRange('temperature', 600, 800)
    assert pr.nominal_value == 700


def test_parameter_range_invalid_bounds():
    """Test that invalid bounds raise ValueError"""
    with pytest.raises(ValueError, match="min_value must be less than max_value"):
        ParameterRange('temperature', 800, 600)


def test_parameter_range_nominal_out_of_bounds():
    """Test that nominal value outside bounds raises ValueError"""
    with pytest.raises(ValueError, match="must be within bounds"):
        ParameterRange('temperature', 600, 800, nominal_value=900)


def test_parameter_range_invalid_distribution():
    """Test that invalid distribution raises ValueError"""
    with pytest.raises(ValueError, match="distribution must be one of"):
        ParameterRange('temperature', 600, 800, distribution='invalid')


def test_parameter_range_loguniform_negative_bounds():
    """Test that loguniform requires positive bounds"""
    with pytest.raises(ValueError, match="requires positive"):
        ParameterRange('temperature', -10, 800, distribution='loguniform')


def test_parameter_range_sample_uniform():
    """Test uniform sampling"""
    pr = ParameterRange('temperature', 600, 800, distribution='uniform')
    samples = pr.sample(100, random_state=42)
    assert len(samples) == 100
    assert np.all(samples >= 600)
    assert np.all(samples <= 800)


def test_parameter_range_sample_loguniform():
    """Test loguniform sampling"""
    pr = ParameterRange('density', 1e13, 1e14, distribution='loguniform')
    samples = pr.sample(100, random_state=42)
    assert len(samples) == 100
    assert np.all(samples >= 1e13)
    assert np.all(samples <= 1e14)


def test_parameter_range_to_dict():
    """Test ParameterRange to_dict conversion"""
    pr = ParameterRange('temperature', 600, 800, nominal_value=700)
    d = pr.to_dict()
    assert d['name'] == 'temperature'
    assert d['min_value'] == 600
    assert d['max_value'] == 800
    assert d['nominal_value'] == 700


# =============================================================================
# SensitivityAnalyzer Base Class Tests
# =============================================================================

def test_sensitivity_analyzer_creation():
    """Test basic SensitivityAnalyzer creation"""
    analyzer = SensitivityAnalyzer()
    assert analyzer.base_parameters is not None
    assert analyzer.parameter_ranges == []
    assert analyzer.output_names == ['swelling']


def test_sensitivity_analyzer_with_parameter_ranges():
    """Test SensitivityAnalyzer with parameter ranges"""
    ranges = [
        ParameterRange('temperature', 600, 800),
        ParameterRange('fission_rate', 1e20, 5e20)
    ]
    analyzer = SensitivityAnalyzer(parameter_ranges=ranges)
    assert len(analyzer.parameter_ranges) == 2
    assert analyzer.get_n_parameters() == 2


def test_sensitivity_analyzer_add_parameter_range():
    """Test adding parameter range"""
    analyzer = SensitivityAnalyzer()
    pr = ParameterRange('temperature', 600, 800)
    analyzer.add_parameter_range(pr)
    assert len(analyzer.parameter_ranges) == 1


def test_sensitivity_analyzer_add_duplicate_parameter():
    """Test that adding duplicate parameter raises ValueError"""
    analyzer = SensitivityAnalyzer()
    pr1 = ParameterRange('temperature', 600, 800)
    pr2 = ParameterRange('temperature', 500, 900)
    analyzer.add_parameter_range(pr1)
    with pytest.raises(ValueError, match="already exists"):
        analyzer.add_parameter_range(pr2)


def test_sensitivity_analyzer_remove_parameter_range():
    """Test removing parameter range"""
    analyzer = SensitivityAnalyzer()
    pr = ParameterRange('temperature', 600, 800)
    analyzer.add_parameter_range(pr)
    analyzer.remove_parameter_range('temperature')
    assert len(analyzer.parameter_ranges) == 0


def test_sensitivity_analyzer_remove_nonexistent_parameter():
    """Test that removing nonexistent parameter raises ValueError"""
    analyzer = SensitivityAnalyzer()
    with pytest.raises(ValueError, match="not found"):
        analyzer.remove_parameter_range('temperature')


def test_sensitivity_analyzer_get_parameter_range():
    """Test getting parameter range"""
    analyzer = SensitivityAnalyzer()
    pr = ParameterRange('temperature', 600, 800)
    analyzer.add_parameter_range(pr)
    retrieved = analyzer.get_parameter_range('temperature')
    assert retrieved.name == 'temperature'
    assert retrieved.min_value == 600


def test_sensitivity_analyzer_get_nominal_parameters():
    """Test getting nominal parameters"""
    ranges = [
        ParameterRange('temperature', 600, 800, nominal_value=700),
        ParameterRange('fission_rate', 1e20, 5e20, nominal_value=2e20)
    ]
    analyzer = SensitivityAnalyzer(parameter_ranges=ranges)
    nominal = analyzer.get_nominal_parameters()
    assert nominal['temperature'] == 700
    assert nominal['fission_rate'] == 2e20


def test_sensitivity_analyzer_apply_parameters_dict():
    """Test applying parameters as dict"""
    analyzer = SensitivityAnalyzer()
    base = {'temperature': 700, 'fission_rate': 2e20}
    new_params = analyzer.apply_parameters(base, {'temperature': 750})
    assert new_params['temperature'] == 750
    assert new_params['fission_rate'] == 2e20


def test_sensitivity_analyzer_apply_parameters_array():
    """Test applying parameters as array"""
    ranges = [
        ParameterRange('temperature', 600, 800),
        ParameterRange('fission_rate', 1e20, 5e20)
    ]
    analyzer = SensitivityAnalyzer(parameter_ranges=ranges)
    base = analyzer.get_nominal_parameters()
    new_values = np.array([750, 2.5e20])
    new_params = analyzer.apply_parameters(base, new_values)
    assert new_params['temperature'] == 750
    assert new_params['fission_rate'] == 2.5e20


def test_sensitivity_analyzer_apply_parameters_mismatched_array():
    """Test that mismatched array length raises ValueError"""
    ranges = [
        ParameterRange('temperature', 600, 800),
        ParameterRange('fission_rate', 1e20, 5e20)
    ]
    analyzer = SensitivityAnalyzer(parameter_ranges=ranges)
    base = analyzer.get_nominal_parameters()
    new_values = np.array([750])  # Only one value
    with pytest.raises(ValueError, match="does not match"):
        analyzer.apply_parameters(base, new_values)


def test_sensitivity_analyzer_validate_parameter_ranges():
    """Test parameter range validation"""
    analyzer = SensitivityAnalyzer()
    pr = ParameterRange('nonexistent_param', 0, 100)
    analyzer.add_parameter_range(pr)
    errors = analyzer.validate_parameter_ranges()
    assert len(errors) > 0
    assert 'nonexistent_param' in errors[0]


def test_sensitivity_analyzer_get_parameter_names():
    """Test getting parameter names"""
    ranges = [
        ParameterRange('temperature', 600, 800),
        ParameterRange('fission_rate', 1e20, 5e20)
    ]
    analyzer = SensitivityAnalyzer(parameter_ranges=ranges)
    names = analyzer.get_parameter_names()
    assert names == ['temperature', 'fission_rate']


def test_sensitivity_analyzer_summary():
    """Test analyzer summary"""
    ranges = [
        ParameterRange('temperature', 600, 800)
    ]
    analyzer = SensitivityAnalyzer(parameter_ranges=ranges)
    summary = analyzer.summary()
    assert summary['n_parameters'] == 1
    assert 'temperature' in summary['parameter_names']


def test_create_default_parameter_ranges():
    """Test creation of default parameter ranges"""
    ranges = create_default_parameter_ranges()
    assert len(ranges) > 0
    assert any(pr.name == 'temperature' for pr in ranges)
    assert any(pr.name == 'fission_rate' for pr in ranges)


# =============================================================================
# OATAnalyzer Tests
# =============================================================================

def test_oat_analyzer_creation():
    """Test basic OATAnalyzer creation"""
    analyzer = OATAnalyzer()
    assert analyzer.sim_time == 7200000.0
    assert analyzer.t_eval_points == 100


def test_oat_analyzer_with_custom_settings():
    """Test OATAnalyzer with custom settings"""
    analyzer = OATAnalyzer(
        sim_time=3600000.0,
        t_eval_points=50
    )
    assert analyzer.sim_time == 3600000.0
    assert analyzer.t_eval_points == 50


def test_oat_analyzer_extract_output_swelling():
    """Test extracting swelling output"""
    analyzer = OATAnalyzer()
    # Create a mock result
    result = {
        'Rcb': np.array([1e-7, 1e-7]),
        'Rcf': np.array([1e-7, 1e-7]),
        'Ccb': np.array([1e20, 1e20]),
        'Ccf': np.array([1e20, 1e20])
    }
    swelling = analyzer.extract_output(result, 'swelling')
    assert isinstance(swelling, float)


def test_oat_analyzer_extract_output_invalid():
    """Test that invalid output name raises ValueError"""
    analyzer = OATAnalyzer()
    result = {'Rcb': np.array([1e-7, 1e-7])}
    with pytest.raises(ValueError, match="Unknown output"):
        analyzer.extract_output(result, 'invalid_output')


def test_oat_analyzer_calculate_sensitivity_metrics():
    """Test sensitivity metrics calculation"""
    analyzer = OATAnalyzer()
    param_values = np.array([650, 700, 750])
    output_values = np.array([0.8, 1.0, 1.2])
    metrics = analyzer.calculate_sensitivity_metrics(
        param_values, output_values, 700, 1.0
    )
    assert 'normalized' in metrics
    assert 'elasticity' in metrics
    assert 'std' in metrics


def test_oat_analyzer_calculate_sensitivity_metrics_zero_nominal():
    """Test that zero nominal values return zero metrics"""
    analyzer = OATAnalyzer()
    param_values = np.array([1, 2, 3])
    output_values = np.array([0.1, 0.2, 0.3])
    metrics = analyzer.calculate_sensitivity_metrics(
        param_values, output_values, 0, 0
    )
    assert metrics['normalized'] == 0.0
    assert metrics['elasticity'] == 0.0


def test_oat_analyzer_run_oat_analysis_no_parameters():
    """Test that OAT analysis without parameters raises ValueError"""
    analyzer = OATAnalyzer()
    with pytest.raises(ValueError, match="No parameter ranges defined"):
        analyzer.run_oat_analysis(verbose=False)


def test_oat_analyzer_summary():
    """Test OAT analyzer summary"""
    ranges = [ParameterRange('temperature', 600, 800)]
    analyzer = OATAnalyzer(parameter_ranges=ranges)

    # Create mock results
    results = [
        OATResult(
            parameter_name='temperature',
            nominal_value=700,
            variations=[650, 750],
            outputs={'swelling': np.array([0.8, 1.2])},
            sensitivities={'swelling': {'normalized': 1.0, 'elasticity': 1.0, 'std': 0.0}},
            baseline_outputs={'swelling': 1.0}
        )
    ]

    summary = analyzer.summary(results)
    assert summary['n_parameters_analyzed'] == 1
    assert 'parameter_ranking' in summary


# =============================================================================
# OATResult Tests
# =============================================================================

def test_oat_result_creation():
    """Test OATResult creation"""
    result = OATResult(
        parameter_name='temperature',
        nominal_value=700,
        variations=[650, 700, 750],
        outputs={'swelling': np.array([0.8, 1.0, 1.2])},
        sensitivities={'swelling': {'normalized': 1.0, 'elasticity': 1.0, 'std': 0.0}},
        baseline_outputs={'swelling': 1.0}
    )
    assert result.parameter_name == 'temperature'
    assert result.nominal_value == 700
    assert len(result.variations) == 3


def test_oat_result_to_dict():
    """Test OATResult to_dict conversion"""
    result = OATResult(
        parameter_name='temperature',
        nominal_value=700,
        variations=[650, 750],
        outputs={'swelling': np.array([0.8, 1.2])},
        sensitivities={'swelling': {'normalized': 1.0, 'elasticity': 1.0, 'std': 0.0}},
        baseline_outputs={'swelling': 1.0}
    )
    d = result.to_dict()
    assert d['parameter_name'] == 'temperature'
    assert isinstance(d['outputs']['swelling'], list)  # Should be converted from array


# =============================================================================
# MorrisAnalyzer Tests
# =============================================================================

def test_morris_analyzer_creation():
    """Test basic MorrisAnalyzer creation"""
    analyzer = MorrisAnalyzer()
    assert analyzer.num_levels == 10
    assert 0 < analyzer.delta < 1


def test_morris_analyzer_with_custom_levels():
    """Test MorrisAnalyzer with custom levels"""
    analyzer = MorrisAnalyzer(num_levels=8)
    assert analyzer.num_levels == 8
    assert analyzer.delta == pytest.approx(8.0 / (2.0 * 7.0))


def test_morris_analyzer_invalid_delta():
    """Test that invalid delta raises ValueError"""
    with pytest.raises(ValueError, match="delta must be in"):
        MorrisAnalyzer(delta=1.5)


def test_morris_analyzer_extract_output_swelling():
    """Test extracting swelling output"""
    analyzer = MorrisAnalyzer()
    result = {
        'Rcb': np.array([1e-7, 1e-7]),
        'Rcf': np.array([1e-7, 1e-7]),
        'Ccb': np.array([1e20, 1e20]),
        'Ccf': np.array([1e20, 1e20])
    }
    swelling = analyzer.extract_output(result, 'swelling')
    assert isinstance(swelling, float)


def test_morris_analyzer_extract_output_invalid():
    """Test that invalid output name raises ValueError"""
    analyzer = MorrisAnalyzer()
    result = {'Rcb': np.array([1e-7, 1e-7])}
    with pytest.raises(ValueError, match="Unknown output"):
        analyzer.extract_output(result, 'invalid_output')


def test_morris_analyzer_generate_trajectory():
    """Test trajectory generation"""
    ranges = [
        ParameterRange('temperature', 600, 800),
        ParameterRange('fission_rate', 1e20, 5e20)
    ]
    analyzer = MorrisAnalyzer(parameter_ranges=ranges)
    trajectory = analyzer.generate_trajectory(random_state=42)
    assert trajectory.shape == (3, 2)  # (n_params + 1, n_params)
    assert np.all(trajectory >= 0)
    assert np.all(trajectory <= 1)


def test_morris_analyzer_map_trajectory_to_parameters():
    """Test mapping trajectory to parameters"""
    ranges = [ParameterRange('temperature', 600, 800)]
    analyzer = MorrisAnalyzer(parameter_ranges=ranges)
    trajectory = np.array([[0.0], [0.5], [1.0]])
    param_dicts = analyzer.map_trajectory_to_parameters(trajectory)
    assert len(param_dicts) == 3
    assert param_dicts[0]['temperature'] == 600
    assert param_dicts[1]['temperature'] == 700
    assert param_dicts[2]['temperature'] == 800


def test_morris_analyzer_compute_elementary_effects():
    """Test elementary effects computation"""
    ranges = [ParameterRange('temperature', 600, 800)]
    analyzer = MorrisAnalyzer(parameter_ranges=ranges)
    outputs = [1.0, 1.5, 2.0]  # Three outputs for 2 parameters + 1
    ee = analyzer.compute_elementary_effects(outputs)
    assert len(ee) == 1  # One parameter


def test_morris_analyzer_run_morris_analysis_no_parameters():
    """Test that Morris analysis without parameters raises ValueError"""
    analyzer = MorrisAnalyzer()
    with pytest.raises(ValueError, match="No parameter ranges defined"):
        analyzer.run_morris_analysis(n_trajectories=2, verbose=False)


def test_morris_analyzer_summary():
    """Test Morris analyzer summary"""
    ranges = [ParameterRange('temperature', 600, 800)]
    analyzer = MorrisAnalyzer(parameter_ranges=ranges)

    # Create mock results
    results = MorrisResult(
        parameter_names=['temperature'],
        mu=np.array([0.5]),
        mu_star=np.array([0.6]),
        sigma=np.array([0.2]),
        elementary_effects={'swelling': np.array([[0.5, 0.7]])},
        output_names=['swelling'],
        n_trajectories=10
    )

    summary = analyzer.summary(results)
    assert summary['n_trajectories'] == 10
    assert 'parameter_ranking' in summary


# =============================================================================
# MorrisResult Tests
# =============================================================================

def test_morris_result_creation():
    """Test MorrisResult creation"""
    result = MorrisResult(
        parameter_names=['temperature', 'fission_rate'],
        mu=np.array([0.5, 0.3]),
        mu_star=np.array([0.6, 0.4]),
        sigma=np.array([0.2, 0.1]),
        elementary_effects={'swelling': np.array([[0.5, 0.7], [0.3, 0.4]])},
        output_names=['swelling'],
        n_trajectories=10
    )
    assert len(result.parameter_names) == 2
    assert result.n_trajectories == 10


def test_morris_result_to_dict():
    """Test MorrisResult to_dict conversion"""
    result = MorrisResult(
        parameter_names=['temperature'],
        mu=np.array([0.5]),
        mu_star=np.array([0.6]),
        sigma=np.array([0.2]),
        elementary_effects={'swelling': np.array([[0.5, 0.7]])},
        output_names=['swelling'],
        n_trajectories=10
    )
    d = result.to_dict()
    assert d['parameter_names'] == ['temperature']
    assert isinstance(d['mu'], list)  # Should be converted from array


def test_morris_result_get_ranking():
    """Test parameter ranking by mu_star"""
    result = MorrisResult(
        parameter_names=['temperature', 'fission_rate'],
        mu=np.array([0.5, 0.3]),
        mu_star=np.array([0.6, 0.4]),
        sigma=np.array([0.2, 0.1]),
        elementary_effects={'swelling': np.array([[0.5, 0.7], [0.3, 0.4]])},
        output_names=['swelling'],
        n_trajectories=10
    )
    ranking = result.get_ranking('swelling')
    assert len(ranking) == 2
    assert ranking[0][0] == 'temperature'  # Higher mu_star


def test_morris_result_get_ranking_invalid_output():
    """Test that invalid output name raises ValueError"""
    result = MorrisResult(
        parameter_names=['temperature'],
        mu=np.array([0.5]),
        mu_star=np.array([0.6]),
        sigma=np.array([0.2]),
        elementary_effects={'swelling': np.array([[0.5, 0.7]])},
        output_names=['swelling'],
        n_trajectories=10
    )
    with pytest.raises(ValueError, match="not in results"):
        result.get_ranking('invalid_output')


# =============================================================================
# SobolAnalyzer Tests
# =============================================================================

def test_sobol_analyzer_creation():
    """Test basic SobolAnalyzer creation"""
    analyzer = SobolAnalyzer()
    assert analyzer.sim_time == 7200000.0
    assert analyzer.t_eval_points == 100
    assert analyzer.calc_second_order is False


def test_sobol_analyzer_with_custom_settings():
    """Test SobolAnalyzer with custom settings"""
    analyzer = SobolAnalyzer(
        sim_time=3600000.0,
        t_eval_points=50,
        calc_second_order=True
    )
    assert analyzer.sim_time == 3600000.0
    assert analyzer.t_eval_points == 50
    assert analyzer.calc_second_order is True


def test_sobol_analyzer_extract_output_swelling():
    """Test extracting swelling output"""
    analyzer = SobolAnalyzer()
    result = {
        'Rcb': np.array([1e-7, 1e-7]),
        'Rcf': np.array([1e-7, 1e-7]),
        'Ccb': np.array([1e20, 1e20]),
        'Ccf': np.array([1e20, 1e20])
    }
    swelling = analyzer.extract_output(result, 'swelling')
    assert isinstance(swelling, float)


def test_sobol_analyzer_extract_output_invalid():
    """Test that invalid output name raises ValueError"""
    analyzer = SobolAnalyzer()
    result = {'Rcb': np.array([1e-7, 1e-7])}
    with pytest.raises(ValueError, match="Unknown output"):
        analyzer.extract_output(result, 'invalid_output')


def test_sobol_analyzer_generate_saltelli_samples():
    """Test Saltelli sample generation"""
    ranges = [
        ParameterRange('temperature', 600, 800),
        ParameterRange('fission_rate', 1e20, 5e20)
    ]
    analyzer = SobolAnalyzer(parameter_ranges=ranges)
    samples = analyzer.generate_saltelli_samples(n_samples=10, random_state=42)
    # Should have N * (2 + p) samples
    expected_shape = (10 * (2 + 2), 2)
    assert samples.shape == expected_shape
    assert np.all(samples >= 0)
    assert np.all(samples <= 1)


def test_sobol_analyzer_map_samples_to_parameters():
    """Test mapping samples to parameters"""
    ranges = [ParameterRange('temperature', 600, 800)]
    analyzer = SobolAnalyzer(parameter_ranges=ranges)
    samples = np.array([[0.0], [0.5], [1.0]])
    param_dicts = analyzer.map_samples_to_parameters(samples)
    assert len(param_dicts) == 3
    assert param_dicts[0]['temperature'] == 600
    assert param_dicts[1]['temperature'] == 700
    assert param_dicts[2]['temperature'] == 800


def test_sobol_analyzer_compute_sobol_indices():
    """Test Sobol indices computation"""
    analyzer = SobolAnalyzer()
    Y_A = np.array([1.0, 2.0, 3.0])
    Y_B = np.array([1.5, 2.5, 3.5])
    Y_AB = np.array([[1.2, 2.2, 3.2]])

    S1, ST = analyzer.compute_sobol_indices(Y_A, Y_B, Y_AB)
    assert len(S1) == 1
    assert len(ST) == 1
    assert S1[0] >= 0  # Should be non-negative
    assert ST[0] >= 0  # Should be non-negative


def test_sobol_analyzer_compute_sobol_indices_zero_variance():
    """Test Sobol indices with zero variance"""
    analyzer = SobolAnalyzer()
    Y_A = np.array([1.0, 1.0, 1.0])
    Y_B = np.array([1.0, 1.0, 1.0])
    Y_AB = np.array([[1.0, 1.0, 1.0]])

    S1, ST = analyzer.compute_sobol_indices(Y_A, Y_B, Y_AB)
    assert np.all(S1 == 0)
    assert np.all(ST == 0)


def test_sobol_analyzer_run_sobol_analysis_no_parameters():
    """Test that Sobol analysis without parameters raises ValueError"""
    analyzer = SobolAnalyzer()
    with pytest.raises(ValueError, match="No parameter ranges defined"):
        analyzer.run_sobol_analysis(n_samples=10, verbose=False)


def test_sobol_analyzer_summary():
    """Test Sobol analyzer summary"""
    ranges = [ParameterRange('temperature', 600, 800)]
    analyzer = SobolAnalyzer(parameter_ranges=ranges)

    # Create mock results
    results = SobolResult(
        parameter_names=['temperature'],
        S1=np.array([[0.6]]),
        ST=np.array([[0.7]]),
        output_names=['swelling'],
        n_samples=100
    )

    summary = analyzer.summary(results)
    assert summary['n_samples'] == 100
    assert 'parameter_ranking' in summary


# =============================================================================
# SobolResult Tests
# =============================================================================

def test_sobol_result_creation():
    """Test SobolResult creation"""
    result = SobolResult(
        parameter_names=['temperature', 'fission_rate'],
        S1=np.array([[0.6, 0.3], [0.2, 0.4]]),
        ST=np.array([[0.7, 0.5], [0.3, 0.6]]),
        output_names=['swelling', 'gas_release'],
        n_samples=100
    )
    assert len(result.parameter_names) == 2
    assert result.n_samples == 100
    assert result.S1.shape == (2, 2)
    assert result.ST.shape == (2, 2)


def test_sobol_result_with_confidence_intervals():
    """Test SobolResult with confidence intervals"""
    result = SobolResult(
        parameter_names=['temperature'],
        S1=np.array([[0.6]]),
        ST=np.array([[0.7]]),
        output_names=['swelling'],
        n_samples=100,
        S1_conf=np.array([[0.05]]),
        ST_conf=np.array([[0.05]])
    )
    assert result.S1_conf is not None
    assert result.ST_conf is not None


def test_sobol_result_to_dict():
    """Test SobolResult to_dict conversion"""
    result = SobolResult(
        parameter_names=['temperature'],
        S1=np.array([[0.6]]),
        ST=np.array([[0.7]]),
        output_names=['swelling'],
        n_samples=100
    )
    d = result.to_dict()
    assert d['parameter_names'] == ['temperature']
    assert isinstance(d['S1'], list)  # Should be converted from array
    assert isinstance(d['ST'], list)


def test_sobol_result_get_ranking_by_ST():
    """Test parameter ranking by total-order index"""
    result = SobolResult(
        parameter_names=['temperature', 'fission_rate'],
        S1=np.array([[0.6], [0.2]]),
        ST=np.array([[0.7], [0.3]]),
        output_names=['swelling'],
        n_samples=100
    )
    ranking = result.get_ranking('swelling', order='ST')
    assert len(ranking) == 2
    assert ranking[0][0] == 'temperature'  # Higher ST


def test_sobol_result_get_ranking_by_S1():
    """Test parameter ranking by first-order index"""
    result = SobolResult(
        parameter_names=['temperature', 'fission_rate'],
        S1=np.array([[0.6], [0.2]]),
        ST=np.array([[0.7], [0.3]]),
        output_names=['swelling'],
        n_samples=100
    )
    ranking = result.get_ranking('swelling', order='S1')
    assert len(ranking) == 2
    assert ranking[0][0] == 'temperature'  # Higher S1


def test_sobol_result_get_ranking_invalid_output():
    """Test that invalid output name raises ValueError"""
    result = SobolResult(
        parameter_names=['temperature'],
        S1=np.array([[0.6]]),
        ST=np.array([[0.7]]),
        output_names=['swelling'],
        n_samples=100
    )
    with pytest.raises(ValueError, match="not in results"):
        result.get_ranking('invalid_output')


def test_sobol_result_get_ranking_invalid_order():
    """Test that invalid order defaults to ST"""
    result = SobolResult(
        parameter_names=['temperature'],
        S1=np.array([[0.6]]),
        ST=np.array([[0.7]]),
        output_names=['swelling'],
        n_samples=100
    )
    # Should use ST (default behavior) even with invalid order
    ranking = result.get_ranking('swelling', order='invalid')
    assert len(ranking) == 1


# =============================================================================
# End-to-End Workflow Tests (Integration Tests)
# =============================================================================

def test_oat_workflow():
    """
    Integration test for complete OAT sensitivity analysis workflow.

    This test verifies the end-to-end workflow:
    1. Create parameter ranges
    2. Initialize OAT analyzer
    3. Run analysis
    4. Verify results structure and content
    """
    # Step 1: Define parameter ranges
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700),
        ParameterRange('fission_rate', 1.5e20, 2.5e20, nominal_value=2e20)
    ]

    # Step 2: Create analyzer with short simulation for testing
    analyzer = OATAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=3600000.0,  # ~41 days for faster testing
        t_eval_points=50
    )

    # Step 3: Run OAT analysis
    results = analyzer.run_oat_analysis(
        percent_variations=[-10, 10],
        verbose=False
    )

    # Step 4: Verify results structure
    assert isinstance(results, list)
    assert len(results) == 2  # Two parameters analyzed

    # Verify first result (temperature)
    temp_result = results[0]
    assert temp_result.parameter_name == 'temperature'
    assert temp_result.nominal_value == 700
    assert len(temp_result.variations) == 2  # Two variations tested
    assert 'swelling' in temp_result.outputs
    assert 'swelling' in temp_result.sensitivities
    assert 'swelling' in temp_result.baseline_outputs

    # Verify sensitivity metrics structure
    sens = temp_result.sensitivities['swelling']
    assert 'normalized' in sens
    assert 'elasticity' in sens
    assert 'std' in sens
    assert isinstance(sens['normalized'], (int, float))
    assert isinstance(sens['elasticity'], (int, float))
    assert isinstance(sens['std'], (int, float))

    # Verify second result (fission_rate)
    fission_result = results[1]
    assert fission_result.parameter_name == 'fission_rate'
    assert fission_result.nominal_value == 2e20

    # Verify outputs are arrays/floats
    assert hasattr(temp_result.outputs['swelling'], '__len__')  # Should be array-like
    assert isinstance(temp_result.baseline_outputs['swelling'], (int, float))


def test_oat_workflow_multiple_outputs():
    """
    Integration test for OAT workflow with multiple output metrics.
    """
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700)
    ]

    analyzer = OATAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling', 'final_bubble_radius_bulk', 'gas_release_fraction'],
        sim_time=3600000.0,
        t_eval_points=50
    )

    results = analyzer.run_oat_analysis(
        percent_variations=[-5, 5],
        verbose=False
    )

    assert len(results) == 1
    result = results[0]

    # Verify all outputs are present
    for output_name in ['swelling', 'final_bubble_radius_bulk', 'gas_release_fraction']:
        assert output_name in result.outputs
        assert output_name in result.sensitivities
        assert output_name in result.baseline_outputs

        # Verify sensitivity metrics for each output
        assert 'normalized' in result.sensitivities[output_name]
        assert 'elasticity' in result.sensitivities[output_name]
        assert 'std' in result.sensitivities[output_name]


def test_morris_workflow():
    """
    Integration test for complete Morris sensitivity analysis workflow.

    This test verifies the end-to-end workflow:
    1. Create parameter ranges
    2. Initialize Morris analyzer
    3. Run analysis
    4. Verify results structure and content
    """
    # Step 1: Define parameter ranges
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700),
        ParameterRange('fission_rate', 1.5e20, 2.5e20, nominal_value=2e20)
    ]

    # Step 2: Create analyzer with minimal trajectories for testing
    analyzer = MorrisAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=3600000.0,  # ~41 days for faster testing
        t_eval_points=50,
        num_trajectories=3,  # Minimal for testing
        num_levels=5
    )

    # Step 3: Run Morris analysis
    results = analyzer.run_morris_analysis(
        n_trajectories=3,
        verbose=False
    )

    # Step 4: Verify results structure
    assert isinstance(results, MorrisResult)
    assert len(results.parameter_names) == 2
    assert results.n_trajectories == 3

    # Verify mu, mu_star, and sigma arrays
    assert len(results.mu) == 2
    assert len(results.mu_star) == 2
    assert len(results.sigma) == 2

    # Verify all values are non-negative for mu_star and sigma
    assert np.all(results.mu_star >= 0)
    assert np.all(results.sigma >= 0)

    # Verify elementary effects
    assert 'swelling' in results.elementary_effects
    ee = results.elementary_effects['swelling']
    assert ee.shape[0] == 3  # n_trajectories
    assert ee.shape[1] == 2  # n_parameters

    # Verify output names
    assert 'swelling' in results.output_names

    # Verify ranking functionality
    ranking = results.get_ranking('swelling')
    assert len(ranking) == 2
    assert all(isinstance(name, str) for name, _ in ranking)
    assert all(isinstance(val, (int, float)) for _, val in ranking)


def test_sobol_workflow():
    """
    Integration test for complete Sobol sensitivity analysis workflow.

    This test verifies the end-to-end workflow:
    1. Create parameter ranges
    2. Initialize Sobol analyzer
    3. Run analysis
    4. Verify results structure and content
    """
    # Step 1: Define parameter ranges
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700),
        ParameterRange('fission_rate', 1.5e20, 2.5e20, nominal_value=2e20)
    ]

    # Step 2: Create analyzer with minimal samples for testing
    analyzer = SobolAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=3600000.0,  # ~41 days for faster testing
        t_eval_points=50,
        calc_second_order=False  # Faster without second order
    )

    # Step 3: Run Sobol analysis with minimal samples
    results = analyzer.run_sobol_analysis(
        n_samples=20,  # Minimal for testing (N*(2+p) = 20*4 = 80 model runs)
        verbose=False
    )

    # Step 4: Verify results structure
    assert isinstance(results, SobolResult)
    assert len(results.parameter_names) == 2
    assert results.n_samples == 20

    # Verify S1 and ST indices
    assert results.S1.shape == (2, 1)  # (n_parameters, n_outputs)
    assert results.ST.shape == (2, 1)

    # Verify indices are in valid range [0, 1]
    assert np.all(results.S1 >= 0)
    assert np.all(results.S1 <= 1)
    assert np.all(results.ST >= 0)
    assert np.all(results.ST <= 1)

    # Verify ST >= S1 (total order should be >= first order)
    assert np.all(results.ST >= results.S1 - 1e-10)  # Allow small numerical errors

    # Verify output names
    assert 'swelling' in results.output_names

    # Verify ranking functionality
    ranking = results.get_ranking('swelling', order='ST')
    assert len(ranking) == 2
    assert all(isinstance(name, str) for name, _ in ranking)
    assert all(isinstance(val, (int, float)) for _, val in ranking)


def test_oat_workflow_with_summary():
    """
    Integration test for OAT workflow with summary generation.
    """
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700),
        ParameterRange('dislocation_density', 5e13, 9e13, nominal_value=7e13)
    ]

    analyzer = OATAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=3600000.0,
        t_eval_points=50
    )

    results = analyzer.run_oat_analysis(
        percent_variations=[-10, 10],
        verbose=False
    )

    # Generate summary
    summary = analyzer.summary(results)

    # Verify summary structure
    assert 'n_parameters_analyzed' in summary
    assert summary['n_parameters_analyzed'] == 2
    assert 'parameter_ranking' in summary
    assert len(summary['parameter_ranking']) == 2

    # Verify ranking is a list of tuples
    assert all(isinstance(name, str) for name, _ in summary['parameter_ranking'])
    assert all(isinstance(val, (int, float)) for _, val in summary['parameter_ranking'])


def test_morris_workflow_with_summary():
    """
    Integration test for Morris workflow with summary generation.
    """
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700)
    ]

    analyzer = MorrisAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=3600000.0,
        t_eval_points=50
    )

    results = analyzer.run_morris_analysis(
        n_trajectories=3,
        verbose=False
    )

    # Generate summary
    summary = analyzer.summary(results)

    # Verify summary structure
    assert 'n_trajectories' in summary
    assert 'n_parameters_analyzed' in summary
    assert 'parameter_ranking' in summary


def test_sobol_workflow_with_summary():
    """
    Integration test for Sobol workflow with summary generation.
    """
    param_ranges = [
        ParameterRange('temperature', 650, 750, nominal_value=700)
    ]

    analyzer = SobolAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=3600000.0,
        t_eval_points=50,
        calc_second_order=False
    )

    results = analyzer.run_sobol_analysis(
        n_samples=20,
        verbose=False
    )

    # Generate summary
    summary = analyzer.summary(results)

    # Verify summary structure
    assert 'n_samples' in summary
    assert 'n_parameters_analyzed' in summary
    assert 'parameter_ranking' in summary


# =============================================================================
# Integration/Import Tests
# =============================================================================

def test_import_sensitivity_analyzer():
    """Test that SensitivityAnalyzer can be imported"""
    from gas_swelling.analysis.sensitivity import SensitivityAnalyzer
    assert SensitivityAnalyzer is not None


def test_import_oat_analyzer():
    """Test that OATAnalyzer can be imported"""
    from gas_swelling.analysis.sensitivity import OATAnalyzer
    assert OATAnalyzer is not None


def test_import_morris_analyzer():
    """Test that MorrisAnalyzer can be imported"""
    from gas_swelling.analysis.sensitivity import MorrisAnalyzer
    assert MorrisAnalyzer is not None


def test_import_sobol_analyzer():
    """Test that SobolAnalyzer can be imported"""
    from gas_swelling.analysis.sensitivity import SobolAnalyzer
    assert SobolAnalyzer is not None


def test_import_all_classes():
    """Test that all sensitivity classes can be imported"""
    from gas_swelling.analysis.sensitivity import (
        ParameterRange,
        SensitivityAnalyzer,
        OATAnalyzer,
        OATResult,
        MorrisAnalyzer,
        MorrisResult,
        SobolAnalyzer,
        SobolResult
    )
    assert ParameterRange is not None
    assert SensitivityAnalyzer is not None
    assert OATAnalyzer is not None
    assert OATResult is not None
    assert MorrisAnalyzer is not None
    assert MorrisResult is not None
    assert SobolAnalyzer is not None
    assert SobolResult is not None
