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

    def to_dataframe(self, include_time_series: bool = False) -> pd.DataFrame:
        """
        将结果转换为pandas DataFrame

        参数:
            include_time_series: 是否包含时间序列数据的统计信息

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
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 主结果表
                df = self.to_dataframe(include_time_series=True)
                df.to_excel(writer, sheet_name='Results', index=False)

                # 仅成功的模拟结果
                successful_df = df[df['success'] == True]
                successful_df.to_excel(writer, sheet_name='Successful Only', index=False)

                # 汇总统计
                if include_summary and not df.empty:
                    summary = self.get_summary_statistics()
                    summary.to_excel(writer, sheet_name='Summary Statistics')

                    # 按关键参数汇总
                    if 'temperature' in df.columns:
                        temp_summary = self.aggregate_by_parameter('temperature', 'mean')
                        temp_summary.to_excel(writer, sheet_name='By Temperature')

                logger.info(f"结果已导出到Excel: {filepath}")
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            raise

    def export_json(self, filepath: str, include_time_series: bool = False) -> None:
        """
        导出结果到JSON文件

        参数:
            filepath: JSON文件路径
            include_time_series: 是否包含完整的时间序列数据
        """
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
            for result in self.results:
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

            # 添加汇总统计
            df = self.to_dataframe()
            if not df.empty:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                data['summary'] = {
                    'total_runs': len(self.results),
                    'successful_runs': sum(1 for r in self.results if r.success),
                    'failed_runs': sum(1 for r in self.results if not r.success),
                    'statistics': df[numeric_cols].describe().to_dict()
                }

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=lambda x: float(x) if isinstance(x, (np.integer, np.floating)) else str(x))

            logger.info(f"结果已导出到JSON: {filepath}")
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            raise

    def export_parquet(self, filepath: str) -> None:
        """
        导出结果到Parquet文件（高效的二进制格式）

        参数:
            filepath: Parquet文件路径
        """
        try:
            df = self.to_dataframe(include_time_series=True)
            df.to_parquet(filepath, index=False)
            logger.info(f"结果已导出到Parquet: {filepath}")
        except ImportError:
            logger.error("pyarrow或fastparquet未安装，无法导出Parquet格式")
            raise
        except Exception as e:
            logger.error(f"导出Parquet失败: {e}")
            raise

    def export_csv(self, filepath: str, include_time_series: bool = False) -> None:
        """
        导出结果到CSV文件

        参数:
            filepath: CSV文件路径
            include_time_series: 是否包含时间序列数据的统计信息
        """
        df = self.to_dataframe(include_time_series=include_time_series)
        df.to_csv(filepath, index=False)
        logger.info(f"结果已导出到CSV: {filepath} ({len(df)} 行)")


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
