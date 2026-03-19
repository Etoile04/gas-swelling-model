# 1D Radial Gas Swelling Model: Theory and Implementation

> **Current implementation note**
>
> The repository still keeps the original fully coupled radial ODE formulation,
> and that is the focus of the theory discussion below. In day-to-day package
> usage, however, `RadialGasSwellingModel` now defaults to
> `radial_solver_mode='decoupled'` for practical turnaround, while
> `radial_solver_mode='coupled'` remains available when you explicitly want the
> coupled path.

## Table of Contents

1. [Introduction and Overview](#1-introduction-and-overview)
2. [Model Architecture and State Variables](#2-model-architecture-and-state-variables)
3. [Radial Mesh and Geometry](#3-radial-mesh-and-geometry)
4. [Radial Transport Equations](#4-radial-transport-equations)
5. [Temperature Profiles and Flux Depression](#5-temperature-profiles-and-flux-depression)
6. [Boundary Conditions](#6-boundary-conditions)
7. [Numerical Solution Method](#7-numerical-solution-method)
8. [Model Assumptions and Limitations](#8-model-assumptions-and-limitations)
9. [Comparison with 0D Model](#9-comparison-with-0d-model)
10. [Practical Usage Guide](#10-practical-usage-guide)
11. [References](#11-references)

---

## 1. Introduction and Overview

### 1.1 Purpose of the 1D Radial Model

The **1D Radial Gas Swelling Model** extends the 0D (single-point) rate theory model to capture spatial variations in fission gas behavior across the fuel pellet radius. In real nuclear fuel pins, temperature, fission rate, and gas concentrations vary significantly from the centerline to the surface, leading to non-uniform swelling distributions that affect fuel performance and safety margins.

This document explains the theoretical framework, numerical implementation, and practical usage of the 1D radial model, with emphasis on understanding its capabilities and limitations.

**Intended Audience:**
- Researchers extending the 0D model to spatially-resolved simulations
- Engineers assessing radial swelling distribution in fuel pins
- Students learning about spatial discretization in nuclear fuel modeling
- Anyone needing to understand when the 1D radial model is appropriate

### 1.2 Motivation for Spatial Resolution

The 0D model assumes uniform conditions throughout the fuel pellet, treating the entire volume as a single well-mixed reactor. While this provides useful average values, real fuel pins exhibit important spatial variations:

#### Temperature Gradients
- **Centerline**: Hottest region due to parabolic temperature profile
  - Typical centerline temperatures: 900-1200 K
  - Enhanced gas diffusion and bubble growth
  - Higher swelling rates

- **Surface**: Cooler region near cladding
  - Typical surface temperatures: 600-800 K
  - Reduced gas mobility
  - Lower swelling rates

**Impact**: Swelling can be 2-3× higher at the centerline compared to the surface, affecting fuel-cladding mechanical interaction (FCMI).

#### Flux Depression
- Neutron flux decreases toward the pellet center due to self-shielding
- Typical centerline flux is 60-80% of surface flux
- Reduces fission gas production in central regions
- Moderates swelling in the hottest region

**Impact**: Creates complex coupling where higher temperature promotes swelling but lower flux reduces gas production.

#### Gas Diffusion and Redistribution
- Gas atoms produced throughout the pellet diffuse toward grain boundaries
- Radial concentration gradients drive gas transport
- Equilibration between bulk and boundary phases varies spatially

**Impact**: The 1D model captures how gas redistributes spatially over time, affecting bubble nucleation and growth patterns.

### 1.3 Key Differences from 0D Model

| Aspect | 0D Model | 1D Radial Model |
|--------|----------|-----------------|
| **State Variables** | 17 (single values) | 17 × n_nodes (radial profiles) |
| **Temperature** | Uniform | Spatially varying profile |
| **Fission Rate** | Uniform | Radial distribution with flux depression |
| **Gas Transport** | Grain-to-boundary only | Grain-to-boundary + radial diffusion |
| **Geometry** | Point (0D) | 1D line (cylindrical or slab) |
| **Results** | Time series | Time series of radial profiles |
| **Computational Cost** | Low | Moderate (scales with n_nodes) |

### 1.4 Model Scope and Applications

**Supported Fuel Types:**
- U-Zr alloys (e.g., U-10Zr)
- U-Pu-Zr alloys (e.g., U-19Pu-10Zr)
- High-purity uranium (validation cases)

**Supported Geometries:**
- **Cylindrical**: Standard fuel pin geometry (default)
  - Radial coordinate r from centerline (r=0) to surface (r=R)
  - Accounts for varying cross-sectional area with radius

- **Slab**: Planar geometry for validation or simplified cases
  - Cartesian coordinate x from midplane (x=0) to surface (x=L/2)
  - Constant cross-sectional area

**Phenomena Captured:**
- Radial temperature distribution (parabolic or user-specified)
- Flux depression effects on fission rate
- Radial gas diffusion between nodes
- Spatially-dependent bubble nucleation and growth
- Non-uniform swelling distribution
- Gas release from pellet surface

**Typical Use Cases:**
- Assessing radial swelling distribution in fuel pins
- Studying centerline effects on fuel performance
- Evaluating fuel-cladding mechanical interaction (FCMI)
- Comparing with experimental radial profilometry data
- Providing boundary conditions for 2D/3D fuel performance codes

### 1.5 Document Organization

The remainder of this document covers:

- **Section 2**: State variables and how they scale with radial nodes
- **Section 3**: Radial mesh structure, geometry options, and discretization
- **Section 4**: Radial transport equations and spatial coupling
- **Section 5**: Temperature profiles and flux depression implementation
- **Section 6**: Boundary conditions at centerline and surface
- **Section 7**: Numerical solution method for multi-node ODE systems
- **Section 8**: Model assumptions, limitations, and validity range
- **Section 9**: Comparison with 0D model for verification
- **Section 10**: Practical usage guide with examples
- **Section 11**: References and further reading

---

## 2. Model Architecture and State Variables

### 2.1 State Vector Structure

The 1D radial model solves a system of **17 × n_nodes** coupled ordinary differential equations (ODEs), where **n_nodes** is the number of radial mesh nodes. Each node solves the same 17-state-variable ODE system as the 0D model, but with additional radial coupling terms.

**State Variable Organization:**
```
Total state vector length = 17 × n_nodes

Layout: [Node_0, Node_1, Node_2, ..., Node_n-1]
        where each node has 17 variables:
        [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf,
         cvb, cib, kvb, kib, cvf, cif, kvf, kif,
         released_gas]
```

**Result Data Structure:**
After solving, each variable is returned as a 2D array with shape `(n_time_points, n_nodes)`:
```python
result = {
    'time': array of length n_time_points,
    'Cgb': array of shape (n_time_points, n_nodes),
    'swelling': array of shape (n_time_points, n_nodes),
    'Rcb': array of shape (n_time_points, n_nodes),
    # ... (all 17 variables)
}
```

### 2.2 State Variables Per Node

Each radial node tracks 17 state variables identical to the 0D model:

#### Bulk Gas Variables (4)
1. **Cgb** - Gas atom concentration in bulk (atoms/m³)
2. **Ccb** - Cavity concentration in bulk (cavities/m³)
3. **Ncb** - Gas atoms per bulk cavity (atoms/cavity)
4. **Rcb** - Bulk cavity radius (m) - *derived from Ncb*

#### Boundary Gas Variables (4)
5. **Cgf** - Gas atom concentration at boundaries (atoms/m³)
6. **Ccf** - Cavity concentration at boundaries (cavities/m³)
7. **Ncf** - Gas atoms per boundary cavity (atoms/cavity)
8. **Rcf** - Boundary cavity radius (m) - *derived from Ncf*

#### Bulk Defect Variables (4)
9. **cvb** - Vacancy concentration in bulk (dimensionless)
10. **cib** - Interstitial concentration in bulk (dimensionless)
11. **kvb** - Vacancy sink strength in bulk (m⁻²) - *derived*
12. **kib** - Interstitial sink strength in bulk (m⁻²) - *derived*

#### Boundary Defect Variables (4)
13. **cvf** - Vacancy concentration at boundaries (dimensionless)
14. **cif** - Interstitial concentration at boundaries (dimensionless)
15. **kvf** - Vacancy sink strength at boundaries (m⁻²) - *derived*
16. **kif** - Interstitial sink strength at boundaries (m⁻²) - *derived*

#### Gas Release (1)
17. **released_gas** - Cumulative gas release fraction (dimensionless)

### 2.3 Spatial Coupling Between Nodes

While each node solves the same 17-variable ODE system, the nodes are coupled through:

1. **Radial Gas Diffusion**: Gas atoms diffuse between adjacent nodes due to concentration gradients
2. **Temperature Distribution**: Each node has its own temperature, affecting local reaction rates
3. **Fission Rate Distribution**: Each node has its own fission rate, affecting gas production
4. **Boundary Conditions**: Centerline (r=0) and surface (r=R) conditions constrain the system

**Coupling Mechanism:**
```python
# For each node i:
dCgb[i]/dt = (local production) - (grain boundary sink)
             + (radial diffusion from node i-1)
             + (radial diffusion from node i+1)
```

### 2.4 Derived Quantities (Not State Variables)

Several important quantities are computed from state variables at each time step but not stored as state variables:

#### Bubble Radii (Rcb, Rcf)
Calculated iteratively from Ncb/Ncf using mechanical equilibrium:
```python
P_gas = calculate_gas_pressure(Nc, R, T)
# R is found such that: P_gas = 2*gamma/R + sigma_ext
```

#### Sink Strengths (kvb, kib, kvf, kif)
Calculated from cavity concentrations and radii:
```python
k_v2 = 4*pi*R*Cc*(1 + kv*R)  # Vacancy sink strength
k_i2 = Z_i*k_v2              # Interstitial sink strength (with bias)
```

#### Swelling Percentage
Volumetric strain due to cavities:
```python
swelling = (4/3)*pi*R^3*Cc  # Volume fraction
```

---

## 3. Radial Mesh and Geometry

### 3.1 RadialMesh Class

The **RadialMesh** class creates the 1D spatial discretization across the fuel pellet radius. It determines where nodes are placed, how spacing is distributed, and what geometry factors to apply.

**Key Attributes:**
```python
mesh = RadialMesh(
    n_nodes=10,           # Number of radial nodes
    radius=0.003,         # Pellet radius (m) - default 3 mm
    geometry='cylindrical',  # 'cylindrical' or 'slab'
    spacing='uniform'     # 'uniform' or 'geometric'
)

# Access mesh properties
mesh.nodes        # Node positions: [0.0, 0.00033, ..., 0.003] m
mesh.dr           # Spacing between nodes
mesh.geometry_factor  # 1.0 for cylindrical, 0.0 for slab
```

### 3.2 Node Distribution Strategies

#### Uniform Spacing (Default)
Nodes are evenly distributed from centerline to surface:
```
r = [0, R/(n-1), 2R/(n-1), ..., R]
```

**Advantages:**
- Simple and predictable
- Equal resolution everywhere
- Easy to implement

**Disadvantages:**
- May under-resolve boundary layers
- Can be inefficient if high resolution only needed near surfaces

**Use Case:**
- General-purpose simulations
- When gradients are moderate
- For validation and testing

#### Geometric Spacing
Node spacing grows by a constant ratio:
```
dr[i+1] = growth_ratio * dr[i]
```

With default growth_ratio = 1.15, each interval is 15% larger than the previous.

**Advantages:**
- Higher resolution near centerline (finer dr)
- Lower resolution near surface (coarser dr)
- Efficient use of computational resources
- Captures boundary layer effects

**Disadvantages:**
- More complex node placement
- Uneven resolution requires careful interpretation

**Use Case:**
- Problems with steep gradients near centerline
- When computational efficiency matters
- Capturing sharp temperature transitions

### 3.3 Geometry Types

#### Cylindrical Geometry (Default)
Standard fuel pin geometry in cylindrical coordinates (r, θ, z).

**Geometry Factor: 1.0**

**Key Features:**
- Radial coordinate r from centerline (r=0) to surface (r=R)
- Cross-sectional area varies with radius: A(r) = 2πrL
- Accounts for increasing volume of annular shells with radius

**Governing Equation:**
```
∂C/∂t = D/r × ∂/∂r(r × ∂C/∂r) + S
```

**Node Placement:**
```
r = [0, Δr, 2Δr, ..., R]  # uniform spacing
```

#### Slab Geometry
Planar geometry in Cartesian coordinates (x, y, z).

**Geometry Factor: 0.0**

**Key Features:**
- Cartesian coordinate x from midplane (x=0) to surface (x=L/2)
- Constant cross-sectional area: A = constant
- Simpler transport equation

**Governing Equation:**
```
∂C/∂t = D × ∂²C/∂x² + S
```

**Node Placement:**
```
x = [0, Δx, 2Δx, ..., L/2]  # uniform spacing
```

**Use Case:**
- Validation against analytical solutions
- Simplified test problems
- Comparison with slab geometry experiments

### 3.4 Mesh Recommendations

#### Number of Nodes
| Use Case | Recommended n_nodes | Rationale |
|----------|---------------------|-----------|
| Quick scoping studies | 5-10 | Fast computation, basic profiles |
| Standard simulations | 10-20 | Good balance of speed and accuracy |
| High-resolution studies | 20-50 | Capture steep gradients accurately |
| Verification/validation | 5-10 | Sufficient for comparing with 0D |

#### Geometry Selection
- Use **cylindrical** for realistic fuel pin simulations
- Use **slab** for validation against analytical solutions

#### Spacing Strategy
- Use **uniform** for general-purpose work
- Use **geometric** when high resolution needed near centerline

---

## 4. Radial Transport Equations

### 4.1 Radial Diffusion Coupling

The 1D radial model adds spatial coupling between nodes through Fick's law of diffusion. Gas atoms can diffuse radially between adjacent nodes due to concentration gradients.

#### Fick's First Law (Finite Difference)
For node i, the radial diffusive flux from node i-1 to i is:
```text
J[i-1 → i] = -D_gb × (C[i] - C[i-1]) / (r[i] - r[i-1])
```

Where:
- J = diffusive flux (atoms/m²/s)
- D_gb = gas diffusion coefficient in bulk (m²/s)
- C[i] = gas concentration at node i (atoms/m³)
- r[i] = radial position of node i (m)

#### Net Rate of Change for Node i
The radial diffusion contribution to dCgb/dt at node i is:
```text
# Flux balance for node i (interior nodes)
dCgb_radial[i] = (A[i-1] × J[i-1→i] - A[i] × J[i→i+1]) / V[i]

# Where:
# A[i] = cross-sectional area between node i and i+1
# V[i] = volume of node i
```

For cylindrical geometry, A[i] scales with radius: A[i] = 2πr[i]L

### 4.2 Radial Transport Implementation

The **calculate_radial_flux** function computes flux between adjacent nodes:

```python
def calculate_radial_flux(
    concentration: np.ndarray,  # shape (n_nodes,)
    diffusion_coeff: float,     # m²/s
    mesh_nodes: np.ndarray,     # radial positions (m)
    geometry_factor: float      # 1.0 (cyl) or 0.0 (slab)
) -> np.ndarray:  # shape (n_nodes-1,)
    """
    Calculate diffusive flux between adjacent nodes.

    Returns flux array where flux[i] is flux from node i to i+1.
    """
    dr = np.diff(mesh_nodes)
    dC_dr = np.diff(concentration) / dr
    flux = -diffusion_coeff * dC_dr  # Fick's first law
    return flux
```

### 4.3 Coupled ODE System

For each radial node i, the gas balance equation becomes:

```text
dCgb[i]/dt = (Production at node i)
             - (Grain boundary sink at node i)
             + (Radial diffusion coupling)

# Radial diffusion coupling (for interior nodes):
+ D_gb/r[i] × [(r[i+1] - r[i])/Δr[i] × (Cgb[i+1] - Cgb[i])
               - (r[i] - r[i-1])/Δr[i-1] × (Cgb[i] - Cgb[i-1])]
```

**Simplified Form:**
```python
dCgb[i]/dt = local_terms[i] + coupling_terms[i-1] - coupling_terms[i]
```

### 4.4 Geometry Factor in Transport

The geometry factor (1.0 for cylindrical, 0.0 for slab) affects the radial transport equation:

**Cylindrical (factor=1.0):**
```
∂C/∂t = D/r × ∂/∂r(r × ∂C/∂r) + S
```
Accounts for varying cross-sectional area with radius.

**Slab (factor=0.0):**
```
∂C/∂t = D × ∂²C/∂x² + S
```
Standard Cartesian diffusion with constant area.

**Implementation:**
```python
# Cylindrical geometry
area_scale = mesh_nodes[i] / (mesh_nodes[i] + mesh_nodes[i+1]) / 2
flux_corrected = flux * area_scale

# Slab geometry
flux_corrected = flux  # No area correction needed
```

---

## 5. Temperature Profiles and Flux Depression

### 5.1 Temperature Profile Options

The 1D radial model supports three types of temperature distributions:

#### Uniform Temperature (Default)
Same temperature at all radial nodes:
```python
model = RadialGasSwellingModel(params, n_nodes=10)
# All nodes use params['temperature']
```

**Use Case:** Comparison with 0D model, isothermal simulations.

#### Parabolic Temperature Profile
Approximates realistic heat conduction in fuel pins:
```python
model = RadialGasSwellingModel(
    params,
    n_nodes=10,
    temperature_profile='parabolic',
    centerline_temp=900,  # K
    surface_temp=600      # K
)
```

**Temperature Distribution:**
```text
T(r) = T_surface + (T_centerline - T_surface) × (1 - r²/R²)
```

**Physical Basis:** Parabolic profile arises from constant volumetric heat generation with temperature-independent thermal conductivity.

#### User-Specified Temperature Profile
Custom temperature array:
```python
import numpy as np
T_custom = np.array([900, 850, 800, 750, 700, 680, 660, 640, 620, 600])  # K
model = RadialGasSwellingModel(
    params,
    n_nodes=10,
    temperature_profile='user',
    temperature_data=T_custom
)
```

**Use Cases:**
- From detailed thermal-hydraulics calculations
- Experimental temperature measurements
- Time-dependent temperature profiles (multiple simulations)

### 5.2 Temperature Dependence of Model Parameters

Many parameters vary with temperature, creating spatial variation in kinetics:

#### Diffusion Coefficients (Arrhenius)
```text
D_gb(T) = D_0 × exp(-Q_D / (k_B × T))
```
- Higher T → faster diffusion → more gas transport to boundaries

#### Bubble Nucleation Rates
```text
nucleation_rate ∝ exp(-E_nuc / (k_B × T))
```
- Higher T → enhanced nucleation → more bubbles

#### Vacancy Emission from Cavities
```text
thermal_emission ∝ exp(-E_f / (k_B × T))
```
- Higher T → more vacancy emission → reduced cavity growth

**Impact:** Hotter centerline regions have faster kinetics but also faster thermal emission, competing effects that determine swelling distribution.

### 5.3 Flux Depression Effects

Neutron flux decreases toward the pellet center due to self-shielding:

#### Flux Depression Model
```python
model = RadialGasSwellingModel(
    params,
    n_nodes=10,
    flux_depression=True
)
```

**Implementation:**
The fission rate at radius r is:
```text
fission_rate(r) = fission_rate_surface × (1 - 0.3 × J₀(2.405 × r/R))
```

Where J₀ is the Bessel function of the first kind (zeroth order).

**Typical Values:**
- Centerline flux ≈ 0.7 × surface flux (30% depression)
- Maximum flux ≈ 1.05 × surface flux (slight enhancement near surface)

**Physical Origin:**
- Neutron absorption in fuel reduces flux toward center
- Depends on fuel composition, enrichment, and pellet size
- Affects fission gas production rate spatially

**Impact on Swelling:**
- Reduces gas production in center (where T is highest)
- Moderates swelling in hottest region
- Creates complex T-flux coupling

### 5.4 Combined Temperature and Flux Effects

The interplay of temperature and flux depression creates interesting swelling patterns:

| Region | Temperature | Flux | Net Effect on Swelling |
|--------|-------------|------|------------------------|
| Centerline | High (promotes swelling) | Low (reduces gas production) | Competition |
| Mid-radius | Medium | Medium | Moderate swelling |
| Near surface | Low (reduces kinetics) | High (high gas production) | Often lower swelling |

**Result:** Maximum swelling often occurs at intermediate radius (not at centerline) due to flux depression counteracting high temperature.

---

## 6. Boundary Conditions

### 6.1 Centerline Boundary Condition (r = 0)

#### Symmetry Condition
At the centerline (r=0), the radial flux must be zero due to cylindrical symmetry:
```python
J(centerline) = 0
```

**Physical Meaning:** Gas cannot cross the centerline to "negative radius."

#### Implementation
```python
# For node 0 (centerline):
# Only allow flux from node 0 to node 1
# No flux from "node -1" (doesn't exist)
dCgb[0]/dt = local_terms[0] - coupling_terms[0]
```

**Mathematical Form:**
```text
∂C/∂r|r=0 = 0  # Zero radial gradient at centerline
```

### 6.2 Surface Boundary Condition (r = R)

#### Zero Flux to Cladding (Default)
Gas does not escape the fuel at the surface (grain boundaries act as sinks):
```python
J(surface) = 0
```

**Physical Meaning:** All gas release occurs through grain boundary interconnected networks, not direct surface escape.

#### Surface Flux (Optional)
If modeling gas escape to cladding:
```text
# Apply surface flux BC
J(surface) = -h × (C_surface - C_cladding)
```

Where h is a mass transfer coefficient.

**Implementation:**
```python
# For node n-1 (surface):
# Only allow flux from node n-2 to node n-1
# Surface flux can be prescribed or zero
dCgb[n-1]/dt = local_terms[n-1] + coupling_terms[n-2] + J_surface
```

### 6.3 Boundary Condition Summary

| Boundary | Condition | Physical Meaning | Implementation |
|----------|-----------|------------------|----------------|
| Centerline (r=0) | Zero flux (∂C/∂r = 0) | Symmetry, no flow across center | Only outward flux from node 0 |
| Surface (r=R) | Zero flux or prescribed flux | Gas release to cladding | Only inward flux to node n-1 |

---

## 7. Numerical Solution Method

### 7.1 Solver Overview

The 1D radial model uses `scipy.integrate.solve_ivp` to integrate the coupled ODE system:

```python
result = solve_ivp(
    fun=lambda t, y: radial_ode_system(t, y, ...),
    t_span=(0, t_final),
    y0=initial_state,  # length = 17 × n_nodes
    method='RK23',     # Runge-Kutta 2(3)
    t_eval=time_points
)
```

**Method Choice:**
- **RK23** (default): Explicit Runge-Kutta, good for non-stiff problems
- **Radau**: Implicit method for stiff systems (slower but more robust)
- **BDF**: Backward differentiation formula, also for stiff systems

### 7.2 Computational Cost

The computational cost scales with:
- **n_nodes**: More nodes → more ODEs → longer solve time
- **Time span**: Longer simulations → more integration steps
- **Stiffness**: Temperature-dependent kinetics can create stiff systems

**Typical Performance:**
```
n_nodes = 5:   ~10 seconds for 100 days
n_nodes = 10:  ~30 seconds for 100 days
n_nodes = 20:  ~90 seconds for 100 days
```

### 7.3 Time Step Adaptation

The adaptive solver adjusts time steps based on local error estimates:
- Small time steps during rapid transients (early irradiation)
- Larger time steps during quasi-steady evolution (later stages)

**User Control:**
```python
result = model.solve(
    t_span=(0, t_final),
    t_eval=time_points,
    method='RK23',
    rtol=1e-6,   # Relative tolerance (default: 1e-3)
    atol=1e-9    # Absolute tolerance (default: 1e-6)
)
```

### 7.4 Result Structure

After solving, results are reshaped from flat array to radial profiles:

```python
# Flat state from solver: shape (17 × n_nodes,)
y_flat = [Cgb_0, Cgb_1, ..., Cgb_n-1, Ccb_0, ..., released_gas_n-1]

# Reshaped results: shape (n_time, n_nodes) per variable
result = {
    'time': time_array,
    'Cgb': Cgb_array,      # (n_time, n_nodes)
    'swelling': swelling_array,
    # ... all 17 variables
}
```

---

## 8. Model Assumptions and Limitations

### 8.1 Key Assumptions

#### Spatial Assumptions
1. **1D Geometry**: Only radial variations considered; azimuthal (θ) and axial (z) homogeneity assumed
2. **Node Independence**: Each node's ODE system is coupled only through radial diffusion
3. **Fixed Mesh**: Mesh does not deform with swelling (Lagrangian approach not implemented)
4. **Isotropic Diffusion**: Diffusion coefficient same in all radial directions

#### Temporal Assumptions
5. **Steady-State Temperature**: Temperature profile fixed during simulation (no thermal coupling)
6. **Constant Fission Rate**: No time-dependent power transients
7. **No Mechanical Effects**: Swelling does not affect temperature or stress

#### Physics Assumptions
8. **Rate Theory Valid**: Rate theory assumptions from 0D model apply at each node
9. **Local Equilibrium**: Each node is in local equilibrium with its neighbors
10. **Independent Bubbles**: No bubble coalescence between nodes (only within each node)

### 8.2 Model Limitations

#### Geometric Limitations
- **No Cladding Interaction**: Does not model fuel-cladding mechanical interaction (FCMI)
- **No Pellet-Pellet Interaction**: Does not account for stacking or dish effects
- **Fixed Pellet Radius**: Does not update geometry as swelling occurs

#### Physics Limitations
- **No Gas Plenum**: Does not model gas release to plenum volume
- **No Thermal Coupling**: Temperature profile fixed, not coupled to swelling
- **No Stress Effects**: Swelling-induced stresses not modeled
- **No Grain Growth**: Grain size assumed constant

#### Numerical Limitations
- **Mesh Resolution**: Coarse mesh may miss steep gradients
- **Stiffness**: Strong temperature dependence can create stiff systems requiring implicit solvers
- **Computational Cost**: High node counts (50+) can be slow

### 8.3 Validity Range

#### Temperature Range
- **Valid**: 600-1200 K (typical fuel operating range)
- **Caution**: Below 600 K, diffusion very slow; above 1200 K, phase transitions may occur

#### Spatial Resolution
- **Valid**: n_nodes ≥ 5 for basic profiles
- **Recommended**: n_nodes = 10-20 for accurate resolution
- **Caution**: n_nodes < 5 may miss important radial variations

#### Burnup Range
- **Valid**: Up to ~10-15 at.% burnup
- **Limit**: High burnup (>15 at.%) may exceed model's physical assumptions

#### Geometry
- **Cylindrical**: Realistic for fuel pins
- **Slab**: For validation only, not representative of real fuel

### 8.4 When to Use 1D vs 0D vs 2D/3D

| Use Case | Recommended Model | Rationale |
|----------|-------------------|-----------|
| Quick swelling estimates | 0D | Fast, simple, average values |
| Radial swelling distribution | 1D | Captures radial gradients efficiently |
| Fuel-cladding interaction | 2D/3D | Requires axial and azimuthal resolution |
| Localized effects (cracks, defects) | 3D | Requires full spatial resolution |
| Parameter studies | 0D or 1D | Faster than full 3D |

---

## 9. Comparison with 0D Model

### 9.1 Verification: Uniform Conditions

When temperature and fission rate are uniform, the 1D model should reproduce 0D results:

```python
# 0D Model
from gas_swelling import RefactoredGasSwellingModel
model_0d = RefactoredGasSwellingModel(params)
result_0d = model_0d.solve(t_span=(0, t_final))

# 1D Model (uniform conditions)
from gas_swelling import RadialGasSwellingModel
model_1d = RadialGasSwellingModel(params, n_nodes=10)
result_1d = model_1d.solve(t_span=(0, t_final))

# Compare: results should agree within ~30%
# (differences due to spatial discretization)
```

**Expected Agreement:** Within 30% for most variables at final time.

### 9.2 Key Differences in Results

#### Swelling Distribution
- **0D**: Single swelling value (e.g., 5%)
- **1D**: Radial profile (e.g., 3% at surface, 7% at centerline)

#### Temperature Effect
- **0D**: Single temperature; cannot capture T-dependence
- **1D**: Shows how swelling varies with local temperature

#### Gas Release
- **0D**: Total gas release fraction
- **1D**: Radial profile of gas release (more release from hotter regions)

### 9.3 Verification Checklist

When validating 1D model against 0D:

- [ ] Run 0D model with uniform conditions
- [ ] Run 1D model with uniform temperature, no flux depression
- [ ] Compare final swelling values (should agree within 30%)
- [ ] Compare time evolution (similar trends expected)
- [ ] Verify that 1D results are uniform across nodes (small variations OK)

---

## 10. Practical Usage Guide

### 10.1 Basic Usage Example

```python
import numpy as np

from gas_swelling import RadialGasSwellingModel, create_default_parameters

# Create parameters
params = create_default_parameters()
params['temperature'] = 773.15  # 500°C in Kelvin

# Create 1D radial model
model = RadialGasSwellingModel(
    params=params,
    n_nodes=10,              # 10 radial nodes
    radius=0.003,            # 3 mm pellet radius
    geometry='cylindrical'   # Fuel pin geometry
)

# Define simulation time (100 days)
t_final = 100 * 24 * 3600  # seconds
t_eval = np.linspace(0, t_final, 100)

# Solve
result = model.solve(t_span=(0, t_final), t_eval=t_eval)

# Access results
swelling_profile = result['swelling']  # shape (100, 10)
radius = model.mesh.nodes  # radial positions

# Final swelling vs radius
import matplotlib.pyplot as plt
plt.plot(radius * 1000, swelling_profile[-1, :])
plt.xlabel('Radius (mm)')
plt.ylabel('Swelling (%)')
plt.show()
```

### 10.2 Temperature Gradient Example

```python
# Create model with parabolic temperature profile
model = RadialGasSwellingModel(
    params=params,
    n_nodes=10,
    temperature_profile='parabolic',
    centerline_temp=900,  # K
    surface_temp=600      # K
)

# Solve and compare with uniform temperature case
result_parabolic = model.solve(t_span=(0, t_final), t_eval=t_eval)

# Plot swelling distribution
plt.figure()
plt.plot(radius * 1000, result_uniform['swelling'][-1, :], label='Uniform T')
plt.plot(radius * 1000, result_parabolic['swelling'][-1, :], label='Parabolic T')
plt.xlabel('Radius (mm)')
plt.ylabel('Swelling (%)')
plt.legend()
plt.show()
```

### 10.3 Visualization Example

```python
from gas_swelling.visualization import RadialProfilePlotter

# Create plotter
plotter = RadialProfilePlotter()
plotter.load_radial_result(result, model.mesh)

# Plot single variable
fig1 = plotter.plot_radial_profile('swelling', time_index=-1)
fig1.savefig('swelling_profile.png')

# Plot multiple variables
fig2 = plotter.plot_radial_comparison(
    variables=['swelling', 'Rcb', 'Pg_b'],
    time_index=-1
)
fig2.savefig('combined_profile.png')

# Plot evolution over time
fig3 = plotter.plot_radial_evolution(
    variable='swelling',
    time_indices=[0, 25, 50, 75, 99]  # Plot at 5 time points
)
fig3.savefig('swelling_evolution.png')
```

### 10.4 Best Practices

#### Mesh Selection
- Start with n_nodes=10 for initial studies
- Increase to n_nodes=20 for production runs
- Use geometric spacing for high resolution near centerline

#### Time Step Control
- Use default tolerances (rtol=1e-3, atol=1e-6) for most cases
- Tighten tolerances for high-precision work
- Use implicit methods (Radau, BDF) if solver fails

#### Result Interpretation
- Always plot radial profiles to check for numerical artifacts
- Verify that results make physical sense (smooth profiles, no oscillations)
- Compare with 0D model to ensure consistency

---

## 11. References

### 11.1 Theoretical Foundation

1. **Original Rate Theory Paper**:
   - "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium phase of irradiated U-Zr and U-Pu-Zr fuel"
   - Describes the 0D rate theory framework extended to 1D

2. **Radial Transport**:
   - Crank, J. (1975). *The Mathematics of Diffusion* (2nd ed.). Oxford University Press.
   - Carslaw, H. S., & Jaeger, J. C. (1959). *Conduction of Heat in Solids*. Oxford University Press.

3. **Nuclear Fuel Behavior**:
   - Olander, D. R. (1976). *Fundamental Aspects of Nuclear Reactor Fuel Elements*. TID-26711-P1.

### 11.2 Numerical Methods

4. **ODE Solvers**:
   - Hairer, E., Norsett, S. P., & Wanner, G. (1993). *Solving Ordinary Differential Equations I: Nonstiff Problems* (2nd ed.). Springer.
   - Hairer, E., & Wanner, G. (1996). *Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems* (2nd ed.). Springer.

5. **Spatial Discretization**:
   - Morton, K. W., & Mayers, D. F. (2005). *Numerical Solution of Partial Differential Equations* (2nd ed.). Cambridge University Press.

### 11.3 Fuel Performance Modeling

6. **Fuel Performance Codes**:
   - **BISON**: Multi-dimensional fuel performance code (INL)
   - **FRAPCON**: Fuel rod behavior code (NRC)
   - **TRANSURANUS**: Fuel performance code (EU)

### 11.4 Related Documentation

7. **Project Documentation**:
   - `THEORY_DOCUMENTATION.md`: 0D model theory
   - `README.md`: Quick start guide and examples
   - `parameter_reference.md`: Complete parameter guide
   - `adaptive_stepping.md`: Numerical solver details

8. **Example Scripts**:
   - `examples/radial_simulation_tutorial.py`: Basic 1D tutorial
   - `examples/radial_temperature_profile_demo.py`: Temperature profile examples

---

## Appendix A: Variable Naming Conventions

| Symbol | Meaning | Units |
|--------|---------|-------|
| r | Radial position | m |
| R | Pellet radius | m |
| n_nodes | Number of radial nodes | - |
| dr | Node spacing | m |
| T(r) | Temperature profile | K |
| φ(r) | Fission rate profile | fissions/(m³·s) |
| Cgb(r) | Bulk gas concentration profile | atoms/m³ |
| swelling(r) | Swelling profile | % |
| J(r) | Radial flux | atoms/(m²·s) |

---

## Appendix B: Troubleshooting

### Issue: Solver Fails to Converge
**Solution**:
- Reduce time span or increase time points
- Try implicit method: `method='Radau'` or `method='BDF'`
- Tighten tolerances: `rtol=1e-6, atol=1e-9`

### Issue: Unphysical Oscillations in Profiles
**Solution**:
- Increase number of nodes (n_nodes)
- Check for negative concentrations (numerical instability)
- Reduce time step size

### Issue: 1D Results Don't Match 0D
**Solution**:
- Ensure uniform temperature and no flux depression for comparison
- Verify that 0D and 1D use identical parameters
- Expect ~30% differences due to spatial discretization

### Issue: Very Slow Computation
**Solution**:
- Reduce number of nodes (n_nodes)
- Use explicit method (RK23) instead of implicit
- Reduce number of output time points (t_eval)

---

*Document Version: 1.0*
*Last Updated: 2026-02-06*
*Author: Gas Swelling Model Development Team*
