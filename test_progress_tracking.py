#!/usr/bin/env python3
"""
测试参数扫描的进度跟踪功能

Test script for parameter sweep progress tracking functionality.
"""

import numpy as np
import logging
import time
from parameter_sweep import (
    ParameterSweep,
    SweepConfig,
    create_progress_bar,
    format_time_duration,
    estimate_remaining_time,
    ProgressTracker
)
from params.parameters import create_default_parameters

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_progress')


def test_basic_progress_bar():
    """测试基本的进度条功能"""
    logger.info("======== 测试1: 基本进度条 ========")

    # 创建一些测试数据
    test_items = list(range(10))

    # 使用进度条迭代
    for item in create_progress_bar(test_items, desc="测试迭代"):
        time.sleep(0.1)  # 模拟工作

    logger.info("基本进度条测试完成\n")


def test_time_formatting():
    """测试时间格式化功能"""
    logger.info("======== 测试2: 时间格式化 ========")

    test_times = [30, 65, 3661, 7325, -1]
    for t in test_times:
        formatted = format_time_duration(t)
        logger.info(f"{t}秒 -> {formatted}")

    logger.info("时间格式化测试完成\n")


def test_eta_estimation():
    """测试ETA估计"""
    logger.info("======== 测试3: ETA估计 ========")

    start = time.time()
    total = 10

    for i in range(total):
        time.sleep(0.2)  # 模拟工作
        eta = estimate_remaining_time(start, i + 1, total)
        progress = (i + 1) / total * 100
        logger.info(f"进度: {progress:.0f}%, 预计剩余: {format_time_duration(eta)}")

    logger.info("ETA估计测试完成\n")


def test_progress_tracker():
    """测试ProgressTracker类"""
    logger.info("======== 测试4: ProgressTracker类 ========")

    tracker = ProgressTracker(total_tasks=10, desc="测试任务")

    # 模拟执行任务
    for i in range(10):
        time.sleep(0.15)  # 模拟工作时间
        is_cache = i % 3 == 0  # 模拟一些缓存命中
        success = i != 7  # 模拟一个失败

        tracker.update(
            success=success,
            is_cache_hit=is_cache,
            task_time=0.15 if not is_cache else 0.001
        )

        # 每3个任务打印一次进度
        if (i + 1) % 3 == 0:
            summary = tracker.get_summary()
            logger.info(
                f"进度: {summary['progress_percent']:.0f}% | "
                f"成功: {summary['completed'] - summary['failed']} | "
                f"失败: {summary['failed']} | "
                f"缓存: {summary['cache_hits']} | "
                f"预计剩余: {summary['eta_formatted']}"
            )

    # 打印最终摘要
    tracker.log_summary(logger)
    logger.info("ProgressTracker测试完成\n")


def test_mini_parameter_sweep():
    """测试小规模的参数扫描（使用实际模型）"""
    logger.info("======== 测试5: 小规模参数扫描 ========")

    try:
        # 创建基础参数
        base_params = create_default_parameters()

        # 创建扫描配置 - 只扫描少量参数以快速测试
        config = SweepConfig(
            parameter_ranges={
                'temperature': [600, 650, 700],  # 3个温度点
                'Fnb': [1e-5, 1e-4]  # 2个成核因子值
            },
            sampling_method='grid',
            parallel=False,  # 使用串行以便观察进度
            cache_enabled=True,
            sim_time=360000  # 较短的模拟时间用于测试
        )

        # 创建参数扫描器
        sweep = ParameterSweep(base_params, config)

        # 运行扫描
        logger.info("开始参数扫描（应显示进度条）...")
        results = sweep.run()

        # 打印结果摘要
        logger.info(f"扫描完成，共{len(results)}个结果")
        n_success = sum(1 for r in results if r.success)
        logger.info(f"成功: {n_success}/{len(results)}")

        # 转换为DataFrame并打印前几行
        df = sweep.to_dataframe()
        if not df.empty:
            logger.info("\n前5个结果:")
            logger.info(df.head().to_string())

    except Exception as e:
        logger.error(f"参数扫描测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("小规模参数扫描测试完成\n")


def test_progress_bar_with_postfix():
    """测试带动态后缀的进度条"""
    logger.info("======== 测试6: 带后缀的进度条 ========")

    if not create_progress_bar([1, 2, 3], desc="检查").__class__.__name__ == 'tqdm':
        logger.warning("tqdm不可用，跳过此测试")
        return

    from tqdm import tqdm
    items = list(range(20))

    with tqdm(items, desc="处理中", ncols=100) as pbar:
        cache_hits = 0
        failures = 0

        for item in pbar:
            time.sleep(0.05)  # 模拟工作

            # 模拟一些条件
            if item % 5 == 0:
                cache_hits += 1
            if item % 17 == 0:
                failures += 1

            # 更新后缀信息
            pbar.set_postfix({
                '缓存命中': cache_hits,
                '失败': failures,
                '成功率': f"{((item+1-failures)/(item+1)*100):.0f}%"
            })

    logger.info("带后缀的进度条测试完成\n")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("参数扫描进度跟踪功能测试")
    print("=" * 60)
    print()

    # 运行测试
    test_basic_progress_bar()
    test_time_formatting()
    test_eta_estimation()
    test_progress_tracker()
    test_progress_bar_with_postfix()
    test_mini_parameter_sweep()

    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
