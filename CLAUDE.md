# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a scientific computing project that implements a **Gas Swelling Model** for nuclear fuel materials (U-Zr and U-Pu-Zr alloys). The model simulates fission gas bubble evolution and void swelling behavior in irradiated metallic fuels based on rate theory. The implementation follows the theoretical framework from "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel."

## Core Architecture

### State Vector (10 variables)
The model solves a system of 10 coupled ordinary differential equations (ODEs):

1. **Cgb**: Gas atom concentration in bulk matrix (atoms/m³)
2. **Ccb**: Cavity/bubble concentration in bulk (cavities/m³)
3. **Ncb**: Gas atoms per bulk cavity (atoms/cavity)
4. **cvb**: Vacancy concentration in bulk
5. **cib**: Interstitial concentration in bulk
6. **Cgf**: Gas atom concentration at phase boundaries
7. **Ccf**: Cavity concentration at phase boundaries
8. **Ncf**: Gas atoms per boundary cavity
9. **cvf**: Vacancy concentration at boundaries
10. **cif**: Interstitial concentration at boundaries

### Key Physical Relationships

- **Gas Pressure**: Calculated via ideal gas law or modified Van der Waals EOS (configurable via `eos_model` parameter)
- **Cavity Radius**: Computed from gas atoms per cavity (Nc) using mechanical equilibrium between gas pressure and surface tension
- **Swelling Rate**: Total volume fraction occupied by cavities: `V_bubble = (4/3)πR³ × Cc`
- **Critical Radius**: Distinguishes gas-driven swelling (overpressurized) from bias-driven void growth (underpressurized)

## Common Development Tasks

### Running the Model

```bash
# Run default simulation
python test4_run_rk23.py

# Run temperature sweep study
python test4_run_rk23.py  # (contains temperature_sweep function)
```

### Parameter Configuration

All material and simulation parameters are defined in `parameters.py`:

- **MaterialParameters**: Physical constants (lattice constants, diffusion coefficients, surface energy, dislocation density, etc.)
- **SimulationParameters**: Fission rate, temperature, time stepping, gas production rates

Key parameters frequently modified:
- `temperature`: Operating temperature (K)
- `fission_rate`: Fission density (fissions/m³/s)
- `dislocation_density`: Defect sink strength (m⁻²)
- `surface_energy`: Affects cavity stability (J/m²)
- `Fnb`, `Fnf`: Bubble nucleation factors (bulk and boundary)
- `eos_model`: 'ideal' or 'ronchi' for gas equation of state

### Numerical Solver

The model uses `scipy.integrate.solve_ivp` with the RK23 method:

```python
result = model.solve(
    t_span=(0, sim_time),
    t_eval=time_points
)
```

Returns dictionary with time series of all state variables plus derived quantities (Rcb, Rcf, Pg, swelling, etc.).

## Code Organization

- `modelrk23.py`: Main model class `GasSwellingModel` containing all rate equations and solver logic
- `parameters.py`: Parameter dataclasses and default configuration
- `test4_run_rk23.py`: Test harness with plotting and parameter sweep studies
- `model_design.md`: Theoretical framework documentation (Chinese)
- `original paper of swelling rate theory.md`: Reference paper (English)

## Model Equations (Paper references)

1. **Gas transport** (Eqs. 1-8): Diffusion, nucleation, cavity growth
2. **Defect kinetics** (Eqs. 17-20): Vacancy/interstitial production, recombination, sink annihilation
3. **Cavity growth** (Eq. 14): Bias-driven vacancy influx vs thermal emission
4. **Gas release** (Eqs. 9-12): Interconnectivity threshold and release fraction
5. **Swelling calculation**: Volume fraction of cavities

## Testing and Validation

The model has been validated against:
- U-10Zr fuel swelling data (Fig. 6 in paper)
- U-19Pu-10Zr fuel data (Fig. 7)
- High-purity uranium swelling (Figs. 9-10)

Typical validation metrics:
- Final swelling percent at given burnup
- Bubble radius evolution
- Gas release fraction
- Temperature-dependent swelling peak

## Performance Notes

- The ODE system is stiff due to widely varying timescales (defect recombination vs cavity growth)
- RK23 method chosen for balance of accuracy and speed
- Debug history tracking available for diagnostics (can be disabled for production runs)
- Typical simulation: 100 days of irradiation in ~100 seconds of computation

## Parameter Sensitivity

High-sensitivity parameters (from paper Section 5):
- Dislocation density (ρ): ±40% swelling change
- Dislocation bias (Zi): Affects vacancy supersaturation
- Boundary nucleation factor (Fnf): Controls incubation period
- Temperature: Bell-shaped swelling curve with peak ~700-800K
