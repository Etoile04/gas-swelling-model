#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sobol Variance-Based Sensitivity Analysis Example
==================================================

This example demonstrates how to perform a global sensitivity analysis
using the Sobol variance-based method for the gas swelling model.

What is Sobol Sensitivity Analysis?
------------------------------------
Sobol analysis is a variance-based method that decomposes the output variance
into contributions from individual parameters and their interactions. It provides
quantitative sensitivity indices based on variance decomposition.

Key Indices:
- S1 (first-order): Fraction of output variance due to each parameter alone
- ST (total-order): Fraction due to each parameter including all interactions

The method decomposes output variance as:
V(Y) = Σ_i V_i + Σ_i Σ_{j>i} V_{ij} + Σ_i Σ_{j>i} Σ_{k>j} V_{ijk} + ...

where:
- V_i: Variance due to parameter i alone (main effect)
- V_{ij}: Variance due to interaction between i and j
- V_{ijk}: Variance due to three-way interaction, etc.

When to use Sobol?
- Quantitative sensitivity analysis with precise error estimates
- Understanding parameter interactions (ST - S1 ≈ interaction strength)
- Validating models with many input parameters
- When computational budget allows for extensive sampling

Advantages:
- Provides rigorous quantitative sensitivity measures
- Captures parameter interactions through (ST - S1)
- Model-independent (works with any computational model)
- Comprehensive exploration of parameter space

Limitations:
- Computationally expensive (requires N × (2 + p) simulations)
- Cost scales linearly with number of parameters
- May require large N for accurate confidence intervals

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.analysis.sensitivity import (
    SobolAnalyzer,
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


def run_basic_sobol_example():
    """
    Run a basic Sobol analysis with default parameters.

    This example uses pre-defined parameter ranges for key model parameters
    and analyzes their effect on fuel swelling using the Sobol method.
    """

    print_section_header("STEP 1: Set Up Sobol Analyzer")

    print("Creating Sobol analyzer with default parameter ranges...")
    print("The following parameters will be analyzed:")

    # Create default parameter ranges
    param_ranges = create_default_parameter_ranges()

    for pr in param_ranges:
        print(f"  - {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}], nominal={pr.nominal_value:.3g}")

    # Initialize analyzer
    analyzer = SobolAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],  # Analyze effect on swelling
        sim_time=7200000.0,         # 83.3 days (shorter for demonstration)
        t_eval_points=100,
        calc_second_order=False    # Set to True for interaction indices (expensive)
    )

    print(f"\nAnalyzer configuration:")
    print(f"  - Number of parameters: {analyzer.get_n_parameters()}")
    print(f"  - Simulation time: {analyzer.sim_time:.1f}s ({analyzer.sim_time/86400:.2f} days)")
    print(f"  - Output metric: swelling (%)")

    print_section_header("STEP 2: Run Sobol Analysis")

    # Number of samples per matrix
    # Total simulations = n_samples × (2 + n_parameters)
    n_samples = 100
    n_simulations = n_samples * (2 + analyzer.get_n_parameters())

    print(f"\nBase samples (N): {n_samples}")
    print(f"Total simulations: {n_simulations}")
    print("\nGenerating Saltelli sample sequence and computing variance decomposition...\n")

    # Run the analysis
    results = analyzer.run_sobol_analysis(
        n_samples=n_samples,
        verbose=True,
        random_state=42,  # For reproducibility
        track_convergence=False  # Set to True to analyze convergence
    )

    print_section_header("STEP 3: Analyze Results")

    print("\nSobol Sensitivity Indices (ranked by total-order ST):")
    print("-" * 75)
    print(f"{'Parameter':<25} {'S1':<10} {'ST':<10} {'ST - S1':<12} {'Interactions':<12}")
    print("-" * 75)

    # Sort results by ST (descending)
    ranking = results.get_ranking('swelling', order='ST')

    for param_name, ST in ranking:
        param_idx = results.parameter_names.index(param_name)
        S1 = results.S1[param_idx, 0]  # First output (swelling)
        interactions = ST - S1

        # Classify interaction strength
        if interactions > 0.3:
            interaction_strength = "Strong"
        elif interactions > 0.1:
            interaction_strength = "Moderate"
        else:
            interaction_strength = "Weak"

        print(f"{param_name:<25} {S1:>9.3f} {ST:>9.3f} {interactions:>11.3f} {interaction_strength:<12}")

    print("\nInterpretation:")
    print("  - S1 (first-order): Main effect - variance due to parameter alone")
    print("  - ST (total-order): Total effect - including all interactions")
    print("  - ST - S1: Interaction effect - higher values = stronger interactions")
    print("  - Sum of S1: Should be < 1.0 (remaining = interactions)")
    print("  - Parameters with high ST are most important overall")

    # Check variance decomposition
    sum_S1 = np.sum(results.S1[:, 0])
    print(f"\nVariance decomposition check:")
    print(f"  - Sum of first-order indices: {sum_S1:.3f}")
    print(f"  - Remaining (interactions + higher-order): {1 - sum_S1:.3f}")

    print_section_header("STEP 4: Visualize Results")

    # Create Sobol analysis plots
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 1. First-order vs Total-order comparison
    ax1 = fig.add_subplot(gs[0, :])

    param_names = results.parameter_names
    S1_values = results.S1[:, 0]
    ST_values = results.ST[:, 0]

    x = np.arange(len(param_names))
    width = 0.35

    bars1 = ax1.bar(x - width/2, S1_values, width, label='S1 (First-order)',
                    color='steelblue', alpha=0.7, edgecolor='black')
    bars2 = ax1.bar(x + width/2, ST_values, width, label='ST (Total-order)',
                    color='coral', alpha=0.7, edgecolor='black')

    ax1.set_xlabel('Parameters', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Sobol Index', fontsize=11, fontweight='bold')
    ax1.set_title('First-Order (S1) vs Total-Order (ST) Sobol Indices',
                  fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(param_names, rotation=45, ha='right')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=8)

    # 2. Parameter ranking by total-order index
    ax2 = fig.add_subplot(gs[1, 0])

    sorted_indices = np.argsort(ST_values)[::-1]
    sorted_names = [param_names[i] for i in sorted_indices]
    sorted_ST = [ST_values[i] for i in sorted_indices]
    sorted_S1 = [S1_values[i] for i in sorted_indices]

    colors = ['coral' if st > 0.5 else 'wheat' for st in sorted_ST]
    bars = ax2.barh(sorted_names, sorted_ST, color=colors, alpha=0.7, edgecolor='black')

    # Add first-order indicators
    for i, (bar, s1) in enumerate(zip(bars, sorted_S1)):
        bar_st = bar.get_width()
        ax2.barh(i, s1, color='steelblue', alpha=0.5, edgecolor='black')
        ax2.text(bar_st, i, f' ST={bar_st:.3f}', va='center', fontsize=9, fontweight='bold')

    ax2.set_xlabel('Sobol Index', fontsize=11, fontweight='bold')
    ax2.set_title('Parameter Ranking by Total Influence (ST)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='steelblue', alpha=0.5, label='S1 (main effect)'),
        Patch(facecolor='coral', alpha=0.7, label='ST (total effect)')
    ]
    ax2.legend(handles=legend_elements, fontsize=9)

    # 3. Interaction effects (ST - S1)
    ax3 = fig.add_subplot(gs[1, 1])

    interactions = ST_values - S1_values
    sorted_indices_int = np.argsort(interactions)[::-1]
    sorted_names_int = [param_names[i] for i in sorted_indices_int]
    sorted_int = [interactions[i] for i in sorted_indices_int]

    colors_int = ['red' if val > 0.2 else 'orange' if val > 0.1 else 'lightgreen'
                  for val in sorted_int]

    bars = ax3.barh(sorted_names_int, sorted_int, color=colors_int,
                    alpha=0.7, edgecolor='black')

    ax3.set_xlabel('ST - S1 (Interaction Effect)', fontsize=11, fontweight='bold')
    ax3.set_title('Parameter Interaction Strength', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    ax3.axvline(x=0, color='black', linestyle='-', linewidth=1)

    # Add value labels
    for bar, val in zip(bars, sorted_int):
        ax3.text(val, bar.get_y() + bar.get_height()/2,
                f' {val:.3f}', va='center', fontsize=9)

    # Save figure
    output_filename = 'sobol_sensitivity_analysis.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_filename}")
    plt.show()

    return results


def run_custom_sobol_example():
    """
    Demonstrate custom Sobol analysis with multiple outputs.

    This example shows how to analyze multiple output metrics and
    interpret the results comprehensively.
    """

    print_section_header("BONUS: Custom Multi-Output Sobol Analysis")

    print("\nDefining custom parameter ranges...")
    print("Analyzing multiple output metrics simultaneously...\n")

    # Select key parameters for detailed analysis
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
            distribution='loguniform'
        ),
        ParameterRange(
            name='fission_rate',
            min_value=1.5e20,
            max_value=2.5e20,
            nominal_value=2.0e20,
            distribution='uniform'
        )
    ]

    # Create analyzer with multiple outputs
    analyzer = SobolAnalyzer(
        parameter_ranges=custom_params,
        output_names=['swelling', 'max_swelling', 'final_bubble_radius_bulk'],
        sim_time=7200000.0,
        t_eval_points=100,
        calc_second_order=False
    )

    print(f"Custom Sobol configuration:")
    print(f"  - Parameters: {analyzer.get_n_parameters()}")
    print(f"  - Outputs: {analyzer.output_names}")
    print()

    # Run analysis with reduced samples for demo
    print("Running Sobol analysis with reduced samples for demonstration...")
    n_samples = 50  # Reduced for faster demo
    results = analyzer.run_sobol_analysis(
        n_samples=n_samples,
        verbose=True,
        random_state=42
    )

    # Display multi-output results
    print_section_header("Multi-Output Sensitivity Comparison")

    print("\nParameter ranking across different outputs:")
    print("-" * 85)

    for output_idx, output_name in enumerate(results.output_names):
        print(f"\n{output_name.upper()}:")
        print(f"{'Parameter':<25} {'S1':<10} {'ST':<10} {'Interaction':<15} {'Rank':<5}")
        print("-" * 85)

        ranking = results.get_ranking(output_name, order='ST')

        for rank, (param_name, ST) in enumerate(ranking, 1):
            param_idx = results.parameter_names.index(param_name)
            S1 = results.S1[param_idx, output_idx]
            interaction = ST - S1

            interaction_str = f"{interaction:.3f}"
            if interaction > 0.2:
                interaction_str += " (Strong)"
            elif interaction > 0.1:
                interaction_str += " (Mod)"

            print(f"{param_name:<25} {S1:>9.3f} {ST:>9.3f} {interaction_str:<15} {rank:<5}")

    print("\n" + "=" * 85)
    print("Interpretation:")

    # Find consistent influential parameters
    print("\n1. Consistently Important Parameters:")
    print("   Parameters that rank high across multiple outputs:")
    all_rankings = {}
    for output_name in results.output_names:
        ranking = results.get_ranking(output_name, order='ST')
        for rank, (param_name, _) in enumerate(ranking, 1):
            if param_name not in all_rankings:
                all_rankings[param_name] = []
            all_rankings[param_name].append(rank)

    # Compute average rank
    avg_ranks = {name: np.mean(ranks) for name, ranks in all_rankings.items()}
    top_params = sorted(avg_ranks.items(), key=lambda x: x[1])[:3]

    for param_name, avg_rank in top_params:
        print(f"   - {param_name}: Average rank = {avg_rank:.1f}")

    print("\n2. Output-Specific Parameters:")
    print("   Parameters that strongly affect specific outputs:")
    for output_name in results.output_names:
        output_idx = results.output_names.index(output_name)
        max_ST_idx = np.argmax(results.ST[:, output_idx])
        param_name = results.parameter_names[max_ST_idx]
        ST_value = results.ST[max_ST_idx, output_idx]

        print(f"   - {output_name}: {param_name} (ST = {ST_value:.3f})")

    print("\n3. Interaction Patterns:")
    print("   Parameters with strong interaction effects:")
    for output_name in results.output_names:
        output_idx = results.output_names.index(output_name)
        max_int_idx = np.argmax(results.ST[:, output_idx] - results.S1[:, output_idx])
        param_name = results.parameter_names[max_int_idx]
        interaction = (results.ST[max_int_idx, output_idx] -
                      results.S1[max_int_idx, output_idx])

        if interaction > 0.1:
            print(f"   - {output_name}: {param_name} (ST - S1 = {interaction:.3f})")

    return results


def main():
    """Main function to run Sobol sensitivity analysis examples"""

    print("\n" + "=" * 70)
    print("  SOBOL VARIANCE-BASED SENSITIVITY ANALYSIS TUTORIAL")
    print("=" * 70)
    print("\nThis tutorial demonstrates quantitative global sensitivity analysis")
    print("using the Sobol variance decomposition method.\n")

    # Run basic example
    print("PART 1: Basic Sobol Analysis")
    print("Running comprehensive Sobol analysis on all key parameters...\n")
    results1 = run_basic_sobol_example()

    # Ask if user wants to continue
    print("\n" + "-" * 70)
    response = input("\nWould you like to see the multi-output analysis example? (y/n): ")

    if response.lower() == 'y':
        results2 = run_custom_sobol_example()

    print_section_header("Tutorial Complete!")

    print("\nKey Takeaways:")
    print("  1. Sobol analysis provides quantitative sensitivity indices")
    print("  2. S1 measures main effects (parameter acting alone)")
    print("  3. ST measures total effects (including all interactions)")
    print("  4. ST - S1 quantifies interaction strength")
    print("  5. Sum of S1 < 1 indicates parameter interactions are important")

    print("\nWhen to use Sobol vs other methods:")
    print("  - Sobol: Quantitative analysis, interaction assessment")
    print("  - Morris: Efficient screening, many parameters")
    print("  - OAT: Quick local analysis, limited parameters")

    print("\nPractical Guidelines:")
    print("  - Use N ≥ 100 for reliable results")
    print("  - Total cost = N × (2 + p) simulations")
    print("  - For p = 6 parameters and N = 100: ~800 simulations needed")
    print("  - Increase N if confidence intervals are large")

    print("\nNext Steps:")
    print("  - Use results to prioritize calibration efforts")
    print("  - Focus on high-ST parameters for uncertainty reduction")
    print("  - Investigate high-interaction parameters with targeted studies")
    print("  - Consider fixing low-ST parameters at nominal values")

    print("\nFor more information, see:")
    print("  - examples/sensitivity_oat_example.py (local sensitivity)")
    print("  - examples/sensitivity_morris_example.py (screening method)")
    print("  - docs/sensitivity_analysis_guide.md (detailed guide)")
    print("\n")


if __name__ == "__main__":
    main()
