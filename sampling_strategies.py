#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采样策略模块

提供多种参数采样方法，用于参数扫描和优化研究。

作者: 研究团队
日期: 2025
"""

import numpy as np
import itertools
import logging
from typing import Dict, List, Any, Optional, Union
from scipy.stats import qmc

# 配置日志
logger = logging.getLogger('sampling_strategies')


def grid_sampling(param_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """
    网格采样（笛卡尔积）

    生成所有参数组合的笛卡尔积，用于穷举搜索参数空间。

    参数:
        param_ranges: 参数范围字典
            键: 参数名 (str)
            值: 参数值列表 (list)

            示例:
                {
                    'temperature': [300, 400, 500],
                    'fission_rate': [1e19, 2e19],
                    'surface_energy': [0.5, 0.6, 0.7]
                }

    返回:
        参数组合列表，每个元素是一个参数字典

        示例:
            [
                {'temperature': 300, 'fission_rate': 1e19, 'surface_energy': 0.5},
                {'temperature': 300, 'fission_rate': 1e19, 'surface_energy': 0.6},
                {'temperature': 300, 'fission_rate': 1e19, 'surface_energy': 0.7},
                {'temperature': 300, 'fission_rate': 2e19, 'surface_energy': 0.5},
                ...
            ]

    示例:
        >>> params = grid_sampling({'temperature': [300, 400], 'fission_rate': [1e19, 2e19]})
        >>> print(f"生成的参数组合数量: {len(params)}")
        生成的参数组合数量: 4

        >>> for p in params:
        ...     print(p)
        {'temperature': 300, 'fission_rate': 1e19}
        {'temperature': 300, 'fission_rate': 2e19}
        {'temperature': 400, 'fission_rate': 1e19}
        {'temperature': 400, 'fission_rate': 2e19}
    """
    try:
        # 验证输入
        if not param_ranges:
            logger.warning("参数范围为空，返回空列表")
            return []

        if not isinstance(param_ranges, dict):
            raise TypeError("param_ranges 必须是字典类型")

        # 检查所有参数值是否为列表
        for param_name, param_values in param_ranges.items():
            if not isinstance(param_values, (list, np.ndarray)):
                raise TypeError(f"参数 '{param_name}' 的值必须是列表或numpy数组")

            if len(param_values) == 0:
                logger.warning(f"参数 '{param_name}' 的值列表为空，将其作为单值处理")

        # 获取所有参数名和对应的值列表
        param_names = list(param_ranges.keys())
        param_values_lists = [param_ranges[name] for name in param_names]

        # 计算总组合数
        total_combinations = 1
        for values in param_values_lists:
            total_combinations *= len(values)

        logger.info(f"开始生成网格采样: {len(param_names)}个参数, 总共{total_combinations}种组合")
        logger.info(f"参数: {param_names}")
        logger.info(f"每个参数的取值数量: {[len(v) for v in param_values_lists]}")

        # 生成笛卡尔积
        cartesian_product = itertools.product(*param_values_lists)

        # 构建参数字典列表
        parameter_combinations = []
        for combination in cartesian_product:
            param_dict = {name: value for name, value in zip(param_names, combination)}
            parameter_combinations.append(param_dict)

        logger.info(f"网格采样完成，生成了 {len(parameter_combinations)} 个参数组合")

        return parameter_combinations

    except Exception as e:
        logger.error(f"网格采样过程中出错: {str(e)}")
        raise


def grid_sampling_with_logspace(param_ranges: Dict[str, Union[List[Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    带对数空间的网格采样

    支持在对数空间中均匀采样参数值，适用于跨越多个数量级的参数。

    参数:
        param_ranges: 参数范围字典
            键: 参数名 (str)
            值: 可以是列表或包含对数采样配置的字典

            列表示例: [300, 400, 500]
            字典示例:
                {
                    'type': 'logspace',
                    'start': 1e18,  # 起始值
                    'stop': 1e21,   # 结束值
                    'num': 5        # 采样点数
                }

    返回:
        参数组合列表

    示例:
        >>> param_ranges = {
        ...     'temperature': [300, 400, 500],
        ...     'fission_rate': {'type': 'logspace', 'start': 1e18, 'stop': 1e21, 'num': 4}
        ... }
        >>> params = grid_sampling_with_logspace(param_ranges)
        >>> print(f"生成的参数组合数量: {len(params)}")
        生成的参数组合数量: 12
    """
    try:
        # 处理参数范围，将对数空间配置转换为实际值列表
        processed_ranges = {}

        for param_name, param_config in param_ranges.items():
            if isinstance(param_config, dict) and param_config.get('type') == 'logspace':
                # 对数空间采样
                start = param_config.get('start', 1e18)
                stop = param_config.get('stop', 1e21)
                num = param_config.get('num', 10)

                # 使用对数空间生成采样点
                log_values = np.logspace(np.log10(start), np.log10(stop), num=num)
                processed_ranges[param_name] = log_values

                logger.info(f"参数 '{param_name}' 使用对数空间采样: {num}个点, 范围 [{start:.2e}, {stop:.2e}]")

            elif isinstance(param_config, (list, np.ndarray)):
                # 直接使用提供的列表
                processed_ranges[param_name] = param_config
            else:
                raise ValueError(f"参数 '{param_name}' 的配置格式不正确")

        # 使用标准网格采样
        return grid_sampling(processed_ranges)

    except Exception as e:
        logger.error(f"带对数空间的网格采样出错: {str(e)}")
        raise


def grid_sampling_with_linspace(param_ranges: Dict[str, Union[List[Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    带线性空间的网格采样

    支持在线性空间中均匀采样参数值。

    参数:
        param_ranges: 参数范围字典
            键: 参数名 (str)
            值: 可以是列表或包含线性采样配置的字典

            列表示例: [300, 400, 500]
            字典示例:
                {
                    'type': 'linspace',
                    'start': 300,   # 起始值
                    'stop': 1000,   # 结束值
                    'num': 8        # 采样点数
                }

    返回:
        参数组合列表

    示例:
        >>> param_ranges = {
        ...     'temperature': {'type': 'linspace', 'start': 300, 'stop': 1000, 'num': 8},
        ...     'fission_rate': [1e19, 2e19]
        ... }
        >>> params = grid_sampling_with_linspace(param_ranges)
        >>> print(f"生成的参数组合数量: {len(params)}")
        生成的参数组合数量: 16
    """
    try:
        # 处理参数范围，将线性空间配置转换为实际值列表
        processed_ranges = {}

        for param_name, param_config in param_ranges.items():
            if isinstance(param_config, dict) and param_config.get('type') == 'linspace':
                # 线性空间采样
                start = param_config.get('start', 300)
                stop = param_config.get('stop', 1000)
                num = param_config.get('num', 10)

                # 使用线性空间生成采样点
                lin_values = np.linspace(start, stop, num=num)
                processed_ranges[param_name] = lin_values

                logger.info(f"参数 '{param_name}' 使用线性空间采样: {num}个点, 范围 [{start}, {stop}]")

            elif isinstance(param_config, (list, np.ndarray)):
                # 直接使用提供的列表
                processed_ranges[param_name] = param_config
            else:
                raise ValueError(f"参数 '{param_name}' 的配置格式不正确")

        # 使用标准网格采样
        return grid_sampling(processed_ranges)

    except Exception as e:
        logger.error(f"带线性空间的网格采样出错: {str(e)}")
        raise


def latin_hypercube_sampling(param_ranges: Dict[str, tuple], n_samples: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    拉丁超立方采样 (Latin Hypercube Sampling, LHS)

    使用拉丁超立方采样生成参数组合。LHS是一种分层采样方法，能够确保
    每个参数在其范围内被均匀采样，同时避免了随机采样可能出现的聚类现象。

    相比网格采样，LHS能够用更少的样本数更好地探索高维参数空间。

    参数:
        param_ranges: 参数范围字典
            键: 参数名 (str)
            值: 参数范围元组 (min, max)

            示例:
                {
                    'temperature': (300, 1000),
                    'fission_rate': (1e18, 1e21),
                    'surface_energy': (0.5, 1.0)
                }

        n_samples: 采样数量 (int)
            要生成的参数组合数量。建议至少为参数数量的2倍。

        seed: 随机种子 (Optional[int])
            用于结果可复现。如果为None，则每次运行结果不同。

    返回:
        参数组合列表，每个元素是一个参数字典

        示例:
            [
                {'temperature': 342.5, 'fission_rate': 3.2e19, 'surface_energy': 0.78},
                {'temperature': 891.3, 'fission_rate': 1.1e20, 'surface_energy': 0.55},
                ...
            ]

    示例:
        >>> params = latin_hypercube_sampling({'temperature': (300, 1000)}, 10, seed=42)
        >>> print(f"生成的参数组合数量: {len(params)}")
        生成的参数组合数量: 10
        >>> print(f"温度范围: {min(p['temperature'] for p in params):.1f} - {max(p['temperature'] for p in params):.1f}")
        温度范围: 315.2 - 983.7

        >>> # 多参数采样
        >>> params_multi = latin_hypercube_sampling({
        ...     'temperature': (300, 1000),
        ...     'fission_rate': (1e19, 1e21),
        ...     'surface_energy': (0.5, 1.0)
        ... }, n_samples=20, seed=42)
        >>> print(f"生成的参数组合数量: {len(params_multi)}")
        生成的参数组合数量: 20

    参考文献:
        McKay, M.D., Beckman, R.J. and Conover, W.J. (1979)
        "A Comparison of Three Methods for Selecting Values of Input Variables
        in the Analysis of Output from a Computer Code"
        Technometrics, 21(2):239-245
    """
    try:
        # 验证输入
        if not param_ranges:
            logger.warning("参数范围为空，返回空列表")
            return []

        if not isinstance(param_ranges, dict):
            raise TypeError("param_ranges 必须是字典类型")

        if not isinstance(n_samples, int) or n_samples <= 0:
            raise ValueError("n_samples 必须是正整数")

        # 检查所有参数范围格式
        for param_name, param_range in param_ranges.items():
            if not isinstance(param_range, (tuple, list)) or len(param_range) != 2:
                raise TypeError(f"参数 '{param_name}' 的范围必须是包含两个元素的元组 (min, max)")

            min_val, max_val = param_range
            if min_val >= max_val:
                raise ValueError(f"参数 '{param_name}' 的最小值必须小于最大值")

        # 获取参数信息
        param_names = list(param_ranges.keys())
        n_params = len(param_names)

        # 提取参数范围
        param_bounds = [param_ranges[name] for name in param_names]

        logger.info(f"开始拉丁超立方采样: {n_params}个参数, {n_samples}个样本")
        logger.info(f"参数: {param_names}")
        logger.info(f"参数范围: {param_bounds}")

        # 创建拉丁超立方采样器
        sampler = qmc.LatinHypercube(d=n_params, seed=seed)

        # 生成样本 (单位超立方体 [0, 1)^d)
        sample_unit = sampler.random(n=n_samples)

        # 将样本从 [0, 1) 空间映射到实际参数范围
        sample_scaled = qmc.scale(sample_unit, [b[0] for b in param_bounds], [b[1] for b in param_bounds])

        # 构建参数字典列表
        parameter_combinations = []
        for i in range(n_samples):
            param_dict = {name: float(sample_scaled[i, j]) for j, name in enumerate(param_names)}
            parameter_combinations.append(param_dict)

        logger.info(f"拉丁超立方采样完成，生成了 {len(parameter_combinations)} 个参数组合")

        # 验证采样的均匀性
        for j, name in enumerate(param_names):
            samples = [p[name] for p in parameter_combinations]
            logger.info(f"参数 '{name}' 采样范围: [{min(samples):.4e}, {max(samples):.4e}]")

        return parameter_combinations

    except Exception as e:
        logger.error(f"拉丁超立方采样过程中出错: {str(e)}")
        raise


def print_sampling_summary(params: List[Dict[str, Any]], show_first_n: int = 5):
    """
    打印采样结果摘要

    参数:
        params: 参数组合列表
        show_first_n: 显示前N个组合的详细信息
    """
    print(f"\n{'='*60}")
    print(f"采样摘要")
    print(f"{'='*60}")
    print(f"总参数组合数: {len(params)}")

    if params:
        # 获取所有参数名
        param_names = list(params[0].keys())
        print(f"参数名: {param_names}")

        # 显示每个参数的取值范围
        print(f"\n参数取值:")
        for name in param_names:
            unique_values = sorted(set([p[name] for p in params]))
            print(f"  {name}: {len(unique_values)} 个值")
            if len(unique_values) <= 10:
                print(f"    值: {unique_values}")
            else:
                print(f"    范围: [{unique_values[0]}, ..., {unique_values[-1]}]")

        # 显示前几个组合
        print(f"\n前 {min(show_first_n, len(params))} 个参数组合:")
        for i, param in enumerate(params[:show_first_n]):
            print(f"  {i+1}. {param}")

        if len(params) > show_first_n:
            print(f"  ... (还有 {len(params) - show_first_n} 个组合)")

    print(f"{'='*60}\n")


# 便捷函数
def create_simple_grid(**kwargs) -> List[Dict[str, Any]]:
    """
    创建简单网格采样的便捷函数

    参数:
        **kwargs: 关键字参数，每个参数名对应一个值列表

    示例:
        >>> params = create_simple_grid(
        ...     temperature=[300, 400, 500],
        ...     fission_rate=[1e19, 2e19]
        ... )
        >>> print(len(params))
        6
    """
    return grid_sampling(kwargs)


if __name__ == "__main__":
    # 测试代码
    print("测试网格采样功能\n")

    # 测试1: 基本网格采样
    print("=" * 60)
    print("测试1: 基本网格采样")
    print("=" * 60)

    param_ranges = {
        'temperature': [300, 400],
        'fission_rate': [1e19, 2e19]
    }

    params = grid_sampling(param_ranges)
    print(f"生成的参数组合数量: {len(params)}")
    print("参数组合:")
    for i, p in enumerate(params):
        print(f"  {i+1}. {p}")

    # 验证：应该有 2 * 2 = 4 个组合
    assert len(params) == 4, f"期望4个组合，实际得到{len(params)}个"
    print("✓ 测试1通过\n")

    # 测试2: 三参数网格采样
    print("=" * 60)
    print("测试2: 三参数网格采样")
    print("=" * 60)

    param_ranges_3 = {
        'temperature': [300, 400, 500],
        'fission_rate': [1e19, 2e19],
        'surface_energy': [0.5, 0.6]
    }

    params_3 = grid_sampling(param_ranges_3)
    print(f"生成的参数组合数量: {len(params_3)}")

    # 验证：应该有 3 * 2 * 2 = 12 个组合
    assert len(params_3) == 12, f"期望12个组合，实际得到{len(params_3)}个"
    print("✓ 测试2通过\n")

    # 测试3: 对数空间采样
    print("=" * 60)
    print("测试3: 对数空间采样")
    print("=" * 60)

    param_ranges_log = {
        'temperature': [300, 400],
        'fission_rate': {'type': 'logspace', 'start': 1e18, 'stop': 1e20, 'num': 3}
    }

    params_log = grid_sampling_with_logspace(param_ranges_log)
    print(f"生成的参数组合数量: {len(params_log)}")
    print("前3个组合:")
    for i, p in enumerate(params_log[:3]):
        print(f"  {i+1}. {p}")

    # 验证：应该有 2 * 3 = 6 个组合
    assert len(params_log) == 6, f"期望6个组合，实际得到{len(params_log)}个"
    print("✓ 测试3通过\n")

    # 测试4: 线性空间采样
    print("=" * 60)
    print("测试4: 线性空间采样")
    print("=" * 60)

    param_ranges_lin = {
        'temperature': {'type': 'linspace', 'start': 300, 'stop': 500, 'num': 3},
        'fission_rate': [1e19]
    }

    params_lin = grid_sampling_with_linspace(param_ranges_lin)
    print(f"生成的参数组合数量: {len(params_lin)}")
    print("所有组合:")
    for i, p in enumerate(params_lin):
        print(f"  {i+1}. {p}")

    # 验证：应该有 3 * 1 = 3 个组合
    assert len(params_lin) == 3, f"期望3个组合，实际得到{len(params_lin)}个"
    print("✓ 测试4通过\n")

    # 测试5: 便捷函数
    print("=" * 60)
    print("测试5: 便捷函数")
    print("=" * 60)

    params_easy = create_simple_grid(
        temp=[300, 400],
        rate=[1e19, 2e19]
    )
    print(f"生成的参数组合数量: {len(params_easy)}")

    # 验证：应该有 2 * 2 = 4 个组合
    assert len(params_easy) == 4, f"期望4个组合，实际得到{len(params_easy)}个"
    print("✓ 测试5通过\n")

    print("=" * 60)
    print("所有测试通过！")
    print("=" * 60)
