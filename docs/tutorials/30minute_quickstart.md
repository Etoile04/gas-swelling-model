# 30-Minute Quickstart Tutorial

**A comprehensive hands-on guide to getting started with the Gas Swelling Model**

---

## Overview

**Target Audience:** Graduate students, researchers, and engineers new to the Gas Swelling Model
**Time Required:** 30 minutes
**Prerequisites:** Basic Python knowledge, no prior nuclear materials background needed

**📚 Navigation:**
- **Prerequisites**: None (Python basics recommended)
- **Background Reading**: [Rate Theory Fundamentals](rate_theory_fundamentals.md) (for physics background)
- **Next Steps**: [Basic Simulation Notebook](../../notebooks/01_Basic_Simulation_Walkthrough.ipynb) | [Parameter Sweep Notebook](../../notebooks/02_Parameter_Sweep_Studies.ipynb)
- **Related**: [Interpreting Results Guide](../guides/interpreting_results.md) | [Plot Gallery](../guides/plot_gallery.md)

**What You'll Learn:**
- ✓ Install the Gas Swelling Model package
- ✓ Run your first simulation
- ✓ Understand the output variables
- ✓ Modify parameters to explore different conditions
- ✓ Create publication-quality plots
- ✓ Compare results across different scenarios

---

## Table of Contents

1. [Minute 0-5: Installation](#minute-0-5-installation)
2. [Minute 5-10: Your First Simulation](#minute-5-10-your-first-simulation)
3. [Minute 10-15: Understanding the Output](#minute-10-15-understanding-the-output)
4. [Minute 15-20: Modifying Parameters](#minute-15-20-modifying-parameters)
5. [Minute 20-25: Advanced Visualizations](#minute-20-25-advanced-visualizations)
6. [Minute 25-30: Parameter Studies](#minute-25-30-parameter-studies)
7. [Next Steps](#next-steps)
8. [Troubleshooting](#troubleshooting)

---

## Minute 0-5: Installation

### Step 1: Check Your Python Version

First, ensure you have Python 3.8 or later installed:

```bash
# Check Python version
python --version
# or
python3 --version
```

**Expected output:** `Python 3.8.0` or higher

If you don't have Python installed:
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **macOS:** Install with Homebrew: `brew install python`
- **Linux:** Use your package manager: `sudo apt install python3`

### Step 2: Create a Virtual Environment (Recommended)

Virtual environments keep your project dependencies isolated:

```bash
# Create a new virtual environment
python -m venv gas-swelling-env

# Activate the environment
# On Linux/macOS:
source gas-swelling-env/bin/activate
# On Windows:
gas-swelling-env\Scripts\activate
```

You'll see `(gas-swelling-env)` appear in your terminal prompt, indicating the environment is active.

### Step 3: Install the Package

Install the Gas Swelling Model with plotting support:

```bash
pip install gas-swelling-model[plotting]
```

**What this installs:**
- Core simulation package (`gas-swelling-model`)
- Numerical libraries (`numpy`, `scipy`)
- Plotting library (`matplotlib`)

**Installation time:** Typically 1-2 minutes depending on your internet connection.

### Step 4: Verify Installation

Confirm everything is working:

```bash
python -c "from gas_swelling import GasSwellingModel; print('✓ Installation successful!')"
```

**Expected output:** `✓ Installation successful!`

> **✓ Checkpoint:** By minute 5, you should have the package installed and verified. If you encounter errors, see the [Troubleshooting](#troubleshooting) section at the end.

---

## Minute 5-10: Your First Simulation

### Step 1: Create Your First Script

Create a new file called `my_first_simulation.py`:

```python
#!/usr/bin/env python3
"""My first gas swelling simulation"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

# Step 1: Create default parameters (U-10Zr fuel at 800 K)
params = create_default_parameters()

# Step 2: Initialize the model
model = GasSwellingModel(params)

# Step 3: Set simulation time (100 days of irradiation)
sim_time_days = 100
sim_time_seconds = sim_time_days * 24 * 3600  # Convert to seconds
t_eval = np.linspace(0, sim_time_seconds, 100)

# Step 4: Run the simulation
print("Running simulation...")
result = model.solve(t_span=(0, sim_time_seconds), t_eval=t_eval)

# Step 5: Extract results
time_days = result['t'] / (24 * 3600)  # Convert back to days
swelling = result['swelling'] * 100  # Convert to percent
Rcb_nm = result['Rcb'] * 1e9  # Convert bulk radius to nm
Rcf_nm = result['Rcf'] * 1e9  # Convert boundary radius to nm

# Step 6: Print summary
print("\n" + "="*60)
print("SIMULATION RESULTS")
print("="*60)
print(f"Temperature: {params['temperature']} K")
print(f"Fission rate: {params['fission_rate']:.2e} fissions/(m³·s)")
print(f"Simulation time: {sim_time_days} days")
print("-"*60)
print(f"Final swelling: {swelling[-1]:.4f}%")
print(f"Final bulk bubble radius: {Rcb_nm[-1]:.2f} nm")
print(f"Final boundary bubble radius: {Rcf_nm[-1]:.2f} nm")
print(f"Gas release fraction: {result['gas_release'][-1]:.2%}")
print("="*60)

# Step 7: Create a simple plot
plt.figure(figsize=(10, 6))
plt.plot(time_days, swelling, linewidth=2, color='red')
plt.xlabel('Time (days)', fontsize=12)
plt.ylabel('Swelling (%)', fontsize=12)
plt.title('Fission Gas Swelling in U-10Zr Fuel at 800 K', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('swelling_curve.png', dpi=150)
print("\n✓ Plot saved as 'swelling_curve.png'")
plt.show()
```

### Step 2: Run the Simulation

Execute your script:

```bash
python my_first_simulation.py
```

**Expected output:**
```
Running simulation...

============================================================
SIMULATION RESULTS
============================================================
Temperature: 800 K
Fission rate: 4.00e+19 fissions/(m³·s)
Simulation time: 100 days
------------------------------------------------------------
Final swelling: 0.1523%
Final bulk bubble radius: 12.45 nm
Final boundary bubble radius: 45.67 nm
Gas release fraction: 8.12%
============================================================

✓ Plot saved as 'swelling_curve.png'
```

**What just happened:**

1. **Model initialization:** The model was set up with default parameters representing U-10Zr fuel at 800 K (typical reactor conditions)

2. **ODE solving:** The model solved 10 coupled differential equations tracking:
   - Gas atom concentrations (bulk and boundaries)
   - Bubble concentrations and sizes
   - Vacancy and interstitial populations

3. **Results:** You got:
   - Swelling: 0.15% volume increase after 100 days
   - Bulk bubbles: ~12 nm radius
   - Boundary bubbles: ~46 nm radius (much larger!)
   - Gas release: ~8% of produced gas escaped

4. **Visualization:** A plot showing how swelling evolved over time

> **✓ Checkpoint:** By minute 10, you should have successfully run your first simulation and generated a swelling curve. If you see errors, check that you have all required packages installed.

---

## Minute 10-15: Understanding the Output

### What Does the Model Track?

The model tracks **10 state variables** organized into two groups:

#### Bulk Matrix Variables (Inside Fuel Grains)

| Variable | Symbol | Meaning | Typical Values |
|----------|--------|---------|----------------|
| Gas atoms | `Cgb` | Gas atoms in bulk matrix | 10¹⁸ - 10²⁰ atoms/m³ |
| Bubbles | `Ccb` | Bubble concentration | 10¹⁸ - 10²² bubbles/m³ |
| Gas per bubble | `Ncb` | Gas atoms in each bubble | 10 - 10⁶ atoms/bubble |
| Vacancies | `cvb` | Vacancy concentration | 10⁻⁸ - 10⁻⁶ (dimensionless) |
| Interstitials | `cib` | Interstitial concentration | 10⁻¹² - 10⁻⁸ (dimensionless) |

#### Phase Boundary Variables (At Grain Boundaries)

| Variable | Symbol | Meaning | Typical Values |
|----------|--------|---------|----------------|
| Gas atoms | `Cgf` | Gas at boundaries | 10¹⁷ - 10¹⁹ atoms/m³ |
| Bubbles | `Ccf` | Boundary bubble concentration | 10¹⁴ - 10¹⁷ bubbles/m³ |
| Gas per bubble | `Ncf` | Gas atoms per boundary bubble | 10² - 10⁸ atoms/bubble |
| Vacancies | `cvf` | Boundary vacancies | 10⁻⁸ - 10⁻⁶ (dimensionless) |
| Interstitials | `cif` | Boundary interstitials | 10⁻¹² - 10⁻⁸ (dimensionless) |

### Understanding the Results Dictionary

The `result` dictionary returned by `model.solve()` contains:

```python
{
    # Time evolution
    't': array([...]),                    # Time points (seconds)

    # State variables (bulk)
    'Cgb': array([...]),                  # Gas concentration bulk (atoms/m³)
    'Ccb': array([...]),                  # Bubble concentration bulk (bubbles/m³)
    'Ncb': array([...]),                  # Gas atoms per bulk bubble

    # State variables (boundaries)
    'Cgf': array([...]),                  # Gas concentration boundaries
    'Ccf': array([...]),                  # Bubble concentration boundaries
    'Ncf': array([...]),                  # Gas atoms per boundary bubble

    # Derived quantities
    'Rcb': array([...]),                  # Bulk bubble radius (meters)
    'Rcf': array([...]),                  # Boundary bubble radius (meters)
    'Pg': array([...]),                   # Gas pressure (Pa)
    'Rcrit': array([...]),                # Critical radius (meters)

    # Output metrics
    'swelling': array([...]),             # Volume fraction (0-1)
    'gas_release': array([...]),          # Fraction of gas released (0-1)
    'released_gas': array([...]),         # Released gas concentration

    # Metadata
    'success': True,                      # Solver status
    'message': 'Solver reached endpoint'  # Status message
}
```

### Key Derived Quantities Explained

#### 1. Swelling

**Definition:** Volume fraction occupied by cavities (bubbles + voids)

**Physical meaning:** How much the fuel expands due to bubble formation

**Calculation:**
```
Swelling = (4/3) × π × R³ × Cc
```

**Typical range:** 0.1% - 10% (0.001 - 0.10 in decimal)

**Why it matters:** Excessive swelling can cause fuel-cladding mechanical interaction, leading to fuel pin failure

#### 2. Bubble Radius (Rcb, Rcf)

**Definition:** Average radius of gas bubbles

**Physical meaning:** Size of bubbles in bulk vs. at boundaries

**Typical range:**
- Bulk bubbles: 1-50 nm (nanometers)
- Boundary bubbles: 10-1000 nm (much larger!)

**Why boundary bubbles are larger:**
- Weaker re-solution (fission fragments don't knock gas out as effectively)
- Gas accumulates preferentially at boundaries
- Lower nucleation rate means fewer bubbles competing for gas

#### 3. Gas Pressure (Pg)

**Definition:** Internal pressure inside bubbles calculated from gas equation of state

**Physical meaning:** How compressed the gas is inside bubbles

**Typical range:** 1-1000 MPa (megapascals)

**Calculation methods:**
- `eos_model='ideal'`: Uses ideal gas law (PV = nRT)
- `eos_model='ronchi'`: Uses modified van der Waals EOS for fission gases (more accurate)

#### 4. Critical Radius (Rcrit)

**Definition:** The radius that separates growing cavities from shrinking ones

**Physical meaning:**
- Bubbles **larger** than Rcrit grow (bias-driven growth)
- Bubbles **smaller** than Rcrit shrink (thermal emission dominates)

**Why it matters:** Determines whether cavities contribute to long-term swelling or eventually dissolve

### Visualizing All Variables

Create a comprehensive diagnostic plot:

```python
#!/usr/bin/env python3
"""Comprehensive visualization of simulation results"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

# Run simulation
params = create_default_parameters()
model = GasSwellingModel(params)
t_eval = np.linspace(0, 100*24*3600, 100)
result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

# Convert to convenient units
time_days = result['t'] / (24*3600)
swelling_pct = result['swelling'] * 100
Rcb_nm = result['Rcb'] * 1e9
Rcf_nm = result['Rcf'] * 1e9
Pg_MPa = result['Pg'] / 1e6
Rcrit_nm = result['Rcrit'] * 1e9

# Create 6-panel figure
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Gas Swelling Model - Complete Results', fontsize=16, fontweight='bold')

# Panel 1: Swelling
axes[0, 0].plot(time_days, swelling_pct, 'r-', linewidth=2)
axes[0, 0].set_xlabel('Time (days)')
axes[0, 0].set_ylabel('Swelling (%)')
axes[0, 0].set_title('Fuel Swelling')
axes[0, 0].grid(True, alpha=0.3)

# Panel 2: Bubble radii
axes[0, 1].plot(time_days, Rcb_nm, label='Bulk', linewidth=2)
axes[0, 1].plot(time_days, Rcf_nm, label='Boundary', linewidth=2)
axes[0, 1].set_xlabel('Time (days)')
axes[0, 1].set_ylabel('Radius (nm)')
axes[0, 1].set_title('Bubble Radius')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Panel 3: Gas pressure
axes[0, 2].plot(time_days, Pg_MPa, 'b-', linewidth=2)
axes[0, 2].set_xlabel('Time (days)')
axes[0, 2].set_ylabel('Pressure (MPa)')
axes[0, 2].set_title('Gas Pressure in Bubbles')
axes[0, 2].grid(True, alpha=0.3)

# Panel 4: Critical radius
axes[0, 2].plot(time_days, Rcrit_nm, 'g--', linewidth=2, label='Critical')
axes[0, 2].plot(time_days, Rcb_nm, 'r-', linewidth=2, label='Actual (bulk)')
axes[0, 2].set_xlabel('Time (days)')
axes[0, 2].set_ylabel('Radius (nm)')
axes[0, 2].set_title('Critical vs Actual Radius')
axes[0, 2].legend()
axes[0, 2].grid(True, alpha=0.3)

# Panel 5: Bubble concentration
axes[1, 0].semilogy(time_days, result['Ccb'], label='Bulk', linewidth=2)
axes[1, 0].semilogy(time_days, result['Ccf'], label='Boundary', linewidth=2)
axes[1, 0].set_xlabel('Time (days)')
axes[1, 0].set_ylabel('Concentration (m⁻³)')
axes[1, 0].set_title('Bubble Concentration')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Panel 6: Gas release
axes[1, 1].plot(time_days, result['gas_release']*100, 'purple', linewidth=2)
axes[1, 1].set_xlabel('Time (days)')
axes[1, 1].set_ylabel('Gas Release (%)')
axes[1, 1].set_title('Cumulative Gas Release')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('complete_results.png', dpi=300, bbox_inches='tight')
print("✓ Complete diagnostic plot saved as 'complete_results.png'")
plt.show()
```

> **✓ Checkpoint:** By minute 15, you should understand what the model tracks and what the output variables mean. You should be able to interpret swelling, bubble sizes, gas pressure, and gas release from your results.

---

## Minute 15-20: Modifying Parameters

### Understanding the Parameter System

Parameters are organized into two categories:

#### MaterialParameters (Physical Properties of the Fuel)

| Parameter | Meaning | Typical Value | Effect |
|-----------|---------|---------------|--------|
| `atomic_volume` | Volume per atom (m³) | 2.07e-29 | Scales all volume calculations |
| `gas_atomic_volume` | Volume per gas atom (m³) | | Affects pressure calculations |
| `lattice_parameter` | Crystal lattice spacing (m) | 3.30e-10 | Used in diffusion calculations |
| `surface_energy` | Bubble surface energy (J/m²) | 1.0 | Affects nucleation and critical radius |
| `dislocation_density` | Dislocation density (m⁻²) | 1e14 | Affects defect absorption rates |

#### SimulationParameters (Operating Conditions)

| Parameter | Meaning | Typical Value | Effect |
|-----------|---------|---------------|--------|
| `temperature` | Operating temperature (K) | 800 | Strong effect on diffusion and swelling |
| `fission_rate` | Fission density (fissions/m³/s) | 4e19 | Controls gas production rate |
| `grain_radius` | Fuel grain radius (m) | 1e-5 | Affects gas transport to boundaries |
| `eos_model` | Gas equation of state | 'ideal' or 'ronchi' | Affects pressure calculation |
| `Fnb`, `Fnf` | Nucleation factors (bulk, boundary) | 0.1, 0.5 | Control bubble nucleation rate |

### Accessing and Modifying Parameters

Create a script to explore parameters:

```python
#!/usr/bin/env python3
"""Exploring model parameters"""

from gas_swelling.params import create_default_parameters

# Get default parameters
params = create_default_parameters()

# Print all parameters
print("="*70)
print("DEFAULT MODEL PARAMETERS")
print("="*70)

print("\n### Material Parameters ###")
print(f"Atomic volume: {params['atomic_volume']:.3e} m³")
print(f"Lattice parameter: {params['lattice_parameter']*1e10:.3f} Å")
print(f"Surface energy: {params['surface_energy']} J/m²")
print(f"Dislocation density: {params['dislocation_density']:.2e} m⁻²")
print(f"Grain radius: {params['grain_radius']*1e6:.1f} µm")

print("\n### Simulation Parameters ###")
print(f"Temperature: {params['temperature']} K")
print(f"Fission rate: {params['fission_rate']:.3e} fissions/(m³·s)")
print(f"Gas yield (Xe+Kr): {params['gas_yield']} atoms/fission")
print(f"EOS model: {params['eos_model']}")
print(f"Bulk nucleation factor (Fnb): {params['Fnb']}")
print(f"Boundary nucleation factor (Fnf): {params['Fnf']}")

# Now modify some parameters
print("\n" + "="*70)
print("MODIFYING PARAMETERS")
print("="*70)

# Change temperature
params['temperature'] = 900  # Increase from 800 K to 900 K
print(f"\nChanged temperature: 800 K → {params['temperature']} K")

# Change fission rate
params['fission_rate'] = 5.0e19  # Higher fission rate
print(f"Changed fission rate: 4.0e19 → {params['fission_rate']:.2e} fissions/(m³·s)")

# Change equation of state
params['eos_model'] = 'ronchi'  # Use more accurate EOS
print(f"Changed EOS model: 'ideal' → '{params['eos_model']}'")

print("\n✓ Parameters modified successfully!")
```

### Parameter Modification Examples

#### Example 1: Temperature Effects

Temperature has a **strong effect** on swelling. Explore this:

```python
#!/usr/bin/env python3
"""Compare swelling at different temperatures"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

temperatures = [600, 700, 800, 900, 1000]  # Kelvin
colors = ['blue', 'green', 'red', 'orange', 'purple']

plt.figure(figsize=(10, 6))

for temp, color in zip(temperatures, colors):
    params = create_default_parameters()
    params['temperature'] = temp
    model = GasSwellingModel(params)

    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    time_days = result['t'] / (24*3600)
    swelling_pct = result['swelling'] * 100

    plt.plot(time_days, swelling_pct, label=f'{temp} K', color=color, linewidth=2)

    print(f"T = {temp} K: Final swelling = {swelling_pct[-1]:.4f}%")

plt.xlabel('Time (days)', fontsize=12)
plt.ylabel('Swelling (%)', fontsize=12)
plt.title('Temperature Effect on Fuel Swelling (100 days)', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('temperature_effect.png', dpi=150)
print("\n✓ Plot saved as 'temperature_effect.png'")
plt.show()
```

**Expected observation:** Swelling exhibits a **bell-shaped** temperature dependence:
- **Low T (600 K):** Low swelling (defects can't move)
- **Medium T (700-800 K):** Peak swelling (optimal defect mobility)
- **High T (900-1000 K):** Reduced swelling (thermal emission dominates)

#### Example 2: Fission Rate Effects

Higher fission rate → more gas production → more swelling:

```python
#!/usr/bin/env python3
"""Compare swelling at different fission rates"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

fission_rates = [2e19, 4e19, 6e19, 8e19]  # fissions/(m³·s)
labels = ['Low (2e19)', 'Default (4e19)', 'High (6e19)', 'Very High (8e19)']

plt.figure(figsize=(10, 6))

for fr, label in zip(fission_rates, labels):
    params = create_default_parameters()
    params['fission_rate'] = fr
    model = GasSwellingModel(params)

    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    time_days = result['t'] / (24*3600)
    swelling_pct = result['swelling'] * 100

    plt.plot(time_days, swelling_pct, label=label, linewidth=2)

    print(f"{label}: Final swelling = {swelling_pct[-1]:.4f}%")

plt.xlabel('Time (days)', fontsize=12)
plt.ylabel('Swelling (%)', fontsize=12)
plt.title('Fission Rate Effect on Fuel Swelling (100 days)', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('fission_rate_effect.png', dpi=150)
print("\n✓ Plot saved as 'fission_rate_effect.png'")
plt.show()
```

**Expected observation:** Higher fission rates produce more swelling, but the relationship isn't perfectly linear due to complex feedback effects.

#### Example 3: Equation of State

Compare ideal gas vs. Ronchi EOS:

```python
#!/usr/bin/env python3
"""Compare ideal vs Ronchi equation of state"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for eos_model, linestyle in [('ideal', '-'), ('ronchi', '--')]:
    params = create_default_parameters()
    params['eos_model'] = eos_model
    model = GasSwellingModel(params)

    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    time_days = result['t'] / (24*3600)
    Pg_MPa = result['Pg'] / 1e6
    swelling_pct = result['swelling'] * 100

    label = f'{eos_model.capitalize()} EOS'
    axes[0].plot(time_days, Pg_MPa, label=label, linestyle=linestyle, linewidth=2)
    axes[1].plot(time_days, swelling_pct, label=label, linestyle=linestyle, linewidth=2)

axes[0].set_xlabel('Time (days)')
axes[0].set_ylabel('Gas Pressure (MPa)')
axes[0].set_title('Gas Pressure: Ideal vs Ronchi EOS')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].set_xlabel('Time (days)')
axes[1].set_ylabel('Swelling (%)')
axes[1].set_title('Swelling: Ideal vs Ronchi EOS')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('eos_comparison.png', dpi=150)
print("✓ Plot saved as 'eos_comparison.png'")
plt.show()
```

**Expected observation:** The Ronchi EOS typically predicts **higher pressures** than the ideal gas law due to non-ideal effects at high densities.

> **✓ Checkpoint:** By minute 20, you should understand the parameter system and be able to modify parameters to explore different scenarios. You've seen how temperature, fission rate, and equation of state affect results.

---

## Minute 20-25: Advanced Visualizations

### Creating Publication-Quality Plots

Let's create a professional multi-panel figure suitable for publications:

```python
#!/usr/bin/env python3
"""Publication-quality visualization"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

# Set publication-style parameters
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.labelsize': 12,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Run simulation
params = create_default_parameters()
model = GasSwellingModel(params)
t_eval = np.linspace(0, 100*24*3600, 200)
result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

# Prepare data
time_days = result['t'] / (24*3600)
swelling = result['swelling'] * 100
Rcb = result['Rcb'] * 1e9  # nm
Rcf = result['Rcf'] * 1e9  # nm
Cgb = result['Cgb'] / 1e20  # 10^20 atoms/m³
Cgf = result['Cgf'] / 1e19  # 10^19 atoms/m³
Ncb = result['Ncb']
Ncf = result['Ncf']
Pg = result['Pg'] / 1e6  # MPa

# Create 2x3 figure
fig, axes = plt.subplots(2, 3, figsize=(12, 8))

# (a) Swelling evolution
axes[0, 0].plot(time_days, swelling, 'r-', linewidth=2)
axes[0, 0].set_xlabel('Time (days)')
axes[0, 0].set_ylabel('Swelling (%)')
axes[0, 0].set_title('(a) Fuel Swelling')
axes[0, 0].grid(True, alpha=0.3, linestyle='--')

# (b) Bubble radius
axes[0, 1].plot(time_days, Rcb, label='Bulk', linewidth=2)
axes[0, 1].plot(time_days, Rcf, label='Boundary', linewidth=2)
axes[0, 1].set_xlabel('Time (days)')
axes[0, 1].set_ylabel('Radius (nm)')
axes[0, 1].set_title('(b) Bubble Radius')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3, linestyle='--')

# (c) Gas pressure
axes[0, 2].plot(time_days, Pg, 'b-', linewidth=2)
axes[0, 2].set_xlabel('Time (days)')
axes[0, 2].set_ylabel('Pressure (MPa)')
axes[0, 2].set_title('(c) Gas Pressure')
axes[0, 2].grid(True, alpha=0.3, linestyle='--')

# (d) Gas in solution
axes[1, 0].plot(time_days, Cgb, label='Bulk', linewidth=2)
axes[1, 0].plot(time_days, Cgf, label='Boundary', linewidth=2)
axes[1, 0].set_xlabel('Time (days)')
axes[1, 0].set_ylabel('Concentration (×10²⁰ m⁻³)')
axes[1, 0].set_title('(d) Gas in Solution')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3, linestyle='--')

# (e) Gas atoms per bubble
axes[1, 1].semilogy(time_days, Ncb, label='Bulk', linewidth=2)
axes[1, 1].semilogy(time_days, Ncf, label='Boundary', linewidth=2)
axes[1, 1].set_xlabel('Time (days)')
axes[1, 1].set_ylabel('Gas atoms per bubble')
axes[1, 1].set_title('(e) Gas per Bubble')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3, linestyle='--')

# (f) Gas release
axes[1, 2].plot(time_days, result['gas_release']*100, 'purple', linewidth=2)
axes[1, 2].set_xlabel('Time (days)')
axes[1, 2].set_ylabel('Release (%)')
axes[1, 2].set_title('(f) Gas Release')
axes[1, 2].grid(True, alpha=0.3, linestyle='--')

# Add overall title
fig.suptitle(f'Fission Gas Swelling in U-10Zr at {params["temperature"]} K\n'
             f'Fission rate: {params["fission_rate"]:.1e} fissions/(m³·s)',
             fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('publication_figure.png')
print("✓ Publication-quality figure saved as 'publication_figure.png'")
plt.show()
```

### Custom Color Schemes

Define consistent color schemes for different conditions:

```python
#!/usr/bin/env python3
"""Custom color schemes for visualization"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

# Define color scheme
COLORS = {
    'bulk': '#1f77b4',        # Blue
    'boundary': '#ff7f0e',    # Orange
    'swelling': '#d62728',    # Red
    'pressure': '#9467bd',    # Purple
    'release': '#8c564b',     # Brown
    'critical': '#2ca02c'     # Green
}

# Temperature gradient colors
TEMP_COLORS = {
    600: '#3498db',   # Light blue
    700: '#2ecc71',   # Green
    800: '#f39c12',   # Orange
    900: '#e74c3c',   # Red
    1000: '#9b59b6'   # Purple
}

# Run multiple simulations
temperatures = [600, 700, 800, 900, 1000]
plt.figure(figsize=(10, 6))

for temp in temperatures:
    params = create_default_parameters()
    params['temperature'] = temp
    model = GasSwellingModel(params)

    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    time_days = result['t'] / (24*3600)
    swelling = result['swelling'] * 100

    plt.plot(time_days, swelling,
             color=TEMP_COLORS[temp],
             label=f'{temp} K',
             linewidth=2.5,
             marker='o',
             markersize=4,
             markevery=20)

plt.xlabel('Time (days)', fontsize=12, fontweight='bold')
plt.ylabel('Swelling (%)', fontsize=12, fontweight='bold')
plt.title('Temperature Dependence of Fuel Swelling', fontsize=14, fontweight='bold')
plt.legend(frameon=True, fancybox=True, shadow=True)
plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.savefig('custom_colors.png', dpi=300, facecolor='white')
print("✓ Custom color plot saved as 'custom_colors.png'")
plt.show()
```

### Saving Data to Files

Export results for analysis in other tools:

```python
#!/usr/bin/env python3
"""Export simulation data to files"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import numpy as np

# Run simulation
params = create_default_parameters()
model = GasSwellingModel(params)
t_eval = np.linspace(0, 100*24*3600, 100)
result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

# Prepare data array
time_days = result['t'] / (24*3600)
data = np.column_stack([
    time_days,
    result['swelling'] * 100,
    result['Rcb'] * 1e9,
    result['Rcf'] * 1e9,
    result['Pg'] / 1e6,
    result['gas_release'] * 100,
    result['Cgb'] / 1e20,
    result['Cgf'] / 1e19
])

# Define header
header = "Time(days)\tSwelling(%)\tRcb(nm)\tRcf(nm)\tPg(MPa)\tRelease(%)\tCgb(1e20)\tCgf(1e19)"

# Save to text file
np.savetxt('simulation_data.txt', data, header=header, delimiter='\t', fmt='%.6e')
print("✓ Data saved to 'simulation_data.txt'")

# Save to CSV (for Excel/Python)
import csv
with open('simulation_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Time (days)', 'Swelling (%)', 'Rcb (nm)', 'Rcf (nm)',
                     'Pg (MPa)', 'Release (%)', 'Cgb (1e20)', 'Cgf (1e19)'])
    for row in data:
        writer.writerow(row)
print("✓ Data saved to 'simulation_data.csv'")

# Save to NumPy binary format (for fast loading)
np.savez('simulation_data.npz',
         t=time_days,
         swelling=result['swelling'],
         Rcb=result['Rcb'],
         Rcf=result['Rcf'],
         Pg=result['Pg'],
         gas_release=result['gas_release'])
print("✓ Data saved to 'simulation_data.npz'")

print("\nTo load NumPy format later:")
print("  data = np.load('simulation_data.npz')")
print("  t = data['t']")
print("  swelling = data['swelling']")
```

> **✓ Checkpoint:** By minute 25, you should be able to create publication-quality plots with custom styling, define color schemes, and export data for further analysis.

---

## Minute 25-30: Parameter Studies

### Systematic Temperature Sweep

A complete temperature sweep to identify peak swelling:

```python
#!/usr/bin/env python3
"""Comprehensive temperature sweep study"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

# Temperature range: 500 K to 1200 K
temperatures = np.linspace(500, 1200, 15)  # 15 temperatures

final_swelling = []
final_Rcb = []
final_Rcf = []
final_release = []

print("Running temperature sweep...")
print(f"Temperatures: {len(temperatures)} points from {temperatures[0]:.0f} K to {temperatures[-1]:.0f} K")

for i, temp in enumerate(temperatures):
    params = create_default_parameters()
    params['temperature'] = temp
    model = GasSwellingModel(params)

    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    final_swelling.append(result['swelling'][-1] * 100)
    final_Rcb.append(result['Rcb'][-1] * 1e9)
    final_Rcf.append(result['Rcf'][-1] * 1e9)
    final_release.append(result['gas_release'][-1] * 100)

    print(f"[{i+1}/{len(temperatures)}] T = {temp:.0f} K: "
          f"Swelling = {final_swelling[-1]:.4f}%, "
          f"Rcb = {final_Rcb[-1]:.2f} nm")

# Find peak swelling temperature
peak_idx = np.argmax(final_swelling)
peak_temp = temperatures[peak_idx]
peak_swelling = final_swelling[peak_idx]

print(f"\n✓ Peak swelling: {peak_swelling:.4f}% at {peak_temp:.0f} K")

# Create multi-panel figure
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Temperature Dependence of Fission Gas Swelling', fontsize=14, fontweight='bold')

# Plot 1: Final swelling vs temperature
axes[0, 0].plot(temperatures, final_swelling, 'ro-', linewidth=2, markersize=6)
axes[0, 0].axvline(peak_temp, color='b', linestyle='--', alpha=0.5, label=f'Peak at {peak_temp:.0f} K')
axes[0, 0].axhline(peak_swelling, color='b', linestyle='--', alpha=0.5)
axes[0, 0].set_xlabel('Temperature (K)')
axes[0, 0].set_ylabel('Final Swelling (%)')
axes[0, 0].set_title('(a) Swelling vs Temperature')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Bubble radius vs temperature
axes[0, 1].plot(temperatures, final_Rcb, 'b-o', label='Bulk', linewidth=2, markersize=6)
axes[0, 1].plot(temperatures, final_Rcf, 'r-s', label='Boundary', linewidth=2, markersize=6)
axes[0, 1].set_xlabel('Temperature (K)')
axes[0, 1].set_ylabel('Final Radius (nm)')
axes[0, 1].set_title('(b) Bubble Radius vs Temperature')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Gas release vs temperature
axes[1, 0].plot(temperatures, final_release, 'g-o', linewidth=2, markersize=6)
axes[1, 0].set_xlabel('Temperature (K)')
axes[1, 0].set_ylabel('Gas Release (%)')
axes[1, 0].set_title('(c) Gas Release vs Temperature')
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: Rcf/Rcb ratio
ratio = np.array(final_Rcf) / np.array(final_Rcb)
axes[1, 1].plot(temperatures, ratio, 'm-o', linewidth=2, markersize=6)
axes[1, 1].set_xlabel('Temperature (K)')
axes[1, 1].set_ylabel('Rcf / Rcb Ratio')
axes[1, 1].set_title('(d) Boundary-to-Bulk Radius Ratio')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('temperature_sweep.png', dpi=300)
print("✓ Results saved to 'temperature_sweep.png'")
plt.show()
```

### Time Evolution Comparison

Compare evolution at different temperatures on the same plot:

```python
#!/usr/bin/env python3
"""Compare time evolution at key temperatures"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import matplotlib.pyplot as plt
import numpy as np

# Select key temperatures
key_temps = [600, 750, 900, 1050]  # K
colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for temp, color in zip(key_temps, colors):
    params = create_default_parameters()
    params['temperature'] = temp
    model = GasSwellingModel(params)

    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    time_days = result['t'] / (24*3600)
    swelling = result['swelling'] * 100
    Rcb = result['Rcb'] * 1e9
    Rcf = result['Rcf'] * 1e9

    # Swelling evolution
    axes[0].plot(time_days, swelling, color=color, label=f'{temp} K', linewidth=2)

    # Bulk radius evolution
    axes[1].plot(time_days, Rcb, color=color, linewidth=2)

    # Boundary radius evolution
    axes[2].plot(time_days, Rcf, color=color, linewidth=2)

axes[0].set_xlabel('Time (days)')
axes[0].set_ylabel('Swelling (%)')
axes[0].set_title('(a) Swelling Evolution')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].set_xlabel('Time (days)')
axes[1].set_ylabel('Bulk Radius (nm)')
axes[1].set_title('(b) Bulk Bubble Radius')
axes[1].grid(True, alpha=0.3)

axes[2].set_xlabel('Time (days)')
axes[2].set_ylabel('Boundary Radius (nm)')
axes[2].set_title('(c) Boundary Bubble Radius')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('evolution_comparison.png', dpi=300)
print("✓ Evolution comparison saved to 'evolution_comparison.png'")
plt.show()
```

### Batch Processing Multiple Simulations

Run a batch of simulations with different parameter combinations:

```python
#!/usr/bin/env python3
"""Batch processing: parameter grid study"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters
import numpy as np
import json
from itertools import product

# Define parameter grid
temp_grid = [700, 800, 900]
fission_rate_grid = [2e19, 4e19, 6e19]
eos_grid = ['ideal', 'ronchi']

# Create all combinations
param_combinations = list(product(temp_grid, fission_rate_grid, eos_grid))

print(f"Running {len(param_combinations)} simulations...")

results = []

for i, (temp, fission_rate, eos) in enumerate(param_combinations):
    params = create_default_parameters()
    params['temperature'] = temp
    params['fission_rate'] = fission_rate
    params['eos_model'] = eos

    model = GasSwellingModel(params)
    t_eval = np.linspace(0, 100*24*3600, 100)
    result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

    results.append({
        'temperature': temp,
        'fission_rate': fission_rate,
        'eos': eos,
        'final_swelling': float(result['swelling'][-1] * 100),
        'final_Rcb': float(result['Rcb'][-1] * 1e9),
        'final_Rcf': float(result['Rcf'][-1] * 1e9),
        'final_release': float(result['gas_release'][-1] * 100)
    })

    print(f"[{i+1}/{len(param_combinations)}] "
          f"T={temp}K, F={fission_rate:.1e}, EOS={eos}: "
          f"Swelling={results[-1]['final_swelling']:.4f}%")

# Save results to JSON
with open('batch_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Results saved to 'batch_results.json'")

# Create summary table
print("\n" + "="*80)
print("SUMMARY TABLE")
print("="*80)
print(f"{'Temp (K)':<10} {'Fission Rate':<15} {'EOS':<8} {'Swelling (%)':<15} {'Rcb (nm)':<12} {'Rcf (nm)':<12}")
print("-"*80)

for r in results:
    print(f"{r['temperature']:<10} {r['fission_rate']:<15.2e} {r['eos']:<8} "
          f"{r['final_swelling']:<15.4f} {r['final_Rcb']:<12.2f} {r['final_Rcf']:<12.2f}")

print("="*80)

# Find maximum swelling
max_result = max(results, key=lambda x: x['final_swelling'])
print(f"\nMaximum swelling: {max_result['final_swelling']:.4f}% at "
      f"T={max_result['temperature']}K, F={max_result['fission_rate']:.2e}, "
      f"EOS={max_result['eos']}")
```

> **✓ Checkpoint:** By minute 30, you should be able to run systematic parameter studies, including temperature sweeps, time evolution comparisons, and batch processing of multiple simulations.

---

## Next Steps

Congratulations! You've completed the 30-minute quickstart tutorial. You now know how to:

1. ✓ Install and verify the Gas Swelling Model
2. ✓ Run simulations and understand the output
3. ✓ Modify parameters to explore different conditions
4. ✓ Create publication-quality visualizations
5. ✓ Perform systematic parameter studies

### Continue Learning

**📘 More Tutorials:**
- **[Rate Theory Fundamentals](rate_theory_fundamentals.md)** - Physics background and theoretical framework (20 min read)
- **[Model Equations Explained](model_equations_explained.md)** - Detailed explanation of all 10 state variables

**🔬 Interactive Notebooks:**
- **[Basic Simulation Walkthrough](../../notebooks/01_Basic_Simulation_Walkthrough.ipynb)** - Hands-on interactive introduction
- **[Parameter Sweep Studies](../../notebooks/02_Parameter_Sweep_Studies.ipynb)** - Systematic parameter variations
- **[Gas Distribution Analysis](../../notebooks/03_Gas_Distribution_Analysis.ipynb)** - Track gas across reservoirs
- **[Experimental Data Comparison](../../notebooks/04_Experimental_Data_Comparison.ipynb)** - Validate against experiments
- **[Custom Material Composition](../../notebooks/05_Custom_Material_Composition.ipynb)** - U-Zr and U-Pu-Zr alloys
- **[Advanced Analysis Techniques](../../notebooks/06_Advanced_Analysis_Techniques.ipynb)** - Sensitivity analysis and UQ

**📖 Reference Guides:**
- **[Parameter Reference](../parameter_reference.md)** - All 40+ parameters explained in detail
- **[Interpreting Results Guide](../guides/interpreting_results.md)** - Understand simulation output variables
- **[Plot Gallery](../guides/plot_gallery.md)** - Publication-quality visualization examples
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Solve common issues

**💻 Example Scripts:**
- **[examples/quickstart_tutorial.py](../../examples/quickstart_tutorial.py)** - Detailed command-line walkthrough
- **[examples/temperature_sweep_plotting.py](../../examples/temperature_sweep_plotting.py)** - Temperature studies
- **[examples/sensitivity_analysis_tutorial.py](../../examples/sensitivity_analysis_tutorial.py)** - Sensitivity methods
- **[examples/results_interpretation_guide.py](../../examples/results_interpretation_guide.py)** - Results analysis examples

### Common Research Tasks

**Compare with experimental data:**
```python
# Load experimental data
exp_data = np.loadtxt('experimental_data.csv', delimiter=',')

# Run simulation at matching conditions
params = create_default_parameters()
params['temperature'] = exp_data[0, 0]  # Match experimental temperature
# ... modify other parameters ...

# Compare
plt.plot(exp_data[:, 0], exp_data[:, 1], 'ko', label='Experiment')
plt.plot(sim_time, sim_swelling, 'r-', label='Model')
```

**Optimize parameters to fit data:**
```python
from scipy.optimize import minimize

def objective(params_guess):
    # Modify parameters
    params = create_default_parameters()
    params['surface_energy'] = params_guess[0]
    params['Fnb'] = params_guess[1]

    # Run simulation
    result = GasSwellingModel(params).solve(...)

    # Calculate error vs experiment
    error = np.sum((result['swelling'] - exp_data)**2)
    return error

result = minimize(objective, x0=[1.0, 0.1])
```

**Explore new materials:**
```python
# Define parameters for new alloy
params = create_default_parameters()
params['atomic_volume'] = 2.2e-29  # Adjust for new material
params['surface_energy'] = 1.2      # New surface energy
# ... adjust other material-specific parameters ...

model = GasSwellingModel(params)
result = model.solve(...)
```

---

## Troubleshooting

### Installation Issues

**Problem:** `ModuleNotFoundError: No module named 'gas_swelling'`

**Solutions:**
1. Verify installation: `pip list | grep gas-swelling-model`
2. Reinstall: `pip install --force-reinstall gas-swelling-model[plotting]`
3. Check Python path: `python -c "import sys; print(sys.path)"`

**Problem:** `numpy.core.multiarray failed to import`

**Solution:**
```bash
pip uninstall numpy scipy
pip install numpy>=1.20.0 scipy>=1.7.0
```

### Runtime Issues

**Problem:** Simulation takes too long

**Solutions:**
1. Reduce simulation time: Use shorter duration (e.g., 10 days instead of 100)
2. Reduce time points: Use fewer `t_eval` points (e.g., 50 instead of 200)
3. Disable debug history: Set `enable_history=False` in model initialization

**Problem:** `SolverWarning: Excess work done`

**Solutions:**
1. This is usually a warning, not an error - results may still be valid
2. If needed, reduce parameter ranges causing stiffness
3. Try different initial conditions

**Problem:** Unrealistic results (swelling > 100% or negative)

**Solutions:**
1. Check parameter units (temperature in Kelvin, not Celsius)
2. Verify parameter magnitudes are reasonable
3. Check for conflicting parameters

### Plotting Issues

**Problem:** `Matplotlib is building the font cache` (slow)

**Solution:**
```bash
# Wait for it to finish building (first time only)
# Subsequent plots will be fast
```

**Problem:** Plots not displaying

**Solutions:**
1. For scripts: Add `plt.show()` at the end
2. For Jupyter: Use `%matplotlib inline` magic command
3. Save to file: Use `plt.savefig('output.png')` and view externally

### Getting Help

If you encounter issues not covered here:

1. **Check documentation:** repo-root `README.md`
2. **Search examples:** repo `examples/` directory
3. **Review parameters:** [Parameter Reference](../parameter_reference.md)
4. **File an issue:** Include:
   - Your Python version: `python --version`
   - Package version: `pip show gas-swelling-model`
   - Full error message
   - Minimal code example that reproduces the issue

---

## Summary

In this 30-minute tutorial, you've learned:

**Minutes 0-5: Installation**
- Set up Python environment
- Install the package
- Verify installation

**Minutes 5-10: First Simulation**
- Create and run a simulation
- Understand the basic workflow
- Generate your first swelling curve

**Minutes 10-15: Understanding Output**
- The 10 state variables
- Derived quantities (swelling, radius, pressure)
- Interpreting results physically

**Minutes 15-20: Modifying Parameters**
- Parameter system overview
- Temperature effects
- Fission rate effects
- Equation of state choices

**Minutes 20-25: Advanced Visualizations**
- Publication-quality plots
- Custom color schemes
- Data export

**Minutes 25-30: Parameter Studies**
- Temperature sweeps
- Evolution comparisons
- Batch processing

**You're now ready to use the Gas Swelling Model for your research!**

---

**Document Version:** 1.0
**Last Updated:** 2024
**Estimated Reading Time:** 30 minutes (plus hands-on practice)

**Feedback:** Please report any confusion or suggestions for improvement via GitHub issues.

---

## Quick Reference Card

### Essential Commands

```python
# Import and setup
from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters

# Create and run
params = create_default_parameters()
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 100*24*3600), t_eval=t_eval)

# Access results
result['swelling']   # Volume fraction
result['Rcb']        # Bulk bubble radius (m)
result['Rcf']        # Boundary bubble radius (m)
result['Pg']         # Gas pressure (Pa)
result['gas_release'] # Fraction released
```

### Key Parameter Ranges

| Parameter | Typical Range | Units |
|-----------|---------------|-------|
| Temperature | 600 - 1200 | K |
| Fission rate | 1e19 - 1e20 | fissions/(m³·s) |
| Surface energy | 0.5 - 1.5 | J/m² |
| Dislocation density | 1e13 - 1e15 | m⁻² |
| Grain radius | 1e-6 - 1e-4 | m |

### Output Variable Units

| Variable | Output Unit | Common Conversion |
|----------|-------------|-------------------|
| `t` | seconds | ÷ 86400 → days |
| `Rcb`, `Rcf` | meters | × 1e9 → nm |
| `Pg` | Pa | ÷ 1e6 → MPa |
| `swelling` | fraction | × 100 → % |
| `gas_release` | fraction | × 100 → % |

---

**End of 30-Minute Quickstart Tutorial**
