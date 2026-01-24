"""
参数扫描模块 - Parameter Sweep Module

提供多参数扫描、缓存、并行执行和智能采样功能。
Provides multi-parameter sweep, caching, parallel execution, and smart sampling capabilities.

主要类 (Main Classes):
    - SweepConfig: 参数扫描配置类
    - SimulationResult: 单次模拟结果类
    - ProgressTracker: 进度跟踪器类
    - ParameterSweep: 参数扫描主类

使用示例 (Usage Examples):

基本用法 (Basic Usage):
    >>> from parameter_sweep import ParameterSweep, SweepConfig
    >>> from params.parameters import create_default_parameters
    >>>
    >>> # 准备基础参数
    >>> base_params = create_default_parameters()
    >>>
    >>> # 配置简单的温度扫描
    >>> config = SweepConfig(
    ...     parameter_ranges={'temperature': [600, 700, 800]},
    ...     sampling_method='grid',
    ...     cache_enabled=True
    ... )
    >>>
    >>> # 创建并运行扫描
    >>> sweep = ParameterSweep(base_params, config)
    >>> results = sweep.run()
    >>>
    >>> # 分析结果
    >>> df = sweep.to_dataframe()
    >>> print(df[['temperature', 'final_swelling']].head())

高级用法 (Advanced Usage):
    >>> # 多参数扫描 + 并行执行
    >>> config = SweepConfig(
    ...     parameter_ranges={
    ...         'temperature': [600, 700, 800],
    ...         'fission_rate': [1e19, 2e19],
    ...         'surface_energy': [0.5, 0.6, 0.7]
    ...     },
    ...     sampling_method='grid',
    ...     parallel=True,
    ...     n_jobs=-1  # 使用所有CPU核心
    ... )
    >>>
    >>> sweep = ParameterSweep(base_params, config)
    >>> results = sweep.run()
    >>>
    >>> # 导出结果
    >>> sweep.export_csv('sweep_results.csv')
    >>> sweep.export_excel('sweep_results.xlsx', include_summary=True)

拉丁超立方采样 (Latin Hypercube Sampling):
    >>> # 使用拉丁超立方采样探索大参数空间
    >>> config = SweepConfig(
    ...     parameter_ranges={
    ...         'temperature': (300, 1000),
    ...         'fission_rate': (1e19, 1e21),
    ...         'surface_energy': (0.3, 1.0)
    ...     },
    ...     sampling_method='latin_hypercube',
    ...     n_samples=50  # 生成50个样本点
    ... )
    >>>
    >>> sweep = ParameterSweep(base_params, config)
    >>> results = sweep.run()

结果分析 (Result Analysis):
    >>> # 只分析成功的结果
    >>> successful_results = [r for r in results if r.success]
    >>>
    >>> # 按参数聚合
    >>> agg_df = sweep.aggregate_by_parameter('temperature', agg_func='mean')
    >>>
    >>> # 获取统计摘要
    >>> summary_df = sweep.get_summary_statistics()
    >>> print(summary_df.describe())
"""

import numpy as np
import pandas as pd
import logging
import os
import hashlib
import json
from typing import Dict, List, Any, Tuple, Optional, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
import time

# 尝试导入可选依赖
try:
    from joblib import Memory, Parallel, delayed
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    logging.warning("joblib not available, caching and parallel execution will be limited")

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logging.warning("tqdm not available, progress bars will not be displayed")

try:
    from netCDF4 import Dataset
    NETCDF_AVAILABLE = True
except ImportError:
    NETCDF_AVAILABLE = False
    logging.warning("netCDF4 not available, NetCDF export will be disabled")


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('parameter_sweep')


@dataclass
class SweepConfig:
    """
    参数扫描配置类

    用于配置参数扫描的所有参数，包括采样方法、缓存选项和并行执行设置。

    属性:
        parameter_ranges: 参数范围字典，格式为 {'param_name': [min, max] 或 [val1, val2, ...]}
        n_samples: 每个维度的采样点数（用于网格采样）
        sampling_method: 采样方法 ('grid', 'latin_hypercube', 'random')
        parallel: 是否启用并行执行
        n_jobs: 并行任务数 (-1表示使用所有CPU核心)
        cache_enabled: 是否启用缓存
        cache_dir: 缓存目录路径
        sim_time: 模拟时间（秒）
        output_interval: 输出间隔

    示例:
        >>> # 基本配置 - 网格采样
        >>> config = SweepConfig(
        ...     parameter_ranges={
        ...         'temperature': [300, 400, 500],
        ...         'fission_rate': [1e19, 2e19]
        ...     },
        ...     sampling_method='grid',
        ...     cache_enabled=True
        ... )

        >>> # 拉丁超立方采样配置
        >>> config_lhs = SweepConfig(
        ...     parameter_ranges={
        ...         'temperature': (300, 1000),
        ...         'fission_rate': (1e19, 1e21)
        ...     },
        ...     sampling_method='latin_hypercube',
        ...     n_samples=20,
        ...     parallel=True,
        ...     n_jobs=-1
        ... )

        >>> # 禁用缓存的配置
        >>> config_no_cache = SweepConfig(
        ...     parameter_ranges={'surface_energy': [0.5, 0.6, 0.7]},
        ...     cache_enabled=False,
        ...     sim_time=3600000  # 1小时模拟
        ... )
    """
    parameter_ranges: Dict[str, List[float]] = field(default_factory=dict)
    n_samples: int = 10
    sampling_method: str = 'grid'
    parallel: bool = False
    n_jobs: int = -1
    cache_enabled: bool = True
    cache_dir: str = '__sweep_cache__'
    sim_time: float = 7200000  # 默认模拟时间（秒）
    output_interval: int = 1000

    def __post_init__(self):
        """验证配置参数"""
        # 验证采样方法
        valid_sampling = ['grid', 'latin_hypercube', 'random']
        if self.sampling_method not in valid_sampling:
            raise ValueError(f"sampling_method must be one of {valid_sampling}, got {self.sampling_method}")

        # 验证n_samples
        if self.n_samples <= 0:
            raise ValueError(f"n_samples must be positive, got {self.n_samples}")

        # 验证sim_time
        if self.sim_time <= 0:
            raise ValueError(f"sim_time must be positive, got {self.sim_time}")

        # 验证output_interval
        if self.output_interval <= 0:
            raise ValueError(f"output_interval must be positive, got {self.output_interval}")

        # 验证parameter_ranges格式
        if self.parameter_ranges:
            if not isinstance(self.parameter_ranges, dict):
                raise ValueError(f"parameter_ranges must be a dictionary, got {type(self.parameter_ranges)}")

            for param_name, param_values in self.parameter_ranges.items():
                if not isinstance(param_name, str):
                    raise ValueError(f"Parameter name must be string, got {type(param_name)}")

                if not isinstance(param_values, list):
                    raise ValueError(f"Parameter values for '{param_name}' must be a list, got {type(param_values)}")

                if len(param_values) == 0:
                    raise ValueError(f"Parameter values for '{param_name}' cannot be empty")

                # 验证所有值都是数值
                for i, val in enumerate(param_values):
                    if not isinstance(val, (int, float)):
                        raise ValueError(f"Parameter value {i} for '{param_name}' must be numeric, got {type(val)}: {val}")

        # 验证n_jobs
        if self.n_jobs is not None and self.n_jobs != -1 and self.n_jobs < 1:
            raise ValueError(f"n_jobs must be -1, None, or >= 1, got {self.n_jobs}")


@dataclass
class SimulationResult:
    """
    单次模拟结果类

    存储单次气体肿胀模拟的完整结果，包括状态变量、派生量和元数据。

    属性:
        parameters: 使用的参数字典
        time: 时间数组 (np.ndarray)
        state_variables: 状态变量字典，包含：
            - 'Cgb': 基体气体原子浓度
            - 'Ccb': 基体气腔浓度
            - 'Ncb': 基体气泡内气体原子数
            - 'cvb': 基体空位浓度
            - 'cib': 基体间隙原子浓度
            - 'Cgf': 相界面气体原子浓度
            - 'Ccf': 相界面气腔浓度
            - 'Ncf': 相界面气泡内气体原子数
            - 'cvf': 相界面空位浓度
            - 'cif': 相界面间隙原子浓度
        derived_quantities: 派生量字典，包含：
            - 'Rcb': 基体气泡半径
            - 'Rcf': 相界面气泡半径
            - 'swelling': 肿胀率（百分比）
            - 'Pg_b': 基体气泡内气体压力
            - 'Pg_f': 相界面气泡内气体压力
            - 'released_gas': 释放的气体量
        metadata: 元数据字典，包含：
            - 'runtime': 运行时间（秒）
            - 'final_swelling': 最终肿胀率
            - 'final_Rcb': 最终基体气泡半径
            - 'final_Rcf': 最终相界面气泡半径
            - 'from_cache': 是否来自缓存
        success: 模拟是否成功
        error_message: 错误信息（如果失败）

    方法:
        to_dict(): 将结果转换为字典格式

    示例:
        >>> result = SimulationResult(
        ...     parameters={'temperature': 600, 'fission_rate': 1e19},
        ...     time=np.linspace(0, 1000, 100),
        ...     state_variables={'Cgb': np.zeros(100)},
        ...     derived_quantities={'swelling': np.zeros(100)},
        ...     metadata={'runtime': 5.2, 'final_swelling': 1.5},
        ...     success=True
        ... )
        >>> print(f"最终肿胀率: {result.metadata['final_swelling']:.2f}%")
        最终肿胀率: 1.50%
        >>> result_dict = result.to_dict()
    """
    parameters: Dict[str, Any] = field(default_factory=dict)
    time: np.ndarray = field(default_factory=lambda: np.array([]))
    state_variables: Dict[str, np.ndarray] = field(default_factory=dict)
    derived_quantities: Dict[str, np.ndarray] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> Dict:
        """将结果转换为字典"""
        return asdict(self)


class ProgressTracker:
    """
    进度跟踪器类，用于参数扫描过程中的详细统计和时间估计

    跟踪参数扫描的执行进度，包括任务完成情况、缓存命中率、
    执行时间和吞吐量等统计信息。

    属性:
        total_tasks: 总任务数
        desc: 进度描述
        completed_tasks: 已完成任务数
        failed_tasks: 失败任务数
        cache_hits: 缓存命中次数
        start_time: 开始时间戳
        task_times: 各任务执行时间列表（秒）

    示例:
        >>> tracker = ProgressTracker(total_tasks=100, desc="温度扫描")
        >>> tracker.update(success=True, is_cache_hit=False, task_time=2.5)
        >>> progress = tracker.get_progress_percent()
        >>> print(f"进度: {progress:.1f}%")
        进度: 1.0%
        >>> summary = tracker.get_summary()
        >>> print(f"吞吐量: {summary['throughput']:.2f} 任务/秒")
        吞吐量: 0.40 任务/秒
    """

    def __init__(self, total_tasks: int, desc: str = "进度"):
        """
        初始化进度跟踪器

        参数:
            total_tasks: 总任务数
            desc: 进度描述

        异常:
            ValueError: 如果 total_tasks 不是正整数
        """
        self.total_tasks = total_tasks
        self.desc = desc
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.cache_hits = 0
        self.start_time = time.time()
        self.task_times = []  # 记录每个任务的执行时间
        self.last_update_time = self.start_time

    def update(self, success: bool = True, is_cache_hit: bool = False, task_time: float = None):
        """
        更新进度

        参数:
            success: 任务是否成功
            is_cache_hit: 是否来自缓存
            task_time: 任务执行时间（秒）
        """
        self.completed_tasks += 1
        if not success:
            self.failed_tasks += 1
        if is_cache_hit:
            self.cache_hits += 1
        if task_time is not None:
            self.task_times.append(task_time)
        self.last_update_time = time.time()

    def get_progress_percent(self) -> float:
        """获取进度百分比"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    def get_elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        return time.time() - self.start_time

    def get_eta(self) -> float:
        """
        估计剩余时间（秒）

        返回:
            预计剩余时间（秒），如果无法估计则返回-1
        """
        if self.completed_tasks == 0:
            return -1

        elapsed = self.get_elapsed_time()
        avg_time_per_task = elapsed / self.completed_tasks
        remaining_tasks = self.total_tasks - self.completed_tasks

        return avg_time_per_task * remaining_tasks

    def get_average_task_time(self) -> float:
        """
        获取平均任务执行时间（秒）

        返回:
            平均执行时间，如果没有完成任务则返回0
        """
        if len(self.task_times) == 0:
            return 0.0
        return sum(self.task_times) / len(self.task_times)

    def get_throughput(self) -> float:
        """
        获取吞吐量（任务/秒）

        返回:
            每秒完成任务数
        """
        elapsed = self.get_elapsed_time()
        if elapsed == 0:
            return 0.0
        return self.completed_tasks / elapsed

    def format_time(self, seconds: float) -> str:
        """
        格式化时间为可读字符串

        参数:
            seconds: 时间（秒）

        返回:
            格式化的时间字符串
        """
        if seconds < 0:
            return "未知"

        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}小时"

    def get_summary(self) -> Dict[str, Any]:
        """
        获取进度摘要信息

        返回:
            包含进度统计的字典
        """
        eta = self.get_eta()
        return {
            'desc': self.desc,
            'total': self.total_tasks,
            'completed': self.completed_tasks,
            'failed': self.failed_tasks,
            'cache_hits': self.cache_hits,
            'progress_percent': self.get_progress_percent(),
            'elapsed_time': self.get_elapsed_time(),
            'elapsed_time_formatted': self.format_time(self.get_elapsed_time()),
            'eta': eta,
            'eta_formatted': self.format_time(eta),
            'avg_task_time': self.get_average_task_time(),
            'throughput': self.get_throughput()
        }

    def log_summary(self, logger_instance):
        """
        记录进度摘要到日志

        参数:
            logger_instance: 日志记录器实例
        """
        summary = self.get_summary()
        logger_instance.info(f"======== {self.desc}摘要 ========")
        logger_instance.info(f"总任务数: {summary['total']}")
        logger_instance.info(f"已完成: {summary['completed']} ({summary['progress_percent']:.1f}%)")
        logger_instance.info(f"成功: {summary['completed'] - summary['failed']}")
        logger_instance.info(f"失败: {summary['failed']}")
        logger_instance.info(f"缓存命中: {summary['cache_hits']}")
        logger_instance.info(f"已用时间: {summary['elapsed_time_formatted']}")
        logger_instance.info(f"预计剩余: {summary['eta_formatted']}")
        logger_instance.info(f"平均任务时间: {summary['avg_task_time']:.3f}秒")
        logger_instance.info(f"吞吐量: {summary['throughput']:.3f}任务/秒")


class SimulationCache:
    """
    模拟结果缓存类

    使用joblib.Memory缓存模拟结果，避免重复运行相同参数的模拟。
    """

    def __init__(self, cache_dir: str = '__sweep_cache__', verbose: int = 0):
        """
        初始化缓存

        参数:
            cache_dir: 缓存目录路径
            verbose: 日志详细程度 (0=静默, 1=简略, 2=详细)
        """
        self.cache_dir = Path(cache_dir)
        self.verbose = verbose
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if JOBLIB_AVAILABLE:
            self.memory = Memory(location=str(self.cache_dir), verbose=verbose)
            logger.info(f"缓存已启用，目录: {self.cache_dir.absolute()}")
        else:
            self.memory = None
            logger.warning("joblib不可用，缓存功能已禁用")

    def _hash_parameters(self, parameters: Dict[str, Any]) -> str:
        """
        生成参数的哈希值作为缓存键

        参数:
            parameters: 参数字典

        返回:
            参数哈希字符串
        """
        # 将参数转换为可哈希的字符串
        param_str = json.dumps(parameters, sort_keys=True, default=str)
        return hashlib.md5(param_str.encode()).hexdigest()

    def get(self, parameters: Dict[str, Any]) -> Optional[SimulationResult]:
        """
        从缓存获取模拟结果

        参数:
            parameters: 参数字典

        返回:
            缓存的结果，如果不存在则返回None
        """
        if not JOBLIB_AVAILABLE:
            return None

        cache_key = self._hash_parameters(parameters)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                import pickle
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)
                if self.verbose >= 1:
                    logger.info(f"缓存命中: {cache_key}")
                return result
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}")
                return None
        return None

    def set(self, parameters: Dict[str, Any], result: SimulationResult) -> None:
        """
        将模拟结果存入缓存

        参数:
            parameters: 参数字典
            result: 模拟结果
        """
        if not JOBLIB_AVAILABLE:
            return

        cache_key = self._hash_parameters(parameters)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            import pickle
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            if self.verbose >= 1:
                logger.info(f"结果已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")

    def clear(self) -> None:
        """清空缓存"""
        if JOBLIB_AVAILABLE:
            self.memory.clear()
            logger.info("缓存已清空")

        # 删除缓存目录中的所有文件
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"删除缓存文件失败 {cache_file}: {e}")

        logger.info(f"缓存目录已清空: {self.cache_dir}")


class ParameterSweep:
    """
    参数扫描主类

    提供多参数扫描、结果缓存、并行执行和进度跟踪功能。
    支持网格采样、拉丁超立方采样等多种采样策略。

    参数:
        base_params: 基础参数字典，包含模型运行所需的所有参数
        config: 扫描配置对象 (SweepConfig)，如果为None则使用默认配置

    属性:
        base_params: 基础参数字典的副本
        config: 扫描配置对象
        results: 模拟结果列表 (List[SimulationResult])
        cache: 缓存对象 (SimulationCache 或 None)

    主要方法:
        generate_parameter_sets(): 生成参数组合
        run(): 运行参数扫描
        run_sequential(): 顺序执行参数扫描
        run_parallel(): 并行执行参数扫描
        clear_cache(): 清除缓存
        get_results_dataframe(): 获取结果DataFrame
        export_results(): 导出结果到文件

    示例:
        >>> from parameter_sweep import ParameterSweep, SweepConfig
        >>> from params.parameters import create_default_parameters
        >>>
        >>> # 准备基础参数
        >>> base_params = create_default_parameters()
        >>>
        >>> # 配置参数扫描
        >>> config = SweepConfig(
        ...     parameter_ranges={
        ...         'temperature': [600, 700, 800],
        ...         'fission_rate': [1e19, 2e19]
        ...     },
        ...     sampling_method='grid',
        ...     cache_enabled=True
        ... )
        >>>
        >>> # 创建参数扫描器
        >>> sweep = ParameterSweep(base_params, config)
        >>>
        >>> # 运行扫描
        >>> results = sweep.run()
        >>>
        >>> # 获取结果摘要
        >>> df = sweep.get_results_dataframe()
        >>> print(f"完成 {len(results)} 次模拟")
        完成 6 次模拟
        >>>
        >>> # 导出结果
        >>> sweep.export_results('sweep_results.csv')

    异常:
        TypeError: 如果 base_params 不是字典
        ValueError: 如果 base_params 为空
        ImportError: 如果无法导入 GasSwellingModel
    """

    def __init__(self, base_params: Dict[str, Any], config: Optional[SweepConfig] = None):
        """
        初始化参数扫描器

        参数:
            base_params: 基础参数字典，必须包含模型运行所需的关键参数
                推荐参数: 'temperature', 'fission_rate', 'time_step'
            config: 扫描配置对象 (SweepConfig)，如果为None则使用默认配置

        异常:
            TypeError: 如果 base_params 不是字典
            ValueError: 如果 base_params 为空或包含无效值
            ImportError: 如果无法导入 GasSwellingModel

        示例:
            >>> from params.parameters import create_default_parameters
            >>> base_params = create_default_parameters()
            >>> sweep = ParameterSweep(base_params)
        """
        # 验证base_params
        if not isinstance(base_params, dict):
            raise TypeError(f"base_params must be a dictionary, got {type(base_params)}")

        if len(base_params) == 0:
            raise ValueError("base_params cannot be empty")

        # 验证base_params中的基本参数类型和值
        required_params = ['temperature', 'fission_rate', 'time_step']
        missing_params = [p for p in required_params if p not in base_params]
        if missing_params:
            logger.warning(f"base_params is missing recommended parameters: {missing_params}")

        # 验证关键参数的值
        if 'temperature' in base_params:
            temp = base_params['temperature']
            if not isinstance(temp, (int, float)) or temp <= 0:
                raise ValueError(f"temperature must be a positive number, got {temp}")

        if 'fission_rate' in base_params:
            fission_rate = base_params['fission_rate']
            if not isinstance(fission_rate, (int, float)) or fission_rate <= 0:
                raise ValueError(f"fission_rate must be a positive number, got {fission_rate}")

        self.base_params = base_params.copy()
        self.config = config if config is not None else SweepConfig()
        self.results: List[SimulationResult] = []

        # 初始化缓存
        try:
            if self.config.cache_enabled:
                self.cache = SimulationCache(cache_dir=self.config.cache_dir)
            else:
                self.cache = None
                logger.info("缓存已禁用")
        except Exception as e:
            logger.error(f"缓存初始化失败: {e}")
            raise

        # 导入模型（延迟导入以避免循环依赖）
        try:
            # 尝试从models目录导入
            from models.modelrk23 import GasSwellingModel
            self.ModelClass = GasSwellingModel
        except ImportError:
            # 如果失败，尝试直接导入（兼容旧结构）
            try:
                # 假设与当前脚本在同一目录
                import importlib.util
                spec = importlib.util.spec_from_file_location("modelrk23", "modelrk23.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.ModelClass = module.GasSwellingModel
            except Exception as e:
                logger.error(f"无法导入GasSwellingModel: {e}")
                raise ImportError("无法导入GasSwellingModel模型类，请确保models/modelrk23.py存在")

        logger.info(f"参数扫描器初始化完成")
        logger.info(f"基础参数: {len(self.base_params)} 个")
        if self.config.parameter_ranges:
            logger.info(f"扫描参数: {list(self.config.parameter_ranges.keys())}")

    def _run_single_simulation(self, params: Dict[str, Any], show_progress: bool = False) -> SimulationResult:
        """
        运行单次模拟（内部方法）

        创建 GasSwellingModel 实例并运行模拟，支持缓存以提高性能。

        参数:
            params: 参数字典，必须包含 'temperature' 和 'fission_rate'
            show_progress: 是否显示单个模拟的进度（保留参数，当前未使用）

        返回:
            SimulationResult 对象，包含：
                - parameters: 使用的参数
                - time: 时间数组
                - state_variables: 状态变量字典
                - derived_quantities: 派生量字典
                - metadata: 元数据（运行时间、是否来自缓存等）
                - success: 是否成功
                - error_message: 错误信息（如果失败）

        异常:
            不会抛出异常，失败时返回包含错误信息的 SimulationResult
        """
        # 验证参数
        try:
            if not isinstance(params, dict):
                raise TypeError(f"params must be a dictionary, got {type(params)}")

            if len(params) == 0:
                raise ValueError("params cannot be empty")

            # 验证关键参数存在且有效
            if 'temperature' not in params:
                raise ValueError("params must contain 'temperature'")

            if 'fission_rate' not in params:
                raise ValueError("params must contain 'fission_rate'")

            temp = params.get('temperature')
            if not isinstance(temp, (int, float)) or temp <= 0:
                raise ValueError(f"temperature must be a positive number, got {temp}")

            fission_rate = params.get('fission_rate')
            if not isinstance(fission_rate, (int, float)) or fission_rate <= 0:
                raise ValueError(f"fission_rate must be a positive number, got {fission_rate}")

        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            return SimulationResult(
                parameters=params.copy() if isinstance(params, dict) else {},
                success=False,
                error_message=f"参数验证失败: {str(e)}",
                metadata={'runtime': 0, 'from_cache': False}
            )

        # 检查缓存
        if self.cache is not None:
            try:
                cached_result = self.cache.get(params)
                if cached_result is not None:
                    # 缓存命中，记录元数据
                    cached_result.metadata['from_cache'] = True
                    return cached_result
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")

        # 创建模型并运行模拟
        start_time = time.time()
        try:
            logger.debug(f"开始模拟: temperature={params['temperature']}, fission_rate={params['fission_rate']}")

            model = self.ModelClass(params)

            # 设置时间点
            t_eval = np.linspace(0, self.config.sim_time, 100)

            # 求解
            result = model.solve(
                t_span=(0, self.config.sim_time),
                t_eval=t_eval
            )

            # 验证结果
            if not isinstance(result, dict):
                raise TypeError(f"model.solve must return a dictionary, got {type(result)}")

            required_keys = ['time', 'Rcb', 'Rcf', 'Ccb', 'Ccf', 'Ncb', 'Ncf']
            missing_keys = [k for k in required_keys if k not in result]
            if missing_keys:
                raise ValueError(f"结果缺少必需的键: {missing_keys}")

            # 计算派生量
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100  # 百分比

            # 构造结果对象
            sim_result = SimulationResult(
                parameters=params.copy(),
                time=result['time'],
                state_variables={
                    'Cgb': result['Cgb'],
                    'Ccb': result['Ccb'],
                    'Ncb': result['Ncb'],
                    'cvb': result['cvb'],
                    'cib': result['cib'],
                    'Cgf': result['Cgf'],
                    'Ccf': result['Ccf'],
                    'Ncf': result['Ncf'],
                    'cvf': result['cvf'],
                    'cif': result['cif']
                },
                derived_quantities={
                    'Rcb': Rcb,
                    'Rcf': Rcf,
                    'swelling': swelling,
                    'Pg_b': result.get('Pg_b', np.zeros_like(result['time'])),
                    'Pg_f': result.get('Pg_f', np.zeros_like(result['time'])),
                    'released_gas': result.get('released_gas', np.zeros_like(result['time']))
                },
                metadata={
                    'runtime': time.time() - start_time,
                    'final_swelling': swelling[-1] if len(swelling) > 0 else 0.0,
                    'final_Rcb': Rcb[-1] if len(Rcb) > 0 else 0.0,
                    'final_Rcf': Rcf[-1] if len(Rcf) > 0 else 0.0,
                    'from_cache': False
                },
                success=True
            )

            logger.debug(f"模拟成功: runtime={sim_result.metadata['runtime']:.3f}s, "
                        f"final_swelling={sim_result.metadata['final_swelling']:.4f}%")

            # 存入缓存
            if self.cache is not None:
                try:
                    self.cache.set(params, sim_result)
                except Exception as e:
                    logger.warning(f"缓存写入失败: {e}")

            return sim_result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"模拟失败 (参数: {params}): {error_msg}")

            # 导入traceback以获取详细的错误信息
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")

            return SimulationResult(
                parameters=params.copy(),
                success=False,
                error_message=error_msg,
                metadata={'runtime': time.time() - start_time, 'from_cache': False}
            )

    def generate_parameter_sets(self) -> List[Dict[str, Any]]:
        """
        生成参数集合

        根据配置的采样方法和参数范围，生成所有要运行的参数组合。
        支持 grid（网格）、latin_hypercube（拉丁超立方）和 random（随机）采样。

        返回:
            参数字典列表，每个字典包含一组完整的参数

        异常:
            ValueError: 如果采样方法无效或参数值格式错误
            ImportError: 如果采样策略模块不可用且内置采样失败

        示例:
            >>> config = SweepConfig(
            ...     parameter_ranges={'temperature': [600, 700, 800]},
            ...     sampling_method='grid'
            ... )
            >>> sweep = ParameterSweep(base_params, config)
            >>> param_sets = sweep.generate_parameter_sets()
            >>> print(f"生成了 {len(param_sets)} 个参数集")
            生成了 3 个参数集
            >>> for i, params in enumerate(param_sets):
            ...     print(f"参数集 {i+1}: temperature={params['temperature']}")
            参数集 1: temperature=600
            参数集 2: temperature=700
            参数集 3: temperature=800
        """
        try:
            if not self.config.parameter_ranges:
                logger.info("未指定参数范围，仅使用基础参数")
                return [self.base_params.copy()]

            # 验证parameter_ranges中的参数名存在于base_params中
            invalid_params = [p for p in self.config.parameter_ranges.keys() if p not in self.base_params]
            if invalid_params:
                logger.warning(f"参数范围中的参数不在基础参数中: {invalid_params}。"
                             f"这些参数将被添加到参数集中。")

            # 导入采样策略
            try:
                from sampling_strategies import grid_sampling, latin_hypercube_sampling, random_sampling
            except ImportError:
                logger.warning("sampling_strategies模块不可用，使用简单的网格采样")
                # 简单的网格采样实现
                param_sets = []
                param_names = list(self.config.parameter_ranges.keys())
                param_values = [self.config.parameter_ranges[name] for name in param_names]

                # 验证参数值
                for name, values in zip(param_names, param_values):
                    if not isinstance(values, list) or len(values) == 0:
                        raise ValueError(f"参数 '{name}' 的值必须是非空列表，得到: {values}")

                # 生成所有组合
                import itertools
                for combination in itertools.product(*param_values):
                    params = self.base_params.copy()
                    for name, value in zip(param_names, combination):
                        params[name] = value
                    param_sets.append(params)

                logger.info(f"生成了 {len(param_sets)} 个参数集（网格采样）")
                return param_sets

            # 使用采样策略模块
            if self.config.sampling_method == 'grid':
                param_sets = grid_sampling(self.base_params, self.config.parameter_ranges)
            elif self.config.sampling_method == 'latin_hypercube':
                param_sets = latin_hypercube_sampling(
                    self.base_params,
                    self.config.parameter_ranges,
                    n_samples=self.config.n_samples
                )
            elif self.config.sampling_method == 'random':
                param_sets = random_sampling(
                    self.base_params,
                    self.config.parameter_ranges,
                    n_samples=self.config.n_samples
                )
            else:
                raise ValueError(f"未知的采样方法: {self.config.sampling_method}")

            logger.info(f"生成了 {len(param_sets)} 个参数集（{self.config.sampling_method} 采样）")
            return param_sets

        except Exception as e:
            logger.error(f"生成参数集失败: {e}")
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def run(self) -> List[SimulationResult]:
        """
        运行参数扫描

        根据配置的采样方法生成参数集，并执行所有模拟。
        支持并行执行和进度跟踪。

        返回:
            模拟结果列表 (List[SimulationResult])，每个元素包含：
            - parameters: 使用的参数
            - time: 时间数组
            - state_variables: 状态变量
            - derived_quantities: 派生量
            - metadata: 元数据
            - success: 是否成功
            - error_message: 错误信息（如果失败）

        示例:
            >>> config = SweepConfig(
            ...     parameter_ranges={'temperature': [600, 700]},
            ...     parallel=True,
            ...     n_jobs=-1
            ... )
            >>> sweep = ParameterSweep(base_params, config)
            >>> results = sweep.run()
            >>> print(f"完成 {len(results)} 次模拟")
            完成 2 次模拟
            >>> successful = [r for r in results if r.success]
            >>> print(f"成功: {len(successful)}, 失败: {len(results) - len(successful)}")
            成功: 2, 失败: 0
        """
        logger.info("======== 参数扫描开始 ========")
        param_sets = self.generate_parameter_sets()
        n_simulations = len(param_sets)

        logger.info(f"总模拟数: {n_simulations}")
        logger.info(f"采样方法: {self.config.sampling_method}")
        logger.info(f"并行执行: {'是' if self.config.parallel else '否'}")

        self.results = []
        start_time = time.time()

        # 统计变量
        cache_hits = 0
        cache_misses = 0
        failed_sims = []

        if self.config.parallel and JOBLIB_AVAILABLE:
            # 并行执行
            logger.info(f"并行任务数: {self.config.n_jobs}")

            if TQDM_AVAILABLE:
                # 使用tqdm包装并行任务
                iter_params = tqdm(
                    param_sets,
                    desc="参数扫描进度",
                    total=n_simulations,
                    unit="sim",
                    unit_scale=True,
                    ncols=120,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
                )
            else:
                iter_params = param_sets

            self.results = Parallel(n_jobs=self.config.n_jobs)(
                delayed(self._run_single_simulation)(params)
                for params in iter_params
            )

            # 统计结果
            for result in self.results:
                if result.success:
                    # 检查是否来自缓存（通过运行时间判断，缓存的结果通常非常快）
                    if result.metadata.get('runtime', 0) < 0.01:  # 小于10ms认为是缓存
                        cache_hits += 1
                    else:
                        cache_misses += 1
                else:
                    failed_sims.append(result.parameters)

        else:
            # 串行执行
            if TQDM_AVAILABLE:
                # 创建进度条，显示更多详细信息
                pbar = tqdm(
                    param_sets,
                    desc="参数扫描进度",
                    total=n_simulations,
                    unit="sim",
                    unit_scale=True,
                    ncols=120,
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
                )

                # 手动更新进度条以显示缓存状态
                for params in pbar:
                    sim_start = time.time()
                    result = self._run_single_simulation(params)
                    sim_time = time.time() - sim_start

                    self.results.append(result)

                    # 更新统计
                    if result.success:
                        # 检查是否来自缓存
                        if self.cache is not None:
                            cached_result = self.cache.get(params)
                            if cached_result is not None and sim_time < 0.01:
                                cache_hits += 1
                                cache_status = "缓存命中"
                            else:
                                cache_misses += 1
                                cache_status = "新计算"
                        else:
                            cache_misses += 1
                            cache_status = "无缓存"
                    else:
                        failed_sims.append(result.parameters)
                        cache_status = "失败"

                    # 更新进度条后缀显示统计信息
                    pbar.set_postfix({
                        '成功': sum(1 for r in self.results if r.success),
                        '失败': len(failed_sims),
                        '缓存': cache_hits,
                        '状态': cache_status
                    })

                pbar.close()

            else:
                # 不使用tqdm
                for i, params in enumerate(param_sets, 1):
                    result = self._run_single_simulation(params)
                    self.results.append(result)

                    if i % max(1, n_simulations // 10) == 0:  # 每10%打印一次进度
                        logger.info(f"进度: {i}/{n_simulations} ({i/n_simulations*100:.1f}%)")

        elapsed_time = time.time() - start_time
        n_success = sum(1 for r in self.results if r.success)
        n_failed = len(self.results) - n_success

        logger.info("======== 参数扫描完成 ========")
        logger.info(f"总耗时: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分钟)")

        # 详细统计信息
        if elapsed_time > 0:
            avg_time = elapsed_time / n_simulations
            logger.info(f"平均每模拟: {avg_time:.3f} 秒")
            logger.info(f"吞吐量: {n_simulations/elapsed_time:.3f} sim/s")

        logger.info(f"成功: {n_success}/{n_simulations} ({n_success/n_simulations*100:.1f}%)")
        logger.info(f"失败: {n_failed}/{n_simulations} ({n_failed/n_simulations*100:.1f}%)")

        if self.cache is not None:
            logger.info(f"缓存命中: {cache_hits} ({cache_hits/n_simulations*100:.1f}%)")
            logger.info(f"新计算: {cache_misses} ({cache_misses/n_simulations*100:.1f}%)")

        if n_failed > 0:
            logger.warning(f"有 {n_failed} 次模拟失败")
            # 记录失败的参数（仅前5个）
            for i, failed_params in enumerate(failed_sims[:5]):
                logger.warning(f"失败参数 {i+1}: {failed_params}")
            if len(failed_sims) > 5:
                logger.warning(f"还有 {len(failed_sims)-5} 个失败参数未显示")

        return self.results

    def to_dataframe(self, include_time_series: bool = False) -> pd.DataFrame:
        """
        将结果转换为pandas DataFrame

        将所有模拟结果转换为表格格式，便于分析和可视化。
        默认只包含最终值，可选择包含时间序列的统计信息。

        参数:
            include_time_series: 是否包含时间序列数据的统计信息（最大值、最小值、均值、标准差）

        返回:
            pandas DataFrame，包含以下列：
                - 所有参数列（来自 parameters）
                - success: 是否成功
                - runtime: 运行时间（秒）
                - final_swelling: 最终肿胀率（%）
                - final_Rcb: 最终基体气泡半径（m）
                - final_Rcf: 最终相界面气泡半径（m）
                - from_cache: 是否来自缓存
                - final_*: 各状态变量的最终值（如果存在）
                - *_max, *_min, *_mean, *_std: 时间序列统计（如果 include_time_series=True）

        示例:
            >>> results = sweep.run()
            >>> df = sweep.to_dataframe()
            >>> print(f"结果DataFrame形状: {df.shape}")
            结果DataFrame形状: (10, 15)
            >>> df[['temperature', 'final_swelling', 'runtime']].head()
               temperature  final_swelling  runtime
            0        600.0        1.2345   5.234
            1        700.0        2.3456   5.123
            ...
            >>>
            >>> # 包含时间序列统计
            >>> df_stats = sweep.to_dataframe(include_time_series=True)
            >>> df_stats[['swelling_max', 'swelling_mean', 'swelling_std']].head()
               swelling_max  swelling_mean  swelling_std
            0      1.5000       0.7500      0.4330
            1      2.8000       1.4000      0.8000
            ...
        """
        if not self.results:
            logger.warning("没有结果可转换")
            return pd.DataFrame()

        rows = []
        for result in self.results:
            if not result.success:
                continue

            # 基础行：参数 + 最终值
            row = result.parameters.copy()
            row.update({
                'success': result.success,
                'runtime': result.metadata.get('runtime', 0),
                'final_swelling': result.metadata.get('final_swelling', 0),
                'final_Rcb': result.metadata.get('final_Rcb', 0),
                'final_Rcf': result.metadata.get('final_Rcf', 0),
                'from_cache': result.metadata.get('from_cache', False)
            })

            # 添加状态变量的最终值
            if result.state_variables:
                for var_name, var_data in result.state_variables.items():
                    if len(var_data) > 0:
                        row[f'final_{var_name}'] = var_data[-1]

            # 添加派生量的统计信息
            if include_time_series and result.derived_quantities:
                for qty_name, qty_data in result.derived_quantities.items():
                    if len(qty_data) > 0:
                        row[f'{qty_name}_max'] = np.max(qty_data)
                        row[f'{qty_name}_min'] = np.min(qty_data)
                        row[f'{qty_name}_mean'] = np.mean(qty_data)
                        row[f'{qty_name}_std'] = np.std(qty_data)

            rows.append(row)

        df = pd.DataFrame(rows)
        logger.info(f"结果已转换为DataFrame: {len(df)} 行 × {len(df.columns)} 列")
        return df

    def get_summary_statistics(self) -> pd.DataFrame:
        """
        获取汇总统计信息

        返回:
            包含汇总统计的DataFrame
        """
        if not self.results:
            logger.warning("没有结果可统计")
            return pd.DataFrame()

        df = self.to_dataframe()

        if df.empty:
            return pd.DataFrame()

        # 计算统计摘要
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        summary = pd.DataFrame({
            'count': df[numeric_cols].count(),
            'mean': df[numeric_cols].mean(),
            'std': df[numeric_cols].std(),
            'min': df[numeric_cols].min(),
            '25%': df[numeric_cols].quantile(0.25),
            '50%': df[numeric_cols].quantile(0.50),
            '75%': df[numeric_cols].quantile(0.75),
            'max': df[numeric_cols].max()
        })

        logger.info(f"汇总统计已生成: {len(summary)} 个数值列")
        return summary

    def get_successful_results(self) -> List[SimulationResult]:
        """
        获取所有成功的模拟结果

        返回:
            成功的模拟结果列表
        """
        successful = [r for r in self.results if r.success]
        logger.info(f"成功结果: {len(successful)}/{len(self.results)}")
        return successful

    def get_failed_results(self) -> List[SimulationResult]:
        """
        获取所有失败的模拟结果

        返回:
            失败的模拟结果列表
        """
        failed = [r for r in self.results if not r.success]
        if failed:
            logger.warning(f"失败结果: {len(failed)}/{len(self.results)}")
        return failed

    def aggregate_by_parameter(self, param_name: str, agg_func: str = 'mean') -> pd.DataFrame:
        """
        按指定参数聚合结果

        参数:
            param_name: 要聚合的参数名
            agg_func: 聚合函数 ('mean', 'median', 'std', 'min', 'max')

        返回:
            聚合后的DataFrame
        """
        df = self.to_dataframe()

        if param_name not in df.columns:
            logger.error(f"参数 '{param_name}' 不存在于结果中")
            return pd.DataFrame()

        # 获取数值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # 按参数分组并聚合
        if agg_func == 'mean':
            agg_df = df.groupby(param_name)[numeric_cols].mean()
        elif agg_func == 'median':
            agg_df = df.groupby(param_name)[numeric_cols].median()
        elif agg_func == 'std':
            agg_df = df.groupby(param_name)[numeric_cols].std()
        elif agg_func == 'min':
            agg_df = df.groupby(param_name)[numeric_cols].min()
        elif agg_func == 'max':
            agg_df = df.groupby(param_name)[numeric_cols].max()
        else:
            logger.error(f"未知的聚合函数: {agg_func}")
            return pd.DataFrame()

        logger.info(f"按 '{param_name}' 聚合完成，使用 {agg_func} 函数")
        return agg_df

    def export_excel(self, filepath: str, include_summary: bool = True) -> None:
        """
        导出结果到Excel文件（多工作表）

        参数:
            filepath: Excel文件路径
            include_summary: 是否包含汇总统计工作表
        """
        # 验证filepath
        if not filepath:
            raise ValueError("filepath不能为空")

        if not isinstance(filepath, str):
            raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

        # 检查目录是否存在
        import os
        file_dir = os.path.dirname(filepath)
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                logger.info(f"创建目录: {file_dir}")
            except Exception as e:
                raise IOError(f"无法创建目录 {file_dir}: {e}")

        # 检查是否有结果
        if not self.results:
            raise ValueError("没有结果可导出")

        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 主结果表
                df = self.to_dataframe(include_time_series=True)

                if df.empty:
                    logger.warning("DataFrame为空，仅导出表头")
                    df.to_excel(writer, sheet_name='Results', index=False)
                else:
                    df.to_excel(writer, sheet_name='Results', index=False)
                    logger.info(f"导出主结果表: {len(df)} 行")

                    # 仅成功的模拟结果
                    successful_df = df[df['success'] == True]
                    successful_df.to_excel(writer, sheet_name='Successful Only', index=False)
                    logger.info(f"导出成功结果表: {len(successful_df)} 行")

                    # 汇总统计
                    if include_summary and not df.empty:
                        try:
                            summary = self.get_summary_statistics()
                            if not summary.empty:
                                summary.to_excel(writer, sheet_name='Summary Statistics')
                                logger.info("导出汇总统计表")

                                # 按关键参数汇总
                                if 'temperature' in df.columns:
                                    temp_summary = self.aggregate_by_parameter('temperature', 'mean')
                                    if not temp_summary.empty:
                                        temp_summary.to_excel(writer, sheet_name='By Temperature')
                                        logger.info("导出温度汇总表")
                        except Exception as e:
                            logger.warning(f"生成汇总统计失败: {e}")

            logger.info(f"结果已导出到Excel: {filepath}")
        except ImportError as e:
            logger.error(f"缺少必需的库: {e}")
            raise ImportError("导出Excel需要openpyxl库。请安装: pip install openpyxl")
        except PermissionError:
            logger.error(f"文件权限错误，无法写入: {filepath}")
            raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限或是否被其他程序打开")
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def export_json(self, filepath: str, include_time_series: bool = False) -> None:
        """
        导出结果到JSON文件

        参数:
            filepath: JSON文件路径
            include_time_series: 是否包含完整的时间序列数据
        """
        # 验证filepath
        if not filepath:
            raise ValueError("filepath不能为空")

        if not isinstance(filepath, str):
            raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

        # 检查目录是否存在
        import os
        file_dir = os.path.dirname(filepath)
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                logger.info(f"创建目录: {file_dir}")
            except Exception as e:
                raise IOError(f"无法创建目录 {file_dir}: {e}")

        # 检查是否有结果
        if not self.results:
            raise ValueError("没有结果可导出")

        try:
            data = {
                'config': {
                    'sim_time': self.config.sim_time,
                    'sampling_method': self.config.sampling_method,
                    'n_samples': self.config.n_samples,
                    'parallel': self.config.parallel,
                    'cache_enabled': self.config.cache_enabled
                },
                'results': [],
                'summary': {}
            }

            # 转换结果为可序列化的格式
            for i, result in enumerate(self.results):
                try:
                    result_dict = {
                        'parameters': result.parameters,
                        'success': result.success,
                        'metadata': result.metadata
                    }

                    if result.success:
                        # 添加最终值
                        result_dict['final_values'] = {}
                        if result.state_variables:
                            for var_name, var_data in result.state_variables.items():
                                if len(var_data) > 0:
                                    result_dict['final_values'][var_name] = float(var_data[-1])

                        if result.derived_quantities:
                            for qty_name, qty_data in result.derived_quantities.items():
                                if len(qty_data) > 0:
                                    result_dict['final_values'][qty_name] = float(qty_data[-1])

                        # 可选：添加时间序列数据
                        if include_time_series:
                            result_dict['time_series'] = {}
                            if result.state_variables:
                                for var_name, var_data in result.state_variables.items():
                                    result_dict['time_series'][var_name] = var_data.tolist()
                            if result.derived_quantities:
                                for qty_name, qty_data in result.derived_quantities.items():
                                    result_dict['time_series'][qty_name] = qty_data.tolist()
                            result_dict['time'] = result.time.tolist()
                    else:
                        result_dict['error'] = result.error_message

                    data['results'].append(result_dict)
                except Exception as e:
                    logger.warning(f"结果 {i} 序列化失败: {e}")
                    data['results'].append({
                        'parameters': result.parameters if hasattr(result, 'parameters') else {},
                        'success': False,
                        'error': f"序列化失败: {str(e)}"
                    })

            # 添加汇总统计
            try:
                df = self.to_dataframe()
                if not df.empty:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    data['summary'] = {
                        'total_runs': len(self.results),
                        'successful_runs': sum(1 for r in self.results if r.success),
                        'failed_runs': sum(1 for r in self.results if not r.success),
                        'statistics': df[numeric_cols].describe().to_dict()
                    }
            except Exception as e:
                logger.warning(f"生成汇总统计失败: {e}")
                data['summary'] = {
                    'total_runs': len(self.results),
                    'successful_runs': sum(1 for r in self.results if r.success),
                    'failed_runs': sum(1 for r in self.results if not r.success),
                    'error': f"统计生成失败: {str(e)}"
                }

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=lambda x: float(x) if isinstance(x, (np.integer, np.floating)) else str(x))

            logger.info(f"结果已导出到JSON: {filepath} ({len(data['results'])} 条结果)")
        except PermissionError:
            logger.error(f"文件权限错误，无法写入: {filepath}")
            raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限")
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def export_parquet(self, filepath: str) -> None:
        """
        导出结果到Parquet文件（高效的二进制格式）

        参数:
            filepath: Parquet文件路径
        """
        # 验证filepath
        if not filepath:
            raise ValueError("filepath不能为空")

        if not isinstance(filepath, str):
            raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

        # 检查目录是否存在
        import os
        file_dir = os.path.dirname(filepath)
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                logger.info(f"创建目录: {file_dir}")
            except Exception as e:
                raise IOError(f"无法创建目录 {file_dir}: {e}")

        # 检查是否有结果
        if not self.results:
            raise ValueError("没有结果可导出")

        try:
            df = self.to_dataframe(include_time_series=True)
            if df.empty:
                logger.warning("DataFrame为空，导出空Parquet文件")
            df.to_parquet(filepath, index=False)
            logger.info(f"结果已导出到Parquet: {filepath} ({len(df)} 行)")
        except ImportError as e:
            logger.error(f"缺少必需的库: {e}")
            raise ImportError("导出Parquet需要pyarrow或fastparquet库。请安装: pip install pyarrow")
        except PermissionError:
            logger.error(f"文件权限错误，无法写入: {filepath}")
            raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限")
        except Exception as e:
            logger.error(f"导出Parquet失败: {e}")
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def export_netcdf(self, filepath: str, include_time_series: bool = True, compression: int = 4) -> None:
        """
        导出结果到NetCDF文件（多维数据格式）

        NetCDF (Network Common Data Form) 是一种用于存储和共享科学数组数据的文件格式。
        特别适合处理多维时间序列数据。

        参数:
            filepath: NetCDF文件路径 (.nc或.nc4)
            include_time_series: 是否包含完整的时间序列数据
            compression: 压缩级别 (0-9, 0=无压缩, 4=默认, 9=最大压缩)

        异常:
            ImportError: 当netCDF4库不可用时抛出
            ValueError: 当results为空时
            IOError: 当文件写入失败时

        示例:
            >>> sweep = ParameterSweep(params, config)
            >>> results = sweep.run()
            >>> sweep.export_netcdf('sweep_results.nc')
            >>> sweep.export_netcdf('results.nc4', include_time_series=True, compression=6)
        """
        # 验证netCDF4可用性
        if not NETCDF_AVAILABLE:
            raise ImportError("netCDF4库不可用。请安装: pip install netCDF4")

        # 验证filepath
        if not filepath:
            raise ValueError("filepath不能为空")

        if not isinstance(filepath, str):
            raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

        # 检查目录是否存在
        import os
        file_dir = os.path.dirname(filepath)
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                logger.info(f"创建目录: {file_dir}")
            except Exception as e:
                raise IOError(f"无法创建目录 {file_dir}: {e}")

        # 检查是否有结果
        if not self.results:
            raise ValueError("没有结果可导出")

        try:
            # 创建NetCDF文件
            with Dataset(filepath, 'w', format='NETCDF4') as nc:
                # 添加全局属性
                nc.title = 'Parameter Sweep Results'
                nc.institution = 'Gas Swelling Model Simulation'
                nc.source = 'parameter_sweep.ParameterSweep'
                nc.history = f'Created {time.ctime(time.time())}'
                nc.Conventions = 'CF-1.6'

                # 添加配置元数据
                nc.sim_time = self.config.sim_time
                nc.sampling_method = self.config.sampling_method
                nc.n_samples = getattr(self.config, 'n_samples', 0)
                nc.parallel = self.config.parallel
                nc.cache_enabled = self.config.cache_enabled
                nc.total_simulations = len(self.results)
                nc.successful_simulations = sum(1 for r in self.results if r.success)

                # 定义维度
                # n_simulations: 模拟次数
                nc.createDimension('n_simulations', len(self.results))

                # 收集所有参数名和变量名
                all_param_names = set()
                all_state_var_names = set()
                all_derived_qty_names = set()
                time_length = 0

                for result in self.results:
                    if result.success:
                        all_param_names.update(result.parameters.keys())
                        if result.state_variables:
                            all_state_var_names.update(result.state_variables.keys())
                        if result.derived_quantities:
                            all_derived_qty_names.update(result.derived_quantities.keys())
                        if len(result.time) > time_length:
                            time_length = len(result.time)

                # 如果有时间序列数据，创建time维度
                if include_time_series and time_length > 0:
                    nc.createDimension('time', time_length)
                    time_var = nc.createVariable('time', 'f8', ('time',), zlib=True, complevel=compression)
                    time_var.units = 'seconds'
                    time_var.long_name = 'Simulation time'
                    time_var.standard_name = 'time'
                    # 使用第一个成功结果的时间数组（假设所有模拟的时间点相同）
                    for result in self.results:
                        if result.success and len(result.time) > 0:
                            time_var[:] = result.time
                            break

                # 创建模拟索引变量
                sim_idx_var = nc.createVariable('simulation_index', 'i4', ('n_simulations',), zlib=True, complevel=compression)
                sim_idx_var[:] = np.arange(len(self.results))
                sim_idx_var.long_name = 'Simulation index'

                # 创建success标志变量
                success_var = nc.createVariable('success', 'i1', ('n_simulations',), zlib=True, complevel=compression)
                success_var[:] = np.array([int(r.success) for r in self.results], dtype='i1')
                success_var.long_name = 'Simulation success flag'

                # 创建运行时间变量
                runtime_var = nc.createVariable('runtime', 'f8', ('n_simulations',), zlib=True, complevel=compression)
                runtime_var[:] = np.array([r.metadata.get('runtime', np.nan) for r in self.results], dtype='f8')
                runtime_var.units = 'seconds'
                runtime_var.long_name = 'Simulation runtime'

                # 创建缓存标志变量
                cache_var = nc.createVariable('from_cache', 'i1', ('n_simulations',), zlib=True, complevel=compression)
                cache_var[:] = np.array([int(r.metadata.get('from_cache', False)) for r in self.results], dtype='i1')
                cache_var.long_name = 'Result from cache flag'

                # 导出参数（每个参数作为一个变量）
                param_names = sorted(all_param_names)
                for param_name in param_names:
                    # 创建变量
                    var = nc.createVariable(
                        f'param_{param_name}',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var.long_name = f'Parameter: {param_name}'

                    # 填充数据
                    data = []
                    for result in self.results:
                        if result.parameters and param_name in result.parameters:
                            data.append(result.parameters[param_name])
                        else:
                            data.append(np.nan)
                    var[:] = np.array(data, dtype='f8')

                # 导出最终状态变量值
                state_var_names = sorted(all_state_var_names)
                for var_name in state_var_names:
                    # 创建最终值变量
                    var = nc.createVariable(
                        f'state_{var_name}_final',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var.long_name = f'State variable final value: {var_name}'

                    # 填充数据
                    data = []
                    for result in self.results:
                        if result.success and result.state_variables and var_name in result.state_variables:
                            var_data = result.state_variables[var_name]
                            if len(var_data) > 0:
                                data.append(float(var_data[-1]))
                            else:
                                data.append(np.nan)
                        else:
                            data.append(np.nan)
                    var[:] = np.array(data, dtype='f8')

                # 导出派生量
                derived_qty_names = sorted(all_derived_qty_names)
                for qty_name in derived_qty_names:
                    # 创建最终值变量
                    var = nc.createVariable(
                        f'derived_{qty_name}_final',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var.long_name = f'Derived quantity final value: {qty_name}'

                    # 填充数据
                    data = []
                    for result in self.results:
                        if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                            qty_data = result.derived_quantities[qty_name]
                            if len(qty_data) > 0:
                                data.append(float(qty_data[-1]))
                            else:
                                data.append(np.nan)
                        else:
                            data.append(np.nan)
                    var[:] = np.array(data, dtype='f8')

                    # 如果需要，添加时间序列统计
                    if include_time_series:
                        # 最大值
                        var_max = nc.createVariable(
                            f'derived_{qty_name}_max',
                            'f8',
                            ('n_simulations',),
                            zlib=True,
                            complevel=compression,
                            fill_value=np.nan
                        )
                        var_max.long_name = f'Derived quantity maximum: {qty_name}'
                        data_max = []
                        for result in self.results:
                            if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                                qty_data = result.derived_quantities[qty_name]
                                if len(qty_data) > 0:
                                    data_max.append(float(np.max(qty_data)))
                                else:
                                    data_max.append(np.nan)
                            else:
                                data_max.append(np.nan)
                        var_max[:] = np.array(data_max, dtype='f8')

                        # 最小值
                        var_min = nc.createVariable(
                            f'derived_{qty_name}_min',
                            'f8',
                            ('n_simulations',),
                            zlib=True,
                            complevel=compression,
                            fill_value=np.nan
                        )
                        var_min.long_name = f'Derived quantity minimum: {qty_name}'
                        data_min = []
                        for result in self.results:
                            if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                                qty_data = result.derived_quantities[qty_name]
                                if len(qty_data) > 0:
                                    data_min.append(float(np.min(qty_data)))
                                else:
                                    data_min.append(np.nan)
                            else:
                                data_min.append(np.nan)
                        var_min[:] = np.array(data_min, dtype='f8')

                        # 平均值
                        var_mean = nc.createVariable(
                            f'derived_{qty_name}_mean',
                            'f8',
                            ('n_simulations',),
                            zlib=True,
                            complevel=compression,
                            fill_value=np.nan
                        )
                        var_mean.long_name = f'Derived quantity mean: {qty_name}'
                        data_mean = []
                        for result in self.results:
                            if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                                qty_data = result.derived_quantities[qty_name]
                                if len(qty_data) > 0:
                                    data_mean.append(float(np.mean(qty_data)))
                                else:
                                    data_mean.append(np.nan)
                            else:
                                data_mean.append(np.nan)
                        var_mean[:] = np.array(data_mean, dtype='f8')

                        # 标准差
                        var_std = nc.createVariable(
                            f'derived_{qty_name}_std',
                            'f8',
                            ('n_simulations',),
                            zlib=True,
                            complevel=compression,
                            fill_value=np.nan
                        )
                        var_std.long_name = f'Derived quantity std: {qty_name}'
                        data_std = []
                        for result in self.results:
                            if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                                qty_data = result.derived_quantities[qty_name]
                                if len(qty_data) > 1:
                                    data_std.append(float(np.std(qty_data)))
                                else:
                                    data_std.append(np.nan)
                            else:
                                data_std.append(np.nan)
                        var_std[:] = np.array(data_std, dtype='f8')

                    # 如果需要，添加完整的时间序列数据（多维变量）
                    if include_time_series and time_length > 0:
                        # 创建 (n_simulations, time) 维度的变量
                        ts_var = nc.createVariable(
                            f'derived_{qty_name}_timeseries',
                            'f8',
                            ('n_simulations', 'time'),
                            zlib=True,
                            complevel=compression,
                            fill_value=np.nan
                        )
                        ts_var.long_name = f'Derived quantity time series: {qty_name}'

                        # 填充数据
                        ts_data = np.full((len(self.results), time_length), np.nan, dtype='f8')
                        for i, result in enumerate(self.results):
                            if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                                qty_data = result.derived_quantities[qty_name]
                                if len(qty_data) > 0:
                                    # 截断或填充到time_length
                                    actual_len = min(len(qty_data), time_length)
                                    ts_data[i, :actual_len] = qty_data[:actual_len]

                        ts_var[:] = ts_data

            logger.info(f"结果已导出到NetCDF: {filepath}")
            logger.info(f"  - 总结果数: {len(self.results)}")
            logger.info(f"  - 成功: {sum(1 for r in self.results if r.success)}")
            logger.info(f"  - 参数: {len(param_names)}")
            logger.info(f"  - 状态变量: {len(state_var_names)}")
            logger.info(f"  - 派生量: {len(derived_qty_names)}")
            logger.info(f"  - 时间序列: {'是' if include_time_series else '否'}")
            logger.info(f"  - 压缩级别: {compression}")

        except PermissionError:
            logger.error(f"文件权限错误，无法写入: {filepath}")
            raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限")
        except Exception as e:
            logger.error(f"导出NetCDF失败: {e}")
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def export_csv(self, filepath: str, include_time_series: bool = False) -> None:
        """
        导出结果到CSV文件

        将模拟结果导出为逗号分隔值（CSV）格式，便于在Excel或其他工具中分析。

        参数:
            filepath: CSV文件路径（相对或绝对路径）
            include_time_series: 是否包含时间序列数据的统计信息（最大值、最小值、均值、标准差）

        异常:
            PermissionError: 如果文件无法写入（权限问题或文件被占用）
            Exception: 其他导出错误

        示例:
            >>> sweep.run()
            >>> sweep.export_csv('results.csv')
            结果已导出到CSV: results.csv
              - 总结果数: 10
              - 成功: 10
            >>>
            >>> # 包含时间序列统计
            >>> sweep.export_csv('results_detailed.csv', include_time_series=True)
            结果已导出到CSV: results_detailed.csv
              - 总结果数: 10
              - 包含时间序列统计: 是
        """
        # 验证filepath
        if not filepath:
            raise ValueError("filepath不能为空")

        if not isinstance(filepath, str):
            raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

        # 检查目录是否存在
        import os
        file_dir = os.path.dirname(filepath)
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                logger.info(f"创建目录: {file_dir}")
            except Exception as e:
                raise IOError(f"无法创建目录 {file_dir}: {e}")

        # 检查是否有结果
        if not self.results:
            raise ValueError("没有结果可导出")

        try:
            df = self.to_dataframe(include_time_series=include_time_series)
            if df.empty:
                logger.warning("DataFrame为空，导出空CSV文件")
            df.to_csv(filepath, index=False)
            logger.info(f"结果已导出到CSV: {filepath} ({len(df)} 行)")
        except PermissionError:
            logger.error(f"文件权限错误，无法写入: {filepath}")
            raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限")
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            raise


class ParallelRunner:
    """
    并行执行器类，用于多进程并行运行模拟任务

    使用multiprocessing.Pool或joblib.Parallel实现并行执行，
    支持动态任务分配和进度跟踪。

    属性:
        n_jobs: 并行进程数 (-1表示使用所有CPU核心)
        backend: 并行后端 ('multiprocessing' 或 'joblib')
        prefer: 任务调度偏好 ('processes', 'threads', 或 None)
        verbose: 日志详细程度
    """

    def __init__(self, n_jobs: int = -1, backend: str = 'auto', prefer: str = None, verbose: int = 0):
        """
        初始化并行执行器

        参数:
            n_jobs: 并行任务数，-1表示使用所有CPU核心，None表示禁用并行
            backend: 并行后端选择
                - 'auto': 自动选择（优先joblib，其次multiprocessing）
                - 'joblib': 使用joblib.Parallel
                - 'multiprocessing': 使用multiprocessing.Pool
            prefer: 任务调度偏好（仅joblib后端支持）
                - 'processes': 使用进程池
                - 'threads': 使用线程池
                - None: 自动选择
            verbose: 日志详细程度 (0=静默, 1=简略, 2=详细)
        """
        self.n_jobs = n_jobs
        self.backend = self._determine_backend(backend)
        self.prefer = prefer
        self.verbose = verbose
        self._pool = None

        # 确定实际使用的CPU核心数
        if n_jobs == -1:
            import os
            self._actual_n_jobs = os.cpu_count() or 1
        elif n_jobs is None:
            self._actual_n_jobs = 1
        else:
            self._actual_n_jobs = max(1, n_jobs)

        if self.verbose >= 1:
            logger.info(f"并行执行器初始化: 后端={self.backend}, 任务数={self._actual_n_jobs}")

    def _determine_backend(self, backend: str) -> str:
        """
        确定使用的后端

        参数:
            backend: 用户指定的后端

        返回:
            实际使用的后端名称
        """
        if backend == 'auto':
            # 优先使用joblib（如果可用），其次使用multiprocessing
            if JOBLIB_AVAILABLE:
                return 'joblib'
            else:
                return 'multiprocessing'
        elif backend == 'joblib':
            if JOBLIB_AVAILABLE:
                return 'joblib'
            else:
                logger.warning("joblib不可用，回退到multiprocessing")
                return 'multiprocessing'
        elif backend == 'multiprocessing':
            return 'multiprocessing'
        else:
            logger.warning(f"未知的后端 '{backend}'，使用auto选择")
            return self._determine_backend('auto')

    def run(self, func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
        """
        并行执行函数任务列表

        参数:
            func: 要执行的函数，接受单个参数
            tasks: 任务参数列表
            **kwargs: 额外的并行参数（传递给后端）

        返回:
            函数执行结果列表，顺序与输入任务相同

        示例:
            >>> runner = ParallelRunner(n_jobs=4)
            >>> results = runner.run(simulation_function, [params1, params2, params3])
        """
        if not tasks:
            logger.warning("任务列表为空，返回空结果")
            return []

        # 如果n_jobs为None或1，使用串行执行
        if self.n_jobs is None or self.n_jobs == 1 or len(tasks) == 1:
            if self.verbose >= 1:
                logger.info(f"串行执行 {len(tasks)} 个任务")
            return [func(task) for task in tasks]

        # 并行执行
        if self.verbose >= 1:
            logger.info(f"并行执行 {len(tasks)} 个任务，使用 {self._actual_n_jobs} 个进程")

        if self.backend == 'joblib':
            return self._run_with_joblib(func, tasks, **kwargs)
        else:  # multiprocessing
            return self._run_with_multiprocessing(func, tasks, **kwargs)

    def _run_with_joblib(self, func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
        """
        使用joblib.Parallel执行并行任务

        参数:
            func: 要执行的函数
            tasks: 任务列表
            **kwargs: 额外参数

        返回:
            结果列表
        """
        try:
            from joblib import Parallel, delayed

            # 合并额外参数
            joblib_kwargs = {
                'n_jobs': self.n_jobs,
                'verbose': max(0, self.verbose - 1),  # joblib的verbose级别不同
                'prefer': self.prefer,
                'backend': 'multiprocessing' if self.prefer == 'processes' else None
            }
            joblib_kwargs.update(kwargs)

            # 执行并行任务
            results = Parallel(**joblib_kwargs)(
                delayed(func)(task) for task in tasks
            )

            if self.verbose >= 1:
                logger.info(f"joblib并行执行完成: {len(results)} 个结果")

            return results

        except Exception as e:
            logger.error(f"joblib并行执行失败: {e}，尝试使用multiprocessing")
            return self._run_with_multiprocessing(func, tasks, **kwargs)

    def _run_with_multiprocessing(self, func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
        """
        使用multiprocessing.Pool执行并行任务

        参数:
            func: 要执行的函数
            tasks: 任务列表
            **kwargs: 额外参数

        返回:
            结果列表
        """
        import multiprocessing as mp
        from multiprocessing import Pool

        # 确定进程池大小
        pool_size = self._actual_n_jobs

        # 准备参数
        pool_kwargs = {
            'processes': pool_size,
        }
        pool_kwargs.update(kwargs)

        results = []
        try:
            with Pool(**pool_kwargs) as pool:
                if self.verbose >= 1:
                    logger.info(f"创建进程池: {pool_size} 个进程")

                # 使用imap_unordered以获得更好的性能，然后重新排序
                if TQDM_AVAILABLE and self.verbose >= 1:
                    # 使用tqdm显示进度
                    from tqdm import tqdm
                    results = list(tqdm(
                        pool.imap(func, tasks),
                        total=len(tasks),
                        desc="并行执行",
                        unit="task"
                    ))
                else:
                    # 不使用进度条
                    results = pool.map(func, tasks)

                if self.verbose >= 1:
                    logger.info(f"multiprocessing并行执行完成: {len(results)} 个结果")

        except Exception as e:
            logger.error(f"multiprocessing并行执行失败: {e}")
            # 回退到串行执行
            logger.info("回退到串行执行")
            results = [func(task) for task in tasks]

        return results

    def map(self, func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
        """
        map函数的别名，与run方法功能相同

        参数:
            func: 要执行的函数
            tasks: 任务列表
            **kwargs: 额外参数

        返回:
            结果列表
        """
        return self.run(func, tasks, **kwargs)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，确保资源清理"""
        self.close()
        return False

    def close(self):
        """关闭并行执行器，释放资源"""
        if self._pool is not None:
            self._pool.close()
            self._pool.join()
            self._pool = None
            if self.verbose >= 1:
                logger.info("并行执行器已关闭")

    @property
    def n_jobs_actual(self) -> int:
        """获取实际使用的CPU核心数"""
        return self._actual_n_jobs


class JoblibRunner:
    """
    Joblib并行执行器类，专门用于基于joblib的并行任务执行

    提供简洁的接口来使用joblib.Parallel进行并行计算，
    支持可选的n_jobs参数和进度跟踪。

    属性:
        n_jobs: 并行任务数 (-1表示使用所有CPU核心，1表示串行)
        verbose: 日志详细程度
        prefer: 任务调度偏好 ('processes', 'threads', 或 None)
    """

    def __init__(self, n_jobs: int = -1, verbose: int = 0, prefer: str = None):
        """
        初始化Joblib并行执行器

        参数:
            n_jobs: 并行任务数
                - -1: 使用所有可用的CPU核心（默认）
                - 1: 串行执行（不使用并行）
                - >1: 使用指定数量的进程
                - None: 禁用并行，等同于1
            verbose: 日志详细程度 (0=静默, 1=简略, 2=详细)
            prefer: 任务调度偏好
                - 'processes': 使用进程池（内存隔离，适合CPU密集型）
                - 'threads': 使用线程池（共享内存，适合I/O密集型）
                - None: 自动选择

        异常:
            ImportError: 当joblib不可用时抛出
        """
        if not JOBLIB_AVAILABLE:
            raise ImportError("joblib is not available. Please install it with: pip install joblib")

        self.n_jobs = n_jobs if n_jobs is not None else 1
        self.verbose = verbose
        self.prefer = prefer

        # 确定实际使用的CPU核心数
        if self.n_jobs == -1:
            import os
            self._actual_n_jobs = os.cpu_count() or 1
        else:
            self._actual_n_jobs = max(1, self.n_jobs)

        if self.verbose >= 1:
            logger.info(f"JoblibRunner初始化: n_jobs={self.n_jobs}, 实际核心数={self._actual_n_jobs}")

    def run(self, func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
        """
        并行执行函数任务列表

        参数:
            func: 要执行的函数，接受单个参数
            tasks: 任务参数列表
            **kwargs: 额外的并行参数（传递给joblib.Parallel）
                例如: backend='multiprocessing', verbose=10

        返回:
            函数执行结果列表，顺序与输入任务相同

        示例:
            >>> runner = JoblibRunner(n_jobs=4)
            >>> results = runner.run(simulation_function, [params1, params2, params3])
        """
        if not tasks:
            if self.verbose >= 1:
                logger.warning("任务列表为空，返回空结果")
            return []

        # 如果n_jobs为1，使用串行执行
        if self.n_jobs == 1:
            if self.verbose >= 1:
                logger.info(f"串行执行 {len(tasks)} 个任务")
            return [func(task) for task in tasks]

        # 并行执行
        if self.verbose >= 1:
            logger.info(f"并行执行 {len(tasks)} 个任务，使用 {self._actual_n_jobs} 个进程")

        try:
            from joblib import Parallel, delayed

            # 准备joblib参数
            joblib_kwargs = {
                'n_jobs': self.n_jobs,
                'verbose': self.verbose * 10,  # joblib使用0-100的verbose级别
            }

            # 添加prefer参数（如果指定）
            if self.prefer is not None:
                joblib_kwargs['prefer'] = self.prefer

            # 合并用户提供的额外参数
            joblib_kwargs.update(kwargs)

            # 执行并行任务
            results = Parallel(**joblib_kwargs)(
                delayed(func)(task) for task in tasks
            )

            if self.verbose >= 1:
                logger.info(f"Joblib并行执行完成: {len(results)} 个结果")

            return results

        except Exception as e:
            logger.error(f"Joblib并行执行失败: {e}")
            # 回退到串行执行
            logger.info("回退到串行执行")
            return [func(task) for task in tasks]

    def map(self, func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
        """
        map函数的别名，与run方法功能相同

        参数:
            func: 要执行的函数
            tasks: 任务列表
            **kwargs: 额外参数

        返回:
            结果列表
        """
        return self.run(func, tasks, **kwargs)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        return False

    @property
    def n_jobs_actual(self) -> int:
        """获取实际使用的CPU核心数"""
        return self._actual_n_jobs

    def __repr__(self) -> str:
        """字符串表示"""
        return f"JoblibRunner(n_jobs={self.n_jobs}, prefer={self.prefer})"


# 便捷函数
def create_progress_bar(iterable, desc: str = "进度", total: int = None,
                       show_stats: bool = True, **kwargs):
    """
    创建增强的进度条

    参数:
        iterable: 可迭代对象
        desc: 进度描述
        total: 总数量（如果为None则从iterable推断）
        show_stats: 是否显示统计信息
        **kwargs: 传递给tqdm的其他参数

    返回:
        tqdm迭代器或原始iterable（如果tqdm不可用）
    """
    if not TQDM_AVAILABLE:
        logger.warning("tqdm不可用，返回原始迭代器")
        return iterable

    # 默认参数
    default_kwargs = {
        'desc': desc,
        'unit': 'it',
        'unit_scale': True,
        'ncols': 120,
        'bar_format': '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    }

    # 合并用户提供的参数
    default_kwargs.update(kwargs)

    # 设置总数
    if total is not None:
        default_kwargs['total'] = total

    return tqdm(iterable, **default_kwargs)


def format_time_duration(seconds: float) -> str:
    """
    格式化时间持续时间为可读字符串

    参数:
        seconds: 时间（秒）

    返回:
        格式化的时间字符串

    示例:
        >>> format_time_duration(3661)
        '1小时1分钟1秒'
        >>> format_time_duration(65)
        '1分钟5秒'
        >>> format_time_duration(30)
        '30秒'
    """
    if seconds < 0:
        return "未知"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if secs > 0 or len(parts) == 0:
        parts.append(f"{secs}秒")

    return ''.join(parts)


def estimate_remaining_time(start_time: float, completed: int, total: int) -> float:
    """
    估计剩余时间

    参数:
        start_time: 开始时间戳（秒）
        completed: 已完成数量
        total: 总数量

    返回:
        预计剩余时间（秒），如果无法估计则返回-1
    """
    if completed == 0 or total == 0:
        return -1

    elapsed = time.time() - start_time
    avg_time_per_task = elapsed / completed
    remaining_tasks = total - completed

    return avg_time_per_task * remaining_tasks


def run_parameter_sweep(
    base_params: Dict[str, Any],
    parameter_ranges: Dict[str, List[float]],
    n_samples: int = 10,
    sampling_method: str = 'grid',
    parallel: bool = False,
    n_jobs: int = -1,
    cache_dir: str = '__sweep_cache__',
    sim_time: float = 7200000
) -> List[SimulationResult]:
    """
    运行参数扫描的便捷函数

    参数:
        base_params: 基础参数字典
        parameter_ranges: 参数范围字典
        n_samples: 采样点数
        sampling_method: 采样方法 ('grid', 'latin_hypercube', 'random')
        parallel: 是否启用并行执行
        n_jobs: 并行任务数
        cache_dir: 缓存目录
        sim_time: 模拟时间（秒）

    返回:
        模拟结果列表
    """
    config = SweepConfig(
        parameter_ranges=parameter_ranges,
        n_samples=n_samples,
        sampling_method=sampling_method,
        parallel=parallel,
        n_jobs=n_jobs,
        cache_dir=cache_dir,
        sim_time=sim_time
    )

    sweep = ParameterSweep(base_params, config)
    return sweep.run()


def export_results_csv(
    results: List[SimulationResult],
    filepath: str,
    include_metadata: bool = True,
    include_time_series_stats: bool = True
) -> None:
    """
    导出模拟结果到CSV文件（便捷函数）

    这是一个独立的便捷函数，用于将SimulationResult列表导出为CSV格式。
    支持元数据、参数和统计信息的导出。

    参数:
        results: SimulationResult对象列表
        filepath: CSV文件输出路径
        include_metadata: 是否包含元数据列（运行时间、缓存状态等）
        include_time_series_stats: 是否包含时间序列统计信息（最大值、最小值、平均值等）

    异常:
        ValueError: 当results为空时
        IOError: 当文件写入失败时
        TypeError: 当参数类型错误时

    示例:
        >>> from parameter_sweep import export_results_csv
        >>> export_results_csv(results, 'sweep_results.csv')
        >>> export_results_csv(results, 'results_simple.csv', include_metadata=False)
    """
    # 验证参数
    if not isinstance(results, list):
        raise TypeError(f"results必须是列表，得到 {type(results)}")

    if not results:
        raise ValueError("results列表不能为空")

    if not isinstance(filepath, str):
        raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

    if not filepath:
        raise ValueError("filepath不能为空")

    # 检查目录是否存在
    import os
    file_dir = os.path.dirname(filepath)
    if file_dir and not os.path.exists(file_dir):
        try:
            os.makedirs(file_dir, exist_ok=True)
            logger.info(f"创建目录: {file_dir}")
        except Exception as e:
            raise IOError(f"无法创建目录 {file_dir}: {e}")

    # 准备数据行
    rows = []
    all_param_keys = set()
    all_state_var_keys = set()
    all_derived_qty_keys = set()

    # 第一次遍历：收集所有可能的键名
    for result in results:
        if result.success:
            all_param_keys.update(result.parameters.keys())
            if result.state_variables:
                all_state_var_keys.update(result.state_variables.keys())
            if result.derived_quantities:
                all_derived_qty_keys.update(result.derived_quantities.keys())

    # 转换为有序列表以保证列顺序一致
    param_keys = sorted(all_param_keys)
    state_var_keys = sorted(all_state_var_keys)
    derived_qty_keys = sorted(all_derived_qty_keys)

    # 第二次遍历：构建数据行
    for i, result in enumerate(results):
        try:
            if not result.success:
                # 失败的结果：仅记录参数和错误信息
                row = {
                    'result_index': i,
                    'success': False,
                    'error_message': result.error_message
                }
                # 添加参数（如果有）
                if result.parameters:
                    for key in param_keys:
                        row[f'param_{key}'] = result.parameters.get(key, '')
                rows.append(row)
                continue

            # 成功的结果
            row = {
                'result_index': i,
                'success': True
            }

            # 添加参数
            for key in param_keys:
                value = result.parameters.get(key, '')
                row[f'param_{key}'] = value

            # 添加状态变量的最终值
            for key in state_var_keys:
                if result.state_variables and key in result.state_variables:
                    var_data = result.state_variables[key]
                    if len(var_data) > 0:
                        row[f'state_{key}_final'] = float(var_data[-1])
                    else:
                        row[f'state_{key}_final'] = None
                else:
                    row[f'state_{key}_final'] = None

            # 添加派生量的最终值和统计信息
            for key in derived_qty_keys:
                if result.derived_quantities and key in result.derived_quantities:
                    qty_data = result.derived_quantities[key]
                    if len(qty_data) > 0:
                        row[f'derived_{key}_final'] = float(qty_data[-1])

                        if include_time_series_stats:
                            row[f'derived_{key}_max'] = float(np.max(qty_data))
                            row[f'derived_{key}_min'] = float(np.min(qty_data))
                            row[f'derived_{key}_mean'] = float(np.mean(qty_data))
                            row[f'derived_{key}_std'] = float(np.std(qty_data))
                    else:
                        row[f'derived_{key}_final'] = None
                        if include_time_series_stats:
                            row[f'derived_{key}_max'] = None
                            row[f'derived_{key}_min'] = None
                            row[f'derived_{key}_mean'] = None
                            row[f'derived_{key}_std'] = None
                else:
                    row[f'derived_{key}_final'] = None
                    if include_time_series_stats:
                        row[f'derived_{key}_max'] = None
                        row[f'derived_{key}_min'] = None
                        row[f'derived_{key}_mean'] = None
                        row[f'derived_{key}_std'] = None

            # 添加元数据
            if include_metadata:
                row['runtime_seconds'] = result.metadata.get('runtime', 0)
                row['from_cache'] = result.metadata.get('from_cache', False)
                row['final_swelling'] = result.metadata.get('final_swelling', None)
                row['final_Rcb'] = result.metadata.get('final_Rcb', None)
                row['final_Rcf'] = result.metadata.get('final_Rcf', None)

            rows.append(row)

        except Exception as e:
            logger.warning(f"处理结果 {i} 时出错: {e}")
            rows.append({
                'result_index': i,
                'success': False,
                'error_message': f"数据处理失败: {str(e)}"
            })

    # 创建DataFrame并写入CSV
    try:
        df = pd.DataFrame(rows)

        # 设置列的顺序：result_index在前，然后是参数，然后是状态变量，然后是派生量，最后是元数据
        column_order = ['result_index', 'success']

        # 参数列
        param_cols = [f'param_{key}' for key in param_keys]
        column_order.extend(param_cols)

        # 状态变量列
        state_cols = [f'state_{key}_final' for key in state_var_keys]
        column_order.extend(state_cols)

        # 派生量列（基础+统计）
        derived_cols = []
        for key in derived_qty_keys:
            derived_cols.append(f'derived_{key}_final')
            if include_time_series_stats:
                derived_cols.extend([
                    f'derived_{key}_max',
                    f'derived_{key}_min',
                    f'derived_{key}_mean',
                    f'derived_{key}_std'
                ])
        column_order.extend(derived_cols)

        # 元数据列
        if include_metadata:
            metadata_cols = ['runtime_seconds', 'from_cache', 'final_swelling', 'final_Rcb', 'final_Rcf']
            column_order.extend(metadata_cols)

        # 添加错误信息列（如果有失败的结果）
        if any('error_message' in row for row in rows):
            column_order.append('error_message')

        # 重新排列列顺序（仅包含存在的列）
        existing_columns = [col for col in column_order if col in df.columns]
        other_columns = [col for col in df.columns if col not in column_order]
        df = df[existing_columns + other_columns]

        # 写入CSV
        df.to_csv(filepath, index=False, encoding='utf-8')

        # 统计信息
        n_success = sum(1 for r in results if r.success)
        n_failed = len(results) - n_success

        logger.info(f"结果已导出到CSV: {filepath}")
        logger.info(f"  - 总结果数: {len(results)}")
        logger.info(f"  - 成功: {n_success} ({n_success/len(results)*100:.1f}%)")
        logger.info(f"  - 失败: {n_failed} ({n_failed/len(results)*100:.1f}%)")
        logger.info(f"  - 列数: {len(df.columns)}")
        logger.info(f"  - 行数: {len(df)}")

    except PermissionError:
        logger.error(f"文件权限错误，无法写入: {filepath}")
        raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限")
    except Exception as e:
        logger.error(f"导出CSV失败: {e}")
        import traceback
        logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
        raise


def export_results_netcdf(
    results: List[SimulationResult],
    filepath: str,
    include_time_series: bool = True,
    compression: int = 4,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    导出模拟结果到NetCDF文件（便捷函数）

    这是一个独立的便捷函数，用于将SimulationResult列表导出为NetCDF格式。
    NetCDF特别适合存储多维科学数据，特别是带有时间序列的数据。

    参数:
        results: SimulationResult对象列表
        filepath: NetCDF文件输出路径 (.nc或.nc4)
        include_time_series: 是否包含完整的时间序列数据和统计信息
        compression: 压缩级别 (0-9, 0=无压缩, 4=默认, 9=最大压缩)
        metadata: 可选的元数据字典，将添加为全局属性

    异常:
        ImportError: 当netCDF4库不可用时抛出
        ValueError: 当results为空时
        IOError: 当文件写入失败时
        TypeError: 当参数类型错误时

    示例:
        >>> from parameter_sweep import export_results_netcdf
        >>> export_results_netcdf(results, 'sweep_results.nc')
        >>> export_results_netcdf(results, 'results.nc4', include_time_series=True, compression=6)
        >>> export_results_netcdf(results, 'output.nc', metadata={'author': 'Research Team'})
    """
    # 验证netCDF4可用性
    if not NETCDF_AVAILABLE:
        raise ImportError("netCDF4库不可用。请安装: pip install netCDF4")

    # 验证参数
    if not isinstance(results, list):
        raise TypeError(f"results必须是列表，得到 {type(results)}")

    if not results:
        raise ValueError("results列表不能为空")

    if not isinstance(filepath, str):
        raise TypeError(f"filepath必须是字符串，得到 {type(filepath)}")

    if not filepath:
        raise ValueError("filepath不能为空")

    if not isinstance(compression, int) or compression < 0 or compression > 9:
        raise ValueError(f"compression必须是0-9的整数，得到 {compression}")

    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError(f"metadata必须是字典或None，得到 {type(metadata)}")

    # 检查目录是否存在
    import os
    file_dir = os.path.dirname(filepath)
    if file_dir and not os.path.exists(file_dir):
        try:
            os.makedirs(file_dir, exist_ok=True)
            logger.info(f"创建目录: {file_dir}")
        except Exception as e:
            raise IOError(f"无法创建目录 {file_dir}: {e}")

    try:
        # 创建NetCDF文件
        with Dataset(filepath, 'w', format='NETCDF4') as nc:
            # 添加全局属性
            nc.title = 'Parameter Sweep Results'
            nc.institution = 'Gas Swelling Model Simulation'
            nc.source = 'parameter_sweep.export_results_netcdf'
            nc.history = f'Created {time.ctime(time.time())}'
            nc.Conventions = 'CF-1.6'

            # 添加用户提供的元数据
            if metadata:
                for key, value in metadata.items():
                    try:
                        # 设置全局属性（自动转换为字符串）
                        nc.setncattr(key, str(value))
                    except Exception as e:
                        logger.warning(f"无法添加元数据 {key}: {e}")

            # 添加基本统计元数据
            nc.total_simulations = len(results)
            nc.successful_simulations = sum(1 for r in results if r.success)
            nc.failed_simulations = sum(1 for r in results if not r.success)

            # 定义维度
            nc.createDimension('n_simulations', len(results))

            # 收集所有参数名和变量名
            all_param_names = set()
            all_state_var_names = set()
            all_derived_qty_names = set()
            time_length = 0

            for result in results:
                if result.success:
                    all_param_names.update(result.parameters.keys())
                    if result.state_variables:
                        all_state_var_names.update(result.state_variables.keys())
                    if result.derived_quantities:
                        all_derived_qty_names.update(result.derived_quantities.keys())
                    if len(result.time) > time_length:
                        time_length = len(result.time)

            # 如果有时间序列数据，创建time维度
            if include_time_series and time_length > 0:
                nc.createDimension('time', time_length)
                time_var = nc.createVariable('time', 'f8', ('time',), zlib=True, complevel=compression)
                time_var.units = 'seconds'
                time_var.long_name = 'Simulation time'
                time_var.standard_name = 'time'
                # 使用第一个成功结果的时间数组
                for result in results:
                    if result.success and len(result.time) > 0:
                        time_var[:] = result.time
                        break

            # 创建基本变量
            # 模拟索引
            sim_idx_var = nc.createVariable('simulation_index', 'i4', ('n_simulations',), zlib=True, complevel=compression)
            sim_idx_var[:] = np.arange(len(results))
            sim_idx_var.long_name = 'Simulation index'

            # 成功标志
            success_var = nc.createVariable('success', 'i1', ('n_simulations',), zlib=True, complevel=compression)
            success_var[:] = np.array([int(r.success) for r in results], dtype='i1')
            success_var.long_name = 'Simulation success flag'

            # 运行时间
            runtime_var = nc.createVariable('runtime', 'f8', ('n_simulations',), zlib=True, complevel=compression)
            runtime_var[:] = np.array([r.metadata.get('runtime', np.nan) for r in results], dtype='f8')
            runtime_var.units = 'seconds'
            runtime_var.long_name = 'Simulation runtime'

            # 缓存标志
            cache_var = nc.createVariable('from_cache', 'i1', ('n_simulations',), zlib=True, complevel=compression)
            cache_var[:] = np.array([int(r.metadata.get('from_cache', False)) for r in results], dtype='i1')
            cache_var.long_name = 'Result from cache flag'

            # 导出参数
            param_names = sorted(all_param_names)
            for param_name in param_names:
                var = nc.createVariable(
                    f'param_{param_name}',
                    'f8',
                    ('n_simulations',),
                    zlib=True,
                    complevel=compression,
                    fill_value=np.nan
                )
                var.long_name = f'Parameter: {param_name}'

                data = []
                for result in results:
                    if result.parameters and param_name in result.parameters:
                        data.append(result.parameters[param_name])
                    else:
                        data.append(np.nan)
                var[:] = np.array(data, dtype='f8')

            # 导出状态变量最终值
            state_var_names = sorted(all_state_var_names)
            for var_name in state_var_names:
                var = nc.createVariable(
                    f'state_{var_name}_final',
                    'f8',
                    ('n_simulations',),
                    zlib=True,
                    complevel=compression,
                    fill_value=np.nan
                )
                var.long_name = f'State variable final value: {var_name}'

                data = []
                for result in results:
                    if result.success and result.state_variables and var_name in result.state_variables:
                        var_data = result.state_variables[var_name]
                        if len(var_data) > 0:
                            data.append(float(var_data[-1]))
                        else:
                            data.append(np.nan)
                    else:
                        data.append(np.nan)
                var[:] = np.array(data, dtype='f8')

                # 如果需要，添加完整时间序列
                if include_time_series and time_length > 0:
                    ts_var = nc.createVariable(
                        f'state_{var_name}_timeseries',
                        'f8',
                        ('n_simulations', 'time'),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    ts_var.long_name = f'State variable time series: {var_name}'

                    ts_data = np.full((len(results), time_length), np.nan, dtype='f8')
                    for i, result in enumerate(results):
                        if result.success and result.state_variables and var_name in result.state_variables:
                            var_data = result.state_variables[var_name]
                            if len(var_data) > 0:
                                actual_len = min(len(var_data), time_length)
                                ts_data[i, :actual_len] = var_data[:actual_len]

                    ts_var[:] = ts_data

            # 导出派生量
            derived_qty_names = sorted(all_derived_qty_names)
            for qty_name in derived_qty_names:
                # 最终值
                var = nc.createVariable(
                    f'derived_{qty_name}_final',
                    'f8',
                    ('n_simulations',),
                    zlib=True,
                    complevel=compression,
                    fill_value=np.nan
                )
                var.long_name = f'Derived quantity final value: {qty_name}'

                data = []
                for result in results:
                    if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                        qty_data = result.derived_quantities[qty_name]
                        if len(qty_data) > 0:
                            data.append(float(qty_data[-1]))
                        else:
                            data.append(np.nan)
                    else:
                        data.append(np.nan)
                var[:] = np.array(data, dtype='f8')

                # 时间序列统计
                if include_time_series:
                    # 最大值
                    var_max = nc.createVariable(
                        f'derived_{qty_name}_max',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var_max.long_name = f'Derived quantity maximum: {qty_name}'
                    data_max = []
                    for result in results:
                        if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                            qty_data = result.derived_quantities[qty_name]
                            if len(qty_data) > 0:
                                data_max.append(float(np.max(qty_data)))
                            else:
                                data_max.append(np.nan)
                        else:
                            data_max.append(np.nan)
                    var_max[:] = np.array(data_max, dtype='f8')

                    # 最小值
                    var_min = nc.createVariable(
                        f'derived_{qty_name}_min',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var_min.long_name = f'Derived quantity minimum: {qty_name}'
                    data_min = []
                    for result in results:
                        if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                            qty_data = result.derived_quantities[qty_name]
                            if len(qty_data) > 0:
                                data_min.append(float(np.min(qty_data)))
                            else:
                                data_min.append(np.nan)
                        else:
                            data_min.append(np.nan)
                    var_min[:] = np.array(data_min, dtype='f8')

                    # 平均值
                    var_mean = nc.createVariable(
                        f'derived_{qty_name}_mean',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var_mean.long_name = f'Derived quantity mean: {qty_name}'
                    data_mean = []
                    for result in results:
                        if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                            qty_data = result.derived_quantities[qty_name]
                            if len(qty_data) > 0:
                                data_mean.append(float(np.mean(qty_data)))
                            else:
                                data_mean.append(np.nan)
                        else:
                            data_mean.append(np.nan)
                    var_mean[:] = np.array(data_mean, dtype='f8')

                    # 标准差
                    var_std = nc.createVariable(
                        f'derived_{qty_name}_std',
                        'f8',
                        ('n_simulations',),
                        zlib=True,
                        complevel=compression,
                        fill_value=np.nan
                    )
                    var_std.long_name = f'Derived quantity std: {qty_name}'
                    data_std = []
                    for result in results:
                        if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                            qty_data = result.derived_quantities[qty_name]
                            if len(qty_data) > 1:
                                data_std.append(float(np.std(qty_data)))
                            else:
                                data_std.append(np.nan)
                        else:
                            data_std.append(np.nan)
                    var_std[:] = np.array(data_std, dtype='f8')

                    # 完整时间序列
                    if time_length > 0:
                        ts_var = nc.createVariable(
                            f'derived_{qty_name}_timeseries',
                            'f8',
                            ('n_simulations', 'time'),
                            zlib=True,
                            complevel=compression,
                            fill_value=np.nan
                        )
                        ts_var.long_name = f'Derived quantity time series: {qty_name}'

                        ts_data = np.full((len(results), time_length), np.nan, dtype='f8')
                        for i, result in enumerate(results):
                            if result.success and result.derived_quantities and qty_name in result.derived_quantities:
                                qty_data = result.derived_quantities[qty_name]
                                if len(qty_data) > 0:
                                    actual_len = min(len(qty_data), time_length)
                                    ts_data[i, :actual_len] = qty_data[:actual_len]

                        ts_var[:] = ts_data

        # 统计信息
        n_success = sum(1 for r in results if r.success)
        n_failed = len(results) - n_success

        logger.info(f"结果已导出到NetCDF: {filepath}")
        logger.info(f"  - 总结果数: {len(results)}")
        logger.info(f"  - 成功: {n_success} ({n_success/len(results)*100:.1f}%)")
        logger.info(f"  - 失败: {n_failed} ({n_failed/len(results)*100:.1f}%)")
        logger.info(f"  - 参数: {len(param_names)}")
        logger.info(f"  - 状态变量: {len(state_var_names)}")
        logger.info(f"  - 派生量: {len(derived_qty_names)}")
        logger.info(f"  - 时间序列: {'是' if include_time_series else '否'}")
        logger.info(f"  - 时间点数: {time_length}")
        logger.info(f"  - 压缩级别: {compression}")

    except PermissionError:
        logger.error(f"文件权限错误，无法写入: {filepath}")
        raise PermissionError(f"无法写入文件 {filepath}，请检查文件权限")
    except Exception as e:
        logger.error(f"导出NetCDF失败: {e}")
        import traceback
        logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
        raise


if __name__ == '__main__':
    # 测试代码
    print("参数扫描模块已导入")

    # 测试配置类
    config = SweepConfig()
    print(f"默认配置: {config}")

    # 测试缓存类
    cache = SimulationCache()
    print(f"缓存目录: {cache.cache_dir}")

    # 测试参数扫描器（需要有效的参数）
    print("运行基本测试...")
    try:
        from params.parameters import create_default_parameters
        params = create_default_parameters()
        sweep = ParameterSweep(params)
        print("参数扫描器创建成功")
    except Exception as e:
        print(f"测试失败（预期行为，如果参数模块不可用）: {e}")
