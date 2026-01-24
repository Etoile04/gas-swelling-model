# Gas Swelling Visualization Module

A comprehensive visualization toolkit for the Gas Swelling Model package. This module provides powerful plotting and visualization capabilities for analyzing fission gas bubble evolution and void swelling behavior in irradiated metallic fuels.

## Overview

The visualization module offers a complete suite of tools for creating publication-quality figures and interactive visualizations. It is organized into four main categories:

- **📊 Evolution Plots**: Time-series visualization of state variables and derived quantities
- **🔥 Parameter Sweeps**: Temperature and parameter sensitivity analysis visualizations
- **⚖️ Comparison Plots**: Bulk vs. interface comparisons, gas distribution, and correlation analysis
- **🛠️ Utilities**: Style configuration, figure management, unit conversions, and formatting helpers

## Key Features

✅ **Publication-Quality Output**: Built-in styles for scientific publications with customizable DPI and formats
✅ **Comprehensive Coverage**: Visualizations for all 10 state variables plus derived quantities
✅ **Flexible API**: Both high-level convenience functions and low-level customization
✅ **Consistent Styling**: Unified color palettes and formatting across all plot types
✅ **Batch Processing**: Efficient multi-panel plots and parameter sweep visualizations
✅ **Unit Handling**: Automatic time/length unit conversions and formatting

## Installation

The visualization module is part of the gas_swelling package. Install the complete package:

```bash
pip install gas-swelling
```

Or install with visualization dependencies:

```bash
pip install gas-swelling[visualization]
```

**Dependencies:**
- `matplotlib >= 3.5`
- `numpy >= 1.20`
- `scipy >= 1.7`

## Quick Start

### Basic Evolution Plot

```python
from gas_swelling import GasSwellingModel, MaterialParameters, SimulationParameters
from gas_swelling.visualization import plot_swelling_evolution

# Set up and run simulation
params = MaterialParameters(temperature=950, fission_rate=4.5e19)
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 100*24*3600), t_eval=np.linspace(0, 100*24*3600, 100))

# Create visualization
fig, ax = plot_swelling_evolution(result, time_unit='days')
fig.savefig('swelling_evolution.png', dpi=300)
```

### Multi-Panel Visualization

```python
from gas_swelling.visualization import plot_multi_panel_evolution

# Create comprehensive 6-panel plot
fig = plot_multi_panel_evolution(
    result,
    time_unit='days',
    variables=['swelling', 'Rcb', 'Rcf', 'Pg', 'Cgb', 'Cgf']
)
fig.savefig('multi_panel.png', dpi=300, bbox_inches='tight')
```

### Parameter Sweep

```python
from gas_swelling.visualization import plot_temperature_sweep

# Run temperature sweep
temperatures = np.linspace(700, 1000, 7)
results = [run_simulation(T) for T in temperatures]

# Visualize temperature dependence
fig, ax = plot_temperature_sweep(
    results,
    temperatures,
    variable='swelling',
    time_unit='days'
)
fig.savefig('temperature_sweep.png')
```

## 📘 Usage by Category

### Evolution Plots

Visualize how variables change over time during irradiation.

#### Swelling Evolution

```python
from gas_swelling.visualization import plot_swelling_evolution

fig, ax = plot_swelling_evolution(
    result,
    time_unit='days',  # 'seconds', 'hours', 'days', 'years'
    show_gas_release=True,
    figsize=(8, 6)
)
ax.set_title('Void Swelling vs. Irradiation Time')
```

#### Bubble Radius Evolution

```python
from gas_swelling.visualization import plot_bubble_radius_evolution

fig, ax = plot_bubble_radius_evolution(
    result,
    time_unit='days',
    length_unit='nm',  # 'm', 'um', 'nm'
    compare_bulk_interface=True  # Show both bulk and interface bubbles
)
```

#### Gas Pressure Evolution

```python
from gas_swelling.visualization import plot_gas_pressure_evolution

fig, ax = plot_gas_pressure_evolution(
    result,
    time_unit='days',
    pressure_unit='MPa',  # 'Pa', 'MPa', 'GPa'
    show_critical_pressure=True
)
```

#### Multi-Panel Evolution

```python
from gas_swelling.visualization import plot_multi_panel_evolution

# Create custom 4-panel plot
fig = plot_multi_panel_evolution(
    result,
    time_unit='days',
    variables=['swelling', 'Rcb', 'Pg', 'Cgb'],
    nrows=2,
    ncols=2,
    figsize=(12, 10)
)
```

**Available evolution plot functions:**
- `plot_swelling_evolution` - Total swelling over time
- `plot_bubble_radius_evolution` - Bubble radius (bulk/interface)
- `plot_gas_concentration_evolution` - Gas concentration in matrix
- `plot_bubble_concentration_evolution` - Cavity/bubble density
- `plot_gas_atoms_evolution` - Gas atoms per cavity
- `plot_gas_pressure_evolution` - Internal bubble pressure
- `plot_defect_concentration_evolution` - Vacancy/interstitial concentrations
- `plot_released_gas_evolution` - Cumulative gas release fraction
- `plot_multi_panel_evolution` - Custom multi-panel layouts

---

### Parameter Sweeps

Analyze how model outputs vary with parameters.

#### Temperature Sweep

```python
from gas_swelling.visualization import plot_temperature_sweep

temperatures = [700, 800, 900, 950, 1000]  # Kelvin
sweep_results = [run_simulation(T) for T in temperatures]

fig, ax = plot_temperature_sweep(
    sweep_results,
    temperatures,
    variable='swelling',  # Any result variable
    time_unit='days',
    show_individual_runs=False,  # Show only mean/std
    error_band=True
)
ax.set_title('Temperature Dependence of Swelling')
```

#### Multi-Variable Temperature Sweep

```python
from gas_swelling.visualization import plot_multi_param_temperature_sweep

fig = plot_multi_param_temperature_sweep(
    sweep_results,
    temperatures,
    variables=['swelling', 'Rcb', 'Rcf', 'Pg'],
    time_unit='days',
    nrows=2,
    ncols=2,
    figsize=(12, 10)
)
```

#### Parameter Sensitivity Analysis

```python
from gas_swelling.visualization import plot_parameter_sensitivity

param_name = 'dislocation_density'
param_values = [1e13, 5e13, 1e14, 5e14, 1e15]  # m^-2
sensitivity_results = [run_simulation(**{param_name: val}) for val in param_values]

fig, ax = plot_parameter_sensitivity(
    sensitivity_results,
    param_values,
    param_name=param_name,
    output_variable='swelling',
    time_point=-1,  # Final time point
    x_scale='log'  # Log scale for parameter axis
)
```

#### Arrhenius Analysis

```python
from gas_swelling.visualization import plot_arrhenius_analysis

# Extract swelling rates at different temperatures
swelling_rates = [extract_swelling_rate(r) for r in sweep_results]

fig, ax = plot_arrhenius_analysis(
    temperatures,
    swelling_rates,
    activation_energy_guess=2.5,  # eV
    temperature_range=(700, 1000)
)
```

**Available parameter sweep functions:**
- `plot_temperature_sweep` - Single variable temperature dependence
- `plot_multi_param_temperature_sweep` - Multiple variables at once
- `plot_parameter_sensitivity` - Generic parameter sensitivity
- `plot_arrhenius_analysis` - Activation energy analysis

---

### Comparison Plots

Compare different aspects of the simulation results.

#### Bulk vs. Interface Comparison

```python
from gas_swelling.visualization import compare_bulk_interface

fig = compare_bulk_interface(
    result,
    time_unit='days',
    variables=['swelling', 'R', 'Pg', 'Cc'],
    nrows=2,
    ncols=2,
    figsize=(12, 10)
)
```

#### Gas Distribution Pie Chart

```python
from gas_swelling.visualization import plot_gas_distribution_pie

fig, ax = plot_gas_distribution_pie(
    result,
    time_point=-1,  # Final time point
    autopct='%1.1f%%',
    colors=None  # Use default palette
)
```

#### Gas Distribution Evolution

```python
from gas_swelling.visualization import plot_gas_distribution_evolution

fig, ax = plot_gas_distribution_evolution(
    result,
    time_unit='days',
    stacked=True,
    alpha=0.8
)
```

#### Correlation Matrix

```python
from gas_swilling.visualization import plot_correlation_matrix

fig, ax = plot_correlation_matrix(
    result,
    variables=['swelling', 'Rcb', 'Rcf', 'Pg', 'Cgb', 'Cgf'],
    time_point=-1,
    cmap='RdBu_r',  # Red-blue colormap
    annot=True  # Show correlation values
)
```

**Available comparison functions:**
- `compare_bulk_interface` - Side-by-side bulk/interface plots
- `plot_bulk_interface_ratio` - Bulk-to-interface ratios
- `plot_gas_distribution_pie` - Gas location pie chart
- `plot_gas_distribution_evolution` - Time evolution of distribution
- `plot_correlation_matrix` - Variable correlation heatmap
- `plot_phase_comparison` - Multi-phase comparisons

---

### Core Plotter Class

For advanced users, the `GasSwellingPlotter` class provides maximum flexibility:

```python
from gas_swelling.visualization import GasSwellingPlotter

# Create plotter with custom settings
plotter = GasSwellingPlotter(
    time_unit='days',
    length_unit='nm',
    style='publication',
    color_palette='default'
)

# Run simulation with result tracking
model = GasSwellingModel(params)
result = model.solve(
    t_span=(0, 100*24*3600),
    t_eval=time_points,
    debug_history=True  # Required for plotter
)

# Attach result to plotter
plotter.attach_result(result)

# Create custom plots
fig, ax = plotter.plot_variable('swelling')
plotter.add_threshold_line(ax, 0.1, label='10% swelling')
plotter.add_annotation(ax, x=50, y=0.05, text='Rapid growth phase')
```

---

## 🛠️ Utilities

### Style Configuration

```python
from gas_swelling.visualization import apply_publication_style, get_publication_style

# Apply publication style globally
apply_publication_style(style='nature')  # 'nature', 'science', 'ieee'

# Or get style dict for custom use
style = get_publication_style('nature')
```

### Color Palettes

```python
from gas_swelling.visualization import get_color_palette

colors = get_color_palette('default')  # 'default', 'colorblind', 'viridis'
```

### Figure Utilities

```python
from gas_swelling.visualization import save_figure, create_figure_grid, add_subfigure_labels

# Save with options
save_figure(
    fig,
    'output.png',
    dpi=300,
    bbox_inches='tight',
    transparent=True
)

# Create grid layout
fig, axes = create_figure_grid(nrows=2, ncols=3, figsize=(15, 10))

# Add subfigure labels
add_subfigure_labels(fig, labels=['a', 'b', 'c', 'd', 'e', 'f'])
```

### Unit Conversions

```python
from gas_swelling.visualization import convert_time_units, convert_length_units, calculate_burnup

# Time conversion
time_days = convert_time_units(time_seconds, from_unit='seconds', to_unit='days')

# Length conversion
radius_nm = convert_length_units(radius_m, from_unit='m', to_unit='nm')

# Burnup calculation
burnup_percent = calculate_burnup(result, fission_density)
```

### Axis Formatting

```python
from gas_swelling.visualization import format_axis_scientific, set_axis_limits

# Scientific notation
ax = format_axis_scientific(ax, axis='y')  # 'x', 'y', or 'both'

# Set limits with padding
ax = set_axis_limits(ax, xlim=(0, 100), ylim=(0, 1), padding=0.05)
```

---

## Advanced Usage

### Custom Multi-Panel Layouts

```python
import matplotlib.pyplot as plt
from gas_swelling.visualization import plot_swelling_evolution, plot_bubble_radius_evolution

fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Custom layout
ax1 = fig.add_subplot(gs[0, :])  # Top row spans both columns
ax2 = fig.add_subplot(gs[1, 0])
ax3 = fig.add_subplot(gs[1, 1])
ax4 = fig.add_subplot(gs[2, 0])
ax5 = fig.add_subplot(gs[2, 1])

plot_swelling_evolution(result, ax=ax1, time_unit='days')
plot_bubble_radius_evolution(result, ax=ax2, time_unit='days')
# ... add more plots

fig.savefig('custom_layout.png', dpi=300)
```

### Animation Support

```python
import matplotlib.animation as animation

fig, ax = plt.subplots()
line, = ax.plot([], [], 'b-', linewidth=2)

def animate(i):
    line.set_data(time[:i], swelling[:i])
    ax.set_xlim(0, time[-1])
    ax.set_ylim(0, max(swelling))
    return line,

anim = animation.FuncAnimation(fig, animate, frames=len(time), interval=50)
anim.save('swelling_animation.mp4', writer='ffmpeg', fps=30)
```

### Batch Processing

```python
from gas_swelling.visualization import plot_multi_panel_evolution

# Process multiple simulations
for i, params in enumerate(parameter_sets):
    result = run_simulation(params)
    fig = plot_multi_panel_evolution(result, time_unit='days')
    fig.savefig(f'simulation_{i:03d}.png', dpi=300)
    plt.close(fig)
```

---

## Publication-Quality Figures

### IEEE Style

```python
from gas_swelling.visualization import apply_publication_style

apply_publication_style('ieee')

# Your plotting code
fig, ax = plot_swelling_evolution(result, time_unit='days')
fig.savefig('ieee_figure.pdf', dpi=600, bbox_inches='tight')
```

### Nature Style

```python
apply_publication_style('nature')

fig, ax = plot_swelling_evolution(result, time_unit='days')
fig.savefig('nature_figure.pdf', dpi=600, bbox_inches='tight')
```

### Custom Styling

```python
# Create custom style
custom_style = {
    'font.size': 12,
    'axes.linewidth': 1.5,
    'xtick.major.width': 1.2,
    'ytick.major.width': 1.2,
    'figure.facecolor': 'white',
    'axes.grid': True,
    'grid.alpha': 0.3
}

plt.rcParams.update(custom_style)

# Your plotting code
```

---

## Tips and Best Practices

### Performance

- **For exploratory work**: Use `dpi=150` for faster rendering
- **For publications**: Use `dpi=300` or higher
- **Vector formats**: Use PDF or EPS for scalability
- **Large datasets**: Downsample time points for faster plotting

```python
# Downsample for visualization
t_eval = np.linspace(0, sim_time, 100)  # Instead of 1000
```

### Consistent Styling

```python
# Use the same color palette across figures
colors = get_color_palette('default')

for i, variable in enumerate(variables):
    ax.plot(time, result[variable], color=colors[i], label=variable)
```

### Figure Organization

```python
# Use descriptive filenames
fig.savefig('swelling_T950K_4.5e19_100days.png')

# Include metadata in filename
import datetime
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
fig.savefig(f'swelling_{timestamp}.png')
```

### Debugging Plots

```python
# Check result structure
print(result.keys())
print(result['time'].shape)
print(result['swelling'].shape)

# Verify data ranges
print(f"Swelling range: {result['swelling'].min():.3f} - {result['swelling'].max():.3f}")
```

---

## API Reference

For complete API documentation, see:

- **Core**: [core.py](core.py) - `GasSwellingPlotter` class
- **Evolution**: [evolution_plots.py](evolution_plots.py) - Time series functions
- **Sweeps**: [parameter_sweeps.py](parameter_sweeps.py) - Parameter analysis
- **Comparison**: [comparison_plots.py](comparison_plots.py) - Comparison visualizations
- **Utilities**: [utils.py](utils.py) - Helper functions

---

## Examples

### Complete Workflow Example

```python
import numpy as np
from gas_swelling import GasSwellingModel, MaterialParameters, SimulationParameters
from gas_swelling.visualization import (
    plot_multi_panel_evolution,
    apply_publication_style,
    save_figure
)

# 1. Set up simulation
params = MaterialParameters(
    temperature=950,
    fission_rate=4.5e19,
    eos_model='ronchi'
)

# 2. Run simulation
model = GasSwellingModel(params)
sim_time = 100 * 24 * 3600  # 100 days in seconds
time_points = np.linspace(0, sim_time, 200)

result = model.solve(
    t_span=(0, sim_time),
    t_eval=time_points,
    debug_history=True
)

# 3. Apply publication style
apply_publication_style('nature')

# 4. Create multi-panel figure
fig = plot_multi_panel_evolution(
    result,
    time_unit='days',
    variables=['swelling', 'Rcb', 'Rcf', 'Pg', 'Cgb', 'Cgf'],
    nrows=2,
    ncols=3,
    figsize=(15, 10)
)

# 5. Save publication-quality figure
save_figure(
    fig,
    'swelling_analysis_nature.pdf',
    dpi=600,
    bbox_inches='tight',
    transparent=False
)
```

### Parameter Study Example

```python
import matplotlib.pyplot as plt
from gas_swelling.visualization import plot_temperature_sweep

# Run temperature sweep
temperatures = np.linspace(700, 1000, 7)
sweep_results = []

for T in temperatures:
    params = MaterialParameters(temperature=T)
    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, sim_time), t_eval=time_points)
    sweep_results.append(result)

# Visualize
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
plot_temperature_sweep(sweep_results, temperatures, 'swelling', ax=axes[0, 0])
plot_temperature_sweep(sweep_results, temperatures, 'Rcb', ax=axes[0, 1])
plot_temperature_sweep(sweep_results, temperatures, 'Pg', ax=axes[1, 0])
plot_temperature_sweep(sweep_results, temperatures, 'Cgb', ax=axes[1, 1])

plt.tight_layout()
plt.savefig('temperature_comprehensive.pdf', dpi=300)
```

---

## Getting Help

- **Documentation**: See docstrings for each function (e.g., `help(plot_swelling_evolution)`)
- **Examples**: Check [examples/](../examples/) for complete working examples
- **Issues**: Report bugs or request features via the project issue tracker
- **API Reference**: See module source code for detailed implementation

---

## Contributing

Contributions to the visualization module are welcome! Areas for improvement:

- Additional plot types (3D visualizations, contour plots)
- Interactive plotting with Plotly or Bokeh
- Animation utilities
- Custom colormaps
- Additional publication style presets

---

**Happy Visualizing! 📊**

For the complete project documentation, see the [main README](../README.md).
