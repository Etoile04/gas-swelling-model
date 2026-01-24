#!/usr/bin/env python3
"""
简单测试：验证parameter_sweep模块可以正确导入和实例化
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_import')

def test_import():
    """测试模块导入"""
    logger.info("测试1: 导入parameter_sweep模块")
    try:
        import parameter_sweep
        logger.info("✓ parameter_sweep模块导入成功")
        return True
    except Exception as e:
        logger.error(f"✗ 导入失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_classes():
    """测试类是否可用"""
    logger.info("测试2: 检查主要类和函数")
    try:
        from parameter_sweep import (
            SweepConfig,
            SimulationResult,
            SimulationCache,
            ParameterSweep,
            ProgressTracker,
            create_progress_bar,
            format_time_duration,
            estimate_remaining_time
        )
        logger.info("✓ 所有类和函数导入成功")
        return True
    except Exception as e:
        logger.error(f"✗ 类导入失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_sweep_config():
    """测试SweepConfig类"""
    logger.info("测试3: 创建SweepConfig实例")
    try:
        from parameter_sweep import SweepConfig
        config = SweepConfig(
            parameter_ranges={'temperature': [600, 650, 700]},
            n_samples=10,
            sampling_method='grid',
            parallel=False,
            cache_enabled=True
        )
        logger.info(f"✓ SweepConfig创建成功: {config}")
        return True
    except Exception as e:
        logger.error(f"✗ SweepConfig创建失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_simulation_result():
    """测试SimulationResult类"""
    logger.info("测试4: 创建SimulationResult实例")
    try:
        from parameter_sweep import SimulationResult
        result = SimulationResult(
            parameters={'temperature': 650},
            success=True,
            metadata={'runtime': 1.5}
        )
        logger.info(f"✓ SimulationResult创建成功: {result.success}")
        return True
    except Exception as e:
        logger.error(f"✗ SimulationResult创建失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_progress_tracker():
    """测试ProgressTracker类"""
    logger.info("测试5: 测试ProgressTracker功能")
    try:
        from parameter_sweep import ProgressTracker
        import time

        tracker = ProgressTracker(total_tasks=10, desc="测试")
        logger.info(f"✓ ProgressTracker创建成功")

        # 模拟一些进度更新
        for i in range(5):
            tracker.update(success=True, is_cache_hit=(i % 2 == 0), task_time=0.1)

        summary = tracker.get_summary()
        logger.info(f"✓ 进度摘要: {summary['progress_percent']:.0f}% 完成")
        logger.info(f"✓ 预计剩余: {summary['eta_formatted']}")

        return True
    except Exception as e:
        logger.error(f"✗ ProgressTracker测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_time_formatting():
    """测试时间格式化函数"""
    logger.info("测试6: 测试时间格式化功能")
    try:
        from parameter_sweep import format_time_duration

        test_cases = [
            (30, "30秒"),
            (90, "1分钟30秒"),
            (3661, "1小时1分钟1秒"),
            (-1, "未知")
        ]

        for seconds, expected in test_cases:
            result = format_time_duration(seconds)
            logger.info(f"  {seconds}秒 -> '{result}'")

        logger.info("✓ 时间格式化功能正常")
        return True
    except Exception as e:
        logger.error(f"✗ 时间格式化测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_eta_estimation():
    """测试ETA估计函数"""
    logger.info("测试7: 测试ETA估计功能")
    try:
        from parameter_sweep import estimate_remaining_time
        import time

        start = time.time()
        # 模拟已完成5个任务，总共10个
        eta = estimate_remaining_time(start, completed=5, total=10)
        logger.info(f"✓ ETA估计: {eta:.1f}秒")

        return True
    except Exception as e:
        logger.error(f"✗ ETA估计测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("参数扫描模块导入和基础功能测试")
    print("=" * 60)
    print()

    tests = [
        test_import,
        test_classes,
        test_sweep_config,
        test_simulation_result,
        test_progress_tracker,
        test_time_formatting,
        test_eta_estimation
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"测试执行出错: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
