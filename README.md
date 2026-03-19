# Gas Swelling Model for Nuclear Fuel Materials

![Tests](https://github.com/Etoile04/gas-swelling-model/workflows/Tests/badge.svg)
![codecov](https://codecov.io/gh/Etoile04/gas-swelling-model/branch/main/graph/badge.svg)
![Lint](https://github.com/Etoile04/gas-swelling-model/workflows/Lint/badge.svg)
![Docs](https://github.com/Etoile04/gas-swelling-model/workflows/Docs/badge.svg)
![Pages](https://github.com/Etoile04/gas-swelling-model/workflows/Pages/badge.svg)

A physics-based computational model for simulating fission gas bubble evolution and void swelling behavior in irradiated metallic nuclear fuels (U-Zr and U-Pu-Zr alloys).

## Overview

This implementation follows the theoretical framework from **"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"**.

The original paper formulation is often described as a 10-variable rate-theory model. The current packaged implementation in this repository is broader: the main 0D solver exposes a 17-state representation, supports multiple reduced-order backends (`full`, `qssa`, `hybrid_qssa`), and includes an optional 1D radial model.

### Who Should Use This Model

- **Nuclear materials researchers** studying fuel performance under irradiation
- **Fuel code developers** benchmarking swelling models
- **Graduate students** learning about fission gas behavior and rate theory
- **Nuclear engineers** analyzing metallic fuel swelling for reactor design

## Key Features

- **Comprehensive Physics**: Models gas transport, defect kinetics, cavity growth, and gas release
- **Validated**: Benchmarked against U-10Zr and U-Pu-Zr experimental data
- **Flexible Configuration**: Dictionary-based defaults generated from parameter dataclasses
- **Production-Ready**: Robust numerical solver with error handling and progress tracking
- **Well-Documented**: Extensive tutorials, parameter reference, and physics documentation
- **Modular Architecture**: Clean separation of physics, solvers, I/O, and models for easy maintenance

## Repository Guide / 仓库导览

This section is the short bilingual entry point for new readers. For the full guide, see **[docs/guides/repository_guide.md](docs/guides/repository_guide.md)**.

### Repository Structure / 仓库结构

```
gas_swelling/    core package / 核心包
tests/           pytest suite / 测试
examples/        runnable examples / 可运行示例
docs/            longer-form documentation / 详细文档
notebooks/       exploratory notebooks / 交互式分析
README.md        project overview / 项目总览
QUICKSTART.md    fastest onboarding / 快速上手
INSTALL.md       installation details / 安装说明
```

### Recommended Entry Points / 推荐入口

- New user / 新用户: start with **[QUICKSTART.md](QUICKSTART.md)**
- Package API / 包入口: **[gas_swelling/__init__.py](gas_swelling/__init__.py)**
- Main 0D implementation / 主 0D 实现: **[gas_swelling/models/refactored_model.py](gas_swelling/models/refactored_model.py)**
- Parameters / 参数定义: **[gas_swelling/params/parameters.py](gas_swelling/params/parameters.py)**
- Simple example / 最小示例: **[examples/quickstart_simple.py](examples/quickstart_simple.py)**
- Guided example / 带讲解示例: **[examples/quickstart_tutorial.py](examples/quickstart_tutorial.py)**
- 1D radial model / 一维径向模型: **[gas_swelling/models/radial_model.py](gas_swelling/models/radial_model.py)** and **[docs/1d_radial_model.md](docs/1d_radial_model.md)**

### Usage at a Glance / 使用速览

```bash
# Use the repo virtualenv / 使用仓库虚拟环境
./.venv/bin/python examples/quickstart_simple.py

# Run a focused test / 跑单个测试文件
./scripts/test_safe.sh tests/test_import.py

# Build docs offline / 离线构建文档
make -C docs html-offline

# Run the full suite / 跑全量测试
./scripts/test_safe.sh -q
```

```python
from gas_swelling import GasSwellingModel, create_default_parameters

params = create_default_parameters()
model = GasSwellingModel(params)
result = model.solve()
print(f"Final swelling: {result['swelling'][-1]:.4f}%")
```

For a fuller repository map, workflows, model variants, and testing notes, see **[docs/guides/repository_guide.md](docs/guides/repository_guide.md)**.

## Architecture

The codebase is organized into a **modular package structure** that separates concerns and enables targeted testing and reuse:

### Module Overview

```
gas_swelling/
├── physics/          # Physics calculations
│   ├── pressure.py        # Gas pressure (ideal, van der Waals, Virial, Ronchi)
│   ├── gas_transport.py   # Gas transport, release, nucleation, resolution
│   └── thermal.py         # Thermal equilibrium defect concentrations
├── ode/              # Rate equation system
│   └── rate_equations.py  # Main packaged ODE system (17-state representation)
├── solvers/          # Numerical solvers
│   ├── rk23_solver.py     # solve_ivp wrapper with multiple solver methods
│   └── euler_solver.py    # Explicit Euler method
├── analysis/         # Sensitivity analysis and metrics
├── io/               # Debug output and result helpers
├── models/           # Model orchestration and variants
│   ├── refactored_model.py   # Main modular 0D implementation
│   ├── qssa_model.py         # Reduced-order QSSA variant
│   ├── hybrid_qssa_model.py  # Hybrid reduced-order variant
│   └── radial_model.py       # 1D radial model
└── params/           # Parameter management
    └── parameters.py      # Default dict builders + parameter dataclasses
```

### Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Separation of Concerns**: Physics separated from numerics and I/O
3. **Testability**: Individual components can be unit tested
4. **Reusability**: Modules can be used independently
5. **Documentation**: Core subpackages include focused READMEs and examples

### Using Individual Modules

For most users, the high-level `GasSwellingModel` interface is sufficient. However, advanced users can import individual modules:

```python
# Use physics calculations directly
from gas_swelling.physics import calculate_gas_pressure, calculate_gas_influx

pressure = calculate_gas_pressure(Nc=1e6, T=800, R=1e-7, eos_model='ronchi')
influx = calculate_gas_influx(Cgb=1e20, Cgf=1e19, Dgb=1e-20, Lb=1e-6)

# Use custom solver with ODE system
from gas_swelling.ode import swelling_ode_system
from gas_swelling.solvers import RK23Solver

solver = RK23Solver(swelling_ode_system, params_dict)
result = solver.solve(
    t_span=(0, 8.64e6),
    y0=initial_conditions
)

# Use visualization utilities
from gas_swelling.io import plot_time_series, plot_swelling_comparison

plot_time_series(result['t'], result['swelling'], xlabel='Time (s)', ylabel='Swelling')
```

**📘 See [REFACTORING.md](REFACTORING.md)** for complete migration guide and architecture details.

## Quick Start

**🚀 New to the model? Start here:** **[QUICKSTART.md](QUICKSTART.md)** - The fastest way to get up and running with installation and your first simulation.

### Installation

Choose your preferred installation method:

- **[📘 INSTALL.md](INSTALL.md)** - Comprehensive installation guide (pip, conda, from-source)

```bash
# Quick install with pip
pip install gas-swelling-model

# Or with plotting support
pip install gas-swelling-model[plotting]
```

### Run Your First Simulation

```python
from gas_swelling import GasSwellingModel, create_default_parameters

# Create default parameters for U-10Zr fuel at 800 K
params = create_default_parameters()

# Initialize and run simulation
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6), t_eval=None)  # 100 days

# Access results
print(f"Final swelling: {result['swelling'][-1]:.4f}%")
print(f"Final bubble radius: {result['Rcb'][-1]*1e9:.1f} nm")
```

For a detailed step-by-step tutorial, see **[examples/quickstart_tutorial.py](examples/quickstart_tutorial.py)**.

## Documentation

### 📚 Tutorials & Learning Resources

New to rate theory or this model? Start with our beginner-friendly tutorials:

**Fundamentals Tutorials:**
- **[🎓 Rate Theory Fundamentals](docs/tutorials/rate_theory_fundamentals.md)** - Plain-language introduction to rate theory concepts, fission gas behavior, and swelling mechanisms
- **[⚡ 30-Minute Quickstart](docs/tutorials/30minute_quickstart.md)** - Comprehensive hands-on tutorial covering installation, first simulation, understanding output, modifying parameters, and advanced visualizations
- **[📐 Model Equations Explained](docs/tutorials/model_equations_explained.md)** - Walkthrough of the paper-level variables and how they relate to the packaged implementation

**Jupyter Notebooks (Interactive Examples):**
- **[📓 01 - Basic Simulation Walkthrough](notebooks/01_Basic_Simulation_Walkthrough.ipynb)** - Step-by-step guide through model setup, parameters, running simulations, and interpreting results
- **[📊 02 - Parameter Sweep Studies](notebooks/02_Parameter_Sweep_Studies.ipynb)** - Temperature sweeps, fission rate variations, sensitivity analysis, and two-parameter studies
- **[💨 03 - Gas Distribution Analysis](notebooks/03_Gas_Distribution_Analysis.ipynb)** - Analyze gas partitioning between bulk solution, bubbles, grain boundaries, and released gas
- **[🔬 04 - Experimental Data Comparison](notebooks/04_Experimental_Data_Comparison.ipynb)** - Validate model against U-10Zr, U-19Pu-10Zr, and high-purity uranium experimental data
- **[🧪 05 - Custom Material Composition](notebooks/05_Custom_Material_Composition.ipynb)** - Explore U-Zr and U-Pu-Zr alloy variations with helper functions for custom compositions
- **[📈 06 - Advanced Analysis Techniques](notebooks/06_Advanced_Analysis_Techniques.ipynb)** - Sensitivity analysis (OAT, Morris, Sobol), Monte Carlo uncertainty quantification, and parameter prioritization

**User Guides:**
- **[🎯 Interpreting Results Guide](docs/guides/interpreting_results.md)** - Comprehensive guide to all 17 output variables with typical ranges, physical interpretations, and warning signs
- **[🖼️ Plot Gallery](docs/guides/plot_gallery.md)** - Collection of 16+ ready-to-use plotting code snippets with examples and customization tips
- **[🔧 Troubleshooting Guide](docs/guides/troubleshooting.md)** - Solutions for 31+ common issues covering installation, parameters, solver convergence, performance, and more

### Getting Started Guides

- **[📘 Installation Guide](INSTALL.md)** - Detailed setup instructions for pip, conda, and source builds
- **[🚀 Quick Start Tutorial](examples/quickstart_tutorial.py)** - Beginner-friendly Python script with explanations
- **[📓 Jupyter Notebook: Temperature Sweep Study](notebooks/Temperature_Sweep_Example.ipynb)** - Interactive exploration of temperature effects

### Reference Documentation

- **[📋 Parameter Reference](docs/parameter_reference.md)** - Complete guide to all model parameters with physical meanings
- **[📐 CLAUDE.md](CLAUDE.md)** - Developer documentation and architecture overview
- **[🔬 Theoretical Framework](model_design.md)** - Physics background and model equations (Chinese)
- **[🔄 REFACTORING.md](REFACTORING.md)** - Migration guide for the modular architecture
- **[📦 Module Documentation](gas_swelling/)** - Each module has its own README:
  - [physics/README.md](gas_swelling/physics/README.md) - Gas pressure, transport, thermal calculations
  - [ode/README.md](gas_swelling/ode/README.md) - Rate equation system
  - [solvers/README.md](gas_swelling/solvers/README.md) - Numerical solver implementations
  - [io/README.md](gas_swelling/io/README.md) - Debug output and visualization

### Example Scripts

- **[examples/quickstart_tutorial.py](examples/quickstart_tutorial.py)** - Basic simulation with detailed comments
- **[examples/results_interpretation_guide.py](examples/results_interpretation_guide.py)** - Complete guide for interpreting simulation results with runnable code examples
- **[examples/plotting_examples.py](examples/plotting_examples.py)** - Plotting-focused example suite for simulation outputs

## Model Physics

### Original Theory vs Current Implementation

The paper-level theory is often summarized as a **10-variable ODE model** that tracks gas, cavities, and point defects in the bulk and at interfaces.

The current package implementation is broader:

- The main packaged 0D solver uses a **17-state representation**
- The repository also includes **QSSA** and **Hybrid QSSA** reduced-order variants
- The 1D radial model defaults to `radial_solver_mode='decoupled'` and keeps `coupled` available as an option

For the most up-to-date implementation details, prefer the package code and tests over older architecture prose.

### Key Outputs

- **Swelling strain**: Volume fraction occupied by cavities
- **Bubble radius distribution**: Average cavity sizes in bulk and at boundaries
- **Gas pressure**: Internal cavity pressure (ideal or Van der Waals EOS)
- **Gas release fraction**: Fraction of fission gas released from fuel
- **Critical radius**: Distinguishes gas-driven vs bias-driven swelling

### Physical Processes Modeled

1. **Gas Transport** (Eqs. 1-8): Diffusion, nucleation, cavity growth
2. **Defect Kinetics** (Eqs. 17-20): Vacancy/interstitial production, recombination, sink annihilation
3. **Cavity Growth** (Eq. 14): Bias-driven vacancy influx vs thermal emission
4. **Gas Release** (Eqs. 9-12): Interconnectivity threshold and release fraction

See [model_design.md](model_design.md) for complete equations.

## Usage Examples

### Example 1: Basic Simulation

```python
from gas_swelling import GasSwellingModel, create_default_parameters

# Setup
params = create_default_parameters()
params['temperature'] = 800  # K
params['fission_rate'] = 4.0e19  # fissions/m³/s

# Run
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6), t_eval=None)

# Plot
import matplotlib.pyplot as plt
plt.plot(result['t']/86400, result['swelling']*100)
plt.xlabel('Time (days)')
plt.ylabel('Swelling (%)')
plt.show()
```

### Example 2: Temperature Sweep

```python
import matplotlib.pyplot as plt

from gas_swelling import GasSwellingModel, create_default_parameters

temperatures = [600, 700, 800, 900, 1000]  # K
swelling_results = []

for T in temperatures:
    params = create_default_parameters()
    params['temperature'] = T
    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 8.64e6), t_eval=None)
    swelling_results.append(result['swelling'][-1])

# Plot temperature dependence
plt.plot(temperatures, swelling_results, 'o-')
plt.xlabel('Temperature (K)')
plt.ylabel('Final Swelling')
plt.show()
```

### Example 3: Custom Parameters

```python
from gas_swelling import GasSwellingModel, create_default_parameters

params = create_default_parameters()
params['dislocation_density'] = 1e14
params['surface_energy'] = 1.0
params['Fnb'] = 1e-4
params['Fnf'] = 1e-3
params['temperature'] = 850
params['fission_rate'] = 5.0e19
params['eos_model'] = 'ronchi'

model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))
```

For more examples, see the **[Parameter Reference](docs/parameter_reference.md)** and **[Jupyter Notebook](notebooks/Temperature_Sweep_Example.ipynb)**.

## Parameter Sensitivity Analysis

The model includes a comprehensive **sensitivity analysis framework** to identify influential parameters, quantify uncertainties, and prioritize experimental measurements. This is essential for understanding which parameters most affect swelling predictions and where to focus research efforts.

### Why Sensitivity Analysis Matters

- **Identify critical parameters** that most affect swelling predictions
- **Quantify uncertainty** in model outputs due to parameter variations
- **Prioritize experimental work** by highlighting parameters needing better measurement
- **Understand parameter interactions** and nonlinear behavior
- **Validate model robustness** across the parameter space

### Available Methods

The framework provides three complementary sensitivity analysis methods:

| Method | Type | Computational Cost | Best For | Output Metrics |
|--------|------|-------------------|----------|----------------|
| **OAT** | Local sensitivity | Low (p × k simulations) | Initial screening, local effects | Elasticity coefficients |
| **Morris** | Global screening | Medium (r × p simulations) | Ranking many parameters, detecting nonlinearity | μ, μ*, σ statistics |
| **Sobol** | Global variance-based | High (N × (2 + p) simulations) | Quantitative analysis, interaction effects | S1, ST indices |

**Quick Selection:**
- **Quick local analysis** → Use OAT
- **Screen many parameters** → Use Morris
- **Rigorous quantitative analysis** → Use Sobol

### Quick Example

```python
from gas_swelling.analysis.sensitivity import OATAnalyzer, create_default_parameter_ranges
from gas_swelling.analysis.visualization import plot_tornado

# Step 1: Define parameter ranges
param_ranges = create_default_parameter_ranges()

# Step 2: Run OAT analysis (±10% variations)
analyzer = OATAnalyzer(
    parameter_ranges=param_ranges,
    output_names=['swelling', 'Rcb', 'gas_release'],
    sim_time=8.64e6,  # 100 days
    t_eval_points=100
)

results = analyzer.run_oat_analysis(
    percent_variations=[-10, 10],
    verbose=True
)

# Step 3: Visualize results
plot_tornado(
    results,
    output_name='swelling',
    metric='elasticity',
    title='OAT Sensitivity Analysis - Swelling',
    save_path='sensitivity_tornado.png'
)

# Step 4: Print parameter ranking
print("\nParameter Ranking by Elasticity:")
for result in sorted(results, key=lambda r: abs(r.sensitivities['swelling']['elasticity']), reverse=True):
    print(f"{result.parameter_name}: {result.sensitivities['swelling']['elasticity']:.2f}")
```

**Expected output:**
```
Parameter Ranking by Elasticity:
dislocation_density: 2.35
surface_energy: -1.80
temperature: 0.95
Fnb: 0.45
Fnf: 0.72
```

### Documentation and Examples

- **[📊 Sensitivity Analysis Guide](docs/sensitivity_analysis_guide.md)** - Comprehensive documentation with theory, examples, and best practices
- **[🐍 OAT Example](examples/sensitivity_oat_example.py)** - One-at-a-time analysis tutorial
- **[🐍 Morris Example](examples/sensitivity_morris_example.py)** - Global screening tutorial
- **[🐍 Sobol Example](examples/sensitivity_sobol_example.py)** - Variance-based analysis tutorial
- **[🐍 Complete Workflow](examples/sensitivity_analysis_tutorial.py)** - Full sensitivity study combining all methods

### High-Impact Parameters

Based on sensitivity analysis, these parameters have the strongest influence on swelling predictions:

| Parameter | Influence | Physical Meaning |
|-----------|-----------|------------------|
| **Dislocation density** (ρ) | Very high (±40% swelling) | Defect sink strength, vacancy absorption |
| **Temperature** | High (bell-shaped, ~700-800 K peak) | Diffusion rates, thermal emission |
| **Surface energy** (γ) | High (-1.8 elasticity) | Cavity stability, bubble nucleation |
| **Dislocation bias** (Zi) | Moderate | Vacancy supersaturation driving force |
| **Boundary nucleation** (Fnf) | Moderate | Incubation period, bubble density |

**Key insight:** Dislocation density has the strongest effect on swelling (elasticity ≈ 2.35). A 10% increase in dislocation density causes a ~23.5% increase in swelling. This parameter should be prioritized for accurate experimental measurement.

### When to Use Sensitivity Analysis

**Use sensitivity analysis when:**
- Calibrating the model to experimental data
- Assessing model uncertainty for safety cases
- Designing experiments to measure key parameters
- Comparing fuel compositions (U-Zr vs U-Pu-Zr)
- Optimizing fuel performance parameters
- Validating model behavior across operating conditions

**Typical workflow:**
1. **Screen** parameters with Morris method (fast global screening)
2. **Rank** parameters by importance (μ* statistics)
3. **Analyze** top parameters with Sobol method (quantitative)
4. **Validate** findings with physical reasoning and experiments

For detailed methodology, see the **[Sensitivity Analysis Guide](docs/sensitivity_analysis_guide.md)**.

## Parameter Configuration

Default parameters are exposed through `create_default_parameters()`, which returns a dictionary assembled from the underlying `MaterialParameters` and `SimulationParameters` dataclasses.

Typical usage is:

```python
from gas_swelling import create_default_parameters

params = create_default_parameters()
params['temperature'] = 850
params['model_backend'] = 'hybrid_qssa'
params['radial_solver_mode'] = 'decoupled'
```

**📋 See [Parameter Reference](docs/parameter_reference.md) for complete documentation.**

### High-Sensitivity Parameters

These parameters have strong influence on swelling predictions:
- **Dislocation density** (ρ): ±40% swelling change
- **Dislocation bias** (Zi): Affects vacancy supersaturation
- **Boundary nucleation factor** (Fnf): Controls incubation period
- **Temperature**: Bell-shaped swelling curve (~700-800 K peak)

## Validation

The model has been validated against experimental data:

| Fuel Type | Temperature | Burnup | Validation Status |
|-----------|-------------|--------|-------------------|
| U-10Zr | 600-900°C | 2-10 at.% | ✓ Matches Fig. 6 data |
| U-19Pu-10Zr | 600-800°C | 2-8 at.% | ✓ Matches Fig. 7 data |
| Pure U | Various | Various | ✓ Matches Figs. 9-10 data |

Typical validation metrics:
- Final swelling percent at given burnup
- Bubble radius evolution
- Gas release fraction
- Temperature-dependent swelling peak

## Performance

- **Main 0D default**: stiff-aware `solve_ivp` workflow through the packaged model interface
- **Reduced-order options**: `qssa` and `hybrid_qssa` are available for faster studies
- **Radial default**: `radial_solver_mode='decoupled'` for practical turnaround, with `coupled` retained for deeper numerical studies
- **Performance depends strongly on** simulation horizon, backend choice, and whether radial coupling is enabled

## Requirements

- Python 3.8+
- numpy >= 1.20.0
- scipy >= 1.7.0
- matplotlib >= 3.3.0 (optional, for plotting)

## Installation

See **[INSTALL.md](INSTALL.md)** for detailed instructions:

```bash
# pip (recommended)
pip install gas-swelling-model

# conda
conda create -n gas-swelling python=3.11
conda activate gas-swelling
conda install -c conda-forge numpy scipy matplotlib
pip install gas-swelling-model

# From source
git clone https://github.com/yourusername/gas-swelling-model.git
cd gas-swelling-model
pip install -e .
```

## Getting Help

- **Documentation**: Start with [INSTALL.md](INSTALL.md) and [Parameter Reference](docs/parameter_reference.md)
- **Examples**: Run [quickstart_tutorial.py](examples/quickstart_tutorial.py) or explore [notebooks/](notebooks/)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/gas-swelling-model/issues)
- **Physics Questions**: See [model_design.md](model_design.md) and [original paper](original paper of swelling rate theory.md)

## Citation

If you use this model in your research, please cite:

```bibtex
@software{gas_swelling_model,
  title = {Gas Swelling Model for U-Zr and U-Pu-Zr Nuclear Fuels},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/gas-swelling-model}
}
```

And the original theoretical paper:
```bibtex
@article{original_paper,
  title = {Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel},
  author = {Original Authors},
  journal = {Journal of Nuclear Materials},
  year = {Year}
}
```

## License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

## Contributing

Contributions are welcome! The **modular architecture** makes it easy to contribute:

- **Physics improvements**: Modify `gas_swelling/physics/` modules
- **New solvers**: Add to `gas_swelling/solvers/`
- **Enhanced I/O**: Extend `gas_swelling/io/` utilities
- **Bug fixes**: Clear module boundaries make issues easy to isolate

Please see [CLAUDE.md](CLAUDE.md) for development guidelines and [REFACTORING.md](REFACTORING.md) for architecture details.

### Testing

```bash
# Safe default test entry (timeout + child-process cleanup)
./scripts/test_safe.sh tests/ -v
./.venv/bin/python scripts/test_safe.py tests/ -v

# Run fast tests only (exclude slow integration tests)
./scripts/test_safe.sh tests/ -v -m 'not slow'

# Run with coverage
./scripts/test_safe.sh tests/ --cov=gas_swelling --cov-report=term-missing

# Shorter timeout for a targeted run
./.venv/bin/python scripts/test_safe.py --timeout 300 -- tests/test_import.py
```

## Acknowledgments

This implementation is based on the theoretical framework developed in the original paper on fission gas bubble nucleated void swelling in metallic fuels.

---

**📘 Documentation Index** | **[INSTALL](INSTALL.md)** | **[Parameter Reference](docs/parameter_reference.md)** | **[Quick Start Tutorial](examples/quickstart_tutorial.py)** | **[Jupyter Notebook](notebooks/Temperature_Sweep_Example.ipynb)**
