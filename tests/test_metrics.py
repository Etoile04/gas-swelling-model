"""
Test sensitivity metrics calculations
"""

import pytest
import numpy as np
from gas_swelling.analysis.metrics import (
    calculate_normalized_sensitivity,
    calculate_elasticity,
    calculate_absolute_sensitivity,
    calculate_relative_sensitivity,
    calculate_sensitivity_coefficient,
    calculate_sensitivity_metrics
)


def test_calculate_normalized_sensitivity_basic():
    """Test basic normalized sensitivity calculation"""
    # Example from docstring: 50% increase in y from 10% increase in x gives sensitivity of 5
    result = calculate_normalized_sensitivity(1.5, 1.0, 0.1)
    assert result == 5.0


def test_calculate_normalized_sensitivity_negative_change():
    """Test normalized sensitivity with negative parameter change"""
    result = calculate_normalized_sensitivity(0.5, 1.0, -0.2)
    # -50% change in y from -20% change in x = 2.5
    assert result == 2.5


def test_calculate_normalized_sensitivity_zero_y_base():
    """Test that zero y_base raises ValueError"""
    with pytest.raises(ValueError, match="y_base cannot be zero"):
        calculate_normalized_sensitivity(1.5, 0.0, 0.1)


def test_calculate_normalized_sensitivity_zero_delta_x():
    """Test that zero delta_x_ratio raises ValueError"""
    with pytest.raises(ValueError, match="delta_x_ratio cannot be zero"):
        calculate_normalized_sensitivity(1.5, 1.0, 0.0)


def test_calculate_elasticity_basic():
    """Test basic elasticity calculation"""
    result = calculate_elasticity(1.5, 1.0, 1.1, 1.0)
    assert result == pytest.approx(5.0)


def test_calculate_elasticity_different_values():
    """Test elasticity with different parameter values"""
    # y changes by 50% when x changes by 20%
    result = calculate_elasticity(1.5, 1.0, 1.2, 1.0)
    assert result == pytest.approx(2.5)


def test_calculate_elasticity_zero_y_base():
    """Test that zero y_base raises ValueError"""
    with pytest.raises(ValueError, match="y_base cannot be zero"):
        calculate_elasticity(1.5, 0.0, 1.1, 1.0)


def test_calculate_elasticity_zero_x_base():
    """Test that zero x_base raises ValueError"""
    with pytest.raises(ValueError, match="x_base cannot be zero"):
        calculate_elasticity(1.5, 1.0, 1.1, 0.0)


def test_calculate_elasticity_zero_relative_change_x():
    """Test that zero relative change in x raises ValueError"""
    with pytest.raises(ValueError, match="Relative change in x cannot be zero"):
        calculate_elasticity(1.5, 1.0, 1.0, 1.0)


def test_calculate_absolute_sensitivity_basic():
    """Test basic absolute sensitivity calculation"""
    # Delta y = 0.5, Delta x = 0.1, Sensitivity = 5
    result = calculate_absolute_sensitivity(1.5, 1.0, 1.1, 1.0)
    assert result == pytest.approx(5.0)


def test_calculate_absolute_sensitivity_negative():
    """Test absolute sensitivity with negative correlation"""
    result = calculate_absolute_sensitivity(0.5, 1.0, 1.1, 1.0)
    assert result == pytest.approx(-5.0)


def test_calculate_absolute_sensitivity_zero_delta_x():
    """Test that identical x values raise ValueError"""
    with pytest.raises(ValueError, match="x_new and x_base must be different"):
        calculate_absolute_sensitivity(1.5, 1.0, 1.0, 1.0)


def test_calculate_relative_sensitivity_basic():
    """Test basic relative sensitivity calculation"""
    result = calculate_relative_sensitivity(1.5, 1.0, 1.1, 1.0)
    # Should be 5.0 * 100 = 500.0 (percentage form)
    assert result == pytest.approx(500.0)


def test_calculate_relative_sensitivity_zero_y_base():
    """Test that zero y_base raises ValueError"""
    with pytest.raises(ValueError, match="y_base cannot be zero"):
        calculate_relative_sensitivity(1.5, 0.0, 1.1, 1.0)


def test_calculate_relative_sensitivity_zero_x_base():
    """Test that zero x_base raises ValueError"""
    with pytest.raises(ValueError, match="x_base cannot be zero"):
        calculate_relative_sensitivity(1.5, 1.0, 1.1, 0.0)


def test_calculate_sensitivity_coefficient_linear():
    """Test sensitivity coefficient with linear fit"""
    x = np.array([1.0, 1.1, 1.2])
    y = np.array([1.0, 1.5, 2.0])
    result = calculate_sensitivity_coefficient(y, x, method='linear')
    # Linear fit should give slope of 5
    assert abs(result - 5.0) < 0.01


def test_calculate_sensitivity_coefficient_log():
    """Test sensitivity coefficient with log-log fit"""
    x = np.array([1.0, 2.0, 4.0])
    y = np.array([1.0, 4.0, 16.0])
    result = calculate_sensitivity_coefficient(y, x, method='log')
    # Log-log fit for y = x^2 should give exponent of 2
    assert abs(result - 2.0) < 0.01


def test_calculate_sensitivity_coefficient_mismatched_lengths():
    """Test that mismatched array lengths raise ValueError"""
    x = np.array([1.0, 1.1])
    y = np.array([1.0, 1.5, 2.0])
    with pytest.raises(ValueError, match="must have the same length"):
        calculate_sensitivity_coefficient(y, x)


def test_calculate_sensitivity_coefficient_insufficient_points():
    """Test that insufficient data points raise ValueError"""
    x = np.array([1.0])
    y = np.array([1.0])
    with pytest.raises(ValueError, match="At least 2 data points required"):
        calculate_sensitivity_coefficient(y, x)


def test_calculate_sensitivity_coefficient_invalid_method():
    """Test that invalid method raises ValueError"""
    x = np.array([1.0, 1.1])
    y = np.array([1.0, 1.5])
    with pytest.raises(ValueError, match="Unknown method"):
        calculate_sensitivity_coefficient(y, x, method='invalid')


def test_calculate_sensitivity_coefficient_log_negative_values():
    """Test that negative values raise ValueError for log method"""
    x = np.array([1.0, -1.0, 2.0])
    y = np.array([1.0, 1.5, 2.0])
    with pytest.raises(ValueError, match="All values must be positive"):
        calculate_sensitivity_coefficient(y, x, method='log')


def test_calculate_sensitivity_metrics_basic():
    """Test basic sensitivity metrics calculation"""
    metrics = calculate_sensitivity_metrics(1.5, 1.0, 1.1, 1.0)

    assert isinstance(metrics, dict)
    assert 'normalized_sensitivity' in metrics
    assert 'absolute_sensitivity' in metrics
    assert 'relative_sensitivity_percent' in metrics
    assert 'delta_y_percent' in metrics
    assert 'delta_x_percent' in metrics


def test_calculate_sensitivity_metrics_values():
    """Test that sensitivity metrics have correct values"""
    metrics = calculate_sensitivity_metrics(1.5, 1.0, 1.1, 1.0)

    assert metrics['normalized_sensitivity'] == pytest.approx(5.0)
    assert metrics['absolute_sensitivity'] == pytest.approx(5.0)
    assert metrics['relative_sensitivity_percent'] == pytest.approx(500.0)
    assert metrics['delta_y_percent'] == pytest.approx(50.0)
    assert metrics['delta_x_percent'] == pytest.approx(10.0)


def test_calculate_sensitivity_metrics_negative_change():
    """Test sensitivity metrics with negative changes"""
    metrics = calculate_sensitivity_metrics(0.5, 1.0, 0.9, 1.0)

    assert metrics['delta_y_percent'] == pytest.approx(-50.0)
    assert metrics['delta_x_percent'] == pytest.approx(-10.0)


def test_calculate_sensitivity_metrics_with_arrays():
    """Test sensitivity metrics with numpy array inputs"""
    y_new = np.array([1.5, 2.0])
    y_base = np.array([1.0, 1.0])
    x_new = np.array([1.1, 1.2])
    x_base = np.array([1.0, 1.0])

    metrics = calculate_sensitivity_metrics(y_new, y_base, x_new, x_base)

    # Should handle arrays and return scalar metrics
    assert isinstance(metrics['normalized_sensitivity'], float)
    assert isinstance(metrics['absolute_sensitivity'], float)


def test_import_metrics_module():
    """Test that all metrics functions can be imported"""
    from gas_swelling.analysis.metrics import (
        calculate_normalized_sensitivity,
        calculate_elasticity,
        calculate_absolute_sensitivity,
        calculate_relative_sensitivity,
        calculate_sensitivity_coefficient,
        calculate_sensitivity_metrics
    )
    assert calculate_normalized_sensitivity is not None
    assert calculate_elasticity is not None
    assert calculate_absolute_sensitivity is not None
    assert calculate_relative_sensitivity is not None
    assert calculate_sensitivity_coefficient is not None
    assert calculate_sensitivity_metrics is not None
