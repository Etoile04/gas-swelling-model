#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensitivity Analysis Tutorial for Gas Swelling Model
====================================================

This tutorial provides a comprehensive guide to parameter sensitivity analysis
for the gas swelling model using three different methods:

1. One-at-a-Time (OAT): Local sensitivity analysis
2. Morris Method: Global screening analysis
3. Sobol Method: Variance-based global sensitivity analysis

What is Sensitivity Analysis?
-----------------------------
Sensitivity analysis helps us understand how different input parameters affect
model outputs. It answers questions like:
- Which parameters have the greatest influence on swelling?
- How sensitive is the model to changes in temperature, fission rate, etc.?
- Are there interactions between parameters?
- Which parameters need to be measured most accurately?

Why do we need it?
------------------
- Model validation: Understand which parameters drive predictions
- Uncertainty quantification: Identify sources of prediction uncertainty
- Experimental design: Focus measurement efforts on important parameters
- Model reduction: Fix insensitive parameters to simplify the model
- Confidence building: Demonstrate robustness to parameter variations

Physics Background:
------------------
The gas swelling model simulates fission gas bubble evolution in nuclear fuel.
Key parameters that affect swelling include:
- Temperature: Affects gas diffusion and bubble growth
- Fission rate: Determines gas production rate
- Dislocation density: Influences defect sink strength
- Surface energy: Controls bubble stability
- Nucleation factors (Fnb, Fnf): Affect bubble number density

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.analysis.sensitivity import (
    OATAnalyzer,
    MorrisAnalyzer,
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


def print_subsection(title):
    """Print a formatted subsection header"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)


# ============================================================================
# PART 1: ONE-AT-A-TIME (OAT) SENSITIVITY ANALYSIS
# ============================================================================

def tutorial_part1_oat_analysis():
    """
    Part 1: One-at-a-Time (OAT) Sensitivity Analysis

    OAT analysis varies one parameter at a time while keeping all others
    at their nominal values. This is the simplest form of sensitivity analysis.

    Pros:
    - Easy to understand and interpret
    - Computationally inexpensive
    - Good for initial parameter screening

    Cons:
    - Does not capture parameter interactions
    - Only provides local sensitivity (near nominal values)
    - May miss nonlinear effects
    """

    print_section_header("PART 1: ONE-AT-A-TIME (OAT) SENSITIVITY ANALYSIS")

    print("\nWhat is OAT Analysis?")
    print("-" * 70)
    print("OAT analysis varies one parameter at a time while keeping all other")
    print("parameters at their nominal (baseline) values. This helps identify:")
    print()
    print("  1. Which parameters have the strongest influence on model outputs")
    print("  2. The direction of parameter effects (positive/negative correlation)")
    print("  3. Approximate linear sensitivity around nominal parameter values")
    print()
    print("Best used for:")
    print("  - Initial screening to identify important parameters")
    print("  - Understanding local parameter sensitivities")
    print("  - Quick sensitivity assessment with limited computational resources")

    print_subsection("Step 1: Define Parameter Ranges")

    # Create parameter ranges for OAT analysis
    param_ranges = create_default_parameter_ranges()

    print("\nWe'll analyze the following parameters:")
    for i, pr in enumerate(param_ranges, 1):
        print(f"  {i}. {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}]")
        print(f"     Nominal = {pr.nominal_value:.3g}, Distribution = {pr.distribution}")

    print_subsection("Step 2: Initialize OAT Analyzer")

    # Create OAT analyzer
    analyzer = OATAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=7200000.0,  # 83.3 days
        t_eval_points=100
    )

    print(f"\nAnalyzer configuration:")
    print(f"  Number of parameters: {analyzer.get_n_parameters()}")
    print(f"  Simulation time: {analyzer.sim_time:.1f}s ({analyzer.sim_time/86400:.2f} days)")
    print(f"  Output metric: swelling (%)")

    print_subsection("Step 3: Run OAT Analysis")

    # Define percentage variations
    percent_variations = [-20, -10, 10, 20]

    print(f"\nTesting variations: {percent_variations}%")
    print("Each parameter will be varied by these percentages while")
    print("all other parameters remain at their nominal values.")
    print()
    print("Running analysis... (this may take a few minutes)")

    # Run the analysis
    results = analyzer.run_oat_analysis(
        percent_variations=percent_variations,
        verbose=True
    )

    print_subsection("Step 4: Interpret OAT Results")

    print("\nParameter Ranking by Elasticity:")
    print("-" * 70)
    print("Elasticity measures the percent change in output per percent change in input.")
    print("Higher values indicate greater sensitivity.")
    print()

    # Sort parameters by elasticity
    ranking = []
    for result in results:
        elasticity = abs(result.sensitivities['swelling']['elasticity'])
        ranking.append((result.parameter_name, elasticity, result))

    ranking.sort(key=lambda x: x[1], reverse=True)

    for i, (name, elasticity, result) in enumerate(ranking, 1):
        sens = result.sensitivities['swelling']
        print(f"{i}. {name:20s}:")
        print(f"   Elasticity = {sens['elasticity']:+.3f}")
        print(f"   Normalized = {sens['normalized']:.3f} ± {sens['std']:.3f}")
        print(f"   Baseline swelling = {result.baseline_outputs['swelling']:.4f}%")
        print()

    print_subsection("Step 5: Visualize OAT Results")

    # Create visualization
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('OAT Sensitivity Analysis Results', fontsize=14, fontweight='bold')

    # Plot tornado plot
    ax_tornado = axes[0, 0]
    param_names = [r[0] for r in ranking]
    elasticities = [r[1] for r in ranking]
    y_pos = np.arange(len(param_names))

    colors = ['red' if e > 0 else 'blue' for e in elasticities]
    ax_tornado.barh(y_pos, elasticities, color=colors, alpha=0.7)
    ax_tornado.set_yticks(y_pos)
    ax_tornado.set_yticklabels(param_names)
    ax_tornado.set_xlabel('Elasticity (|dY/Y| / |dX/X|)')
    ax_tornado.set_title('Parameter Importance (Tornado Plot)')
    ax_tornado.grid(True, alpha=0.3, axis='x')

    # Plot parameter variations
    for idx, (name, elasticity, result) in enumerate(ranking[:5]):
        if idx >= 5:
            break
        ax = axes[1 + idx // 3, idx % 3]

        variations = np.array(result.variations)
        outputs = result.outputs['swelling']
        nominal = result.nominal_value
        baseline = result.baseline_outputs['swelling']

        # Calculate percent change
        pct_change_param = (variations - nominal) / nominal * 100
        pct_change_output = (outputs - baseline) / baseline * 100

        ax.plot(pct_change_param, pct_change_output, 'o-', linewidth=2, markersize=8)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)
        ax.set_xlabel(f'{name} change (%)')
        ax.set_ylabel('Swelling change (%)')
        ax.set_title(name)
        ax.grid(True, alpha=0.3)

    # Hide empty subplot
    axes[0, 1].axis('off')
    axes[0, 2].axis('off')

    plt.tight_layout()
    filename = 'sensitivity_tutorial_oat_results.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nOAT results plot saved to: {filename}")
    plt.show()

    return results, ranking


# ============================================================================
# PART 2: MORRIS ELEMENTARY EFFECTS ANALYSIS
# ============================================================================

def tutorial_part2_morris_analysis():
    """
    Part 2: Morris Elementary Effects Screening

    The Morris method is a global sensitivity analysis technique that
    explores the entire parameter space by computing "elementary effects"
    along random trajectories.

    Pros:
    - Captures nonlinear effects and parameter interactions
    - More efficient than variance-based methods for screening
    - Provides both influence (μ*) and nonlinearity (σ) measures

    Cons:
    - Less precise than Sobol analysis
    - Requires careful choice of number of trajectories
    - Results can vary with different random seeds
    """

    print_section_header("PART 2: MORRIS ELEMENTARY EFFECTS SCREENING")

    print("\nWhat is Morris Analysis?")
    print("-" * 70)
    print("The Morris method computes 'elementary effects' by varying one")
    print("parameter at a time along random trajectories through parameter space.")
    print()
    print("Key statistics:")
    print("  • μ (mu): Mean of elementary effects (can cancel out)")
    print("  • μ* (mu_star): Mean of absolute effects (overall influence)")
    print("  • σ (sigma): Standard deviation (nonlinearity/interactions)")
    print()
    print("Best used for:")
    print("  - Screening many parameters efficiently")
    print("  - Identifying parameters with nonlinear effects")
    print("  - Detecting parameter interactions")

    print_subsection("Step 1: Define Parameter Ranges")

    # Use fewer parameters for Morris to keep computation time reasonable
    param_ranges = create_default_parameter_ranges()[:4]  # First 4 parameters

    print("\nWe'll analyze the following parameters:")
    for i, pr in enumerate(param_ranges, 1):
        print(f"  {i}. {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}]")

    print_subsection("Step 2: Initialize Morris Analyzer")

    # Create Morris analyzer
    analyzer = MorrisAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=7200000.0,
        t_eval_points=100,
        num_levels=10,  # Discretization levels
        delta=None  # Will use default: p/(2(p-1))
    )

    print(f"\nAnalyzer configuration:")
    print(f"  Number of parameters: {analyzer.get_n_parameters()}")
    print(f"  Discretization levels: {analyzer.num_levels}")
    print(f"  Delta (step size): {analyzer.delta:.3f}")
    print(f"  Simulation time: {analyzer.sim_time:.1f}s ({analyzer.sim_time/86400:.2f} days)")

    print_subsection("Step 3: Run Morris Analysis")

    # Number of trajectories
    n_trajectories = 20

    print(f"\nNumber of trajectories: {n_trajectories}")
    print(f"Total simulations: {n_trajectories * (analyzer.get_n_parameters() + 1)}")
    print()
    print("Running analysis... (this may take several minutes)")

    # Run the analysis
    results = analyzer.run_morris_analysis(
        n_trajectories=n_trajectories,
        verbose=True,
        random_state=42  # For reproducibility
    )

    print_subsection("Step 4: Interpret Morris Results")

    print("\nMorris Statistics:")
    print("-" * 70)
    print("Parameters are ranked by μ* (mu_star), which measures overall influence.")
    print("High σ indicates nonlinear effects or parameter interactions.")
    print()

    ranking = results.get_ranking('swelling')

    for i, (name, mu_star) in enumerate(ranking, 1):
        idx = results.parameter_names.index(name)
        mu = results.mu[idx]
        sigma = results.sigma[idx]

        print(f"{i}. {name:20s}:")
        print(f"   μ*  = {mu_star:.3f} (overall influence)")
        print(f"   μ   = {mu:.3f} (mean effect)")
        print(f"   σ   = {sigma:.3f} (nonlinearity/interactions)")
        print()

    print_subsection("Step 5: Visualize Morris Results")

    # Create Morris plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract data
    param_names = results.parameter_names
    mu_star = results.mu_star
    sigma = results.sigma

    # Color by sign of mu
    colors = ['red' if mu > 0 else 'blue' for mu in results.mu]

    # Create scatter plot
    scatter = ax.scatter(mu_star, sigma, c=colors, s=100, alpha=0.7, edgecolors='black')

    # Add parameter labels
    for i, name in enumerate(param_names):
        ax.annotate(name, (mu_star[i], sigma[i]),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=9, fontweight='bold')

    ax.set_xlabel('μ* (mu_star) - Overall Influence', fontsize=12)
    ax.set_ylabel('σ (sigma) - Nonlinearity/Interactions', fontsize=12)
    ax.set_title('Morris Elementary Effects Results', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.7, label='Positive effect (μ > 0)'),
        Patch(facecolor='blue', alpha=0.7, label='Negative effect (μ < 0)')
    ]
    ax.legend(handles=legend_elements, loc='upper left')

    plt.tight_layout()
    filename = 'sensitivity_tutorial_morris_results.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nMorris results plot saved to: {filename}")
    plt.show()

    return results, ranking


# ============================================================================
# PART 3: SOBOL VARIANCE-BASED SENSITIVITY ANALYSIS
# ============================================================================

def tutorial_part3_sobol_analysis():
    """
    Part 3: Sobol Variance-Based Sensitivity Analysis

    Sobol analysis is a comprehensive global sensitivity method that
    decomposes the output variance into contributions from each parameter.

    Pros:
    - Provides rigorous variance decomposition
    - Quantifies both main effects (S1) and total effects (ST)
    - Captures all parameter interactions

    Cons:
    - Computationally expensive (many simulations required)
    - Can be overkill for simple screening
    - Requires careful convergence analysis
    """

    print_section_header("PART 3: SOBOL VARIANCE-BASED SENSITIVITY ANALYSIS")

    print("\nWhat is Sobol Analysis?")
    print("-" * 70)
    print("Sobol analysis decomposes the output variance into contributions")
    print("from each parameter and their interactions.")
    print()
    print("Key indices:")
    print("  • S1 (first-order): Fraction of variance due to each parameter alone")
    print("  • ST (total-order): Fraction including all interactions")
    print("  • (S2, S3, ...): Higher-order interaction effects")
    print()
    print("Interpretation:")
    print("  - High S1: Parameter has strong main effect")
    print("  - High ST but low S1: Parameter mainly affects through interactions")
    print("  - ST - S1: Measures interaction strength")
    print()
    print("Best used for:")
    print("  - Comprehensive sensitivity assessment")
    print("  - Quantifying parameter interactions")
    print("  - Final validation after screening methods")

    print_subsection("Step 1: Define Parameter Ranges")

    # Use even fewer parameters for Sobol (computationally intensive)
    param_ranges = create_default_parameter_ranges()[:3]  # First 3 parameters

    print("\nWe'll analyze the following parameters:")
    for i, pr in enumerate(param_ranges, 1):
        print(f"  {i}. {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}]")

    print_subsection("Step 2: Initialize Sobol Analyzer")

    # Create Sobol analyzer
    analyzer = SobolAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],
        sim_time=7200000.0,
        t_eval_points=100
    )

    print(f"\nAnalyzer configuration:")
    print(f"  Number of parameters: {analyzer.get_n_parameters()}")
    print(f"  Simulation time: {analyzer.sim_time:.1f}s ({analyzer.sim_time/86400:.2f} days)")

    print_subsection("Step 3: Determine Sample Size")

    # Choose sample size
    n_samples = 100

    n_simulations = n_samples * (2 + analyzer.get_n_parameters())
    print(f"\nSample size per matrix (N): {n_samples}")
    print(f"Total simulations needed: {n_simulations}")
    print()
    print("Note: Sobol analysis is computationally intensive!")
    print("      For production use, consider N = 500-1000 for robust results.")

    print_subsection("Step 4: Run Sobol Analysis")

    print("\nRunning analysis... (this will take several minutes)")
    print("Please be patient...")

    # Run the analysis
    results = analyzer.run_sobol_analysis(
        n_samples=n_samples,
        verbose=True,
        random_state=42
    )

    print_subsection("Step 5: Interpret Sobol Results")

    print("\nSobol Indices:")
    print("-" * 70)
    print("Parameters are ranked by total-order index (ST).")
    print()

    ranking = results.get_ranking('swelling', order='ST')

    for i, (name, st) in enumerate(ranking, 1):
        idx = results.parameter_names.index(name)
        s1 = results.S1[idx, 0]
        interaction = st - s1

        print(f"{i}. {name:20s}:")
        print(f"   ST = {st:.3f} (total effect)")
        print(f"   S1 = {s1:.3f} (main effect)")
        print(f"   Interaction = {interaction:.3f}")
        print()

    print_subsection("Step 6: Visualize Sobol Results")

    # Create Sobol plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Sobol Variance-Based Sensitivity Analysis', fontsize=14, fontweight='bold')

    # Extract data
    param_names = results.parameter_names
    s1 = results.S1[:, 0]
    st = results.ST[:, 0]
    interactions = st - s1

    y_pos = np.arange(len(param_names))

    # Plot 1: First-order (S1) and Total-order (ST)
    axes[0].barh(y_pos, s1, color='steelblue', alpha=0.7, label='S1 (main effect)')
    axes[0].barh(y_pos, interactions, left=s1, color='coral', alpha=0.7, label='Interactions')
    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(param_names)
    axes[0].set_xlabel('Variance Fraction')
    axes[0].set_title('First-Order (S1) vs Total-Order (ST)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='x')
    axes[0].set_xlim(0, 1)

    # Plot 2: Direct comparison of S1 and ST
    axes[1].scatter(s1, st, s=100, alpha=0.7, edgecolors='black')
    axes[1].plot([0, 1], [0, 1], 'k--', alpha=0.3, label='S1 = ST (no interactions)')

    # Add parameter labels
    for i, name in enumerate(param_names):
        axes[1].annotate(name, (s1[i], st[i]),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9, fontweight='bold')

    axes[1].set_xlabel('S1 (first-order)', fontsize=12)
    axes[1].set_ylabel('ST (total-order)', fontsize=12)
    axes[1].set_title('Interaction Plot (ST vs S1)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)

    plt.tight_layout()
    filename = 'sensitivity_tutorial_sobol_results.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nSobol results plot saved to: {filename}")
    plt.show()

    return results, ranking


# ============================================================================
# PART 4: COMPARISON AND RECOMMENDATIONS
# ============================================================================

def tutorial_part4_comparison():
    """
    Part 4: Comparison of Methods and Recommendations

    This section compares the three sensitivity analysis methods and provides
    guidance on when to use each one.
    """

    print_section_header("PART 4: METHOD COMPARISON AND RECOMMENDATIONS")

    print("\nComparison of Sensitivity Analysis Methods:")
    print("=" * 70)

    # Create comparison table
    comparison = """
    ┌─────────────────────┬──────────────┬──────────────┬──────────────┐
    │ Feature             │     OAT      │   Morris     │    Sobol     │
    ├─────────────────────┼──────────────┼──────────────┼──────────────┤
    │ Type                │ Local        │ Global       │ Global       │
    │ Computational cost  │ Low          │ Medium       │ High         │
    │ Captures            │ Linear only  │ Nonlinear    │ Nonlinear    │
    │ interactions        │ No           │ Partially    │ Yes          │
    │ Output metrics      │ Elasticity   │ μ*, μ, σ     │ S1, ST       │
    │ Ease of use         │ High         │ Medium       │ Medium       │
    │ Best for            │ Screening    │ Screening    │ Comprehensive│
    └─────────────────────┴──────────────┴──────────────┴──────────────┘
    """
    print(comparison)

    print("\nRecommended Workflow:")
    print("-" * 70)
    print()
    print("1. Start with OAT analysis")
    print("   - Quick screening of many parameters")
    print("   - Identify obviously important/unimportant parameters")
    print("   - Understand local sensitivities")
    print()
    print("2. Follow up with Morris analysis")
    print("   - Explore nonlinear effects")
    print("   - Detect parameter interactions")
    print("   - Refine parameter ranking")
    print()
    print("3. Finalize with Sobol analysis (if needed)")
    print("   - Quantify variance contributions")
    print("   - Measure interaction strengths")
    print("   - Provide rigorous sensitivity metrics")
    print()
    print("When to use each method:")
    print("-" * 70)
    print("  • OAT: Initial exploration, limited computational resources")
    print("  • Morris: Medium-complexity models, screening many parameters")
    print("  • Sobol: Final validation, detailed interaction analysis")

    print("\nKey Principles:")
    print("-" * 70)
    print()
    print("1. Start simple, then add complexity")
    print("   → Use OAT first to narrow down parameter list")
    print()
    print("2. Balance accuracy and computational cost")
    print("   → Morris often provides best cost/benefit ratio")
    print()
    print("3. Consider your goals")
    print("   → Screening? Use Morris")
    print("   → Publishing? Use Sobol for rigor")
    print("   → Quick check? Use OAT")
    print()
    print("4. Validate your results")
    print("   → Compare results from different methods")
    print("   → Check convergence (increase sample sizes)")
    print("   → Use multiple random seeds for Morris/Sobol")


# ============================================================================
# MAIN TUTORIAL FLOW
# ============================================================================

def main():
    """Main tutorial function"""

    print("\n" + "=" * 70)
    print("  GAS SWELLING MODEL - SENSITIVITY ANALYSIS TUTORIAL")
    print("=" * 70)
    print()
    print("Welcome! This tutorial will guide you through three different")
    print("sensitivity analysis methods for the gas swelling model.")
    print()
    print("You will learn:")
    print("  1. One-at-a-Time (OAT) analysis - local sensitivity")
    print("  2. Morris method - global screening")
    print("  3. Sobol method - variance-based analysis")
    print()
    print("Each method has different strengths and is suited for different tasks.")
    print()

    # Ask which parts to run
    print("This tutorial has 4 parts:")
    print("  Part 1: OAT Sensitivity Analysis (fast, ~2 minutes)")
    print("  Part 2: Morris Elementary Effects (medium, ~5 minutes)")
    print("  Part 3: Sobol Variance-Based Analysis (slow, ~10 minutes)")
    print("  Part 4: Method Comparison and Recommendations (instant)")
    print()
    print("You can run any combination of these parts.")
    print()

    response = input("Run all parts? (y/n): ").strip().lower()

    if response == 'y':
        run_oat = True
        run_morris = True
        run_sobol = True
        run_comparison = True
    else:
        run_oat = input("Run Part 1 (OAT)? (y/n): ").strip().lower() == 'y'
        run_morris = input("Run Part 2 (Morris)? (y/n): ").strip().lower() == 'y'
        run_sobol = input("Run Part 3 (Sobol)? (y/n): ").strip().lower() == 'y'
        run_comparison = input("Run Part 4 (Comparison)? (y/n): ").strip().lower() == 'y'

    print()

    # Run selected parts
    if run_oat:
        try:
            tutorial_part1_oat_analysis()
        except Exception as e:
            print(f"\nError in OAT analysis: {e}")
            print("Continuing to next part...")

    if run_morris:
        try:
            tutorial_part2_morris_analysis()
        except Exception as e:
            print(f"\nError in Morris analysis: {e}")
            print("Continuing to next part...")

    if run_sobol:
        try:
            tutorial_part3_sobol_analysis()
        except Exception as e:
            print(f"\nError in Sobol analysis: {e}")
            print("Continuing to next part...")

    if run_comparison:
        try:
            tutorial_part4_comparison()
        except Exception as e:
            print(f"\nError in comparison: {e}")

    print_section_header("Tutorial Complete!")
    print()
    print("Congratulations! You've completed the Sensitivity Analysis Tutorial.")
    print()
    print("Key takeaways:")
    print("  • OAT is quick and simple but local")
    print("  • Morris balances global exploration with computational cost")
    print("  • Sobol provides the most comprehensive analysis")
    print()
    print("Next steps:")
    print("  - Try these methods on your own parameters")
    print("  - Experiment with different sample sizes")
    print("  - Compare results across methods")
    print("  - Check out the individual example scripts for more details")
    print()
    print("For more information, see:")
    print("  - examples/sensitivity_oat_example.py")
    print("  - examples/sensitivity_morris_example.py")
    print("  - examples/sensitivity_sobol_example.py")
    print("  - gas_swelling/analysis/sensitivity.py")
    print()


if __name__ == "__main__":
    main()
