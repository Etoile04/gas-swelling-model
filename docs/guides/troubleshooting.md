# Troubleshooting Guide

**Target Audience:** Users encountering issues with the Gas Swelling Model
**Reading Time:** ~25 minutes
**Prerequisites:** Basic familiarity with running simulations

---

## Learning Objectives

After reading this guide, you will be able to:

- ✓ Diagnose and fix common installation issues
- ✓ Resolve runtime errors and warnings
- ✓ Troubleshoot solver convergence problems
- ✓ Optimize simulation performance
- ✓ Identify and correct unrealistic results
- ✓ Debug parameter-related issues

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Import and Module Errors](#import-and-module-errors)
3. [Parameter Issues](#parameter-issues)
4. [Solver Convergence Problems](#solver-convergence-problems)
5. [Performance Issues](#performance-issues)
6. [Unrealistic Results](#unrealistic-results)
7. [Numerical Instability](#numerical-instability)
8. [Gas Release Issues](#gas-release-issues)
9. [Temperature-Related Problems](#temperature-related-problems)
10. [Experimental Validation Mismatches](#experimental-validation-mismatches)
11. [Plotting and Visualization Issues](#plotting-and-visualization-issues)
12. [Memory and Resource Issues](#memory-and-resource-issues)
13. [Getting Additional Help](#getting-additional-help)

---

## Installation Issues

### Problem: Python Version Not Supported

**Error Message:**
```
SyntaxError: future feature annotations is not available
```
or
```
ERROR: Package 'gas-swelling-model' requires a different Python version
```

**Diagnosis:**
The model requires Python 3.8 or later. You're running an older version.

**Solution:**

```bash
# Check your Python version
python --version

# If using conda, create a new environment with Python 3.11
conda create -n gas-swelling python=3.11
conda activate gas-swelling

# If using venv
python3.11 -m venv gas-swelling-env
source gas-swelling-env/bin/activate  # On Windows: gas-swelling-env\Scripts\activate
```

**Prevention:**
Always use Python 3.8+. Python 3.10 or 3.11 is recommended.

---

### Problem: numpy/scipy Import Errors

**Error Message:**
```
ImportError: numpy.core.multiarray failed to import
```
or
```
ImportError: cannot import name 'solve_ivp' from 'scipy.integrate'
```

**Diagnosis:**
Incompatible or missing numpy/scipy versions.

**Solution:**

```bash
# Uninstall existing versions
pip uninstall numpy scipy -y

# Install compatible versions
pip install "numpy>=1.20.0,<2.0.0" "scipy>=1.7.0"

# Or use conda for better compatibility
conda install -c conda-forge numpy scipy
```

**Version Requirements:**
- numpy: >= 1.20.0
- scipy: >= 1.7.0

---

### Problem: Permission Denied During Installation

**Error Message:**
```
[Errno 13] Permission denied: '/usr/local/lib/python3.x/site-packages'
```

**Diagnosis:**
Trying to install system-wide without admin privileges.

**Solution:**

```bash
# Option 1: Use user installation
pip install --user gas-swelling-model

# Option 2: Use virtual environment (RECOMMENDED)
python -m venv gas-swelling-env
source gas-swelling-env/bin/activate
pip install gas-swelling-model

# Option 3: Use conda environment
conda create -n gas-swelling python=3.11
conda activate gas-swelling
pip install gas-swelling-model
```

---

## Import and Module Errors

### Problem: ModuleNotFoundError

**Error Message:**
```
ModuleNotFoundError: No module named 'gas_swelling'
```

**Diagnosis:**
Package not installed or Python can't find it.

**Solution:**

```bash
# Check if package is installed
pip list | grep gas-swelling

# If not installed, install it
pip install gas-swelling-model

# If installed but not found, check Python path
python -c "import sys; print(sys.path)"

# Reinstall if needed
pip install --force-reinstall gas-swelling-model
```

**Common Causes:**
1. Package not installed
2. Virtual environment not activated
3. Installing in one Python but running with another

---

### Problem: ImportError: Cannot Import Specific Function

**Error Message:**
```
ImportError: cannot import name 'GasSwellingModel' from 'gas_swelling'
```

**Diagnosis:**
Incorrect import path or using outdated API.

**Solution:**

```python
# CORRECT imports for the refactored model
from gas_swelling.models.refactored_model import RefactoredGasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Create model
params = create_default_parameters()
model = RefactoredGasSwellingModel(params)

# For backward compatibility with old code
from gas_swelling import GasSwellingModel  # May be deprecated
```

**API Changes:**
The refactored model uses modular components. Use `RefactoredGasSwellingModel` for new code.

---

## Parameter Issues

### Problem: Temperature Below Minimum

**Error Message:**
```
ValueError: Temperature must be >= 273.15 K (0°C)
```

**Diagnosis:**
Temperature specified in Celsius instead of Kelvin, or value too low.

**Solution:**

```python
# WRONG: Temperature in Celsius
params['temperature'] = 500  # This is 500°C, not 500 K

# CORRECT: Convert Celsius to Kelvin
params['temperature'] = 500 + 273.15  # 773.15 K

# Or specify in Kelvin directly
params['temperature'] = 773.15  # 500°C in Kelvin
```

**Temperature Range:**
- Minimum: 273.15 K (0°C)
- Maximum: ~1200 K (fuel melting point)
- Typical: 600-900 K

---

### Problem: Negative or Zero Fission Rate

**Symptom:**
No swelling or gas production occurs.

**Diagnosis:**
Fission rate set to zero or negative value.

**Solution:**

```python
# Check fission rate
params = create_default_parameters()
print(f"Fission rate: {params['fission_rate']:.2e} fissions/m³/s")

# Set appropriate fission rate
# Typical range: 1e19 to 1e21 fissions/m³/s
params['fission_rate'] = 2e20  # Standard value

# Verify in results
results = model.solve(t_span=(0, 8640000), t_eval=None)
print(f"Gas produced: {results['released_gas'][-1]:.2e} atoms/m³")
```

**Typical Values:**
- Low power: 1e19 fissions/m³/s
- Normal: 2e20 fissions/m³/s
- High power: 5e20+ fissions/m³/s

---

### Problem: Invalid Nucleation Factors

**Symptom:**
No bubbles form, or bubble count explodes.

**Diagnosis:**
Nucleation factors (Fnb, Fnf) set incorrectly.

**Solution:**

```python
# Check nucleation factors
params = create_default_parameters()
print(f"Bulk nucleation (Fnb): {params['Fnb']}")
print(f"Boundary nucleation (Fnf): {params['Fnf']}")

# Typical range: 1e-6 to 1e-4
params['Fnb'] = 1e-5  # Bulk nucleation
params['Fnf'] = 1e-5  # Boundary nucleation

# Too high: causes unrealistic bubble nucleation
# Too low: no bubbles form
```

**Nucleation Factor Guide:**
| Value | Effect |
|-------|--------|
| < 1e-7 | Very few bubbles form |
| 1e-6 - 1e-5 | Normal range |
| > 1e-4 | Excessive nucleation |

---

## Solver Convergence Problems

### Problem: Solver Failed to Converge

**Error Message:**
```
OdeintWarning: Excess work done on this call (perhaps wrong Dfun type).
```
or
```
solve_ivp terminated: solver failed with status -1
```

**Diagnosis:**
ODE system is too stiff or solver can't handle the dynamics.

**Solution:**

```python
# Option 1: Reduce time span and check intermediate results
params = create_default_parameters()
model = RefactoredGasSwellingModel(params)

# Try shorter simulation first
results = model.solve(t_span=(0, 86400), t_eval=None)  # 1 day instead of 100

# Option 2: Use smaller initial time step
params['time_step'] = 1e-10  # Reduce from 1e-9
params['max_time_step'] = 1e1  # Reduce from 1e2

# Option 3: Enable adaptive stepping (if available)
params['adaptive_stepping_enabled'] = True

# Option 4: Try different solver method
# The refactored model uses RK23; consider if BDF (stiff solver) is needed
```

**When This Happens:**
- Very high fission rates (> 1e21)
- Very low temperatures (< 400 K)
- Extreme nucleation factors
- Long simulation times without checkpoints

---

### Problem: Simulation Stops Prematurely

**Symptom:**
Simulation ends before reaching max_time.

**Diagnosis:**
Solver encountered numerical issues or reached maximum iterations.

**Solution:**

```python
# Check solver status
results = model.solve(t_span=(0, params['max_time']), t_eval=None)

if not results.get('success', True):
    print(f"Solver failed at t = {results['time'][-1]:.2e} s")
    print(f"Status: {results.get('message', 'Unknown error')}")

# Reduce max_time and run in segments
segment_time = 864000  # 10 days per segment
all_results = None
current_state = model.initial_state

for i in range(10):  # 10 segments = 100 days
    results = model.solve(
        t_span=(0, segment_time),
        t_eval=None,
        y0=current_state
    )
    # Concatenate results...
    current_state = results['y'][:, -1]
```

---

## Performance Issues

### Problem: Simulation Takes Too Long

**Symptom:**
Simulation running for hours without completion.

**Diagnosis:**
Too many time points, small time steps, or debugging enabled.

**Solution:**

```python
# Option 1: Reduce number of output time points
# WRONG: Too many points
t_eval = np.linspace(0, 8640000, 100000)  # 100k points - SLOW!

# CORRECT: Fewer points for output
t_eval = np.linspace(0, 8640000, 100)  # 100 points - FAST!

# Option 2: Disable debug output
params['debug_enabled'] = False  # Make sure this is False
model.debug_config.enabled = False

# Option 3: Use adaptive solver (let it choose points)
results = model.solve(t_span=(0, 8640000), t_eval=None)  # None = adaptive

# Option 4: Check if you're running unnecessary simulations
# Use parameter sweeps efficiently (see notebook 02)
```

**Performance Tips:**
- Use `t_eval=None` for adaptive output
- Disable debug mode for production runs
- Use parameter sweeps for studies, not sequential runs
- Consider parallel execution for multiple simulations

---

### Problem: Memory Usage Too High

**Error Message:**
```
MemoryError: Unable to allocate array
```

**Diagnosis:**
Storing too much data from multiple simulations or too many time points.

**Solution:**

```python
# Option 1: Process results in batches
for temp in [600, 700, 800, 900]:
    params['temperature'] = temp
    model = RefactoredGasSwellingModel(params)
    results = model.solve(t_span=(0, 8640000), t_eval=None)
    # Process and save results immediately
    save_results(results, f"results_T{temp}.npz")
    del results  # Free memory

# Option 2: Reduce time points
t_eval = np.linspace(0, 8640000, 100)  # Not 10000

# Option 3: Save to disk instead of keeping in memory
import numpy as np
np.savez('simulation_results.npz', **results)

# Option 4: Use float32 instead of float64 (if precision allows)
results_float32 = {k: v.astype(np.float32) for k, v in results.items()}
```

---

## Unrealistic Results

### Problem: Swelling Is Zero or Very Low

**Symptom:**
`results['swelling']` shows 0% or < 0.01%.

**Diagnosis:**
No gas production, no bubbles forming, or time too short.

**Solution:**

```python
# Check 1: Verify gas production
params = create_default_parameters()
params['fission_rate'] = 2e20  # Ensure non-zero
params['gas_production_rate'] = 0.25  # Standard value

# Check 2: Verify nucleation is enabled
params['Fnb'] = 1e-5  # Bulk nucleation
params['Fnf'] = 1e-5  # Boundary nucleation

# Check 3: Check simulation time
# Swelling takes time to develop!
results = model.solve(t_span=(0, 8640000*10), t_eval=None)  # 1000 days

# Check 4: Verify temperature is in appropriate range
params['temperature'] = 773.15  # 500°C in Kelvin

# Diagnostic: Check state variables
results = model.solve(t_span=(0, 8640000), t_eval=None)
print(f"Bulk bubbles: {results['Ccb'][-1]:.2e} cavities/m³")
print(f"Bubble radius: {results['Rcb'][-1]:.2e} m")
print(f"Gas in bubbles: {results['Ncb'][-1]:.2e} atoms/bubble")
```

**Expected Swelling:**
- U-10Zr at 500°C: ~5% after 100 days
- High-purity U at 400°C: ~0.5% after 100 days

---

### Problem: Swelling Is Too High (> 50%)

**Symptom:**
`results['swelling']` shows unrealistic values > 50%.

**Diagnosis:**
Bubble radius calculation error or pressure equation issue.

**Solution:**

```python
# Check 1: Verify EOS model
params['eos_model'] = 'ideal'  # Try ideal instead of ronchi

# Check 2: Check surface energy
params['surface_energy'] = 0.5  # J/m², standard value
# Too low -> bubbles grow too large

# Check 3: Verify gas production rate
params['gas_production_rate'] = 0.25  # Should be ~0.25 (25% of fission products)

# Check 4: Check nucleation factors
params['Fnb'] = 1e-5  # Not too high
params['Fnf'] = 1e-5

# Diagnostic: Check individual components
results = model.solve(t_span=(0, 8640000), t_eval=None)
V_bubbles = (4/3) * np.pi * results['Rcb'][-1]**3 * results['Ccb'][-1]
print(f"Bubble volume fraction: {V_bubbles:.4f}")
print(f"Expected: < 0.10 for 10% swelling")
```

---

### Problem: Negative Concentrations

**Symptom:**
State variables become negative during simulation.

**Diagnosis:**
Numerical instability from large time steps or extreme parameters.

**Solution:**

```python
# Option 1: Reduce time step
params['time_step'] = 1e-10  # Smaller initial step
params['max_time_step'] = 1e1  # Smaller max step

# Option 2: Check parameter values
params['temperature'] = 773.15  # Reasonable temperature
params['fission_rate'] = 2e20  # Reasonable fission rate

# Option 3: Enable debug output to see when it becomes negative
model.debug_config.enabled = True
model.debug_config.time_step_interval = 100

# Run and inspect debug history
results = model.solve(t_span=(0, 86400), t_eval=None)
# Look for first negative value in debug output
```

---

## Numerical Instability

### Problem: Oscillating Results

**Symptom:**
Variables oscillate wildly instead of changing smoothly.

**Diagnosis:**
Solver time step too large for the dynamics.

**Solution:**

```python
# Reduce maximum time step
params['max_time_step'] = 1.0  # Reduce from 1e2
params['time_step'] = 1e-10  # Reduce initial step

# Check stiffness indicators
# High temperature + low dislocation density = stiff
if params['temperature'] > 900 and params['dislocation_density'] < 1e13:
    params['max_time_step'] = 0.1  # Need smaller steps

# Enable adaptive stepping
params['adaptive_stepping_enabled'] = True
```

---

### Problem: Results Change with Different Time Steps

**Symptom:**
Running with different `t_eval` gives different answers.

**Diagnosis:**
Solver tolerance not tight enough.

**Solution:**

```python
# The solver should give consistent results regardless of t_eval
# t_eval only affects output, not internal solver steps

# If results differ significantly, check solver tolerances
from scipy.integrate import solve_ivp

result = solve_ivp(
    fun=lambda t, y: model._equations(t, y),
    t_span=(0, 8640000),
    y0=model.initial_state,
    method='RK23',
    rtol=1e-6,  # Reduce tolerance
    atol=1e-9,
    t_eval=t_eval
)
```

---

## Gas Release Issues

### Problem: No Gas Release

**Symptom:**
`results['released_gas']` is zero or constant.

**Diagnosis:**
Bubble interconnectivity threshold not reached.

**Solution:**

```python
# Check 1: Verify simulation is long enough
# Gas release typically starts after significant swelling
results = model.solve(t_span=(0, 8640000*10), t_eval=None)  # Longer time

# Check 2: Check temperature effect
# Higher temperatures promote gas release
params['temperature'] = 873.15  # Try 600°C instead of 300°C

# Check 3: Check gas production rate
params['gas_production_rate'] = 0.25  # Ensure gas is being produced

# Check 4: Examine bubble distribution
results = model.solve(t_span=(0, 8640000), t_eval=None)
print(f"Boundary bubble concentration: {results['Ccf'][-1]:.2e}")
print(f"Boundary bubble radius: {results['Rcf'][-1]:.2e} m")
# Gas release requires large, interconnected boundary bubbles
```

**Gas Release Threshold:**
- Typically requires > 3-5% swelling
- More likely at higher temperatures (> 600°C)
- Depends on boundary bubble interconnectivity

---

### Problem: All Gas Released Immediately

**Symptom:**
100% gas release at very early times.

**Diagnosis:**
Nucleation or growth parameters causing unrealistic behavior.

**Solution:**

```python
# Check nucleation factors
params['Fnb'] = 1e-5  # Reduce if too high
params['Fnf'] = 1e-5  # Reduce if too high

# Check resolution rate (recoil resolution)
params['resolution_rate'] = 2e-5  # Standard value
# Too high -> gas keeps getting knocked out of bubbles

# Check temperature
params['temperature'] = 773.15  # Ensure reasonable
```

---

## Temperature-Related Problems

### Problem: No Temperature Dependence

**Symptom:**
Results look the same at 300°C and 600°C.

**Diagnosis:**
Temperature in wrong units or not being applied.

**Solution:**

```python
# MUST use Kelvin, not Celsius
params['temperature'] = 500 + 273.15  # 500°C to Kelvin

# Verify temperature is being used
print(f"Simulation temperature: {params['temperature']} K")

# Check diffusion coefficients
from gas_swelling.physics.thermal import calculate_diffusion_coefficient
Dgb = calculate_diffusion_coefficient(params['temperature'], params)
print(f"Bulk diffusion coefficient: {Dgb:.2e} m²/s")
# Should vary significantly with temperature
```

---

### Problem: Bell-Shaped Swelling Curve Missing

**Symptom:**
Swelling increases monotonically with temperature (no peak).

**Diagnosis:**
Parameters outside range where bell curve appears.

**Solution:**

```python
# The bell curve appears around 700-800 K
# Run a proper temperature sweep

temperatures = np.linspace(500, 1000, 20)  # K
final_swelling = []

for T in temperatures:
    params['temperature'] = T
    model = RefactoredGasSwellingModel(params)
    results = model.solve(t_span=(0, 8640000), t_eval=None)
    final_swelling.append(results['swelling'][-1])

# Plot to see if peak appears
import matplotlib.pyplot as plt
plt.plot(temperatures, final_swelling)
plt.xlabel('Temperature (K)')
plt.ylabel('Final Swelling (%)')
plt.show()

# Peak typically at 700-800 K for U-10Zr
```

---

## Experimental Validation Mismatches

### Problem: Model Predicts Much Higher Swelling Than Experiments

**Symptom:**
Model shows 10% swelling, experiments show 2%.

**Diagnosis:**
Parameters not matched to experimental conditions.

**Solution:**

```python
# Check 1: Match fuel composition
# U-10Zr vs U-19Pu-10Zr vs pure U have different parameters
# See notebook 05: Custom Material Composition

# Check 2: Adjust dislocation density
# Higher dislocation density -> more defect annihilation -> less swelling
params['dislocation_density'] = 1e14  # Try higher value

# Check 3: Adjust nucleation factors
# More nucleation -> more smaller bubbles -> different swelling
params['Fnb'] = 1e-4  # Higher nucleation

# Check 4: Check temperature gradient
# Experiments may have temperature variations
params['temperature'] = 673.15  # Match experimental temperature

# Check 5: Verify simulation time matches experiment
# 100 days simulation vs 1 year experiment?
```

**Common Adjustments for Validation:**
- Dislocation density: 1e13 to 1e15 m⁻²
- Nucleation factors: 1e-6 to 1e-4
- Surface energy: 0.3 to 0.7 J/m²

---

### Problem: Peak Temperature Shifted

**Symptom:**
Model peaks at 800 K, experiments peak at 700 K.

**Diagnosis:**
Activation energies or diffusion parameters need adjustment.

**Solution:**

```python
# This is advanced - usually means material parameters differ
# Consider using composition-specific parameters

# For U-Zr alloys with different Zr content:
# See notebook 05 for composition-dependent parameters

# Quick adjustments (use with caution):
params['Dgb_activation_energy'] = 1.16  # eV
params['Evm'] = 0.74  # eV, vacancy migration energy

# Note: These are material-specific and shouldn't be changed arbitrarily
# Use validated values from literature for your specific alloy
```

---

## Plotting and Visualization Issues

### Problem: Plots Are Empty or Show Wrong Data

**Symptom:**
Matplotlib figure appears blank or shows unexpected values.

**Diagnosis:**
Data not being passed correctly to plotting function.

**Solution:**

```python
# Check 1: Verify results contain expected data
results = model.solve(t_span=(0, 8640000), t_eval=None)
print(f"Keys in results: {results.keys()}")
print(f"Swelling shape: {results['swelling'].shape}")

# Check 2: Convert time to appropriate units
time_days = results['time'] / (24 * 3600)  # Seconds to days

# Check 3: Check for NaN or Inf values
print(f"Contains NaN: {np.any(np.isnan(results['swelling']))}")
print(f"Contains Inf: {np.any(np.isinf(results['swelling']))}")

# Check 4: Verify plot commands
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(time_days, results['swelling'])
ax.set_xlabel('Time (days)')
ax.set_ylabel('Swelling (%)')
ax.set_title('Gas Swelling vs Time')
plt.show()

# If still empty, try basic plot
plt.figure()
plt.plot(results['swelling'])
plt.show()
```

---

### Problem: Saving Figures Fails

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'output/swelling.png'
```

**Diagnosis:**
Output directory doesn't exist.

**Solution:**

```python
import os

# Create output directory if it doesn't exist
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# Now save figure
plt.savefig(os.path.join(output_dir, 'swelling.png'), dpi=300)

# Or use absolute path
output_path = os.path.abspath('output/swelling.png')
plt.savefig(output_path)
```

---

## Memory and Resource Issues

### Problem: Out of Memory During Parameter Sweep

**Symptom:**
System crashes or becomes unresponsive during large parameter studies.

**Diagnosis:**
Trying to run too many simulations or storing too much data.

**Solution:**

```python
# Option 1: Process one parameter at a time
temperatures = [600, 700, 800, 900]
results_list = []

for T in temperatures:
    params['temperature'] = T
    model = RefactoredGasSwellingModel(params)
    result = model.solve(t_span=(0, 8640000), t_eval=None)

    # Extract only what you need
    summary = {
        'temperature': T,
        'final_swelling': result['swelling'][-1],
        'max_bubble_radius': np.max(result['Rcb'])
    }
    results_list.append(summary)

    # Clear memory
    del result

# Option 2: Save results incrementally
import json
for i, T in enumerate(temperatures):
    # ... run simulation ...
    with open(f'results_T{T}.json', 'w') as f:
        json.dump(summary, f)
```

---

### Problem: CPU Usage 100% but No Progress

**Symptom:**
Simulation appears stuck with high CPU usage.

**Diagnosis:**
Solver in infinite loop or experiencing stiffness.

**Solution:**

```python
# Add timeout or progress monitoring
import time

start_time = time.time()
timeout = 300  # 5 minutes

# Enable progress output
params['show_progress'] = True
params['progress_interval'] = 100

# Run with monitoring
try:
    results = model.solve(t_span=(0, 8640000), t_eval=None)
    elapsed = time.time() - start_time
    print(f"Simulation completed in {elapsed:.1f} seconds")
except KeyboardInterrupt:
    print(f"Simulation interrupted after {time.time() - start_time:.1f} seconds")

# If consistently slow, reduce problem size
params['max_time'] = 864000  # Try 10 days instead of 100
```

---

## Getting Additional Help

### Debug Mode

Enable debug output to see what's happening internally:

```python
# Enable debug configuration
model.debug_config.enabled = True
model.debug_config.time_step_interval = 1000
model.debug_config.save_to_file = True
model.debug_config.output_file = 'debug_output.txt'

# Run simulation
results = model.solve(t_span=(0, 86400), t_eval=None)

# Check debug history
print(f"Number of debug entries: {len(model.debug_history.time)}")

# Analyze problematic time points
for i, (t, state) in enumerate(zip(model.debug_history.time,
                                     model.debug_history.state)):
    if np.any(state < 0):
        print(f"Negative value at step {i}, t={t:.2e}")
        print(f"State: {state}")
        break
```

### Verification Checklist

Before seeking help, verify:

- [ ] Python version is 3.8+
- [ ] All dependencies installed (numpy, scipy, matplotlib)
- [ ] Temperature is in Kelvin
- [ ] Fission rate is non-zero
- [ ] Simulation time is sufficient (days to months)
- [ ] Error message is documented
- [ ] Minimal reproducible example created

### Where to Get Help

1. **Documentation**: Check the tutorial and guide pages under `docs/tutorials/` and `docs/guides/`
2. **Examples**: Review the repo `notebooks/` directory for working examples
3. **GitHub Issues**: Search existing issues or create new one
4. **Discussion Forum**: Ask questions in GitHub Discussions

### Creating a Minimal Reproducible Example

When reporting issues, include:

```python
"""
Minimal example to reproduce the issue

Expected behavior: [describe what should happen]
Actual behavior: [describe what actually happens]
Error message: [paste full error traceback]
"""

from gas_swelling.models.refactored_model import RefactoredGasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Minimal parameters showing issue
params = create_default_parameters()
params['temperature'] = 773.15  # Only changed this
params['fission_rate'] = 2e20

model = RefactoredGasSwellingModel(params)
results = model.solve(t_span=(0, 8640000), t_eval=None)

# What goes wrong:
print(f"Swelling: {results['swelling'][-1]}")  # Expected: ~5%, Got: 0
```

---

## Quick Reference: Error Messages

| Error Message | Most Likely Cause | Quick Fix |
|--------------|-------------------|-----------|
| `ModuleNotFoundError` | Package not installed | `pip install gas-swelling-model` |
| `ValueError: Temperature must be >= 273.15` | Temperature in Celsius | Add 273.15 to convert to Kelvin |
| `OdeintWarning: Excess work` | System too stiff | Reduce time step or simulation time |
| `MemoryError` | Too many time points | Use `t_eval=None` or reduce points |
| `ImportError: cannot import name` | Wrong import path | Use `RefactoredGasSwellingModel` |
| `ZeroDivisionError` | Zero parameter value | Check fission_rate, nucleation factors |

---

## Prevention Best Practices

1. **Always** use virtual environments
2. **Always** specify temperature in Kelvin
3. **Always** check parameter values before running
4. **Always** start with shorter simulations to verify behavior
5. **Always** use `t_eval=None` for adaptive time stepping
6. **Always** verify units when comparing to experiments
7. **Always** save intermediate results for long simulations
8. **Always** document parameter choices for reproducibility

---

For more information, see:
- Installation guide: repo-root `INSTALL.md`
- [30-Minute Quickstart](../tutorials/30minute_quickstart.md)
- [Interpreting Results](interpreting_results.md)
- [Parameter Reference](../parameter_reference.md)
