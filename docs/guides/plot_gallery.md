# Plot Gallery: Code Snippets & Examples

**Target Audience:** Researchers and students visualizing gas swelling simulation results
**Reading Time:** ~35 minutes
**Prerequisites:** Completion of [30-minute quickstart](../tutorials/30minute_quickstart.md)

---

## Learning Objectives

After exploring this gallery, you will be able to:

- ✓ Create 10+ different types of plots for simulation results
- ✓ Customize plot styles for presentations and publications
- ✓ Compare results across multiple simulation conditions
- ✓ Visualize gas distribution and evolution
- ✓ Generate publication-quality multi-panel figures

---

## Table of Contents

1. [Basic Time Series Plots](#basic-time-series-plots)
2. [Bubble Evolution Plots](#bubble-evolution-plots)
3. [Gas Distribution Visualizations](#gas-distribution-visualizations)
4. [Temperature Comparison Plots](#temperature-comparison-plots)
5. [Multi-Panel Summary Figures](#multi-panel-summary-figures)
6. [Bulk vs Interface Comparisons](#bulk-vs-interface-comparisons)
7. [Parameter Sweep Visualizations](#parameter-sweep-visualizations)
8. [Publication-Quality Figures](#publication-quality-figures)
9. [Advanced Analysis Plots](#advanced-analysis-plots)
10. [Custom Styled Plots](#custom-styled-plots)
11. [Gas Release Analysis](#gas-release-analysis)
12. [Arrhenius Analysis](#arrhenius-analysis)

---

## Basic Time Series Plots

### 1. Swelling Evolution Over Time

**What it shows:** How fuel swelling progresses during irradiation

**When to use:** Basic analysis of swelling behavior, presentations

```python
import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Run simulation
params = create_default_parameters()
model = GasSwellingModel(params)

sim_time = 100 * 24 * 3600  # 100 days in seconds
t_eval = np.linspace(0, sim_time, 200)
result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

# Calculate swelling
V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
swelling = (V_bubble_b + V_bubble_f) * 100  # Convert to percent

# Create plot
time_days = result['time'] / (24 * 3600)
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(time_days, swelling, linewidth=2.5, color='#2E86AB')
ax.fill_between(time_days, swelling, alpha=0.3, color='#2E86AB')

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Swelling (%)', fontsize=12, fontweight='bold')
ax.set_title('Fuel Swelling Evolution', fontsize=14, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('swelling_evolution.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Monotonically increasing curve
- Initial slow growth (incubation period)
- Accelerating growth phase
- Possible approach to steady-state

---

### 2. Bubble Radius Evolution

**What it shows:** Growth of bubbles in bulk vs at phase boundaries

**When to use:** Understanding microstructure evolution

```python
# Using the same result from above

fig, ax = plt.subplots(figsize=(10, 6))

time_days = result['time'] / (24 * 3600)
ax.plot(time_days, result['Rcb'] * 1e9,
        label='Bulk Bubbles', linewidth=2, color='#2E86AB')
ax.plot(time_days, result['Rcf'] * 1e9,
        label='Interface Bubbles', linewidth=2, color='#A23B72', linestyle='--')

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Bubble Radius (nm)', fontsize=12, fontweight='bold')
ax.set_title('Bubble Growth Comparison', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('bubble_radius.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Interface bubbles grow faster than bulk bubbles
- Typical size ratio: Rcf/Rcb ≈ 5-20x
- Logarithmic-style growth at long times

---

## Bubble Evolution Plots

### 3. Bubble Concentration Evolution (Log Scale)

**What it shows:** Number density of bubbles over time

**When to use:** Analyzing nucleation and growth dynamics

```python
fig, ax = plt.subplots(figsize=(10, 6))

time_days = result['time'] / (24 * 3600)
ax.semilogy(time_days, result['Ccb'],
            label='Bulk Bubbles', linewidth=2, color='#2E86AB')
ax.semilogy(time_days, result['Ccf'],
            label='Interface Bubbles', linewidth=2, color='#A23B72', linestyle='--')

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Bubble Concentration (cavities/m³)', fontsize=12, fontweight='bold')
ax.set_title('Bubble Nucleation and Coarsening', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('bubble_concentration.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Initial nucleation phase (rapid increase)
- Possible decline due to coarsening (Ostwald ripening)
- Interface concentration typically higher than bulk

---

### 4. Gas Atoms per Bubble

**What it shows:** How gas accumulates in individual bubbles

**When to use:** Understanding bubble growth mechanisms

```python
fig, ax = plt.subplots(figsize=(10, 6))

time_days = result['time'] / (24 * 3600)
ax.semilogy(time_days, result['Ncb'],
            label='Bulk Bubbles', linewidth=2, color='#2E86AB')
ax.semilogy(time_days, result['Ncf'],
            label='Interface Bubbles', linewidth=2, color='#A23B72', linestyle='--')

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Gas Atoms per Bubble', fontsize=12, fontweight='bold')
ax.set_title('Gas Accumulation in Bubbles', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('gas_atoms_per_bubble.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Monotonic increase (gas continuously accumulates)
- Interface bubbles contain more atoms than bulk
- Values typically: 10² - 10⁵ atoms per bubble

---

## Gas Distribution Visualizations

### 5. Gas Distribution Pie Chart (Simplified)

**What it shows:** Where gas resides at end of simulation

**When to use:** Quick overview of gas partitioning

```python
# Calculate gas distribution at final time
Cgb = result['Cgb'][-1]  # Bulk solution
Cgf = result['Cgf'][-1]  # Interface solution
Ccb = result['Ccb'][-1]  # Bulk bubble concentration
Ccf = result['Ccf'][-1]  # Interface bubble concentration
Ncb = result['Ncb'][-1]  # Gas atoms per bulk bubble
Ncf = result['Ncf'][-1]  # Gas atoms per interface bubble
released = result['released_gas'][-1]

# Calculate totals
gas_in_solution = Cgb + Cgf
gas_in_bubbles = Ccb * Ncb + Ccf * Ncf
total_gas = gas_in_solution + gas_in_bubbles + released

# Create pie chart
labels = ['In Solution', 'In Bubbles', 'Released']
sizes = [
    gas_in_solution / total_gas * 100,
    gas_in_bubbles / total_gas * 100,
    released / total_gas * 100
]
colors = ['#06A77D', '#F4845F', '#8E44AD']

fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    sizes, labels=labels, colors=colors,
    autopct='%1.1f%%', startangle=90,
    explode=[0.02, 0.02, 0.02]
)

# Make percentage text bold
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(12)

ax.set_title('Gas Distribution at Final Time',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('gas_pie_chart.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Most gas typically in bubbles (>80%)
- Small fraction in solution at high burnup
- Release fraction depends on temperature and swelling

---

### 6. Gas Distribution Evolution (Stacked Area)

**What it shows:** How gas redistributes over time

**When to use:** Understanding gas migration dynamics

```python
# Calculate gas distribution over time
gas_in_solution = result['Cgb'] + result['Cgf']
gas_in_bubbles = result['Ccb'] * result['Ncb'] + result['Ccf'] * result['Ncf']
gas_released = result['released_gas']

# Normalize to get fractions
total = gas_in_solution + gas_in_bubbles + gas_released
frac_solution = gas_in_solution / total * 100
frac_bubbles = gas_in_bubbles / total * 100
frac_released = gas_released / total * 100

# Create stacked area plot
time_days = result['time'] / (24 * 3600)
fig, ax = plt.subplots(figsize=(12, 6))

ax.stackplot(time_days, [frac_solution, frac_bubbles, frac_released],
             labels=['In Solution', 'In Bubbles', 'Released'],
             colors=['#06A77D', '#F4845F', '#8E44AD'], alpha=0.8)

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Gas Fraction (%)', fontsize=12, fontweight='bold')
ax.set_title('Gas Distribution Evolution', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=11)
ax.set_ylim(0, 100)
ax.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig('gas_distribution_evolution.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Initial: Most gas in solution
- Evolution: Gas migrates to bubbles
- Final: Most gas in bubbles, some release if interconnection occurs

---

## Temperature Comparison Plots

### 7. Temperature Sweep: Swelling vs Temperature

**What it shows:** How swelling varies with operating temperature

**When to use:** Optimizing operating conditions, validation studies

```python
# Run simulations at multiple temperatures
temperatures = [600, 700, 800, 900]  # Kelvin
final_swellings = []

for T in temperatures:
    params = create_default_parameters()
    params['temperature'] = T
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 200)
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Calculate final swelling
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100
    final_swellings.append(swelling[-1])

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(temperatures, final_swellings, 'o-',
        linewidth=2.5, markersize=10,
        markeredgecolor='white', markeredgewidth=1.5,
        color='#E63946')
ax.fill_between(temperatures, final_swellings, alpha=0.2, color='#E63946')

ax.set_xlabel('Temperature (K)', fontsize=12, fontweight='bold')
ax.set_ylabel('Final Swelling (%)', fontsize=12, fontweight='bold')
ax.set_title('Temperature Dependence of Swelling', fontsize=14, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.6)

# Add peak temperature annotation
peak_idx = np.argmax(final_swellings)
peak_T = temperatures[peak_idx]
peak_swelling = final_swellings[peak_idx]
ax.annotate(f'Peak: {peak_swelling:.2f}% at {peak_T} K',
            xy=(peak_T, peak_swelling),
            xytext=(peak_T+30, peak_swelling+0.2),
            fontsize=10, fontweight='bold',
            arrowprops=dict(arrowstyle='->', lw=1.5))

plt.tight_layout()
plt.savefig('swelling_vs_temperature.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Bell-shaped curve
- Peak swelling around 750-850 K
- Low swelling at very low and very high temperatures

---

### 8. Temperature Comparison: Time Evolution

**What it shows:** Swelling progression at different temperatures

**When to use:** Comparing kinetics at different operating conditions

```python
# Collect full time series for each temperature
results_by_temp = {}
for T in temperatures:
    params = create_default_parameters()
    params['temperature'] = T
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 200)
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    result['swelling'] = (V_bubble_b + V_bubble_f) * 100
    result['time_days'] = result['time'] / (24 * 3600)
    results_by_temp[T] = result

# Create comparison plot with colormap
fig, ax = plt.subplots(figsize=(12, 7))

cmap = plt.get_cmap('viridis')
colors = cmap(np.linspace(0, 1, len(temperatures)))

for i, T in enumerate(temperatures):
    r = results_by_temp[T]
    ax.plot(r['time_days'], r['swelling'],
            label=f'{T} K', linewidth=2.5, color=colors[i])

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Swelling (%)', fontsize=12, fontweight='bold')
ax.set_title('Swelling Evolution at Different Temperatures',
             fontsize=14, fontweight='bold')
ax.legend(fontsize=11, ncol=2)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('swelling_temperature_comparison.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Higher T → faster swelling kinetics
- Different asymptotic values
- Crossing patterns possible depending on conditions

---

## Multi-Panel Summary Figures

### 9. Comprehensive 2×2 Summary

**What it shows:** Key variables in one figure

**When to use:** Presentations, reports, quick overview

```python
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Gas Swelling Simulation Summary', fontsize=16, fontweight='bold')

time_days = result['time'] / (24 * 3600)

# Panel (a): Swelling
V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
swelling = (V_bubble_b + V_bubble_f) * 100

axes[0, 0].plot(time_days, swelling, linewidth=2, color='#2E86AB')
axes[0, 0].fill_between(time_days, swelling, alpha=0.3, color='#2E86AB')
axes[0, 0].set_ylabel('Swelling (%)', fontsize=11, fontweight='bold')
axes[0, 0].set_title('(a) Swelling Evolution', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].text(0.02, 0.98, '(a)', transform=axes[0, 0].transAxes,
                fontsize=14, fontweight='bold', va='top')

# Panel (b): Bubble radius
axes[0, 1].plot(time_days, result['Rcb'] * 1e9,
                label='Bulk', linewidth=2, color='#2E86AB')
axes[0, 1].plot(time_days, result['Rcf'] * 1e9,
                label='Interface', linewidth=2, color='#A23B72', linestyle='--')
axes[0, 1].set_ylabel('Radius (nm)', fontsize=11, fontweight='bold')
axes[0, 1].set_title('(b) Bubble Growth', fontsize=12, fontweight='bold')
axes[0, 1].legend(fontsize=10)
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].text(0.02, 0.98, '(b)', transform=axes[0, 1].transAxes,
                fontsize=14, fontweight='bold', va='top')

# Panel (c): Bubble concentration
axes[1, 0].semilogy(time_days, result['Ccb'],
                    label='Bulk', linewidth=2, color='#2E86AB')
axes[1, 0].semilogy(time_days, result['Ccf'],
                    label='Interface', linewidth=2, color='#A23B72', linestyle='--')
axes[1, 0].set_xlabel('Time (days)', fontsize=11, fontweight='bold')
axes[1, 0].set_ylabel('Concentration (m⁻³)', fontsize=11, fontweight='bold')
axes[1, 0].set_title('(c) Bubble Concentration', fontsize=12, fontweight='bold')
axes[1, 0].legend(fontsize=10)
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].text(0.02, 0.98, '(c)', transform=axes[1, 0].transAxes,
                fontsize=14, fontweight='bold', va='top')

# Panel (d): Gas atoms per bubble
axes[1, 1].semilogy(time_days, result['Ncb'],
                    label='Bulk', linewidth=2, color='#2E86AB')
axes[1, 1].semilogy(time_days, result['Ncf'],
                    label='Interface', linewidth=2, color='#A23B72', linestyle='--')
axes[1, 1].set_xlabel('Time (days)', fontsize=11, fontweight='bold')
axes[1, 1].set_ylabel('Gas Atoms per Bubble', fontsize=11, fontweight='bold')
axes[1, 1].set_title('(d) Gas Content', fontsize=12, fontweight='bold')
axes[1, 1].legend(fontsize=10)
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].text(0.02, 0.98, '(d)', transform=axes[1, 1].transAxes,
                fontsize=14, fontweight='bold', va='top')

plt.tight_layout()
plt.savefig('summary_2x2.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Four panels showing different aspects
- Consistent styling across panels
- Panel labels (a), (b), (c), (d) for referencing

---

## Bulk vs Interface Comparisons

### 10. Bulk vs Interface: Multi-Variable Comparison

**What it shows:** Side-by-side comparison of bulk and interface behavior

**When to use:** Understanding where interface effects dominate

```python
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Bulk vs Interface Behavior Comparison',
             fontsize=14, fontweight='bold')

time_days = result['time'] / (24 * 3600)

# Define variables to compare
variables = [
    ('Rcb', 'Rcf', 'Bubble Radius', 'nm', 1e9, False),
    ('Ccb', 'Ccf', 'Bubble Concentration', 'm⁻³', 1, True),
    ('Ncb', 'Ncf', 'Gas Atoms per Bubble', 'atoms', 1, True),
    ('Cgb', 'Cgf', 'Gas Concentration', 'atoms/m³', 1, True),
    ('cvb', 'cvf', 'Vacancy Concentration', '', 1, True),
    ('cib', 'cif', 'Interstitial Concentration', '', 1, True)
]

axes_flat = axes.flatten()

for idx, (bulk_key, interface_key, title, unit, scale, use_log) in enumerate(variables):
    ax = axes_flat[idx]

    bulk_data = result[bulk_key] * scale
    interface_data = result[interface_key] * scale

    if use_log:
        ax.semilogy(time_days, bulk_data, label='Bulk',
                   linewidth=2, color='#2E86AB')
        ax.semilogy(time_days, interface_data, label='Interface',
                   linewidth=2, color='#A23B72', linestyle='--')
    else:
        ax.plot(time_days, bulk_data, label='Bulk',
               linewidth=2, color='#2E86AB')
        ax.plot(time_days, interface_data, label='Interface',
               linewidth=2, color='#A23B72', linestyle='--')

    ax.set_xlabel('Time (days)', fontsize=10)
    ax.set_ylabel(f'{title} ({unit})' if unit else title, fontsize=10)
    ax.set_title(f'({chr(97+idx)}) {title}', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bulk_interface_comparison.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Six panels comparing bulk vs interface
- Log scales for exponential variables
- Clear visualization of interface enhancement effects

---

## Parameter Sweep Visualizations

### 11. Fission Rate Sweep

**What it shows:** How fission rate affects swelling behavior

**When to use:** Understanding power level effects

```python
# Run simulations at different fission rates
fission_rates = [1e19, 5e19, 1e20, 2e20]  # fissions/m³/s
results_by_fission = []

for fr in fission_rates:
    params = create_default_parameters()
    params['fission_rate'] = fr
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 200)
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    result['swelling'] = (V_bubble_b + V_bubble_f) * 100
    result['time_days'] = result['time'] / (24 * 3600)
    results_by_fission.append(result)

# Create plot
fig, ax = plt.subplots(figsize=(12, 7))

colors = ['#F18F01', '#C73E1D', '#8E44AD', '#2E86AB']

for i, (fr, r) in enumerate(zip(fission_rates, results_by_fission)):
    ax.plot(r['time_days'], r['swelling'],
            label=f'{fr:.1e} fissions/m³/s', linewidth=2.5, color=colors[i])

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Swelling (%)', fontsize=12, fontweight='bold')
ax.set_title('Fission Rate Effect on Swelling', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('fission_rate_sweep.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Higher fission rate → faster swelling kinetics
- Higher gas production → more bubbles
- Approximately linear relationship at early times

---

## Publication-Quality Figures

### 12. Journal-Style Multi-Panel Figure

**What it shows:** Publication-ready figure for scientific papers

**When to use:** Journal submissions, technical reports

```python
# Set publication style
plt.rcParams['font.size'] = 8
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['lines.linewidth'] = 1.2

# Create figure (double column width = 7 inches)
fig, axes = plt.subplots(2, 3, figsize=(7, 5))
fig.suptitle('Gas Swelling Model Results', fontsize=10, fontweight='bold')

time_days = result['time'] / (24 * 3600)

# Panel (a): Swelling
axes[0, 0].plot(time_days, swelling, 'k-', linewidth=1.2)
axes[0, 0].set_ylabel('Swelling (%)', fontsize=8)
axes[0, 0].set_title('(a)', fontsize=9, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].text(0.02, 0.98, '(a)', transform=axes[0, 0].transAxes,
                fontsize=10, fontweight='bold', va='top')

# Panel (b): Bubble radius
axes[0, 1].plot(time_days, result['Rcb'] * 1e9, 'b-', linewidth=1.2, label='Bulk')
axes[0, 1].plot(time_days, result['Rcf'] * 1e9, 'r--', linewidth=1.2, label='Interface')
axes[0, 1].set_ylabel('Radius (nm)', fontsize=8)
axes[0, 1].legend(fontsize=7)
axes[0, 1].set_title('(b)', fontsize=9, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].text(0.02, 0.98, '(b)', transform=axes[0, 1].transAxes,
                fontsize=10, fontweight='bold', va='top')

# Panel (c): Bubble concentration
axes[0, 2].semilogy(time_days, result['Ccb'], 'b-', linewidth=1.2)
axes[0, 2].semilogy(time_days, result['Ccf'], 'r--', linewidth=1.2)
axes[0, 2].set_ylabel('Concentration (m⁻³)', fontsize=8)
axes[0, 2].set_title('(c)', fontsize=9, fontweight='bold')
axes[0, 2].grid(True, alpha=0.3)
axes[0, 2].text(0.02, 0.98, '(c)', transform=axes[0, 2].transAxes,
                fontsize=10, fontweight='bold', va='top')

# Panel (d): Gas atoms per bubble
axes[1, 0].semilogy(time_days, result['Ncb'], 'b-', linewidth=1.2)
axes[1, 0].semilogy(time_days, result['Ncf'], 'r--', linewidth=1.2)
axes[1, 0].set_xlabel('Time (days)', fontsize=8)
axes[1, 0].set_ylabel('Atoms/bubble', fontsize=8)
axes[1, 0].set_title('(d)', fontsize=9, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].text(0.02, 0.98, '(d)', transform=axes[1, 0].transAxes,
                fontsize=10, fontweight='bold', va='top')

# Panel (e): Gas pressure (if available)
if 'Pg' in result:
    axes[1, 1].plot(time_days, result['Pg'] / 1e6, 'g-', linewidth=1.2)
    axes[1, 1].set_xlabel('Time (days)', fontsize=8)
    axes[1, 1].set_ylabel('Gas Pressure (MPa)', fontsize=8)
    axes[1, 1].set_title('(e)', fontsize=9, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].text(0.02, 0.98, '(e)', transform=axes[1, 1].transAxes,
                    fontsize=10, fontweight='bold', va='top')

# Panel (f): Gas release
axes[1, 2].plot(time_days, result['released_gas'] / 1e20, 'm-', linewidth=1.2)
axes[1, 2].set_xlabel('Time (days)', fontsize=8)
axes[1, 2].set_ylabel('Released Gas (10²⁰ atoms/m³)', fontsize=8)
axes[1, 2].set_title('(f)', fontsize=9, fontweight='bold')
axes[1, 2].grid(True, alpha=0.3)
axes[1, 2].text(0.02, 0.98, '(f)', transform=axes[1, 2].transAxes,
                fontsize=10, fontweight='bold', va='top')

plt.tight_layout()

# Save in multiple formats
for fmt in ['pdf', 'png', 'svg']:
    plt.savefig(f'publication_figure.{fmt}', bbox_inches='tight', dpi=300)

plt.show()
```

**Expected Output:**
- Clean, minimalist style
- Standard journal figure dimensions
- Vector format (PDF/SVG) for crisp reproduction
- Panel labels for figure caption referencing

---

## Advanced Analysis Plots

### 13. Swelling Rate Analysis

**What it shows:** Rate of swelling change over time

**When to use:** Identifying growth phases, rate transitions

```python
# Calculate swelling rate
time_days = result['time'] / (24 * 3600)
swelling_rate = np.gradient(swelling, time_days)

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(time_days, swelling_rate, linewidth=2, color='#E63946')
ax.fill_between(time_days, swelling_rate, alpha=0.3, color='#E63946')

ax.set_xlabel('Time (days)', fontsize=12, fontweight='bold')
ax.set_ylabel('Swelling Rate (%/day)', fontsize=12, fontweight='bold')
ax.set_title('Swelling Rate Evolution', fontsize=14, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.6)

# Find and annotate peak rate
peak_idx = np.argmax(swelling_rate)
peak_time = time_days[peak_idx]
peak_rate = swelling_rate[peak_idx]
ax.axvline(peak_time, color='gray', linestyle='--', alpha=0.5)
ax.annotate(f'Peak rate: {peak_rate:.3f} %/day',
            xy=(peak_time, peak_rate),
            xytext=(peak_time+10, peak_rate),
            fontsize=10, fontweight='bold',
            arrowprops=dict(arrowstyle='->', lw=1.5))

plt.tight_layout()
plt.savefig('swelling_rate_analysis.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Initial low rate (incubation)
- Peak rate (accelerated growth phase)
- Declining rate (saturation approach)

---

## Custom Styled Plots

### 14. Presentation-Style Plot with Custom Colors

**What it shows:** Eye-catching plot for presentations

**When to use:** Conference presentations, seminars

```python
# Custom color scheme
colors = {
    'background': '#F8F9FA',
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'text': '#2B2D42'
}

# Create figure with custom background
fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor(colors['background'])
ax.set_facecolor(colors['background'])

# Plot with custom styling
ax.plot(time_days, swelling, linewidth=3.5, color=colors['primary'],
        marker='o', markersize=4, markeredgecolor='white', markeredgewidth=1.5)
ax.fill_between(time_days, swelling, alpha=0.25, color=colors['primary'])

# Customize spines
for spine in ax.spines.values():
    spine.set_edgecolor(colors['text'])
    spine.set_linewidth(1.5)

# Customize labels
ax.set_xlabel('Time (days)', fontsize=14, fontweight='bold',
             color=colors['text'])
ax.set_ylabel('Swelling (%)', fontsize=14, fontweight='bold',
             color=colors['text'])
ax.set_title('Fuel Swelling During Irradiation', fontsize=16,
             fontweight='bold', color=colors['text'], pad=20)

# Customize grid
ax.grid(True, linestyle=':', alpha=0.4, color=colors['text'])

# Customize ticks
ax.tick_params(axis='both', which='major', labelsize=11,
               colors=colors['text'])

plt.tight_layout()
plt.savefig('presentation_style.png', dpi=300, bbox_inches='tight',
            facecolor=colors['background'])
plt.show()
```

**Expected Output:**
- Professional presentation aesthetics
- Custom color scheme
- Enhanced readability

---

## Gas Release Analysis

### 15. Gas Release Fraction vs Temperature

**What it shows:** How much gas escapes at different temperatures

**When to use:** Safety analysis, fission product release modeling

```python
# Calculate gas release fraction at different temperatures
temperatures = np.linspace(600, 1000, 9)
release_fractions = []

for T in temperatures:
    params = create_default_parameters()
    params['temperature'] = T
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 200)
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    # Calculate gas release fraction
    total_gas = (result['Cgb'][-1] + result['Cgf'][-1] +
                result['Ccb'][-1] * result['Ncb'][-1] +
                result['Ccf'][-1] * result['Ncf'][-1] +
                result['released_gas'][-1])
    release_frac = result['released_gas'][-1] / total_gas * 100 if total_gas > 0 else 0
    release_fractions.append(release_frac)

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(temperatures, release_fractions, 's-', linewidth=2.5,
        markersize=10, markeredgecolor='white', markeredgewidth=1.5,
        color='#8E44AD')
ax.fill_between(temperatures, release_fractions, alpha=0.2, color='#8E44AD')

ax.set_xlabel('Temperature (K)', fontsize=12, fontweight='bold')
ax.set_ylabel('Gas Release Fraction (%)', fontsize=12, fontweight='bold')
ax.set_title('Temperature Dependence of Gas Release', fontsize=14, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.6)

# Add threshold annotation
ax.axhline(y=10, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
ax.text(temperatures[0], 11, '10% release threshold',
        fontsize=10, color='red')

plt.tight_layout()
plt.savefig('gas_release_vs_temperature.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Increasing release with temperature
- Threshold behavior around 800-900 K
- Sigmoidal shape typical of activated processes

---

## Arrhenius Analysis

### 16. Arrhenius Plot for Activation Energy

**What it shows:** Temperature dependence of swelling rate

**When to use:** Extracting activation energies, physics analysis

```python
# Calculate swelling rates at different temperatures
swelling_rates = []
for T in temperatures:
    params = create_default_parameters()
    params['temperature'] = T
    model = GasSwellingModel(params)

    sim_time = 100 * 24 * 3600
    t_eval = np.linspace(0, sim_time, 200)
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    # Average swelling rate (%/day)
    rate = swelling[-1] / (sim_time / (24 * 3600))
    swelling_rates.append(rate)

# Create Arrhenius plot
inv_T = 1000 / np.array(temperatures)  # 1000/T
ln_rate = np.log(swelling_rates)

fig, ax = plt.subplots(figsize=(10, 6))

# Plot data
ax.plot(inv_T, ln_rate, 'ro', markersize=10,
        markeredgecolor='white', markeredgewidth=1.5, label='Data')

# Fit line (excluding outliers)
valid_mask = np.array(swelling_rates) > 0
if np.sum(valid_mask) > 1:
    coeffs = np.polyfit(inv_T[valid_mask], ln_rate[valid_mask], 1)
    trend_line = np.poly1d(coeffs)
    inv_T_smooth = np.linspace(min(inv_T), max(inv_T), 100)
    ax.plot(inv_T_smooth, trend_line(inv_T_smooth), 'b--',
           linewidth=2, label='Linear fit')

    # Calculate apparent activation energy
    # Slope = -Ea/R where R = 8.314 J/mol·K
    Ea = -coeffs[0] * 8.314 * 1000 / 1000  # kJ/mol

    ax.text(0.02, 0.02, f'Ea ≈ {Ea:.1f} kJ/mol',
           transform=ax.transAxes, fontsize=12, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

ax.set_xlabel('1000/T (K⁻¹)', fontsize=12, fontweight='bold')
ax.set_ylabel('ln(Swelling Rate)', fontsize=12, fontweight='bold')
ax.set_title('Arrhenius Plot: Swelling Rate', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('arrhenius_plot.png', dpi=300, bbox_inches='tight')
plt.show()
```

**Expected Output:**
- Linear trend (Arrhenius behavior)
- Slope gives apparent activation energy
- Typical values: 100-300 kJ/mol depending on conditions

---

## Summary: Quick Reference

| Plot Type | Use Case | Key Function |
|-----------|----------|--------------|
| Time series | Basic evolution | `ax.plot()` |
| Log scale | Exponential growth | `ax.semilogy()` |
| Comparison | Multiple conditions | Multiple `ax.plot()` calls |
| Stacked area | Composition evolution | `ax.stackplot()` |
| Pie chart | Distribution snapshot | `ax.pie()` |
| Multi-panel | Comprehensive overview | `plt.subplots()` |
| Arrhenius | Activation energy | Plot `ln(rate)` vs `1/T` |

---

## Next Steps

- Try modifying these examples for your specific research questions
- Explore the repo `notebooks/` directory for interactive examples
- See [parameter reference](../parameter_reference.md) for customization options
- Check [interpreting results guide](interpreting_results.md) for understanding outputs

---

**Need More Help?**
- See [troubleshooting guide](troubleshooting.md) for common issues
- Explore the tutorial pages under `docs/tutorials/` for deeper understanding
