# Gas Swelling Model

A scientific computing package for modeling fission gas bubble evolution and void swelling behavior in irradiated metallic fuels (U-Zr and U-Pu-Zr alloys).

This package implements rate theory models based on the theoretical framework from:
*"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel."*

## Overview

The Gas Swelling Model simulates fission gas bubble evolution and void swelling behavior in irradiated metallic fuels. It solves a system of 10 coupled ordinary differential equations (ODEs) to model:

- Gas atom transport in bulk matrix and at phase boundaries
- Cavity/bubble nucleation and growth
- Vacancy and interstitial defect kinetics
- Gas pressure evolution (ideal gas law or Van der Waals EOS)
- Void swelling rate calculation
- Gas release fraction

## Installation

### From PyPI (recommended)

```bash
pip install gas-swelling-model
```

### For development

```bash
# Clone the repository
git clone https://github.com/yourusername/gas-swelling-model.git
cd gas-swelling-model

# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### With optional dependencies

```bash
# Install with plotting support
pip install gas-swelling-model[plotting]

# Install with all optional dependencies
pip install gas-swelling-model[all]
```

## Quick Start

### Basic Usage

```python
from gas_swelling import GasSwellingModel, create_default_parameters
import numpy as np

# Create default parameters
params = create_default_parameters()

# Customize parameters if needed
params.simulation.temperature = 773.15  # Temperature in K (500°C)
params.simulation.fission_rate = 1e19   # Fission rate (fissions/m³/s)

# Create and run model
model = GasSwellingModel(params)

# Define time span for simulation (0 to 100 days)
sim_time = 100 * 24 * 3600  # seconds
time_points = np.linspace(0, sim_time, 1000)

# Solve the ODE system
result = model.solve(
    t_span=(0, sim_time),
    t_eval=time_points
)

# Access results
print(f"Final swelling: {result['swelling'][-1]:.2%}")
print(f"Final bubble radius: {result['Rcb'][-1]*1e9:.2f} nm")
print(f"Gas release fraction: {result['fgr'][-1]:.2%}")
```

### Parameter Configuration

```python
from gas_swelling import MaterialParameters, SimulationParameters

# Create custom material parameters
material_params = MaterialParameters(
    dislocation_density=1e14,  # m⁻²
    surface_energy=1.0,        # J/m²
    grain_size=10e-6,          # 10 μm
)

# Create custom simulation parameters
sim_params = SimulationParameters(
    temperature=773.15,        # K
    fission_rate=1e19,         # fissions/m³/s
)

# Combine parameters
params = create_default_parameters()
params.material = material_params
params.simulation = sim_params
```

## Key Features

### State Variables (10 coupled ODEs)

1. **Cgb**: Gas atom concentration in bulk matrix (atoms/m³)
2. **Ccb**: Cavity/bubble concentration in bulk (cavities/m³)
3. **Ncb**: Gas atoms per bulk cavity (atoms/cavity)
4. **cvb**: Vacancy concentration in bulk
5. **cib**: Interstitial concentration in bulk
6. **Cgf**: Gas atom concentration at phase boundaries
7. **Ccf**: Cavity concentration at phase boundaries
8. **Ncf**: Gas atoms per boundary cavity
9. **cvf**: Vacancy concentration at boundaries
10. **cif**: Interstitial concentration at boundaries

### Physical Models

- **Gas Pressure**: Ideal gas law or modified Van der Waals EOS (configurable via `eos_model`)
- **Cavity Radius**: Mechanical equilibrium between gas pressure and surface tension
- **Swelling Rate**: Total volume fraction occupied by cavities: `V_bubble = (4/3)πR³ × Cc`
- **Critical Radius**: Distinguishes gas-driven swelling from bias-driven void growth

### Model Output

The `solve()` method returns a dictionary with time series of:
- All 10 state variables
- Bubble radii (Rcb, Rcf)
- Gas pressure (Pg)
- Swelling fraction
- Gas release fraction (fgr)
- And more derived quantities

## Dependencies

### Required

- Python >= 3.8
- NumPy >= 1.20.0
- SciPy >= 1.7.0

### Optional

- Matplotlib >= 3.3.0 (for plotting examples)
- pytest >= 7.0.0 (for running tests)
- build >= 0.10.0 (for building distributions)
- twine >= 4.0.0 (for PyPI uploads)

## Project Structure

```
gas_swelling/
├── __init__.py           # Package initialization and exports
├── models/
│   ├── __init__.py
│   └── modelrk23.py      # Main GasSwellingModel class
└── params/
    ├── __init__.py
    └── parameters.py     # Parameter classes and defaults

examples/
├── __init__.py
└── run_simulation.py     # Example simulations with plotting

tests/
├── __init__.py
└── test_import.py        # Basic import tests
```

## Examples

See the `examples/` directory for complete working examples:

```bash
# Run example simulation (requires matplotlib)
python examples/run_simulation.py
```

## Documentation

For detailed information about the model, see:

- **CLAUDE.md**: Developer guide and API documentation
- **model_design.md**: Theoretical framework (in Chinese)
- **original paper of swelling rate theory.md**: Reference paper (English)

### Model Equations

1. **Gas transport** (Eqs. 1-8): Diffusion, nucleation, cavity growth
2. **Defect kinetics** (Eqs. 17-20): Vacancy/interstitial production, recombination, sink annihilation
3. **Cavity growth** (Eq. 14): Bias-driven vacancy influx vs thermal emission
4. **Gas release** (Eqs. 9-12): Interconnectivity threshold and release fraction
5. **Swelling calculation**: Volume fraction of cavities

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gas_swelling
```

## Validation

The model has been validated against experimental data:
- U-10Zr fuel swelling data (Fig. 6 in reference paper)
- U-19Pu-10Zr fuel data (Fig. 7)
- High-purity uranium swelling (Figs. 9-10)

## Performance Notes

- The ODE system is stiff due to widely varying timescales
- RK23 method provides balance of accuracy and speed
- Typical simulation: 100 days of irradiation in ~100 seconds

## Citation

If you use this package in your research, please cite the underlying theoretical framework:

```bibtex
@article{swelling_rate_theory,
  title={Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel},
  author={[Author et al.]},
  journal={[Journal]},
  year={[Year]}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions, issues, or suggestions:
- Open an issue on [GitHub Issues](https://github.com/yourusername/gas-swelling-model/issues)
- Check the documentation in CLAUDE.md
- Review the examples in the `examples/` directory

## Acknowledgments

This package implements theoretical models developed by the nuclear fuel research community. We acknowledge the contributions of all researchers who have advanced the understanding of fission gas behavior in metallic fuels.
