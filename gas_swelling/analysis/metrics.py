"""
Sensitivity metrics for parameter sensitivity analysis.

This module provides functions for calculating various sensitivity metrics
including normalized sensitivity (elasticity), absolute sensitivity, and
relative sensitivity measures.
"""

import numpy as np
from typing import Union, Optional


def calculate_normalized_sensitivity(
    y_new: float,
    y_base: float,
    delta_x_ratio: float
) -> float:
    """计算归一化敏感度(弹性系数)

    归一化敏感度(弹性系数)表示输出相对变化与输入相对变化的比值。
    公式: S = (Δy/y₀) / (Δx/x₀)

    Parameters
    ----------
    y_new : float
        参数变化后的输出值
    y_base : float
        基准输出值(参数未变化时的输出)
    delta_x_ratio : float
        参数的相对变化量 (Δx/x₀)

    Returns
    -------
    float
        归一化敏感度(弹性系数)

    Examples
    --------
    >>> calculate_normalized_sensitivity(1.5, 1.0, 0.1)
    5.0
    """
    if y_base == 0:
        raise ValueError("y_base cannot be zero for normalized sensitivity calculation")
    if delta_x_ratio == 0:
        raise ValueError("delta_x_ratio cannot be zero")

    relative_change_y = (y_new - y_base) / y_base
    normalized_sensitivity = relative_change_y / delta_x_ratio

    return normalized_sensitivity


def calculate_elasticity(
    y_new: float,
    y_base: float,
    x_new: float,
    x_base: float
) -> float:
    """计算弹性系数(另一种形式)

    使用参数的绝对值计算弹性系数。
    公式: ε = (Δy/y₀) / (Δx/x₀)

    Parameters
    ----------
    y_new : float
        参数变化后的输出值
    y_base : float
        基准输出值
    x_new : float
        新参数值
    x_base : float
        基准参数值

    Returns
    -------
    float
        弹性系数

    Examples
    --------
    >>> calculate_elasticity(1.5, 1.0, 1.1, 1.0)
    5.0
    """
    if y_base == 0:
        raise ValueError("y_base cannot be zero for elasticity calculation")
    if x_base == 0:
        raise ValueError("x_base cannot be zero for elasticity calculation")

    relative_change_y = (y_new - y_base) / y_base
    relative_change_x = (x_new - x_base) / x_base

    if relative_change_x == 0:
        raise ValueError("Relative change in x cannot be zero")

    elasticity = relative_change_y / relative_change_x
    return elasticity


def calculate_absolute_sensitivity(
    y_new: float,
    y_base: float,
    x_new: float,
    x_base: float
) -> float:
    """计算绝对敏感度(偏导数近似)

    绝对敏感度表示单位参数变化引起的输出变化。
    公式: S_abs = Δy / Δx

    Parameters
    ----------
    y_new : float
        参数变化后的输出值
    y_base : float
        基准输出值
    x_new : float
        新参数值
    x_base : float
        基准参数值

    Returns
    -------
    float
        绝对敏感度

    Examples
    --------
    >>> calculate_absolute_sensitivity(1.5, 1.0, 1.1, 1.0)
    5.0
    """
    delta_y = y_new - y_base
    delta_x = x_new - x_base

    if delta_x == 0:
        raise ValueError("x_new and x_base must be different")

    absolute_sensitivity = delta_y / delta_x
    return absolute_sensitivity


def calculate_relative_sensitivity(
    y_new: float,
    y_base: float,
    x_new: float,
    x_base: float
) -> float:
    """计算相对敏感度(百分比变化)

    相对敏感度表示输出百分比变化与参数百分比变化的比值。
    公式: S_rel = (Δy/y₀) / (Δx/x₀) × 100%

    Parameters
    ----------
    y_new : float
        参数变化后的输出值
    y_base : float
        基准输出值
    x_new : float
        新参数值
    x_base : float
        基准参数值

    Returns
    -------
    float
        相对敏感度(百分比形式)

    Examples
    --------
    >>> calculate_relative_sensitivity(1.5, 1.0, 1.1, 1.0)
    500.0
    """
    if y_base == 0:
        raise ValueError("y_base cannot be zero for relative sensitivity calculation")
    if x_base == 0:
        raise ValueError("x_base cannot be zero for relative sensitivity calculation")

    elasticity = calculate_elasticity(y_new, y_base, x_new, x_base)
    relative_sensitivity = elasticity * 100.0

    return relative_sensitivity


def calculate_sensitivity_coefficient(
    y_values: np.ndarray,
    x_values: np.ndarray,
    method: str = 'linear'
) -> float:
    """计算敏感度系数(通过拟合)

    通过拟合x-y关系计算敏感度系数。

    Parameters
    ----------
    y_values : np.ndarray
        输出值数组
    x_values : np.ndarray
        参数值数组
    method : str, optional
        拟合方法, 默认为'linear', 可选'log'用于对数拟合

    Returns
    -------
    float
        敏感度系数(斜率或弹性)

    Raises
    ------
    ValueError
        如果数组长度不匹配或method无效

    Examples
    --------
    >>> import numpy as np
    >>> x = np.array([1.0, 1.1, 1.2])
    >>> y = np.array([1.0, 1.5, 2.0])
    >>> calculate_sensitivity_coefficient(y, x)
    5.0
    """
    if len(y_values) != len(x_values):
        raise ValueError("y_values and x_values must have the same length")
    if len(y_values) < 2:
        raise ValueError("At least 2 data points required")

    if method == 'linear':
        # 线性拟合: y = a + b*x, 返回斜率b
        coefficients = np.polyfit(x_values, y_values, 1)
        return float(coefficients[0])
    elif method == 'log':
        # 对数拟合: log(y) = a + b*log(x), 返回弹性b
        if np.any(y_values <= 0) or np.any(x_values <= 0):
            raise ValueError("All values must be positive for log-log fit")
        log_x = np.log(x_values)
        log_y = np.log(y_values)
        coefficients = np.polyfit(log_x, log_y, 1)
        return float(coefficients[0])
    else:
        raise ValueError(f"Unknown method: {method}. Use 'linear' or 'log'")


def calculate_sensitivity_metrics(
    y_new: Union[float, np.ndarray],
    y_base: Union[float, np.ndarray],
    x_new: Union[float, np.ndarray],
    x_base: Union[float, np.ndarray]
) -> dict:
    """计算完整的敏感度指标集合

    一次性计算多个敏感度指标,便于比较分析。

    Parameters
    ----------
    y_new : float or np.ndarray
        参数变化后的输出值
    y_base : float or np.ndarray
        基准输出值
    x_new : float or np.ndarray
        新参数值
    x_base : float or np.ndarray
        基准参数值

    Returns
    -------
    dict
        包含以下敏感度指标的字典:
        - 'normalized_sensitivity': 归一化敏感度(弹性系数)
        - 'absolute_sensitivity': 绝对敏感度
        - 'relative_sensitivity_percent': 相对敏感度(百分比)
        - 'delta_y_percent': 输出变化百分比
        - 'delta_x_percent': 参数变化百分比

    Examples
    --------
    >>> metrics = calculate_sensitivity_metrics(1.5, 1.0, 1.1, 1.0)
    >>> print(f"{metrics['normalized_sensitivity']:.2f}")
    5.00
    """
    # 处理数组输入
    if isinstance(y_new, np.ndarray) or isinstance(y_base, np.ndarray):
        y_new = np.asarray(y_new)
        y_base = np.asarray(y_base)
        x_new = np.asarray(x_new)
        x_base = np.asarray(x_base)

    # 计算各项指标
    delta_y = y_new - y_base
    delta_x = x_new - x_base

    delta_y_percent = (delta_y / y_base) * 100.0 if np.isscalar(y_base) else (delta_y / y_base) * 100.0
    delta_x_percent = (delta_x / x_base) * 100.0 if np.isscalar(x_base) else (delta_x / x_base) * 100.0

    normalized_sens = calculate_normalized_sensitivity(
        float(y_new) if np.isscalar(y_new) else float(y_new.flat[0]),
        float(y_base) if np.isscalar(y_base) else float(y_base.flat[0]),
        float(delta_x / x_base) if np.isscalar(x_base) else float((delta_x / x_base).flat[0])
    )

    absolute_sens = calculate_absolute_sensitivity(
        float(y_new) if np.isscalar(y_new) else float(y_new.flat[0]),
        float(y_base) if np.isscalar(y_base) else float(y_base.flat[0]),
        float(x_new) if np.isscalar(x_new) else float(x_new.flat[0]),
        float(x_base) if np.isscalar(x_base) else float(x_base.flat[0])
    )

    relative_sens = calculate_relative_sensitivity(
        float(y_new) if np.isscalar(y_new) else float(y_new.flat[0]),
        float(y_base) if np.isscalar(y_base) else float(y_base.flat[0]),
        float(x_new) if np.isscalar(x_new) else float(x_new.flat[0]),
        float(x_base) if np.isscalar(x_base) else float(x_base.flat[0])
    )

    return {
        'normalized_sensitivity': normalized_sens,
        'absolute_sensitivity': absolute_sens,
        'relative_sensitivity_percent': relative_sens,
        'delta_y_percent': delta_y_percent,
        'delta_x_percent': delta_x_percent
    }
