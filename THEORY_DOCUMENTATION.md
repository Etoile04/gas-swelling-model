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

*[To be completed in subtask-1-3]*

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
