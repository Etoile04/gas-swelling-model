"""
Debug Output Module for Gas Swelling Model
调试输出模块 (气体肿胀模型)

This module provides utilities for managing and formatting debug output
during gas swelling simulations.
本模块提供在气体肿胀模拟期间管理和格式化调试输出的实用工具。
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import numpy as np


# 设置日志 (Setup logging)
logger = logging.getLogger(__name__)


@dataclass
class DebugConfig:
    """调试配置参数 (Debug Configuration Parameters)"""
    enabled: bool = False  # 是否启用调试模式
    time_step_interval: int = 100  # 每隔多少时间步记录一次
    save_to_file: bool = False  # 是否保存到文件
    output_file: Optional[str] = None  # 输出文件路径
    verbose: bool = False  # 是否输出详细信息


@dataclass
class DebugHistory:
    """调试历史数据容器 (Debug History Data Container)"""
    time: List[float] = field(default_factory=list)
    Cgb: List[float] = field(default_factory=list)  # 晶内气体浓度
    Ccb: List[float] = field(default_factory=list)  # 晶内气泡浓度
    Ncb: List[float] = field(default_factory=list)  # 晶内气泡气体原子数
    Rcb: List[float] = field(default_factory=list)  # 晶内气泡半径
    Cgf: List[float] = field(default_factory=list)  # 相界气体浓度
    Ccf: List[float] = field(default_factory=list)  # 相界气泡浓度
    Ncf: List[float] = field(default_factory=list)  # 相界气泡气体原子数
    Rcf: List[float] = field(default_factory=list)  # 相界气泡半径
    cvb: List[float] = field(default_factory=list)  # 晶内空位浓度
    cib: List[float] = field(default_factory=list)  # 晶内间隙原子浓度
    cvf: List[float] = field(default_factory=list)  # 相界空位浓度
    cif: List[float] = field(default_factory=list)  # 相界间隙原子浓度
    Pg_b: List[float] = field(default_factory=list)  # 晶内气泡压力
    Pg_f: List[float] = field(default_factory=list)  # 相界气泡压力
    Pext_b: List[float] = field(default_factory=list)  # 晶内过压
    Pext_f: List[float] = field(default_factory=list)  # 相界过压
    cv_star_b: List[float] = field(default_factory=list)  # 晶内热平衡空位浓度
    cv_star_f: List[float] = field(default_factory=list)  # 相界热平衡空位浓度
    dRcb_dt: List[float] = field(default_factory=list)  # 晶内半径变化率
    dRcf_dt: List[float] = field(default_factory=list)  # 相界半径变化率
    dCgb_dt: List[float] = field(default_factory=list)  # 晶内气体浓度变化率
    dCgf_dt: List[float] = field(default_factory=list)  # 相界气体浓度变化率
    released_gas: List[float] = field(default_factory=list)  # 释放气体量
    swelling: List[float] = field(default_factory=list)  # 肿胀百分比

    def to_dict(self) -> Dict[str, np.ndarray]:
        """转换为字典格式，方便绘图"""
        return {k: np.array(v) for k, v in self.__dict__.items()}

    def clear(self):
        """清空历史数据"""
        for key in self.__dict__:
            self.__dict__[key] = []

    def __len__(self) -> int:
        """返回记录的数据点数量"""
        return len(self.time)


def format_debug_output(state: Dict[str, float],
                       time: float,
                       params: Dict[str, Any],
                       config: Optional[DebugConfig] = None) -> str:
    """
    格式化调试输出信息

    Parameters
    -----------
    state : Dict[str, float]
        当前状态变量字典
    time : float
        当前时间
    params : Dict[str, Any]
        模型参数字典
    config : Optional[DebugConfig]
        调试配置，如果为None则使用默认配置

    Returns
    --------
    str
        格式化的调试输出字符串

    Examples
    ---------
    >>> state = {'Cgb': 1e20, 'Ccb': 1e15, 'Rcb': 1e-9}
    >>> params = {'fission_rate': 2e20}
    >>> output = format_debug_output(state, 100.0, params)
    >>> print(output)
    Time: 1.00e+02 s | Cgb: 1.00e+20 | Ccb: 1.00e+15 | Rcb: 1.00e-09 m
    """
    if config is None:
        config = DebugConfig()

    # 基本输出
    output = f"Time: {time:.3e} s"

    # 添加关键状态变量
    if config.verbose:
        # 详细模式：显示所有状态变量
        for key, value in state.items():
            if isinstance(value, (int, float)):
                output += f" | {key}: {value:.3e}"
    else:
        # 简洁模式：只显示关键变量
        key_vars = ['Cgb', 'Ccb', 'Rcb', 'Cgf', 'Ccf', 'Rcf']
        for var in key_vars:
            if var in state:
                output += f" | {var}: {state[var]:.3e}"

        # 添加单位
        if 'Rcb' in state:
            output = output.replace(f"Rcb: {state['Rcb']:.3e}",
                                   f"Rcb: {state['Rcb']:.3e} m")
        if 'Rcf' in state:
            output = output.replace(f"Rcf: {state['Rcf']:.3e}",
                                   f"Rcf: {state['Rcf']:.3e} m")

    return output


def log_debug_message(message: str,
                     level: int = logging.DEBUG,
                     config: Optional[DebugConfig] = None):
    """
    记录调试消息

    Parameters
    -----------
    message : str
        调试消息
    level : int
        日志级别（logging.DEBUG, logging.INFO等）
    config : Optional[DebugConfig]
        调试配置，用于判断是否应该输出

    Examples
    ---------
    >>> config = DebugConfig(enabled=True)
    >>> log_debug_message("Simulation started", logging.INFO, config)
    """
    if config is None or config.enabled:
        logger.log(level, message)


def save_debug_history(history: DebugHistory,
                      filepath: str,
                      format: str = 'csv'):
    """
    保存调试历史数据到文件

    Parameters
    -----------
    history : DebugHistory
        调试历史数据
    filepath : str
        保存文件路径
    format : str
        文件格式，支持'csv'或'npy'

    Raises
    -------
    ValueError
        如果格式不支持
    IOError
        如果文件写入失败

    Examples
    ---------
    >>> history = DebugHistory()
    >>> history.time.append(0.0)
    >>> history.Cgb.append(1e20)
    >>> save_debug_history(history, 'debug_data.csv', format='csv')
    """
    try:
        if format == 'csv':
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(history.__dict__.keys())
                # 写入数据
                data = zip(*history.__dict__.values())
                writer.writerows(data)
            logger.info(f"Debug history saved to {filepath}")

        elif format == 'npy':
            # 保存为numpy格式
            data_dict = history.to_dict()
            np.save(filepath, data_dict)
            logger.info(f"Debug history saved to {filepath}")

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'npy'.")

    except Exception as e:
        logger.error(f"Failed to save debug history: {e}")
        raise


def load_debug_history(filepath: str,
                       format: str = 'csv') -> DebugHistory:
    """
    从文件加载调试历史数据

    Parameters
    -----------
    filepath : str
        文件路径
    format : str
        文件格式，支持'csv'或'npy'

    Returns
    --------
    DebugHistory
        加载的调试历史数据

    Raises
    -------
    ValueError
        如果格式不支持
    IOError
        如果文件读取失败

    Examples
    ---------
    >>> history = load_debug_history('debug_data.csv', format='csv')
    >>> print(len(history))
    100
    """
    history = DebugHistory()

    try:
        if format == 'csv':
            import csv
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for key, value in row.items():
                        if hasattr(history, key):
                            getattr(history, key).append(float(value))
            logger.info(f"Debug history loaded from {filepath}")

        elif format == 'npy':
            # 从numpy格式加载
            data_dict = np.load(filepath, allow_pickle=True).item()
            for key, values in data_dict.items():
                if hasattr(history, key):
                    setattr(history, key, list(values))
            logger.info(f"Debug history loaded from {filepath}")

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'npy'.")

    except Exception as e:
        logger.error(f"Failed to load debug history: {e}")
        raise

    return history


def update_debug_history(history: DebugHistory,
                        state: Dict[str, float],
                        time: float,
                        derived: Optional[Dict[str, float]] = None):
    """
    更新调试历史数据

    Parameters
    -----------
    history : DebugHistory
        调试历史数据容器
    state : Dict[str, float]
        当前状态变量
    time : float
        当前时间
    derived : Optional[Dict[str, float]]
        派生变量（如压力、半径等）

    Examples
    ---------
    >>> history = DebugHistory()
    >>> state = {'Cgb': 1e20, 'Ccb': 1e15}
    >>> derived = {'Rcb': 1e-9, 'Pg_b': 1e5}
    >>> update_debug_history(history, state, 0.0, derived)
    >>> len(history)
    1
    """
    # 记录时间
    history.time.append(time)

    # 记录状态变量
    state_mapping = {
        'Cgb': 'Cgb', 'Ccb': 'Ccb', 'Ncb': 'Ncb', 'Rcb': 'Rcb',
        'Cgf': 'Cgf', 'Ccf': 'Ccf', 'Ncf': 'Ncf', 'Rcf': 'Rcf',
        'cvb': 'cvb', 'cib': 'cib', 'cvf': 'cvf', 'cif': 'cif',
        'released_gas': 'released_gas', 'swelling': 'swelling'
    }

    for state_key, history_key in state_mapping.items():
        if state_key in state:
            value = state[state_key]
            if hasattr(history, history_key):
                getattr(history, history_key).append(value)

    # 记录派生变量
    if derived:
        derived_mapping = {
            'Pg_b': 'Pg_b', 'Pg_f': 'Pg_f',
            'Pext_b': 'Pext_b', 'Pext_f': 'Pext_f',
            'cv_star_b': 'cv_star_b', 'cv_star_f': 'cv_star_f',
            'dRcb_dt': 'dRcb_dt', 'dRcf_dt': 'dRcf_dt',
            'dCgb_dt': 'dCgb_dt', 'dCgf_dt': 'dCgf_dt'
        }

        for derived_key, history_key in derived_mapping.items():
            if derived_key in derived:
                value = derived[derived_key]
                if hasattr(history, history_key):
                    getattr(history, history_key).append(value)


def print_simulation_summary(history: DebugHistory,
                           params: Dict[str, Any]):
    """
    打印模拟结果摘要

    Parameters
    -----------
    history : DebugHistory
        调试历史数据
    params : Dict[str, Any]
        模型参数

    Examples
    ---------
    >>> history = DebugHistory()
    >>> history.time.append(100.0)
    >>> history.swelling.append(1.5)
    >>> params = {'fission_rate': 2e20}
    >>> print_simulation_summary(history, params)
    Simulation Summary
    ==================
    Total time: 1.00e+02 s
    Final swelling: 1.50%
    """
    if not history.time:
        logger.warning("No simulation data to summarize")
        return

    print("\n" + "="*50)
    print("Simulation Summary".center(50))
    print("="*50)

    # 时间信息
    total_time = history.time[-1]
    print(f"Total time: {total_time:.3e} s ({total_time/86400:.2f} days)")

    # 肿胀信息
    if history.swelling:
        final_swelling = history.swelling[-1]
        print(f"Final swelling: {final_swelling:.3f}%")

    # 气泡半径信息
    if history.Rcb:
        print(f"Final bulk bubble radius: {history.Rcb[-1]:.3e} m")
    if history.Rcf:
        print(f"Final boundary bubble radius: {history.Rcf[-1]:.3e} m")

    # 气体释放信息
    if history.released_gas:
        released = history.released_gas[-1]
        print(f"Total gas released: {released:.3e} atoms/m³")

    print("="*50 + "\n")


if __name__ == '__main__':
    # 测试调试输出功能
    print("Testing debug_output module")

    # 创建配置
    config = DebugConfig(enabled=True, verbose=True)

    # 创建历史数据
    history = DebugHistory()

    # 模拟一些数据
    for i in range(10):
        time = i * 100.0
        state = {
            'Cgb': 1e20 * (1 - i*0.05),
            'Ccb': 1e15 * (1 + i*0.1),
            'Rcb': 1e-9 * (1 + i*0.05)
        }
        derived = {
            'Pg_b': 1e5 * (1 + i*0.02),
            'dRcb_dt': 1e-12 * i
        }
        update_debug_history(history, state, time, derived)

    # 格式化输出
    output = format_debug_output(state, time, {}, config)
    print(f"Debug output: {output}")

    # 打印摘要
    print_simulation_summary(history, {})

    # 测试保存和加载
    try:
        save_debug_history(history, '/tmp/test_debug.csv', format='csv')
        loaded_history = load_debug_history('/tmp/test_debug.csv', format='csv')
        print(f"Loaded {len(loaded_history)} data points")
    except Exception as e:
        print(f"Save/load test skipped: {e}")

    print("debug_output module OK")
