#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-at-a-Time (OAT) Sensitivity Analysis Example
=================================================

This example demonstrates how to perform a local sensitivity analysis
using the One-at-a-Time (OAT) method for the gas swelling model.

What is OAT Sensitivity Analysis?
----------------------------------
OAT analysis varies one parameter at a time while keeping all other
parameters at their nominal (baseline) values. This helps identify:

1. Which parameters have the strongest influence on model outputs
2. The direction of parameter effects (positive/negative correlation)
3. Approximate linear sensitivity around the nominal parameter values

When to use OAT?
- Initial screening to identify important parameters
- Understanding local parameter sensitivities
- Quick sensitivity assessment with limited computational resources
- Model calibration and parameter ranking

Limitations:
- Does not capture parameter interactions
- Only provides local sensitivity (around nominal values)
- May miss nonlinear effects far from nominal point

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.analysis.sensitivity import (
    OATAnalyzer,
    ParameterRange,
    create_default_parameter_ranges
)
from gas_swelling.params.parameters import create_default_parameters

# Set up matplotlib for better plotting
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_basic_oat_example():
    """
    Run a basic OAT sensitivity analysis with default parameters.

    This example uses pre-defined parameter ranges for key model parameters
    and analyzes their effect on fuel swelling.
    """

    print_section_header("STEP 1: Set Up OAT Analyzer")

    print("Creating OAT analyzer with default parameter ranges...")
    print("The following parameters will be analyzed:")

    # Create default parameter ranges
    param_ranges = create_default_parameter_ranges()

    for pr in param_ranges:
        print(f"  - {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}], nominal={pr.nominal_value:.3g}")

    # Initialize analyzer
    analyzer = OATAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],  # Analyze effect on swelling
        sim_time=7200000.0,         # 83.3 days (shorter for demonstration)
        t_eval_points=100
    )

    print(f"\nAnalyzer configuration:")
    print(f"  - Number of parameters: {analyzer.get_n_parameters()}")
    print(f"  - Simulation time: {analyzer.sim_time:.1f}s ({analyzer.sim_time/86400:.2f} days)")
    print(f"  - Output metric: swelling (%)")

    print_section_header("STEP 2: Run OAT Analysis")

    # Define percentage variations to test
    # We'll test ±10% and ±20% variations
    percent_variations = [-20, -10, 10, 20]

    print(f"\nTesting variations: {percent_variations}%")
    print("This means each parameter will be varied by these percentages")
    print("while all other parameters remain at their nominal values.\n")

    # Run the analysis
    results = analyzer.run_oat_analysis(
        percent_variations=percent_variations,
        verbose=True
    )

    print_section_header("STEP 3: Analyze Results")

    print("\nSensitivity Summary (ranked by elasticity):")
    print("-" * 70)
    print(f"{'Parameter':<25} {'Elasticity':<12} {'Norm. Sens.':<12} {'Direction':<10}")
    print("-" * 70)

    # Sort results by elasticity (absolute value)
    sorted_results = sorted(
        results,
        key=lambda r: abs(r.sensitivities['swelling']['elasticity']),
        reverse=True
    )

    for result in sorted_results:
        sens = result.sensitivities['swelling']
        elasticity = sens['elasticity']
        norm_sens = sens['normalized']

        # Determine direction
        if elasticity > 0.01:
            direction = "Positive"
        elif elasticity < -0.01:
            direction = "Negative"
        else:
            direction = "Neutral"

        print(f"{result.parameter_name:<25} {elasticity:>11.3f} {norm_sens:>11.3f} {direction:<10}")

    print("\nInterpretation:")
    print("  - Elasticity: Percent change in swelling per 1% change in parameter")
    print("  - Positive: Increasing parameter increases swelling")
    print("  - Negative: Increasing parameter decreases swelling")
    print("  - Higher absolute values = stronger sensitivity")

    print_section_header("STEP 4: Visualize Results")

    # Create multi-panel visualization
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. Parameter elasticity bar chart (ranked)
    ax1 = fig.add_subplot(gs[0, :])
    param_names = [r.parameter_name for r in sorted_results]
    elasticities = [r.sensitivities['swelling']['elasticity'] for r in sorted_results]

    colors = ['green' if e > 0 else 'red' for e in elasticities]
    bars = ax1.barh(param_names, elasticities, color=colors, alpha=0.7, edgecolor='black')

    ax1.set_xlabel('Elasticity (Δ% swelling / Δ% parameter)', fontsize=11, fontweight='bold')
    ax1.set_title('Parameter Sensitivity Ranking (OAT Analysis)', fontsize=12, fontweight='bold')
    ax1.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax1.grid(True, alpha=0.3, axis='x')

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, elasticities)):
        ax1.text(val, i, f' {val:.3f}', va='center', fontsize=9, fontweight='bold')

    # 2-7. Individual parameter variation plots
    plot_positions = [(1, 0), (1, 1), (2, 0), (2, 1)]
    n_params_to_plot = min(4, len(sorted_results))

    for idx in range(n_params_to_plot):
        ax = fig.add_subplot(gs[plot_positions[idx][0], plot_positions[idx][1]])
        result = sorted_results[idx]

        # Get parameter variations and outputs
        variations = np.array(result.variations)
        outputs = np.array(result.outputs['swelling'])

        # Calculate percentage changes
        pct_changes = (variations - result.nominal_value) / result.nominal_value * 100

        # Plot
        ax.plot(pct_changes, outputs, 'o-', linewidth=2, markersize=8, color='steelblue')
        ax.axhline(y=result.baseline_outputs['swelling'], color='red',
                   linestyle='--', linewidth=1.5, label='Baseline')
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        ax.set_xlabel(f'{result.parameter_name} variation (%)', fontsize=10)
        ax.set_ylabel('Swelling (%)', fontsize=10)
        ax.set_title(f'{result.parameter_name} Sensitivity', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

        # Add sensitivity metrics as text
        sens = result.sensitivities['swelling']
        textstr = f"Elasticity: {sens['elasticity']:.3f}\nNorm. Sens: {sens['normalized']:.3f}"
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Save figure
    output_filename = 'oat_sensitivity_analysis.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_filename}")
    plt.show()

    return results


def run_custom_oat_example():
    """
    Demonstrate custom parameter range definition and analysis.

    This example shows how to define your own parameter ranges
    and analyze multiple output metrics simultaneously.
    """

    print_section_header("BONUS: Custom OAT Analysis")

    print("\nDefining custom parameter ranges...")

    # Create custom parameter ranges focused on temperature effects
    custom_params = [
        ParameterRange(
            name='temperature',
            min_value=600.0,
            max_value=800.0,
            nominal_value=700.0,
            distribution='uniform'
        ),
        ParameterRange(
            name='surface_energy',
            min_value=0.4,
            max_value=0.6,
            nominal_value=0.5,
            distribution='uniform'
        ),
        ParameterRange(
            name='dislocation_density',
            min_value=5e13,
            max_value=9e13,
            nominal_value=7e13,
            distribution='uniform'
        )
    ]

    print("Custom parameter ranges:")
    for pr in custom_params:
        print(f"  - {pr.name}: {pr.nominal_value} ± {abs(pr.nominal_value - pr.max_value):.3g}")

    # Create analyzer with multiple outputs
    analyzer = OATAnalyzer(
        parameter_ranges=custom_params,
        output_names=['swelling', 'final_bubble_radius_bulk', 'gas_release_fraction'],
        sim_time=7200000.0,
        t_eval_points=100
    )

    print(f"\nAnalyzing {len(analyzer.output_names)} output metrics:")
    for out in analyzer.output_names:
        print(f"  - {out}")

    # Run analysis
    print("\nRunning OAT analysis...")
    results = analyzer.run_oat_analysis(
        percent_variations=[-15, 15],
        verbose=False
    )

    # Display multi-output results
    print("\nMulti-Output Sensitivity Results:")
    print("-" * 80)
    print(f"{'Parameter':<25} {'Swelling':<12} {'Bubble Radius':<15} {'Gas Release':<12}")
    print(f"{'':25} {'Elast.':<12} {'Elast.':<15} {'Elast.':<12}")
    print("-" * 80)

    for result in results:
        row = f"{result.parameter_name:<25} "
        for output_name in ['swelling', 'final_bubble_radius_bulk', 'gas_release_fraction']:
            elast = result.sensitivities[output_name]['elasticity']
            row += f"{elast:>10.3f}   "
        print(row)

    print("\nThis shows how different parameters affect different aspects of the model.")

    return results


def main():
    """Main function to run OAT sensitivity analysis examples"""

    print("\n" + "=" * 70)
    print("  ONE-AT-A-TIME (OAT) SENSITIVITY ANALYSIS TUTORIAL")
    print("=" * 70)
    print("\nThis tutorial demonstrates local sensitivity analysis using the")
    print("One-at-a-Time method for the gas swelling model.\n")

    # Run basic example
    print("PART 1: Basic OAT Analysis")
    print("Running comprehensive OAT analysis on all key parameters...\n")
    results1 = run_basic_oat_example()

    # Ask if user wants to continue
    print("\n" + "-" * 70)
    response = input("\nWould you like to see the custom analysis example? (y/n): ")

    if response.lower() == 'y':
        results2 = run_custom_oat_example()

    print_section_header("Tutorial Complete!")

    print("\nKey Takeaways:")
    print("  1. OAT analysis identifies which parameters most strongly affect outputs")
    print("  2. Elasticity measures the percent change in output per percent change in parameter")
    print("  3. Positive/negative signs indicate the direction of the effect")
    print("  4. Results are local - valid only near the nominal parameter values")

    print("\nNext Steps:")
    print("  - Try different parameter ranges to explore other regions")
    print("  - Use Morris method for global sensitivity analysis")
    print("  - Use Sobol analysis to quantify parameter interactions")
    print("  - Apply to your specific use case with custom parameters")

    print("\nFor more information, see:")
    print("  - examples/sensitivity_morris_example.py (global screening)")
    print("  - examples/sensitivity_sobol_example.py (variance-based analysis)")
    print("  - docs/sensitivity_analysis_guide.md (detailed guide)")
    print("\n")


if __name__ == "__main__":
    main()
