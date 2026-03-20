# ODE Module

The `ode` module implements the complete system of ordinary differential equations (ODEs) that describe gas swelling evolution in irradiated nuclear fuel materials. This is the core mathematical model that couples all physical processes.

## Overview

The ODE module translates physical rate laws (from the `physics` module) into a system of coupled differential equations suitable for numerical integration. It provides the right-hand side (RHS) function that numerical solvers use to advance the system state in time.

**Key Characteristics:**
- **17 state variables** tracking gas, cavities, and point defects
- **Two spatial domains**: Bulk matrix and phase boundaries (grain boundaries)
- **Coupled processes**: Gas transport, defect kinetics, cavity growth
- **Adaptive sink strengths**: Defect sinks evolve with cavity sizes

## State Variables (17 Components)

The ODE system tracks these state variables:

### Bulk Matrix (Variables 0-4)
0. **`Cgb`** - Gas atom concentration in bulk (atoms/m³)
1. **`Ccb`** - Cavity/bubble concentration in bulk (cavities/m³)
2. **`Ncb`** - Gas atoms per bulk cavity (atoms/cavity)
3. **`Rcb`** - Bulk cavity radius (m)
4. **`Cgf`** - Gas atom concentration at grain boundaries (atoms/m³)

### Phase Boundaries (Variables 5-7)
5. **`Ccf`** - Cavity concentration at boundaries (cavities/m³)
6. **`Ncf`** - Gas atoms per boundary cavity (atoms/cavity)
7. **`Rcf`** - Boundary cavity radius (m)

### Point Defects (Variables 8-11)
8. **`cvb`** - Bulk vacancy concentration (dimensionless)
9. **`cib`** - Bulk interstitial concentration (dimensionless)
10. **`cvf`** - Boundary vacancy concentration (dimensionless)
11. **`cif`** - Boundary interstitial concentration (dimensionless)

### Tracking Variables (Variables 12-16)
12. **`released_gas`** - Cumulative released gas fraction (dimensionless)
13. **`kvb`** - Bulk vacancy sink strength (m⁻²)
14. **`kib`** - Bulk interstitial sink strength (m⁻²)
15. **`kvf`** - Boundary vacancy sink strength (m⁻²)
16. **`kif`** - Boundary interstitial sink strength (m⁻²)

## Module Components

### Main Function: `swelling_ode_system()`

**Signature:**
```python
def swelling_ode_system(
    t: float,
    y: np.ndarray,
    params: MaterialParameters | SimulationParameters,
    debug_history: Optional[DebugHistory] = None
) -> np.ndarray
```

**Parameters:**
- `t` - Current time (s)
- `y` - State vector (17 elements)
- `params` - Material and simulation parameters
- `debug_history` - Optional debug logging

**Returns:**
- `dydt` - Time derivatives of all 17 state variables

**Example Usage:**
```python
from gas_swelling.ode import swelling_ode_system
from gas_swelling.params import create_default_parameters
import numpy as np

# Setup
params = create_default_parameters()
y0 = params.initial_state  # Initial conditions (17 elements)

# Calculate derivatives at t=0
dydt = swelling_ode_system(0, y0, params)

# Individual component rates
print(f"dCgb/dt = {dydt[0]:.3e} atoms/m³/s")
print(f"dRcb/dt = {dydt[3]:.3e} m/s")
```

## Helper Functions

### 1. `calculate_sink_strengths()`

Calculates defect sink strengths from cavity microstructure:

```python
kvb, kib, kvf, kif = calculate_sink_strengths(
    Rcb=Rcb,          # Bulk cavity radius
    Rcf=Rcf,          # Boundary cavity radius
    Ccb=Ccb,          # Bulk cavity density
    Ccf=Ccf,          # Boundary cavity density
    dislocation_density=params.dislocation_density,
    grain_size=params.grain_size
)
```

**Physical Meaning:**
- Sink strength quantifies how effectively microstructure features absorb point defects
- Higher cavity density/radius → stronger sinks
- Dislocations are strong biased sinks for interstitials

### 2. `calculate_point_defect_derivatives()`

Computes vacancy and interstitial concentration rates:

```python
d_cvb, d_cib, d_cvf, d_cif = calculate_point_defect_derivatives(
    cvb, cib, cvf, cif,  # Current concentrations
    kvb, kib, kvf, kif,  # Sink strengths
    params               # Material parameters
)
```

**Rate Processes:**
- **Production**: Fission creates vacancy-interstitial pairs
- **Recombination**: Vacancies and interstitials annihilate each other
- **Sink Annihilation**: Defects absorbed by dislocations, cavities, grain boundaries

**Mathematical Form:**
```
dCv/dt = Production - Recombination - Sink_annihilation
dCi/dt = Production - Recombination - Sink_annihilation
```

### 3. `calculate_cavity_radius_derivatives()`

Computes cavity growth rates based on gas pressure and defect fluxes:

```python
d_Rcb, d_Rcf = calculate_cavity_radius_derivatives(
    Rcb, Rcf,          # Current radii
    Ncb, Ncf,          # Gas atoms per cavity
    Ccb, Ccf,          # Cavity concentrations
    cvb, cib, cvf, cif,  # Point defect concentrations
    kvb, kib, kvf, kif,  # Sink strengths
    temperature,
    params
)
```

**Growth Mechanisms:**
- **Vacancy absorption** → Cavity grows (R increases)
- **Interstitial absorption** → Cavity shrinks (R decreases)
- **Thermal emission** → Vacancy emission from cavity surface
- **Gas pressure** → Mechanical equilibrium with surface tension

**Critical Radius:**
- **R < R_critical**: Overpressurized, gas-driven growth
- **R > R_critical**: Underpressurized, bias-driven void growth

### 4. `calculate_gas_concentration_derivatives()`

Computes gas concentration evolution:

```python
d_Cgb, d_Cgf, d_Ccb, d_Ncb, d_Ccf, d_Ncf, d_released = \
    calculate_gas_concentration_derivatives(
        Cgb, Cgf,       # Gas concentrations
        Ccb, Ncb,       # Bulk cavities
        Ccf, Ncf,       # Boundary cavities
        Rcb, Rcf,       # Cavity radii
        cvb, cib,       # Point defects
        params
    )
```

**Gas Balance:**
```
dCg/dt = Production - Nucleation - Absorption + Resolution - Release
```

## Physical Processes Coupled

### 1. Gas Transport Loop
```
Fission → Gas Production → Diffusion → Nucleation/Absorption → Bubble Growth
```

### 2. Defect Kinetics Loop
```
Fission → Frenkel Pairs → Recombination/Sinks → Point Defect Concentrations
```

### 3. Cavity Growth Loop
```
Point Defects + Gas Pressure → Vacancy Flux → Cavity Radius → Sink Strength
```

### 4. Feedback Mechanisms
- **Sink Strength Feedback**: Larger cavities → stronger sinks → affects defect concentrations
- **Gas Pressure Feedback**: More gas atoms → higher pressure → affects critical radius
- **Temperature Coupling**: Affects diffusion, recombination, thermal emission

## Mathematical Structure

The ODE system has the form:

```
dy/dt = f(t, y, params)

where:
y = [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf,
     cvb, cib, cvf, cif, released_gas,
     kvb, kib, kvf, kif]
```

### System Properties

- **Stiff System**: Timescales vary from picoseconds (recombination) to days (cavity growth)
- **Coupled**: All variables interact through nonlinear relationships
- **Mass Conserving**: Total gas + released gas = fission gas produced
- **Physically Bounded**: Concentrations ≥ 0, radii ≥ lattice spacing

## Dependencies

**Internal:**
- `physics` module - Calculates rates (influx, nucleation, pressure, etc.)
- `params` module - Material and simulation parameters

**External:**
- `numpy` - Vectorized array operations
- `typing` - Type hints

## Integration with Solvers

The ODE module provides the RHS function for numerical solvers:

```python
from gas_swelling.solvers import RK23Solver
from gas_swelling.ode import swelling_ode_system

# Create solver with ODE function
solver = RK23Solver(
    ode_func=swelling_ode_system,
    params=params
)

# Solve the system
result = solver.solve(
    t_span=(0, 8.64e6),  # 0 to 100 days
    y0=y0                # Initial conditions
)
```

## Usage in Model

End users typically **don't call the ODE function directly**. Instead, use the high-level model interface:

```python
from gas_swelling import GasSwellingModel

model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))

# Results contain time evolution of all state variables
print(result['Cgb'])   # Gas concentration over time
print(result['Rcb'])   # Bubble radius over time
print(result['cvb'])   # Vacancy concentration over time
```

## Debugging and Diagnostics

The ODE system supports optional debug logging:

```python
from gas_swelling.io import DebugHistory

debug = DebugHistory(enabled=True)

# Run with debug output
dydt = swelling_ode_system(t, y, params, debug_history=debug)

# Inspect intermediate calculations
print(debug.history)
```

This logs:
- Sink strength calculations
- Individual rate terms (nucleation, absorption, resolution)
- Pressure calculations
- Growth regime (gas-driven vs bias-driven)

## Numerical Considerations

### Stiffness
The system is **stiff** due to widely varying timescales:
- **Fast** (~10⁻¹² s): Point defect recombination
- **Medium** (~10⁻⁶ s): Gas atom diffusion
- **Slow** (~10⁵ s): Cavity growth and swelling

**Solution**: Use adaptive step size methods (RK23, BDF, LSODA)

### Initial Conditions
Proper initialization is critical:
```python
# Initial thermal equilibrium
cv0 = thermal.calculate_cv0(temperature, params)
ci0 = thermal.calculate_ci0(temperature, params)

# No cavities initially
Ccb0 = 0
Ncb0 = 0
```

### Conservation Laws
The solver should verify:
1. **Gas mass balance**: Total gas = fission gas produced - released gas
2. **Non-negative concentrations**: All state variables ≥ 0
3. **Physical bounds**: Cavity radii ≥ atomic radius

## Testing

Unit tests for ODE system:
```bash
pytest tests/ode/test_rate_equations.py
```

Test coverage:
- Individual component derivatives
- Mass conservation checks
- Steady-state solutions
- Coupling between variables

## Mathematical References

The ODE system implements rate theory from:

- **Eqs. 1-8**: Gas transport and bubble nucleation
- **Eq. 14**: Cavity growth kinetics
- **Eqs. 17-20**: Point defect kinetics
- **Eqs. 21-24**: Sink strength calculations

See `model_design.md` for complete derivations.

## Future Extensions

Potential improvements to the ODE module:
- **Anisotropic swelling**: Direction-dependent cavity growth
- **Multiple bubble populations**: Size distribution instead of mean-field
- **Grain boundary migration**: Moving boundary conditions
- **Temperature transients**: Time-dependent temperature profiles
- **Mechanical coupling**: Stress effects on diffusion and growth

---

**For physics calculations, see:** `../physics/README.md`
**For numerical solvers, see:** `../solvers/README.md`
**For parameter definitions, see:** `gas_swelling/params/parameters.py`
