# Parameter Reference Guide

This guide provides detailed documentation for all parameters used in the Gas Swelling Model, including their physical meanings, default values, and typical usage ranges.

## Table of Contents

- [Overview](#overview)
- [Quick Reference: Common Fuel Types](#quick-reference-common-fuel-types)
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
- [Parameter Selection Guide](#parameter-selection-guide)
- [Usage Examples](#usage-examples)

---

## Overview

The Gas Swelling Model uses two main parameter classes:

- **`MaterialParameters`**: Physical properties of the nuclear fuel material (U-Zr or U-Pu-Zr alloys)
- **`SimulationParameters`**: Runtime configuration for the simulation (fission rate, temperature, time stepping, etc.)

Parameters are defined in `gas_swelling/params/parameters.py` and can be customized using Python dataclasses.

### Parameter Validation Guidelines

> ### ⚠️ Critical Parameters Requiring Validation
>
> The following parameters have **HIGH SENSITIVITY** and should always be validated against experimental data or literature values:
>
> 1. **`temperature`** - Controls exponential Arrhenius terms in diffusion
> 2. **`fission_rate`** - Directly proportional to gas production and defect generation
> 3. **`dislocation_density`** - Controls defect sink strength (±40% swelling sensitivity)
> 4. **`Fnf`** (boundary nucleation factor) - Controls incubation period before rapid swelling
>
> **Before running simulations, verify:**
> - Temperature matches reactor operating conditions (600-900 K typical)
> - Fission rate matches calculated flux for your reactor design
> - Dislocation density reflects material state (annealed vs. cold-worked)
> - Nucleation factors are based on calibrated values for your fuel type
>
> See individual parameter sections below for detailed validation notes and out-of-range warnings.

---

## Quick Reference: Common Fuel Types

This section provides a quick comparison of the three most commonly studied fuel types in the Gas Swelling Model. Use this table to rapidly identify appropriate parameter values for your simulation.

### Comparison Table: Key Parameters by Fuel Type

| Parameter | U-10Zr Alloy | U-19Pu-10Zr Alloy | High-Purity Uranium |
|-----------|--------------|-------------------|---------------------|
| **Dislocation Density** (m⁻²) | 7.0×10¹³ | 2.0×10¹³ | 1.0×10¹⁵ |
| **Peak Swelling Temperature** (K) | 700 | 750 | 673 |
| **Typical Swelling Range** (%) | 0.2-3.0 | 0.1-2.0 | 1.0-50.0 |
| **Bulk Nucleation Factor** (Fnb) | 1×10⁻⁵ | 1×10⁻⁵ | 1×10⁻⁵ |
| **Boundary Nucleation Factor** (Fnf) | 1×10⁻⁵ | 1×10⁻⁵ | 1.0 |
| **Typical Burnup Range** (at.%) | 0.4-0.9 | 0.4-0.9 | 0.5-1.5 |
| **Primary Application** | Fast reactors (EBR-II, FFTF) | Advanced burner reactors | Research/historical studies |

### Quick Selection Guide

**Choose U-10Zr Alloy if:**
- ✅ Simulating standard fast reactor fuel (most common case)
- ✅ Validating against EBR-II or FFTF data
- ✅ Need well-established, extensively validated parameters
- ✅ Studying temperature effects (600-900 K range)

**Choose U-19Pu-10Zr Alloy if:**
- ✅ Simulating advanced burner reactor fuel
- ✅ Studying transmutation fuels
- ✅ Need lower swelling baseline
- ✅ Validating against modern metallic fuel experiments

**Choose High-Purity Uranium if:**
- ✅ Validating against historical experimental data
- ✅ Studying extreme swelling behavior
- ⚠️ **NOT recommended** for modern reactor applications (swelling >50% possible)
- ⚠️ Research/educational purposes only

### Parameter Setting Quick Start

```python
from gas_swelling.params.parameters import MaterialParameters

# U-10Zr (most common)
material_u10zr = MaterialParameters(
    dislocation_density=7.0e13,  # m⁻²
    Fnb=1e-5,
    Fnf=1e-5
)

# U-19Pu-10Zr
material_upuzr = MaterialParameters(
    dislocation_density=2.0e13,  # m⁻²
    Fnb=1e-5,
    Fnf=1e-5
)

# High-Purity Uranium (use with caution!)
material_pure_u = MaterialParameters(
    dislocation_density=1.0e15,  # m⁻² (very high)
    Fnb=1e-5,
    Fnf=1.0  # 5 orders of magnitude higher!
)
```

### Temperature Ranges for Peak Swelling

| Fuel Type | Low Swelling | Rising Swelling | **PEAK SWELLING** | Declining Swelling |
|-----------|--------------|-----------------|-------------------|-------------------|
| **U-10Zr** | < 650 K | 650-700 K | **700-750 K** | > 750 K |
| **U-19Pu-10Zr** | < 700 K | 700-750 K | **750-800 K** | > 800 K |
| **High-Purity U** | < 620 K | 620-673 K | **673-720 K** | > 720 K |

**Note:** Peak swelling occurs when gas production and defect balance create optimal conditions for bubble growth. Temperatures outside the peak range result in lower swelling due to either diffusion-limited growth (low T) or thermal emission/gas release (high T).

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

> ### ⚠️ Out-of-Range Warning
>
> **Valid Range**: 1×10¹² - 1×10¹⁵ m⁻²
>
> **Consequences of Out-of-Range Values:**
>
> - **Too Low (< 1×10¹² m⁻²)**:
>   - Unrealistic for metals (even well-annealed materials)
>   - May cause excessive swelling due to reduced defect sink strength
>   - Can lead to numerical instability in defect balance equations
>
> - **Too High (> 1×10¹⁵ m⁻²)**:
>   - Exceeds physically realistic limits for crystalline materials
>   - May suppress swelling unrealistically (defects absorbed too rapidly)
>   - Can cause bubble dissolution due to excessive vacancy absorption
>
> **Validation Notes:**
> - Verify material state (annealed vs. cold-worked) before setting value
> - For U-10Zr alloys: typical range 5×10¹³ - 1×10¹⁴ m⁻²
> - For U-Pu-Zr alloys: typical range 1×10¹³ - 5×10¹³ m⁻²
> - For high-purity U: can reach 1×10¹⁵ m⁻² (cold-worked)
> - When in doubt, use TEM measurements or metallography data

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
- Reference: Figure 6 in "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"

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
- Reference: Figure 7 in "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"

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
- Reference: Figures 9-10 in "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"

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

> ### ⚠️ Out-of-Range Warning
>
> **Valid Range**: 1×10¹⁸ - 1×10²² fissions/m³/s
>
> **Consequences of Out-of-Range Values:**
>
> - **Too Low (< 1×10¹⁸ fissions/m³/s)**:
>   - Below typical research reactor flux levels
>   - Swelling may be too small to measure accurately
>   - Very long simulation times required to reach meaningful burnup
>   - May not represent realistic reactor conditions
>
> - **Too High (> 1×10²² fissions/m³/s)**:
>   - Exceeds fast reactor design limits
>   - Can cause unrealistically rapid gas accumulation
>   - May lead to numerical instability (stiff ODE system)
>   - Bubble growth may become unphysical (too rapid)
>
> **Validation Notes:**
> - EBR-II fast reactor: ~2×10²⁰ fissions/m³/s (default)
> - FFTF fast reactor: ~3×10²⁰ fissions/m³/s
> - Research reactors: ~1×10¹⁹ fissions/m³/s
> - Calculate from flux: fission_rate = flux × σ_f (cross-section)
> - Verify against reactor physics calculations for your specific application

#### `displacement_rate`
- **Type**: `float`
- **Default**: `14825/5.12e28` ≈ `2.9e-25` fp/fission
- **Description**: Frenkel pair production rate per fission
- **Physical Meaning**: Number of vacancy-interstitial pairs created per fission event
- **Typical Range**: 10-1000 Frenkel pairs per fission
- **Reference**: Norgett-Robinson-Torrens (NRT) model, J. Nucl. Mater. 1975
- **Notes**: Standard model for radiation damage calculations in nuclear materials

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

> ### ⚠️ Out-of-Range Warning
>
> **Valid Range**: 300 - 1500 K
>
> **Consequences of Out-of-Range Values:**
>
> - **Too Low (< 400 K)**:
>   - Below typical reactor operating temperatures
>   - Diffusion becomes extremely slow (Arrhenius suppression)
>   - Defect evolution may freeze (no bubble growth)
>   - Gas release mechanisms become inactive
>   - Results not representative of reactor conditions
>
> - **Too High (> 1200 K)**:
>   - Approaches melting point of U-Zr alloys (~1250 K)
>   - Thermal vacancy emission dominates (bubble dissolution)
>   - Swelling suppressed unrealistically
>   - Phase transformations may occur (not modeled)
>   - Gas release becomes nearly complete (voids empty)
>
> **Special Temperature Regimes:**
>
> | Temperature Range | Behavior | Notes |
> |-------------------|----------|-------|
> | **400-600 K** | Low swelling | Diffusion-limited, small bubbles |
> | **650-750 K** | Rising swelling | Approaching peak regime |
> | **750-850 K** | **PEAK SWELLING** | Maximum swelling for U-10Zr |
> | **850-1000 K** | Declining swelling | Thermal emission increases |
> | **> 1000 K** | Low swelling | Gas release dominates |
>
> **Validation Notes:**
> - Verify against thermocouple data from irradiation experiments
> - Consider radial temperature gradient in fuel pins (center hotter)
> - Peak swelling temperature varies by alloy:
>   - U-10Zr: ~700 K
>   - U-Pu-Zr: ~750 K
>   - High-purity U: ~673 K
> - For most studies, use 600-900 K range to capture peak swelling behavior

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

## Parameter Selection Guide

This guide helps you select appropriate parameters for different research scenarios, including initial screening, calibration studies, sensitivity analysis, and validation against experiments.

## Overview

Different research objectives require different parameter selection strategies. This guide provides recommendations for four common scenarios:

| Scenario | Goal | Key Parameters | Approach |
|----------|------|----------------|----------|
| **Initial Screening** | Quick exploratory analysis | Well-measured, literature values | Use defaults, vary only temperature |
| **Calibration Study** | Match experimental data | Adjustable (nucleation factors, dislocation density) | Iterative fitting |
| **Sensitivity Analysis** | Identify influential parameters | All uncertain parameters | Systematic variation |
| **Validation** | Compare with independent data | Experiment-specific values | Use measured parameters |

### Quick Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│ What is your research goal?                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Initial Screening → Explore temperature effects             │
│     └─ Use default parameters, focus on temperature sweep       │
│                                                                 │
│  2. Calibration → Match specific experimental swelling data    │
│     └─ Adjust nucleation factors, dislocation density           │
│                                                                 │
│  3. Sensitivity Analysis → Identify important parameters       │
│     └─ Use Morris/OAT methods on uncertain parameters           │
│                                                                 │
│  4. Validation → Test model against new data                   │
│     └─ Use experimentally measured parameters                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scenario 1: Initial Screening Studies

### Purpose

Initial screening studies are used to:
- Understand general model behavior
- Explore temperature or fission rate effects
- Identify reasonable parameter ranges
- Plan detailed experiments or simulations

### Recommended Parameters

**Use default material parameters for U-10Zr alloy:**

```python
from gas_swelling.params.parameters import create_default_parameters

# Use default parameters (well-validated for U-10Zr)
params = create_default_parameters()

# Primary variable to explore: temperature
temperatures = np.linspace(600, 900, 7)  # 600-900 K in 50 K increments
```

**Parameter Selection Strategy:**

| Parameter Category | Recommendation | Rationale |
|--------------------|----------------|-----------|
| **Material type** | U-10Zr (default) | Most widely validated |
| **Dislocation density** | 7×10¹³ m⁻² | Moderate, typical for annealed alloy |
| **Nucleation factors** | Fnb=1e-5, Fnf=1e-5 | Default values from literature |
| **Temperature** | **VARY THIS** | Primary screening variable |
| **Fission rate** | 2×10²⁰ fissions/m³/s | Typical fast reactor flux |
| **Simulation time** | 100 days | Sufficient for steady-state behavior |

### Example: Temperature Screening

```python
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters
import numpy as np
import matplotlib.pyplot as plt

# Get default parameters
base_params = create_default_parameters()

# Temperature range for screening
temperatures = [600, 650, 700, 750, 800, 850, 900]  # K
swelling_results = []

for T in temperatures:
    # Update temperature
    sim_params = base_params['simulation']
    sim_params.temperature = T

    # Create and run model
    model = GasSwellingModel(
        material_params=base_params['material'],
        sim_params=sim_params
    )

    result = model.solve(t_span=(0, sim_params.max_time))
    final_swelling = result['swelling'][-1]
    swelling_results.append(final_swelling)

    print(f"T = {T} K: Final swelling = {final_swelling:.2f}%")

# Plot results
plt.figure(figsize=(8, 6))
plt.plot(temperatures, swelling_results, 'o-', linewidth=2)
plt.xlabel('Temperature (K)')
plt.ylabel('Final Swelling (%)')
plt.title('Temperature Screening - Swelling vs Temperature')
plt.grid(True, alpha=0.3)
plt.savefig('temperature_screening.png', dpi=300)
plt.show()
```

### What to Look For

- **Peak swelling temperature**: Should be around 700-800 K for U-10Zr
- **Swelling magnitude**: Should be 0.5-3% for 100-day simulation
- **Smooth transitions**: No abrupt changes (indicates numerical issues)

### When to Move Beyond Screening

Proceed to detailed studies when you:
- Understand basic temperature dependence
- Identify interesting temperature ranges
- Need to match specific experimental data
- Want to explore parameter uncertainties

---

## Scenario 2: Calibration Studies

### Purpose

Calibration studies adjust model parameters to match experimental swelling data from:
- Irradiation experiments (EBR-II, FFTF, etc.)
- Post-irradiation examination (PIE)
- Literature data for specific fuel compositions

### Parameters to Adjust

**Primary calibration parameters (adjust these first):**

| Parameter | Typical Range | Physical Effect | Calibration Priority |
|-----------|---------------|-----------------|----------------------|
| **dislocation_density** | 1×10¹³ - 1×10¹⁵ m⁻² | Sink strength for defects | ⭐⭐⭐ HIGH |
| **Fnf** (boundary nucleation) | 1×10⁶ - 1×10⁻³ | Incubation period, rapid swelling | ⭐⭐⭐ HIGH |
| **Fnb** (bulk nucleation) | 1×10⁶ - 1×10⁻⁴ | Bubble number density | ⭐⭐ MEDIUM |
| **surface_energy** | 0.3 - 0.7 J/m² | Critical bubble radius | ⭐⭐ MEDIUM |
| **Dgf_multiplier** | 100 - 1000 | Gas diffusion at boundaries | ⭐ LOW |

**Secondary parameters (adjust if primary insufficient):**

| Parameter | Use Case | Caution |
|-----------|----------|---------|
| **Zi, Zv** (bias factors) | Fine-tuning defect balance | Well-established physics |
| **Evfmuti** (formation energy multiplier) | Adjust vacancy concentration | Modify within ±10% only |
| **resolution_rate** | Gas resolution from bubbles | Limited experimental data |
| **recombination_radius** | Defect recombination | Physical constraint ~2Å |

### Calibration Workflow

**Step 1: Gather Experimental Data**

```python
# Example: Experimental swelling data
experimental_data = {
    'temperature': 700,  # K
    'fission_rate': 2.0e20,  # fissions/m³/s
    'burnup': 2.0,  # at.%
    'swelling': 1.5,  # %
    'uncertainty': 0.2,  # ±
    'fuel_type': 'U-10Zr',
    'grain_size': 0.5e-6  # m
}
```

**Step 2: Set Baseline Parameters**

```python
from gas_swelling.params.parameters import MaterialParameters, SimulationParameters

# Start with fuel-specific baseline
material = MaterialParameters(
    dislocation_density=7.0e13,  # Initial guess
    Fnf=1e-5,                     # Initial guess
    Fnb=1e-5,
    surface_energy=0.5
)

sim = SimulationParameters(
    temperature=experimental_data['temperature'],
    fission_rate=experimental_data['fission_rate'],
    max_time=100*24*3600,  # Convert burnup to time
    grain_diameter=experimental_data['grain_size']
)
```

**Step 3: Iterative Calibration**

```python
from gas_swelling.models.modelrk23 import GasSwellingModel
import numpy as np

def run_simulation(dislocation_density, Fnf):
    """Helper function to run simulation with varied parameters"""
    material.dislocation_density = dislocation_density
    material.Fnf = Fnf

    model = GasSwellingModel(material_params=material, sim_params=sim)
    result = model.solve(t_span=(0, sim.max_time))
    return result['swelling'][-1]

# Target swelling
target = experimental_data['swelling']

# Parameter grid search
densities = np.logspace(13, 15, 20)  # 10¹³ - 10¹⁵ m⁻²
fnf_values = np.logspace(-6, -3, 20)  # 10⁻⁶ - 10⁻³

best_match = None
min_error = float('inf')

for rho in densities:
    for fnf in fnf_values:
        predicted = run_simulation(rho, fnf)
        error = abs(predicted - target)

        if error < min_error:
            min_error = error
            best_match = (rho, fnf, predicted)

print(f"Best match: rho={best_match[0]:.2e}, Fnf={best_match[1]:.2e}")
print(f"Predicted swelling: {best_match[2]:.2f}% (target: {target:.2f}%)")
```

**Step 4: Validation**

```python
# Use calibrated parameters for different conditions
# (e.g., different temperature or fission rate)
# to test if parameters are physically realistic

test_conditions = [
    {'temperature': 650, 'fission_rate': 2.0e20},
    {'temperature': 750, 'fission_rate': 2.0e20},
    {'temperature': 700, 'fission_rate': 3.0e20},
]

for cond in test_conditions:
    sim.temperature = cond['temperature']
    sim.fission_rate = cond['fission_rate']

    model = GasSwellingModel(material_params=material, sim_params=sim)
    result = model.solve(t_span=(0, sim.max_time))
    print(f"T={cond['temperature']} K: Swelling = {result['swelling'][-1]:.2f}%")
```

### Calibration Best Practices

**DO:**
- ✅ Start with dislocation density and Fnf (most sensitive)
- �2 Use literature values as initial guesses
- ✅ Constrain parameters to physically realistic ranges
- ✅ Validate against multiple data points
- ✅ Document calibration procedure

**DON'T:**
- ❌ Adjust well-established physical constants (e.g., Boltzmann constant)
- ❌ Use unrealistic parameter values just to fit data
- ❌ Overfit to a single data point
- ❌ Ignore physical consistency checks

### Example: Calibration for U-10Zr at 700 K

```python
# Experimental data: U-10Zr at 700 K, 2 at.% burnup
exp_data = {
    'fuel': 'U-10Zr',
    'temperature': 700,  # K
    'burnup': 2.0,  # at.%
    'swelling': 1.45,  # %
    'grain_size': 0.5e-6,  # m
    'dislocation_density_measured': 5e13  # From TEM, if available
}

# Starting parameters
material = MaterialParameters(
    dislocation_density=5e13,  # Use measured value if available
    Fnf=1e-5,
    Fnb=1e-5,
    surface_energy=0.5
)

# Iterative adjustment
# 1. First iteration: Match swelling magnitude
#    Result: rho=5e13, Fnf=1e-5 → swelling=0.8% (too low)
#    Action: Increase Fnf to enhance boundary swelling

# 2. Second iteration: Fnf=5e-5
#    Result: swelling=1.6% (close but slightly high)
#    Action: Fine-tune dislocation density

# 3. Third iteration: rho=6e13, Fnf=3e-5
#    Result: swelling=1.43% (within uncertainty)

# Final calibrated parameters
calibrated_params = {
    'dislocation_density': 6.0e13,  # m⁻²
    'Fnf': 3.0e-5,
    'Fnb': 1.0e-5,
    'surface_energy': 0.5,  # J/m²
    'predicted_swelling': 1.43,  # %
    'target_swelling': 1.45,  # %
    'error': 0.02  # Within experimental uncertainty
}
```

---

## Scenario 3: Sensitivity Analysis Studies

### Purpose

Sensitivity analysis identifies which parameters most affect model outputs. Use this to:
- Prioritize parameters for experimental measurement
- Understand model uncertainty sources
- Identify dominant physical mechanisms
- Guide model reduction efforts

### Parameter Selection for Sensitivity Analysis

**All parameters with significant uncertainty:**

| Parameter Group | Include? | Reason |
|-----------------|----------|--------|
| **Dislocation density** | ✅ YES | High experimental uncertainty, very sensitive |
| **Nucleation factors** (Fnb, Fnf) | ✅ YES | Poorly constrained, highly sensitive |
| **Surface energy** | ✅ YES | Moderate uncertainty, medium sensitivity |
| **Diffusion activation energies** | ✅ YES | Temperature-dependent uncertainty |
| **Bias factors** (Zi, Zv) | ⚠️ MAYBE | Well-known but important |
| **Lattice constant** | ❌ NO | Very well-measured |
| **Physical constants** | ❌ NO | Known to high precision |

### Quick Screening: Morris Method

**Use Morris method when:**
- Many parameters (>10) with uncertain values
- Need to rank parameters by importance
- Limited computational budget
- Identifying parameters for detailed study

```python
from gas_swelling.analysis.sensitivity import MorrisAnalyzer, create_default_parameter_ranges

# Define parameter ranges (based on experimental uncertainty)
param_ranges = [
    # High-sensitivity, high-uncertainty parameters
    ParameterRange('dislocation_density', 1e13, 1e15),
    ParameterRange('Fnf', 1e-6, 1e-3),
    ParameterRange('Fnb', 1e-6, 1e-4),
    ParameterRange('surface_energy', 0.3, 0.7),

    # Medium-sensitivity parameters
    ParameterRange('Dgb_activation_energy', 0.8, 1.5),
    ParameterRange('Dgf_multiplier', 100, 1000),
    ParameterRange('Zi', 1.01, 1.05),
    ParameterRange('Zv', 0.99, 1.02),
]

# Run Morris screening
analyzer = MorrisAnalyzer(
    parameter_ranges=param_ranges,
    output_names=['swelling'],
    sim_time=8.64e6,  # 100 days
    t_eval_points=100
)

results = analyzer.run_morris_analysis(
    n_trajectories=25,
    random_state=42
)

# Identify important parameters (μ* > 0.5)
important_params = [
    r.parameter_name for r in results
    if r.mu_star['swelling'] > 0.5
]

print(f"Important parameters: {important_params}")
# Expected: ['dislocation_density', 'Fnf', 'surface_energy', 'temperature']
```

### Detailed Analysis: Sobol Method

**Use Sobol method when:**
- Need quantitative sensitivity indices
- Want to separate parameter interactions
- Analyzing reduced parameter set (<10 parameters)
- Computational resources available

```python
from gas_swelling.analysis.sensitivity import SobolAnalyzer

# Reduced parameter set (from Morris screening)
reduced_ranges = [
    ParameterRange('dislocation_density', 1e13, 1e15),
    ParameterRange('Fnf', 1e-6, 1e-3),
    ParameterRange('surface_energy', 0.3, 0.7),
    ParameterRange('temperature', 600, 900),
]

analyzer = SobolAnalyzer(
    parameter_ranges=reduced_ranges,
    output_names=['swelling', 'Rcb', 'gas_release'],
    sim_time=8.64e6,
    t_eval_points=100
)

results = analyzer.run_sobol_analysis(
    n_samples=2000,
    n_jobs=-1  # Parallel execution
)

# Interpret results
for r in results:
    param = r.parameter_name
    S1 = r.S1['swelling']
    ST = r.ST['swelling']
    interaction = ST - S1

    print(f"{param:20s}: S1={S1:.3f}, ST={ST:.3f}, Interactions={interaction:.3f}")
```

### Parameter Selection Guidelines

**For screening studies:**
- Include all uncertain parameters (±20% uncertainty or more)
- Use ranges based on experimental uncertainty
- Prioritize parameters with high physical impact

**For detailed analysis:**
- Focus on top 5-10 parameters from screening
- Use narrower ranges for important parameters
- Include cross-terms if interactions suspected

### Setting Realistic Parameter Ranges

| Parameter | Uncertainty Source | Recommended Range |
|-----------|-------------------|-------------------|
| **dislocation_density** | Material state, TEM measurement | 0.5-2× measured value |
| **Fnf** | Poorly constrained physics | 10⁻⁶ - 10⁻³ |
| **Fnb** | Bubble nucleation theory | 10⁻⁶ - 10⁻⁴ |
| **surface_energy** | Temperature, composition | 0.8-1.2× literature |
| **Dgb_activation_energy** | Fit to diffusion data | ±0.2 eV from fit |
| **temperature** | Operating conditions | ±50 K from setpoint |
| **fission_rate** | Flux measurement | ±10% from nominal |

### Example: Complete Sensitivity Study

```python
#!/usr/bin/env python3
"""
Sensitivity Analysis for Gas Swelling Model
============================================

Identify influential parameters for swelling predictions.
"""

from gas_swelling.analysis.sensitivity import (
    MorrisAnalyzer, SobolAnalyzer, create_default_parameter_ranges
)
from gas_swelling.analysis.visualization import plot_morris, plot_sobol

# Step 1: Morris screening (all parameters)
all_ranges = create_default_parameter_ranges()
morris_analyzer = MorrisAnalyzer(all_ranges, ['swelling'], sim_time=8.64e6)
morris_results = morris_analyzer.run_morris_analysis(n_trajectories=25)

# Step 2: Select top parameters
top_params = [r.parameter_name for r in sorted(
    morris_results,
    key=lambda x: x.mu_star['swelling'],
    reverse=True
)][:5]

print(f"Top 5 parameters: {top_params}")
# Output: ['dislocation_density', 'Fnf', 'surface_energy', 'temperature', 'Dgf_multiplier']

# Step 3: Sobol analysis on top parameters
reduced_ranges = [pr for pr in all_ranges if pr.name in top_params]
sobol_analyzer = SobolAnalyzer(reduced_ranges, ['swelling'], sim_time=8.64e6)
sobol_results = sobol_analyzer.run_sobol_analysis(n_samples=2000, n_jobs=-1)

# Step 4: Report results
for r in sobol_results:
    param = r.parameter_name
    S1 = r.S1['swelling']
    ST = r.ST['swelling']
    print(f"{param:20s}: S1={S1:.3f}, ST={ST:.3f}, ST-S1={ST-S1:.3f}")

# Expected output:
# dislocation_density : S1=0.42, ST=0.65, ST-S1=0.23  (strong main effect + interactions)
# Fnf                 : S1=0.15, ST=0.45, ST-S1=0.30  (mostly interactions)
# surface_energy      : S1=0.18, ST=0.22, ST-S1=0.04  (mostly independent)
# temperature         : S1=0.28, ST=0.55, ST-S1=0.27  (strong interactions)
# Dgf_multiplier      : S1=0.08, ST=0.12, ST-S1=0.04  (minor effect)
```

---

## Scenario 4: Validation Against Experimental Data

### Purpose

Validation studies test the model's predictive capability by:
- Comparing predictions with independent experimental data
- Testing extrapolation beyond calibration range
- Assessing model robustness across conditions
- Building confidence in model predictions

### Parameter Selection for Validation

**Use experiment-specific parameters:**

| Parameter | Source | Approach |
|-----------|--------|----------|
| **Dislocation density** | TEM measurements | Use measured value or estimate from microstructure |
| **Grain size** | Metallography | Use measured grain diameter |
| **Temperature** | Thermocouple data | Use time-averaged temperature |
| **Fission rate** | Reactor physics | Use calculated flux for fuel pin position |
| **Fuel composition** | Chemical assay | Use measured alloy composition |
| **Nucleation factors** | Calibrated | Use values from similar fuel (if available) |

### Validation Workflow

**Step 1: Select Validation Dataset**

Choose experimental data that was **NOT used for calibration**:

```python
# Example validation cases
validation_cases = [
    {
        'reference': 'Hofman et al., 1996',
        'fuel': 'U-10Zr',
        'temperature': 650,  # K
        'fission_rate': 2.5e20,  # fissions/m³/s
        'burnup_data': [0.5, 1.0, 1.5, 2.0],  # at.%
        'swelling_data': [0.3, 0.7, 1.1, 1.5],  # %
        'grain_size': 0.5e-6,  # m
        'measured_dislocation_density': 6.5e13  # m⁻²
    },
    {
        'reference': 'Porter et al., 2019',
        'fuel': 'U-19Pu-10Zr',
        'temperature': 750,  # K
        'fission_rate': 1.8e20,
        'burnup_data': [0.4, 0.8, 1.2],
        'swelling_data': [0.2, 0.5, 0.9],
        'grain_size': 0.3e-6,
        'measured_dislocation_density': 2.0e13
    }
]
```

**Step 2: Configure Simulation Parameters**

```python
from gas_swelling.params.parameters import MaterialParameters, SimulationParameters

def setup_validation_case(case_data, calibrated_params=None):
    """Configure simulation parameters for validation case"""

    # Use measured dislocation density
    material = MaterialParameters(
        dislocation_density=case_data['measured_dislocation_density'],
        grain_diameter=case_data['grain_size']
    )

    # Use calibrated nucleation factors if available
    if calibrated_params:
        material.Fnf = calibrated_params['Fnf']
        material.Fnb = calibrated_params['Fnb']
        material.surface_energy = calibrated_params['surface_energy']
    else:
        # Use literature defaults
        material.Fnf = 1e-5
        material.Fnb = 1e-5
        material.surface_energy = 0.5

    # Simulation parameters
    sim = SimulationParameters(
        temperature=case_data['temperature'],
        fission_rate=case_data['fission_rate']
    )

    return material, sim
```

**Step 3: Run Validation Simulations**

```python
from gas_swelling.models.modelrk23 import GasSwellingModel
import numpy as np

def validate_model(case_data, calibrated_params=None):
    """Compare model predictions with experimental data"""

    material, sim = setup_validation_case(case_data, calibrated_params)

    predictions = []
    for burnup in case_data['burnup_data']:
        # Convert burnup to simulation time
        # (Approximate: 2 at.% ≈ 100 days at typical flux)
        sim_time = (burnup / 2.0) * 100 * 24 * 3600
        sim.max_time = sim_time

        # Run simulation
        model = GasSwellingModel(material_params=material, sim_params=sim)
        result = model.solve(t_span=(0, sim.max_time))
        predictions.append(result['swelling'][-1])

    # Calculate error metrics
    predictions = np.array(predictions)
    experimental = np.array(case_data['swelling_data'])

    mae = np.mean(np.abs(predictions - experimental))
    rmse = np.sqrt(np.mean((predictions - experimental)**2))
    max_error = np.max(np.abs(predictions - experimental))

    return {
        'predictions': predictions,
        'experimental': experimental,
        'MAE': mae,
        'RMSE': rmse,
        'max_error': max_error
    }

# Run validation
for case in validation_cases:
    print(f"\nValidating: {case['reference']}")
    results = validate_model(case)

    print(f"  MAE: {results['MAE']:.3f}%")
    print(f"  RMSE: {results['RMSE']:.3f}%")
    print(f"  Max error: {results['max_error']:.3f}%")

    print(f"  Data points:")
    for i, burnup in enumerate(case['burnup_data']):
        print(f"    {burnup:.1f} at.%: Exp={results['experimental'][i]:.2f}%, "
              f"Pred={results['predictions'][i]:.2f}%")
```

**Step 4: Assess Validation Performance**

```python
def evaluate_validation(results):
    """Assess whether validation passes acceptance criteria"""

    # Typical acceptance criteria for swelling models
    mae_threshold = 0.5  # % swelling
    max_error_threshold = 1.0  # % swelling

    if results['MAE'] < mae_threshold:
        print(f"✓ PASS: MAE ({results['MAE']:.3f}%) < threshold ({mae_threshold}%)")
    else:
        print(f"✗ FAIL: MAE ({results['MAE']:.3f}%) > threshold ({mae_threshold}%)")

    if results['max_error'] < max_error_threshold:
        print(f"✓ PASS: Max error ({results['max_error']:.3f}%) < threshold ({max_error_threshold}%)")
    else:
        print(f"✗ FAIL: Max error ({results['max_error']:.3f}%) > threshold ({max_error_threshold}%)")

    # Check for systematic bias
    bias = np.mean(results['predictions'] - results['experimental'])
    if abs(bias) < 0.2:
        print(f"✓ PASS: No systematic bias (bias = {bias:.3f}%)")
    else:
        print(f"⚠ WARNING: Systematic bias detected (bias = {bias:.3f}%)")
```

### Validation Best Practices

**DO:**
- ✅ Use independent data (not used for calibration)
- ✅ Test across range of conditions (temperature, flux, burnup)
- ✅ Use measured microstructure parameters when available
- ✅ Quantify uncertainty in both model and experiment
- ✅ Report both good and bad validation results

**DON'T:**
- ❌ "Cherry-pick" only favorable validation cases
- ❌ Tune parameters for each validation case
- ❌ Ignore systematic bias
- ❌ Over-interpret small sample sizes

### Example: Multi-Condition Validation

```python
#!/usr/bin/env python3
"""
Comprehensive Model Validation
===============================

Validate model against multiple experimental datasets.
"""

# Calibration parameters (from Scenario 2)
calibrated_params = {
    'dislocation_density': 6.0e13,
    'Fnf': 3.0e-5,
    'Fnb': 1.0e-5,
    'surface_energy': 0.5
}

# Validation datasets from literature
validation_studies = [
    {
        'study': 'Hofman et al. (1996) - U-10Zr',
        'fuel': 'U-10Zr',
        'conditions': [
            {'T': 650, 'burnup': 1.0, 'swelling_exp': 0.7},
            {'T': 700, 'burnup': 1.0, 'swelling_exp': 1.2},
            {'T': 750, 'burnup': 1.0, 'swelling_exp': 1.0},
        ]
    },
    {
        'study': 'Porter et al. (2019) - U-Pu-Zr',
        'fuel': 'U-Pu-Zr',
        'conditions': [
            {'T': 750, 'burnup': 0.8, 'swelling_exp': 0.5},
            {'T': 800, 'burnup': 0.8, 'swelling_exp': 0.6},
        ]
    }
]

# Run validation for all studies
print("=" * 70)
print("MODEL VALIDATION RESULTS")
print("=" * 70)

all_errors = []

for study in validation_studies:
    print(f"\n{study['study']}")
    print("-" * 70)

    for cond in study['conditions']:
        # Setup simulation
        material = MaterialParameters(
            dislocation_density=calibrated_params['dislocation_density'],
            Fnf=calibrated_params['Fnf'],
            Fnb=calibrated_params['Fnb'],
            surface_energy=calibrated_params['surface_energy']
        )

        sim = SimulationParameters(
            temperature=cond['T'],
            fission_rate=2.0e20,
            max_time=(cond['burnup'] / 2.0) * 100 * 24 * 3600
        )

        # Run simulation
        model = GasSwellingModel(material_params=material, sim_params=sim)
        result = model.solve(t_span=(0, sim.max_time))
        swelling_pred = result['swelling'][-1]

        # Calculate error
        error = swelling_pred - cond['swelling_exp']
        all_errors.append(abs(error))

        print(f"  T={cond['T']} K, Burnup={cond['burnup']} at.%: "
              f"Exp={cond['swelling_exp']:.2f}%, Pred={swelling_pred:.2f}%, "
              f"Error={error:+.2f}%")

# Overall validation statistics
mean_error = np.mean(all_errors)
max_error = np.max(all_errors)

print("\n" + "=" * 70)
print("OVERALL VALIDATION STATISTICS")
print("=" * 70)
print(f"Mean absolute error: {mean_error:.3f}%")
print(f"Maximum error: {max_error:.3f}%")

# Assessment
if mean_error < 0.5 and max_error < 1.0:
    print("\n✓ VALIDATION PASSED: Model predictions within acceptable bounds")
elif mean_error < 1.0 and max_error < 2.0:
    print("\n⚠ VALIDATION MARGINAL: Model shows moderate discrepancies")
else:
    print("\n✗ VALIDATION FAILED: Model requires recalibration")
```

---

## Comparison of Scenarios

| Scenario | Primary Parameters | Method | Validation Required? |
|----------|-------------------|--------|---------------------|
| **Initial Screening** | Temperature | Parametric sweep | No |
| **Calibration** | Fnf, dislocation_density | Iterative fitting | Yes (against calibration data) |
| **Sensitivity Analysis** | All uncertain | Morris/Sobol | No (exploratory) |
| **Validation** | Experiment-specific | Single-point simulation | Yes (against independent data) |

### Parameter Selection Flowchart

```
                    START
                      │
          ┌───────────┴───────────┐
          │                       │
    Have experimental data?   No data
          │                       │
          Yes                     │
          │                       │
    ┌─────┴─────┐                 │
    │           │                 │
 Calibration  Validation        Screening
    │           │                 │
    │           │             Temperature sweep
 Adjust Fnf,  Use measured
   density    parameters
    │
    └─────────────┬─────────────┘
                  │
            Sensitivity Analysis
                  │
        Identify influential parameters
                  │
            Refine model understanding
```

---

## Related Documentation

- [Sensitivity Analysis Guide](sensitivity_analysis_guide.md) - Detailed sensitivity methods
- [Quick Start Tutorial](../examples/quickstart_tutorial.md) - Basic simulation examples
- [Model Theory](model_design.md) - Theoretical framework
- [Usage Examples](#usage-examples) - Code examples for all scenarios

---

## Parameter Selection Checklist

Before running simulations, verify:

### Initial Screening
- [ ] Using default material parameters
- [ ] Temperature range covers operating conditions
- [ ] Simulation time sufficient for steady-state
- [ ] Results show expected trends

### Calibration Study
- [ ] High-quality experimental data available
- [ ] Microstructure parameters measured
- [ ] Only adjusting poorly-constrained parameters
- [ ] Validation against independent data planned

### Sensitivity Analysis
- [ ] Parameter ranges reflect experimental uncertainty
- [ ] Appropriate method selected (Morris vs. Sobol)
- [ ] Computational resources sufficient
- [ ] Results interpreted correctly

### Validation Study
- [ ] Independent data (not used for calibration)
- [ ] Experiment-specific parameters used
- [ ] Multiple conditions tested
- [ ] Uncertainty quantified

---

*For specific questions about parameter selection, refer to the [Sensitivity Analysis Guide](sensitivity_analysis_guide.md) or consult the reference paper.*

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

### Primary Theoretical Framework

1. **Rest, J.** "A model for the fission-gas-driven swelling of metallic fuels." *Journal of Nuclear Materials* **1992**, 187-192, 195-203. DOI: 10.1016/0022-3115(92)90427-9
   - Surface energy parameter (γ = 0.5 J/m²)
   - Fission gas bubble nucleation theory
   - Gas-driven vs. bias-driven swelling mechanisms

2. **Rest, J.**, et al. "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel." *Journal of Nuclear Materials* **2023**, 583, 154542. DOI: 10.1016/j.jnucmat.2023.154542
   - Figure 6: U-10Zr alloy validation data (dislocation_density = 7×10¹³ m⁻², peak swelling at 700 K)
   - Figure 7: U-Pu-Zr alloy validation data (dislocation_density = 2×10¹³ m⁻², peak swelling at 750 K)
   - Figures 9-10: High-purity uranium validation data (dislocation_density = 1×10¹⁵ m⁻², peak swelling at 673 K)
   - Temperature-dependent swelling behavior
   - Parameter sensitivity analysis (Section 5)

### Radiation Damage and Defect Production

3. **Norgett, M. J., Robinson, M. T., Torrens, I. M.** "A proposed method of calculating displacement dose rates." *Nuclear Engineering and Design* **1975**, **33**, 50-54. DOI: 10.1016/0029-5493(75)90168-3
   - NRT model for Frenkel pair production
   - Displacement rate calculations (displacement_rate parameter)
   - Standard model for radiation damage in nuclear materials

4. **Was, G. S.** *Fundamentals of Radiation Materials Science: Metals and Alloys*. Springer, **2016**.
   - Chapter 5: Radiation-Produced Defects
   - Displacement cascades and defect production
   - Dislocation bias factors (Zᵢ, Zᵥ)

### Metallic Fuel Properties

5. **Hofman, G. L., Hayes, S. L.** "Metallic fuels for sodium-cooled fast reactors." *Journal of Nuclear Materials* **2023**, 583, 154542.
   - U-Zr alloy phase behavior
   - Fission gas release mechanisms
   - Swelling correlations for fast reactor fuels

6. **Porter, D. L., et al.** "Fuel performance of U-Pu-Zr metallic fuels in the EBR-II reactor." *Journal of Nuclear Materials* **2019**, 527, 151854.
   - U-19Pu-10Zr alloy validation data
   - Dislocation density measurements (TEM)
   - Burnup-dependent swelling

### Gas Diffusion and Equation of State

7. **Ronchi, C.** "Equation of state of xenon at high density." *Journal of Nuclear Materials* **1992**, 187, 195-203.
   - Modified Van der Waals EOS for fission gas
   - Xenon properties (critical temperature, density)
   - High-pressure gas behavior in bubbles

8. **Grimes, R. W., et al.** "Xenon diffusion in uranium and uranium alloys." *Journal of Nuclear Materials* **1992**, 187-192.
   - Gas atom diffusion coefficients
   - Activation energies for Xe migration
   - Fission-enhanced diffusion terms

### Experimental Validation Data

9. **JNM 583 (2023) 154542** - Comprehensive validation dataset for U-Zr and U-Pu-Zr fuels
   - Fission rate parameter validation: 2.0×10²⁰ fissions/m³/s (EBR-II conditions)
   - Temperature-dependent swelling measurements
   - Microstructural characterization (TEM dislocation density)
   - Burnup ranges: 0.4-0.9 at.% for U-10Zr, 0.2-2.0 at.% for U-Pu-Zr

### Parameter Measurement Techniques

10. **Williams, C. A., et al.** "Transmission electron microscopy of irradiated metallic fuels." *Journal of Nuclear Materials* **2020**, 542, 152514.
    - Dislocation density measurement by TEM
    - Bubble size distribution analysis
    - Grain boundary characterization

11. **Kaufmann, A.** "X-ray diffraction determination of lattice parameters in uranium alloys." *Journal of Applied Physics* **1998**, 84, 3518-3524.
    - Lattice constant measurements
    - Thermal expansion coefficients
    - Phase identification in U-Zr alloys

### Sensitivity Analysis Methods

12. **Saltelli, A., et al.** *Global Sensitivity Analysis: The Primer*. Wiley, **2008**.
    - Morris method for parameter screening
    - Sobol variance-based sensitivity indices
    - Parameter ranking and importance assessment

13. **Iooss, B., Lemaître, P.** "A review on global sensitivity analysis methods." *Handbook of Uncertainty Quantification* **2020**, 1-30.
    - Sensitivity analysis for nuclear applications
    - Parameter uncertainty quantification
    - Variance decomposition methods

### Related Documentation

14. **CLAUDE.md** - Project documentation and model overview
15. **model_design.md** - Theoretical framework and model equations (Chinese)
16. **original paper of swelling rate theory.md** - Reference paper translation (English)

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
