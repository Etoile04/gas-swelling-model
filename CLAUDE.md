# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A scientific computing package for modeling fission gas bubble evolution and void swelling in irradiated metallic nuclear fuels (U-Zr and U-Pu-Zr alloys). Based on rate theory from "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel."

## Commands

### Running Tests
```bash
# Safe test runner (recommended - handles timeouts and process cleanup)
./scripts/test_safe.sh tests/ -v

# Run single test file
./scripts/test_safe.sh tests/test_import.py -v

# Run fast tests only (exclude slow integration tests)
./scripts/test_safe.sh tests/ -v -m 'not slow'

# Run with coverage
./scripts/test_safe.sh tests/ --cov=gas_swelling --cov-report=term-missing

# Shorter timeout for quick runs
./.venv/bin/python scripts/test_safe.py --timeout 300 -- tests/test_import.py
```

### Running Examples
```bash
# Use repo virtualenv
./.venv/bin/python examples/quickstart_simple.py
./.venv/bin/python examples/quickstart_tutorial.py
./.venv/bin/python examples/plotting_examples.py
```

### Building Documentation
```bash
# Build HTML docs
make -C docs html

# Build offline (no network access)
make -C docs html-offline
```

## Core Architecture

### Model Backends (`model_backend` parameter)

| Backend | Description | Use Case |
|---------|-------------|----------|
| `full` | 17-state ODE system (default) | Production runs, full physics |
| `qssa` | Quasi-steady-state approximation | Faster studies, sensitivity analysis |
| `hybrid_qssa` | Hybrid reduced-order | Balance of speed and accuracy |

### State Vector (17 components in `full` backend)

The main ODE system tracks:
- **Gas**: Cgb (bulk gas), Cgf (boundary gas), released_gas
- **Cavities**: Ccb, Ccf (concentrations), Ncb, Ncf (gas atoms per cavity), Rcb, Rcf (radii)
- **Defects**: cvb, cib (bulk vacancies/interstitials), cvf, cif (boundary)
- **Sink strengths**: kvb, kib, kvf, kif

### Package Structure
```
gas_swelling/
├── models/           # Model implementations
│   ├── refactored_model.py   # Main 0D model (RefactoredGasSwellingModel)
│   ├── qssa_model.py         # Reduced-order variant
│   ├── hybrid_qssa_model.py  # Hybrid variant
│   └── radial_model.py       # 1D radial model
├── physics/          # Pressure, transport, thermal calculations
├── ode/              # Rate equation systems (full, qssa, hybrid)
├── solvers/          # Numerical solvers (RK23, Euler)
├── params/           # Parameter dataclasses and defaults
├── analysis/         # Sensitivity analysis (OAT, Morris, Sobol)
├── visualization/    # Plotting utilities
├── io/               # Debug output helpers
└── validation/       # Paper data comparison scripts
```

### Key Entry Points

- **Package API**: `gas_swelling/__init__.py` - exports `GasSwellingModel`, `create_default_parameters`
- **Main 0D model**: `gas_swelling/models/refactored_model.py`
- **Parameters**: `gas_swelling/params/parameters.py`
- **1D radial model**: `gas_swelling/models/radial_model.py` (uses `radial_solver_mode='decoupled'` by default)

## Usage

```python
from gas_swelling import GasSwellingModel, create_default_parameters

params = create_default_parameters()
params['temperature'] = 800  # K
params['model_backend'] = 'full'  # or 'qssa', 'hybrid_qssa'

model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))  # 100 days
print(f"Final swelling: {result['swelling'][-1]:.4f}%")
```

## Key Parameters

| Parameter | Effect | Typical Range |
|-----------|--------|---------------|
| `temperature` | Bell-shaped swelling curve | 600-1000 K |
| `dislocation_density` | Strong effect (±40% swelling) | 1e13-1e15 m⁻² |
| `surface_energy` | Cavity stability | 0.8-1.5 J/m² |
| `fission_rate` | Gas production rate | 1e19-1e20 fissions/m³/s |
| `eos_model` | Gas equation of state | 'ideal' or 'ronchi' |
| `model_backend` | ODE system variant | 'full', 'qssa', 'hybrid_qssa' |

## 1D Radial Model

The radial model extends the 0D model to capture spatial variations across the fuel pellet:
- `radial_solver_mode='decoupled'` (default): Fast node-wise solve, reuses 0D backend
- `radial_solver_mode='coupled'`: Full coupled ODE solve (slower, for numerical studies)

## Validation

Model validated against:
- U-10Zr data (Fig. 6)
- U-19Pu-10Zr data (Fig. 7)
- High-purity U (Figs. 9-10)

Validation scripts in `gas_swelling/validation/scripts/`
