# Repository Guide / 仓库结构与使用说明

This guide is the long-form companion to the short repository overview in the repo-root `README.md`.

本指南是根目录 `README.md` 中“仓库导览”章节的完整版，适合第一次进入仓库、想快速定位功能入口，或准备参与开发的读者。

## 1. What This Repo Contains / 这个仓库包含什么

### 中文

这个仓库是一个以 [`gas_swelling`](../../gas_swelling/__init__.py) 包为核心的科学计算项目，用于模拟金属核燃料中裂变气体气泡演化与肿胀行为。

当前主线是**包化结构**：

- 运行入口以 `gas_swelling` 包、`examples/`、`docs/` 和 `tests/` 为主
- 根目录的历史脚本和论文材料仍可作为参考，但不应再被视为主要 API 或主要使用入口

### English

This repository is a scientific computing project centered on the [`gas_swelling`](../../gas_swelling/__init__.py) package for simulating fission gas bubble evolution and swelling behavior in metallic nuclear fuels.

The current source of truth is the **packaged codebase**:

- primary entry points live in the `gas_swelling` package, `examples/`, `docs/`, and `tests/`
- legacy root-level scripts and paper notes remain useful as references, but they are no longer the main public API

## 2. Repository Map / 仓库地图

```text
gas_swelling/
├── models/         core model entry points and variants
├── ode/            rate-equation systems
├── physics/        reusable physics utilities
├── solvers/        solver wrappers and numerical helpers
├── visualization/  plotting and post-processing
├── analysis/       sensitivity analysis and metrics
├── validation/     datasets, metrics, reproduction scripts
├── params/         parameter defaults and dataclasses
└── io/             debug/history/output helpers

examples/           runnable examples and tutorials
tests/              pytest suite
docs/               long-form documentation
notebooks/          exploratory notebooks
```

### 中文

- `gas_swelling/models`: 模型入口与变体；重点看 `refactored_model.py`、`qssa_model.py`、`hybrid_qssa_model.py`、`radial_model.py`
- `gas_swelling/ode`: 速率方程实现；重点看 `rate_equations.py` 和 `qssa_rate_equations.py`
- `gas_swelling/physics`: 压力、输运、热平衡等基础物理计算
- `gas_swelling/solvers`: 数值求解包装层，如 `rk23_solver.py`
- `gas_swelling/visualization`: 各类绘图与结果展示
- `gas_swelling/analysis`: sensitivity analysis、指标和相关 CLI
- `gas_swelling/validation`: 实验数据、验证指标、复现实验脚本
- `gas_swelling/params`: `create_default_parameters()` 与 dataclass 参数定义
- `examples`: 最适合跟跑的脚本入口
- `tests`: 当前行为的可执行规范
- `docs`: 教程、参数说明、故障排查和专题指南

### English

- `gas_swelling/models`: model entry points and variants; start with `refactored_model.py`, `qssa_model.py`, `hybrid_qssa_model.py`, and `radial_model.py`
- `gas_swelling/ode`: rate-equation implementations; the main files are `rate_equations.py` and `qssa_rate_equations.py`
- `gas_swelling/physics`: reusable physics utilities such as pressure, transport, and thermal calculations
- `gas_swelling/solvers`: solver wrappers and numerical helpers
- `gas_swelling/visualization`: plotting and post-processing
- `gas_swelling/analysis`: sensitivity analysis, metrics, and related CLI helpers
- `gas_swelling/validation`: experimental datasets, validation metrics, and reproduction scripts
- `gas_swelling/params`: parameter defaults via `create_default_parameters()` plus dataclass definitions
- `examples`: the best place to start running the repo
- `tests`: the executable specification of current behavior
- `docs`: tutorials, references, troubleshooting, and specialized guides

## 3. How to Use the Repo / 如何使用这个仓库

### 中文

按你的目标，推荐这样进入：

- 只想快速跑模型
  - 先看 repo 根目录里的 `QUICKSTART.md`
  - 也可以配合 [`docs/tutorials/30minute_quickstart.md`](../tutorials/30minute_quickstart.md)
  - 运行 [`examples/quickstart_simple.py`](../../examples/quickstart_simple.py)
- 想改参数或做 sweep
  - 看 [`gas_swelling/params/parameters.py`](../../gas_swelling/params/parameters.py)
  - 看 [`examples/quickstart_tutorial.py`](../../examples/quickstart_tutorial.py) 和 [`examples/temperature_sweep_plotting.py`](../../examples/temperature_sweep_plotting.py)
- 想看 QSSA / Hybrid QSSA
  - 看 [`gas_swelling/models/qssa_model.py`](../../gas_swelling/models/qssa_model.py)
  - 看 [`gas_swelling/models/hybrid_qssa_model.py`](../../gas_swelling/models/hybrid_qssa_model.py)
  - 看 [`examples/qssa_benchmark.py`](../../examples/qssa_benchmark.py)
- 想用 1D radial model
  - 看 [`gas_swelling/models/radial_model.py`](../../gas_swelling/models/radial_model.py)
  - 看 [`docs/1d_radial_model.md`](../1d_radial_model.md)
  - 看 [`examples/radial_simulation_tutorial.py`](../../examples/radial_simulation_tutorial.py)
- 想做 sensitivity analysis
  - 看 [`gas_swelling/analysis/sensitivity.py`](../../gas_swelling/analysis/sensitivity.py)
  - 看 [`docs/sensitivity_analysis_guide.md`](../sensitivity_analysis_guide.md)
  - 看 [`examples/sensitivity_analysis_tutorial.py`](../../examples/sensitivity_analysis_tutorial.py)
- 想复现实验验证图
  - 看 `gas_swelling/validation/scripts`
  - 看 [`docs/validation_guide.md`](../validation_guide.md)

### English

Choose your entry point by intent:

- If you want to run the model quickly
  - start with the repo-root `QUICKSTART.md`
  - optionally pair it with [`docs/tutorials/30minute_quickstart.md`](../tutorials/30minute_quickstart.md)
  - run [`examples/quickstart_simple.py`](../../examples/quickstart_simple.py)
- If you want to edit parameters or run sweeps
  - read [`gas_swelling/params/parameters.py`](../../gas_swelling/params/parameters.py)
  - use [`examples/quickstart_tutorial.py`](../../examples/quickstart_tutorial.py) and [`examples/temperature_sweep_plotting.py`](../../examples/temperature_sweep_plotting.py)
- If you want to inspect QSSA / Hybrid QSSA
  - read [`gas_swelling/models/qssa_model.py`](../../gas_swelling/models/qssa_model.py)
  - read [`gas_swelling/models/hybrid_qssa_model.py`](../../gas_swelling/models/hybrid_qssa_model.py)
  - run [`examples/qssa_benchmark.py`](../../examples/qssa_benchmark.py)
- If you want the 1D radial model
  - read [`gas_swelling/models/radial_model.py`](../../gas_swelling/models/radial_model.py)
  - read [`docs/1d_radial_model.md`](../1d_radial_model.md)
  - run [`examples/radial_simulation_tutorial.py`](../../examples/radial_simulation_tutorial.py)
- If you want sensitivity analysis
  - read [`gas_swelling/analysis/sensitivity.py`](../../gas_swelling/analysis/sensitivity.py)
  - read [`docs/sensitivity_analysis_guide.md`](../sensitivity_analysis_guide.md)
  - run [`examples/sensitivity_analysis_tutorial.py`](../../examples/sensitivity_analysis_tutorial.py)
- If you want validation / figure reproduction
  - use `gas_swelling/validation/scripts`
  - read [`docs/validation_guide.md`](../validation_guide.md)

## 4. Recommended Workflows / 推荐工作流

### 普通用户 / General user

```bash
# 1. Use the repo virtualenv / 使用仓库虚拟环境
./.venv/bin/python examples/quickstart_simple.py

# 2. Try a guided example / 跑带讲解示例
./.venv/bin/python examples/quickstart_tutorial.py
```

```python
from gas_swelling import GasSwellingModel, create_default_parameters

params = create_default_parameters()
model = GasSwellingModel(params)
result = model.solve()
print(result['swelling'][-1])
```

Recommended flow:

1. create defaults with `create_default_parameters()`
2. modify a few keys in the returned dict
3. run the model
4. inspect result arrays or move to `examples/` and `visualization/`

### 开发者 / Developer

```bash
# Focused test / 跑单文件
./scripts/test_safe.sh tests/test_import.py

# Related subset with matplotlib config / 相关子集
./.venv/bin/python scripts/test_safe.py --timeout 600 -- tests/test_distribution_plots.py tests/test_visualization_e2e.py

# Full suite / 全量测试
./scripts/test_safe.sh -q
```

Recommended flow:

1. start from a failing or relevant test in `tests/`
2. trace imports back into `gas_swelling/`
3. run a targeted subset
4. finish with the full suite when your change stabilizes

### 文档构建 / Documentation build

```bash
# Install docs dependencies / 安装文档依赖
./.venv/bin/python -m pip install -r docs/requirements.txt

# Fast docs smoke / 文档快速检查
make -C docs dummy-offline

# Full HTML build / 生成 HTML
make -C docs html-offline
```

Notes:

1. `html-offline` uses the repo virtualenv by default through `docs/Makefile`
2. offline mode disables external intersphinx fetches, which is useful in restricted environments
3. generated HTML lands in `docs/_build/html/`

## 5. Current Model Variants / 当前模型变体

### 中文

- 0D 主入口通过 [`GasSwellingModel`](../../gas_swelling/__init__.py) 暴露，底层支持：
  - `model_backend = 'full'`
  - `model_backend = 'qssa'`
  - `model_backend = 'hybrid_qssa'`
- 1D radial model 通过 [`RadialGasSwellingModel`](../../gas_swelling/models/radial_model.py) 提供：
  - 默认 `radial_solver_mode = 'decoupled'`，适合日常使用和测试
  - 可选 `radial_solver_mode = 'coupled'`，保留完整耦合径向 ODE 路径

### English

- The 0D package entry point is exposed as [`GasSwellingModel`](../../gas_swelling/__init__.py), with:
  - `model_backend = 'full'`
  - `model_backend = 'qssa'`
  - `model_backend = 'hybrid_qssa'`
- The 1D radial model is provided by [`RadialGasSwellingModel`](../../gas_swelling/models/radial_model.py):
  - default `radial_solver_mode = 'decoupled'` for practical turnaround and testing
  - optional `radial_solver_mode = 'coupled'` to keep the original coupled radial ODE path available

## 6. Testing Guide / 测试说明

### 中文

当前推荐命令：

```bash
# 单文件
./scripts/test_safe.sh tests/test_import.py

# 相关子集
./scripts/test_safe.sh tests/test_docstring_examples.py

# 全量
./scripts/test_safe.sh -q
```

最近一次已确认的本地全量结果是：**987 passed, 2 skipped**。如果你在此之后继续修改代码，请重新运行 `./scripts/test_safe.sh -q` 以刷新最新汇总。

### English

Recommended commands:

```bash
# Single file
./scripts/test_safe.sh tests/test_import.py

# Related subset
./scripts/test_safe.sh tests/test_docstring_examples.py

# Full suite
./scripts/test_safe.sh -q
```

The latest confirmed local full-suite result is **987 passed, 2 skipped**. If you make further code changes, rerun `./scripts/test_safe.sh -q` to refresh that summary in your own environment.

## 7. Important Notes / 重要说明

### 中文

- 仓库里仍然有一些旧文档会提到 “10-variable model” 或旧版流程；这通常是**理论原始表述**，不一定等于当前包实现
- 当前代码里很多地方已经采用 17 状态表示、QSSA / Hybrid QSSA 变体，以及默认 `decoupled` 的 radial 路径
- 遇到文档冲突时，以 `gas_swelling` 包代码和 `tests/` 为准

### English

- Some older documents still refer to a “10-variable model” or legacy workflows; those are often descriptions of the original theory, not the exact current package implementation
- The current codebase includes a 17-state packaged representation, QSSA / Hybrid QSSA variants, and a default `decoupled` radial execution path
- When documentation conflicts, prefer the `gas_swelling` package code and the `tests/` directory as the source of truth
