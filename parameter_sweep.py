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

    def _run_single_simulation(self, params: Dict[str, Any]) -> SimulationResult:
        """
        运行单次模拟

        参数:
            params: 参数字典

        返回:
            模拟结果
        """
        # 检查缓存
        if self.cache is not None:
            cached_result = self.cache.get(params)
            if cached_result is not None:
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
                    'final_Rcf': Rcf[-1] if len(Rcf) > 0 else 0.0
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
                metadata={'runtime': time.time() - start_time}
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

        if self.config.parallel and JOBLIB_AVAILABLE:
            # 并行执行
            logger.info(f"并行任务数: {self.config.n_jobs}")
            # 根据tqdm是否可用选择迭代器
            iter_params = tqdm(param_sets, desc="参数扫描进度") if TQDM_AVAILABLE else param_sets
            self.results = Parallel(n_jobs=self.config.n_jobs)(
                delayed(self._run_single_simulation)(params)
                for params in iter_params
            )
        else:
            # 串行执行
            if TQDM_AVAILABLE:
                param_sets = tqdm(param_sets, desc="参数扫描进度")

            for params in param_sets:
                result = self._run_single_simulation(params)
                self.results.append(result)

        elapsed_time = time.time() - start_time
        n_success = sum(1 for r in self.results if r.success)
        n_failed = len(self.results) - n_success

        logger.info("======== 参数扫描完成 ========")
        logger.info(f"总耗时: {elapsed_time:.2f} 秒")
        logger.info(f"成功: {n_success}/{n_simulations}")
        logger.info(f"失败: {n_failed}/{n_simulations}")

        if n_failed > 0:
            logger.warning(f"有 {n_failed} 次模拟失败")

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
