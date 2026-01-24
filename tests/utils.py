"""
Test utilities for numpy array comparisons and floating point assertions

This module provides enhanced assertion functions for comparing numpy arrays
and floating point values with informative error messages.
"""

import numpy as np
from typing import Union, Sequence, Optional


def assert_allclose(
    actual: Union[np.ndarray, Sequence, float],
    desired: Union[np.ndarray, Sequence, float],
    rtol: float = 1e-7,
    atol: float = 0.0,
    equal_nan: bool = False,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that two arrays are element-wise equal within a tolerance.

    Enhanced version of numpy.allclose with detailed error messages.

    Parameters
    ----------
    actual : array_like
        Array obtained (computed values).
    desired : array_like
        Array desired (expected values).
    rtol : float, optional
        Relative tolerance (default: 1e-7).
    atol : float, optional
        Absolute tolerance (default: 0.0).
    equal_nan : bool, optional
        If True, consider NaN values as equal (default: False).
    err_msg : str, optional
        Custom error message to display on failure.

    Raises
    ------
    AssertionError
        If arrays are not element-wise equal within tolerance.

    Examples
    --------
    >>> assert_allclose([1.0, 2.0], [1.0, 2.0000001])
    >>> assert_allclose(np.array([1, 2]), np.array([1, 2]))
    """
    actual_array = np.asarray(actual)
    desired_array = np.asarray(desired)

    # Check if shapes match
    if actual_array.shape != desired_array.shape:
        raise AssertionError(
            f"{err_msg or 'Array shapes do not match'}\n"
            f"  Actual shape: {actual_array.shape}\n"
            f"  Desired shape: {desired_array.shape}"
        )

    # Use numpy's allclose for comparison
    if not np.allclose(actual_array, desired_array, rtol=rtol, atol=atol, equal_nan=equal_nan):
        # Find elements that don't match
        if not equal_nan:
            mismatch_mask = ~np.isclose(actual_array, desired_array, rtol=rtol, atol=atol, equal_nan=equal_nan)
        else:
            mismatch_mask = ~(np.isclose(actual_array, desired_array, rtol=rtol, atol=atol, equal_nan=False) |
                            (np.isnan(actual_array) & np.isnan(desired_array)))

        num_mismatches = np.sum(mismatch_mask)
        total_elements = actual_array.size

        # Get worst offenders
        if num_mismatches > 0:
            actual_flat = actual_array.flatten()
            desired_flat = desired_array.flatten()
            mismatch_flat = mismatch_mask.flatten()

            # Calculate relative errors where desired is not zero
            with np.errstate(divide='ignore', invalid='ignore'):
                rel_errors = np.abs((actual_flat - desired_flat) / desired_flat)
                rel_errors[~np.isfinite(rel_errors)] = np.inf

            # Show top 5 mismatches
            worst_indices = np.where(mismatch_flat)[0]
            if len(worst_indices) > 0:
                worst_idx = worst_indices[np.argmax(rel_errors[worst_indices])]
                worst_rel_error = rel_errors[worst_idx]
                worst_abs_error = np.abs(actual_flat[worst_idx] - desired_flat[worst_idx])

        error_msg = err_msg or "Arrays are not element-wise equal within tolerance"
        raise AssertionError(
            f"{error_msg}\n"
            f"  Mismatches: {num_mismatches}/{total_elements} elements\n"
            f"  Relative tolerance (rtol): {rtol}\n"
            f"  Absolute tolerance (atol): {atol}\n"
            f"  Worst relative error: {worst_rel_error:.2e}\n"
            f"  Worst absolute error: {worst_abs_error:.2e}\n"
            f"  Example mismatch: actual={actual_flat[worst_idx]:.6e}, "
            f"desired={desired_flat[worst_idx]:.6e}"
        )


def assert_relative_close(
    actual: Union[np.ndarray, Sequence, float],
    desired: Union[np.ndarray, Sequence, float],
    rel_tol: float = 1e-7,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that values are close within a relative tolerance.

    Parameters
    ----------
    actual : array_like
        Computed values.
    desired : array_like
        Expected values.
    rel_tol : float, optional
        Relative tolerance (default: 1e-7).
    err_msg : str, optional
        Custom error message.

    Raises
    ------
    AssertionError
        If values are not close within relative tolerance.
    """
    actual_array = np.asarray(actual)
    desired_array = np.asarray(desired)

    if actual_array.shape != desired_array.shape:
        raise AssertionError(
            f"{err_msg or 'Array shapes do not match'}\n"
            f"  Actual shape: {actual_array.shape}\n"
            f"  Desired shape: {desired_array.shape}"
        )

    with np.errstate(divide='ignore', invalid='ignore'):
        rel_diff = np.abs((actual_array - desired_array) / desired_array)

    if not np.all(rel_diff <= rel_tol):
        max_diff = np.max(rel_diff)
        raise AssertionError(
            f"{err_msg or 'Values are not close within relative tolerance'}\n"
            f"  Maximum relative difference: {max_diff:.2e}\n"
            f"  Required tolerance: {rel_tol:.2e}"
        )


def assert_absolute_close(
    actual: Union[np.ndarray, Sequence, float],
    desired: Union[np.ndarray, Sequence, float],
    abs_tol: float = 1e-7,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that values are close within an absolute tolerance.

    Parameters
    ----------
    actual : array_like
        Computed values.
    desired : array_like
        Expected values.
    abs_tol : float, optional
        Absolute tolerance (default: 1e-7).
    err_msg : str, optional
        Custom error message.

    Raises
    ------
    AssertionError
        If values are not close within absolute tolerance.
    """
    actual_array = np.asarray(actual)
    desired_array = np.asarray(desired)

    if actual_array.shape != desired_array.shape:
        raise AssertionError(
            f"{err_msg or 'Array shapes do not match'}\n"
            f"  Actual shape: {actual_array.shape}\n"
            f"  Desired shape: {desired_array.shape}"
        )

    abs_diff = np.abs(actual_array - desired_array)

    if not np.all(abs_diff <= abs_tol):
        max_diff = np.max(abs_diff)
        raise AssertionError(
            f"{err_msg or 'Values are not close within absolute tolerance'}\n"
            f"  Maximum absolute difference: {max_diff:.2e}\n"
            f"  Required tolerance: {abs_tol:.2e}"
        )


def assert_array_shape(
    array: Union[np.ndarray, Sequence],
    expected_shape: tuple,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that an array has the expected shape.

    Parameters
    ----------
    array : array_like
        Array to check.
    expected_shape : tuple
        Expected shape.
    err_msg : str, optional
        Custom error message.

    Raises
    ------
    AssertionError
        If array shape does not match expected shape.
    """
    actual_array = np.asarray(array)
    actual_shape = actual_array.shape

    if actual_shape != expected_shape:
        raise AssertionError(
            f"{err_msg or 'Array shape does not match expected shape'}\n"
            f"  Actual shape: {actual_shape}\n"
            f"  Expected shape: {expected_shape}"
        )


def assert_array_dimension(
    array: Union[np.ndarray, Sequence],
    expected_ndim: int,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that an array has the expected number of dimensions.

    Parameters
    ----------
    array : array_like
        Array to check.
    expected_ndim : int
        Expected number of dimensions.
    err_msg : str, optional
        Custom error message.

    Raises
    ------
    AssertionError
        If array dimension does not match expected dimension.
    """
    actual_array = np.asarray(array)
    actual_ndim = actual_array.ndim

    if actual_ndim != expected_ndim:
        raise AssertionError(
            f"{err_msg or 'Array dimension does not match expected dimension'}\n"
            f"  Actual dimension: {actual_ndim}\n"
            f"  Expected dimension: {expected_ndim}"
        )


def assert_array_monotonic(
    array: Union[np.ndarray, Sequence],
    increasing: bool = True,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that an array is monotonically increasing or decreasing.

    Parameters
    ----------
    array : array_like
        Array to check.
    increasing : bool, optional
        If True, check for monotonically increasing (default).
        If False, check for monotonically decreasing.
    err_msg : str, optional
        Custom error message.

    Raises
    ------
    AssertionError
        If array is not monotonic as specified.
    """
    actual_array = np.asarray(array)

    if increasing:
        if not np.all(np.diff(actual_array) >= 0):
            violations = np.sum(np.diff(actual_array) < 0)
            raise AssertionError(
                f"{err_msg or 'Array is not monotonically increasing'}\n"
                f"  Found {violations} decreasing steps"
            )
    else:
        if not np.all(np.diff(actual_array) <= 0):
            violations = np.sum(np.diff(actual_array) > 0)
            raise AssertionError(
                f"{err_msg or 'Array is not monotonically decreasing'}\n"
                f"  Found {violations} increasing steps"
            )
