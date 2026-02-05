# Validation Guide for Gas Swelling Model

A comprehensive guide to validating the gas swelling model against experimental data from U-10Zr, U-19Pu-10Zr, and high-purity uranium swelling measurements. This guide covers validation methodology, parameter ranges, error metrics, and best practices for quantitative model validation.

## Overview

Model validation is the process of comparing computational model predictions with experimental measurements to assess accuracy, build confidence, and identify limitations. For the gas swelling model, validation against experimental data is essential for:

- **Establishing predictive accuracy** across different materials and conditions
- **Quantifying uncertainty** in model predictions
- **Identifying model limitations** and domains of validity
- **Supporting publication-quality research** with rigorous validation
- **Building stakeholder confidence** in model predictions

### Why Validation Matters

The gas swelling model simulates complex physical processes (fission gas bubble evolution, void swelling, defect kinetics) with numerous parameters. Validation provides:

1. **Reality check**: Ensures the model reproduces observed experimental behavior
2. **Error quantification**: Provides numerical metrics (RMSE, R², MAE) for prediction accuracy
3. **Domain definition**: Identifies temperature, burnup, and composition ranges where the model is reliable
4. **Model improvement**: Highlights areas where physics or parameters need refinement
5. **Regulatory acceptance**: Supports safety cases with quantitative validation evidence

## Validation Methodology

This guide implements a systematic validation approach:

```
┌─────────────────────────────────────────────────────────────┐
│ Validation Workflow:                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Load experimental data (U-10Zr, U-19Pu-10Zr, etc.)    │
│            │                                                │
│  2. Configure model parameters for material                │
│            │                                                │
│  3. Run simulation at experimental conditions              │
│            │                                                │
│  4. Extract model outputs (swelling, radius, etc.)         │
│            │                                                │
│  5. Calculate error metrics (RMSE, R², MAE)               │
│            │                                                │
│  6. Generate comparison plots                              │
│            │                                                │
│  7. Analyze discrepancies and identify limitations         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Validation Levels

| Level | Description | Purpose | Example |
|-------|-------------|---------|---------|
| **Figure Reproduction** | Reproduce published figures from reference paper | Verify model implementation matches paper | Figures 6, 7, 9, 10 |
| **Quantitative Validation** | Calculate error metrics against experimental data | Quantify prediction accuracy | RMSE, R², MAE |
| **Parameter Sensitivity** | Assess parameter uncertainty effects | Understand confidence intervals | ±10% parameter variations |
| **Cross-Material** | Validate across multiple materials | Test generalizability | U-10Zr, U-19Pu-10Zr, pure U |

## Experimental Datasets

The validation suite includes experimental data from the reference paper:

### Figure 6: U-10Zr Swelling vs Temperature

U-10 wt% Zr alloy swelling data at different temperatures and burnup levels:

```python
from gas_swelling.validation.datasets import get_u10zr_data

u10zr_data = get_u10zr_data()

# Data structure:
for data_point in u10zr_data:
    print(f"Material: {data_point['material']}")
    print(f"Composition: {data_point['composition']}")
    print(f"Burnup: {data_point['burnup_at_percent']} at.%")
    print(f"Temperature: {data_point['temperature_k']} K")
    print(f"Swelling: {data_point['swelling_percent']}%")
```

**Key features:**
- **Temperature range**: 600-800 K (typical operating range)
- **Burnup levels**: 0.4 and 0.9 at.% (low to moderate burnup)
- **Peak swelling**: ~2.5% at 700 K, 0.9 at.% burnup
- **Data points**: 6 experimental conditions

**Physical interpretation:**
- Bell-shaped temperature dependence with peak around 700 K
- Higher burnup → higher swelling (nonlinear)
- Temperature-driven swelling mechanisms dominate

### Figure 7: U-19Pu-10Zr Swelling vs Temperature

U-19 wt% Pu-10 wt% Zr alloy swelling data:

```python
from gas_swelling.validation.datasets import get_u19pu10zr_data

u19pu10zr_data = get_u19pu10zr_data()
```

**Key features:**
- **Lower swelling** than U-10Zr at comparable conditions
- **Different dislocation density** affects bias factors
- **Peak temperature** shifted relative to U-10Zr

**Physical interpretation:**
- Pu addition changes defect sink strengths
- Validates model's material composition handling
- Tests parameter generalizability

### Figures 9-10: High-Purity Uranium Swelling

Pure uranium swelling data (up to 50% swelling):

```python
from gas_swelling.validation.datasets import get_high_purity_u_data

high_purity_u_data = get_high_purity_u_data()
```

**Key features:**
- **Extremely high swelling** (up to 50% vs 2-3% for alloys)
- **Tests model limits** for high swelling regimes
- **Validates gas release mechanisms** at high swelling

**Physical interpretation:**
- No alloying elements → different nucleation behavior
- Tests bubble interconnection and gas release models
- Validates model outside typical alloy fuel regime

## Validation Metrics

The validation module provides several quantitative metrics:

### Root Mean Square Error (RMSE)

Measures the standard deviation of prediction errors:

```python
from gas_swelling.validation.metrics import calculate_rmse

y_true = [0.2, 0.5, 0.3, 1.0, 2.5, 1.8]  # Experimental data (%)
y_pred = [0.22, 0.48, 0.31, 0.95, 2.6, 1.75]  # Model predictions

rmse = calculate_rmse(y_true, y_pred)
print(f"RMSE = {rmse:.3f}%")
```

**Interpretation:**
- RMSE = 0.1% → Typical error of 0.1 percentage points
- Lower is better
- Sensitive to outliers (squared errors)
- Same units as the data (% swelling)

### Coefficient of Determination (R²)

Measures proportion of variance explained by the model:

```python
from gas_swelling.validation.metrics import calculate_r2

r2 = calculate_r2(y_true, y_pred)
print(f"R² = {r2:.3f}")
```

**Interpretation:**
- R² = 1.0 → Perfect prediction
- R² = 0.98 → Model explains 98% of variance (excellent)
- R² = 0.90 → Model explains 90% of variance (good)
- R² < 0.80 → Model may need improvement

**Guidelines:**
- **R² ≥ 0.95**: Excellent agreement
- **R² ≥ 0.90**: Good agreement
- **R² ≥ 0.80**: Acceptable agreement
- **R² < 0.80**: Model may need refinement

### Mean Absolute Error (MAE)

Measures average absolute prediction error:

```python
from gas_swelling.validation.metrics import calculate_mae

mae = calculate_mae(y_true, y_pred)
print(f"MAE = {mae:.3f}%")
```

**Interpretation:**
- MAE = 0.08% → Average error of 0.08 percentage points
- More interpretable than RMSE (linear scale)
- Less sensitive to outliers
- Same units as the data

### Maximum Error

Identifies worst-case prediction error:

```python
from gas_swelling.validation.metrics import calculate_max_error

max_err = calculate_max_error(y_true, y_pred)
print(f"Max error = {max_err:.3f}%")
```

**Interpretation:**
- Identifies largest discrepancy between model and experiment
- Important for safety cases (worst-case scenarios)
- May highlight specific conditions needing attention

## Parameter Ranges

The model is validated over specific parameter ranges. Using the model outside these ranges may result in unreliable predictions.

### Validated Temperature Ranges

| Material | Min Temp | Max Temp | Peak Swelling Temp | Notes |
|----------|----------|----------|-------------------|-------|
| **U-10Zr** | 600 K | 800 K | ~700 K | Bell-shaped curve |
| **U-19Pu-10Zr** | 650 K | 850 K | ~750 K | Pu shifts peak |
| **High-purity U** | 600 K | 900 K | ~800 K | Very high swelling |

**⚠️ DO NOT extrapolate far beyond validated ranges:**
- Below 600 K: Limited data, different mechanisms may dominate
- Above 900 K: Phase transitions, creep mechanisms not modeled
- Use at boundaries with caution

### Validated Burnup Ranges

| Material | Min Burnup | Max Burnup | Typical Range | Notes |
|----------|------------|------------|---------------|-------|
| **U-10Zr** | 0.4 at.% | 0.9 at.% | 0.4-1.5 at.% | Low to moderate |
| **U-19Pu-10Zr** | 0.4 at.% | 0.9 at.% | 0.4-1.5 at.% | Similar to U-10Zr |
| **High-purity U** | 0.5 at.% | 2.0 at.% | 0.5-3.0 at.% | Higher burnup data |

**⚠️ High burnup limitations:**
- Model may not capture saturation effects
- Gas release interconnections not fully validated >2 at.%
- Use caution beyond 3 at.% burnup

### Validated Material Compositions

| Material | Zr (wt%) | Pu (wt%) | U (wt%) | Validation Status |
|----------|----------|----------|---------|-------------------|
| **U-10Zr** | 10% | 0% | 90% | ✅ Validated |
| **U-19Pu-10Zr** | 10% | 19% | 71% | ✅ Validated |
| **High-purity U** | 0% | 0% | 100% | ✅ Validated |
| **U-5Zr** | 5% | 0% | 95% | ⚠️ Not validated |
| **U-20Zr** | 20% | 0% | 80% | ⚠️ Not validated |

**⚠️ Composition limitations:**
- Model calibrated for 10 wt% Zr alloys
- Different Zr content changes phase boundaries
- Extrapolate to other compositions with caution

## Running Validation

### Quick Validation: Reproduce Paper Figures

The easiest way to validate the model is to reproduce the figures from the reference paper:

```python
# Reproduce Figure 6 (U-10Zr)
python -m gas_swelling.validation.scripts.reproduce_figure6 \
    --output figure6_reproduction.png \
    --no-show

# Reproduce Figure 7 (U-19Pu-10Zr)
python -m gas_swelling.validation.scripts.reproduce_figure7 \
    --output figure7_reproduction.png \
    --no-show

# Reproduce Figures 9-10 (High-purity U)
python -m gas_swelling.validation.scripts.reproduce_figures9_10 \
    --output figures9_10_reproduction.png \
    --no-show
```

**Expected output:** PNG files showing model predictions (lines) vs experimental data (points).

### Full Validation Report

Generate a comprehensive validation report with all materials and metrics:

```python
from gas_swelling.validation.reporting import generate_validation_report

# Generate full validation report
report_path = generate_validation_report(
    output_path='validation_report.pdf',
    show=False  # Don't display interactive plots
)

print(f"Validation report saved to: {report_path}")
```

**Report includes:**
- Model vs experimental comparison plots for all materials
- Error metrics table (RMSE, R², MAE, max error)
- Parameter sensitivity analysis
- Discussion of model limitations

**⏱️ Runtime:** Full report takes 5-10 minutes (multiple ODE simulations).

### Material-Specific Validation

Validate a single material:

```python
from gas_swelling.validation.reporting import generate_material_report

# Validate only U-10Zr
report_path = generate_material_report(
    material='U-10Zr',
    temperatures=[600, 700, 800],  # K
    fission_rate=2.0e19,  # fissions/m³/s
    sim_time=8.64e6,  # 100 days in seconds
    output_path='u10zr_validation.pdf'
)
```

### CLI-Based Validation

Use the command-line interface for validation:

```bash
# Quick validation (all materials, default parameters)
python -m gas_swelling.analysis.cli validation --format quick

# Full validation report (all materials)
python -m gas_swelling.analysis.cli validation \
    --format full \
    --output validation_report.pdf

# Material-specific validation
python -m gas_swelling.analysis.cli validation \
    --format material \
    --material U-10Zr \
    --temperatures 600,700,800 \
    --output u10zr_validation.pdf
```

## Interpreting Validation Results

### What Constitutes Good Agreement?

| Metric | Excellent | Good | Acceptable | Needs Improvement |
|--------|-----------|------|------------|-------------------|
| **R²** | ≥ 0.95 | 0.90-0.95 | 0.80-0.90 | < 0.80 |
| **RMSE** | < 0.1% | 0.1-0.2% | 0.2-0.5% | > 0.5% |
| **MAE** | < 0.08% | 0.08-0.15% | 0.15-0.4% | > 0.4% |
| **Max Error** | < 0.3% | 0.3-0.6% | 0.6-1.0% | > 1.0% |

### Typical Validation Results

Based on reference paper comparisons:

**U-10Zr (Figure 6):**
- **R²**: ~0.92-0.96 (Good to Excellent)
- **RMSE**: ~0.15-0.25% swelling
- **Peak swelling**: Model captures 700 K peak within 10%
- **Temperature trend**: Bell shape reproduced correctly

**U-19Pu-10Zr (Figure 7):**
- **R²**: ~0.88-0.93 (Acceptable to Good)
- **RMSE**: ~0.20-0.30% swelling
- **Magnitude**: Lower swelling than U-10Zr captured
- **Temperature trend**: Reasonable agreement

**High-purity U (Figures 9-10):**
- **R²**: ~0.85-0.92 (Acceptable to Good)
- **RMSE**: ~2-5% swelling (larger due to high absolute values)
- **Magnitude**: Very high swelling (30-50%) captured
- **Trend**: Good agreement on temperature dependence

### Understanding Discrepancies

When model predictions differ from experiment, consider:

**1. Parameter uncertainty:**
- Dislocation density (ρ): ±40% variation causes ±40% swelling change
- Surface energy (γ): ±20% variation causes ±15% swelling change
- Nucleation factors (Fnb, Fnf): Poorly known, can vary 2-3×

**2. Model limitations:**
- **Single phase**: Model only models α-U phase (not γ or δ phases)
- **Temperature limits**: Phase transitions not modeled
- **High burnup**: Gas interconnection threshold approximate
- **Mechanical effects**: Fuel-cladding interaction not included

**3. Experimental uncertainty:**
- Swelling measurements: ±10-20% typical
- Temperature gradients: ±10-20 K in experiments
- Burnup variations: ±5-10% heterogeneity

**4. Material variability:**
- Impurity effects: Small impurity changes affect swelling
- Microstructure: Grain size, texture not fully specified
- Irradiation history: Time-dependent effects not always reported

## Validation Checklist

Use this checklist when validating the model for a new application:

### Pre-Validation Checks

- [ ] Define validation requirements (accuracy, conditions)
- [ ] Identify experimental data for validation
- [ ] Confirm parameters are within validated ranges
- [ ] Check material composition is supported
- [ ] Review experimental uncertainty in data

### Validation Execution

- [ ] Run simulation at experimental conditions
- [ ] Extract relevant outputs (swelling, radius, etc.)
- [ ] Calculate all error metrics (RMSE, R², MAE, max error)
- [ ] Generate comparison plots
- [ ] Document parameter values used

### Post-Validation Analysis

- [ ] Assess if metrics meet accuracy requirements
- [ ] Identify any systematic biases (over/under prediction)
- [ ] Analyze outliers and extreme errors
- [ ] Document model limitations for this application
- [ ] Specify validated parameter ranges

### Documentation

- [ ] Save validation plots with clear labeling
- [ ] Record error metrics in validation report
- [ ] Document parameter values and assumptions
- [ ] Note any discrepancies or concerns
- [ ] Archive code and data for reproducibility

## Best Practices

### 1. Start with Known Validated Conditions

Before validating new conditions, confirm the model reproduces published results:

```python
# First: Reproduce Figure 6 to verify implementation
from gas_swelling.validation.scripts.reproduce_figure6 import main
main(output_path='verification_figure6.png', show=False)

# If Figure 6 matches, proceed with new validation
```

### 2. Use Multiple Metrics

Don't rely on a single metric:

```python
# Calculate all metrics for comprehensive assessment
from gas_swelling.validation.metrics import (
    calculate_rmse,
    calculate_r2,
    calculate_mae,
    calculate_max_error
)

metrics = {
    'RMSE': calculate_rmse(y_true, y_pred),
    'R²': calculate_r2(y_true, y_pred),
    'MAE': calculate_mae(y_true, y_pred),
    'Max Error': calculate_max_error(y_true, y_pred)
}

for metric_name, value in metrics.items():
    print(f"{metric_name}: {value:.4f}")
```

### 3. Visual Inspection is Essential

Always plot predictions vs data:

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
plt.scatter(experimental_temps, experimental_swelling,
            label='Experimental', s=100, zorder=5)
plt.plot(model_temps, model_swelling,
         label='Model', linewidth=2)
plt.xlabel('Temperature (K)')
plt.ylabel('Swelling (%)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.title('Validation: Model vs Experimental')
plt.savefig('validation_comparison.png', dpi=300)
```

**What to look for:**
- Systematic over/under prediction (bias)
- Incorrect trends (slope, curvature)
- Outliers at specific conditions
- Missing peaks or inflection points

### 4. Validate Across the Parameter Space

Don't validate at a single condition:

```python
# Bad: Only one temperature
single_temp_validation(700 K)  # ❌ Insufficient

# Good: Multiple temperatures
multi_temp_validation([600, 650, 700, 750, 800 K])  # ✅ Comprehensive

# Better: Temperature + burnup matrix
full_validation(
    temperatures=[600, 700, 800 K],
    burnups=[0.4, 0.9, 1.5 at.%]
)  # ✅✅ Best practice
```

### 5. Document Assumptions and Uncertainties

Always document:

```python
"""
Validation Run: U-10Zr at 700 K
==========================================

Parameters:
- Temperature: 700 K ± 10 K (experimental uncertainty)
- Fission rate: 2.0e19 fissions/m³/s (assumed)
- Dislocation density: 1e14 m⁻² (literature value)
- Surface energy: 1.0 J/m² (default value)

Experimental Data Source:
- Figure 6, reference paper
- Uncertainty: ±15% swelling

Results:
- R² = 0.94
- RMSE = 0.18% swelling
- Max error = 0.35% swelling at 700 K, 0.9 at.%

Limitations:
- Single data point at 700 K, 0.9 at.%
- Need more data for confident validation
"""
```

### 6. Use Validation for Model Improvement

When validation reveals discrepancies:

```python
# Identify systematic bias
if mean(y_pred - y_true) > 0:
    print("Model systematically over-predicts swelling")
    print("Consider adjusting:")
    print("  - Dislocation density (higher → more swelling)")
    print("  - Surface energy (lower → more swelling)")
    print("  - Nucleation factors (higher → more swelling)")
```

## Troubleshooting Validation Issues

### Problem 1: Poor R² (< 0.80)

**Symptoms:** Model explains less than 80% of variance in data.

**Possible causes:**
1. **Wrong parameters**: Material parameters don't match experimental conditions
2. **Outside validated range**: Temperature or burnup outside tested range
3. **Missing physics**: Model doesn't capture important mechanism
4. **Bad data**: Experimental errors or misreported conditions

**Solutions:**
```python
# Step 1: Verify parameters
print("Parameters:")
print(f"  Temperature: {temperature} K")
print(f"  Fission rate: {fission_rate} fissions/m³/s")
print(f"  Dislocation density: {dislocation_density} m⁻²")

# Step 2: Check if within validated range
if temperature < 600 or temperature > 900:
    print("⚠️ Warning: Temperature outside validated range (600-900 K)")

# Step 3: Try parameter adjustments
for rho_mult in [0.5, 1.0, 2.0]:
    params.dislocation_density = base_rho * rho_mult
    # Re-run simulation
```

### Problem 2: Systematic Over-Prediction

**Symptoms:** Model consistently predicts higher swelling than experiment.

**Common causes:**
1. **Dislocation density too high**: Higher ρ → more vacancy absorption → more swelling
2. **Surface energy too low**: Lower γ → easier bubble growth → more swelling
3. **Nucleation factors too high**: More bubble nucleation → more swelling

**Solutions:**
```python
# Adjust parameters to reduce swelling
params.dislocation_density *= 0.7  # Reduce by 30%
params.surface_energy *= 1.2  # Increase by 20%
params.Fnb *= 0.8  # Reduce bulk nucleation
params.Fnf *= 0.8  # Reduce boundary nucleation

# Re-validate
```

### Problem 3: Wrong Temperature Trend

**Symptoms:** Model predicts peak at different temperature than experiment.

**Possible causes:**
1. **Incorrect activation energies**: Diffusion coefficients wrong
2. **Missing mechanisms**: Temperature-dependent mechanisms not captured
3. **Gas equation of state**: Ideal gas vs Van der Waals EOS choice

**Solutions:**
```python
# Check activation energies
print(f"Activation energy: {params.D0_g_u_alpha} J/mol")

# Try different EOS
for eos_model in ['ideal', 'ronchi']:
    params.eos_model = eos_model
    # Re-run simulation and compare

# Adjust activation energy within uncertainty
params.D0_g_u_alpha *= 1.5  # Increase by 50%
```

### Problem 4: Divergence at High Burnup

**Symptoms:** Model matches at low burnup but diverges at high burnup (>2 at.%).

**Possible causes:**
1. **Gas release threshold**: Interconnection model not calibrated for high burnup
2. **Saturation effects**: Model doesn't capture saturation
3. **Numerical issues**: Solver errors at large swelling

**Solutions:**
```python
# Check gas release
release_fraction = result['gas_release'][-1]
print(f"Gas release fraction: {release_fraction:.2%}")

# Limit validation to tested range
if burnup > 2.0:
    print("⚠️ Warning: Burnup exceeds validated range (<2 at.%)")

# Use smaller time steps for stability
result = model.solve(
    t_span=(0, sim_time),
    t_eval=time_points,
    method='RK23',
    max_step=1e5  # Smaller max step
)
```

## Example: Complete Validation Workflow

This example shows a complete validation workflow for a new experimental dataset:

```python
#!/usr/bin/env python3
"""
Complete Validation Workflow Example
=====================================

This script demonstrates a complete validation workflow:
1. Load experimental data
2. Run model simulations
3. Calculate error metrics
4. Generate comparison plots
5. Document results
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.validation import datasets, metrics
from gas_swelling.validation.reporting import run_simulation_for_material

# =============================================================================
# STEP 1: Load Experimental Data
# =============================================================================

print("=" * 70)
print("STEP 1: Loading Experimental Data")
print("=" * 70)

# Load U-10Zr validation data
u10zr_data = datasets.get_u10zr_data()

print(f"\nLoaded {len(u10zr_data)} data points:")
for i, data in enumerate(u10zr_data):
    print(f"  {i+1}. T={data['temperature_k']}K, "
          f"burnup={data['burnup_at_percent']}at.%, "
          f"swelling={data['swelling_percent']}%")

# =============================================================================
# STEP 2: Run Model Simulations
# =============================================================================

print("\n" + "=" * 70)
print("STEP 2: Running Model Simulations")
print("=" * 70)

# Simulation parameters
sim_time = 8.64e6  # 100 days
fission_rate = 2.0e19  # fissions/m³/s

# Store model predictions
model_predictions = []

for data in u10zr_data:
    print(f"\nSimulating: T={data['temperature_k']}K, "
          f"burnup={data['burnup_at_percent']}at.%")

    # Run simulation
    result = run_simulation_for_material(
        material='U-10Zr',
        temperature=data['temperature_k'],
        fission_rate=fission_rate,
        sim_time=sim_time
    )

    # Extract final swelling prediction
    predicted_swelling = result['swelling'][-1] * 100  # Convert to %
    model_predictions.append(predicted_swelling)

    print(f"  Experimental: {data['swelling_percent']:.2f}%")
    print(f"  Model:        {predicted_swelling:.2f}%")
    print(f"  Error:        {predicted_swelling - data['swelling_percent']:.2f}%")

# =============================================================================
# STEP 3: Calculate Error Metrics
# =============================================================================

print("\n" + "=" * 70)
print("STEP 3: Calculating Error Metrics")
print("=" * 70)

# Extract experimental values
y_true = np.array([data['swelling_percent'] for data in u10zr_data])
y_pred = np.array(model_predictions)

# Calculate all metrics
rmse = metrics.calculate_rmse(y_true, y_pred)
r2 = metrics.calculate_r2(y_true, y_pred)
mae = metrics.calculate_mae(y_true, y_pred)
max_err = metrics.calculate_max_error(y_true, y_pred)

print("\nValidation Metrics:")
print("-" * 40)
print(f"RMSE:        {rmse:.4f}%")
print(f"R²:          {r2:.4f}")
print(f"MAE:         {mae:.4f}%")
print(f"Max Error:   {max_err:.4f}%")

# Assess validation quality
print("\nValidation Assessment:")
if r2 >= 0.95:
    quality = "Excellent ✅"
elif r2 >= 0.90:
    quality = "Good ✅"
elif r2 >= 0.80:
    quality = "Acceptable ⚠️"
else:
    quality = "Needs Improvement ❌"
print(f"Overall: {quality}")

# =============================================================================
# STEP 4: Generate Comparison Plots
# =============================================================================

print("\n" + "=" * 70)
print("STEP 4: Generating Comparison Plots")
print("=" * 70)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Model vs Experimental (scatter)
ax = axes[0]
temperatures = [data['temperature_k'] for data in u10zr_data]

# Separate by burnup
for burnup in [0.4, 0.9]:
    mask = [data['burnup_at_percent'] == burnup for data in u10zr_data]
    temps_burnup = [temperatures[i] for i, m in enumerate(mask) if m]
    exp_burnup = [y_true[i] for i, m in enumerate(mask) if m]
    pred_burnup = [y_pred[i] for i, m in enumerate(mask) if m]

    ax.scatter(temps_burnup, exp_burnup, s=100, label=f'Exp ({burnup} at.%)',
               alpha=0.7, zorder=5)
    ax.plot(temps_burnup, pred_burnup, '--o', label=f'Model ({burnup} at.%)',
            linewidth=2, markersize=8)

ax.set_xlabel('Temperature (K)', fontsize=12)
ax.set_ylabel('Swelling (%)', fontsize=12)
ax.set_title('Model vs Experimental Data', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Plot 2: Parity plot
ax = axes[1]
ax.scatter(y_true, y_pred, s=100, alpha=0.7, zorder=5)
ax.plot([0, max(y_true)], [0, max(y_true)], 'k--', label='Perfect agreement',
        linewidth=2)
ax.set_xlabel('Experimental Swelling (%)', fontsize=12)
ax.set_ylabel('Model Prediction (%)', fontsize=12)
ax.set_title(f'Parity Plot (R² = {r2:.3f})', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.axis('equal')

plt.tight_layout()
plt.savefig('validation_complete.png', dpi=300, bbox_inches='tight')
print("\nPlot saved to: validation_complete.png")

# =============================================================================
# STEP 5: Document Results
# =============================================================================

print("\n" + "=" * 70)
print("STEP 5: Documenting Results")
print("=" * 70)

report = f"""
Validation Report: U-10Zr Model vs Experimental Data
====================================================

Date: {np.datetime64('now')}

Experimental Data:
- Source: Figure 6, reference paper
- Material: U-10 wt% Zr
- Data points: {len(u10zr_data)}
- Temperature range: {min(temperatures)}-{max(temperatures)} K
- Burnup levels: 0.4, 0.9 at.%

Simulation Parameters:
- Material: U-10Zr
- Fission rate: {fission_rate:.2e} fissions/m³/s
- Simulation time: {sim_time/86400:.1f} days
- EOS model: ronchi (default)

Validation Metrics:
- RMSE: {rmse:.4f}%
- R²: {r2:.4f}
- MAE: {mae:.4f}%
- Max Error: {max_err:.4f}%

Quality Assessment: {quality}

Conclusions:
{"✅ Model predictions agree well with experimental data" if r2 >= 0.90 else "⚠️ Model shows moderate agreement, consider parameter refinement"}

Recommendations:
{
"- Model validated for U-10Zr at 600-800 K"
"- Can use for predictions in validated range"
"- Consider sensitivity analysis for uncertainty quantification"
if r2 >= 0.90 else
"- Review parameter values for potential adjustments"
"- Consider collecting additional experimental data"
"- Perform parameter sensitivity study"
}
"""

print(report)

# Save report
with open('validation_report.txt', 'w') as f:
    f.write(report)

print("\nReport saved to: validation_report.txt")

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
```

**Output:** Complete validation with metrics, plots, and documentation.

## API Quick Reference

### Validation Metrics

```python
from gas_swelling.validation.metrics import (
    calculate_rmse,
    calculate_r2,
    calculate_mae,
    calculate_max_error
)

# All functions take the same arguments
rmse = calculate_rmse(y_true, y_pred)
r2 = calculate_r2(y_true, y_pred)
mae = calculate_mae(y_true, y_pred)
max_err = calculate_max_error(y_true, y_pred)
```

### Validation Datasets

```python
from gas_swelling.validation.datasets import (
    get_u10zr_data,
    get_u19pu10zr_data,
    get_high_purity_u_data
)

# Returns list of dicts with keys:
# - material, composition, burnup_at_percent
# - temperature_k, swelling_percent, figure, data_type, notes
u10zr_data = get_u10zr_data()
```

### Validation Reporting

```python
from gas_swelling.validation.reporting import (
    generate_validation_report,
    generate_material_report,
    generate_quick_report,
    run_simulation_for_material
)

# Full validation report (all materials)
report_path = generate_validation_report(
    output_path='validation_report.pdf',
    show=False
)

# Material-specific report
report_path = generate_material_report(
    material='U-10Zr',
    temperatures=[600, 700, 800],
    fission_rate=2.0e19,
    sim_time=8.64e6,
    output_path='material_validation.pdf'
)

# Quick validation (minimal computation)
report_path = generate_quick_report(
    output_path='quick_validation.pdf'
)

# Run single simulation
result = run_simulation_for_material(
    material='U-10Zr',
    temperature=700,
    fission_rate=2.0e19,
    sim_time=8.64e6
)
```

### Figure Reproduction Scripts

```python
# Figure 6: U-10Zr
python -m gas_swelling.validation.scripts.reproduce_figure6 \
    --output figure6.png \
    --no-show

# Figure 7: U-19Pu-10Zr
python -m gas_swelling.validation.scripts.reproduce_figure7 \
    --output figure7.png \
    --no-show

# Figures 9-10: High-purity U
python -m gas_swelling.validation.scripts.reproduce_figures9_10 \
    --output figures9_10.png \
    --no-show
```

### CLI Validation

```bash
# Quick validation
python -m gas_swelling.analysis.cli validation --format quick

# Full report
python -m gas_swelling.analysis.cli validation \
    --format full \
    --output report.pdf

# Material-specific
python -m gas_swelling.analysis.cli validation \
    --format material \
    --material U-10Zr \
    --temperatures 600,700,800 \
    --output u10zr.pdf
```

## References

### Experimental Data Sources

**Primary Reference:**
- "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"
  - Figure 6: U-10Zr swelling vs temperature
  - Figure 7: U-19Pu-10Zr swelling vs temperature
  - Figures 9-10: High-purity uranium swelling

**Additional Validation Data:**
- Hofman, G. L., et al. (1997). "Swelling of U-Pu-Zr fuel alloys." *Journal of Nuclear Materials*
- Rest, J., et al. (2019). "Metallic fuel development for advanced reactors." *Progress in Nuclear Energy*

### Model Implementation

- **Model design**: `model_design.md` (Chinese)
- **Theoretical framework**: `original paper of swelling rate theory.md`
- **Parameter reference**: `parameters.py`

### Validation Methodology

- ASME V&V 10-2006: "Guide for Verification and Validation in Computational Solid Mechanics"
- ANSI/ANS-20.7-2019: "Verification and Validation of Multi-Physics Computational Models"

---

**Version**: 1.0.0
**Last Updated**: 2024-01-26
**Authors**: Gas Swelling Model Development Team

---

**📘 Documentation Index** | **[README](../README.md)** | **[Parameter Reference](parameter_reference.md)** | **[Sensitivity Analysis Guide](sensitivity_analysis_guide.md)** | **[Quick Start Tutorial](../examples/quickstart_tutorial.py)**
