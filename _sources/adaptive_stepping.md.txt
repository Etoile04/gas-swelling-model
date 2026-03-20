# Adaptive Time Stepping Guide

This guide explains the adaptive time-stepping algorithm, error control parameters, performance tuning guidelines, and when to use adaptive versus fixed stepping in the Gas Swelling Model.

## Table of Contents

- [Overview](#overview)
- [How Adaptive Stepping Works](#how-adaptive-stepping-works)
  - [Embedded Runge-Kutta Methods](#embedded-runge-kutta-methods)
  - [Error Estimation](#error-estimation)
  - [Step Size Control](#step-size-control)
  - [Algorithm Flow](#algorithm-flow)
- [Error Control Parameters](#error-control-parameters)
  - [Relative Tolerance (rtol)](#relative-tolerance-rtol)
  - [Absolute Tolerance (atol)](#absolute-tolerance-atol)
  - [Minimum Step Size (min_step)](#minimum-step-size-min_step)
  - [Maximum Step Size (max_step)](#maximum-step-size-max_step)
  - [Safety Factor (safety_factor)](#safety-factor-safety_factor)
  - [Integration Method (method)](#integration-method-method)
- [Performance Tuning Guidelines](#performance-tuning-guidelines)
  - [Balancing Accuracy and Speed](#balancing-accuracy-and-speed)
  - [Stiff System Considerations](#stiff-system-considerations)
  - [Recommended Parameter Sets](#recommended-parameter-sets)
  - [Monitoring Performance](#monitoring-performance)
- [Adaptive vs Fixed Stepping](#adaptive-vs-fixed-stepping)
  - [When to Use Adaptive Stepping](#when-to-use-adaptive-stepping)
  - [When to Use Fixed Stepping](#when-to-use-fixed-stepping)
  - [Performance Comparison](#performance-comparison)
  - [Accuracy Comparison](#accuracy-comparison)
- [Usage Examples](#usage-examples)
  - [Basic Adaptive Stepping](#basic-adaptive-stepping)
  - [Custom Tolerances](#custom-tolerances)
  - [Temperature Sweep with Adaptive Stepping](#temperature-sweep-with-adaptive-stepping)
  - [Comparing Adaptive and Fixed](#comparing-adaptive-and-fixed)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Overview

Adaptive time stepping automatically adjusts the integration step size during simulation based on the local truncation error of each step. The solver:

- **Takes smaller steps** during rapid changes (early irradiation, gas release events, temperature transients)
- **Takes larger steps** during quasi-steady periods (stable bubble growth, equilibrium conditions)
- **Maintains accuracy** by keeping estimated errors below user-specified tolerances
- **Optimizes efficiency** by minimizing the number of steps while meeting accuracy requirements

### Key Benefits

1. **Automatic tuning**: No manual trial-and-error to find optimal step sizes
2. **Guaranteed accuracy**: Errors are controlled within specified tolerances
3. **Progress tracking**: Real-time feedback on simulation progress and step sizes
4. **Flexibility**: Works with a wide range of parameter regimes

### Limitations

- For **very stiff systems** (like the gas swelling model), explicit methods (RK23/RK45) may be slower than implicit methods (BDF/LSODA)
- Performance gains are most pronounced for systems with **varying timescales** (fast transients + slow evolution)
- Requires careful **tolerance selection** to balance speed and accuracy

---

## How Adaptive Stepping Works

The adaptive solver uses **embedded Runge-Kutta methods**, which compute two solutions of different orders in a single step. The difference between these solutions provides an estimate of the local truncation error, which is then used to adjust the step size.

### Embedded Runge-Kutta Methods

The solver supports two embedded methods:

#### RK23 (Bogacki-Shampine 2(3))

- **2nd order solution**: Used for error estimation
- **3rd order solution**: Used for advancement (higher accuracy)
- **4 stages**: Requires 4 function evaluations per step
- **FSAL property**: First Same As Last - reduces computational cost
- **Best for**: Moderate accuracy requirements, non-stiff to moderately stiff problems

```python
# Bogacki-Shampine coefficients
k1 = f(t, y)
k2 = f(t + 0.5*dt, y + 0.5*dt*k1)
k3 = f(t + 0.75*dt, y + 0.75*dt*k2)
k4 = f(t + dt, y + dt*(2/9*k1 + 1/3*k2 + 4/9*k3))

# 3rd order solution (advanced)
y_new = y + dt*(7/24*k1 + 1/4*k2 + 1/3*k3 + 1/8*k4)

# 2nd order solution (error estimate)
y_low = y + dt*(2/9*k1 + 1/3*k2 + 4/9*k3)

# Error estimate
error = y_new - y_low
```

#### RK45 (Cash-Karp 4(5))

- **4th order solution**: Used for error estimation
- **5th order solution**: Used for advancement (higher accuracy)
- **6 stages**: Requires 6 function evaluations per step
- **Best for**: High accuracy requirements, smooth solutions

```python
# Cash-Karp coefficients (6 stages)
k1 = f(t, y)
k2 = f(t + 0.2*dt, y + 0.2*dt*k1)
k3 = f(t + 0.3*dt, y + dt*(0.075*k1 + 0.225*k2))
k4 = f(t + 0.6*dt, y + dt*(0.3*k1 - 0.9*k2 + 1.8*k3))
k5 = f(t + dt, y + dt*(-11/54*k1 + 2.5*k2 - 70/27*k3 + 35/27*k4))
k6 = f(t + 0.875*dt, y + dt*(1631/55296*k1 + 175/512*k2 + 575/13824*k3 + 44275/110592*k4 + 253/4096*k5))

# 5th order solution (advanced)
y_new = y + dt*(37/378*k1 + 250/621*k3 + 125/594*k4 + 512/1771*k6)

# 4th order solution (error estimate)
y_low = y + dt*(2825/27648*k1 + 18575/48384*k3 + 13525/55296*k4 + 277/14336*k5 + 0.25*k6)

# Error estimate
error = y_new - y_low
```

### Error Estimation

The error estimate is computed as a weighted norm using both relative and absolute tolerances:

```python
# Scale for each state variable
scale = atol + rtol * |y|

# Weighted RMS error norm
error_norm = sqrt(mean((error / scale)^2))
```

- **If error_norm ≤ 1**: Step is **accepted**
- **If error_norm > 1**: Step is **rejected** and retried with smaller step size

### Step Size Control

The step size is adjusted based on the error estimate:

```python
# Compute step size adjustment factor
if error_norm == 0:
    factor = 2.0  # No error, increase step size
elif error_norm < 1.0:
    # Error acceptable, modestly increase step size
    factor = safety_factor * (1.0 / error_norm) ^ exponent
else:
    # Error too large, decrease step size
    factor = safety_factor * (1.0 / error_norm) ^ exponent

# Limit step size changes (factor ∈ [0.1, 5.0])
factor = clip(factor, 0.1, 5.0)

# Compute new step size
dt_new = dt * factor

# Constrain to allowable range
dt_new = clip(dt_new, min_step, max_step)
```

Where:
- **exponent** = 0.5 for RK23 (optimal for 2nd/3rd order methods)
- **exponent** = 0.2 for RK45 (optimal for 4th/5th order methods)
- **safety_factor** = 0.9 (default) provides conservative step changes

### Algorithm Flow

```
1. Initialize: t = t_start, y = y0, estimate initial step size
2. While t < t_end and steps < max_steps:
   a. Perform RK23 or RK45 step → (y_new, error_estimate)
   b. Compute error_norm = weighted_norm(error_estimate, y)
   c. If error_norm ≤ 1.0:
      - Accept step: t += dt, y = y_new
      - Increment n_accepted
      - Print progress if needed
   d. Else:
      - Reject step: keep t, y unchanged
      - Increment n_rejected
      - Log warning periodically
   e. Adjust step size: dt = adjust_step_size(dt, error_norm)
   f. Increment n_steps
3. Interpolate results to user-requested t_eval points
4. Return solution with statistics
```

---

## Error Control Parameters

### Relative Tolerance (rtol)

- **Type**: `float`
- **Default**: `1e-4` (0.01%)
- **Description**: Desired relative accuracy for each state variable
- **Physical Meaning**: Error relative to the current magnitude of each variable
- **Equation**: `error_i ≤ rtol × |y_i| + atol`
- **Typical Range**: 1e-6 to 1e-3

#### Impact on Simulation

| rtol | Accuracy | Speed | Step Size | Use Case |
|------|----------|-------|-----------|----------|
| 1e-6 | Very high | Slow | Small | Final validation, publication-quality results |
| 1e-5 | High | Moderate | Moderate | Detailed studies, sensitivity analysis |
| 1e-4 | Medium | Fast | Moderate | Default, exploratory studies |
| 1e-3 | Low | Very fast | Large | Quick parameter sweeps, screening |

#### Recommendations

- **Start with rtol=1e-4** for exploratory studies
- **Use rtol=1e-5 to 1e-6** for final results and publications
- **Use rtol=1e-3** for quick parameter sweeps

### Absolute Tolerance (atol)

- **Type**: `float`
- **Default**: `1e-6`
- **Description**: Absolute error tolerance for near-zero state variables
- **Physical Meaning**: Minimum acceptable error when y ≈ 0
- **Equation**: `error_i ≤ rtol × |y_i| + atol`
- **Typical Range**: 1e-9 to 1e-5

#### Why Both Tolerances?

The combined error criterion handles two regimes:

1. **Large values**: `rtol × |y|` dominates (relative error)
2. **Near zero**: `atol` dominates (absolute error)

```python
# Example: For variables ranging from 1e-10 to 1e-5
scale = atol + rtol * |y|
# When y = 1e-10: scale ≈ atol = 1e-6 (absolute tolerance)
# When y = 1e-5:  scale ≈ rtol * y = 1e-9 (relative tolerance)
```

#### Recommendations

- **Set atol to 10-100× smaller than your smallest meaningful value**
- For gas concentrations (typically 1e-5 to 1e20 atoms/m³), use atol=1e-6 to 1e-9
- **Keep atol proportional to rtol** for consistent error control across scales

### Minimum Step Size (min_step)

- **Type**: `float`
- **Default**: `1e-12` s
- **Description**: Minimum allowed step size
- **Physical Meaning**: Prevents numerical instability from excessively small steps
- **Typical Range**: 1e-15 to 1e-9 s

#### When min_step Matters

- **Prevents infinite loops**: If the system is too stiff, the solver keeps reducing step size
- **Numerical precision**: Steps below ~1e-15 s suffer from floating-point round-off
- **Timescale limits**: Physical processes have minimum timescales (e.g., atomic vibrations ~1e-13 s)

#### Recommendations

- **Default (1e-12 s)** works for most cases
- **Increase to 1e-10 or 1e-9 s** for stiff systems to avoid getting stuck
- **Decrease to 1e-15 s** only if studying ultra-fast transients

### Maximum Step Size (max_step)

- **Type**: `float`
- **Default**: `100.0` s
- **Description**: Maximum allowed step size
- **Physical Meaning**: Prevents overshooting rapid transients
- **Typical Range**: 0.1 to 10,000 s

#### When max_step Matters

- **Accuracy during transients**: Limits step size during gas release events
- **Output resolution**: Affects how well rapid changes are resolved
- **Stability**: Large steps can cause instability in stiff systems

#### Recommendations

```python
# For short simulations (< 1 day):
max_step = sim_time / 1000  # At least 1000 steps

# For long simulations (> 100 days):
max_step = sim_time / 10000  # At least 10000 steps

# For studies with rapid transients:
max_step = 1.0  # Keep steps small
```

### Safety Factor (safety_factor)

- **Type**: `float`
- **Default**: `0.9`
- **Description**: Conservative multiplier for step size adjustment
- **Range**: (0, 1), typically 0.8 - 0.95
- **Physical Meaning**: Reduces risk of step rejection by being conservative

#### How It Works

```python
factor = safety_factor * (1.0 / error_norm) ^ exponent

# With safety_factor = 0.9:
# If error_norm = 0.5: factor = 0.9 * (2.0) ^ 0.5 = 1.27 (modest increase)
# If error_norm = 2.0: factor = 0.9 * (0.5) ^ 0.5 = 0.64 (conservative decrease)
```

#### Recommendations

- **Default (0.9)** is optimal for most problems
- **Increase to 0.95** for faster but less conservative stepping
- **Decrease to 0.8** for very conservative stepping (fewer rejections)

### Integration Method (method)

- **Type**: `str`
- **Options**: `'RK23'` (default) or `'RK45'`
- **Description**: Embedded Runge-Kutta method for error estimation

| Method | Order | Cost | Accuracy | Speed | Best For |
|--------|-------|------|----------|-------|----------|
| RK23 | 2(3) | 4 evals/step | Good | Fast | Default, moderately stiff systems |
| RK45 | 4(5) | 6 evals/step | Excellent | Moderate | High accuracy, smooth solutions |

#### Recommendations

- **Use RK23** for most gas swelling simulations (default)
- **Use RK45** for:
  - High accuracy requirements (rtol < 1e-5)
  - Smooth, non-stiff problems
  - Final validation studies

---

## Performance Tuning Guidelines

### Balancing Accuracy and Speed

The key to effective adaptive stepping is choosing tolerances that are:

1. **Loose enough** to allow efficient large steps
2. **Tight enough** to maintain required accuracy

#### Tuning Strategy

```python
# Step 1: Start with default tolerances
rtol, atol = 1e-4, 1e-6

# Step 2: Run a short test simulation
result = model.solve(t_span=(0, 3600), rtol=rtol, atol=atol)

# Step 3: Check performance
print(f"Steps: {result['n_steps']}, Accepted: {result['n_accepted']}, Rejected: {result['n_rejected']}")

# Step 4: Adjust based on results
if result['n_rejected'] > result['n_accepted'] * 0.1:
    # Too many rejections, tighten tolerances
    rtol *= 0.5
    atol *= 0.5
elif result['n_steps'] < 100:
    # Very few steps, can loosen tolerances
    rtol *= 2.0
    atol *= 2.0

# Step 5: Validate final accuracy by comparing with tighter tolerances
result_tight = model.solve(t_span=(0, 3600), rtol=rtol/10, atol=atol/10)
error = np.max(np.abs(result['y'][-1] - result_tight['y'][-1]))
print(f"Validation error: {error}")
```

### Stiff System Considerations

The gas swelling model is a **very stiff system** with:

- **Fast timescales**: Vacancy-interstitial recombination (~1e-9 s)
- **Slow timescales**: Bubble growth over days (~1e5 s)
- **Timescale ratio**: ~10¹⁴ (extremely stiff!)

#### Implications

1. **Explicit methods (RK23/RK45)** are limited by stability requirements
2. **Implicit methods (BDF/LSODA)** are often faster for stiff systems
3. **Adaptive stepping may not provide speedup** compared to scipy's BDF method

#### Recommendations for Stiff Systems

```python
# For gas swelling model, try these parameter sets:

# Option 1: Conservative (stable but slow)
params = {
    'adaptive_stepping_enabled': True,
    'rtol': 1e-3,
    'atol': 1e-5,
    'min_step': 1e-10,
    'max_step': 1000.0,
    'method': 'RK23'
}

# Option 2: Balanced (default)
params = {
    'adaptive_stepping_enabled': True,
    'rtol': 1e-4,
    'atol': 1e-6,
    'min_step': 1e-12,
    'max_step': 100.0,
    'method': 'RK23'
}

# Option 3: For comparison, use scipy's BDF (often faster for stiff systems)
params = {
    'adaptive_stepping_enabled': False,  # Use scipy's BDF
    'max_time_step': 100.0
}
```

### Recommended Parameter Sets

#### Quick Exploratory Study

```python
params = create_default_parameters()
params.update({
    'adaptive_stepping_enabled': True,
    'rtol': 1e-3,       # Relaxed tolerance
    'atol': 1e-5,       # Relaxed tolerance
    'min_step': 1e-10,  # Prevent getting stuck
    'max_step': 1000.0, # Allow large steps
    'method': 'RK23'
})
```

#### Standard Production Run

```python
params = create_default_parameters()
params.update({
    'adaptive_stepping_enabled': True,
    'rtol': 1e-4,       # Default tolerance
    'atol': 1e-6,       # Default tolerance
    'min_step': 1e-12,
    'max_step': 100.0,
    'method': 'RK23'
})
```

#### High Accuracy Validation

```python
params = create_default_parameters()
params.update({
    'adaptive_stepping_enabled': True,
    'rtol': 1e-6,       # Tight tolerance
    'atol': 1e-9,       # Tight tolerance
    'min_step': 1e-14,  # Allow very small steps
    'max_step': 10.0,   # Keep steps moderate
    'method': 'RK45'    # Higher order method
})
```

#### Parameter Sweep (Fast)

```python
params = create_default_parameters()
params.update({
    'adaptive_stepping_enabled': True,
    'rtol': 1e-3,       # Very relaxed
    'atol': 1e-4,       # Very relaxed
    'min_step': 1e-9,   # Aggressive
    'max_step': 10000.0 # Very aggressive
})
```

### Monitoring Performance

Enable progress tracking and statistics:

```python
params = create_default_parameters()
params.update({
    'adaptive_stepping_enabled': True,
    'show_progress': True,
    'progress_interval': 100  # Print every 100 accepted steps
})

result = model.solve(t_span=(0, sim_time))

# Check solver statistics
print(f"Total steps: {result['n_steps']}")
print(f"Accepted: {result['n_accepted']}")
print(f"Rejected: {result['n_rejected']}")
print(f"Acceptance rate: {result['n_accepted'] / result['n_steps'] * 100:.1f}%")

# Performance indicators:
# - Acceptance rate > 80%: Well-tuned
# - Acceptance rate 50-80%: Acceptable
# - Acceptance rate < 50%: Consider tightening min_step
```

---

## Adaptive vs Fixed Stepping

### When to Use Adaptive Stepping

✅ **Use adaptive stepping when:**

1. **Exploring new parameter regimes** - No prior knowledge of appropriate step sizes
2. **Systems with varying timescales** - Fast transients + slow evolution
3. **Automatic error control needed** - Want guaranteed accuracy
4. **Parameter sweeps** - Different parameters require different optimal step sizes
5. **Gas release events** - Rapid changes during interconnection
6. **Temperature changes** - Transients during temperature ramps

✅ **Benefits:**

- Automatic tuning - no manual trial-and-error
- Guaranteed accuracy within tolerances
- Real-time progress feedback
- Works across wide range of conditions

### When to Use Fixed Stepping

✅ **Use fixed stepping (scipy's BDF/LSODA) when:**

1. **Very stiff systems** - Gas swelling model is extremely stiff
2. **Benchmarking** - Need consistent, reproducible results
3. **Known optimal step size** - From prior experience
4. **Performance critical** - Scipy's BDF is optimized for stiff systems
5. **Simple dynamics** - No rapid transients or regime changes

✅ **Benefits:**

- **Faster for stiff systems** - BDF method uses Newton iteration
- **Well-tested** - Scipy's solvers are mature and robust
- **Predictable performance** - Consistent step sizes
- **Lower overhead** - No step rejection/retry

### Performance Comparison

Benchmark results for 1-hour simulation (3600 s) at 773 K:

| Method | Time (s) | Steps | Speedup |
|--------|----------|-------|---------|
| Fixed (BDF) | 0.04 | ~100 | 1.0x (baseline) |
| Adaptive (RK23, rtol=1e-4) | 177 | ~10,000 | 0.00x (slower) |
| Adaptive (RK23, rtol=1e-3) | 95 | ~5,000 | 0.00x (slower) |

**Key Insight**: For the gas swelling model (very stiff system), scipy's BDF method is **significantly faster** than explicit RK23 adaptive stepping. This is expected behavior:

- **BDF (implicit)**: Handles stiffness efficiently using Newton iteration
- **RK23 (explicit)**: Limited by stability requirement, requires tiny steps

### Accuracy Comparison

Final swelling values after 1 day (86400 s) at 773 K:

| Method | Swelling (%) | Difference |
|--------|--------------|------------|
| Fixed (BDF) | 0.152 | Baseline |
| Adaptive (RK23, rtol=1e-3) | 0.145 | 4.6% |
| Adaptive (RK23, rtol=1e-4) | 0.149 | 1.9% |
| Adaptive (RK23, rtol=1e-5) | 0.151 | 0.7% |

**Key Insight**: Adaptive stepping produces results within **same order of magnitude** as fixed stepping. For stiff systems, small differences (<5%) are acceptable and reflect different numerical approaches.

### Decision Flowchart

```
Start
  │
  ├─ Is system very stiff? (timescale ratio > 10⁶)
  │   ├─ Yes → Use fixed stepping (BDF)
  │   └─ No  → Continue
  │
  ├─ Are there rapid transients? (gas release, T changes)
  │   ├─ Yes → Use adaptive stepping
  │   └─ No  → Continue
  │
  ├─ Is automatic tuning needed?
  │   ├─ Yes → Use adaptive stepping
  │   └─ No  → Continue
  │
  ├─ Is performance critical?
  │   ├─ Yes → Use fixed stepping (BDF)
  │   └─ No  → Use adaptive stepping
  │
End
```

---

## Usage Examples

### Basic Adaptive Stepping

```python
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Create parameters with adaptive stepping enabled
params = create_default_parameters()
params['adaptive_stepping_enabled'] = True
params['temperature'] = 773  # 500°C

# Create and run model
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 86400))  # 1 day

# Access results
print(f"Final swelling: {result['swelling'][-1]:.3f}%")
print(f"Steps taken: {result['n_steps']}")
print(f"Accepted: {result['n_accepted']}, Rejected: {result['n_rejected']}")
```

### Custom Tolerances

```python
# High accuracy simulation
params = create_default_parameters()
params.update({
    'adaptive_stepping_enabled': True,
    'rtol': 1e-6,        # Tight relative tolerance
    'atol': 1e-9,        # Tight absolute tolerance
    'min_step': 1e-14,   # Allow very small steps
    'max_step': 10.0,    # Limit maximum step size
    'method': 'RK45'     # Higher order method
})

model = GasSwellingModel(params)
result = model.solve(t_span=(0, 86400*100))  # 100 days
```

### Temperature Sweep with Adaptive Stepping

```python
temperatures = [600, 700, 800, 900, 1000]  # K
results = []

for T in temperatures:
    params = create_default_parameters()
    params.update({
        'adaptive_stepping_enabled': True,
        'temperature': T,
        'rtol': 1e-4,
        'atol': 1e-6,
        'show_progress': True
    })

    model = GasSwellingModel(params)
    result = model.solve(t_span=(0, 86400*100))  # 100 days
    results.append(result)

    print(f"T = {T} K, Final swelling = {result['swelling'][-1]:.3f}%")

# Plot results
import matplotlib.pyplot as plt
swelling = [r['swelling'][-1] for r in results]
plt.plot(temperatures, swelling, 'o-')
plt.xlabel('Temperature (K)')
plt.ylabel('Swelling (%)')
plt.title('Temperature Dependence of Swelling')
plt.show()
```

### Comparing Adaptive and Fixed

```python
import time

# Fixed stepping (BDF)
params_fixed = create_default_parameters()
params_fixed['adaptive_stepping_enabled'] = False
model_fixed = GasSwellingModel(params_fixed)

t0 = time.time()
result_fixed = model_fixed.solve(t_span=(0, 86400))
time_fixed = time.time() - t0

# Adaptive stepping (RK23)
params_adaptive = create_default_parameters()
params_adaptive.update({
    'adaptive_stepping_enabled': True,
    'rtol': 1e-4,
    'atol': 1e-6,
    'show_progress': False
})
model_adaptive = GasSwellingModel(params_adaptive)

t0 = time.time()
result_adaptive = model_adaptive.solve(t_span=(0, 86400))
time_adaptive = time.time() - t0

# Compare
print(f"Fixed stepping: {time_fixed:.2f}s, {result_fixed['swelling'][-1]:.4f}%")
print(f"Adaptive: {time_adaptive:.2f}s, {result_adaptive['swelling'][-1]:.4f}%")
print(f"Speedup: {time_fixed/time_adaptive:.2f}x")
print(f"Accuracy difference: {abs(result_fixed['swelling'][-1] - result_adaptive['swelling'][-1]):.4f}%")
```

---

## Troubleshooting

### Problem: Too Many Rejected Steps

**Symptoms**: High rejection rate (>30%), slow simulation

**Solutions**:
1. **Tighten tolerances**: Reduce rtol and atol
2. **Increase min_step**: Prevent excessive step reduction
3. **Reduce safety_factor**: Use 0.8 instead of 0.9

```python
params.update({
    'rtol': 1e-5,        # Tighter (was 1e-4)
    'atol': 1e-8,        # Tighter (was 1e-6)
    'min_step': 1e-10,   # Larger (was 1e-12)
    'safety_factor': 0.8 # More conservative (was 0.9)
})
```

### Problem: Simulation Gets Stuck

**Symptoms**: Step size reduces to min_step and stays there, simulation never completes

**Solutions**:
1. **Increase min_step**: Allow larger minimum steps
2. **Switch to fixed stepping**: Use scipy's BDF method
3. **Check parameter values**: Ensure physical parameters are reasonable

```python
# Option 1: Increase min_step
params['min_step'] = 1e-9  # Was 1e-12

# Option 2: Switch to fixed stepping
params['adaptive_stepping_enabled'] = False
```

### Problem: Poor Accuracy

**Symptoms**: Results don't match expected values or vary significantly with tolerances

**Solutions**:
1. **Tighten tolerances**: Use rtol=1e-6 or tighter
2. **Use RK45 method**: Higher order accuracy
3. **Validate against fixed stepping**: Compare with BDF results

```python
params.update({
    'rtol': 1e-6,        # Much tighter
    'atol': 1e-9,        # Much tighter
    'method': 'RK45'     # Higher order
})
```

### Problem: Slow Performance

**Symptoms**: Simulation takes much longer than fixed stepping

**Solutions**:
1. **Loosen tolerances**: Use rtol=1e-3
2. **Increase max_step**: Allow larger steps
3. **Use fixed stepping**: BDF is faster for stiff systems

```python
# Option 1: Looser tolerances
params.update({
    'rtol': 1e-3,
    'atol': 1e-5,
    'max_step': 1000.0
})

# Option 2: Use fixed stepping (recommended for stiff systems)
params['adaptive_stepping_enabled'] = False
```

---

## References

### Numerical Methods

1. **Hairer, Nørsett, Wanner** (1993). *Solving Ordinary Differential Equations I: Nonstiff Problems*. Springer.
   - Chapter II.4: Embedded Runge-Kutta Methods

2. **Hairer, Wanner** (1996). *Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems*. Springer.
   - Chapter IV.6: BDF Methods

3. **Bogacki, Shampine** (1989). "An Efficient Runge-Kutta (4,5) Pair". *SIAM J. Numer. Anal.*, 26(3).

4. **Cash, Karp** (1990). "A Variable Order Runge-Kutta Method for Initial Value Problems with Rapidly Varying Right-Hand Sides". *ACM TOMS*, 16(3).

### Adaptive Stepping Theory

5. **Söderlind** (2002). "Automatic Control and Adaptive Time-Stepping". *Numerical Algorithms*, 31.
   - Stability and efficiency of adaptive step size control

6. **Gustafsson** (1991). "Control Theoretic Techniques for Step Size Selection in Explicit Runge-Kutta Methods". *ACM TOMS*, 17(4).

### Gas Swelling Model

7. Rest, J. "A model for the fission-gas-driven swelling of metallic fuels." *J. Nucl. Mater.* (1992).

8. Original theoretical paper: "Kinetics of fission-gas-bubble-nucleated void swelling"

---

## Related Documentation

- [Parameter Reference Guide](./parameter_reference.md) - All model parameters and their meanings
- Model theory: see repo-root `model_design.md`
- [Adaptive Stepping Demo](../examples/adaptive_stepping_demo.py) - Interactive demonstration
- Installation guide: see repo-root `INSTALL.md`

---

*For questions or issues, please refer to the [GitHub repository](https://github.com/Etoile04/gas-swelling-model) or contact the development team.*
