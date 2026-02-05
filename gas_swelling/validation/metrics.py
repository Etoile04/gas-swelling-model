"""
Validation metrics for comparing model predictions with experimental data.

This module provides functions for calculating various error metrics
including RMSE, R², max error, and MAE for model validation.
"""

import numpy as np
from typing import Union


def calculate_rmse(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list]
) -> float:
    """计算均方根误差 (Root Mean Square Error)

    均方根误差衡量预测值与真实值之间的偏差程度。
    公式: RMSE = √(Σ(y_true - y_pred)² / n)

    Parameters
    ----------
    y_true : np.ndarray or list
        真实值数组 (实验数据)
    y_pred : np.ndarray or list
        预测值数组 (模型输出)

    Returns
    -------
    float
        均方根误差

    Raises
    ------
    ValueError
        如果数组长度不匹配或为空

    Examples
    --------
    >>> import numpy as np
    >>> y_true = np.array([1.0, 2.0, 3.0])
    >>> y_pred = np.array([1.1, 2.1, 3.1])
    >>> calculate_rmse(y_true, y_pred)
    0.1
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true has {len(y_true)} elements, y_pred has {len(y_pred)} elements")
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    squared_errors = (y_true - y_pred) ** 2
    mse = np.mean(squared_errors)
    rmse = np.sqrt(mse)

    return float(rmse)


def calculate_mae(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list]
) -> float:
    """计算平均绝对误差 (Mean Absolute Error)

    平均绝对误差衡量预测值与真实值之间的平均绝对偏差。
    公式: MAE = Σ|y_true - y_pred| / n

    Parameters
    ----------
    y_true : np.ndarray or list
        真实值数组 (实验数据)
    y_pred : np.ndarray or list
        预测值数组 (模型输出)

    Returns
    -------
    float
        平均绝对误差

    Raises
    ------
    ValueError
        如果数组长度不匹配或为空

    Examples
    --------
    >>> import numpy as np
    >>> y_true = np.array([1.0, 2.0, 3.0])
    >>> y_pred = np.array([1.1, 2.1, 3.1])
    >>> calculate_mae(y_true, y_pred)
    0.1
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true has {len(y_true)} elements, y_pred has {len(y_pred)} elements")
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    absolute_errors = np.abs(y_true - y_pred)
    mae = np.mean(absolute_errors)

    return float(mae)


def calculate_max_error(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list]
) -> float:
    """计算最大绝对误差 (Maximum Absolute Error)

    最大绝对误差衡量预测值与真实值之间的最大偏差。
    公式: Max Error = max|y_true - y_pred|

    Parameters
    ----------
    y_true : np.ndarray or list
        真实值数组 (实验数据)
    y_pred : np.ndarray or list
        预测值数组 (模型输出)

    Returns
    -------
    float
        最大绝对误差

    Raises
    ------
    ValueError
        如果数组长度不匹配或为空

    Examples
    --------
    >>> import numpy as np
    >>> y_true = np.array([1.0, 2.0, 3.0])
    >>> y_pred = np.array([1.1, 2.1, 3.1])
    >>> calculate_max_error(y_true, y_pred)
    0.1
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true has {len(y_true)} elements, y_pred has {len(y_pred)} elements")
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    absolute_errors = np.abs(y_true - y_pred)
    max_error = np.max(absolute_errors)

    return float(max_error)


def calculate_r2(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list]
) -> float:
    """计算决定系数 (R², Coefficient of Determination)

    决定系数衡量模型对观测数据的拟合程度。
    公式: R² = 1 - (SS_res / SS_tot)
    其中 SS_res = Σ(y_true - y_pred)² (残差平方和)
         SS_tot = Σ(y_true - ȳ)² (总平方和)

    Parameters
    ----------
    y_true : np.ndarray or list
        真实值数组 (实验数据)
    y_pred : np.ndarray or list
        预测值数组 (模型输出)

    Returns
    -------
    float
        决定系数 (R²), 范围通常在[0, 1],越接近1表示拟合越好

    Raises
    ------
    ValueError
        如果数组长度不匹配、为空或真实值方差为零

    Examples
    --------
    >>> import numpy as np
    >>> y_true = np.array([1.0, 2.0, 3.0])
    >>> y_pred = np.array([1.1, 2.1, 3.1])
    >>> round(calculate_r2(y_true, y_pred), 4)
    0.985
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true has {len(y_true)} elements, y_pred has {len(y_pred)} elements")
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    # Calculate residual sum of squares (SS_res)
    ss_res = np.sum((y_true - y_pred) ** 2)

    # Calculate total sum of squares (SS_tot)
    y_mean = np.mean(y_true)
    ss_tot = np.sum((y_true - y_mean) ** 2)

    # Check for zero variance in y_true
    if ss_tot == 0:
        raise ValueError("Cannot calculate R² when y_true has zero variance (all values are identical)")

    # Calculate R²
    r2 = 1 - (ss_res / ss_tot)

    return float(r2)
