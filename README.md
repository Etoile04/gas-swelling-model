# Gas Swelling Model - Command-Line Interface

A scientific computing tool for simulating fission gas bubble evolution and void swelling behavior in irradiated metallic nuclear fuels (U-Zr and U-Pu-Zr alloys) based on rate theory.

## Overview

This project implements the theoretical framework from **"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel."** The command-line interface allows researchers to run simulations without writing Python code, making parameter studies and automation accessible to non-programmers.

### Key Features

- **10-variable coupled ODE system** modeling gas transport, cavity nucleation, and defect kinetics
- **Multiple output formats**: CSV, JSON, HDF5, MATLAB
- **Configurable parameters** via YAML files
- **Progress tracking** during simulations
- **Validated against experimental data** for U-10Zr and U-Pu-Zr fuels

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd swelling

# Install in development mode (recommended)
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# For MATLAB output support
pip install -e ".[matlab]"
```

### Verify Installation

```bash
gas-swelling --help
```

Expected output:
```
Gas Swelling Simulation CLI

A command-line interface for running gas swelling simulations
without editing Python code.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  run        Run a gas swelling simulation using a YAML configuration...
```

## Quick Start

### 1. Basic Simulation

Run a simulation with the example configuration:

```bash
gas-swelling run examples/config_example.yaml
```

This will:
- Load parameters from `config_example.yaml`
- Run the simulation for 100 days (default)
- Display progress during execution
- Show final results (bubble radius, swelling percentage)
- Save output to `output/` directory in CSV format

### 2. Custom Output Directory

```bash
gas-swelling run examples/config_example.yaml --output-dir my_results/
```

### 3. Different Output Format

```bash
# JSON format with metadata
gas-swelling run examples/config_example.yaml --format json

# HDF5 format (for large datasets)
gas-swelling run examples/config_example.yaml --format hdf5

# MATLAB format (for post-processing in MATLAB)
gas-swelling run examples/config_example.yaml --format matlab
```

### 4. Verbose Output

See detailed progress and parameter information:

```bash
gas-swelling run examples/config_example.yaml --verbose
```

## CLI Reference

### Command: `gas-swelling run`

Run a gas swelling simulation using a YAML configuration file.

**Syntax:**
```bash
gas-swelling run [OPTIONS] CONFIG
```

**Arguments:**
- `CONFIG`: Path to the YAML configuration file (required)

**Options:**
- `--output-dir PATH`: Output directory for results (default: `output/`)
- `--format FORMAT`: Output format - choices: `csv`, `json`, `hdf5`, `matlab` (default: `csv`)
- `--verbose, -v`: Enable verbose output with detailed progress
- `--help`: Show help message and exit

**Exit Codes:**
- `0`: Success - simulation completed
- `1`: Error - configuration error, file not found, or simulation failure

## Configuration Files

### YAML Structure

Configuration files use a flat key-value structure. Only specify parameters you want to override - default values are built into the code.

**Basic Example:**

```yaml
# simulation_config.yaml
temperature: 773.0        # Operating temperature (K)
fission_rate: 2.0e+20    # Fission rate (fissions/m³/s)
max_time: 8.64e+6        # Simulation time (s) - 100 days
eos_model: ideal         # Equation of state: 'ideal' or 'ronchi'
```

### Commonly Modified Parameters

| Parameter | Description | Typical Range | Impact |
|-----------|-------------|---------------|--------|
| `temperature` | Operating temperature | 600-1000 K | **High** - bell-shaped swelling curve, peak ~700-800 K |
| `fission_rate` | Fission density | 1e19 to 1e21 fissions/m³/s | **High** - linear effect on gas production |
| `max_time` | Simulation duration | 1e6 to 1e8 s | Controls total burnup simulated |
| `dislocation_density` | Defect sink strength | 1e13 to 1e15 m⁻² | **High** - higher density → lower swelling |
| `Fnb`, `Fnf` | Bubble nucleation factors | 1e-6 to 1e-4 | **High** - controls incubation period |
| `surface_energy` | Gas/matrix interface energy | 0.3-0.7 J/m² | Medium - affects bubble stability |
| `eos_model` | Gas equation of state | 'ideal' or 'ronchi' | Medium - 'ronchi' gives ~10-15% higher swelling |

### Example Configurations

**High-Temperature Simulation (800 K):**
```yaml
temperature: 800.0
eos_model: ronchi
max_time: 8.64e6  # 100 days
fission_rate: 2.0e+20
```

**Low Fission Rate Study:**
```yaml
fission_rate: 5.0e19
temperature: 773.0
max_time: 1.728e7  # 200 days
```

**Cold-Worked Material (High Dislocation Density):**
```yaml
dislocation_density: 1.0e14
temperature: 700.0
fission_rate: 2.0e+20
```

## Output Files

### CSV Format (Default)

Time-series data with columns for all state variables:

```csv
time,Rcb,Rcf,Ccb,Ccf,Ncb,Ncf,swelling,...
0,1.0e-9,1.2e-9,1.0e20,2.0e19,100,150,0.001,...
86400,1.1e-9,1.3e-9,1.1e20,2.1e19,105,155,0.0012,...
```

### JSON Format

Structured data with metadata:

```json
{
  "metadata": {
    "config_file": "config.yaml",
    "temperature": 773.0,
    "fission_rate": 2.0e+20,
    "eos_model": "ideal"
  },
  "data": {
    "time": [0, 86400, ...],
    "Rcb": [1.0e-9, 1.1e-9, ...],
    "swelling": [0.001, 0.0012, ...]
  }
}
```

### HDF5 Format

Hierarchical data format for large datasets (use with `h5py` or `pandas`):

```python
import h5py
import pandas as pd

with h5py.File('output/results.h5', 'r') as f:
    df = pd.DataFrame({key: f[key][:] for key in f.keys()})
```

## Common Use Cases

### Parameter Study

Run multiple simulations with different temperatures:

```bash
#!/bin/bash
for temp in 650 700 750 800 850; do
  cat > temp_config.yaml << EOF
temperature: ${temp}.0
fission_rate: 2.0e+20
max_time: 8.64e6
EOF

  gas-swelling run temp_config.yaml --output-dir results/temp_${temp}/
done
```

### Batch Processing

Process multiple configurations:

```bash
#!/bin/bash
for config in configs/*.yaml; do
  name=$(basename "$config" .yaml)
  gas-swelling run "$config" --output-dir "batch_results/$name"
done
```

### Automated Analysis

Combine with Python for post-processing:

```python
import subprocess
import pandas as pd

temperatures = range(600, 900, 50)
results = []

for temp in temperatures:
    # Run simulation
    subprocess.run([
        'gas-swelling', 'run',
        'examples/config_example.yaml',
        '--output-dir', f'temp_{temp}',
        '--format', 'json'
    ])

    # Load results
    data = pd.read_json(f'temp_{temp}/output.json')
    final_swelling = data['swelling'].iloc[-1]
    results.append({'temperature': temp, 'swelling': final_swelling})

# Create temperature-sweep plot
df = pd.DataFrame(results)
print(df)
```

## Model Background

### State Variables (10 ODEs)

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

### Key Physical Relationships

- **Gas Pressure**: Ideal gas law or modified Van der Waals EOS
- **Cavity Radius**: Mechanical equilibrium between gas pressure and surface tension
- **Swelling Rate**: Volume fraction occupied by cavities: `V_bubble = (4/3)πR³ × Cc`
- **Critical Radius**: Distinguishes gas-driven vs bias-driven void growth

## Validation

The model has been validated against experimental data:

- ✅ U-10Zr fuel swelling (Fig. 6 in reference paper)
- ✅ U-19Pu-10Zr fuel data (Fig. 7)
- ✅ High-purity uranium swelling (Figs. 9-10)

Typical validation metrics:
- Final swelling percent at given burnup
- Bubble radius evolution
- Gas release fraction
- Temperature-dependent swelling peak

## Performance Notes

- **Stiff ODE system** due to widely varying timescales (defect recombination vs cavity growth)
- **RK23 solver** chosen for balance of accuracy and speed
- **Typical simulation**: 100 days of irradiation in ~100 seconds of computation
- **Memory usage**: ~50-200 MB depending on output resolution

### Performance Tips

1. Reduce `max_time` or increase `time_step` for faster exploratory runs
2. Use `csv` format for small datasets, `hdf5` for large datasets
3. Disable verbose output for batch processing (slight speedup)

## Troubleshooting

### Common Errors

**Error: `Cannot import GasSwellingModel`**
```bash
# Solution: Make sure you're in the project directory
cd /path/to/swelling
gas-swelling run config.yaml
```

**Error: `Configuration error: Invalid parameter`**
```bash
# Solution: Check YAML syntax and parameter names
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**Error: `Simulation error: Solver failed to converge`**
```bash
# Solution: Try reducing time_step or max_time_step
# In config.yaml:
time_step: 1.0e-10
max_time_step: 1.0e+1
```

## Advanced Usage

### Custom Parameter Studies

Use Python scripting for complex parameter sweeps:

```python
from cli.config import load_config, validate_params
from modelrk23 import GasSwellingModel
import numpy as np

# Load base configuration
params = load_config('examples/config_example.yaml')

# Temperature sweep
temperatures = np.linspace(600, 900, 7)
results = {}

for temp in temperatures:
    params['temperature'] = temp
    model = GasSwellingModel(params)

    result = model.solve(
        t_span=(0, 8.64e6),
        t_eval=np.linspace(0, 8.64e6, 100)
    )

    results[temp] = result['swelling'][-1]

print(results)
```

### Integration with Other Tools

**MATLAB:**
```matlab
% Load HDF5 output
data = h5read('output/results.h5', '/');
swelling = data(:, strcmp(data.Properties.VariableNames, 'swelling'));
plot(swelling);
```

**Python (pandas):**
```python
import pandas as pd

# Load CSV
df = pd.read_csv('output/results.csv')

# Plot swelling evolution
df.plot(x='time', y='swelling')
```

## Citation

If you use this software in publications, please cite:

```
[Author names]. "Kinetics of fission-gas-bubble-nucleated void swelling
of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel."
[Journal] [Year].
```

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: See `CLAUDE.md` for developers
- **Issues**: Report bugs via GitHub Issues
- **Examples**: Check `examples/` directory for sample configurations

## Acknowledgments

This implementation follows the theoretical framework developed in the original paper on gas swelling kinetics in metallic nuclear fuels.
