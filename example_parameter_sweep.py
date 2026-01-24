#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例参数扫描脚本 - Example Parameter Sweep Script

演示如何使用参数扫描模块进行多参数研究，包括缓存、并行执行和结果导出。
Demonstrates how to use the parameter sweep module for multi-parameter studies,
including caching, parallel execution, and result export.

功能演示 (Features Demonstrated):
    - 多维参数网格扫描 (Multi-dimensional grid sweeps)
    - 拉丁超立方采样 (Latin Hypercube Sampling)
    - 结果缓存 (Result caching)
    - 并行执行 (Parallel execution)
    - 进度跟踪 (Progress tracking)
    - 结果导出 (Result export)

作者: 研究团队
日期: 2025
"""

import numpy as np
import matplotlib.pyplot as plt
import argparse
import logging
import sys
import os
from pathlib import Path

# 导入参数扫描模块
from parameter_sweep import ParameterSweep, SweepConfig
from sampling_strategies import grid_sampling, latin_hypercube_sampling
from params.parameters import create_default_parameters

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parameter_sweep_example.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('parameter_sweep_example')


def parse_arguments():
    """
    解析命令行参数

    返回:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='多参数扫描示例脚本 - Multi-Parameter Sweep Example',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法 (Examples):

  # 基本网格扫描 (温度 x 裂变率)
  python example_parameter_sweep.py --sweep-type grid --n-temps 4 --n-rates 3

  # 拉丁超立方采样 (20个样本点)
  python example_parameter_sweep.py --sweep-type lhs --n-samples 20

  # 启用并行执行和缓存
  python example_parameter_sweep.py --parallel --n-jobs -1 --cache

  # 快速测试模式 (仅4个样本)
  python example_parameter_sweep.py --test

  # 自定义参数范围
  python example_parameter_sweep.py --temp-min 600 --temp-max 800 --n-temps 5
        """
    )

    # 扫描类型
    parser.add_argument(
        '--sweep-type',
        type=str,
        choices=['grid', 'lhs'],
        default='grid',
        help='扫描类型: grid=网格扫描, lhs=拉丁超立方采样 (默认: grid)'
    )

    # 网格扫描参数
    parser.add_argument(
        '--n-temps',
        type=int,
        default=5,
        help='温度扫描点数 (默认: 5)'
    )
    parser.add_argument(
        '--n-rates',
        type=int,
        default=3,
        help='裂变率扫描点数 (默认: 3)'
    )
    parser.add_argument(
        '--n-energies',
        type=int,
        default=2,
        help='表面能扫描点数 (默认: 2)'
    )

    # 拉丁超立方采样参数
    parser.add_argument(
        '--n-samples',
        type=int,
        default=30,
        help='拉丁超立方采样样本数 (默认: 30)'
    )

    # 参数范围
    parser.add_argument(
        '--temp-min',
        type=float,
        default=600,
        help='最低温度 (K) (默认: 600)'
    )
    parser.add_argument(
        '--temp-max',
        type=float,
        default=800,
        help='最高温度 (K) (默认: 800)'
    )
    parser.add_argument(
        '--rate-min',
        type=float,
        default=1e19,
        help='最低裂变率 (fissions/m³/s) (默认: 1e19)'
    )
    parser.add_argument(
        '--rate-max',
        type=float,
        default=1e20,
        help='最高裂变率 (fissions/m³/s) (默认: 1e20)'
    )

    # 执行选项
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='启用并行执行'
    )
    parser.add_argument(
        '--n-jobs',
        type=int,
        default=-1,
        help='并行任务数: -1=所有核心, 1=串行, >1=指定核心数 (默认: -1)'
    )
    parser.add_argument(
        '--cache',
        action='store_true',
        help='启用结果缓存'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        default='__pycache__/parameter_sweep_cache',
        help='缓存目录路径 (默认: __pycache__/parameter_sweep_cache)'
    )

    # 输出选项
    parser.add_argument(
        '--output-dir',
        type=str,
        default='sweep_results',
        help='结果输出目录 (默认: sweep_results)'
    )
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='导出结果到CSV文件'
    )
    parser.add_argument(
        '--export-excel',
        action='store_true',
        help='导出结果到Excel文件'
    )
    parser.add_argument(
        '--export-json',
        action='store_true',
        help='导出结果到JSON文件'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='生成结果图表'
    )

    # 测试模式
    parser.add_argument(
        '--test',
        action='store_true',
        help='快速测试模式 (仅运行4个样本)'
    )

    # 模拟时间
    parser.add_argument(
        '--sim-time',
        type=float,
        default=3600,
        help='模拟时间 (秒) (默认: 3600)'
    )

    # 详细程度
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    return parser.parse_args()


def create_grid_sweep_config(args):
    """
    创建网格扫描配置

    参数:
        args: 命令行参数

    返回:
        SweepConfig: 扫描配置对象
    """
    # 生成温度列表
    temperatures = np.linspace(args.temp_min, args.temp_max, args.n_temps).tolist()

    # 生成裂变率列表 (对数空间)
    fission_rates = np.logspace(
        np.log10(args.rate_min),
        np.log10(args.rate_max),
        args.n_rates
    ).tolist()

    # 生成表面能列表
    surface_energies = np.linspace(0.5, 0.7, args.n_energies).tolist()

    logger.info(f"网格扫描配置:")
    logger.info(f"  温度: {len(temperatures)} 个点 ({args.temp_min}-{args.temp_max} K)")
    logger.info(f"  裂变率: {len(fission_rates)} 个点 ({args.rate_min:.1e}-{args.rate_max:.1e} fissions/m³/s)")
    logger.info(f"  表面能: {len(surface_energies)} 个点")
    logger.info(f"  总组合数: {len(temperatures) * len(fission_rates) * len(surface_energies)}")

    config = SweepConfig(
        parameter_ranges={
            'temperature': temperatures,
            'fission_rate': fission_rates,
            'surface_energy': surface_energies
        },
        sampling_method='grid',
        sim_time=args.sim_time,
        parallel=args.parallel,
        n_jobs=args.n_jobs,
        cache_enabled=args.cache,
        cache_dir=args.cache_dir
    )

    return config


def create_lhs_sweep_config(args):
    """
    创建拉丁超立方采样配置

    参数:
        args: 命令行参数

    返回:
        SweepConfig: 扫描配置对象
    """
    n_samples = args.n_samples if not args.test else 4

    logger.info(f"拉丁超立方采样配置:")
    logger.info(f"  样本数: {n_samples}")
    logger.info(f"  温度范围: {args.temp_min}-{args.temp_max} K")
    logger.info(f"  裂变率范围: {args.rate_min:.1e}-{args.rate_max:.1e} fissions/m³/s")
    logger.info(f"  表面能范围: 0.5-0.7 J/m²")

    config = SweepConfig(
        parameter_ranges={
            'temperature': (args.temp_min, args.temp_max),
            'fission_rate': (args.rate_min, args.rate_max),
            'surface_energy': (0.5, 0.7)
        },
        sampling_method='latin_hypercube',
        n_samples=n_samples,
        sim_time=args.sim_time,
        parallel=args.parallel,
        n_jobs=args.n_jobs,
        cache_enabled=args.cache,
        cache_dir=args.cache_dir
    )

    return config


def run_sweep(args):
    """
    运行参数扫描

    参数:
        args: 命令行参数

    返回:
        ParameterSweep: 扫描对象
    """
    logger.info("=" * 60)
    logger.info("开始参数扫描 - Starting Parameter Sweep")
    logger.info("=" * 60)

    # 创建基础参数
    logger.info("创建基础参数...")
    base_params = create_default_parameters()

    # 设置一些固定参数
    base_params['time_step'] = 1e-9
    base_params['max_time_step'] = 0.1
    base_params['Fnb'] = 1e-5
    base_params['Fnf'] = 1e-5
    base_params['dislocation_density'] = 7.0e13
    base_params['resolution_rate'] = 2.0e-5
    base_params['Dgb_prefactor'] = 8.55e-12
    base_params['Dgb_fission_term'] = 1.0e-40
    base_params['Dgf_multiplier'] = 1.0
    base_params['Dv0'] = 7.767e-10
    base_params['Di0'] = 1.259e-8
    base_params['Evm'] = 0.347
    base_params['Eim'] = 0.42
    base_params['Evfmuti'] = 1.0
    base_params['gas_production_rate'] = 0.5
    base_params['critical_radius'] = 50e-9
    base_params['radius_smoothing_factor'] = 0.8
    base_params['pressure_scaling_factor'] = 0.5
    base_params['vacancy_contribution_weight'] = 1.2

    logger.info(f"基础参数配置完成")
    logger.info(f"  模拟时间: {args.sim_time} 秒")
    logger.info(f"  并行执行: {args.parallel} (n_jobs={args.n_jobs})")
    logger.info(f"  缓存启用: {args.cache}")

    # 创建扫描配置
    if args.sweep_type == 'grid':
        config = create_grid_sweep_config(args)
    else:  # lhs
        config = create_lhs_sweep_config(args)

    # 创建扫描对象
    logger.info("\n创建参数扫描对象...")
    sweep = ParameterSweep(base_params, config)

    # 运行扫描
    logger.info("\n开始运行扫描...")
    logger.info("-" * 60)
    results = sweep.run()
    logger.info("-" * 60)

    # 统计结果
    total_simulations = len(results)
    successful_simulations = sum(1 for r in results if r.success)
    failed_simulations = total_simulations - successful_simulations
    cache_hits = sum(1 for r in results if r.from_cache)

    logger.info(f"\n扫描完成!")
    logger.info(f"  总模拟数: {total_simulations}")
    logger.info(f"  成功: {successful_simulations}")
    logger.info(f"  失败: {failed_simulations}")
    logger.info(f"  缓存命中: {cache_hits}")

    if failed_simulations > 0:
        logger.warning(f"警告: {failed_simulations} 个模拟失败")
        failed_results = [r for r in results if not r.success]
        for i, result in enumerate(failed_results[:5], 1):  # 只显示前5个
            logger.warning(f"  失败 {i}: {result.error_message if result.error_message else 'Unknown error'}")

    return sweep


def export_results(sweep, args):
    """
    导出结果

    参数:
        sweep: ParameterSweep对象
        args: 命令行参数
    """
    logger.info("\n导出结果...")

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 转换为DataFrame
    df = sweep.to_dataframe(include_time_series=False)

    logger.info(f"结果DataFrame形状: {df.shape}")
    logger.info(f"  列: {list(df.columns[:10])}...")  # 只显示前10列

    # 导出CSV
    if args.export_csv:
        csv_path = output_dir / 'sweep_results.csv'
        logger.info(f"导出CSV: {csv_path}")
        sweep.export_csv(str(csv_path))
        logger.info(f"  CSV文件已保存: {csv_path}")

    # 导出Excel
    if args.export_excel:
        excel_path = output_dir / 'sweep_results.xlsx'
        logger.info(f"导出Excel: {excel_path}")
        try:
            sweep.export_excel(str(excel_path))
            logger.info(f"  Excel文件已保存: {excel_path}")
        except ImportError as e:
            logger.error(f"  Excel导出失败: {e}")
            logger.error(f"  请安装openpyxl: pip install openpyxl")

    # 导出JSON
    if args.export_json:
        json_path = output_dir / 'sweep_results.json'
        logger.info(f"导出JSON: {json_path}")
        sweep.export_json(str(json_path))
        logger.info(f"  JSON文件已保存: {json_path}")

    # 默认导出CSV (如果没有指定任何导出选项)
    if not (args.export_csv or args.export_excel or args.export_json):
        csv_path = output_dir / 'sweep_results.csv'
        logger.info(f"导出CSV (默认): {csv_path}")
        sweep.export_csv(str(csv_path))
        logger.info(f"  CSV文件已保存: {csv_path}")

    logger.info("结果导出完成")


def plot_results(sweep, args):
    """
    绘制结果图表

    参数:
        sweep: ParameterSweep对象
        args: 命令行参数
    """
    logger.info("\n生成结果图表...")

    try:
        # 获取DataFrame
        df = sweep.to_dataframe(include_time_series=False)

        # 只保留成功的结果
        df_successful = df[df['success'] == True].copy()

        if len(df_successful) == 0:
            logger.warning("没有成功的结果可以绘图")
            return

        # 创建输出目录
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Parameter Sweep Results', fontsize=16, fontweight='bold')

        # 1. 肿胀率 vs 温度
        if 'param_temperature' in df_successful.columns:
            ax = axes[0, 0]
            ax.scatter(df_successful['param_temperature'],
                      df_successful['final_swelling'],
                      c=df_successful['param_fission_rate'] if 'param_fission_rate' in df_successful.columns else 'blue',
                      cmap='viridis', alpha=0.6, s=50)
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel('Final Swelling (%)')
            ax.set_title('Swelling vs Temperature')
            ax.grid(True, alpha=0.3)
            if 'param_fission_rate' in df_successful.columns:
                cbar = plt.colorbar(ax.collections[0], ax=ax)
                cbar.set_label('Fission Rate (fissions/m³/s)')

        # 2. 肿胀率 vs 裂变率
        if 'param_fission_rate' in df_successful.columns:
            ax = axes[0, 1]
            ax.scatter(df_successful['param_fission_rate'],
                      df_successful['final_swelling'],
                      c=df_successful['param_temperature'] if 'param_temperature' in df_successful.columns else 'red',
                      cmap='coolwarm', alpha=0.6, s=50)
            ax.set_xscale('log')
            ax.set_xlabel('Fission Rate (fissions/m³/s)')
            ax.set_ylabel('Final Swelling (%)')
            ax.set_title('Swelling vs Fission Rate')
            ax.grid(True, alpha=0.3)
            if 'param_temperature' in df_successful.columns:
                cbar = plt.colorbar(ax.collections[0], ax=ax)
                cbar.set_label('Temperature (K)')

        # 3. 气泡半径 vs 温度
        if 'param_temperature' in df_successful.columns and 'final_Rcb' in df_successful.columns:
            ax = axes[1, 0]
            ax.scatter(df_successful['param_temperature'],
                      df_successful['final_Rcb'] * 1e9,  # 转换为nm
                      c=df_successful['final_swelling'],
                      cmap='plasma', alpha=0.6, s=50)
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel('Final Bubble Radius (nm)')
            ax.set_title('Bubble Radius vs Temperature')
            ax.grid(True, alpha=0.3)
            cbar = plt.colorbar(ax.collections[0], ax=ax)
            cbar.set_label('Final Swelling (%)')

        # 4. 气泡浓度 vs 温度
        if 'param_temperature' in df_successful.columns and 'final_Ccb' in df_successful.columns:
            ax = axes[1, 1]
            ax.scatter(df_successful['param_temperature'],
                      df_successful['final_Ccb'],
                      c=df_successful['final_swelling'],
                      cmap='magma', alpha=0.6, s=50)
            ax.set_yscale('log')
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel('Final Bubble Concentration (cavities/m³)')
            ax.set_title('Bubble Concentration vs Temperature')
            ax.grid(True, alpha=0.3)
            cbar = plt.colorbar(ax.collections[0], ax=ax)
            cbar.set_label('Final Swelling (%)')

        plt.tight_layout()

        # 保存图表
        plot_path = output_dir / 'sweep_results_plots.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"图表已保存: {plot_path}")
        plt.close()

    except Exception as e:
        logger.error(f"绘图失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def print_summary(sweep):
    """
    打印结果摘要

    参数:
        sweep: ParameterSweep对象
    """
    logger.info("\n" + "=" * 60)
    logger.info("结果摘要 - Results Summary")
    logger.info("=" * 60)

    try:
        # 获取DataFrame
        df = sweep.to_dataframe(include_time_series=False)

        # 只统计成功的结果
        df_successful = df[df['success'] == True]

        if len(df_successful) == 0:
            logger.warning("没有成功的结果")
            return

        logger.info(f"\n成功模拟数量: {len(df_successful)}")

        # 肿胀率统计
        if 'final_swelling' in df_successful.columns:
            swelling = df_successful['final_swelling']
            logger.info(f"\n肿胀率统计 (Swelling Statistics):")
            logger.info(f"  最小值: {swelling.min():.6f}%")
            logger.info(f"  最大值: {swelling.max():.6f}%")
            logger.info(f"  平均值: {swelling.mean():.6f}%")
            logger.info(f"  标准差: {swelling.std():.6f}%")

        # 气泡半径统计
        if 'final_Rcb' in df_successful.columns:
            radius = df_successful['final_Rcb'] * 1e9  # 转换为nm
            logger.info(f"\n气泡半径统计 (Bubble Radius Statistics):")
            logger.info(f"  最小值: {radius.min():.4f} nm")
            logger.info(f"  最大值: {radius.max():.4f} nm")
            logger.info(f"  平均值: {radius.mean():.4f} nm")

        # 运行时间统计
        if 'runtime' in df_successful.columns:
            runtime = df_successful['runtime']
            logger.info(f"\n运行时间统计 (Runtime Statistics):")
            logger.info(f"  总时间: {runtime.sum():.2f} 秒")
            logger.info(f"  平均时间: {runtime.mean():.2f} 秒")
            logger.info(f"  最短时间: {runtime.min():.2f} 秒")
            logger.info(f"  最长时间: {runtime.max():.2f} 秒")

        # 缓存效率
        if 'from_cache' in df_successful.columns:
            cache_hits = df_successful['from_cache'].sum()
            cache_hit_rate = cache_hits / len(df_successful) * 100
            logger.info(f"\n缓存效率 (Cache Efficiency):")
            logger.info(f"  缓存命中: {cache_hits}/{len(df_successful)} ({cache_hit_rate:.1f}%)")

    except Exception as e:
        logger.error(f"生成摘要失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 打印配置
    logger.info("参数扫描示例脚本")
    logger.info("=" * 60)
    logger.info(f"扫描类型: {args.sweep_type}")
    logger.info(f"并行执行: {args.parallel} (n_jobs={args.n_jobs})")
    logger.info(f"缓存启用: {args.cache}")
    logger.info(f"测试模式: {args.test}")
    logger.info(f"输出目录: {args.output_dir}")
    logger.info("=" * 60)

    try:
        # 运行扫描
        sweep = run_sweep(args)

        # 打印摘要
        print_summary(sweep)

        # 导出结果
        export_results(sweep, args)

        # 生成图表
        if args.plot:
            plot_results(sweep, args)

        logger.info("\n" + "=" * 60)
        logger.info("程序执行完成 - Program Completed Successfully")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        logger.warning("\n程序被用户中断")
        return 130

    except Exception as e:
        logger.error(f"\n程序执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
