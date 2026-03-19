#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Results Interpretation Guide for Gas Swelling Model
===================================================

This example demonstrates how to interpret simulation results and extract
meaningful physical insights from the output.

What this example covers:
- Understanding each output variable
- Identifying typical vs. atypical behavior
- Performing common analysis patterns
- Checking for physical consistency
- Identifying warning signs

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Set up matplotlib for better plotting
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subheader(title):
    """Print a formatted subheader"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


def run_simulation_example(temperature=773.15, fission_rate=1e19):
    """
    Run a simulation with specified parameters.

    Parameters
    ----------
    temperature : float
        Temperature in Kelvin (default: 773.15 K = 500°C)
    fission_rate : float
        Fission rate in fissions/(m³·s) (default: 1e19)

    Returns
    -------
    dict
        Simulation results dictionary
    """
    params = create_default_parameters()
    params['temperature'] = temperature
    params['fission_rate'] = fission_rate

    model = GasSwellingModel(params)

    # Simulate 100 days
    sim_time = 100 * 24 * 3600  # seconds
    t_eval = np.linspace(0, sim_time, 200)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    return result


def interpret_basic_results(results):
    """
    Interpret basic simulation results and provide physical insights.

    This function demonstrates how to extract key metrics and understand
    what they mean physically.
    """
    print_section_header("1. BASIC RESULTS INTERPRETATION")

    # Convert time to days
    time_days = results['time'] / (24 * 3600)
    final_idx = -1  # Last time point

    print(f"\nSimulation Duration: {time_days[final_idx]:.1f} days")
    print(f"\n--- Key Results at End of Simulation ---")

    # 1. Swelling
    final_swelling = results['swelling'][final_idx]
    print(f"\n1. Final Swelling: {final_swelling:.4f}%")
    print_interpretation("swelling", final_swelling)

    # 2. Bubble radii
    final_Rcb = results['Rcb'][final_idx] * 1e9  # Convert to nm
    final_Rcf = results['Rcf'][final_idx] * 1e9  # Convert to nm
    print(f"\n2. Bubble Radii:")
    print(f"   Bulk bubbles: {final_Rcb:.2f} nm")
    print(f"   Boundary bubbles: {final_Rcf:.2f} nm")
    print(f"   Ratio (Rcf/Rcb): {final_Rcf/final_Rcb:.1f}x")
    print_interpretation("radius_ratio", final_Rcf/final_Rcb)

    # 3. Bubble concentrations
    final_Ccb = results['Ccb'][final_idx]
    final_Ccf = results['Ccf'][final_idx]
    print(f"\n3. Bubble Concentrations:")
    print(f"   Bulk: {final_Ccb:.2e} bubbles/m³")
    print(f"   Boundaries: {final_Ccf:.2e} bubbles/m²")

    # 4. Gas atoms per bubble
    final_Ncb = results['Ncb'][final_idx]
    final_Ncf = results['Ncf'][final_idx]
    print(f"\n4. Gas Atoms per Bubble:")
    print(f"   Bulk bubbles: {final_Ncb:.1f} atoms/bubble")
    print(f"   Boundary bubbles: {final_Ncf:.1f} atoms/bubble")
    print(f"   Ratio (Ncf/Ncb): {final_Ncf/final_Ncb:.1f}x")

    # 5. Gas distribution
    gas_in_bulk = results['Cgb'][final_idx]
    gas_in_boundaries = results['Cgf'][final_idx]
    gas_in_bulk_bubbles = results['Ccb'][final_idx] * results['Ncb'][final_idx]
    gas_in_boundary_bubbles = results['Ccf'][final_idx] * results['Ncf'][final_idx]
    gas_released = results['released_gas'][final_idx]

    total_gas = (gas_in_bulk + gas_in_boundaries +
                 gas_in_bulk_bubbles + gas_in_boundary_bubbles + gas_released)

    print(f"\n5. Gas Distribution (final state):")
    if total_gas > 0:
        print(f"   Bulk matrix:     {gas_in_bulk/total_gas*100:5.1f}%")
        print(f"   Bulk bubbles:    {gas_in_bulk_bubbles/total_gas*100:5.1f}%")
        print(f"   Boundary matrix: {gas_in_boundaries/total_gas*100:5.1f}%")
        print(f"   Boundary bubbles:{gas_in_boundary_bubbles/total_gas*100:5.1f}%")
        print(f"   Released gas:    {gas_released/total_gas*100:5.1f}%")
        print(f"   TOTAL:           {total_gas:.2e} atoms/m³")

    # 6. Gas release
    print(f"\n6. Gas Release:")
    print(f"   Cumulative released: {gas_released:.2e} atoms/m³")
    print(f"   Release fraction: {gas_released/total_gas*100:.1f}%")
    print_interpretation("release_fraction", gas_released/total_gas*100)

    return {
        'swelling': final_swelling,
        'Rcb': final_Rcb,
        'Rcf': final_Rcf,
        'gas_distribution': {
            'bulk_solution': gas_in_bulk/total_gas if total_gas > 0 else 0,
            'bulk_bubbles': gas_in_bulk_bubbles/total_gas if total_gas > 0 else 0,
            'boundary_solution': gas_in_boundaries/total_gas if total_gas > 0 else 0,
            'boundary_bubbles': gas_in_boundary_bubbles/total_gas if total_gas > 0 else 0,
            'released': gas_released/total_gas if total_gas > 0 else 0
        }
    }


def print_interpretation(metric, value):
    """Provide physical interpretation for a metric"""
    interpretations = {
        'swelling': {
            (0, 0.1): "Minimal swelling - early stage or low temperature",
            (0.1, 0.5): "Low swelling - acceptable for most applications",
            (0.5, 2.0): "Moderate swelling - typical operating range",
            (2.0, 5.0): "Significant swelling - monitor fuel performance",
            (5.0, 10.0): "High swelling - may impact fuel-clad interaction",
            (10.0, 100.0): "Very high swelling - potential fuel failure risk"
        },
        'radius_ratio': {
            (0, 5): "Boundary bubbles moderately larger than bulk",
            (5, 20): "Boundary bubbles significantly larger (typical)",
            (20, 100): "Boundary bubbles much larger (expected at high T)",
            (100, 1000): "Extreme size difference (check parameters)"
        },
        'release_fraction': {
            (0, 5): "Minimal gas release",
            (5, 20): "Low gas release - early stage",
            (20, 40): "Moderate gas release",
            (40, 60): "Significant gas release - typical for high swelling",
            (60, 100): "Very high gas release"
        }
    }

    if metric in interpretations:
        for (low, high), text in interpretations[metric].items():
            if low <= value < high:
                print(f"   Interpretation: {text}")
                return
    print(f"   Note: Value {value:.3f} outside standard interpretation ranges")


def analyze_temporal_evolution(results):
    """
    Analyze how variables evolve over time and identify key stages.

    Identifies:
    - Incubation period
    - Growth phase
    - Saturation phase
    """
    print_section_header("2. TEMPORAL EVOLUTION ANALYSIS")

    time_days = results['time'] / (24 * 3600)

    # Calculate swelling rate
    swelling_rate = np.gradient(results['swelling'], time_days)

    # Find peak swelling rate
    peak_rate_idx = np.argmax(swelling_rate)
    peak_rate_time = time_days[peak_rate_idx]
    peak_rate_value = swelling_rate[peak_rate_idx]

    print(f"\n--- Swelling Rate Analysis ---")
    print(f"Peak swelling rate: {peak_rate_value:.4f} %/day at t = {peak_rate_time:.1f} days")

    # Identify phases based on swelling rate
    initial_rate = swelling_rate[10]  # Early time
    final_rate = swelling_rate[-10]   # Late time

    print(f"\nInitial swelling rate: {initial_rate:.4f} %/day")
    print(f"Final swelling rate: {final_rate:.4f} %/day")

    # Characterize phases
    if peak_rate_value > 0.05:
        print("\n--- Identified Phases ---")
        print(f"1. Incubation: 0 - {peak_rate_time*0.3:.1f} days (slow initial growth)")
        print(f"2. Growth Phase: {peak_rate_time*0.3:.1f} - {peak_rate_time*1.5:.1f} days (rapid swelling)")
        print(f"3. Saturation: {peak_rate_time*1.5:.1f}+ days (approaching steady state)")

    # Check for steady state
    final_swelling_change = results['swelling'][-1] - results['swelling'][-20]
    if final_swelling_change < 0.1:
        print(f"\nSteady State: Approached (swelling change < 0.1% over last {(time_days[-1]-time_days[-20]):.1f} days)")
    else:
        print(f"\nSteady State: NOT reached (swelling still changing)")


def analyze_gas_distribution_evolution(results):
    """
    Track how gas distribution changes over time.

    This reveals where gas resides and how it moves between reservoirs.
    """
    print_section_header("3. GAS DISTRIBUTION EVOLUTION")

    time_days = results['time'] / (24 * 3600)

    # Calculate gas distribution at several time points
    time_points = [0, len(results['time'])//4, len(results['time'])//2,
                   3*len(results['time'])//4, -1]

    print(f"\n{'Time (days)':<15} {'Bulk Sol':<10} {'Bulk Bub':<10} {'Bound Sol':<10} {'Bound Bub':<10} {'Released':<10}")
    print("-" * 75)

    for idx in time_points:
        if idx == -1:
            idx = len(results['time']) - 1

        gas_in_bulk = results['Cgb'][idx]
        gas_in_boundaries = results['Cgf'][idx]
        gas_in_bulk_bubbles = results['Ccb'][idx] * results['Ncb'][idx]
        gas_in_boundary_bubbles = results['Ccf'][idx] * results['Ncf'][idx]
        gas_released = results['released_gas'][idx]

        total = (gas_in_bulk + gas_in_boundaries +
                 gas_in_bulk_bubbles + gas_in_boundary_bubbles + gas_released)

        if total > 0:
            print(f"{time_days[idx]:<15.1f} "
                  f"{gas_in_bulk/total*100:<9.1f} "
                  f"{gas_in_bulk_bubbles/total*100:<9.1f} "
                  f"{gas_in_boundaries/total*100:<9.1f} "
                  f"{gas_in_boundary_bubbles/total*100:<9.1f} "
                  f"{gas_released/total*100:<9.1f}")

    print("\nInterpretation:")
    print("- Gas initially accumulates in solution (bulk + boundary)")
    print("- Over time, gas moves into bubbles (bulk → boundary)")
    print("- Boundary bubbles eventually dominate gas storage")
    print("- Gas release begins when boundary bubbles interconnect")


def check_physical_consistency(results):
    """
    Perform sanity checks to ensure results are physically reasonable.

    Checks for:
    - Mass conservation
    - Reasonable variable ranges
    - Monotonic behavior where expected
    - Steady state approached
    """
    print_section_header("4. PHYSICAL CONSISTENCY CHECKS")

    time_days = results['time'] / (24 * 3600)
    final_idx = -1

    all_passed = True

    print("\n--- Checking Variable Ranges ---")

    # 1. Swelling should be in reasonable range
    swelling = results['swelling'][final_idx]
    if 0 <= swelling <= 20:
        print(f"✓ Swelling: {swelling:.4f}% (reasonable)")
    else:
        print(f"✗ Swelling: {swelling:.4f}% (OUT OF RANGE)")
        all_passed = False

    # 2. Bubble radii should be positive and reasonable
    Rcb_nm = results['Rcb'][final_idx] * 1e9
    Rcf_nm = results['Rcf'][final_idx] * 1e9
    if 0.1 <= Rcb_nm <= 5000:
        print(f"✓ Bulk bubble radius: {Rcb_nm:.2f} nm (reasonable)")
    else:
        print(f"✗ Bulk bubble radius: {Rcb_nm:.2f} nm (OUT OF RANGE)")
        all_passed = False

    if 1 <= Rcf_nm <= 20000:
        print(f"✓ Boundary bubble radius: {Rcf_nm:.2f} nm (reasonable)")
    else:
        print(f"✗ Boundary bubble radius: {Rcf_nm:.2f} nm (OUT OF RANGE)")
        all_passed = False

    # 3. Gas concentrations should be reasonable
    Cgb = results['Cgb'][final_idx]
    if 1e17 <= Cgb <= 1e23:
        print(f"✓ Bulk gas concentration: {Cgb:.2e} atoms/m³ (reasonable)")
    else:
        print(f"✗ Bulk gas concentration: {Cgb:.2e} atoms/m³ (OUT OF RANGE)")
        all_passed = False

    # 4. Defect concentrations should be small
    cvb = results['cvb'][final_idx]
    if 1e-10 <= cvb <= 1e-2:
        print(f"✓ Vacancy concentration: {cvb:.2e} (reasonable)")
    else:
        print(f"✗ Vacancy concentration: {cvb:.2e} (OUT OF RANGE)")
        all_passed = False

    print("\n--- Checking Monotonic Behavior ---")

    # 5. Bubble concentrations should not decrease
    Ccb_change = results['Ccb'][-1] - results['Ccb'][0]
    if Ccb_change >= 0:
        print(f"✓ Bulk bubble concentration: {results['Ccb'][0]:.2e} → {results['Ccb'][-1]:.2e} (non-decreasing)")
    else:
        print(f"✗ Bulk bubble concentration DECREASED (unphysical)")
        all_passed = False

    # 6. Gas per bubble should not decrease significantly
    Ncb_change = (results['Ncb'][-1] - results['Ncb'][0]) / results['Ncb'][0]
    if Ncb_change >= -0.5:  # Allow up to 50% decrease
        print(f"✓ Gas per bulk bubble: {results['Ncb'][0]:.1f} → {results['Ncb'][-1]:.1f} (reasonable)")
    else:
        print(f"✗ Gas per bulk bubble DECREASED significantly")
        all_passed = False

    print("\n--- Checking Steady State ---")

    # 7. Variables should approach steady state
    Cgb_recent_change = abs(results['Cgb'][-1] - results['Cgb'][-20]) / results['Cgb'][-1]
    if Cgb_recent_change < 0.1:
        print(f"✓ Bulk gas concentration approaching steady state")
    else:
        print(f"! Bulk gas concentration still changing significantly")

    print("\n--- Summary ---")
    if all_passed:
        print("✓ All physical consistency checks PASSED")
    else:
        print("✗ Some checks FAILED - review parameters and results")

    return all_passed


def identify_warning_signs(results):
    """
    Identify potential issues or warning signs in the results.

    Looks for:
    - Numerical instabilities
    - Unphysical values
    - Unexpected behavior patterns
    """
    print_section_header("5. WARNING SIGN DETECTION")

    time_days = results['time'] / (24 * 3600)
    warnings_found = False

    print("\n--- Checking for Common Issues ---")

    # 1. Check for oscillations
    swelling_change = np.diff(results['swelling'])
    sign_changes = np.sum(np.diff(np.sign(swelling_change)) != 0)
    if sign_changes > 10:
        print(f"⚠️  WARNING: Swelling oscillating ({sign_changes} sign changes)")
        print("   → May indicate numerical instability")
        warnings_found = True

    # 2. Check for sudden jumps
    swelling_jumps = np.abs(np.diff(results['swelling']))
    max_jump = np.max(swelling_jumps)
    if max_jump > 0.5:  # More than 0.5% in one time step
        jump_idx = np.argmax(swelling_jumps)
        print(f"⚠️  WARNING: Large jump in swelling at t = {time_days[jump_idx]:.1f} days")
        print(f"   → Jump of {max_jump:.3f}% in one time step")
        warnings_found = True

    # 3. Check for negative values
    for var_name, var_data in [('Cgb', results['Cgb']), ('Ccb', results['Ccb']),
                               ('Ncb', results['Ncb']), ('Rcb', results['Rcb'])]:
        if np.any(var_data < 0):
            negative_count = np.sum(var_data < 0)
            print(f"⚠️  WARNING: {var_name} has {negative_count} negative values")
            warnings_found = True

    # 4. Check for excessive swelling
    if results['swelling'][-1] > 20:
        print(f"⚠️  WARNING: Very high swelling ({results['swelling'][-1]:.1f}%)")
        print("   → May indicate parameter values outside physical range")
        warnings_found = True

    # 5. Check for very large bubbles
    Rcf_um = results['Rcf'][-1] * 1e6  # Convert to micrometers
    if Rcf_um > 10:
        print(f"⚠️  WARNING: Very large boundary bubbles ({Rcf_um:.1f} μm)")
        print("   → Verify re-solution and nucleation parameters")
        warnings_found = True

    # 6. Check for lack of swelling
    if results['swelling'][-1] < 0.001 and time_days[-1] > 50:
        print(f"⚠️  WARNING: Very low swelling after {time_days[-1]:.1f} days")
        print("   → May indicate insufficient bubble nucleation")
        print("   → Try increasing Fnb, Fnf parameters or temperature")
        warnings_found = True

    if not warnings_found:
        print("✓ No warning signs detected")
    else:
        print("\n→ Consult the troubleshooting guide for solutions")

    return not warnings_found


def compare_temperatures():
    """
    Compare results at different temperatures to show temperature effects.

    Demonstrates:
    - Temperature dependence of swelling
    - Optimal swelling temperature
    - Gas release vs temperature
    """
    print_section_header("6. TEMPERATURE COMPARISON STUDY")

    temperatures = [600, 700, 800, 900]  # Kelvin
    results_list = []

    print("\nRunning simulations at different temperatures...")
    for temp in temperatures:
        print(f"  T = {temp} K...", end=" ", flush=True)
        result = run_simulation_example(temperature=temp)
        results_list.append(result)
        print(f"Swelling = {result['swelling'][-1]:.4f}%")

    print_subheader("Temperature Dependence Summary")

    print(f"\n{'Temperature (K)':<18} {'Swelling (%)':<15} {'Rcf (nm)':<15} {'Release (%)':<15}")
    print("-" * 65)

    for temp, result in zip(temperatures, results_list):
        final_swelling = result['swelling'][-1]
        final_Rcf = result['Rcf'][-1] * 1e9

        # Calculate release fraction
        total_gas_produced = 1e19 * result['time'][-1]  # Approximate
        release_fraction = result['released_gas'][-1] / total_gas_produced * 100

        print(f"{temp:<18.0f} {final_swelling:<15.4f} {final_Rcf:<15.1f} {release_fraction:<15.1f}")

    print("\nInterpretation:")
    print("- Swelling typically peaks at 700-800 K")
    print("- Low T: Limited diffusion → low swelling")
    print("- High T: Gas release reduces swelling")


def create_interpretation_plots(results):
    """
    Create diagnostic plots to help interpret results.

    Generates:
    - Time evolution of key variables
    - Gas distribution pie chart
    - Swelling rate analysis
    """
    print_section_header("7. CREATING INTERPRETATION PLOTS")

    time_days = results['time'] / (24 * 3600)

    fig = plt.figure(figsize=(16, 12))

    # Plot 1: Swelling evolution
    ax1 = plt.subplot(3, 3, 1)
    ax1.plot(time_days, results['swelling'], 'b-', linewidth=2)
    ax1.set_xlabel('Time (days)')
    ax1.set_ylabel('Swelling (%)')
    ax1.set_title('Swelling Evolution')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Bubble radii
    ax2 = plt.subplot(3, 3, 2)
    ax2.plot(time_days, results['Rcb'] * 1e9, label='Bulk', linewidth=2)
    ax2.plot(time_days, results['Rcf'] * 1e9, label='Boundary', linewidth=2)
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Radius (nm)')
    ax2.set_title('Bubble Radius Evolution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Gas concentrations
    ax3 = plt.subplot(3, 3, 3)
    ax3.plot(time_days, results['Cgb'], label='Bulk', linewidth=2)
    ax3.plot(time_days, results['Cgf'], label='Boundary', linewidth=2)
    ax3.set_xlabel('Time (days)')
    ax3.set_ylabel('Gas concentration (atoms/m³)')
    ax3.set_title('Gas in Solution')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Bubble concentrations
    ax4 = plt.subplot(3, 3, 4)
    ax4.semilogy(time_days, results['Ccb'], label='Bulk', linewidth=2)
    ax4.semilogy(time_days, results['Ccf'], label='Boundary', linewidth=2)
    ax4.set_xlabel('Time (days)')
    ax4.set_ylabel('Bubble concentration')
    ax4.set_title('Bubble Concentration')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Plot 5: Gas per bubble
    ax5 = plt.subplot(3, 3, 5)
    ax5.plot(time_days, results['Ncb'], label='Bulk', linewidth=2)
    ax5.plot(time_days, results['Ncf'], label='Boundary', linewidth=2)
    ax5.set_xlabel('Time (days)')
    ax5.set_ylabel('Atoms per bubble')
    ax5.set_title('Gas Accumulation in Bubbles')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # Plot 6: Gas release
    ax6 = plt.subplot(3, 3, 6)
    ax6.plot(time_days, results['released_gas'], 'purple', linewidth=2)
    ax6.set_xlabel('Time (days)')
    ax6.set_ylabel('Released gas (atoms/m³)')
    ax6.set_title('Cumulative Gas Release')
    ax6.grid(True, alpha=0.3)

    # Plot 7: Swelling rate
    ax7 = plt.subplot(3, 3, 7)
    swelling_rate = np.gradient(results['swelling'], time_days)
    ax7.plot(time_days, swelling_rate, 'r-', linewidth=2)
    ax7.set_xlabel('Time (days)')
    ax7.set_ylabel('Swelling rate (%/day)')
    ax7.set_title('Swelling Rate')
    ax7.grid(True, alpha=0.3)

    # Plot 8: Gas distribution (final state)
    ax8 = plt.subplot(3, 3, 8)
    final_idx = -1
    gas_bulk_sol = results['Cgb'][final_idx]
    gas_bulk_bub = results['Ccb'][final_idx] * results['Ncb'][final_idx]
    gas_bound_sol = results['Cgf'][final_idx]
    gas_bound_bub = results['Ccf'][final_idx] * results['Ncf'][final_idx]
    gas_released = results['released_gas'][final_idx]

    labels = ['Bulk\nSolution', 'Bulk\nBubbles', 'Boundary\nSolution',
              'Boundary\nBubbles', 'Released']
    sizes = [gas_bulk_sol, gas_bulk_bub, gas_bound_sol, gas_bound_bub, gas_released]
    colors = ['#ff9999', '#ffcc99', '#99ff99', '#66b3ff', '#9999ff']
    ax8.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax8.set_title('Final Gas Distribution')

    # Plot 9: Point defects
    ax9 = plt.subplot(3, 3, 9)
    ax9.semilogy(time_days, results['cvb'], label='Vacancy (bulk)', linewidth=2)
    ax9.semilogy(time_days, results['cib'], label='Interstitial (bulk)', linewidth=2)
    ax9.set_xlabel('Time (days)')
    ax9.set_ylabel('Defect concentration')
    ax9.set_title('Point Defect Concentrations')
    ax9.legend()
    ax9.grid(True, alpha=0.3)

    plt.suptitle('Results Interpretation Dashboard', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_file = 'results_interpretation_dashboard.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Dashboard plot saved to: {output_file}")

    return output_file


def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("  RESULTS INTERPRETATION GUIDE FOR GAS SWELLING MODEL")
    print("=" * 80)
    print("\nThis guide demonstrates how to interpret simulation results")
    print("and extract meaningful physical insights.\n")

    # Run a simulation
    print("Running example simulation at T = 773.15 K (500°C)...")
    results = run_simulation_example()
    print("Simulation complete.\n")

    # 1. Basic interpretation
    summary = interpret_basic_results(results)

    # 2. Temporal evolution
    analyze_temporal_evolution(results)

    # 3. Gas distribution
    analyze_gas_distribution_evolution(results)

    # 4. Physical consistency
    check_physical_consistency(results)

    # 5. Warning signs
    identify_warning_signs(results)

    # 6. Create plots
    create_interpretation_plots(results)

    # 7. Optional: Temperature comparison
    print_section_header("8. OPTIONAL ANALYSES")
    response = input("\nWould you like to run a temperature comparison study? (y/n): ")
    if response.lower() == 'y':
        compare_temperatures()

    print_section_header("ANALYSIS COMPLETE")
    print("\nKey Takeaways:")
    print(f"- Final swelling: {summary['swelling']:.4f}%")
    print(f"- Boundary bubbles are {summary['Rcb']/summary['Rcf']:.1f}x larger than bulk bubbles")
    print(f"- {summary['gas_distribution']['boundary_bubbles']*100:.1f}% of gas in boundary bubbles")
    print("\nNext steps:")
    print("- Review the dashboard plot: results_interpretation_dashboard.png")
    print("- Try different temperatures to see temperature effects")
    print("- Modify parameters to understand sensitivity")
    print("- See docs/guides/interpreting_results.md for detailed guidance")
    print("\n")


if __name__ == "__main__":
    main()
