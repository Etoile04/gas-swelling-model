# Parameter Reference Guide

This guide provides detailed documentation for all parameters used in the Gas Swelling Model, including their physical meanings, default values, and typical usage ranges.

## Table of Contents

- [Overview](#overview)
- [Material Parameters](#material-parameters)
  - [Lattice & Atomic Properties](#lattice--atomic-properties)
  - [Diffusion Parameters](#diffusion-parameters)
  - [Dislocation Parameters](#dislocation-parameters)
  - [Surface & Nucleation Parameters](#surface--nucleation-parameters)
  - [Xenon Properties](#xenon-properties)
- [Fuel Composition Specific Parameters](#fuel-composition-specific-parameters)
  - [U-10Zr Alloy](#u-10zr-alloy)
  - [U-Pu-Zr Alloy](#u-pu-zr-alloy)
  - [High-Purity Uranium](#high-purity-uranium)
- [Simulation Parameters](#simulation-parameters)
  - [Fission & Irradiation Parameters](#fission--irradiation-parameters)
  - [Temperature & Time](#temperature--time)
  - [Gas Diffusion Parameters](#gas-diffusion-parameters)
  - [Numerical Solver Parameters](#numerical-solver-parameters)
- [Physical Constants](#physical-constants)
- [Parameter Sensitivity Guide](#parameter-sensitivity-guide)
- [Usage Examples](#usage-examples)

---

## Overview

The Gas Swelling Model uses two main parameter classes:

- **`MaterialParameters`**: Physical properties of the nuclear fuel material (U-Zr or U-Pu-Zr alloys)
- **`SimulationParameters`**: Runtime configuration for the simulation (fission rate, temperature, time stepping, etc.)

Parameters are defined in `gas_swelling/params/parameters.py` and can be customized using Python dataclasses.

---

## Material Parameters

The `MaterialParameters` dataclass contains physical properties of the fuel material.

### Lattice & Atomic Properties

#### `lattice_constant`
- **Type**: `float`
- **Default**: `3.4808e-10` m
- **Description**: Crystal lattice constant for uranium-zirconium alloy
- **Physical Meaning**: Distance between adjacent atoms in the crystal lattice
- **Typical Range**: 3.40-3.60 × 10⁻¹⁰ m
- **Notes**: Affects atomic volume calculations

#### `ATOMIC_VOLUME`
- **Type**: `float`
- **Default**: `4.09e-29` m³
- **Description**: Volume occupied by a single uranium atom
- **Physical Meaning**: Fundamental unit volume for defect concentration calculations
- **Typical Range**: 4.0-4.2 × 10⁻²⁹ m³
- **Impact**: Used in converting between atomic and molar units

#### `nu_constant`
- **Type**: `float`
- **Default**: `7.8e12` s⁻¹
- **Description**: Atomic jump frequency (attempt frequency)
- **Physical Meaning**: Number of times per second an atom attempts to jump to a neighboring site
- **Typical Range**: 10¹² - 10¹³ s⁻¹
- **Impact**: Affects diffusion coefficient calculations

### Diffusion Parameters

#### `Dv0`
- **Type**: `float`
- **Default**: `2.0e-8` m²/s
- **Description**: Pre-exponential factor for vacancy diffusion coefficient
- **Physical Meaning**: Diffusion coefficient magnitude at infinite temperature
- **Equation**: Dv = Dv0 × exp(-Evm / kBT)
- **Typical Range**: 10⁻⁸ - 10⁻⁷ m²/s

#### `Evm`
- **Type**: `float`
- **Default**: `0.74` eV
- **Description**: Vacancy migration energy
- **Physical Meaning**: Energy barrier for a vacancy to move to a neighboring site
- **Typical Range**: 0.6 - 1.0 eV
- **Impact**: Higher values reduce vacancy mobility, slowing defect evolution

#### `Evf_coeffs`
- **Type**: `List[float]`
- **Default**: `[1.034, 7.6e-4]`
- **Description**: Temperature-dependent vacancy formation energy coefficients
- **Equation**: Evf(T) = C₀ + C₁ × T (eV)
- **Physical Meaning**: Energy required to create a vacancy (varies with temperature)
- **Typical Range**: 0.8 - 1.2 eV at operating temperatures

#### `Evfmuti`
- **Type**: `float`
- **Default**: `1.0`
- **Description**: Multiplier for vacancy formation energy
- **Physical Meaning**: Adjustment factor for vacancy formation energy
- **Typical Range**: 0.9 - 1.1
- **Notes**: Used for calibration studies

### Dislocation Parameters

#### `Zv`
- **Type**: `float`
- **Default**: `1.0`
- **Description**: Vacancy bias factor for dislocation absorption
- **Physical Meaning**: Relative strength of dislocations as vacancy sinks
- **Typical Range**: 1.0 - 1.02
- **Impact**: Lower than Zi means vacancies are less strongly attracted to dislocations than interstitials

#### `Zi`
- **Type**: `float`
- **Default**: `1.025`
- **Description**: Interstitial bias factor for dislocation absorption
- **Physical Meaning**: Relative strength of dislocations as interstitial sinks
- **Typical Range**: 1.02 - 1.05
- **Impact**: Higher Zᵢ creates vacancy supersaturation, driving void swelling

#### `dislocation_density`
- **Type**: `float`
- **Default**: `7.0e13` m⁻²
- **Description**: Density of dislocations in the material
- **Physical Meaning**: Total line length of dislocations per unit volume
- **Typical Range**: 10¹² - 10¹⁴ m⁻²
  - Annealed material: ~10¹² m⁻²
  - Cold-worked material: ~10¹⁴ m⁻²
- **Impact**: HIGH SENSITIVITY - ±40% swelling change for ±50% density change
- **Sink Strength**: kᵥ = √(Zᵥ × ρ), kᵢ = √(Zᵢ × ρ)

### Surface & Nucleation Parameters

#### `surface_energy`
- **Type**: `float`
- **Default**: `0.5` J/m²
- **Description**: Surface energy (surface tension) of cavity-matrix interface
- **Physical Meaning**: Energy cost per unit area of creating new cavity surface
- **Reference**: Rest, J. Nucl. Mater. 1992
- **Typical Range**: 0.3 - 0.7 J/m²
- **Impact**: Affects critical cavity radius and mechanical equilibrium

#### `Fnb`
- **Type**: `float`
- **Default**: `1e-5`
- **Description**: Bubble nucleation factor in bulk (grain interior)
- **Physical Meaning**: Probability of new cavity formation per unit time
- **Typical Range**: 10⁻⁶ - 10⁻⁴
- **Impact**: Higher values increase number density of bubbles

#### `Fnf`
- **Type**: `float`
- **Default**: `1e-5`
- **Description**: Bubble nucleation factor at phase boundaries
- **Physical Meaning**: Nucleation rate enhancement at grain boundaries and phase interfaces
- **Typical Range**: 10⁻⁶ - 10⁻³
- **Impact**: HIGH SENSITIVITY - Controls incubation period before rapid swelling

#### `hydrastatic_pressure`
- **Type**: `float`
- **Default**: `0.0` Pa
- **Description**: External hydrostatic pressure
- **Physical Meaning**: Compressive pressure applied to the fuel
- **Typical Range**: 0 - 100 MPa
- **Impact**: Higher pressure suppresses cavity growth

#### `recombination_radius`
- **Type**: `float`
- **Default**: `2.0e-10` m
- **Description**: Capture radius for vacancy-interstitial recombination
- **Physical Meaning**: Distance within which vacancies and interstitials annihilate each other
- **Typical Range**: 1.5 - 3.0 × 10⁻¹⁰ m
- **Impact**: Larger values increase recombination rate, reducing swelling

### Interstitial (SIA) Parameters

#### `Di0`
- **Type**: `float`
- **Default**: `1.259e-12` m²/s
- **Description**: Pre-exponential factor for self-interstitial atom (SIA) diffusion
- **Physical Meaning**: SIA diffusion coefficient at infinite temperature
- **Equation**: Di = Di0 × exp(-Eim / kBT)
- **Typical Range**: 10⁻¹³ - 10⁻¹¹ m²/s
- **Notes**: SIA diffusion is typically 10⁴ - 10⁶ times faster than vacancy diffusion

#### `Eim`
- **Type**: `float`
- **Default**: `1.18` eV
- **Description**: SIA migration energy
- **Physical Meaning**: Energy barrier for an interstitial to move to a neighboring site
- **Typical Range**: 0.1 - 0.5 eV (typically much lower than Evm)
- **Impact**: SIAs are highly mobile due to low migration energy

#### `Eif_coeffs`
- **Type**: `List[float]`
- **Default**: `[-3.992, 0.038, -7.645e-5, 5.213e-8]`
- **Description**: Temperature-dependent SIA formation energy coefficients
- **Equation**: Eif(T) = C₀ + C₁T + C₂T² + C₃T³ (eV)
- **Physical Meaning**: Energy required to create a self-interstitial
- **Notes**: Can be negative due to lattice relaxation effects

### Xenon Properties

Xenon (Xe) is the primary fission gas responsible for swelling.

#### `Xe_radii`
- **Type**: `float`
- **Default**: `2.16e-10` m
- **Description**: Xenon atomic radius
- **Physical Meaning**: Size of Xe atom for volume calculations

#### `xe_epsilon_k`
- **Type**: `float`
- **Default**: `290.0` K
- **Description**: Lennard-Jones potential well depth for Xe-Xe interactions
- **Physical Meaning**: Strength of attractive interaction between Xe atoms
- **Used In**: Van der Waals equation of state (ronchi model)

#### `xe_sigma`
- **Type**: `float`
- **Default**: `3.86e-10` m
- **Description**: Lennard-Jones collision diameter for Xe
- **Physical Meaning**: Distance at which Xe-Xe potential is zero
- **Used In**: Van der Waals equation of state

#### `xe_mass`
- **Type**: `float`
- **Default**: `0.131293` kg/mol
- **Description**: Molar mass of xenon

#### `xe_Tc`
- **Type**: `float`
- **Default**: `290.0` K
- **Description**: Critical temperature of xenon
- **Used In**: Ronchi equation of state

#### `xe_dc`
- **Type**: `float`
- **Default**: `1.103e3` kg/m³
- **Description**: Critical density of xenon

#### `xe_Vc`
- **Type**: `float`
- **Default**: `35.92e-6` m³/mol
- **Description**: Critical molar volume of xenon

#### `xe_q_coeffs`
- **Type**: `List[float]`
- **Default**: `[2.12748, 0.52905, 0.13053, 0.02697, 0.00313]`
- **Description**: Temperature function coefficients for Ronchi EOS
- **Used In**: f(T) correction factor for equation of state

---

## Fuel Composition Specific Parameters

Different fuel compositions require different parameter values to accurately model swelling behavior. The tables below summarize validated parameter sets for three fuel types studied in the reference paper.

### Parameter Selection Guidance

**Key Differences Between Fuel Types:**

1. **Dislocation Density** - Most significant parameter difference
   - High-purity U: 1×10¹⁵ m⁻² (cold-worked)
   - U-10Zr: 7×10¹³ m⁻² (moderate)
   - U-Pu-Zr: 2×10¹³ m⁻² (lower)

2. **Boundary Nucleation Factor** (`Fnf`)
   - High-purity U: 1.0 (very high - causes rapid swelling)
   - Alloys: 1×10⁻⁵ (much lower)

3. **Peak Swelling Temperature**
   - Varies by composition: 673-750 K
   - Affects swelling magnitude significantly

### U-10Zr Alloy

Uranium-10% Zirconium alloy fuel (most common metallic fuel composition).

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| **Dislocation Density** | 7.0×10¹³ | m⁻² | Moderate dislocation density |
| **Peak Temperature** | 700 | K | Temperature of maximum swelling |
| **Swelling Range** | 0.2-3.0 | % | At 0.4-0.9 at.% burnup |
| **Bulk Nucleation Factor** (`Fnb`) | 1×10⁻⁵ | - | Bubble nucleation in grain interior |
| **Boundary Nucleation Factor** (`Fnf`) | 1×10⁻⁵ | - | Nucleation at phase boundaries |
| **Vacancy Formation Energy** | 1.034-1.2 | eV | Temperature-dependent |

**Typical Applications:**
- Fast reactor fuel (EBR-II, FFTF)
- Most widely validated metallic fuel composition
- Reference: Figure 6 in paper

**Parameter Sensitivity for U-10Zr:**
- Most sensitive to: `dislocation_density`, `Fnf`, `temperature`
- Dislocation density ±50% → ±40% swelling change
- Temperature 600-800 K: bell-shaped swelling curve with peak at 700 K

### U-Pu-Zr Alloy

Uranium-Plutonium-Zirconium alloy fuel (typically U-19Pu-10Zr).

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| **Dislocation Density** | 2.0×10¹³ | m⁻² | Lower than U-10Zr (reduced swelling) |
| **Peak Temperature** | 750 | K | Slightly higher than U-10Zr |
| **Swelling Range** | 0.1-2.0 | % | At 0.4-0.9 at.% burnup |
| **Bulk Nucleation Factor** (`Fnb`) | 1×10⁻⁵ | - | Same as U-10Zr |
| **Boundary Nucleation Factor** (`Fnf`) | 1×10⁻⁵ | - | Same as U-10Zr |
| **Vacancy Formation Energy** | 1.034-1.2 | eV | Same as U-10Zr |

**Typical Applications:**
- Advanced burner reactors
- Transmutation fuels
- Reference: Figure 7 in paper

**Key Differences from U-10Zr:**
- Lower dislocation density reduces swelling
- Higher peak swelling temperature (750 K vs 700 K)
- Swelling typically 30-50% lower than U-10Zr at same conditions

### High-Purity Uranium

Pure uranium fuel (no alloying elements).

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| **Dislocation Density** | 1.0×10¹⁵ | m⁻² | Very high (cold-worked material) |
| **Peak Temperature** | 673 | K | Lower than alloys |
| **Swelling Range** | 1.0-50.0 | % | At 0.5-1.5 at.% burnup (can exceed 50%) |
| **Bulk Nucleation Factor** (`Fnb`) | 1×10⁻⁵ | - | Same as alloys |
| **Boundary Nucleation Factor** (`Fnf`) | 1.0 | - | **5 orders of magnitude higher than alloys!** |
| **Vacancy Formation Energy** | 1.7 | eV | Higher than alloys (1.034-1.2 eV) |

**Typical Applications:**
- Research reactors (historical)
- Fundamental swelling studies
- Reference: Figures 9-10 in paper

**Critical Parameter Differences:**
- **Boundary nucleation factor** (`Fnf` = 1.0) is dramatically higher
  - Causes rapid bubble formation on grain boundaries
  - Leads to much higher swelling rates
  - Can cause grain boundary tearing at high burnup

- **Very high dislocation density** (1×10¹⁵ m⁻²)
  - 10-50× higher than alloys
  - Contributes to high swelling

- **Higher vacancy formation energy** (1.7 eV)
  - Affects defect balance calculations

**⚠️ Warning:** High-purity uranium exhibits extreme swelling (up to 50% volume change) and is not representative of modern alloy fuels. Use these parameters only for validation against historical data.

---

## Simulation Parameters

The `SimulationParameters` dataclass contains runtime configuration parameters.

### Fission & Irradiation Parameters

#### `fission_rate`
- **Type**: `float`
- **Default**: `2.0e20` fissions/m³/s
- **Description**: Fission reaction rate density
- **Physical Meaning**: Number of fission events per cubic meter per second
- **Reference**: JNM 583 (2023) 154542
- **Typical Range**: 10¹⁹ - 10²¹ fissions/m³/s
  - Low flux: ~10¹⁹ fissions/m³/s
  - High flux: ~10²¹ fissions/m³/s
- **Impact**: Directly proportional to gas production rate and defect generation

#### `displacement_rate`
- **Type**: `float`
- **Default**: `14825/5.12e28` ≈ `2.9e-25` fp/fission
- **Description**: Frenkel pair production rate per fission
- **Physical Meaning**: Number of vacancy-interstitial pairs created per fission event
- **Typical Range**: 10-1000 Frenkel pairs per fission
- **Notes**: Calculated from Norgett-Robinson-Torrens (NRT) model

#### `sigma_f`
- **Type**: `float`
- **Default**: `2.72e4` m⁻¹
- **Description**: Macroscopic fission cross section
- **Physical Meaning**: Probability of fission per unit path length
- **Typical Range**: 10³ - 10⁵ m⁻¹
- **Used In**: Converting flux to fission rate

#### `gas_production_rate`
- **Type**: `float`
- **Default**: `0.25`
- **Description**: Fission gas yield (atoms per fission)
- **Physical Meaning**: Average number of gas atoms (Xe + Kr) produced per fission
- **Typical Range**: 0.20 - 0.30
  - U-235: ~0.25 gas atoms/fission
  - Pu-239: ~0.28 gas atoms/fission
- **Impact**: Directly proportional to total gas inventory

#### `resolution_rate`
- **Type**: `float`
- **Default**: `2e-5` s⁻¹
- **Description**: Fission gas resolution rate from bubbles
- **Physical Meaning**: Rate at which fission fragments knock gas atoms out of bubbles back into the matrix
- **Typical Range**: 10⁻⁶ - 10⁻⁴ s⁻¹
- **Impact**: Higher rates keep gas in solution, delaying bubble growth

#### `grain_diameter`
- **Type**: `float`
- **Default**: `0.5e-6` m (0.5 μm)
- **Description**: Average grain diameter
- **Physical Meaning**: Size of crystalline grains in the polycrystalline fuel
- **Typical Range**: 0.1 - 10 μm
  - Fine-grained fuel: ~0.5 μm
  - Coarse-grained fuel: ~5 μm
- **Impact**: Affects fraction of atoms near grain boundaries

### Temperature & Time

#### `temperature`
- **Type**: `float`
- **Default**: `600` K
- **Description**: Simulation temperature
- **Physical Meaning**: Operating temperature of the nuclear fuel
- **Typical Range**: 400 - 1200 K
  - Low-temperature regime: 400-600 K
  - Peak swelling: 700-800 K
  - High-temperature regime: 900-1200 K
- **Impact**: CRITICAL - Controls exponential Arrhenius terms in diffusion
- **Sensitivity**: Bell-shaped swelling curve with maximum at 700-800 K

#### `time_step`
- **Type**: `float`
- **Default**: `1e-9` s
- **Description**: Initial time step for ODE solver
- **Physical Meaning**: Starting integration step size
- **Typical Range**: 10⁻¹² - 10⁻⁶ s
- **Notes**: Solver adapts this automatically based on solution stiffness

#### `max_time_step`
- **Type**: `float`
- **Default**: `100` s
- **Description**: Maximum allowed time step for ODE solver
- **Physical Meaning**: Upper limit on adaptive step size
- **Typical Range**: 1 - 1000 s
- **Impact**: Larger values speed up computation but may reduce accuracy

#### `max_time`
- **Type**: `float`
- **Default**: `8,640,000` s (100 days)
- **Description**: Total simulation time
- **Physical Meaning**: Duration of irradiation to simulate
- **Typical Range**: 1 day to 1 year
  - Short-term: 1-10 days
  - Medium-term: 30-100 days
  - Long-term: 1-2 years
- **Notes**: 100 days ≈ 2 at.% burnup for typical reactor conditions

### Gas Diffusion Parameters

#### `Dgb_prefactor`
- **Type**: `float`
- **Default**: `1.2e-7` m²/s
- **Description**: Pre-exponential factor for gas atom diffusion in bulk
- **Equation**: Dgb = Dgb_prefactor × exp(-Ea / kBT) + fission_term
- **Typical Range**: 10⁻⁸ - 10⁻⁶ m²/s
- **Impact**: Controls gas atom mobility to bubbles

#### `Dgb_activation_energy`
- **Type**: `float`
- **Default**: `1.16` eV
- **Description**: Activation energy for gas atom diffusion in bulk
- **Physical Meaning**: Energy barrier for gas atom migration through lattice
- **Typical Range**: 0.8 - 1.5 eV
- **Impact**: Higher values reduce gas mobility exponentially

#### `Dgb_fission_term`
- **Type**: `float`
- **Default**: `5.07e-31` m²/fission
- **Description**: Fission-enhanced diffusion coefficient
- **Physical Meaning**: Additional gas diffusion due to fission fragment mixing
- **Equation Contribution**: Dgb_total = thermal_diffusion + Dgb_fission_term × fission_rate
- **Impact**: Becomes dominant at high fission rates

#### `Dgf_multiplier`
- **Type**: `float`
- **Default**: `300`
- **Description**: Enhancement factor for gas diffusion at phase boundaries
- **Equation**: Dgf = Dgb × Dgf_multiplier
- **Physical Meaning**: Grain boundaries and phase interfaces provide faster diffusion paths
- **Typical Range**: 10 - 10,000
- **Impact**: Higher values accelerate gas transport to boundary bubbles

### Numerical Solver Parameters

#### `eos_model`
- **Type**: `str`
- **Default**: `'ideal'`
- **Options**: `'ideal'` or `'ronchi'`
- **Description**: Equation of state model for gas pressure in bubbles
- **Ideal Gas**: P = nRT/V (simple, fast)
- **Ronchi**: Modified Van der Waals EOS (more accurate at high density)
- **Recommendation**: Use 'ideal' for most studies, 'ronchi' for high-pressure bubbles

---

## Physical Constants

These are fundamental constants defined in `parameters.py`:

### `BOLTZMANN_CONSTANT_EV`
- **Value**: `8.617e-5` eV/K
- **Description**: Boltzmann constant in electronvolt units
- **Used In**: Activation energy calculations

### `BOLTZMANN_CONSTANT_J`
- **Value**: `1.380649e-23` J/K
- **Description**: Boltzmann constant in SI units
- **Used In**: Equation of state calculations

### `GAS_CONSTANT`
- **Value**: `8.314462618` J/(mol·K)
- **Description**: Universal gas constant
- **Used In**: Ideal gas law and EOS

### `AVOGADRO_CONSTANT`
- **Value**: `6.02214076e23` mol⁻¹
- **Description**: Avogadro's number
- **Used In**: Converting between molar and atomic units

---

## Parameter Sensitivity Guide

Based on the theoretical paper (Section 5), here are the parameters that have the greatest impact on swelling predictions:

### High Sensitivity (±30-50% swelling change)

1. **Dislocation Density** (`dislocation_density`)
   - ±50% density → ±40% swelling
   - Mechanism: Controls sink strength for defect absorption

2. **Dislocation Bias** (`Zi`, `Zv`)
   - ΔZi = 0.02 → large swelling change
   - Mechanism: Bias factor creates vacancy supersaturation

3. **Boundary Nucleation Factor** (`Fnf`)
   - Controls incubation period before rapid swelling
   - Critical for matching experimental swelling curves

4. **Temperature** (`temperature`)
   - Non-linear: bell-shaped curve
   - Peak swelling at 700-800 K
   - Changes diffusion exponentially via Arrhenius terms

### Medium Sensitivity (±10-30% swelling change)

5. **Surface Energy** (`surface_energy`)
   - Affects critical cavity radius
   - Higher energy → larger stable bubbles

6. **Gas Production Rate** (`gas_production_rate`)
   - Linear effect on total gas inventory
   - Directly proportional to swelling

7. **Grain Diameter** (`grain_diameter`)
   - Smaller grains → more boundary area → faster gas release
   - Can reduce swelling by venting gas

### Low Sensitivity (<±10% swelling change)

8. **Recombination Radius** (`recombination_radius`)
   - Moderate effect on defect recombination rate

9. **Resolution Rate** (`resolution_rate`)
   - Secondary effect for most conditions

---

## Usage Examples

### Creating Default Parameters

```python
from gas_swelling.params.parameters import create_default_parameters

# Get all default parameters
params = create_default_parameters()

# Access specific parameters
print(params['temperature'])      # 600.0 K
print(params['fission_rate'])     # 2.0e20 fissions/m³/s
print(params['dislocation_density'])  # 7.0e13 m⁻²
```

### Customizing Parameters

```python
from gas_swelling.params.parameters import MaterialParameters, SimulationParameters

# Create custom material parameters
material = MaterialParameters(
    dislocation_density=1.0e14,  # Higher dislocation density (cold-worked)
    surface_energy=0.6,           # Higher surface energy
    Fnf=5e-5                      # Enhanced boundary nucleation
)

# Create custom simulation parameters
sim = SimulationParameters(
    temperature=750,              # Peak swelling temperature
    fission_rate=3.0e20,          # Higher flux
    max_time=3600*24*200          # 200 days
)

# Use with model
from gas_swelling.models.modelrk23 import GasSwellingModel

model = GasSwellingModel(
    material_params=material,
    sim_params=sim
)

result = model.solve(t_span=(0, sim.max_time))
```

### Temperature Sweep Study

```python
temperatures = [600, 700, 800, 900, 1000]  # K
results = []

for T in temperatures:
    sim = SimulationParameters(temperature=T)
    model = GasSwellingModel(sim_params=sim)
    result = model.solve(t_span=(0, sim.max_time))
    results.append(result)

# Plot swelling vs temperature
swelling_at_burnup = [r['swelling'][-1] for r in results]
# ... plotting code ...
```

### Sensitivity Analysis

```python
# Study effect of dislocation density
densities = [5e13, 7e13, 1e14, 2e14]  # m⁻²

for rho in densities:
    material = MaterialParameters(dislocation_density=rho)
    sim = SimulationParameters()
    model = GasSwellingModel(material_params=material, sim_params=sim)
    result = model.solve(t_span=(0, sim.max_time))
    print(f"rho={rho:.1e}, final swelling={result['swelling'][-1]:.2f}%")
```

---

## Related Documentation

- [Quick Start Tutorial](../examples/quickstart_tutorial.md) - Basic simulation examples
- [Model Theory](../docs/model_design.md) - Theoretical framework
- [Installation Guide](../INSTALL.md) - Setting up the environment
- [Jupyter Notebook Examples](../notebooks/) - Interactive tutorials

---

## References

1. Rest, J. "A model for the fission-gas-driven swelling of metallic fuels." *J. Nucl. Mater.* (1992)
2. Original theoretical paper: "Kinetics of fission-gas-bubble-nucleated void swelling"
3. JNM 583 (2023) 154542 - Modern validation data

---

## Parameter Checklist

Before running simulations, verify:

- [ ] Temperature is appropriate for your study (600-1000 K typical)
- [ ] Fission rate matches reactor conditions (10¹⁹-10²¹ fissions/m³/s)
- [ ] Dislocation density reflects material state (annealed vs. cold-worked)
- [ ] Simulation time covers desired burnup (100 days ≈ 2 at.%)
- [ ] EOS model matches pressure regime ('ideal' for most cases)
- [ ] Grain size matches experimental microstructure

---

*For questions or issues, please refer to the [GitHub repository](https://github.com/your-org/gas-swelling-model) or contact the development team.*
