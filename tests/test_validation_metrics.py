"""
Test validation metrics calculations
"""

import pytest
import numpy as np
from gas_swelling.validation.metrics import (
    calculate_rmse,
    calculate_mae,
    calculate_max_error,
    calculate_r2
)


def test_calculate_rmse_basic():
    """Test basic RMSE calculation"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 3.1])
    result = calculate_rmse(y_true, y_pred)
    assert result == pytest.approx(0.1)


def test_calculate_rmse_with_lists():
    """Test RMSE calculation with list inputs"""
    y_true = [1.0, 2.0, 3.0]
    y_pred = [1.1, 2.1, 3.1]
    result = calculate_rmse(y_true, y_pred)
    assert result == pytest.approx(0.1)


def test_calculate_rmse_perfect_fit():
    """Test RMSE with perfect prediction"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    result = calculate_rmse(y_true, y_pred)
    assert result == pytest.approx(0.0)


def test_calculate_rmse_larger_errors():
    """Test RMSE with larger errors"""
    y_true = np.array([0.0, 0.0, 0.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    # RMSE = sqrt((1^2 + 2^2 + 3^2) / 3) = sqrt(14/3) ≈ 2.16
    result = calculate_rmse(y_true, y_pred)
    assert result == pytest.approx(2.160246899469287)


def test_calculate_rmse_length_mismatch():
    """Test that mismatched array lengths raise ValueError"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1])
    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_rmse(y_true, y_pred)


def test_calculate_rmse_empty_arrays():
    """Test that empty arrays raise ValueError"""
    y_true = np.array([])
    y_pred = np.array([])
    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        calculate_rmse(y_true, y_pred)


def test_calculate_mae_basic():
    """Test basic MAE calculation"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 3.1])
    result = calculate_mae(y_true, y_pred)
    assert result == pytest.approx(0.1)


def test_calculate_mae_with_lists():
    """Test MAE calculation with list inputs"""
    y_true = [1.0, 2.0, 3.0]
    y_pred = [1.1, 2.1, 3.1]
    result = calculate_mae(y_true, y_pred)
    assert result == pytest.approx(0.1)


def test_calculate_mae_perfect_fit():
    """Test MAE with perfect prediction"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    result = calculate_mae(y_true, y_pred)
    assert result == pytest.approx(0.0)


def test_calculate_mae_larger_errors():
    """Test MAE with larger errors"""
    y_true = np.array([0.0, 0.0, 0.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    # MAE = (1 + 2 + 3) / 3 = 2.0
    result = calculate_mae(y_true, y_pred)
    assert result == pytest.approx(2.0)


def test_calculate_mae_asymmetric_errors():
    """Test MAE with asymmetric errors"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 1.5, 2.5])
    # MAE = (0.5 + 0.5 + 0.5) / 3 = 0.5
    result = calculate_mae(y_true, y_pred)
    assert result == pytest.approx(0.5)


def test_calculate_mae_length_mismatch():
    """Test that mismatched array lengths raise ValueError"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1])
    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_mae(y_true, y_pred)


def test_calculate_mae_empty_arrays():
    """Test that empty arrays raise ValueError"""
    y_true = np.array([])
    y_pred = np.array([])
    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        calculate_mae(y_true, y_pred)


def test_calculate_max_error_basic():
    """Test basic max error calculation"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 3.1])
    result = calculate_max_error(y_true, y_pred)
    assert result == pytest.approx(0.1)


def test_calculate_max_error_with_lists():
    """Test max error calculation with list inputs"""
    y_true = [1.0, 2.0, 3.0]
    y_pred = [1.1, 2.1, 3.1]
    result = calculate_max_error(y_true, y_pred)
    assert result == pytest.approx(0.1)


def test_calculate_max_error_perfect_fit():
    """Test max error with perfect prediction"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    result = calculate_max_error(y_true, y_pred)
    assert result == pytest.approx(0.0)


def test_calculate_max_error_varying_errors():
    """Test max error with varying error magnitudes"""
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 1.5, 3.8, 3.5])
    # Errors: 0.1, 0.5, 0.8, 0.5 -> max = 0.8
    result = calculate_max_error(y_true, y_pred)
    assert result == pytest.approx(0.8)


def test_calculate_max_error_negative_prediction():
    """Test max error with negative predictions"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([-1.0, 2.0, 3.0])
    # Errors: 2.0, 0.0, 0.0 -> max = 2.0
    result = calculate_max_error(y_true, y_pred)
    assert result == pytest.approx(2.0)


def test_calculate_max_error_length_mismatch():
    """Test that mismatched array lengths raise ValueError"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1])
    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_max_error(y_true, y_pred)


def test_calculate_max_error_empty_arrays():
    """Test that empty arrays raise ValueError"""
    y_true = np.array([])
    y_pred = np.array([])
    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        calculate_max_error(y_true, y_pred)


def test_calculate_r2_basic():
    """Test basic R² calculation"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 3.1])
    result = calculate_r2(y_true, y_pred)
    assert result == pytest.approx(0.985, rel=1e-3)


def test_calculate_r2_with_lists():
    """Test R² calculation with list inputs"""
    y_true = [1.0, 2.0, 3.0]
    y_pred = [1.1, 2.1, 3.1]
    result = calculate_r2(y_true, y_pred)
    assert result == pytest.approx(0.985, rel=1e-3)


def test_calculate_r2_perfect_fit():
    """Test R² with perfect prediction"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    result = calculate_r2(y_true, y_pred)
    assert result == pytest.approx(1.0)


def test_calculate_r2_poor_fit():
    """Test R² with poor prediction"""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    # This should give a negative R² since the prediction is worse than using the mean
    result = calculate_r2(y_true, y_pred)
    assert result < 0


def test_calculate_r2_single_point():
    """Test R² with a single data point raises error due to zero variance"""
    y_true = np.array([1.0])
    y_pred = np.array([1.0])
    # A single data point has zero variance, so R² cannot be calculated
    with pytest.raises(ValueError, match="zero variance"):
        calculate_r2(y_true, y_pred)


def test_calculate_r2_length_mismatch():
    """Test that mismatched array lengths raise ValueError"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1])
    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_r2(y_true, y_pred)


def test_calculate_r2_empty_arrays():
    """Test that empty arrays raise ValueError"""
    y_true = np.array([])
    y_pred = np.array([])
    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        calculate_r2(y_true, y_pred)


def test_calculate_r2_zero_variance():
    """Test that zero variance in y_true raises ValueError"""
    y_true = np.array([1.0, 1.0, 1.0])
    y_pred = np.array([1.1, 1.1, 1.1])
    with pytest.raises(ValueError, match="zero variance"):
        calculate_r2(y_true, y_pred)


def test_all_metrics_consistency():
    """Test that all metrics work with the same data"""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.2, 2.1, 2.9, 4.3, 4.8])

    rmse = calculate_rmse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    max_err = calculate_max_error(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)

    # RMSE should be >= MAE (by mathematical property)
    assert rmse >= mae

    # Max error should be >= MAE (by definition)
    assert max_err >= mae

    # R² should be between 0 and 1 for decent fit
    assert 0 <= r2 <= 1

    # All metrics should be non-negative
    assert rmse >= 0
    assert mae >= 0
    assert max_err >= 0


def test_all_metrics_with_numpy_arrays():
    """Test that all metrics handle numpy array inputs correctly"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 3.1])

    rmse = calculate_rmse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    max_err = calculate_max_error(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)

    # All should return floats
    assert isinstance(rmse, float)
    assert isinstance(mae, float)
    assert isinstance(max_err, float)
    assert isinstance(r2, float)


def test_all_metrics_with_python_lists():
    """Test that all metrics handle Python list inputs correctly"""
    y_true = [1.0, 2.0, 3.0]
    y_pred = [1.1, 2.1, 3.1]

    rmse = calculate_rmse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    max_err = calculate_max_error(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)

    # All should return floats
    assert isinstance(rmse, float)
    assert isinstance(mae, float)
    assert isinstance(max_err, float)
    assert isinstance(r2, float)


def test_import_validation_metrics_module():
    """Test that all validation metrics functions can be imported"""
    from gas_swelling.validation.metrics import (
        calculate_rmse,
        calculate_mae,
        calculate_max_error,
        calculate_r2
    )
    assert calculate_rmse is not None
    assert calculate_mae is not None
    assert calculate_max_error is not None
    assert calculate_r2 is not None
