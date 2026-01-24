# Sensitivity Analysis Guide for Gas Swelling Model

A comprehensive guide to performing parameter sensitivity analysis on the gas swelling model to identify influential parameters, quantify uncertainties, and prioritize experimental measurements.

## Overview

Sensitivity analysis is a powerful tool for understanding how model parameters affect predictions. For the gas swelling model, sensitivity analysis can help:

- **Identify critical parameters** that most affect swelling predictions
- **Quantify uncertainty** in model outputs due to parameter variations
- **Prioritize experimental work** by highlighting parameters needing better measurement
- **Understand parameter interactions** and nonlinear behavior
- **Validate model robustness** across the parameter space

### Why Sensitivity Analysis Matters

The gas swelling model contains numerous physical parameters (diffusion coefficients, nucleation factors, dislocation density, etc.) with varying levels of experimental uncertainty. Sensitivity analysis helps:

1. **Focus research efforts** on the most influential parameters
2. **Understand confidence intervals** in swelling predictions
3. **Support safety cases** with uncertainty quantification
4. **Guide model calibration** by identifying sensitive parameters
5. **Communicate model limitations** to stakeholders

## Sensitivity Analysis Methods

This guide covers three complementary sensitivity analysis methods:

| Method | Type | Cost | Best For | Output |
|--------|------|------|----------|--------|
| **OAT** | Local | Low | Initial screening, local effects | Elasticity coefficients |
| **Morris** | Global screening | Medium | Ranking many parameters, detecting nonlinearity | μ, μ*, σ statistics |
| **Sobol** | Global variance-based | High | Quantitative analysis, interaction effects | S1, ST indices |

### Quick Selection Guide

```
┌─────────────────────────────────────────────────────────────┐
│ Choose your method:                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  START → Many parameters? (>10)                            │
│            │                                                │
│            ├─ Yes → Need quick screening?                  │
│            │         ├─ Yes → Morris method                │
│            │         └─ No → Sobol method (expensive)      │
│            │                                                │
│            └─ Few parameters (<10) → Need quantitative?    │
│                              ├─ Yes → Sobol method         │
│                              └─ No → OAT or Morris         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Method 1: One-at-a-Time (OAT) Analysis

### What is OAT?

One-at-a-Time (OAT) analysis varies **one parameter at a time** while keeping all other parameters at their nominal (baseline) values. It measures the **local sensitivity** of model outputs to small parameter changes.

### How It Works

1. Run baseline simulation with nominal parameters
2. For each parameter:
   - Vary by ±Δ% (e.g., ±10%)
   - Run simulation with perturbed parameter
   - Calculate sensitivity metrics
3. Rank parameters by sensitivity magnitude

### Sensitivity Metrics

OAT analysis provides several metrics:

#### **Normalized Sensitivity (Elasticity)**
Measures the percentage change in output per percentage change in input:

```
S = (Δy/y₀) / (Δx/x₀)
```

**Interpretation:**
- `S = 1.0`: 1% increase in parameter → 1% increase in output
- `S = -2.0`: 1% increase in parameter → 2% decrease in output
- `|S| > 1`: Output is more sensitive than parameter (amplified)
- `|S| < 1`: Output is less sensitive than parameter (damped)

#### **Absolute Sensitivity**
Measures the change in output per unit change in parameter:

```
S_abs = Δy / Δx
```

**Interpretation:** Physical units of output per physical units of input (e.g., % swelling per K temperature).

### When to Use OAT

✅ **Good for:**
- Initial parameter screening
- Understanding local parameter effects
- Quick sensitivity assessment with limited compute
- Model calibration and parameter ranking
- Identifying dominant parameters near nominal values

❌ **Not suitable for:**
- Capturing parameter interactions
- Global sensitivity analysis (far from nominal)
- Highly nonlinear models
- Uncertainty quantification with correlated parameters

### Example: OAT Analysis

```python
from gas_swelling.analysis.sensitivity import OATAnalyzer, create_default_parameter_ranges
from gas_swelling.analysis.visualization import plot_tornado
from gas_swelling.params import create_default_parameters

# Step 1: Define parameter ranges
param_ranges = create_default_parameter_ranges()

# Step 2: Initialize OAT analyzer
analyzer = OATAnalyzer(
    parameter_ranges=param_ranges,
    output_names=['swelling', 'Rcb', 'gas_release'],  # Outputs to analyze
    sim_time=8.64e6,  # 100 days
    t_eval_points=100
)

# Step 3: Run OAT analysis (±10% variations)
results = analyzer.run_oat_analysis(
    percent_variations=[-10, 10],  # Vary each parameter by ±10%
    verbose=True
)

# Step 4: Visualize results
plot_tornado(
    results,
    output_name='swelling',
    metric='elasticity',
    title='OAT Sensitivity Analysis - Swelling',
    save_path='oat_tornado_swelling.png'
)

# Step 5: Print sensitivity ranking
print("\nParameter Ranking by Elasticity:")
print("-" * 50)
for result in sorted(results, key=lambda r: abs(r.sensitivities['swelling']['elasticity']), reverse=True):
    param = result.parameter_name
    elast = result.sensitivities['swelling']['elasticity']
    print(f"{param:25s}: {elast:8.2f}")
```

### Interpreting OAT Results

**Tornado Plot Interpretation:**

```
Parameter      Elasticity    Interpretation
────────────────────────────────────────────────────────
dislocation_density   2.35   Strong positive: Higher ρ → more swelling
surface_energy       -1.80   Strong negative: Higher γ → less swelling
temperature           0.95   Moderate positive: T ~ proportional to swelling
Fnb                    0.45   Weak positive: Small effect on swelling
```

**Key insights:**
- **Magnitude** (`|S|`): Strength of parameter influence
- **Sign** (+/-): Direction of correlation
- **Ranking**: Most to least important parameters

**Example interpretation:**
> "Dislocation density has the strongest effect on swelling (elasticity = 2.35). A 10% increase in dislocation density causes a 23.5% increase in swelling. Surface energy shows a strong negative effect (-1.80), meaning higher surface energy suppresses bubble growth and reduces swelling."

---

## Method 2: Morris Elementary Effects Screening

### What is Morris?

Morris method is a **global screening technique** that computes **elementary effects** by varying one parameter at a time along random trajectories through the parameter space. It's efficient for screening many parameters.

### How It Works

1. Generate `r` random trajectories through parameter space
2. Each trajectory visits `p` parameters once (p = number of parameters)
3. Compute elementary effect for each parameter along each trajectory:
   ```
   EE_i = [y(x₁, ..., x_i + Δ, ..., x_p) - y(x)] / Δ
   ```
4. Calculate statistics across all trajectories:
   - **μ (mu)**: Mean of elementary effects (overall influence)
   - **μ* (mu_star)**: Mean of absolute effects (magnitude of influence)
   - **σ (sigma)**: Standard deviation (nonlinearity/interactions)

### Morris Statistics

| Statistic | Formula | Meaning |
|-----------|---------|---------|
| **μ** | mean(EE) | Overall influence (signed) |
| **μ*** | mean(\|EE\|) | Magnitude of influence |
| **σ** | std(EE) | Nonlinearity / interactions |

**Interpretation:**

| μ* | σ | Interpretation |
|----|---|----------------|
| High | Low | Linear, important parameter |
| High | High | Nonlinear or interacting parameter |
| Low | Low | Unimportant parameter |
| Low | High | Parameter interacting with others |

**Morris Plot:** μ* (x-axis) vs σ (y-axis) with parameter labels.

### When to Use Morris

✅ **Good for:**
- Screening many parameters (efficient)
- Identifying influential vs non-influential parameters
- Understanding nonlinearity and parameter interactions
- Global sensitivity with limited computational budget
- Preliminary analysis before detailed Sobol study

❌ **Not suitable for:**
- Precise quantitative sensitivity indices
- Separating interaction effects from higher-order effects
- Models with very few parameters (use OAT or Sobol instead)

### Example: Morris Analysis

```python
from gas_swelling.analysis.sensitivity import MorrisAnalyzer, create_default_parameter_ranges
from gas_swelling.analysis.visualization import plot_morris, plot_sensitivity_heatmap
import numpy as np

# Step 1: Define parameter ranges
param_ranges = create_default_parameter_ranges()

# Step 2: Initialize Morris analyzer
analyzer = MorrisAnalyzer(
    parameter_ranges=param_ranges,
    output_names=['swelling'],
    sim_time=8.64e6,
    t_eval_points=100
)

# Step 3: Run Morris analysis
# r = number of trajectories (typically 10-50)
results = analyzer.run_morris_analysis(
    n_trajectories=25,  # More trajectories = better statistics
    random_state=42,    # For reproducibility
    verbose=True
)

# Step 4: Visualize results
# Morris plot (μ* vs σ)
plot_morris(
    results,
    output_name='swelling',
    figsize=(10, 8),
    title='Morris Screening - Swelling',
    save_path='morris_swelling.png'
)

# Step 5: Extract and print statistics
print("\nMorris Statistics (μ* and σ):")
print("-" * 60)
print(f"{'Parameter':<25} {'μ*':>10} {'σ':>10} {'Classification':>15}")
print("-" * 60)

for result in results:
    param = result.parameter_name
    mu_star = result.mu_star['swelling']
    sigma = result.sigma['swelling']

    # Classify parameter
    if mu_star > 0.5 and sigma < 0.3:
        classification = "Linear, Important"
    elif mu_star > 0.5 and sigma >= 0.3:
        classification = "Nonlinear/Interacting"
    elif mu_star <= 0.5 and sigma < 0.3:
        classification = "Unimportant"
    else:
        classification = "Interacting"

    print(f"{param:<25} {mu_star:10.3f} {sigma:10.3f} {classification:>15}")
```

### Interpreting Morris Results

**Morris Plot Quadrants:**

```
           σ (nonlinearity)
           ↑
    High   │  [Quadrant II]    │  [Quadrant I]
           │  Nonlinear/       │  Nonlinear/
           │  Interacting      │  Interacting
           │  Important        │  Unimportant
           │───────────────────┼──────────────→ μ*
           │  [Quadrant III]   │  [Quadrant IV]
    Low    │  Linear           │  Linear
           │  Important        │  Unimportant
           │                   │
```

**Typical findings for gas swelling model:**

```
Parameter              μ*      σ      Classification
──────────────────────────────────────────────────────
dislocation_density   2.45   0.35    Nonlinear, Important
temperature           1.80   0.85    Nonlinear, Interacting
surface_energy       1.65   0.20    Linear, Important
Fnb                   0.45   0.15    Linear, Unimportant
Fnf                   0.72   0.55    Nonlinear, Interacting
```

**Key insights:**
- **Temperature**: High μ* and σ → strongly influential with nonlinear behavior
- **Dislocation density**: High μ* but moderate σ → important but mostly linear
- **Nucleation factors**: Lower μ* → less influential on overall swelling

---

## Method 3: Sobol Variance-Based Analysis

### What is Sobol?

Sobol analysis is a **variance-based global sensitivity method** that decomposes the output variance into contributions from individual parameters and their interactions. It provides rigorous **quantitative sensitivity indices**.

### How It Works

1. Generate two independent samples (A and B) of size N using Saltelli's method
2. Create N × p additional matrices by swapping columns
3. Run simulations for all sample points (total N × (2 + p) runs)
4. Decompose output variance:
   ```
   V(Y) = Σ_i V_i + Σ_i Σ_{j>i} V_{ij} + Σ_i Σ_{j>i} Σ_{k>j} V_{ijk} + ...
   ```
5. Calculate sensitivity indices:
   - **S1** (first-order): Main effect of each parameter
   - **ST** (total-order): Main effect + all interactions

### Sobol Indices

| Index | Formula | Meaning |
|-------|---------|---------|
| **S1** | V_i / V(Y) | Fraction of variance due to parameter i alone |
| **ST** | 1 - V_{~i} / V(Y) | Fraction due to parameter i including interactions |

**Key relationship:**
```
ST - S1 ≈ strength of interactions involving parameter i
```

**Interpretation:**

| S1 | ST | Meaning |
|----|----|---------|
| High | Low (≈S1) | Parameter acts independently |
| High | High (»S1) | Parameter has strong interactions |
| Low | Low | Parameter is unimportant |
| Low | High | Parameter mainly through interactions |

### When to Use Sobol

✅ **Good for:**
- Quantitative sensitivity analysis with precise error estimates
- Understanding parameter interactions (ST - S1)
- Models with moderate number of parameters (<20)
- Validating models with rigorous uncertainty quantification
- When computational budget allows for extensive sampling

❌ **Not suitable for:**
- Quick screening (use Morris instead)
- Models with many parameters (computational cost scales linearly)
- Limited computational resources

### Computational Cost

```
Total simulations = N × (2 + p)

where:
  N = base sample size (typically 500-5000)
  p = number of parameters

Example: 10 parameters, N=1000 → 1000 × (2 + 10) = 12,000 simulations
```

**Rule of thumb:** Use N = 1000-5000 for accurate confidence intervals.

### Example: Sobol Analysis

```python
from gas_swelling.analysis.sensitivity import SobolAnalyzer, create_default_parameter_ranges
from gas_swelling.analysis.visualization import plot_sobol, plot_sobol_convergence
import numpy as np

# Step 1: Define parameter ranges
param_ranges = create_default_parameter_ranges()

# Step 2: Initialize Sobol analyzer
analyzer = SobolAnalyzer(
    parameter_ranges=param_ranges,
    output_names=['swelling', 'Rcb', 'gas_release'],
    sim_time=8.64e6,
    t_eval_points=100
)

# Step 3: Run Sobol analysis
# n_samples = base sample size (N)
results = analyzer.run_sobol_analysis(
    n_samples=1000,      # N = 1000 → 1000 × (2 + p) simulations
    random_state=42,
    verbose=True,
    n_jobs=-1            # Use all CPU cores for parallel execution
)

# Step 4: Visualize results
# Sobol bar chart (S1 and ST)
plot_sobol(
    results,
    output_name='swelling',
    figsize=(12, 6),
    title='Sobol Sensitivity Indices - Swelling',
    save_path='sobol_swelling.png'
)

# Convergence plot (check if N is large enough)
plot_sobol_convergence(
    results,
    output_name='swelling',
    figsize=(10, 6),
    title='Sobol Convergence - Swelling',
    save_path='sobol_convergence_swelling.png'
)

# Step 5: Extract and print indices
print("\nSobol Sensitivity Indices:")
print("-" * 70)
print(f"{'Parameter':<25} {'S1':>10} {'ST':>10} {'ST-S1':>10} {'Type':>15}")
print("-" * 70)

for result in results:
    param = result.parameter_name
    S1 = result.S1['swelling']
    ST = result.ST['swelling']
    interaction = ST - S1

    # Classify parameter
    if S1 > 0.1:
        if interaction > 0.05:
            param_type = "Interacting"
        else:
            param_type = "Independent"
    else:
        if ST > 0.1:
            param_type = "Pure interaction"
        else:
            param_type = "Unimportant"

    print(f"{param:<25} {S1:10.3f} {ST:10.3f} {interaction:10.3f} {param_type:>15}")
```

### Interpreting Sobol Results

**Understanding S1 and ST:**

```
Parameter          S1      ST    ST-S1    Interpretation
────────────────────────────────────────────────────────────
dislocation_density 0.42   0.65   0.23    Strong main effect + interactions
temperature         0.28   0.55   0.27    Strong interactions with other params
surface_energy      0.18   0.22   0.04    Mostly independent effect
Fnb                 0.03   0.05   0.02    Unimportant
Fnf                 0.08   0.35   0.27    Important through interactions
```

**Key insights:**

1. **Dislocation density**: S1=0.42 → 42% of output variance explained alone; total 65%
2. **Temperature**: Lower S1 (0.28) but high ST (0.55) → strong interactions
3. **Surface energy**: S1≈ST (0.18 vs 0.22) → acts mostly independently
4. **Nucleation factors**: Low S1 but moderate ST for Fnf → interactions important

**Convergence check:** Ensure confidence intervals are small enough for your needs. Increase N if indices have large uncertainty.

---

## Choosing the Right Method

### Decision Tree

```
                   START
                     │
        ┌────────────┴────────────┐
        │                         │
    Quick analysis?          Rigorous analysis?
        │                         │
        ├─ Yes                    ├─ Yes
        │  │                      │  │
        │  ├─ Many params?        │  ├─ Few params (<10)?
        │  │  (>10)               │  │
        │  │  │                   │  │  └─ Yes → Sobol
        │  │  └─ Yes → Morris     │  │
        │  │                      │  └─ No (many params)
        │  └─ No (few params)     │     │
        │     │                   │     ├─ Need screening → Morris
        │     └─ OAT              │     └─ Need detailed → Sobol (expensive)
        │                         │
        └─ No                     └─ No → OAT
           (need screening)          (quick local analysis)
```

### Comparison Summary

| Aspect | OAT | Morris | Sobol |
|--------|-----|--------|-------|
| **Type** | Local | Global screening | Global variance-based |
| **Cost** | p × k simulations | r × p simulations | N × (2 + p) simulations |
| **Output** | Elasticity | μ, μ*, σ | S1, ST |
| **Interactions** | No | Indirectly (via σ) | Yes (ST - S1) |
| **Nonlinearity** | Local only | Yes | Yes |
| **Quantitative** | Semi | Semi | Yes |
| **Best for** | Initial screening, ranking | Screening many params | Detailed analysis |

### Typical Workflow

**Phase 1: Screening (Morris or OAT)**
```python
# Quick screening to identify important parameters
from gas_swelling.analysis.sensitivity import MorrisAnalyzer

analyzer = MorrisAnalyzer(param_ranges, ['swelling'])
results = analyzer.run_morris_analysis(n_trajectories=20)

# Select top parameters for detailed study
important_params = [r.parameter_name for r in results if r.mu_star['swelling'] > 0.5]
```

**Phase 2: Detailed Analysis (Sobol)**
```python
# Detailed Sobol analysis on important parameters only
from gas_swelling.analysis.sensitivity import SobolAnalyzer

# Reduce parameter ranges to important ones
reduced_ranges = [pr for pr in param_ranges if pr.name in important_params]

analyzer = SobolAnalyzer(reduced_ranges, ['swelling'])
results = analyzer.run_sobol_analysis(n_samples=2000)
```

**Phase 3: Visualization and Reporting**
```python
# Create comprehensive visualization package
plot_tornado(...)        # OAT results
plot_morris(...)         # Morris screening
plot_sobol(...)          # Sobol indices
plot_sobol_convergence(...)  # Validate convergence
```

---

## Practical Guidelines

### Setting Parameter Ranges

**DO:**
- Base ranges on experimental uncertainty (e.g., ±20% for well-measured parameters)
- Use literature values for physical bounds
- Consider operating conditions (e.g., temperature range in reactor)
- Include realistic minimum and maximum values

**DON'T:**
- Use unrealistically wide ranges (results lose meaning)
- Ignore physical constraints (e.g., negative temperature)
- Mix parameters with very different uncertainty magnitudes without normalization

**Example:**
```python
# Good: Realistic ranges based on experimental uncertainty
param_ranges = [
    ParameterRange('temperature', 600, 900, nominal_value=800),  # ±200 K
    ParameterRange('dislocation_density', 1e13, 1e15),  # Order of magnitude
    ParameterRange('surface_energy', 0.8, 1.2),  # ±20%
]

# Avoid: Unrealistic ranges
param_ranges = [
    ParameterRange('temperature', 0, 5000),  # Too wide, includes physically impossible
    ParameterRange('dislocation_density', -1e14, 1e16),  # Negative values unphysical
]
```

### Sample Size Selection

**OAT:** Use k=2-5 variations per parameter (e.g., -10%, +10%, -20%, +20%)

**Morris:**
- Initial screening: r=10-20 trajectories
- Better statistics: r=25-50 trajectories
- Rule: `r ≥ 10` for reasonable estimates

**Sobol:**
- Minimum: N=500 (for exploratory analysis)
- Recommended: N=1000-2000 (for publication-quality)
- High precision: N=5000+ (for small confidence intervals)

**Rule of thumb:** Start with smaller N, check convergence, increase if needed.

### Computational Efficiency

**1. Parallel execution:**
```python
# Use all CPU cores
results = analyzer.run_sobol_analysis(n_samples=1000, n_jobs=-1)
```

**2. Reduce simulation time:**
```python
# Use shorter time for screening
analyzer = OATAnalyzer(
    param_ranges,
    ['swelling'],
    sim_time=3.6e6,  # 40 days instead of 100
    t_eval_points=50  # Fewer output points
)
```

**3. Select fewer outputs:**
```python
# Analyze only key outputs
analyzer = SobolAnalyzer(param_ranges, ['swelling'])  # Not all 10 variables
```

### Interpreting Results

**Red flags to watch for:**

1. **Very high sensitivity (>10)**: May indicate numerical instability or unrealistic parameter range
2. **All parameters unimportant**: Parameter ranges too narrow or model insensitive
3. **Conflicting results (OAT vs Sobol)**: Strong nonlinearity or interactions present
4. **Large confidence intervals**: Need more samples (Sobol) or trajectories (Morris)

**Best practices:**

1. **Cross-validate**: Compare OAT, Morris, and Sobol results for consistency
2. **Check convergence**: Ensure indices are stable with increasing samples
3. **Physical interpretation**: Results should make physical sense
4. **Document uncertainties**: Report confidence intervals for Sobol indices
5. **Iterate**: Refine parameter ranges based on findings

---

## Advanced Topics

### Multi-Output Sensitivity

Analyze sensitivity for multiple outputs simultaneously:

```python
analyzer = SobolAnalyzer(
    param_ranges,
    output_names=['swelling', 'Rcb', 'gas_release', 'bubble_pressure'],
    sim_time=8.64e6
)

results = analyzer.run_sobol_analysis(n_samples=1000)

# Compare parameter rankings across outputs
for output in ['swelling', 'Rcb', 'gas_release']:
    print(f"\nTop parameters for {output}:")
    sorted_results = sorted(results, key=lambda r: r.S1[output], reverse=True)
    for r in sorted_results[:3]:
        print(f"  {r.parameter_name}: S1 = {r.S1[output]:.3f}")
```

### Time-Dependent Sensitivity

Track how sensitivity evolves over time:

```python
# Extract sensitivity at each time point
analyzer = OATAnalyzer(
    param_ranges,
    ['swelling'],
    sim_time=8.64e6,
    t_eval_points=100  # Multiple time points
)

results = analyzer.run_oat_analysis(percent_variations=[-10, 10])

# Sensitivity vs time plot
times = results[0].time_points  # Time array
elasticities_over_time = []

for i, t in enumerate(times):
    # Extract elasticity at this time point
    elast = [r.sensitivities['swelling']['elasticity'][i] for r in results]
    elasticities_over_time.append(elast)

# Plot sensitivity evolution
import matplotlib.pyplot as plt
elasticities_over_time = np.array(elasticities_over_time)
for i, param_name in enumerate([r.parameter_name for r in results]):
    plt.plot(times/86400, elasticities_over_time[:, i], label=param_name)
plt.xlabel('Time (days)')
plt.ylabel('Elasticity')
plt.legend()
plt.show()
```

### Parameter Correlation

For correlated parameters (e.g., diffusion coefficients with temperature), consider:

1. **Group parameters**: Treat correlated groups as single parameters
2. **Use specialized methods**: Iman-Conover or copula methods for correlation
3. **Physical constraints**: Ensure parameter combinations are physically realistic

### Visualization Best Practices

**1. Tornado plots (OAT):**
- Sort by absolute sensitivity
- Use diverging colors for positive/negative
- Include confidence intervals if available

**2. Morris plots:**
- Label top 10 parameters explicitly
- Use marker size for additional information
- Add quadrant lines for interpretation

**3. Sobol plots:**
- Show both S1 and ST on same plot
- Include error bars (confidence intervals)
- Use stacked bars to show interactions

**4. Heatmaps:**
- Useful for multi-output sensitivity
- Color represents sensitivity magnitude
- Clear parameter vs output matrix

---

## Common Pitfalls and Troubleshooting

### Problem 1: All Parameters Show Low Sensitivity

**Possible causes:**
- Parameter ranges too narrow
- Output variable saturated or insensitive
- Model time too short for effects to manifest

**Solutions:**
- Widen parameter ranges (e.g., ±50% instead of ±10%)
- Check if output is changing at all
- Extend simulation time or analyze different outputs

### Problem 2: Conflicting Results Between Methods

**Example:** OAT shows parameter A is important, Sobol shows it's unimportant.

**Possible causes:**
- Strong parameter interactions (Sobol captures, OAT doesn't)
- Nonlinearity far from nominal point (OAT local, Sobol global)
- Different parameter ranges used

**Solutions:**
- Check ST - S1 in Sobol (large = interactions)
- Examine Morris σ (high = nonlinearity)
- Ensure consistent parameter ranges across methods

### Problem 3: Computationally Expensive

**Problem:** Sobol analysis with 20 parameters takes too long.

**Solutions:**
1. **Screen first with Morris** to reduce parameter set
2. **Use smaller N** for exploratory analysis (N=500)
3. **Parallelize** with `n_jobs=-1`
4. **Reduce simulation time** (shorter irradiation period)
5. **Use surrogate models** (Gaussian processes, polynomial chaos)

```python
# Example workflow for computationally expensive model

# Step 1: Morris screening (fast)
morris_analyzer = MorrisAnalyzer(param_ranges, ['swelling'])
morris_results = morris_analyzer.run_morris_analysis(n_trajectories=20)

# Step 2: Select top 5 parameters
top_params = [r.parameter_name for r in sorted(morris_results, key=lambda x: x.mu_star['swelling'], reverse=True)[:5]]

# Step 3: Sobol on reduced set
reduced_ranges = [pr for pr in param_ranges if pr.name in top_params]
sobol_analyzer = SobolAnalyzer(reduced_ranges, ['swelling'])
sobol_results = sobol_analyzer.run_sobol_analysis(n_samples=2000, n_jobs=-1)
```

### Problem 4: Numerical Instability

**Symptoms:**
- Very high sensitivity values (>100)
- Inconsistent results between runs
- NaN or Inf values

**Solutions:**
- Check for division by zero in output metrics
- Ensure parameter values stay in physical range
- Increase numerical precision in solver
- Use relative changes instead of absolute

---

## Example: Complete Sensitivity Study

This example shows a complete sensitivity analysis workflow combining all three methods:

```python
#!/usr/bin/env python3
"""
Complete Sensitivity Study for Gas Swelling Model
=================================================

This script performs a comprehensive sensitivity analysis using
OAT, Morris, and Sobol methods to identify influential parameters.
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.analysis.sensitivity import (
    OATAnalyzer, MorrisAnalyzer, SobolAnalyzer,
    create_default_parameter_ranges
)
from gas_swelling.analysis.visualization import (
    plot_tornado, plot_morris, plot_sobol
)
from gas_swelling.params import create_default_parameters

# Configuration
SIM_TIME = 8.64e6  # 100 days
OUTPUTS = ['swelling', 'Rcb', 'gas_release']
RANDOM_STATE = 42

print("=" * 70)
print("GAS SWELLING MODEL - COMPLETE SENSITIVITY STUDY")
print("=" * 70)

# Create parameter ranges
param_ranges = create_default_parameter_ranges()
print(f"\nAnalyzing {len(param_ranges)} parameters:")
for pr in param_ranges:
    print(f"  - {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}]")

# =============================================================================
# PHASE 1: OAT Analysis (Local Sensitivity)
# =============================================================================

print("\n" + "=" * 70)
print("PHASE 1: OAT ANALYSIS")
print("=" * 70)

oat_analyzer = OATAnalyzer(
    parameter_ranges=param_ranges,
    output_names=OUTPUTS,
    sim_time=SIM_TIME,
    t_eval_points=100
)

oat_results = oat_analyzer.run_oat_analysis(
    percent_variations=[-10, 10],
    verbose=False
)

# Visualize OAT results
for output in OUTPUTS:
    plot_tornado(
        oat_results,
        output_name=output,
        metric='elasticity',
        title=f'OAT Sensitivity - {output}',
        save_path=f'sensitivity_oat_{output}.png',
        show=False
    )

# Print OAT ranking for swelling
print("\nOAT Parameter Ranking (by |elasticity| for swelling):")
print("-" * 60)
sorted_oat = sorted(
    oat_results,
    key=lambda r: abs(r.sensitivities['swelling']['elasticity']),
    reverse=True
)
for r in sorted_oat:
    elast = r.sensitivities['swelling']['elasticity']
    print(f"  {r.parameter_name:25s}: {elast:8.2f}")

# =============================================================================
# PHASE 2: Morris Screening (Global Sensitivity)
# =============================================================================

print("\n" + "=" * 70)
print("PHASE 2: MORRIS SCREENING")
print("=" * 70)

morris_analyzer = MorrisAnalyzer(
    parameter_ranges=param_ranges,
    output_names=OUTPUTS,
    sim_time=SIM_TIME,
    t_eval_points=100
)

morris_results = morris_analyzer.run_morris_analysis(
    n_trajectories=25,
    random_state=RANDOM_STATE,
    verbose=False
)

# Visualize Morris results
for output in OUTPUTS:
    plot_morris(
        morris_results,
        output_name=output,
        title=f'Morris Screening - {output}',
        save_path=f'sensitivity_morris_{output}.png',
        show=False
    )

# Print Morris statistics for swelling
print("\nMorris Statistics (for swelling):")
print("-" * 60)
print(f"{'Parameter':<25} {'μ*':>10} {'σ':>10} {'Classification':>20}")
print("-" * 60)

for r in sorted(morris_results, key=lambda x: x.mu_star['swelling'], reverse=True):
    mu_star = r.mu_star['swelling']
    sigma = r.sigma['swelling']

    if mu_star > 0.5 and sigma < 0.3:
        classification = "Linear, Important"
    elif mu_star > 0.5 and sigma >= 0.3:
        classification = "Nonlinear/Interacting"
    elif mu_star <= 0.5 and sigma < 0.3:
        classification = "Unimportant"
    else:
        classification = "Interacting"

    print(f"  {r.parameter_name:<25} {mu_star:10.3f} {sigma:10.3f} {classification:>20}")

# =============================================================================
# PHASE 3: Sobol Analysis (Variance-Based Sensitivity)
# =============================================================================

print("\n" + "=" * 70)
print("PHASE 3: SOBOL ANALYSIS")
print("=" * 70)

# Identify important parameters from Morris (μ* > 0.3)
important_params = [
    r.parameter_name for r in morris_results
    if r.mu_star['swelling'] > 0.3
]

print(f"\nRunning Sobol analysis on top {len(important_params)} parameters")
print(f"(Reduced from {len(param_ranges)} total parameters)")

# Create reduced parameter ranges
reduced_ranges = [pr for pr in param_ranges if pr.name in important_params]

sobol_analyzer = SobolAnalyzer(
    parameter_ranges=reduced_ranges,
    output_names=OUTPUTS,
    sim_time=SIM_TIME,
    t_eval_points=100
)

sobol_results = sobol_analyzer.run_sobol_analysis(
    n_samples=1000,
    random_state=RANDOM_STATE,
    n_jobs=-1,  # Parallel execution
    verbose=False
)

# Visualize Sobol results
for output in OUTPUTS:
    plot_sobol(
        sobol_results,
        output_name=output,
        title=f'Sobol Indices - {output}',
        save_path=f'sensitivity_sobol_{output}.png',
        show=False
    )

# Print Sobol indices for swelling
print("\nSobol Sensitivity Indices (for swelling):")
print("-" * 70)
print(f"{'Parameter':<25} {'S1':>10} {'ST':>10} {'ST-S1':>10} {'Type':>15}")
print("-" * 70)

for r in sorted(sobol_results, key=lambda x: x.S1['swelling'], reverse=True):
    S1 = r.S1['swelling']
    ST = r.ST['swelling']
    interaction = ST - S1

    if S1 > 0.1:
        if interaction > 0.05:
            param_type = "Interacting"
        else:
            param_type = "Independent"
    else:
        if ST > 0.1:
            param_type = "Pure interaction"
        else:
            param_type = "Unimportant"

    print(f"  {r.parameter_name:<25} {S1:10.3f} {ST:10.3f} {interaction:10.3f} {param_type:>15}")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("SUMMARY: PARAMETER RANKING")
print("=" * 70)

# Compare rankings across methods
print("\nTop 5 parameters by method:")
print("-" * 60)

# OAT top 5
oat_top5 = [r.parameter_name for r in sorted_oat[:5]]
print(f"OAT:        {', '.join(oat_top5)}")

# Morris top 5
morris_top5 = [
    r.parameter_name for r in sorted(
        morris_results,
        key=lambda x: x.mu_star['swelling'],
        reverse=True
    )[:5]
]
print(f"Morris (μ*): {', '.join(morris_top5)}")

# Sobol top 5
sobol_top5 = [
    r.parameter_name for r in sorted(
        sobol_results,
        key=lambda x: x.S1['swelling'],
        reverse=True
    )[:5]
]
print(f"Sobol (S1):  {', '.join(sobol_top5)}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nResults saved to:")
print("  - sensitivity_oat_*.png")
print("  - sensitivity_morris_*.png")
print("  - sensitivity_sobol_*.png")
```

---

## References and Further Reading

### Method References

**OAT Method:**
- Saltelli, A., et al. (2008). *Global Sensitivity Analysis: The Primer*. Wiley.
- Hamby, D. M. (1994). "A review of techniques for parameter sensitivity analysis of environmental models." *Environmental Monitoring and Assessment*, 32(2), 135-154.

**Morris Method:**
- Morris, M. D. (1991). "Factorial sampling plans for preliminary computational experiments." *Technometrics*, 33(2), 161-174.
- Campolongo, F., et al. (2007). "An effective screening design for sensitivity analysis of large models." *Environmental Modelling & Software*, 22(10), 1509-1518.

**Sobol Method:**
- Sobol, I. M. (2001). "Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates." *Mathematics and Computers in Simulation*, 55(1-3), 271-280.
- Saltelli, A. (2002). "Making best use of model evaluations to compute sensitivity indices." *Computer Physics Communications*, 145(2), 280-297.

### Gas Swelling Model References

- Original theoretical framework: **"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"**
- Model implementation: See `model_design.md` and `CLAUDE.md`

### Python Libraries

This implementation uses:
- **NumPy**: Numerical computations
- **SciPy**: Statistical distributions and sampling
- **Matplotlib**: Visualization
- **SALib**: Sensitivity analysis algorithms (future integration planned)

---

## API Quick Reference

### OATAnalyzer

```python
from gas_swelling.analysis.sensitivity import OATAnalyzer

analyzer = OATAnalyzer(
    parameter_ranges,           # List of ParameterRange objects
    output_names,               # List of outputs to analyze
    sim_time,                   # Simulation time (seconds)
    t_eval_points=100,          # Number of time points
    base_params=None            # Base parameters (default: create_default_parameters())
)

results = analyzer.run_oat_analysis(
    percent_variations=[-10, 10],  # Percentage variations to test
    verbose=True                    # Print progress
)

# Access results
for result in results:
    param_name = result.parameter_name
    elasticity = result.sensitivities['swelling']['elasticity']
```

### MorrisAnalyzer

```python
from gas_swelling.analysis.sensitivity import MorrisAnalyzer

analyzer = MorrisAnalyzer(
    parameter_ranges,
    output_names,
    sim_time,
    t_eval_points=100,
    base_params=None
)

results = analyzer.run_morris_analysis(
    n_trajectories=25,        # Number of trajectories (r)
    random_state=None,        # Random seed
    verbose=True
)

# Access results
for result in results:
    param_name = result.parameter_name
    mu_star = result.mu_star['swelling']
    sigma = result.sigma['swelling']
```

### SobolAnalyzer

```python
from gas_swelling.analysis.sensitivity import SobolAnalyzer

analyzer = SobolAnalyzer(
    parameter_ranges,
    output_names,
    sim_time,
    t_eval_points=100,
    base_params=None
)

results = analyzer.run_sobol_analysis(
    n_samples=1000,           # Base sample size (N)
    random_state=None,
    n_jobs=1,                 # Parallel jobs (-1 = all cores)
    verbose=True
)

# Access results
for result in results:
    param_name = result.parameter_name
    S1 = result.S1['swelling']
    ST = result.ST['swelling']
    S1_conf = result.S1_conf['swelling']
    ST_conf = result.ST_conf['swelling']
```

### Visualization Functions

```python
from gas_swelling.analysis.visualization import (
    plot_tornado,
    plot_morris,
    plot_sobol,
    plot_sobol_convergence
)

# Tornado plot (OAT)
plot_tornado(
    oat_results,
    output_name='swelling',
    metric='elasticity',
    title='OAT Sensitivity',
    save_path='oat.png'
)

# Morris plot
plot_morris(
    morris_results,
    output_name='swelling',
    title='Morris Screening',
    save_path='morris.png'
)

# Sobol bar chart
plot_sobol(
    sobol_results,
    output_name='swelling',
    title='Sobol Indices',
    save_path='sobol.png'
)

# Convergence plot
plot_sobol_convergence(
    sobol_results,
    output_name='swelling',
    title='Sobol Convergence',
    save_path='convergence.png'
)
```

---

## Troubleshooting Guide

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Import error** | `ModuleNotFoundError: No module named 'gas_swelling.analysis'` | Install package: `pip install -e .` |
| **Slow execution** | Analysis takes hours | Reduce `n_samples`, use `n_jobs=-1`, screen parameters first |
| **Memory error** | `MemoryError` or OOM | Reduce `n_samples` or `t_eval_points` |
| **Zero variance** | All sensitivities ~0 | Check parameter ranges, extend simulation time |
| **NaN values** | Results contain NaN | Check solver convergence, ensure physical parameter values |
| **Poor convergence** | Large confidence intervals | Increase `n_samples` for Sobol, `n_trajectories` for Morris |

### Getting Help

1. **Check examples**: Run scripts in `examples/sensitivity_*.py`
2. **Read parameter reference**: `docs/parameter_reference.md`
3. **Review source code**: `gas_swelling/analysis/` for implementation details
4. **Model documentation**: `model_design.md` for physics background

---

**Version**: 1.0.0
**Last Updated**: 2024-01-24
**Authors**: Gas Swelling Model Development Team

---

**📘 Documentation Index** | **[README](../README.md)** | **[Parameter Reference](parameter_reference.md)** | **[Quick Start Tutorial](../examples/quickstart_tutorial.py)** | **[Sensitivity Examples](../examples/)**
