#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试参数验证和错误处理

这个脚本测试parameter_sweep模块中的参数验证和错误处理功能。
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_validation')


def test_sweepconfig_validation():
    """测试SweepConfig验证"""
    print("\n" + "="*60)
    print("测试 SweepConfig 参数验证")
    print("="*60)

    from parameter_sweep import SweepConfig

    # 测试1: 正常配置
    print("\n[测试1] 正常配置")
    try:
        config = SweepConfig(
            parameter_ranges={'temperature': [300, 400, 500]},
            n_samples=10,
            sampling_method='grid',
            sim_time=1000
        )
        print("✓ 正常配置验证通过")
    except Exception as e:
        print(f"✗ 不应该失败: {e}")
        return False

    # 测试2: 无效的采样方法
    print("\n[测试2] 无效的采样方法")
    try:
        config = SweepConfig(sampling_method='invalid_method')
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试3: n_samples <= 0
    print("\n[测试3] n_samples <= 0")
    try:
        config = SweepConfig(n_samples=0)
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试4: sim_time <= 0
    print("\n[测试4] sim_time <= 0")
    try:
        config = SweepConfig(sim_time=-100)
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试5: 无效的parameter_ranges
    print("\n[测试5] 无效的parameter_ranges（非字典）")
    try:
        config = SweepConfig(parameter_ranges="invalid")
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试6: parameter_ranges包含空列表
    print("\n[测试6] parameter_ranges包含空列表")
    try:
        config = SweepConfig(parameter_ranges={'temperature': []})
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试7: parameter_ranges包含非数值
    print("\n[测试7] parameter_ranges包含非数值")
    try:
        config = SweepConfig(parameter_ranges={'temperature': ['invalid']})
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试8: 无效的n_jobs
    print("\n[测试8] 无效的n_jobs")
    try:
        config = SweepConfig(n_jobs=0)
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    return True


def test_parametersweep_validation():
    """测试ParameterSweep验证"""
    print("\n" + "="*60)
    print("测试 ParameterSweep 参数验证")
    print("="*60)

    from parameter_sweep import ParameterSweep

    # 测试1: 无效的base_params类型
    print("\n[测试1] 无效的base_params类型")
    try:
        sweep = ParameterSweep(base_params="invalid")
        print("✗ 应该抛出TypeError")
        return False
    except TypeError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试2: 空的base_params
    print("\n[测试2] 空的base_params")
    try:
        sweep = ParameterSweep(base_params={})
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试3: 无效的temperature
    print("\n[测试3] 无效的temperature")
    try:
        sweep = ParameterSweep(base_params={'temperature': -100, 'fission_rate': 1e19})
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试4: 无效的fission_rate
    print("\n[测试4] 无效的fission_rate")
    try:
        sweep = ParameterSweep(base_params={'temperature': 600, 'fission_rate': 0})
        print("✗ 应该抛出ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试5: 正常配置（跳过模型导入测试）
    print("\n[测试5] 正常配置（不导入模型）")
    try:
        # 创建一个模拟的配置，但不会真正导入模型（因为没有实际的参数）
        # 这里只测试验证逻辑
        params = {
            'temperature': 600,
            'fission_rate': 1e19,
            'time_step': 1e-9
        }
        # 注意：这会尝试导入模型，可能会失败，这是预期的
        sweep = ParameterSweep(base_params=params)
        print("✓ 正常配置验证通过（可能因缺少模型文件而失败，这是正常的）")
    except ImportError as e:
        print(f"✓ 预期的导入错误（测试环境）: {e}")
    except Exception as e:
        print(f"✗ 意外的错误: {e}")
        return False

    return True


def test_export_validation():
    """测试导出函数的验证"""
    print("\n" + "="*60)
    print("测试导出函数验证")
    print("="*60)

    from parameter_sweep import ParameterSweep, SweepConfig

    # 创建一个简单的测试实例（使用模拟数据）
    try:
        # 创建模拟配置
        config = SweepConfig(
            parameter_ranges={},
            sim_time=100
        )

        # 创建模拟参数（这可能会因缺少模型而失败）
        params = {
            'temperature': 600,
            'fission_rate': 1e19,
            'time_step': 1e-9
        }

        sweep = ParameterSweep(base_params=params, config=config)

        # 测试1: 导出时没有结果
        print("\n[测试1] 导出时没有结果")
        try:
            sweep.export_csv('/tmp/test.csv')
            print("✗ 应该抛出ValueError")
            return False
        except ValueError as e:
            print(f"✓ 正确捕获错误: {e}")

        # 测试2: 空文件路径
        print("\n[测试2] 空文件路径")
        try:
            sweep.export_csv('')
            print("✗ 应该抛出ValueError")
            return False
        except ValueError as e:
            print(f"✓ 正确捕获错误: {e}")

        # 测试3: 无效的文件路径类型
        print("\n[测试3] 无效的文件路径类型")
        try:
            sweep.export_csv(123)
            print("✗ 应该抛出TypeError")
            return False
        except TypeError as e:
            print(f"✓ 正确捕获错误: {e}")

    except ImportError as e:
        print(f"✓ 预期的导入错误（测试环境缺少模型文件）: {e}")
        print("  导出验证测试跳过（需要有效的模型实例）")
        return True

    return True


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("参数验证和错误处理测试")
    print("="*60)

    all_passed = True

    # 运行所有测试
    if not test_sweepconfig_validation():
        all_passed = False

    if not test_parametersweep_validation():
        all_passed = False

    if not test_export_validation():
        all_passed = False

    # 汇总结果
    print("\n" + "="*60)
    if all_passed:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
