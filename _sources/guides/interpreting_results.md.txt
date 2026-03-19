# Interpreting Simulation Results: A Comprehensive Guide

**Target Audience:** Graduate students and researchers who want to understand what their simulation results mean
**Reading Time:** ~30 minutes
**Prerequisites:** Basic understanding of [Rate Theory Fundamentals](../tutorials/rate_theory_fundamentals.md) and [Model Equations](../tutorials/model_equations_explained.md)

---

## Learning Objectives

After reading this guide, you will understand:

- ✓ What each output variable represents physically
- ✓ How to identify typical vs. atypical behavior
- ✓ What physical processes your results reveal
- ✓ Warning signs that indicate potential problems
- ✓ How to extract meaningful insights from your data

---

## Table of Contents

1. [Quick Reference: Result Dictionary Structure](#quick-reference-result-dictionary-structure)
2. [Primary Output Variables](#primary-output-variables)
3. [Derived Quantities](#derived-quantities)
4. [Interpreting Temporal Evolution](#interpreting-temporal-evolution)
5. [Warning Signs and Troubleshooting](#warning-signs-and-troubleshooting)
6. [Physical Interpretation Checklist](#physical-interpretation-checklist)
7. [Common Analysis Patterns](#common-analysis-patterns)

---

## Quick Reference: Result Dictionary Structure

When you call `model.solve()`, you receive a dictionary with the following keys:

```python
results = {
    # Time
    'time': np.ndarray,          # Time points (seconds)

    # State variables - Bulk (index b = bulk)
    'Cgb': np.ndarray,           # Gas concentration in bulk matrix (atoms/m³)
    'Ccb': np.ndarray,           # Bubble concentration in bulk (cavities/m³)
    'Ncb': np.ndarray,           # Gas atoms per bulk bubble (atoms/bubble)
    'Rcb': np.ndarray,           # Bulk bubble radius (meters)
    'cvb': np.ndarray,           # Vacancy concentration in bulk (dimensionless)
    'cib': np.ndarray,           # Interstitial concentration in bulk (dimensionless)
    'kvb': np.ndarray,           # Vacancy sink strength in bulk (m⁻²)
    'kib': np.ndarray,           # Interstitial sink strength in bulk (m⁻²)

    # State variables - Boundary (index f = facet/boundary)
    'Cgf': np.ndarray,           # Gas concentration at boundaries (atoms/m³)
    'Ccf': np.ndarray,           # Bubble concentration at boundaries (cavities/m³)
    'Ncf': np.ndarray,           # Gas atoms per boundary bubble (atoms/bubble)
    'Rcf': np.ndarray,           # Boundary bubble radius (meters)
    'cvf': np.ndarray,           # Vacancy concentration at boundaries (dimensionless)
    'cif': np.ndarray,           # Interstitial concentration at boundaries (dimensionless)
    'kvf': np.ndarray,           # Vacancy sink strength at boundaries (m⁻²)
    'kif': np.ndarray,           # Interstitial sink strength at boundaries (m⁻²)

    # Cumulative quantities
    'released_gas': np.ndarray,  # Cumulative gas release (atoms/m³)

    # Key derived quantity
    'swelling': np.ndarray       # Swelling percentage (%)
}
```

**Key convention:**
- Variables ending in `b` (bulk) refer to the grain interior
- Variables ending in `f` (facet) refer to grain boundaries

---

## Primary Output Variables

### Time Evolution: `time`

**Units:** seconds

**Physical Meaning:** The simulation time points at which all other variables are evaluated.

**Typical Range:**
- Short simulations: 0 to 3.6×10⁶ seconds (0-42 days)
- Standard simulations: 0 to 8.6×10⁶ seconds (0-100 days)
- Long-term studies: 0 to 3.2×10⁷ seconds (0-370 days)

**What to Look For:**
- The time points should be roughly evenly spaced (if you specified `t_eval`)
- For adaptive solvers, time points may cluster during rapid changes

**Conversion Tip:**
```python
time_days = results['time'] / (24 * 3600)  # Convert seconds to days
```

---

### 1. `Cgb` - Gas Concentration in Bulk Matrix

**Units:** atoms/m³

**Physical Meaning:** Number of fission gas atoms dissolved in the fuel crystal lattice, wandering randomly through the bulk material.

**Typical Ranges:**

| Condition | Typical Value | Interpretation |
|-----------|---------------|----------------|
| **Initial** | ~1×10²⁰ atoms/m³ | Small initial gas concentration |
| **Early irradiation** | 1×10²⁰ - 5×10²⁰ atoms/m³ | Gas production exceeds loss to bubbles |
| **Steady state** | 5×10¹⁹ - 2×10²⁰ atoms/m³ | Balance between production and capture |
| **Low temperature (<600K)** | 1×10²⁰ - 5×10²⁰ atoms/m³ | Low diffusion → gas accumulates in solution |
| **High temperature (>800K)** | 1×10¹⁹ - 1×10²⁰ atoms/m³ | Fast diffusion → gas escapes to boundaries |

**What to Look For:**
1. **Initial rise:** Cgb should increase initially as fission produces gas
2. **Peak and decline:** After reaching a peak, Cgb may decline as gas diffuses to boundaries
3. **Temperature dependence:** Higher temperature → lower steady-state Cgb

**Physical Interpretation:**
- **High Cgb** means: Many gas atoms are still dissolved, not yet trapped in bubbles
- **Low Cgb** means: Most gas has been captured by bubbles or diffused to boundaries
- **Increasing Cgb** means: Gas production is outpacing bubble nucleation/growth

**Warning Signs:**
- ⚠️ Cgb > 1×10²¹ atoms/m³: Unphysically high - may indicate insufficient bubble nucleation
- ⚠️ Cgb decreasing below 1×10¹⁸ atoms/m³: May indicate all gas has been captured (unlikely early in simulation)
- ⚠️ Cgb monotonically increasing: May indicate bubble nucleation is too slow

---

### 2. `Ccb` - Bubble Concentration in Bulk

**Units:** cavities/m³ (number of bubbles per unit volume)

**Physical Meaning:** How many distinct gas bubbles exist in the bulk material. This is the **number density**, not the size.

**Typical Ranges:**

| Condition | Typical Value | Interpretation |
|-----------|---------------|----------------|
| **Initial** | ~1×10¹⁸ cavities/m³ | Small initial bubble nuclei |
| **Early irradiation** | 1×10¹⁸ - 5×10¹⁸ cavities/m³ | Active nucleation phase |
| **Steady state** | 5×10¹⁸ - 2×10¹⁹ cavities/m³ | Nucleation slows, count stabilizes |
| **High nucleation (high Fnb)** | 1×10¹⁹ - 5×10¹⁹ cavities/m³ | Aggressive bubble formation |
| **Low nucleation (low Fnb)** | 1×10¹⁸ - 5×10¹⁸ cavities/m³ | Limited bubble formation |

**What to Look For:**
1. **Monotonic increase:** Bubble count should only increase (bubbles are created, not destroyed)
2. **Initial rapid rise:** Early nucleation phase creates many new bubbles
3. **Plateau:** Bubble count should eventually level off as nucleation slows

**Physical Interpretation:**
- **Higher Ccb** means: More bubbles competing for the same amount of gas → each bubble stays smaller
- **Lower Ccb** means: Fewer bubbles, each can grow larger
- **Rapidly increasing Ccb** means: Active nucleation phase

**Warning Signs:**
- ⚠️ Ccb decreasing: Physical error - bubbles should not disappear in bulk
- ⚠️ Ccb > 1×10²⁰ cavities/m³: Unphysically high - may indicate nucleation parameters are too aggressive
- ⚠️ Ccb < 1×10¹⁵ cavities/m³: Too few bubbles - check nucleation factor Fnb

---

### 3. `Ncb` - Gas Atoms per Bulk Bubble

**Units:** atoms per bubble (dimensionless count)

**Physical Meaning:** Average number of gas atoms contained within each bulk bubble. This determines the gas pressure and whether bubbles grow or shrink.

**Typical Ranges:**

| Condition | Typical Value | Interpretation |
|-----------|---------------|----------------|
| **Initial** | ~5-10 atoms/bubble | Newly nucleated bubbles |
| **Growing** | 10 - 1,000 atoms/bubble | Active gas accumulation |
| **Mature** | 1,000 - 10,000 atoms/bubble | Significant gas content |
| **Large** | 10,000 - 100,000 atoms/bubble | Large, stable bubbles |
| **Overpressurized** | > Critical value | Gas pressure exceeds surface tension → growth |
| **Underpressurized** | < Critical value | Surface tension dominates → shrinkage |

**Critical Radius Insight:**
- **Critical Nc** (atoms per bubble at mechanical equilibrium):
  - For 10 nm bubbles at 800K: ~1000 atoms/bubble
  - For 100 nm bubbles at 800K: ~1,000,000 atoms/bubble
- **Ncb > critical**: Gas pressure > surface tension → bubble grows
- **Ncb < critical**: Surface tension > gas pressure → bubble shrinks

**What to Look For:**
1. **Monotonic increase:** Bubbles accumulate gas over time
2. **Growth rate acceleration:** Ncb may grow faster as bubbles get larger (higher capture cross-section)
3. **Approach to equilibrium:** Ncb may approach equilibrium with gas pressure

**Physical Interpretation:**
- **Higher Ncb** means: Higher internal gas pressure → driving force for bubble growth
- **Lower Ncb** means: Lower pressure → bubble may be stable or shrinking
- **Rapidly increasing Ncb** means: Bubble is actively absorbing gas from matrix

**Warning Signs:**
- ⚠️ Ncb decreasing significantly: May indicate numerical instability or incorrect re-solution
- ⚠️ Ncb > 10⁷ atoms/bubble: Extremely large - verify with expected bubble radius
- ⚠️ Ncb < 2 atoms/bubble: Too small for stable bubbles - check nucleation parameters

---

### 4. `Rcb` - Bulk Bubble Radius

**Units:** meters (typically displayed in nanometers: 1 nm = 10⁻⁹ m)

**Physical Meaning:** Physical radius of bubbles in the bulk matrix, calculated from Ncb using mechanical equilibrium between gas pressure and surface tension.

**Typical Ranges:**

| Condition | Radius (nm) | Interpretation |
|-----------|-------------|----------------|
| **Initial** | ~1-10 nm | Tiny nuclei |
| **Early growth** | 10-50 nm | Small growing bubbles |
| **Intermediate** | 50-200 nm | Medium-sized bubbles |
| **Large** | 200-1000 nm (0.2-1 μm) | Large bubbles |
| **Very large** | > 1000 nm (>1 μm) | Very large bubbles (uncommon in bulk) |

**What to Look For:**
1. **Gradual increase:** Bubbles grow slowly in bulk due to re-solution effect
2. **Size limitation:** Bulk bubbles typically stay below ~500 nm due to re-solution
3. **Correlation with Ncb:** Rcb should track with Ncb (more atoms → larger radius)

**Physical Interpretation:**
- **Larger Rcb** means: More space occupied by each bubble → higher swelling potential
- **Smaller Rcb** means: More numerous but less space-filling bubbles
- **Rapidly growing Rcb** means: Low re-solution, high gas capture

**Relationship to Swelling:**
```
Swelling contribution from bulk = (4/3) × π × Rcb³ × Ccb
```
- Many small bubbles vs. few large bubbles: same gas amount can give different swelling

**Warning Signs:**
- ⚠️ Rcb > 2000 nm (2 μm): Unusually large for bulk - may indicate re-solution is too weak
- ⚠️ Rcb decreasing: Physical error - bubbles should not spontaneously shrink without loss of atoms
- ⚠️ Rcb < 0.1 nm: Too small to be physical - check initial conditions

---

### 5. `cvb` and `cib` - Point Defect Concentrations in Bulk

**Units:** dimensionless (fraction of lattice sites that are vacancies/interstitials)

**Physical Meaning:**
- **cvb:** Fraction of lattice sites that are vacant (missing atoms)
- **cib:** Fraction of lattice sites with extra atoms (interstitials)

**Typical Ranges:**

| Condition | cvb (vacancy) | cib (interstitial) | Interpretation |
|-----------|---------------|-------------------|----------------|
| **Thermal equilibrium** | ~10⁻⁸ - 10⁻⁶ | ~10⁻²⁰ - 10⁻¹⁸ | Baseline thermal defects |
| **Under irradiation** | ~10⁻⁶ - 10⁻⁴ | ~10⁻¹⁰ - 10⁻⁸ | Radiation-enhanced defects |
| **High fission rate** | ~10⁻⁴ - 10⁻³ | ~10⁻⁸ - 10⁻⁷ | Massive defect production |
| **Low temperature** | Lower | Lower | Low thermal emission |

**What to Look For:**
1. **Steady state:** Both should reach steady-state values (production = annihilation)
2. **cib ≫ cvb is FALSE:** Actually cvb ≫ cib typically (vacancies accumulate)
3. **Temperature dependence:** Higher T → higher thermal equilibrium values

**Physical Interpretation:**
- **High cvb** means: Many vacancies available for bubble growth → enhances swelling
- **High cib** means: Many interstitials (but they annihilate quickly at dislocations)
- **Vacancy supersaturation:** When cvb > thermal equilibrium → driving force for void growth

**Key Relationship:**
```
Bubble growth ∝ (vacancy influx) - (thermal vacancy emission)
```
Higher cvb → more vacancy influx → bubble growth

**Warning Signs:**
- ⚠️ cvb or cib > 0.01: Too high - would mean 1% of lattice sites are defects (unphysical)
- ⚠️ cib > cvb: Unusual (interstitials typically annihilate faster)
- ⚠️ cvb or cib monotonically increasing without bound: May indicate sink strength too low

---

### 6. `kvb` and `kib` - Sink Strengths in Bulk

**Units:** m⁻² (inverse area)

**Physical Meaning:** Measure of how effectively defects are absorbed by sinks (dislocations, bubbles, grain boundaries). Higher sink strength = faster defect annihilation.

**Typical Ranges:**

| Condition | kvb (vacancy) | kib (interstitial) | Interpretation |
|-----------|---------------|-------------------|----------------|
| **Initial** | ~10¹⁴ - 10¹⁵ m⁻² | ~10¹⁴ - 10¹⁵ m⁻² | From dislocations only |
| **With bubbles** | ~10¹⁵ - 10¹⁶ m⁻² | ~10¹⁵ - 10¹⁶ m⁻² | Bubbles act as additional sinks |
| **High bubble density** | ~10¹⁶ - 10¹⁷ m⁻² | ~10¹⁶ - 10¹⁷ m⁻² | Many bubble sinks |
| **Low dislocation density** | ~10¹³ - 10¹⁴ m⁻² | ~10¹³ - 10¹⁴ m⁻² | Few dislocation sinks |

**What to Look For:**
1. **Time evolution:** Sink strengths increase as bubbles nucleate and grow
2. **kvb ≈ kib:** Similar magnitude (both depend on bubble/dislocation density)
3. **Correlation with Ccb:** Higher bubble concentration → higher sink strength

**Physical Interpretation:**
- **High sink strength** means: Defects are quickly annihilated → lower steady-state defect concentrations
- **Low sink strength** means: Defects accumulate → higher supersaturation → more bubble growth

**Key Relationship:**
```
Steady-state defect concentration ∝ (production rate) / (sink strength)
```

**Warning Signs:**
- ⚠️ kvb or kib > 10¹⁸ m⁻²: Unphysically high - check bubble density
- ⚠️ kvb or kib decreasing: Should be monotonic increase or constant
- ⚠️ Large discrepancy between kvb and kib: Should be similar (check Zv vs Zi bias)

---

## Boundary Variables (Cgf, Ccf, Ncf, Rcf, cvf, cif, kvf, kif)

**Key Difference from Bulk:**
- **No re-solution effect** at boundaries → bubbles grow much larger
- **Lower dislocation density** → different defect kinetics
- **Gas release possible** when bubbles interconnect

### `Ccf` - Bubble Concentration at Boundaries

**Typical Range:** 10¹⁴ - 10¹⁶ cavities/m² (per unit boundary area)

**Key Difference from Bulk:**
- Much lower than Ccb (2D vs 3D density)
- Units are different: m⁻² (area density) vs m⁻³ (volume density)

### `Ncf` - Gas Atoms per Boundary Bubble

**Typical Range:** 10³ - 10⁷ atoms/bubble

**Key Difference from Bulk:**
- **Much larger than Ncb** (can be 100-1000× larger)
- No re-solution → bubbles accumulate many more atoms
- Drives bubble growth to larger sizes

### `Rcf` - Boundary Bubble Radius

**Typical Range:** 100 nm - 10 μm (0.1 - 10 μm)

**Key Difference from Bulk:**
- **Much larger than Rcb** (10-100× larger)
- Can reach micron-scale at boundaries
- Main contributor to swelling

### `Cgf` - Gas Concentration at Boundaries

**Typical Range:** 10¹⁹ - 10²¹ atoms/m³

**Key Difference from Bulk:**
- Often higher than Cgb (gas accumulates at boundaries)
- Feeds bubble growth at boundaries

### Boundary Point Defects (cvf, cif, kvf, kif)

**Typical Behavior:**
- Similar to bulk but different magnitudes
- Lower dislocation density at boundaries → different sink strengths

---

## Derived Quantities

### `swelling` - Volume Percentage

**Units:** percent (%)

**Physical Meaning:** Percentage of fuel volume occupied by gas bubbles. This is the key output for fuel performance analysis.

**Formula:**
```text
swelling = [(4/3) × π × Rcb³ × Ccb + (4/3) × π × Rcf³ × Ccf] × 100%
```

**Typical Ranges:**

| Condition | Swelling | Interpretation |
|-----------|----------|----------------|
| **Early irradiation** | < 0.1% | Minimal swelling |
| **Standard operation** | 0.1% - 2% | Acceptable swelling |
| **High swelling** | 2% - 10% | Significant swelling, may impact performance |
| **Extreme swelling** | > 10% | Severe swelling, potential fuel failure |
| **Temperature peak (700-800K)** | 1% - 5% | Maximum swelling at intermediate temperatures |
| **Low T (<600K)** | < 1% | Limited diffusion → low swelling |
| **High T (>900K)** | 1% - 3% | Gas release reduces swelling |

**What to Look For:**
1. **Sigmoidal shape:** Slow initial rise → rapid growth → plateau
2. **Temperature dependence:** Peak swelling at ~700-800K
3. **Saturation:** Swelling should eventually saturate (gas production = release)

**Physical Interpretation:**
- **0-0.5% swelling:** Early stage, bubbles nucleating
- **0.5-2% swelling:** Active growth phase
- **2-5% swelling:** Significant swelling, monitor for fuel performance
- **>5% swelling:** High swelling, may require design changes

**Warning Signs:**
- ⚠️ Swelling > 20%: Unphysically high - fuel would be severely degraded
- ⚠️ Swelling decreasing: Physical error - bubbles don't disappear
- ⚠️ Swelling oscillating: Numerical instability
- ⚠️ Swelling < 0.001% after long simulation: May indicate insufficient bubble nucleation

---

### `released_gas` - Cumulative Gas Release

**Units:** atoms/m³

**Physical Meaning:** Total amount of gas that has been released from the fuel (typically via grain boundary interconnection and venting to fuel-clad gap).

**Typical Ranges:**

| Condition | Released Gas | Interpretation |
|-----------|--------------|----------------|
| **Early simulation** | < 10% of total | Most gas retained in fuel |
| **Standard operation** | 10% - 30% of total | Partial gas release |
| **High release** | 30% - 60% of total | Significant release |
| **Very high release** | > 60% of total | Most gas released |

**What to Look For:**
1. **Delayed onset:** Release typically starts after swelling reaches ~1-2%
2. **Accelerating release:** Release rate increases as bubbles interconnect
3. **Temperature dependence:** Higher T → earlier and faster release

**Physical Interpretation:**
- **Gas release threshold:** Bubbles must interconnect before release occurs
- **Release mechanism:** Bubbles at grain boundaries coalesce and form pathways to free surface
- **Impact on swelling:** Release reduces swelling (gas leaves the fuel)

**Calculate Release Fraction:**
```python
total_gas_produced = params['gas_generation_rate'] * final_time
release_fraction = results['released_gas'][-1] / total_gas_produced
```

**Warning Signs:**
- ⚠️ Release > 90%: Unrealistically high - most models predict 30-60% release
- ⚠️ Immediate release at t=0: May indicate interconnection threshold too low
- ⚠️ No release at high swelling: May indicate threshold too high

---

## Interpreting Temporal Evolution

### Stage 1: Incubation Period (0-10 days)

**Characteristics:**
- Low swelling (< 0.1%)
- Active bubble nucleation (Ccb increasing rapidly)
- Gas accumulation in solution (Cgb rising)
- Small bubble radius (Rcb, Rcf < 10 nm)

**Physical Processes:**
- Gas production by fission
- Bubble nucleation
- Gas atom diffusion

**What to Check:**
- Ccb should show rapid initial increase
- Cgb should rise as gas is produced
- Swelling should be minimal

---

### Stage 2: Growth Phase (10-60 days)

**Characteristics:**
- Rapid swelling increase (0.1% → 1-5%)
- Bubble growth (Rcb, Rcf increasing)
- Gas accumulation in bubbles (Ncb, Ncf increasing)
- Cgb may peak and decline

**Physical Processes:**
- Bubble growth by gas absorption
- Vacancy-driven bubble expansion
- Gas diffusion from matrix to bubbles

**What to Check:**
- Swelling curve should show steep upward slope
- Ncb, Ncf should increase monotonically
- Rcb, Rcf should grow steadily
- Boundary bubbles (Rcf) should grow larger than bulk bubbles (Rcb)

---

### Stage 3: Saturation/Release Phase (60+ days)

**Characteristics:**
- Swelling growth slows (approaches plateau)
- Gas release may begin (released_gas increasing)
- Bubble concentrations stabilize (Ccb, Ccf plateau)
- Gas in solution reaches steady state (Cgb stabilizes)

**Physical Processes:**
- Gas release from interconnected bubbles
- Balance between gas production and release
- Bubble growth saturation

**What to Check:**
- Swelling should approach asymptotic value
- released_gas should show accelerating release
- Cgb should reach steady state
- Final swelling should be in physically reasonable range (0.5-10%)

---

## Warning Signs and Troubleshooting

### Numerical Instability

**Symptoms:**
- Oscillating values
- Sudden jumps in variables
- Negative concentrations

**Possible Causes:**
- Time step too large
- Solver method inappropriate (try 'BDF' for stiff systems)
- Initial conditions inconsistent

**Solutions:**
1. Reduce `max_dt` parameter
2. Try `method='BDF'` instead of 'RK23'
3. Check initial conditions are physically reasonable

---

### Unphysical Results

**Symptoms:**
- Bubble radius > 10 μm
- Swelling > 20%
- Gas concentration > 10²² atoms/m³
- Decreasing bubble count

**Possible Causes:**
- Parameters outside physical range
- Incorrect material properties
- Wrong fuel type parameters

**Solutions:**
1. Verify all parameters using [Parameter Reference](../parameter_reference.md)
2. Check material-specific parameters (U-10Zr vs U-Pu-Zr)
3. Compare with validation cases from paper

---

### No Swelling

**Symptoms:**
- Swelling < 0.001% after long simulation
- Bubble radius not growing
- Gas accumulating in solution but not in bubbles

**Possible Causes:**
- Nucleation factors (Fnb, Fnf) too low
- Temperature too low for diffusion
- Surface energy too high (prevents bubble growth)

**Solutions:**
1. Increase Fnb, Fnf parameters
2. Increase temperature to > 700K
3. Verify surface energy parameter (should be ~0.5-1.0 J/m²)

---

### Excessive Swelling

**Symptoms:**
- Swelling > 10% early in simulation
- Rapid unbounded growth
- All gas goes to bubbles

**Possible Causes:**
- Nucleation factors too high
- Re-solution too weak
- Dislocation density too high

**Solutions:**
1. Decrease Fnb, Fnf parameters
2. Verify re-solution parameters
3. Check dislocation density is reasonable (10¹³-10¹⁵ m⁻²)

---

## Physical Interpretation Checklist

Use this checklist to verify your results make physical sense:

### Mass Balance
- [ ] Total gas accounted for: `gas_in_matrix + gas_in_bubbles + released_gas ≈ gas_produced`
- [ ] No negative concentrations
- [ ] Bubble counts are monotonic increasing or constant

### Energy Balance
- [ ] Gas pressure in bubbles is reasonable (check Pg if available)
- [ ] Mechanical equilibrium: gas pressure ≈ surface tension / radius

### Spatial Distribution
- [ ] Boundary bubbles larger than bulk bubbles (Rcf ≫ Rcb)
- [ ] More gas in boundary bubbles than bulk bubbles (typically)
- [ ] Defect concentrations reach steady state

### Time Evolution
- [ ] Swelling follows sigmoidal pattern (slow → fast → saturation)
- [ ] Gas release begins after sufficient swelling
- [ ] All variables approach steady state or monotonic evolution

### Comparison with Expectations
- [ ] Final swelling in expected range (0.1-10% for typical conditions)
- [ ] Temperature dependence matches expectations (peak at 700-800K)
- [ ] Bubble sizes in expected range (nm-μm scale)

---

## Common Analysis Patterns

### Pattern 1: Temperature Sweep Analysis

**Goal:** Understand how temperature affects swelling behavior

**Procedure:**
1. Run simulations at multiple temperatures (600K, 700K, 800K, 900K)
2. Compare final swelling values
3. Identify peak swelling temperature
4. Analyze gas distribution vs temperature

**Expected Result:**
- Bell-shaped swelling curve with peak at ~700-800K
- Low T: Limited diffusion → low swelling
- High T: Gas release reduces swelling
- Peak T: Optimal balance for swelling

---

### Pattern 2: Gas Distribution Analysis

**Goal:** Track where gas resides over time

**Procedure:**
```python
# At any time t:
gas_in_bulk_solution = results['Cgb'][t]
gas_in_bulk_bubbles = results['Ccb'][t] * results['Ncb'][t]
gas_in_boundary_solution = results['Cgf'][t]
gas_in_boundary_bubbles = results['Ccf'][t] * results['Ncf'][t]
gas_released = results['released_gas'][t]

total_gas = (gas_in_bulk_solution + gas_in_bulk_bubbles +
             gas_in_boundary_solution + gas_in_boundary_bubbles +
             gas_released)

fractions = {
    'bulk_solution': gas_in_bulk_solution / total_gas,
    'bulk_bubbles': gas_in_bulk_bubbles / total_gas,
    'boundary_solution': gas_in_boundary_solution / total_gas,
    'boundary_bubbles': gas_in_boundary_bubbles / total_gas,
    'released': gas_released / total_gas
}
```

**Expected Evolution:**
- Early: Most gas in solution
- Mid: Gas moves to bubbles
- Late: Significant gas in boundary bubbles and released

---

### Pattern 3: Swelling Rate Analysis

**Goal:** Identify periods of rapid swelling

**Procedure:**
```python
# Calculate swelling rate
time_days = results['time'] / (24 * 3600)
swelling_rate = np.gradient(results['swelling'], time_days)

# Find peak swelling rate
peak_rate_idx = np.argmax(swelling_rate)
peak_rate_time = time_days[peak_rate_idx]
peak_rate_value = swelling_rate[peak_rate_idx]

print(f"Peak swelling rate: {peak_rate_value:.4f} %/day at {peak_rate_time:.1f} days")
```

**Interpretation:**
- High swelling rate: Active growth phase
- Low swelling rate: Incubation or saturation
- Identify when to take action (e.g., fuel management)

---

### Pattern 4: Bubble Size Distribution

**Goal:** Understand bubble population characteristics

**Procedure:**
```python
# Effective volume per bubble
bulk_bubble_volume = (4/3) * np.pi * results['Rcb']**3
boundary_bubble_volume = (4/3) * np.pi * results['Rcf']**3

# Volume-weighted vs number-weighted sizes
final_time = -1
print(f"Bulk bubbles:")
print(f"  Number: {results['Ccb'][final_time]:.2e} bubbles/m³")
print(f"  Radius: {results['Rcb'][final_time]*1e9:.1f} nm")
print(f"  Volume per bubble: {bulk_bubble_volume[final_time]*1e27:.2f} nm³")

print(f"Boundary bubbles:")
print(f"  Number: {results['Ccf'][final_time]:.2e} bubbles/m²")
print(f"  Radius: {results['Rcf'][final_time]*1e9:.1f} nm")
print(f"  Volume per bubble: {boundary_bubble_volume[final_time]*1e27:.2f} nm³")
```

**Interpretation:**
- Compare bulk vs boundary bubble characteristics
- Understand which population dominates swelling
- Identify which bubbles to target for mitigation

---

## Summary: Key Takeaways

### Most Important Variables for Quick Analysis
1. **`swelling`** - Primary output, directly indicates fuel performance
2. **`Rcf`** - Boundary bubble radius, main swelling contributor
3. **`released_gas`** - Indicates gas release fraction

### Variables for Deep Understanding
1. **`Cgb`, `Cgf`** - Gas in solution, indicates diffusion balance
2. **`Ncb`, `Ncf`** - Gas per bubble, indicates driving pressure
3. **`cvb`, `cib`** - Point defects, control growth kinetics

### Sanity Checks
- Swelling: 0.1-10% typical
- Bubble radius: nm-μm range
- Gas concentrations: 10¹⁹-10²¹ atoms/m³
- Defect concentrations: 10⁻⁶-10⁻⁴ (fraction of lattice sites)

### Warning Signs
- Negative values: Numerical error
- Decreasing bubble count: Physical error
- Extreme swelling (>20%): Parameter error
- No steady state: May need longer simulation

---

## Further Reading

- [Rate Theory Fundamentals](../tutorials/rate_theory_fundamentals.md) - Understanding the physics
- [Model Equations Explained](../tutorials/model_equations_explained.md) - Variable meanings
- [Parameter Reference](../parameter_reference.md) - Parameter guidance
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [30-Minute Quickstart](../tutorials/30minute_quickstart.md) - Getting started

---

**Need Help?** If you encounter unexpected results, check the [Troubleshooting Guide](troubleshooting.md) or consult the validation examples in the Jupyter notebooks.
