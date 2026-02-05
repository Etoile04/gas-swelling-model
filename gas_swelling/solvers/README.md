# Solvers Module

The `solvers` module provides numerical integration methods for solving the gas swelling ODE system. It wraps SciPy's ODE solvers with a convenient interface tailored for the gas swelling model.

## Overview

The solvers module implements numerical time integration methods that advance the system state from initial conditions through time, solving the coupled ODE system from the `ode` module.

**Key Features:**
- **Adaptive step sizing**: Automatically adjusts time step for accuracy and efficiency
- **Multiple solver methods**: Support for stiff and non-stiff ODE systems
- **Automatic stiffness detection**: LSODA method automatically switches between explicit and implicit methods
- **Flexible output**: Dense output for smooth plotting or specified time points

## Supported Solver Methods

### Available Methods

The RK23Solver now supports multiple scipy solver methods:

| Method | Type | Best For | Speed | Stability |
|--------|------|----------|-------|------------|
| **LSODA** | Auto-switching | **General use (RECOMMENDED)** | Fast | Auto-detects stiffness |
| **RK23** | Explicit | Non-stiff, short simulations | Fastest | Conditionally stable |
| **RK45** | Explicit | Non-stiff, high accuracy | Fast | Conditionally stable |
| **BDF** | Implicit | **Stiff systems** | Medium | Unconditionally stable |
| **Radau** | Implicit | Stiff systems | Slow | Unconditionally stable |

### 1. RK23Solver (Default: LSODA)

**Default Method:** LSODA (Adams/BDF with automatic stiffness detection)

**Characteristics:**
- **Flexible**: Supports all scipy ODE solver methods
- **Auto-detection**: LSODA automatically detects stiffness and switches methods
- **Backward compatible**: Can use RK23 for non-stiff problems
- **Stiff-capable**: Can use BDF/Radau for highly stiff systems

**Method Selection:**
```python
    y0=y0,                      # Initial conditions
    t_eval=None,                # Adaptive output (or specify time points)
    rtol=1e-6,                  # Relative tolerance
    atol=1e-9,                  # Absolute tolerance
    progress_callback=None      # Optional progress monitoring
)

# Access results
time = result['t']              # Time points
solution = result['y']          # State variables (17, n_points)
success = result['success']     # Solver convergence status
message = result['message']     # Status message
```

**Advanced Usage with Progress Tracking:**
```python
def progress_callback(t, y):
    """Called at each solver step"""
    swelling_percent = calculate_swelling_from_state(y) * 100
    print(f"t={t/86400:.1f} days, Swelling={swelling_percent:.2f}%")

result = solver.solve(
    t_span=(0, 8.64e6),
    y0=y0,
    progress_callback=progress_callback
)
```

**Specific Output Times:**
```python
# Output at specific time points (e.g., daily)
t_eval = np.linspace(0, 8.64e6, 101)  # 0, 1, 2, ..., 100 days
result = solver.solve(t_span=(0, 8.64e6), y0=y0, t_eval=t_eval)
```

### 2. EulerSolver

**Method:** Explicit Euler first-order integration

**Characteristics:**
- **Order**: 1st order (fixed step size)
- **Simplicity**: Easy to understand and implement
- **Speed**: Fast per step, but requires small steps for stability
- **Limitation**: Not recommended for production use

**Best For:**
- Educational purposes
- Debugging and validation
- Testing new physics models
- Situations where step-by-step control is needed

**Example Usage:**
```python
from gas_swelling.solvers import EulerSolver

# Create solver with fixed step size
solver = EulerSolver(
    ode_func=swelling_ode_system,
    params=params,
    dt=1.0  # 1 second time step (very small!)
)

# Solve
result = solver.solve(
    t_span=(0, 86400),  # 1 day only (Euler is slow)
    y0=y0
)
```

**Warning:** Euler method requires **extremely small** time steps for stability with stiff systems. Not recommended for simulations longer than a few days.

## Solver Interface

### Constructor Arguments

All solvers accept these common arguments:

```python
solver = RK23Solver(
    ode_func=swelling_ode_system,  # ODE RHS function
    params=params,                   # Material/simulation parameters
    first_step=None,                 # Initial step size (auto if None)
    max_step=inf,                    # Maximum step size
    min_step=0.0,                    # Minimum step size
)
```

### Solve Method

```python
result = solver.solve(
    t_span=(t_start, t_end),  # Time interval
    y0,                        # Initial state vector (17 elements)
    t_eval=None,               # Output times (None = adaptive)
    rtol=1e-6,                 # Relative tolerance (RK23 only)
    atol=1e-9,                 # Absolute tolerance (RK23 only)
    progress_callback=None     # Optional callback function
)
```

### Return Format

The solver returns a dictionary:

```python
result = {
    't': np.ndarray,        # Time points (n_points,)
    'y': np.ndarray,        # State variables (17, n_points)
    'success': bool,        # True if solver converged
    'message': str,         # Solver status message
    'nfev': int,            # Number of function evaluations
    'nsteps': int           # Number of solver steps taken
}
```

## Solver Selection Guide

### When to use RK23Solver (Recommended)
- ✅ Production simulations
- ✅ Long irradiation times (> 1 day)
- ✅ When accuracy matters
- ✅ Stiff systems (widely varying timescales)
- ✅ Adaptive step sizing needed

### When to use EulerSolver (Special Cases)
- ✅ Educational demonstrations
- ✅ Debugging intermediate steps
- ✅ Validating new physics
- ✅ Simple test cases
- ❌ Production simulations (too slow/unstable)

## Numerical Considerations

### Stiffness

The gas swelling ODE system is **stiff** due to:
- **Fast processes**: Point defect recombination (~10⁻¹² s)
- **Slow processes**: Cavity growth (~10⁵ s)
- **Time scale ratio**: ~10¹⁷ (extremely stiff!)

**Impact:** Fixed-step methods (Euler) require impractically small steps. Adaptive methods (RK23) automatically adjust.

### Tolerance Selection

**Relative Tolerance (`rtol`)**:
- **1e-4**: Quick exploratory runs
- **1e-6**: Default, good balance (recommended)
- **1e-8**: High accuracy, slower

**Absolute Tolerance (`atol`)**:
- **1e-9**: Default, suitable for concentration units
- **1e-12**: Very high precision
- **1e-6**: Faster, less accurate

**Rule of thumb:** `atol` should be smaller than smallest physical value you care about.

### Step Size Behavior

**Typical step sizes during simulation:**
- **Initial**: Small (~10⁻⁶ s) - fast transients in defect concentrations
- **Early**: Medium (~10⁻² s) - bubble nucleation phase
- **Middle**: Large (~10² s) - steady growth phase
- **Late**: Variable - depends on gas release events

**Monitoring step sizes:**
```python
# Add callback to track step sizes
steps = []
def track_steps(t, y):
    steps.append(t)

result = solver.solve(
    t_span=(0, 8.64e6),
    y0=y0,
    progress_callback=track_steps
)

# Analyze step size distribution
dt = np.diff(steps)
print(f"Min step: {np.min(dt):.3e} s")
print(f"Max step: {np.max(dt):.3e} s")
print(f"Mean step: {np.mean(dt):.3e} s")
```

## Performance Optimization

### Speed vs Accuracy

**Faster simulations:**
```python
# Relax tolerances (less accurate)
result = solver.solve(
    t_span=(0, 8.64e6),
    y0=y0,
    rtol=1e-4,  # Looser
    atol=1e-7   # Looser
)
```

**More accurate simulations:**
```python
# Tighten tolerances (slower)
result = solver.solve(
    t_span=(0, 8.64e6),
    y0=y0,
    rtol=1e-8,  # Tighter
    atol=1e-12  # Tighter
)
```

### Memory Management

For **very long simulations**, avoid storing all intermediate states:

```python
# BAD: Stores all time steps (can be GB of data)
t_eval = np.linspace(0, 8.64e6, 1000000)
result = solver.solve(t_span=(0, 8.64e6), y0=y0, t_eval=t_eval)

# GOOD: Let solver choose adaptive output
result = solver.solve(t_span=(0, 8.64e6), y0=y0, t_eval=None)

# Or save to disk periodically
```

### Parallel Parameter Sweeps

Run multiple simulations in parallel:

```python
from concurrent.futures import ProcessPoolExecutor

def run_simulation(temperature):
    params = create_default_parameters()
    params.temperature = temperature
    solver = RK23Solver(swelling_ode_system, params)
    result = solver.solve(t_span=(0, 8.64e6), y0=params.initial_state)
    return result

# Run in parallel
temperatures = [700, 750, 800, 850, 900]
with ProcessPoolExecutor() as executor:
    results = list(executor.map(run_simulation, temperatures))
```

## Troubleshooting

### Solver Convergence Issues

**Problem:** Solver fails to converge or takes too long

**Solutions:**
1. **Check initial conditions** - Ensure physically reasonable
2. **Relax tolerances** - Try `rtol=1e-4, atol=1e-7`
3. **Limit step size** - Set `max_step` to prevent overshooting
4. **Check physics** - Ensure all rate calculations return finite values

### Unexpected Results

**Problem:** Results don't match expectations

**Debugging:**
```python
# Enable debug output
from gas_swelling.io import DebugHistory

debug = DebugHistory(enabled=True)

# Run with debug tracking in ODE function
# (Note: modify swelling_ode_system to accept debug_history)

# Inspect debug history
debug.print_summary()
```

### Memory Issues

**Problem:** Running out of memory for long simulations

**Solutions:**
1. **Use adaptive output** (`t_eval=None`)
2. **Reduce output frequency** - specify fewer time points
3. **Process in chunks** - Break simulation into segments
4. **Save to disk** - Stream results to file

## Integration with GasSwellingModel

End users typically use solvers indirectly through the high-level model:

```python
from gas_swelling import GasSwellingModel

# Model handles solver selection automatically
model = GasSwellingModel(params)
result = model.solve(
    t_span=(0, 8.64e6),
    method='RK23',     # Solver choice
    rtol=1e-6,
    atol=1e-9
)

# Result contains processed outputs
print(result['swelling'])  # Swelling strain
print(result['Pg'])        # Gas pressure
```

## Dependencies

**Internal:**
- `ode` module - ODE system function to integrate

**External:**
- `scipy.integrate` - Numerical integration methods
- `numpy` - Array operations
- `typing` - Type hints

## Testing

Unit tests for solvers:
```bash
pytest tests/solvers/test_rk23_solver.py
pytest tests/solvers/test_euler_solver.py
```

Test coverage:
- Convergence to known solutions
- Adaptive step size behavior
- Error tolerance handling
- Comparison between solvers
- Edge cases (zero initial conditions, extreme temperatures)

## Future Extensions

Potential solver additions:
- **BDF Solver**: For highly stiff systems
- **LSODA**: Automatic stiffness detection
- **Implicit Methods**: For extreme stiffness
- **Event Handling**: Stop at specific conditions (e.g., interconnectivity)
- **Sensitivity Analysis**: Parameter gradient calculations

## References

**Numerical Methods:**
- Runge-Kutta methods: Press et al., "Numerical Recipes"
- Stiff systems: Hairer & Wanner, "Solving ODEs I & II"
- SciPy documentation: https://docs.scipy.org/doc/scipy/reference/integrate.html

---

**For ODE system definition, see:** `../ode/README.md`
**For physics calculations, see:** `../physics/README.md`
**For I/O utilities, see:** `../io/README.md`

## Solver Selection Guide (Updated)

### Quick Reference

| Method | Type | Best For | Default |
|--------|------|----------|---------|
| **LSODA** | Auto-switch | **General use (RECOMMENDED)** | ✓ Yes |
| **RK23** | Explicit | Short simulations, non-stiff | No |
| **RK45** | Explicit | Non-stiff, high accuracy | No |
| **BDF** | Implicit | Stiff systems | No |
| **Radau** | Implicit | Highly stiff | No |

### Usage Examples

```python
from gas_swelling.solvers import RK23Solver
from gas_swelling.ode import swelling_ode_system
from gas_swelling.params import create_default_parameters

params = create_default_parameters()

# Create solver with specific method
solver = RK23Solver(
    rate_equations=swelling_ode_system,
    params=params,
    method='LSODA'  # or 'RK23', 'RK45', 'BDF', 'Radau'
)

# Solve
result = solver.solve(
    (0, 8.64e6),              # Time span (0 to 100 days)
    initial_state,             # Initial conditions
    t_eval=np.linspace(0, 8.64e6, 101)  # Output points
)
```

### Recommendations

1. **For most users:** Use `method='LSODA'` (default)
   - Automatically detects stiffness
   - Switches between explicit and implicit methods
   - Best performance for general cases

2. **For short simulations:** Use `method='RK23'` or `method='RK45'`
   - Faster for non-stiff problems
   - Good for testing and debugging

3. **For long simulations:** Use `method='BDF'` or `method='LSODA'`
   - Handles stiffness better
   - Larger time steps possible
   - More stable for stiff systems

### Model Usage

The `GasSwellingModel` and `RefactoredGasSwellingModel` use `LSODA` by default:

```python
from gas_swelling import GasSwellingModel

model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))  # Uses LSODA by default

# Override method if needed
result = model.solve(t_span=(0, 8.64e6), method='BDF')
```

### Stiffness Note

The gas swelling ODE system has **timescale ratio ~10^17**, making it extremely stiff. For simulations longer than a few hours, implicit methods (BDF, LSODA, Radau) are recommended over explicit methods (RK23, RK45).

