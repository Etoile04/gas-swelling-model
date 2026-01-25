# I/O Module

The `io` module handles input/output operations for the gas swelling model, including debug logging, result visualization, and data export/import utilities.

## Overview

The I/O module provides utilities for:
1. **Debug output** - Track intermediate calculations during simulation
2. **Visualization** - Plot simulation results with matplotlib
3. **Data persistence** - Save and load simulation results
4. **Progress reporting** - Monitor long-running simulations

The module is designed to be **optional** - the core model works without visualization or debug output, making it suitable for batch processing and HPC environments.

## Module Components

### 1. Debug Output (`debug_output.py`)

Utilities for logging intermediate calculations and tracking solver progress.

#### DebugConfig

Configuration for debug output behavior:

```python
from gas_swelling.io import DebugConfig

config = DebugConfig(
    enabled=True,           # Enable/disable debug output
    log_interval=100,       # Log every N solver steps
    save_to_file=None,      # Optional: save debug log to file
    verbose=True            # Print detailed output
)
```

#### DebugHistory

Container for storing debug information during simulation:

```python
from gas_swelling.io import DebugHistory

# Create debug history
debug = DebugHistory(enabled=True)

# During simulation, the ODE system can log to it
# (internal use by swelling_ode_system)

# Access logged data
for entry in debug.history:
    print(f"t={entry['t']:.2e}, Rcb={entry['Rcb']:.3e}")

# Save to file
debug.save('debug_log.json')

# Load from file
debug2 = DebugHistory.load('debug_log.json')
```

**Debug Log Contents:**
- Time points
- State variables snapshot
- Individual rate terms (nucleation, absorption, resolution)
- Pressure and temperature
- Sink strengths
- Solver step sizes

#### Utility Functions

```python
from gas_swelling.io import (
    format_debug_output,
    log_debug_message,
    save_debug_history,
    load_debug_history,
    update_debug_history,
    print_simulation_summary
)

# Format debug info for display
formatted = format_debug_output(debug_data)

# Log a message with timestamp
log_debug_message("Simulation started", debug=debug)

# Save/load debug history
save_debug_history(debug, 'debug.json')
loaded = load_debug_history('debug.json')

# Update history with new entry
update_debug_history(debug, t=1.0, y=y_current, dydt=dydt)

# Print summary at end
print_simulation_summary(result, params)
```

**Example Output:**
```
========================================
Simulation Summary
========================================
Duration:         100.0 days
Time steps:       1523
Final swelling:   2.34%
Final radius:     15.6 nm
Gas released:     0.12%
Solver status:    Success
========================================
```

### 2. Visualization (`visualization.py`)

Plotting utilities for analyzing simulation results. All plotting functions are **optional** and require matplotlib.

#### Checking Matplotlib Availability

```python
from gas_swelling.io import check_matplotlib_available

if check_matplotlib_available():
    # Matplotlib is installed
    print("Plotting functions available")
else:
    # Matplotlib not available
    print("Plotting not available - install matplotlib")
```

#### Setting Up Chinese Font Support

For plots with Chinese characters (model documentation in Chinese):

```python
from gas_swelling.io import setup_chinese_font

import matplotlib.pyplot as plt
setup_chinese_font()  # Configure font for Chinese characters

plt.figure()
plt.xlabel('时间 (天)')  # Chinese labels now work
plt.ylabel('肿胀 (%)')
plt.show()
```

#### Time Series Plots

Plot single or multiple variables over time:

```python
from gas_swelling.io import plot_time_series

# Plot single variable
plot_time_series(
    t=result['t'],
    y=result['swelling'] * 100,
    xlabel='Time (days)',
    ylabel='Swelling (%)',
    title='Gas Swelling Evolution',
    linewidth=2
)

# Plot multiple variables on same axes
fig, ax = plt.subplots()
plot_time_series(result['t']/86400, result['Rcb']*1e9,
                 xlabel='Time (days)',
                 ylabel='Radius (nm)',
                 ax=ax,
                 label='Bulk cavities')
plot_time_series(result['t']/86400, result['Rcf']*1e9,
                 ax=ax,
                 label='Boundary cavities')
ax.legend()
plt.show()
```

#### Dual-Axis Plots

Plot two variables with different scales:

```python
from gas_swelling.io import plot_dual_axis

plot_dual_axis(
    t=result['t'],
    y1=result['swelling'] * 100,
    y2=result['Pg'] / 1e6,
    xlabel1='Time (days)',
    ylabel1='Swelling (%)',
    ylabel2='Pressure (MPa)',
    title1='Swelling and Gas Pressure',
    color1='blue',
    color2='red'
)
```

#### Debug History Plots

Visualize debug information:

```python
from gas_swelling.io import plot_debug_history

plot_debug_history(
    debug_history=debug,
    variables=['Rcb', 'Ncb', 'Pg'],
    time_units='days'
)
```

#### Comparison Plots

Compare multiple simulation results:

```python
from gas_swelling.io import plot_swelling_comparison

# Run simulations at different temperatures
results = []
temperatures = [700, 800, 900]

for T in temperatures:
    params = create_default_parameters()
    params.temperature = T
    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 8.64e6))
    results.append(result)

# Compare swelling curves
plot_swelling_comparison(
    results=results,
    labels=[f'T={T} K' for T in temperatures],
    variable='swelling',
    xlabel='Time (days)',
    ylabel='Swelling (%)',
    title='Temperature Dependence'
)
```

### 3. Optional Dependencies

The I/O module gracefully handles missing matplotlib:

```python
# Install matplotlib for plotting support
pip install matplotlib

# Or install with extras
pip install gas-swelling-model[plotting]

# If matplotlib is not available:
# - All plotting functions return None
# - check_matplotlib_available() returns False
# - Core model functionality still works
```

## Usage Patterns

### Pattern 1: Minimal I/O (Batch Processing)

```python
from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters

# No debug, no plotting
params = create_default_parameters()
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))

# Save results to file
import json
with open('results.json', 'w') as f:
    json.dump({k: v.tolist() for k, v in result.items()}, f)
```

### Pattern 2: Debug Mode (Development)

```python
from gas_swelling import GasSwellingModel
from gas_swelling.io import DebugHistory

# Enable debug tracking
debug = DebugHistory(enabled=True, log_interval=10)

params = create_default_parameters()
model = GasSwellingModel(params, debug_history=debug)
result = model.solve(t_span=(0, 8.64e6))

# Inspect what happened
debug.print_summary()

# Save debug log for later analysis
debug.save('debug_log.json')
```

### Pattern 3: Interactive Visualization (Exploratory)

```python
from gas_swelling import GasSwellingModel
from gas_swelling.io import plot_time_series, plot_dual_axis
import matplotlib.pyplot as plt

params = create_default_parameters()
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))

# Create multiple plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Swelling evolution
plot_time_series(result['t']/86400, result['swelling']*100,
                xlabel='Time (days)',
                ylabel='Swelling (%)',
                ax=axes[0, 0])

# Bubble radius
plot_time_series(result['t']/86400, result['Rcb']*1e9,
                xlabel='Time (days)',
                ylabel='Radius (nm)',
                ax=axes[0, 1])

# Gas concentrations
plot_time_series(result['t']/86400, result['Cgb'],
                xlabel='Time (days)',
                ylabel='Gas conc. (atoms/m³)',
                ax=axes[1, 0])

# Dual-axis: pressure vs radius
plot_dual_axis(result['t']/86400,
               result['Rcb']*1e9,
               result['Pg']/1e6,
               xlabel1='Time (days)',
               ylabel1='Radius (nm)',
               ylabel2='Pressure (MPa)',
               ax=axes[1, 1])

plt.tight_layout()
plt.savefig('swelling_analysis.png', dpi=300)
plt.show()
```

### Pattern 4: Parameter Sweep (Batch + Visualization)

```python
import numpy as np
from gas_swelling import GasSwellingModel
from gas_swelling.io import plot_swelling_comparison
import matplotlib.pyplot as plt

# Parameter sweep
temperatures = np.linspace(600, 1000, 9)
results = []

for T in temperatures:
    print(f"Running T = {T} K")
    params = create_default_parameters()
    params.temperature = T
    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 8.64e6))
    results.append(result)

# Compare results
plot_swelling_comparison(
    results=results,
    labels=[f'{T:.0f} K' for T in temperatures],
    variable='swelling',
    xlabel='Time (days)',
    ylabel='Swelling (%)',
    title='Temperature Dependence of Swelling'
)

plt.savefig('temperature_sweep.png', dpi=300)
```

## Data Export/Import

### Exporting Results

```python
import numpy as np

# Save as text file
header = "time(s) swelling(%) Rcb(m) Pg(Pa)"
data = np.column_stack([
    result['t'],
    result['swelling'] * 100,
    result['Rcb'],
    result['Pg']
])
np.savetxt('results.txt', data, header=header)

# Save as NumPy binary
np.savez('results.npz', **result)

# Save as JSON
import json
with open('results.json', 'w') as f:
    # Convert arrays to lists for JSON serialization
    json_data = {k: v.tolist() for k, v in result.items()}
    json.dump(json_data, f, indent=2)
```

### Importing Results

```python
# Load from NumPy binary
data = np.load('results.npz')
t = data['t']
swelling = data['swelling']

# Load from JSON
import json
with open('results.json', 'r') as f:
    result = json.load(f)
    # Convert lists back to arrays
    result = {k: np.array(v) for k, v in result.items()}
```

## Custom Visualization

### Creating Custom Plots

```python
import matplotlib.pyplot as plt
from gas_swelling.io import setup_chinese_font

setup_chinese_font()

# Custom multi-panel figure
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(3, 2)

# Main swelling plot
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(result['t']/86400, result['swelling']*100, 'b-', linewidth=2)
ax1.set_xlabel('Time (days)')
ax1.set_ylabel('Swelling (%)')
ax1.set_title('Gas Swelling Evolution')
ax1.grid(True)

# Gas pressure
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(result['t']/86400, result['Pg']/1e6, 'r-', linewidth=2)
ax2.set_xlabel('Time (days)')
ax2.set_ylabel('Gas Pressure (MPa)')
ax2.grid(True)

# Bubble radius
ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(result['t']/86400, result['Rcb']*1e9, 'g-', linewidth=2)
ax3.set_xlabel('Time (days)')
ax3.set_ylabel('Bubble Radius (nm)')
ax3.grid(True)

# Point defects
ax4 = fig.add_subplot(gs[2, 0])
ax4.semilogy(result['t']/86400, result['cvb'], label='Vacancies')
ax4.semilogy(result['t']/86400, result['cib'], label='Interstitials')
ax4.set_xlabel('Time (days)')
ax4.set_ylabel('Concentration')
ax4.legend()
ax4.grid(True)

# Gas release
ax5 = fig.add_subplot(gs[2, 1])
ax5.plot(result['t']/86400, result['released_gas']*100, 'k-', linewidth=2)
ax5.set_xlabel('Time (days)')
ax5.set_ylabel('Released Gas (%)')
ax5.grid(True)

plt.tight_layout()
plt.savefig('comprehensive_analysis.png', dpi=300)
plt.show()
```

## Performance Considerations

### Debug Output Overhead

Debug logging **slows down** simulations:
- **No debug**: ~100 seconds for 100-day simulation
- **With debug**: ~150-200 seconds (50-100% slower)

**Recommendation:** Use debug only during development/debugging, not for production runs.

### Visualization Memory

Large plots can consume significant memory:
```python
# BAD: Plotting millions of points
t_eval = np.linspace(0, 8.64e6, 10000000)  # Too many!
result = model.solve(t_span=(0, 8.64e6), t_eval=t_eval)
plt.plot(result['t'], result['swelling'])  # Memory explosion!

# GOOD: Downsample for plotting
t_eval = np.linspace(0, 8.64e6, 1001)  # Reasonable
# Or use adaptive output and let matplotlib handle it
```

## Integration with Model

The I/O module integrates seamlessly with the main model:

```python
from gas_swelling import GasSwellingModel
from gas_swelling.io import DebugHistory, print_simulation_summary

# Enable debug
debug = DebugHistory(enabled=True)

# Run simulation
model = GasSwellingModel(params, debug_history=debug)
result = model.solve(t_span=(0, 8.64e6))

# Print summary
print_simulation_summary(result, params)

# Plot results
if check_matplotlib_available():
    plot_time_series(result['t']/86400, result['swelling']*100,
                    xlabel='Time (days)',
                    ylabel='Swelling (%)')
```

## Dependencies

**Required:**
- `numpy` - Array operations
- `typing` - Type hints

**Optional:**
- `matplotlib` >= 3.3.0 - Plotting and visualization
  - Install with: `pip install matplotlib`

## Testing

Unit tests for I/O functions:
```bash
pytest tests/io/test_debug_output.py
pytest tests/io/test_visualization.py
```

Test coverage:
- Debug history save/load
- Plotting functions (with matplotlib available)
- Graceful handling when matplotlib unavailable
- Data export/import formats

## Future Extensions

Potential additions to the I/O module:
- **HDF5 support**: Efficient binary format for large datasets
- **Interactive plots**: Plotly/Bokeh for web-based visualization
- **3D visualization**: VTK/Mayavi for spatial representations
- **Real-time monitoring**: WebSocket-based live updates
- **Database integration**: Store results in SQL databases
- **Animation**: Time-lapse videos of evolution
- **Report generation**: Automated PDF reports with figures

## Best Practices

1. **Use debug sparingly** - Only enable when troubleshooting
2. **Save intermediate results** - For long simulations, checkpoint periodically
3. **Choose appropriate output** - `t_eval=None` for adaptive, `t_eval=...` for specific times
4. **Handle missing matplotlib** - Always check `check_matplotlib_available()` before plotting
5. **Downsample for plotting** - Don't plot millions of points
6. **Document custom plots** - Add labels, titles, legends for clarity

---

**For model usage, see:** `../models/README.md`
**For solver configuration, see:** `../solvers/README.md`
**For parameter definitions, see:** `../params/README.md`
