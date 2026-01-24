# Gas Swelling Rate Theory: Model Documentation

## Table of Contents

1. [Introduction and Overview](#1-introduction-and-overview)
2. [Model Architecture and State Variables](#2-model-architecture-and-state-variables)
3. [Gas Transport Equations](#3-gas-transport-equations)
4. [Defect Kinetics Equations](#4-defect-kinetics-equations)
5. [Cavity Growth Mechanisms](#5-cavity-growth-mechanisms)
6. [Model Assumptions and Validity Range](#6-model-assumptions-and-validity-range)
7. [Validation Against Experimental Data](#7-validation-against-experimental-data)
8. [Parameter Reference](#8-parameter-reference)
9. [References and Bibliography](#9-references-and-bibliography)

---

## 1. Introduction and Overview

### 1.1 Purpose of This Document

This documentation provides a comprehensive explanation of the **Gas Swelling Rate Theory Model** for metallic nuclear fuels (U-Zr and U-Pu-Zr alloys). The model implements the theoretical framework developed in the research paper *"Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel."*

The intended audience for this document includes:
- **Students** learning about nuclear fuel behavior and fission gas swelling
- **Researchers** working on metallic fuel performance modeling
- **Engineers** needing to understand model assumptions and limitations
- **Anyone** interested in the physics of radiation damage and cavity evolution

This document serves as both an educational resource and a technical reference for the implementation found in `modelrk23.py`.

### 1.2 What is Gas Swelling?

**Gas swelling** is a critical phenomenon in nuclear fuel materials where fission gas atoms (primarily xenon and krypton) precipitate to form bubbles within the fuel matrix. These bubbles grow over time, causing volumetric expansion (swelling) that can:

- Deform fuel cladding and compromise structural integrity
- Reduce thermal conductivity
- Create pathways for fission gas release
- Impact fuel performance and safety margins

Understanding and predicting gas swelling is essential for:
- Designing safe nuclear reactor fuel assemblies
- Determining fuel burnup limits
- Optimizing fuel composition and microstructure
- Licensing new fuel types for regulatory approval

### 1.3 The Rate Theory Approach

This model uses **rate theory** to describe the evolution of fission gas bubbles and voids. Rate theory tracks the concentrations of various species (gas atoms, vacancies, interstitials, cavities) over time by balancing:

- **Production**: Creation of defects and gas atoms during fission
- **Transport**: Diffusion through the bulk and to grain boundaries
- **Reaction**: Recombination of vacancies and interstitials
- **Annihilation**: Absorption at sinks (dislocations, cavities, boundaries)
- **Nucleation**: Formation of new cavities
- **Growth**: Expansion of existing cavities

The model solves a system of **10 coupled ordinary differential equations (ODEs)** that describe the time evolution of:
- Gas atom concentrations in bulk and at grain boundaries
- Cavity (bubble) concentrations in bulk and at boundaries
- Gas atoms per cavity in bulk and at boundaries
- Vacancy and interstitial concentrations in bulk and at boundaries

### 1.4 Key Physical Mechanisms

The model captures two distinct regimes of cavity growth:

#### Gas-Driven Growth (Overpressurized Bubbles)
- Small cavities with high internal gas pressure
- Gas pressure exceeds surface tension: \(P_{gas} > \frac{2\gamma}{R}\)
- Growth driven by vacancy influx due to **excess pressure** (\(P_{ex} > 0\))
- Dominates early stages of swelling
- Typical bubble radii: nanometer scale

#### Bias-Driven Growth (Underpressurized Voids)
- Larger cavities with low internal pressure
- Surface tension dominates: \(P_{gas} < \frac{2\gamma}{R}\)
- Growth driven by **dislocation bias**—interstitials are preferentially absorbed at dislocations, leaving a net vacancy flux to voids
- Dominates later stages of high-burnup swelling
- Typical void radii: micrometer scale

The **critical radius** \(R_c = \frac{2\gamma}{P_{gas}}\) separates these two regimes:
- \(R < R_c\): Gas-driven (overpressurized)
- \(R > R_c\): Bias-driven (underpressurized)

### 1.5 Model Scope and Applications

This rate theory model specifically addresses:

**Fuel Types:**
- U-Zr alloys (e.g., U-10Zr)
- U-Pu-Zr alloys (e.g., U-19Pu-10Zr)
- High-purity uranium (for validation)

**Phase:**
- α-uranium phase (orthorhombic crystal structure)
- Temperature range: 673-935 K (400-662°C)

**Phenomena Modeled:**
- Fission gas production and diffusion
- Bubble nucleation in grains and at grain boundaries
- Cavity growth by vacancy absorption
- Gas-driven to bias-driven growth transition
- Fission gas release via interconnected bubble networks
- Void swelling (volumetric strain)
- Temperature-dependent swelling behavior
- Burnup-dependent swelling rates

**Model Outputs:**
- Time evolution of all state variables
- Bubble radius distribution
- Gas pressure in cavities
- Swelling percentage vs. burnup
- Gas release fraction
- Cavity number density

### 1.6 Why This Model Matters

**Educational Value:**
- Provides a transparent, physics-based understanding of swelling mechanisms
- Unlike "black box" fuel performance codes, all equations and assumptions are documented
- Demonstrates the coupling between multiple physical processes
- Serves as a teaching tool for nuclear materials science

**Research Applications:**
- Validates against experimental data across multiple fuel compositions
- Enables parameter sensitivity studies
- Supports extrapolation to new fuel designs
- Provides a framework for model improvements

**Practical Utility:**
- Fast computation compared to atomistic simulations
- Captures essential physics without excessive complexity
- Suitable for engineering analysis and scoping studies
- Can be integrated into larger fuel performance codes

### 1.7 Document Organization

The remainder of this document is organized as follows:

- **Section 2**: Describes the 10 state variables and their physical meaning
- **Section 3**: Documents gas transport equations (Eqs. 1-8 from the paper)
- **Section 4**: Documents defect kinetics equations (Eqs. 17-20)
- **Section 5**: Explains cavity growth mechanisms and the gas-driven vs. bias-driven transition
- **Section 6**: Lists model assumptions and validity ranges
- **Section 7**: Shows validation against experimental data
- **Section 8**: Provides a comprehensive parameter reference table
- **Section 9**: Lists references to the original paper and related literature

---

## 2. Model Architecture and State Variables

### 2.1 Overview of the State Vector

The Gas Swelling Model solves a system of **10 coupled ordinary differential equations (ODEs)** that track the time evolution of fission gas behavior in metallic nuclear fuels. The state variables are divided into two domains:

- **Bulk Matrix (subscript 'b')**: Phenomena occurring within the grain interior
- **Phase Boundaries (subscript 'f')**: Phenomena occurring at grain boundaries and interfaces

This dual-domain approach is essential because:
1. **Gas atoms diffuse from grain interiors to boundaries** where they accumulate
2. **Bubble nucleation and growth rates differ** between bulk and boundary environments
3. **Gas release occurs primarily at boundaries** when bubbles interconnect
4. **Defect concentrations and sink strengths vary** between bulk and boundary regions

The 10 state variables represent the minimum set of quantities needed to capture the essential physics of fission gas swelling, while keeping the model computationally tractable.

### 2.2 Bulk Matrix State Variables (5 variables)

#### Variable 1: Cgb - Gas Atom Concentration in Bulk

**Symbol**: \( C_{gb} \)
**Units**: atoms/m³
**Physical Meaning**: Concentration of fission gas atoms (primarily Xe and Kr) dissolved in the metal matrix within grain interiors.

**Role in the Model**:
- **Source**: Gas atoms are produced during nuclear fission and enter the matrix
- **Transport**: Diffuses toward grain boundaries with diffusivity \( D_{gb} \)
- **Sink**: Provides gas atoms to bubbles in the bulk via nucleation and growth
- **Coupling**: Appears in the gas diffusion equation (Eq. 1) and couples to Ccb (bulk cavity concentration) and Ncb (gas atoms per cavity)

**Typical Values**: Ranges from 10²⁴ to 10²⁶ atoms/m³ depending on fission rate and burnup

**Equation**:
\[
\frac{dC_{gb}}{dt} = y_{gas}\sigma_f\phi - \frac{12}{d^2}D_{gb}(C_{gb} - C_{gf}) - \text{nucleation and growth terms}
\]

---

#### Variable 2: Ccb - Cavity Concentration in Bulk

**Symbol**: \( C_{cb} \)
**Units**: cavities/m³
**Physical Meaning**: Number density of cavities (bubbles) per unit volume within the grain interior.

**Role in the Model**:
- **Nucleation**: New cavities form when gas atoms cluster and reach critical size
- **Growth/Shrinkage**: Cavity concentration changes due to nucleation, coalescence, and dissolution
- **Sink Strength**: Determines the effectiveness of cavities as sinks for vacancies and gas atoms
- **Coupling**: Directly affects vacancy concentration (cvb) through sink strength calculation \( k_v^2 = 4\pi R C_c \)

**Typical Values**: 10²⁰ to 10²³ cavities/m³

**Key Relationship**:
\[
k_{vc2}^2 = 4\pi R_{cb} C_{cb}(1 + k_v R_{cb})
\]
where \( k_{vc2}^2 \) is the cavity sink strength for vacancies.

---

#### Variable 3: Ncb - Gas Atoms per Bulk Cavity

**Symbol**: \( N_{cb} \)
**Units**: atoms/cavity
**Physical Meaning**: Average number of gas atoms contained in each bulk cavity.

**Role in the Model**:
- **Growth Metric**: Tracks how much gas each cavity has absorbed over time
- **Pressure Calculation**: Determines internal gas pressure via equation of state (ideal or Van der Waals)
- **Radius Calculation**: Cavity radius \( R_{cb} \) is derived from \( N_{cb} \) using mechanical equilibrium
- **Coupling**: Couples to Cgb (gas concentration), Ccb (cavity concentration), and cvb (vacancy concentration)

**Typical Values**: Ranges from a few atoms (nucleation stage) to millions of atoms (mature bubbles)

**Key Relationship** (Mechanical Equilibrium):
\[
P_{gas} = \frac{2\gamma}{R_{cb}} + \sigma_{ext}
\]
where \( P_{gas} \) is calculated from \( N_{cb} \) and \( R_{cb} \), \( \gamma \) is surface energy, and \( \sigma_{ext} \) is external hydrostatic pressure.

**Derived Quantity**: Cavity radius \( R_{cb} \) is computed from \( N_{cb} \) iteratively, not stored as a state variable.

---

#### Variable 4: cvb - Vacancy Concentration in Bulk

**Symbol**: \( c_{vb} \)
**Units**: dimensionless (atomic fraction)
**Physical Meaning**: Concentration of vacant lattice sites in the grain interior.

**Role in the Model**:
- **Cavity Growth**: Vacancies absorbed by cavities cause them to grow (volume increase)
- **Recombination**: Recombines with interstitials (cib), removing both from the system
- **Supersaturation**: Drives vacancy diffusion to cavities
- **Coupling**: Strongly coupled to cib (recombination), Ccb (sink strength), and Ncb (growth rate)

**Typical Values**: 10⁻⁸ to 10⁻⁶ (atomic fraction), significantly above thermal equilibrium under irradiation

**Equation** (Defect Kinetics):
\[
\frac{dc_{vb}}{dt} = \phi - k_v^2 D_v c_{vb} - \alpha c_{vb}c_{ib}
\]
where:
- \( \phi \) is the defect production rate (Frenkel pairs)
- \( k_v^2 \) is total vacancy sink strength (dislocations + cavities)
- \( D_v \) is vacancy diffusivity
- \( \alpha \) is recombination coefficient
- \( c_{ib} \) is interstitial concentration

**Key Coupling**: Vacancy concentration at cavity surface \( c_v^* \) differs from bulk concentration:
\[
c_v^* = c_{vb} \exp\left(-\frac{P_{ex}\Omega}{k_B T}\right)
\]
where \( P_{ex} = P_{gas} - \frac{2\gamma}{R} - \sigma_{ext} \) is excess pressure.

---

#### Variable 5: cib - Interstitial Concentration in Bulk

**Symbol**: \( c_{ib} \)
**Units**: dimensionless (atomic fraction)
**Physical Meaning**: Concentration of interstitial atoms in the grain interior.

**Role in the Model**:
- **Recombination**: Recombines with vacancies (cvb), removing both from the system
- **Bias Effect**: Dislocations preferentially absorb interstitials over vacancies (Zᵢ > Zᵥ), creating vacancy supersaturation
- **Shrinkage**: If absorbed by cavities, causes them to shrink (unlikely due to bias)
- **Coupling**: Strongly coupled to cvb (recombination) and affects cavity growth through vacancy supersaturation

**Typical Values**: 10⁻¹⁰ to 10⁻⁸ (atomic fraction), generally lower than vacancy concentration

**Equation** (Defect Kinetics):
\[
\frac{dc_{ib}}{dt} = \phi - k_i^2 D_i c_{ib} - \alpha c_{vb}c_{ib}
\]
where:
- \( k_i^2 \) is total interstitial sink strength (dislocations + cavities)
- \( D_i \) is interstitial diffusivity (typically >> Dᵥ)

**Dislocation Bias**: The key mechanism driving void swelling:
\[
k_i^2 = Z_i \rho, \quad k_v^2 = Z_v \rho
\]
where \( Z_i > Z_v \) (typically 1.0-1.2 vs 1.0), causing preferential interstitial absorption at dislocations.

---

### 2.3 Phase Boundary State Variables (5 variables)

#### Variable 6: Cgf - Gas Atom Concentration at Boundaries

**Symbol**: \( C_{gf} \)
**Units**: atoms/m³
**Physical Meaning**: Concentration of fission gas atoms that have diffused to and accumulated at grain boundaries or phase interfaces.

**Role in the Model**:
- **Source**: Receives gas atoms diffusing from bulk (Cgb)
- **Sink**: Provides gas to boundary cavities (Ccf, Ncf)
- **Release**: Primary pathway for fission gas release when cavities interconnect
- **Coupling**: Couples to Cgb (diffusion source), Ccf (boundary cavities), and Ncf (gas per cavity)

**Typical Values**: Can reach 10²⁶-10²⁷ atoms/m³ at grain boundaries due to accumulation

**Equation**:
\[
\frac{dC_{gf}}{dt} = \frac{12}{d^2}D_{gb}(C_{gb} - C_{gf}) - \text{nucleation, growth, and release terms}
\]

**Gas Release**: When boundary bubble area fraction exceeds threshold (~90%), gas is released:
\[
\frac{dC_{gf}}{dt}\bigg|_{release} = -\chi(C_{gf} + C_{cf}N_{cf})
\]
where \( \chi \) is interconnection coefficient.

---

#### Variable 7: Ccf - Cavity Concentration at Boundaries

**Symbol**: \( C_{cf} \)
**Units**: cavities/m² (areal density at boundaries)
**Physical Meaning**: Number density of cavities per unit area at grain boundaries or phase interfaces.

**Role in the Model**:
- **Lenticular Shape**: Boundary cavities are lens-shaped (different from spherical bulk cavities)
- **Higher Density**: Typically higher concentration than bulk cavities due to enhanced nucleation at boundaries
- **Interconnection**: Forms percolating network leading to gas release
- **Coupling**: Affects boundary vacancy concentration (cvf) and gas release calculations

**Typical Values**: 10¹⁴ to 10¹⁶ cavities/m² (boundary area)

**Geometric Factor**:
\[
A_f = \pi R_{cf}^2 C_{cf} f_f(\theta)
\]
where \( f_f(\theta) \) accounts for lenticular shape and \( \theta \) is the dihedral angle.

---

#### Variable 8: Ncf - Gas Atoms per Boundary Cavity

**Symbol**: \( N_{cf} \)
**Units**: atoms/cavity
**Physical Meaning**: Average number of gas atoms contained in each boundary cavity.

**Role in the Model**:
- **Growth Metric**: Tracks gas accumulation in boundary bubbles
- **Pressure Calculation**: Determines internal gas pressure (similar to Ncb)
- **Radius Calculation**: Boundary cavity radius \( R_{cf} \) derived from \( N_{cf} \)
- **Coupling**: Couples to Cgf (boundary gas concentration), Ccf (cavity concentration), and cvf (boundary vacancy concentration)

**Typical Values**: Generally higher than Ncb due to preferential gas diffusion to boundaries

**Key Difference from Bulk**: Boundary cavities have different geometry (lens-shaped vs spherical), affecting the relationship between Ncf, Rcf, and pressure.

---

#### Variable 9: cvf - Vacancy Concentration at Boundaries

**Symbol**: \( c_{vf} \)
**Units**: dimensionless (atomic fraction)
**Physical Meaning**: Concentration of vacant lattice sites at grain boundaries or phase interfaces.

**Role in the Model**:
- **Boundary Cavity Growth**: Vacancies absorbed by boundary cavities cause their growth
- **Enhanced Diffusion**: Grain boundaries act as fast diffusion pathways for vacancies
- **Sink Strength**: Different sink strength than bulk due to boundary geometry
- **Coupling**: Coupled to cif (boundary interstitials), Ccf (boundary cavities), and Ncf (boundary cavity growth)

**Typical Values**: Similar order of magnitude to cvb but can differ due to boundary effects

**Equation** (similar to bulk):
\[
\frac{dc_{vf}}{dt} = \phi - k_{vf}^2 D_v c_{vf} - \alpha c_{vf}c_{if}
\]
where \( k_{vf}^2 \) includes boundary-specific sink strengths.

---

#### Variable 10: cif - Interstitial Concentration at Boundaries

**Symbol**: \( c_{if} \)
**Units**: dimensionless (atomic fraction)
**Physical Meaning**: Concentration of interstitial atoms at grain boundaries or phase interfaces.

**Role in the Model**:
- **Recombination**: Recombines with boundary vacancies (cvf)
- **Bias Effect**: Dislocations at boundaries also preferentially absorb interstitials
- **Coupling**: Strongly coupled to cvf and affects boundary cavity growth through vacancy supersaturation

**Typical Values**: Similar order of magnitude to cib

**Equation** (similar to bulk):
\[
\frac{dc_{if}}{dt} = \phi - k_{if}^2 D_i c_{if} - \alpha c_{vf}c_{if}
\]

---

### 2.4 Variable Coupling and System Dynamics

#### Coupling Diagram

The 10 state variables are highly coupled through the following mechanisms:

**Gas Transport**:
\[
C_{gb} \rightleftharpoons C_{gf}
\]
Gas atoms diffuse from bulk to boundaries, creating concentration gradients.

**Bubble Growth**:
\[
C_{gb} \rightarrow N_{cb}, \quad C_{gf} \rightarrow N_{cf}
\]
Gas concentration decreases as atoms are absorbed into cavities.

**Cavity-Vacancy Coupling**:
\[
c_{vb}, c_{vf} \rightarrow N_{cb}, N_{cf}
\]
Vacancy absorption increases Nc (atoms per cavity), which increases radius.

**Defect Recombination**:
\[
c_{vb} \rightleftharpoons c_{ib}, \quad c_{vf} \rightleftharpoons c_{if}
\]
Vacancies and interstitials recombine, removing both from the system.

**Sink Strength Feedback**:
\[
C_{cb}, C_{cf} \rightarrow k_v^2, k_i^2 \rightarrow c_{vb}, c_{ib}
\]
Cavity concentration affects sink strengths, which control defect concentrations.

#### Derived Quantities

While not state variables, these quantities are calculated from the state variables at each time step:

1. **Cavity Radius** (\( R_{cb}, R_{cf} \)): Derived from Ncb, Ncf using mechanical equilibrium
2. **Gas Pressure** (\( P_{gas} \)): Derived from Ncb/Ncf and radius using equation of state
3. **Swelling Strain**: \( S = \frac{4}{3}\pi R_{cb}^3 C_{cb} + \frac{4}{3}\pi R_{cf}^3 C_{cf} \)
4. **Sink Strengths** (\( k_v^2, k_i^2 \)): Derived from cavity concentrations and radii

#### Timescale Separation

The system exhibits widely varying timescales:
- **Fast** (microseconds): Defect recombination (cv·ci terms)
- **Medium** (seconds to minutes): Gas diffusion, cavity nucleation
- **Slow** (hours to days): Cavity growth, swelling accumulation

This stiffness necessitates careful numerical methods (RK23 with adaptive stepping) and creates numerical challenges in solving the coupled ODE system.

---

### 2.5 Initial Conditions

At time \( t = 0 \) (start of irradiation), the state variables are initialized as follows:

| Variable | Initial Value | Physical Rationale |
|----------|--------------|-------------------|
| Cgb, Cgf | 0 atoms/m³ | No gas present before irradiation begins |
| Ccb, Ccf | 0 cavities/m³ | No cavities before nucleation |
| Ncb, Ncf | 5 atoms/cavity | Small critical nucleus size |
| cvb, cvf | \( c_v^0(T) \) | Thermal equilibrium vacancy concentration |
| cib, cif | \( c_i^0(T) \) | Thermal equilibrium interstitial concentration |

The thermal equilibrium concentrations are calculated from Arrhenius expressions:
\[
c_v^0 = \exp\left(-\frac{E_f^v}{k_B T}\right), \quad c_i^0 = \exp\left(-\frac{E_f^i}{k_B T}\right)
\]

Under irradiation, defect concentrations rapidly increase to steady-state values (~10⁻⁸ to 10⁻⁶) within microseconds, driving the subsequent evolution of gas behavior and cavity growth.

---

### 2.6 Summary Table

| Index | Variable | Symbol | Units | Domain | Physical Meaning |
|-------|----------|--------|-------|--------|------------------|
| 1 | Cgb | \( C_{gb} \) | atoms/m³ | Bulk | Gas atom concentration in grain interior |
| 2 | Ccb | \( C_{cb} \) | cavities/m³ | Bulk | Cavity (bubble) number density in bulk |
| 3 | Ncb | \( N_{cb} \) | atoms/cavity | Bulk | Gas atoms per bulk cavity |
| 4 | cvb | \( c_{vb} \) | dimensionless | Bulk | Vacancy concentration in bulk |
| 5 | cib | \( c_{ib} \) | dimensionless | Bulk | Interstitial concentration in bulk |
| 6 | Cgf | \( C_{gf} \) | atoms/m³ | Boundary | Gas atom concentration at grain boundaries |
| 7 | Ccf | \( C_{cf} \) | cavities/m² | Boundary | Cavity number density at boundaries |
| 8 | Ncf | \( N_{cf} \) | atoms/cavity | Boundary | Gas atoms per boundary cavity |
| 9 | cvf | \( c_{vf} \) | dimensionless | Boundary | Vacancy concentration at boundaries |
| 10 | cif | \( c_{if} \) | dimensionless | Boundary | Interstitial concentration at boundaries |

**Note**: Radius variables (Rcb, Rcf) are **not** independent state variables. They are derived quantities calculated from Ncb and Ncf using the mechanical equilibrium condition between gas pressure and surface tension.

---

## 3. Gas Transport Equations

### 3.1 Overview of Gas Transport

Gas transport in the α-uranium phase of metallic nuclear fuels involves the movement of fission gas atoms (primarily xenon and krypton) from their production sites in the fuel matrix to grain boundaries, where they accumulate in bubbles and may eventually be released. The transport process is governed by a system of **8 coupled differential equations** (Eqs. 1-8) that describe:

1. **Gas production** during nuclear fission
2. **Diffusion** through the bulk matrix to grain boundaries
3. **Nucleation** of new gas bubbles
4. **Growth** of existing bubbles by gas absorption
5. **Re-solution** of gas atoms back into the matrix due to fission fragments
6. **Release** when bubble networks interconnect

These equations form the foundation of the rate theory model and are implemented in the `GasSwellingModel._equations()` method in `modelrk23.py`.

The gas transport equations are divided into two domains:
- **Bulk (superscript 'b')**: Gas behavior within the grain interior
- **Phase Boundaries (superscript 'f')**: Gas behavior at grain boundaries and interfaces

---

### 3.2 Equation 1: Gas Transport in the Bulk Matrix

#### Mathematical Form

$$
\frac{dC_{g}^{b}}{dt} = -16\pi F_{n}^{b} R_{c}^{b} D_{g}^{b} C_{g}^{b} C_{g}^{b} - 4\pi R_{c}^{b} D_{g}^{b} C_{g}^{b} C_{c}^{b} - \dot{g}_{0}(t) + \beta\dot{f} + B N_{c}^{b} C_{c}^{b}
\tag{1}
$$

#### Physical Meaning of Each Term

| Term | Mathematical Expression | Physical Meaning | Sign Convention |
|------|------------------------|------------------|-----------------|
| **Term 1** | \(-16\pi F_{n}^{b} R_{c}^{b} D_{g}^{b} C_{g}^{b} C_{g}^{b}\) | Loss of gas atoms due to **bubble nucleation** in the bulk. When two gas atoms collide, they may form a stable bubble nucleus. | Negative (loss) |
| **Term 2** | \(-4\pi R_{c}^{b} D_{g}^{b} C_{g}^{b} C_{c}^{b}\) | Loss of gas atoms due to **diffusion to existing cavities**. Gas atoms are absorbed by the surfaces of existing bubbles. | Negative (loss) |
| **Term 3** | \(-\dot{g}_{0}(t)\) | Loss of gas atoms due to **diffusion to grain boundaries**. Gas atoms migrate from the bulk to the phase boundaries. | Negative (loss) |
| **Term 4** | \(+\beta\dot{f}\) | **Production of gas atoms** by nuclear fission. Each fission event produces a yield \(\beta\) of gas atoms. | Positive (source) |
| **Term 5** | \(+B N_{c}^{b} C_{c}^{b}\) | **Re-solution of gas atoms** from bubbles back into the matrix. Fission fragments passing through bubbles knock gas atoms back into solution. | Positive (source) |

#### Parameter Definitions

- \(C_{g}^{b}\): Gas atom concentration in bulk (atoms/m³)
- \(C_{c}^{b}\): Cavity (bubble) concentration in bulk (cavities/m³)
- \(R_{c}^{b}\): Average cavity radius in bulk (m)
- \(D_{g}^{b}\): Gas atom diffusivity in bulk (m²/s)
- \(F_{n}^{b}\): Nucleation factor (probability that two gas atoms form a stable nucleus)
- \(N_{c}^{b}\): Gas atoms per cavity (atoms/cavity)
- \(\beta\): Gas yield per fission (atoms/fission)
- \(\dot{f}\): Fission rate (fissions/m³/s)
- \(B\): Irradiation-induced re-solution rate (s⁻¹)
- \(\dot{g}_{0}(t)\): Gas flux to grain boundaries (atoms/m³/s), defined in Eq. 2

#### Code Implementation

**Location**: `modelrk23.py`, lines 333-344

```python
# Gas production rate from fission
term4_Cgb = self.params['gas_production_rate'] * self.params['fission_rate']

# Bubble nucleation (Term 1)
term1_Cgb = -16 * np.pi * self.params['Fnb'] * self.params['Xe_radii'] * Dgb * Cgb**2

# Diffusion to existing cavities (Term 2)
term2_Cgb = -4 * np.pi * Rcb_safe * Dgb * Cgb * Ccb

# Diffusion to grain boundaries (Term 3)
term3_Cgb = -g0  # g0 is calculated by _gas_influx()

# Re-solution from bubbles (Term 5)
term5_Cgb = self.params['resolution_rate'] * Ccb * Ncb

# Combine all terms
dCgb_dt = term1_Cgb + term2_Cgb + term3_Cgb + term4_Cgb + term5_Cgb
```

**Key Implementation Details**:
- The nucleation factor `Fnb` is multiplied by `Xe_radii` (approximate critical nucleus radius)
- The gas flux `g0` is computed by the `_gas_influx()` method (see Eq. 2 documentation)
- Numerical clipping is applied to prevent overflow: `np.clip(dCgb_dt, -1e20, 1e20)`

#### Physical Interpretation

**Equation 1 represents the mass balance for gas atoms in the bulk matrix**. It accounts for all sources and sinks of gas atoms:

1. **Source**: Fission continuously produces gas atoms at rate \(\beta\dot{f}\)
2. **Sinks**:
   - Nucleation removes gas atoms to form new bubbles
   - Existing bubbles absorb gas atoms from solution
   - Diffusion to boundaries removes gas atoms from the bulk
3. **Re-solution**: Acts as a source, returning gas atoms from bubbles to the matrix

**Competition Between Processes**:
- At early times: Nucleation dominates (Term 1), creating many small bubbles
- At intermediate times: Growth dominates (Term 2), existing bubbles absorb gas
- At late times: Boundary diffusion dominates (Term 3), most gas reaches boundaries
- Re-solution (Term 5) opposes nucleation and growth, keeping small bubbles from forming

#### Typical Values and Scaling

| Quantity | Typical Value | Units | Notes |
|----------|---------------|-------|-------|
| \(\beta\dot{f}\) | 10²⁰ - 10²² | atoms/m³/s | Depends on fission rate |
| \(D_{g}^{b}\) | 10⁻²⁰ - 10⁻¹⁶ | m²/s | Strong temperature dependence |
| \(F_{n}^{b}\) | 10⁻³ - 10⁻¹ | dimensionless | Nucleation probability |
| \(B\) | 10⁻⁸ - 10⁻⁶ | s⁻¹ | Re-solution rate |

---

### 3.3 Equation 2: Gas Flux to Grain Boundaries

#### Mathematical Form

$$
\dot{g}_{0}(t) = -\frac{6}{d} \frac{D_{g}^{b} C_{g}^{b}}{\partial r} \bigg|_{r=d/2}
\tag{2}
$$

#### Physical Meaning

**Equation 2 describes the flux of gas atoms from the grain interior to the grain boundaries**. The flux is driven by the concentration gradient of gas atoms between the bulk and the boundary.

**Approximation in the Model**:
The grain is split into two concentric regions of approximately equal volume. In each region, the gas concentration is represented by a quadratic function of the radial coordinate. This simplification allows an analytical expression for the flux:

$$
\dot{g}_{0}(t) \approx \frac{12}{d^2} D_{g}^{b} (C_{g}^{b} - C_{g}^{f})
$$

where:
- \(d\) is the grain diameter
- \(C_{g}^{b}\) is the gas concentration in the bulk center
- \(C_{g}^{f}\) is the gas concentration at the boundary

#### Parameter Definitions

- \(d\): Grain diameter (m), typically 1-2 μm for α-uranium
- \(r\): Radial coordinate (m)
- \(D_{g}^{b}\): Gas diffusivity in bulk (m²/s)
- \(C_{g}^{b}\): Gas concentration in bulk (atoms/m³)
- \(C_{g}^{f}\): Gas concentration at boundary (atoms/m³)

#### Code Implementation

**Location**: `modelrk23.py`, lines 58-61

```python
def _gas_influx(self, Cgb: float, Cgf: float) -> float:
    """计算从基体扩散到相界面的气体原子通量(公式2)"""
    return (12.0 / (self.params['grain_diameter'])**2) * self.params['Dgb'] * (Cgb - Cgf)
```

**Key Implementation Details**:
- Uses the simplified analytical form: \(\frac{12}{d^2} D_{gb} (C_{gb} - C_{gf})\)
- The concentration gradient \((C_{gb} - C_{gf})\) drives the flux
- When \(C_{gb} > C_{gf}\): Gas flows from bulk to boundary (positive flux)
- When \(C_{gb} < C_{gf}\): Gas flows from boundary to bulk (negative flux, unlikely in practice)

#### Physical Interpretation

**Diffusion-Limited Transport**:
- The flux is proportional to the gas diffusivity \(D_{g}^{b}\)
- Higher temperatures → higher diffusivity → faster gas transport to boundaries
- Smaller grains → larger surface-to-volume ratio → faster gas removal

**Steady-State vs. Transient**:
- Under steady-state conditions: \(C_{g}^{f}\) remains much lower than \(C_{g}^{b}\)
- The flux is nearly constant after initial transient
- At very high burnup: \(C_{g}^{f}\) may approach \(C_{g}^{b}\), reducing the flux

#### Coupling to Other Equations

**Eq. 2 appears in**:
- **Eq. 1** (Term 3): Gas loss from bulk to boundaries
- **Eq. 6** (Term 3): Gas gain at boundaries from bulk

This coupling ensures mass conservation: gas atoms leaving the bulk (Eq. 1) appear at the boundaries (Eq. 6).

---

### 3.4 Equation 3: Cavity Nucleation in the Bulk

#### Mathematical Form

$$
\frac{dC_{c}^{b}}{dt} = \frac{16\pi F_{n}^{b} R_{c}^{b} D_{g}^{b} C_{g}^{b} C_{g}^{b}}{N_{c}^{b}}
\tag{3}
$$

#### Physical Meaning

**Equation 3 describes the rate of formation of new cavities (bubbles) in the bulk matrix**. When gas atoms cluster together, they can form a stable bubble nucleus if the cluster reaches a critical size.

**Key Insight**: The numerator is identical to Term 1 of Eq. 1 (bubble nucleation rate), but divided by \(N_{c}^{b}\) (atoms per cavity). This division converts the rate of gas atom consumption into the rate of cavity formation.

#### Parameter Definitions

- \(C_{c}^{b}\): Cavity concentration in bulk (cavities/m³)
- \(F_{n}^{b}\): Nucleation factor (probability of stable nucleus formation)
- \(R_{c}^{b}\): Critical nucleus radius (m)
- \(D_{g}^{b}\): Gas diffusivity (m²/s)
- \(C_{g}^{b}\): Gas concentration (atoms/m³)
- \(N_{c}^{b}\): Gas atoms per cavity (atoms/cavity)

#### Code Implementation

**Location**: `modelrk23.py`, lines 346-348

```python
# Bulk cavity concentration rate (dCcb/dt - Eq. 3)
Ncb_safe_denom = max(Ncb, 2)  # Prevent division by zero
dCcb_dt = (16 * np.pi * self.params['Fnb'] * self.params['Xe_radii'] * Dgb * Cgb**2) / Ncb_safe_denom
```

**Key Implementation Details**:
- The denominator `Ncb_safe_denom` is clipped to a minimum of 2 to prevent division by zero
- `Xe_radii` (approximately the critical nucleus radius) is used for \(R_{c}^{b}\)
- The nucleation rate is proportional to the **square** of gas concentration (\(C_{gb}^2\)), reflecting the bimolecular nature of nucleation (two gas atoms must meet)

#### Physical Interpretation

**Nucleation Threshold**:
- Not every gas atom collision produces a stable cavity
- The nucleation factor \(F_{n}^{b}\) captures the probability of forming a stable nucleus
- Small values of \(F_{n}^{b}\) (10⁻³ - 10⁻¹) indicate that nucleation is a rare event

**Dependence on Gas Concentration**:
- Higher \(C_{g}^{b}\) → more gas atom collisions → more nucleation
- The quadratic dependence (\(C_{g}^{b} C_{g}^{b}\)) means nucleation is very sensitive to gas concentration

**Inverse Dependence on \(N_{c}^{b}\)**:
- As \(N_{c}^{b}\) increases (cavities accumulate gas), the nucleation rate decreases
- This reflects the fact that gas atoms are distributed among more cavities, reducing the probability of new nucleation events

**Nucleation vs. Growth**:
- Early in irradiation: \(N_{c}^{b}\) is small → high nucleation rate
- Later: \(N_{c}^{b}\) grows → nucleation slows, growth of existing cavities dominates

#### Typical Evolution

| Time | Nucleation Rate | Dominant Process |
|------|----------------|------------------|
| Early (< 1 day) | High | Many new bubbles form |
| Intermediate (days) | Moderate | Nucleation and growth compete |
| Late (weeks) | Low | Growth of existing bubbles dominates |

---

### 3.5 Equation 4: Conservation of Gas Atoms in Bulk

#### Mathematical Form

$$
N_{c}^{b} C_{c}^{b} + C_{g}^{b} + \int_0^t \dot{g}_{0}(t) \, dt = \int_0^t \beta \dot{f} \, dt
\tag{4}
$$

#### Physical Meaning

**Equation 4 is a statement of mass conservation for gas atoms in the bulk**. It states that the total number of gas atoms produced by fission must equal the sum of:

1. Gas atoms in bubbles: \(N_{c}^{b} C_{c}^{b}\) (atoms/cavity × cavities/m³)
2. Gas atoms in solution: \(C_{g}^{b}\) (dissolved in the matrix)
3. Gas atoms that have diffused to boundaries: \(\int_0^t \dot{g}_{0}(t) \, dt\)

This equation is **not solved directly** in the numerical implementation. Instead, it is used to derive Eq. 5 (rate of change of gas atoms per cavity).

#### Parameter Definitions

- \(N_{c}^{b}\): Gas atoms per cavity (atoms/cavity)
- \(C_{c}^{b}\): Cavity concentration (cavities/m³)
- \(C_{g}^{b}\): Gas concentration in bulk (atoms/m³)
- \(\dot{g}_{0}(t)\): Gas flux to boundaries (atoms/m³/s)
- \(\beta\dot{f}\): Gas production rate (atoms/m³/s)

#### Code Implementation

**Not directly implemented** as a separate equation. Instead, this conservation law is enforced by the coupled solution of Eqs. 1, 3, and 5.

**Verification**: The model can verify conservation by checking:
```python
total_gas_produced = integral(beta * fission_rate)
total_gas_accounted = Ncb * Ccb + Cgb + integral(g0)
```

#### Physical Interpretation

**Mass Balance Check**:
- Left side: Gas atoms currently in the system (in bubbles + in solution) + gas that left
- Right side: Total gas produced by fission
- If the two sides are equal, mass is conserved

**Role in Deriving Eq. 5**:
By differentiating Eq. 4 with respect to time and substituting Eqs. 1 and 3, we obtain Eq. 5 (rate of change of atoms per cavity). This ensures that the evolution of \(N_{c}^{b}\) is consistent with mass conservation.

#### Practical Significance

**Predicting Gas Release**:
- The term \(\int_0^t \dot{g}_{0}(t) \, dt\) represents gas that has reached the boundaries
- This gas is available for release once bubbles interconnect (see Eq. 9)
- Measuring the ratio \(\frac{\int_0^t \dot{g}_{0}(t) \, dt}{\int_0^t \beta \dot{f} \, dt}\) gives the fractional gas release

---

### 3.6 Equation 5: Gas Atoms per Bulk Cavity

#### Mathematical Form

$$
\frac{dN_{c}^{b}}{dt} = 4\pi R_{c}^{b} D_{g}^{b} C_{g}^{b} - B C_{c}^{b}
\tag{5}
$$

#### Physical Meaning

**Equation 5 describes how the number of gas atoms in each cavity changes over time**. It is derived from the conservation law (Eq. 4) and accounts for:

1. **Gain**: Gas atoms diffusing to the cavity surface and being absorbed
2. **Loss**: Gas atoms being knocked back into the matrix by fission fragments (re-solution)

#### Parameter Definitions

- \(N_{c}^{b}\): Gas atoms per cavity (atoms/cavity)
- \(R_{c}^{b}\): Cavity radius (m)
- \(D_{g}^{b}\): Gas diffusivity (m²/s)
- \(C_{g}^{b}\): Gas concentration in bulk (atoms/m³)
- \(B\): Re-solution rate (s⁻¹)
- \(C_{c}^{b}\): Cavity concentration (cavities/m³)

#### Code Implementation

**Location**: `modelrk23.py`, lines 350-355

```python
# Atoms per cavity rate (dNcb/dt - Eq. 5)
# Gas atoms diffusing to cavity surface
term1_Ncb = 4 * np.pi * Rcb_safe * Dgb * Cgb

# Re-solution from cavity
term2_Ncb = self.params['resolution_rate'] * Ncb

# Net rate of change
dNcb_dt = term1_Ncb - term2_Ncb
```

**Key Implementation Details**:
- Term 1: Absorption rate, proportional to cavity surface area \(4\pi R_{c}^{b}\)
- Term 2: Re-solution rate, proportional to the number of atoms in the cavity \(N_{c}^{b}\)
- Numerical clipping: `np.clip(dNcb_dt, -1e8, 1e8)` to prevent overflow

#### Physical Interpretation

**Absorption Term** (\(4\pi R_{c}^{b} D_{g}^{b} C_{g}^{b}\)):
- Larger cavities have larger surface area → absorb more gas
- Higher gas concentration → more flux to cavity surface
- Higher diffusivity → faster transport of gas atoms to cavity

**Re-solution Term** (\(B N_{c}^{b}\)):
- Cavities with more gas atoms lose more atoms to re-solution
- The re-solution rate \(B\) depends on fission rate (more fission fragments → more re-solution)
- Re-solution opposes cavity growth, especially for small bubbles

**Steady-State Condition**:
Setting \(dN_{c}^{b}/dt = 0\) gives:
$$
N_{c}^{b} = \frac{4\pi R_{c}^{b} D_{g}^{b} C_{g}^{b}}{B}
$$
This represents the balance between absorption and re-solution.

#### Impact on Cavity Growth

As \(N_{c}^{b}\) increases:
1. **Internal gas pressure increases** (via equation of state)
2. **Cavity radius increases** to maintain mechanical equilibrium
3. **Swelling increases** (volume occupied by cavities)

The evolution of \(N_{c}^{b}\) is therefore central to predicting swelling behavior.

---

### 3.7 Equation 6: Gas Transport at Phase Boundaries

#### Mathematical Form

$$
\frac{dC_{g}^{f}}{dt} = -16\pi F_{n}^{f} R_{c}^{f} D_{g}^{f} C_{g}^{f} C_{g}^{f} - 4\pi R_{c}^{f} D_{g}^{f} C_{g}^{f} C_{c}^{f} + \dot{g}_{0}(t) - \dot{h}_{0} C_{g}^{f}
\tag{6}
$$

#### Physical Meaning of Each Term

| Term | Mathematical Expression | Physical Meaning | Sign Convention |
|------|------------------------|------------------|-----------------|
| **Term 1** | \(-16\pi F_{n}^{f} R_{c}^{f} D_{g}^{f} C_{g}^{f} C_{g}^{f}\) | Loss of gas atoms due to **bubble nucleation at boundaries** | Negative (loss) |
| **Term 2** | \(-4\pi R_{c}^{f} D_{g}^{f} C_{g}^{f} C_{c}^{f}\) | Loss of gas atoms due to **absorption by existing boundary cavities** | Negative (loss) |
| **Term 3** | \(+\dot{g}_{0}(t)\) | **Gain of gas atoms** diffusing from the bulk to the boundary | Positive (source) |
| **Term 4** | \(-\dot{h}_{0} C_{g}^{f}\) | Loss of gas atoms due to **fission gas release** when bubbles interconnect | Negative (loss) |

#### Parameter Definitions

- \(C_{g}^{f}\): Gas atom concentration at boundaries (atoms/m³)
- \(C_{c}^{f}\): Cavity concentration at boundaries (cavities/m²)
- \(R_{c}^{f}\): Average boundary cavity radius (m)
- \(D_{g}^{f}\): Gas diffusivity at boundaries (m²/s)
- \(F_{n}^{f}\): Nucleation factor at boundaries
- \(\dot{g}_{0}(t)\): Gas flux from bulk to boundary (atoms/m³/s)
- \(\dot{h}_{0}\): Gas release rate coefficient (s⁻¹)

#### Code Implementation

**Location**: `modelrk23.py`, lines 357-367

```python
# Boundary gas concentration rate (dCgf/dt - Eq. 6)
# Nucleation at boundaries (Term 1)
term1_Cgf = -16 * np.pi * self.params['Fnf'] * self.params['Xe_radii'] * Dgf * Cgf**2

# Absorption by existing cavities (Term 2)
term2_Cgf = -4 * np.pi * Rcf_safe * Dgf * Cgf * Ccf

# Gas arriving from bulk (Term 3)
term3_Cgf = g0  # g0 calculated by _gas_influx()

# Gas release to plenum (Term 4)
term4_Cgf = h0 * Cgf  # h0 calculated by _calculate_gas_release_rate()

# Combine all terms
dCgf_dt = term1_Cgf + term2_Cgf + term3_Cgf - term4_Cgf
```

**Key Implementation Details**:
- Boundary diffusivity `Dgf` is typically a multiple of bulk diffusivity: `Dgf = multiplier * Dgb`
- The nucleation factor `Fnf` at boundaries is often larger than `Fnb` in bulk (boundaries enhance nucleation)
- Gas release `h0` is calculated by `_calculate_gas_release_rate()` based on cavity interconnection (see Eq. 9)

#### Physical Interpretation

**Boundary Accumulation**:
- Gas atoms continuously arrive from the bulk (Term 3: \(+\dot{g}_{0}\))
- This causes \(C_{g}^{f}\) to rise, creating a reservoir at the boundaries
- Boundary gas concentration can become much higher than bulk concentration

**Boundary Bubble Growth**:
- Nucleation (Term 1) creates new boundary bubbles
- Absorption (Term 2) causes existing bubbles to grow
- Boundary bubbles tend to be larger and more numerous than bulk bubbles

**Gas Release Threshold**:
- Release (Term 4) only begins when bubbles interconnect
- The term \(-\dot{h}_{0} C_{g}^{f}\) removes gas from the boundary and vents it to the plenum
- This term is zero until the interconnection threshold is reached (see Eq. 11)

#### Differences from Bulk (Eq. 1)

| Aspect | Bulk (Eq. 1) | Boundary (Eq. 6) |
|--------|--------------|------------------|
| Source term | \(\beta\dot{f}\) (fission production) | \(\dot{g}_{0}(t)\) (diffusion from bulk) |
| Re-solution | Present (\(+B N_{c}^{b} C_{c}^{b}\)) | Absent (boundary re-solution is negligible) |
| Release | Absent (bulk gas cannot escape directly) | Present (\(-\dot{h}_{0} C_{g}^{f}\)) |
| Nucleation factor | \(F_{n}^{b}\) (smaller) | \(F_{n}^{f}\) (larger, boundaries enhance nucleation) |

---

### 3.8 Equation 7: Cavity Nucleation at Phase Boundaries

#### Mathematical Form

$$
\frac{dC_{c}^{f}}{dt} = \frac{16\pi F_{n}^{f} R_{c}^{f} D_{g}^{f} C_{g}^{f} C_{g}^{f}}{N_{c}^{f}}
\tag{7}
$$

#### Physical Meaning

**Equation 7 describes the rate of formation of new cavities at grain boundaries**, analogous to Eq. 3 for the bulk. The form is identical, but all quantities refer to the boundary domain.

#### Parameter Definitions

- \(C_{c}^{f}\): Cavity concentration at boundaries (cavities/m²)
- \(F_{n}^{f}\): Nucleation factor at boundaries
- \(R_{c}^{f}\): Critical nucleus radius at boundaries (m)
- \(D_{g}^{f}\): Gas diffusivity at boundaries (m²/s)
- \(C_{g}^{f}\): Gas concentration at boundaries (atoms/m³)
- \(N_{c}^{f}\): Gas atoms per boundary cavity (atoms/cavity)

#### Code Implementation

**Location**: `modelrk23.py`, lines 369-371

```python
# Boundary cavity concentration rate (dCcf/dt - Eq. 7)
Ncf_safe_denom = max(Ncf, 2)  # Prevent division by zero
dCcf_dt = (16 * np.pi * self.params['Fnf'] * self.params['Xe_radii'] * Dgf * Cgf**2) / Ncf_safe_denom
```

**Key Implementation Details**:
- Structure is identical to bulk nucleation (Eq. 3)
- Uses boundary-specific parameters: `Fnf`, `Dgf`, `Cgf`, `Ncf`

#### Physical Interpretation

**Enhanced Nucleation at Boundaries**:
- Grain boundaries act as preferential nucleation sites
- \(F_{n}^{f}\) is typically larger than \(F_{n}^{b}\)
- Boundary cavities are more numerous than bulk cavities

**Lenticular Geometry**:
- Boundary cavities are lens-shaped (not spherical)
- This affects the relationship between \(N_{c}^{f}\) and cavity radius
- The simplified model uses spherical approximation for numerical efficiency

#### Coupling to Gas Release

As \(C_{c}^{f}\) increases:
1. More cavities cover the grain boundary area
2. The areal fraction \(A_{f}\) increases (see Eq. 10)
3. When \(A_{f}\) exceeds the threshold, gas release begins (Eq. 11)

---

### 3.9 Equation 8: Conservation of Gas Atoms at Boundaries

#### Mathematical Form

$$
N_{c}^{f} C_{c}^{f} + C_{g}^{f} = \int_0^t \dot{g}_{0}(t) \, dt - \int_0^t \dot{h}_{0}(t) \, dt
\tag{8}
$$

#### Physical Meaning

**Equation 8 is a statement of mass conservation for gas atoms at the grain boundaries**. It states that the gas atoms that have arrived from the bulk must equal the sum of:

1. Gas atoms in boundary bubbles: \(N_{c}^{f} C_{c}^{f}\)
2. Gas atoms in solution at boundaries: \(C_{g}^{f}\)
3. Gas atoms that have been released: \(\int_0^t \dot{h}_{0}(t) \, dt\)

#### Parameter Definitions

- \(N_{c}^{f}\): Gas atoms per boundary cavity (atoms/cavity)
- \(C_{c}^{f}\): Cavity concentration at boundaries (cavities/m²)
- \(C_{g}^{f}\): Gas concentration at boundaries (atoms/m³)
- \(\dot{g}_{0}(t)\): Gas flux from bulk to boundary (atoms/m³/s)
- \(\dot{h}_{0}(t)\): Gas release rate (atoms/m³/s)

#### Code Implementation

**Not directly implemented** as a separate equation. This conservation law is enforced by the coupled solution of Eqs. 6, 7, and 13.

**Derivation of Eq. 13**:
Differentiating Eq. 8 with respect to time and substituting Eqs. 6 and 7 yields Eq. 13 (rate of change of atoms per boundary cavity).

#### Physical Interpretation

**Boundary Mass Balance**:
- **Left side**: Gas atoms currently at boundaries (in bubbles + in solution)
- **Right side**: Total gas arrived from bulk minus total gas released

**Gas Release Fraction**:
The fractional gas release can be calculated as:
$$
F_{release} = \frac{\int_0^t \dot{h}_{0}(t) \, dt}{\int_0^t \dot{g}_{0}(t) \, dt}
$$

This ratio typically ranges from 0.7 to 0.8 (70-80% release) for U-Zr fuels at high burnup.

#### Coupling to Gas Release Equations

Eq. 8 is closely linked to Eqs. 9-12, which describe:
- **Eq. 9**: Gas release rate \(\dot{h}_{0}\)
- **Eq. 10**: Areal coverage of cavities \(A_{f}\)
- **Eq. 11**: Interconnection threshold
- **Eq. 12**: Fractional interconnection \(\chi\)

These equations determine when and how much gas is released, which appears in Eq. 8 as the term \(-\int_0^t \dot{h}_{0}(t) \, dt\).

---

### 3.10 Summary of Gas Transport Equations

#### Table of Equations 1-8

| Equation | Variable | Domain | Key Physical Process |
|----------|----------|--------|---------------------|
| **Eq. 1** | \(dC_{g}^{b}/dt\) | Bulk | Gas production, diffusion, nucleation, re-solution |
| **Eq. 2** | \(\dot{g}_{0}(t)\) | Bulk → Boundary | Gas flux to grain boundaries |
| **Eq. 3** | \(dC_{c}^{b}/dt\) | Bulk | Bubble nucleation in bulk |
| **Eq. 4** | Conservation | Bulk | Mass balance (not solved directly) |
| **Eq. 5** | \(dN_{c}^{b}/dt\) | Bulk | Gas atoms per bulk cavity |
| **Eq. 6** | \(dC_{g}^{f}/dt\) | Boundary | Gas accumulation, nucleation, release |
| **Eq. 7** | \(dC_{c}^{f}/dt\) | Boundary | Bubble nucleation at boundaries |
| **Eq. 8** | Conservation | Boundary | Mass balance at boundaries (not solved directly) |

#### Coupling Diagram

```
Fission Gas Production (βḟ)
        ↓
    Bulk Gas (Cgb) ←→ Diffusion (ġ₀) ←→ Boundary Gas (Cgf)
        ↓                      ↓                    ↓
    Bulk Cavities (Ccb)                  Boundary Cavities (Ccf)
        ↓                      ↓                    ↓
  Atoms/Bulk Cavity (Ncb)              Atoms/Boundary Cavity (Ncf)
        ↓                      ↓                    ↓
    ┌────────────────────────┴────────────────────────┘
    ↓
Gas Release (ḣ₀) → Plenum
```

#### Code Structure Mapping

The gas transport equations are implemented in the `_equations()` method:

```python
def _equations(self, t, state):
    # ... (setup code)

    # Eq. 2: Gas flux to boundaries
    g0 = self._gas_influx(Cgb, Cgf)

    # Eq. 9-12: Gas release rate
    h0 = self._calculate_gas_release_rate(Cgf, Ccf, Rcf, Ncf)

    # Eq. 1: Bulk gas concentration
    dCgb_dt = term1_Cgb + term2_Cgb + term3_Cgb + term4_Cgb + term5_Cgb

    # Eq. 3: Bulk cavity concentration
    dCcb_dt = (16 * np.pi * Fnb * Rc * Dgb * Cgb**2) / Ncb

    # Eq. 5: Gas atoms per bulk cavity
    dNcb_dt = 4 * np.pi * Rcb * Dgb * Cgb - B * Ncb

    # Eq. 6: Boundary gas concentration
    dCgf_dt = term1_Cgf + term2_Cgf + term3_Cgf - term4_Cgf

    # Eq. 7: Boundary cavity concentration
    dCcf_dt = (16 * np.pi * Fnf * Rc * Dgf * Cgf**2) / Ncf

    # Eq. 13: Gas atoms per boundary cavity
    dNcf_dt = 4 * np.pi * Rcf * Dgf * Cgf - h0 * Ncf

    return derivatives
```

---

### 3.11 Key Physical Insights from Gas Transport Equations

#### 1. Competition Between Nucleation and Growth

- **Early time**: High nucleation rate (many small bubbles form)
- **Late time**: Growth dominates (fewer bubbles, but larger)
- The division by \(N_{c}\) in Eqs. 3 and 7 causes this transition

#### 2. Role of Re-solution

- Re-solution (\(B N_{c}^{b} C_{c}^{b}\) in Eq. 1) returns gas atoms to the matrix
- This opposes bubble nucleation and growth
- Higher fission rates → more re-solution → smaller bubbles

#### 3. Boundary Accumulation

- Gas continuously flows from bulk to boundaries (\(\dot{g}_{0}\))
- Boundary gas concentration (\(C_{g}^{f}\)) can become very high
- This drives extensive boundary bubble growth

#### 4. Gas Release Threshold

- Release only begins when bubbles interconnect
- The threshold depends on areal coverage (Eq. 10)
- Before threshold: All gas remains at boundaries
- After threshold: Gas is released to the plenum

#### 5. Mass Conservation

- Eqs. 4 and 8 ensure mass conservation
- These are not solved directly but guide the derivation of Eqs. 5 and 13
- The numerical solution conserves mass by solving the coupled system

---

## 4. Defect Kinetics Equations

*[To be completed in subtask-1-4]*

---

## 5. Cavity Growth Mechanisms

*[To be completed in subtask-1-5]*

---

## 6. Model Assumptions and Validity Range

*[To be completed in subtask-1-6]*

---

## 7. Validation Against Experimental Data

*[To be completed in subtask-1-7]*

---

## 8. Parameter Reference

*[To be completed in subtask-1-9]*

---

## 9. References and Bibliography

*[To be completed in subtask-1-8]*
