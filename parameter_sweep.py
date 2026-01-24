"""
参数扫描模块 - Parameter Sweep Module

提供多参数扫描、缓存、并行执行和智能采样功能。
Provides multi-parameter sweep, caching, parallel execution, and smart sampling capabilities.
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
        valid_sampling = ['grid', 'latin_hypercube', 'random']
        if self.sampling_method not in valid_sampling:
            raise ValueError(f"sampling_method must be one of {valid_sampling}, got {self.sampling_method}")


@dataclass
class SimulationResult:
    """
    单次模拟结果类

    属性:
        parameters: 使用的参数字典
        time: 时间数组
        state_variables: 状态变量字典
        derived_quantities: 派生量字典（气泡半径、肿胀率等）
        metadata: 元数据（运行时间、收敛信息等）
        success: 模拟是否成功
        error_message: 错误信息（如果失败）
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
    """

    def __init__(self, total_tasks: int, desc: str = "进度"):
        """
        初始化进度跟踪器

        参数:
            total_tasks: 总任务数
            desc: 进度描述
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

    支持多参数网格扫描、结果缓存、并行执行和进度跟踪。
    """

    def __init__(self, base_params: Dict[str, Any], config: Optional[SweepConfig] = None):
        """
        初始化参数扫描器

        参数:
            base_params: 基础参数字典
            config: 扫描配置，如果为None则使用默认配置
        """
        self.base_params = base_params.copy()
        self.config = config if config is not None else SweepConfig()
        self.results: List[SimulationResult] = []

        # 初始化缓存
        if self.config.cache_enabled:
            self.cache = SimulationCache(cache_dir=self.config.cache_dir)
        else:
            self.cache = None
            logger.info("缓存已禁用")

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
        运行单次模拟

        参数:
            params: 参数字典
            show_progress: 是否显示单个模拟的进度（仅用于长时间运行的模拟）

        返回:
            模拟结果
        """
        # 检查缓存
        if self.cache is not None:
            cached_result = self.cache.get(params)
            if cached_result is not None:
                # 缓存命中，记录元数据
                cached_result.metadata['from_cache'] = True
                return cached_result

        # 创建模型并运行模拟
        start_time = time.time()
        try:
            model = self.ModelClass(params)

            # 设置时间点
            t_eval = np.linspace(0, self.config.sim_time, 100)

            # 求解
            result = model.solve(
                t_span=(0, self.config.sim_time),
                t_eval=t_eval
            )

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

            # 存入缓存
            if self.cache is not None:
                self.cache.set(params, sim_result)

            return sim_result

        except Exception as e:
            logger.error(f"模拟失败 (参数: {params}): {e}")
            return SimulationResult(
                parameters=params.copy(),
                success=False,
                error_message=str(e),
                metadata={'runtime': time.time() - start_time, 'from_cache': False}
            )

    def generate_parameter_sets(self) -> List[Dict[str, Any]]:
        """
        生成参数集合

        返回:
            参数字典列表
        """
        if not self.config.parameter_ranges:
            logger.info("未指定参数范围，仅使用基础参数")
            return [self.base_params.copy()]

        # 导入采样策略
        try:
            from sampling_strategies import grid_sampling, latin_hypercube_sampling, random_sampling
        except ImportError:
            logger.warning("sampling_strategies模块不可用，使用简单的网格采样")
            # 简单的网格采样实现
            param_sets = []
            param_names = list(self.config.parameter_ranges.keys())
            param_values = [self.config.parameter_ranges[name] for name in param_names]

            # 生成所有组合
            import itertools
            for combination in itertools.product(*param_values):
                params = self.base_params.copy()
                for name, value in zip(param_names, combination):
                    params[name] = value
                param_sets.append(params)

            return param_sets

        # 使用采样策略模块
        if self.config.sampling_method == 'grid':
            return grid_sampling(self.base_params, self.config.parameter_ranges)
        elif self.config.sampling_method == 'latin_hypercube':
            return latin_hypercube_sampling(
                self.base_params,
                self.config.parameter_ranges,
                n_samples=self.config.n_samples
            )
        elif self.config.sampling_method == 'random':
            return random_sampling(
                self.base_params,
                self.config.parameter_ranges,
                n_samples=self.config.n_samples
            )
        else:
            raise ValueError(f"未知的采样方法: {self.config.sampling_method}")

    def run(self) -> List[SimulationResult]:
        """
        运行参数扫描

        返回:
            模拟结果列表
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

    def to_dataframe(self) -> pd.DataFrame:
        """
        将结果转换为pandas DataFrame

        返回:
            包含所有模拟结果的DataFrame
        """
        if not self.results:
            logger.warning("没有结果可转换")
            return pd.DataFrame()

        rows = []
        for result in self.results:
            if not result.success:
                continue

            row = result.parameters.copy()
            row.update({
                'success': result.success,
                'runtime': result.metadata.get('runtime', 0),
                'final_swelling': result.metadata.get('final_swelling', 0),
                'final_Rcb': result.metadata.get('final_Rcb', 0),
                'final_Rcf': result.metadata.get('final_Rcf', 0)
            })
            rows.append(row)

        df = pd.DataFrame(rows)
        logger.info(f"结果已转换为DataFrame: {len(df)} 行 × {len(df.columns)} 列")
        return df

    def export_csv(self, filepath: str) -> None:
        """
        导出结果到CSV文件

        参数:
            filepath: CSV文件路径
        """
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        logger.info(f"结果已导出到: {filepath}")


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
