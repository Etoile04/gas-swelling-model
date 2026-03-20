# Physics Module

The `physics` module provides fundamental physics calculations for gas behavior in nuclear fuel materials. This module implements the thermodynamic and kinetic relationships that govern fission gas evolution in irradiated metallic fuels.

## Overview

This module contains pure physics calculations without numerical solver dependencies. All functions are stateless and operate on input parameters to return physical quantities. The module is organized into three main components:

1. **Gas Pressure** (`pressure.py`) - Equation of state calculations
2. **Gas Transport** (`gas_transport.py`) - Gas transport kinetics and rates
3. **Thermal** (`thermal.py`) - Thermal equilibrium calculations

## Module Components

### 1. Gas Pressure (`pressure.py`)

Calculates gas pressure inside cavities/bubbles using different equations of state:

**Available EOS Models:**
- `calculate_ideal_gas_pressure()` - Ideal gas law P = nRT/V
- `calculate_modified_vdw_pressure()` - Modified Van der Waals EOS
- `calculate_virial_eos_pressure()` - Virial equation of state
- `calculate_ronchi_pressure()` - Ronchi hard sphere model
- `calculate_gas_pressure()` - Unified interface (selects via `eos_model` parameter)

**Example Usage:**
```python
from gas_swelling.physics import calculate_gas_pressure

# Calculate pressure using ideal gas law
P = calculate_ideal_gas_pressure(
    Rc=1e-9,           # 1 nm cavity radius
    Nc=100,            # 100 gas atoms per cavity
    temperature=800    # 800 K
)

# Or use unified interface with configuration
P = calculate_gas_pressure(
    Rc=1e-9,
    Nc=100,
    temperature=800,
    eos_model='ronchi',  # Use Ronchi EOS
    kB=1.380649e-23
)
```

### 2. Gas Transport (`gas_transport.py`)

Calculates gas transport rates and kinetic processes:

**Key Functions:**
- `calculate_gas_influx()` - Gas atom influx to cavities
- `calculate_gas_release_rate()` - Gas release from interconnected bubbles
- `calculate_nucleation_rate()` - Bubble nucleation rate
- `calculate_gas_absorption_rate()` - Gas absorption by cavities
- `calculate_gas_resolution_rate()` - Gas resolution back to matrix
- `calculate_gas_production_rate()` - Fission gas production
- `calculate_gas_transport_terms()` - Complete transport calculation

**Physical Processes Modeled:**
1. Gas atom diffusion in bulk matrix
2. Gas atom transport to grain boundaries
3. Bubble nucleation (homogeneous and heterogeneous)
4. Bubble growth by gas absorption
5. Gas resolution from bubble resolution
6. Fission gas production from irradiation
7. Gas release through interconnected bubble network

**Example Usage:**
```python
from gas_swelling.physics import calculate_gas_transport_terms

# Calculate complete gas transport for bulk
transport = calculate_gas_transport_terms(
    Cg=1e24,          # Gas concentration (atoms/m³)
    Cc=1e20,          # Cavity concentration (cavities/m³)
    Nc=50,            # Gas atoms per cavity
    Dg=1e-15,         # Gas diffusion coefficient (m²/s)
    temperature=800,
    params=params     # Material/simulation parameters
)

# Access individual terms
gas_influx = transport['gas_influx']
nucleation = transport['nucleation_rate']
resolution = transport['resolution_rate']
```

### 3. Thermal (`thermal.py`)

Calculates thermal equilibrium point defect concentrations:

**Functions:**
- `calculate_cv0()` - Thermal equilibrium vacancy concentration
- `calculate_ci0()` - Thermal equilibrium interstitial concentration
- `calculate_thermal_equilibrium_concentrations()` - Both concentrations

**Example Usage:**
```python
from gas_swelling.physics import calculate_thermal_equilibrium_concentrations

# Calculate thermal equilibrium at 800 K
cv0, ci0 = calculate_thermal_equilibrium_concentrations(
    temperature=800,
    Ev=1.5 * 1.60218e-19,    # Vacancy formation energy (J)
    Ei=3.0 * 1.60218e-19,    # Interstitial formation energy (J)
    a0=3.5e-10,              # Lattice parameter (m)
    kB=1.380649e-23
)
```

## Physical Models

### Gas Pressure Equations

The module implements multiple equations of state to model gas behavior at different densities and temperatures:

1. **Ideal Gas Law**: Valid at low gas densities
   ```
   P = (3 * Nc * kB * T) / (4 * π * Rc³)
   ```

2. **Modified Van der Waals**: Accounts for finite molecular volume
   ```
   P = kB * T / (v - b) - a * ρ
   ```

3. **Virial EOS**: Higher accuracy for moderate densities
   ```
   P = ρ * kB * T * (1 + B*ρ + C*ρ² + ...)
   ```

4. **Ronchi Model**: Hard sphere model for high-density fission gas
   ```
   P = kB * T * ρ / (1 - η)  # where η = packing fraction
   ```

### Gas Transport Mechanisms

The transport equations account for:

- **Diffusion**: Fick's law with concentration gradients
- **Nucleation**: Classical nucleation theory with critical radius
- **Absorption**: Gas atoms captured by existing bubbles
- **Resolution**: Knock-out of gas atoms back to matrix
- **Release**: Percolation through interconnected bubble network

### Temperature Dependence

All processes include Arrhenius temperature dependence:
```
D = D0 * exp(-Q / (kB * T))
```

## Dependencies

**Internal:**
- Uses `gas_swelling.params` for material parameters

**External:**
- `numpy` - Numerical calculations
- `typing` - Type hints

## Integration with Other Modules

The physics module is used by:
- **`ode` module** - Provides rate expressions for ODE system
- **`models` module** - Physical quantities for model initialization
- **`solvers` module** - Called during integration to compute rates

Data flow:
```
params → physics → ode → solvers → results
```

## Design Principles

1. **Pure Functions**: All functions are deterministic and stateless
2. **Physical Units**: SI units (meters, seconds, Kelvin, Joules)
3. **Type Hints**: Full type annotations for clarity
4. **Documentation**: Detailed docstrings with physical meaning
5. **Testability**: Easy to unit test individual physics relationships

## Mathematical References

The implementations follow these theoretical frameworks:

- Gas pressure: Original paper Eq. 13, Van der Waals theory
- Gas transport: Rate theory (Eqs. 1-8)
- Thermal equilibrium: Statistical mechanics, Arrhenius equations

For complete equations, see `model_design.md` and `original paper of swelling rate theory.md`.

## Usage in Model

The physics module is typically **not used directly** by end users. Instead, it's called internally by the ODE system and model classes:

```python
from gas_swelling import GasSwellingModel

# Physics calculations happen automatically
model = GasSwellingModel(params)
result = model.solve(t_span=(0, 8.64e6))

# Result contains pressure, swelling, etc.
print(result['Pg'])  # Gas pressure (calculated by physics.pressure)
print(result['swelling'])  # Swelling strain
```

## Advanced Usage

For researchers who want to extend or modify physics:

```python
from gas_swelling.physics import pressure

# Define custom EOS
def my_custom_eos(Rc, Nc, temperature, **kwargs):
    # Your implementation here
    return pressure_value

# Use in custom model
from gas_swelling.physics.pressure import calculate_gas_pressure

# Monkey-patch for testing (not recommended for production)
pressure.calculate_gas_pressure = my_custom_eos
```

## Testing

Unit tests for physics calculations are located in:
- `tests/physics/test_pressure.py`
- `tests/physics/test_gas_transport.py`
- `tests/physics/test_thermal.py`

Run tests:
```bash
pytest tests/physics/
```

## Future Extensions

Potential additions to the physics module:
- Additional equations of state (e.g., Peng-Robinson)
- Anisotropic diffusion models
- Temperature-dependent surface energy
- Multi-species gas behavior (Xe + Kr)
- Grain boundary diffusion models

---

**For parameter definitions, see:** `gas_swelling/params/parameters.py`
**For ODE system, see:** `../ode/README.md`
**For solvers, see:** `../solvers/README.md`
