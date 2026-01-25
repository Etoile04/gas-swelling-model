"""
Visualization Module for Gas Swelling Model
可视化模块 (气体肿胀模型)

This module provides plotting and visualization utilities for gas swelling
simulation results, including time series plots, comparison plots, and
debug history plots.
本模块提供气体肿胀模拟结果的绘图和可视化工具，包括时间序列图、比较图和调试历史图。
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np


# 设置日志 (Setup logging)
logger = logging.getLogger(__name__)

# 尝试导入matplotlib（可选依赖）(Try importing matplotlib - optional dependency)
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端 (Use non-interactive backend)
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, ScalarFormatter
    from matplotlib.font_manager import FontProperties
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available. Visualization functions will be disabled.")


def check_matplotlib_available() -> bool:
    """
    检查matplotlib是否可用 (Check if matplotlib is available)

    Returns
    --------
    bool
        如果matplotlib可用返回True，否则返回False
        Returns True if matplotlib is available, False otherwise
    """
    return MATPLOTLIB_AVAILABLE


def setup_chinese_font():
    """
    设置中文字体支持 (Setup Chinese Font Support)

    尝试设置matplotlib使用支持中文的字体。如果设置失败，将使用默认字体。
    Attempts to setup matplotlib to use Chinese-supporting fonts. Falls back to default font on failure.
    """
    if not MATPLOTLIB_AVAILABLE:
        return

    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    except Exception as e:
        logger.warning(f"Failed to set Chinese font: {e}")


def create_fission_formatter(fission_rate: float):
    """
    创建裂变密度格式化函数

    Parameters
    -----------
    fission_rate : float
        裂变速率 (fissions/m³/s)

    Returns
    --------
    callable
        格式化函数，用于将时间转换为裂变密度
    """
    def formatter(x, pos):
        """格式化裂变密度显示"""
        fission_density = x * fission_rate
        if fission_density >= 1e27:
            return f"{fission_density/1e27:.1f}×10²⁷"
        elif fission_density >= 1e24:
            return f"{fission_density/1e24:.1f}×10²⁴"
        elif fission_density >= 1e21:
            return f"{fission_density/1e21:.1f}×10²¹"
        else:
            return f"{fission_density:.1e}"
    return formatter


def plot_time_series(x_data: np.ndarray,
                    y_data_list: List[np.ndarray],
                    labels: List[str],
                    colors: List[str],
                    styles: List[str],
                    x_label: str,
                    y_label: str,
                    title: str,
                    filename: str,
                    save_dir: str = 'plots/',
                    figsize: Tuple[float, float] = (12, 7),
                    dpi: int = 150):
    """
    绘制时间序列图（支持多条曲线）

    Parameters
    -----------
    x_data : np.ndarray
        X轴数据（通常是时间）
    y_data_list : List[np.ndarray]
        Y轴数据列表（每个数组对应一条曲线）
    labels : List[str]
        曲线标签列表
    colors : List[str]
        曲线颜色列表
    styles : List[str]
        曲线样式列表（如 '-', '--', '-.'）
    x_label : str
        X轴标签
    y_label : str
        Y轴标签
    title : str
        图表标题
    filename : str
        保存文件名
    save_dir : str
        保存目录
    figsize : Tuple[float, float]
        图表大小 (宽, 高)
    dpi : int
        图表分辨率

    Raises
    -------
    RuntimeError
        如果matplotlib不可用

    Examples
    ---------
    >>> import numpy as np
    >>> t = np.linspace(0, 100, 100)
    >>> y1 = np.sin(t/10)
    >>> y2 = np.cos(t/10)
    >>> plot_time_series(t, [y1, y2], ['sin', 'cos'],
    ...                ['blue', 'red'], ['-', '--'],
    ...                'Time (s)', 'Value', 'Test Plot', 'test.png')
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib is not available. Cannot create plots.")
        raise RuntimeError("matplotlib is required for plotting")

    try:
        # 创建保存目录
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        # 创建图表
        fig, ax = plt.subplots(figsize=figsize)

        # 绘制多条曲线
        for i, y_data in enumerate(y_data_list):
            ax.plot(x_data, y_data, color=colors[i], linestyle=styles[i],
                   linewidth=1.8, label=labels[i])

        # 设置标签和标题
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=14, pad=15)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='best', fontsize=10, framealpha=0.9)

        # 保存图表
        output_path = Path(save_dir) / filename
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Plot saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to create plot: {e}")
        raise


def plot_dual_axis(x_data: np.ndarray,
                  y_data_list: List[np.ndarray],
                  labels: List[str],
                  colors: List[str],
                  styles: List[str],
                  x_label: str,
                  y_label: str,
                  x2_label: str,
                  title: str,
                  filename: str,
                  save_dir: str = 'plots/',
                  fission_rate: Optional[float] = None,
                  figsize: Tuple[float, float] = (12, 7),
                  dpi: int = 150):
    """
    绘制双X轴图（时间 + 裂变密度）

    Parameters
    -----------
    x_data : np.ndarray
        主X轴数据（时间）
    y_data_list : List[np.ndarray]
        Y轴数据列表
    labels : List[str]
        曲线标签列表
    colors : List[str]
        曲线颜色列表
    styles : List[str]
        曲线样式列表
    x_label : str
        主X轴标签
    y_label : str
        Y轴标签
    x2_label : str
        第二X轴标签
    title : str
        图表标题
    filename : str
        保存文件名
    save_dir : str
        保存目录
    fission_rate : Optional[float]
        裂变速率，如果提供则在第二X轴显示裂变密度
    figsize : Tuple[float, float]
        图表大小
    dpi : int
        图表分辨率

    Raises
    -------
    RuntimeError
        如果matplotlib不可用

    Examples
    ---------
    >>> t = np.linspace(0, 86400, 100)  # 1 day
    >>> y = np.exp(t/86400) * 1e15
    >>> plot_dual_axis(t, [y], ['Growth'], ['blue'], ['-'],
    ...              'Time (s)', 'Concentration (m⁻³)',
    ...              'Fission Density (fissions/m³)',
    ...              'Test', 'test.png', fission_rate=2e20)
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib is not available. Cannot create plots.")
        raise RuntimeError("matplotlib is required for plotting")

    try:
        # 创建保存目录
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        # 创建图表
        fig, ax1 = plt.subplots(figsize=figsize)

        # 绘制多条曲线
        for i, y_data in enumerate(y_data_list):
            ax1.plot(x_data, y_data, color=colors[i], linestyle=styles[i],
                    linewidth=1.8, label=labels[i])

        # 设置主轴
        ax1.set_xlabel(x_label, fontsize=12)
        ax1.set_ylabel(y_label, fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.tick_params(axis='y')

        # 创建第二X轴
        ax2 = ax1.twiny()
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_xlabel(x2_label, fontsize=12, labelpad=12)

        # 如果提供了裂变速率，设置格式化器
        if fission_rate is not None:
            ax2.xaxis.set_major_formatter(FuncFormatter(create_fission_formatter(fission_rate)))

        ax2.grid(True, linestyle=':', alpha=0.4)

        # 添加图例
        ax1.legend(loc='best', fontsize=10, framealpha=0.9)

        plt.title(title, fontsize=14, pad=15)

        # 保存图表
        output_path = Path(save_dir) / filename
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Dual-axis plot saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to create dual-axis plot: {e}")
        raise


def plot_debug_history(history: 'DebugHistory',
                      save_dir: str = 'debug_plots/',
                      fission_rate: Optional[float] = None,
                      dual_axis: bool = True):
    """
    绘制调试历史数据的所有关键变量

    Parameters
    -----------
    history : DebugHistory
        调试历史数据对象（来自debug_output模块）
    save_dir : str
        保存目录
    fission_rate : Optional[float]
        裂变速率，如果提供则在第二X轴显示裂变密度
    dual_axis : bool
        是否使用双X轴（时间 + 裂变密度）

    Raises
    -------
    RuntimeError
        如果matplotlib不可用
    ValueError
        如果历史数据为空

    Examples
    ---------
    >>> from gas_swelling.io.debug_output import DebugHistory
    >>> history = DebugHistory()
    >>> history.time = [0, 100, 200]
    >>> history.Rcb = [1e-9, 1.1e-9, 1.2e-9]
    >>> history.Rcf = [2e-9, 2.1e-9, 2.2e-9]
    >>> plot_debug_history(history, fission_rate=2e20)
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib is not available. Cannot create plots.")
        raise RuntimeError("matplotlib is required for plotting")

    # 检查是否有数据
    if not history.time:
        logger.warning("No debug history data to plot")
        return

    try:
        # 设置中文字体
        setup_chinese_font()

        # 创建保存目录
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        t = np.array(history.time)

        # 选择绘图函数
        plot_func = plot_dual_axis if dual_axis and fission_rate else plot_time_series

        # 1. 绘制半径对比
        if history.Rcb and history.Rcf:
            plot_func(
                t,
                [np.array(history.Rcb), np.array(history.Rcf)],
                labels=['基体气泡半径 (Rcb)', '相界气泡半径 (Rcf)'],
                colors=['blue', 'red'],
                styles=['-', '--'],
                x_label="时间 (秒)",
                y_label="半径 (米)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="气泡半径 vs 时间",
                filename="radius_comparison.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        # 2. 绘制压力对比
        if history.Pg_b:
            y_data = [np.array(history.Pg_b)]
            labels = ['基体气泡压力 (Pg_b)']
            colors = ['green']
            styles = ['-']

            if history.Pg_f:
                y_data.append(np.array(history.Pg_f))
                labels.append('相界气泡压力 (Pg_f)')
                colors.append('purple')
                styles.append('--')

            plot_func(
                t,
                y_data,
                labels=labels,
                colors=colors,
                styles=styles,
                x_label="时间 (秒)",
                y_label="压力 (Pa)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="气泡内压 vs 时间",
                filename="pressure_comparison.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        # 3. 绘制过压对比
        if history.Pext_b and history.Pext_f:
            plot_func(
                t,
                [np.array(history.Pext_b), np.array(history.Pext_f)],
                labels=['基体气泡过压 (Pext_b)', '相界气泡过压 (Pext_f)'],
                colors=['darkorange', 'brown'],
                styles=['-', '--'],
                x_label="时间 (秒)",
                y_label="过压 (Pa)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="气泡过压 vs 时间",
                filename="excess_pressure_comparison.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        # 4. 绘制热平衡空位浓度
        if history.cv_star_b and history.cv_star_f:
            plot_func(
                t,
                [np.array(history.cv_star_b), np.array(history.cv_star_f)],
                labels=['基体热平衡空位浓度 (cv_star_b)', '相界热平衡空位浓度 (cv_star_f)'],
                colors=['teal', 'magenta'],
                styles=['-', '--'],
                x_label="时间 (秒)",
                y_label="空位浓度 (m⁻³)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="热平衡空位浓度 vs 时间",
                filename="thermal_equilibrium_concentration.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        # 5. 绘制半径变化率
        if history.dRcb_dt and history.dRcf_dt:
            plot_func(
                t,
                [np.array(history.dRcb_dt), np.array(history.dRcf_dt)],
                labels=['基体半径变化率 (dRcb_dt)', '相界半径变化率 (dRcf_dt)'],
                colors=['crimson', 'darkblue'],
                styles=['-', '--'],
                x_label="时间 (秒)",
                y_label="半径变化率 (m/s)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="半径变化率 vs 时间",
                filename="radius_change_rate.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        # 6. 绘制气体浓度变化率
        if history.dCgb_dt and history.dCgf_dt:
            plot_func(
                t,
                [np.array(history.dCgb_dt), np.array(history.dCgf_dt)],
                labels=['基体气体浓度变化率 (dCgb_dt)', '相界气体浓度变化率 (dCgf_dt)'],
                colors=['olive', 'maroon'],
                styles=['-', '--'],
                x_label="时间 (秒)",
                y_label="气体浓度变化率 (m⁻³s⁻¹)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="气体浓度变化率 vs 时间",
                filename="gas_concentration_change_rate.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        # 7. 绘制肿胀百分比
        if history.swelling:
            plot_func(
                t,
                [np.array(history.swelling)],
                labels=['肿胀百分比 (Swelling)'],
                colors=['purple'],
                styles=['-'],
                x_label="时间 (秒)",
                y_label="肿胀 (%)",
                x2_label="裂变密度 (fissions/m³)" if dual_axis else "",
                title="肿胀 vs 时间",
                filename="swelling_vs_time.png",
                save_dir=save_dir,
                fission_rate=fission_rate
            )

        logger.info(f"All debug plots saved to {save_dir}")

    except Exception as e:
        logger.error(f"Failed to plot debug history: {e}")
        raise


def plot_swelling_comparison(results_list: List[Dict[str, np.ndarray]],
                            labels: List[str],
                            colors: List[str],
                            save_path: str = 'swelling_comparison.png',
                            save_dir: str = 'plots/'):
    """
    绘制多组模拟结果的肿胀对比图

    Parameters
    -----------
    results_list : List[Dict[str, np.ndarray]]
        结果字典列表，每个字典应包含'time'和'swelling'键
    labels : List[str]
        每组结果的标签
    colors : List[str]
        每组结果的颜色
    save_path : str
        保存文件名
    save_dir : str
        保存目录

    Raises
    -------
    RuntimeError
        如果matplotlib不可用

    Examples
    ---------
    >>> result1 = {'time': np.array([0, 100]), 'swelling': np.array([0, 1.5])}
    >>> result2 = {'time': np.array([0, 100]), 'swelling': np.array([0, 2.0])}
    >>> plot_swelling_comparison([result1, result2],
    ...                          ['Case 1', 'Case 2'],
    ...                          ['blue', 'red'])
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib is not available. Cannot create plots.")
        raise RuntimeError("matplotlib is required for plotting")

    try:
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 7))

        for i, result in enumerate(results_list):
            if 'time' in result and 'swelling' in result:
                ax.plot(result['time'], result['swelling'],
                       color=colors[i], linewidth=2.0, label=labels[i])

        ax.set_xlabel("时间 (秒)", fontsize=12)
        ax.set_ylabel("肿胀 (%)", fontsize=12)
        ax.set_title("肿胀对比", fontsize=14, pad=15)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='best', fontsize=10, framealpha=0.9)

        output_path = Path(save_dir) / save_path
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Swelling comparison plot saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to create swelling comparison plot: {e}")
        raise


if __name__ == '__main__':
    # 测试可视化功能
    print("Testing visualization module")

    if not check_matplotlib_available():
        print("matplotlib not available - skipping tests")
    else:
        print("matplotlib available - running tests")

        # 创建测试数据
        from gas_swelling.io.debug_output import DebugHistory, update_debug_history
        history = DebugHistory()

        for i in range(10):
            time = i * 100.0
            state = {
                'Cgb': 1e20 * (1 - i*0.05),
                'Ccb': 1e15 * (1 + i*0.1),
                'Rcb': 1e-9 * (1 + i*0.05),
                'Rcf': 2e-9 * (1 + i*0.03),
                'swelling': 0.1 * i
            }
            derived = {
                'Pg_b': 1e5 * (1 + i*0.02),
                'Pg_f': 1.2e5 * (1 + i*0.015),
                'Pext_b': 1e4 * (1 + i*0.01),
                'Pext_f': 1.2e4 * (1 + i*0.008),
                'cv_star_b': 1e10 * (1 + i*0.001),
                'cv_star_f': 1.1e10 * (1 + i*0.001),
                'dRcb_dt': 1e-12 * i,
                'dRcf_dt': 8e-13 * i,
                'dCgb_dt': -1e15 * i,
                'dCgf_dt': -9e14 * i
            }
            update_debug_history(history, state, time, derived)

        # 测试绘图
        try:
            plot_debug_history(history, save_dir='/tmp/test_plots/', fission_rate=2e20)
            print("Plots created successfully")
        except Exception as e:
            print(f"Plot test failed: {e}")

    print("visualization module OK")
