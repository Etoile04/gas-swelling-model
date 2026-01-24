#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Morris Elementary Effects Screening Example
===========================================

This example demonstrates how to perform a global sensitivity analysis
using the Morris elementary effects method for the gas swelling model.

What is Morris Sensitivity Analysis?
-------------------------------------
Morris analysis is a global screening method that computes elementary effects
by varying one parameter at a time along random trajectories through the
parameter space. It's efficient for screening many parameters.

Key Statistics:
- μ (mu): Mean of elementary effects (overall influence)
- μ* (mu_star): Mean of absolute elementary effects (overall influence magnitude)
- σ (sigma): Standard deviation of effects (nonlinearity/interactions)

When to use Morris?
- Initial screening of many parameters (efficient compared to Sobol)
- Identifying influential vs non-influential parameters
- Understanding nonlinearity and parameter interactions
- Global sensitivity analysis with limited computational budget

Advantages:
- More efficient than variance-based methods for screening
- Captures global parameter space effects
- Identifies nonlinearity through σ (high σ = strong nonlinearity/interactions)

Limitations:
- Provides qualitative rather than quantitative sensitivity measures
- Doesn't separate interaction effects from higher-order effects
- Less accurate than Sobol for detailed analysis

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.analysis.sensitivity import (
    MorrisAnalyzer,
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


def run_basic_morris_example():
    """
    Run a basic Morris screening analysis with default parameters.

    This example uses pre-defined parameter ranges for key model parameters
    and analyzes their effect on fuel swelling using the Morris method.
    """

    print_section_header("STEP 1: Set Up Morris Analyzer")

    print("Creating Morris analyzer with default parameter ranges...")
    print("The following parameters will be analyzed:")

    # Create default parameter ranges
    param_ranges = create_default_parameter_ranges()

    for pr in param_ranges:
        print(f"  - {pr.name:20s}: [{pr.min_value:.3g}, {pr.max_value:.3g}], nominal={pr.nominal_value:.3g}")

    # Initialize analyzer
    analyzer = MorrisAnalyzer(
        parameter_ranges=param_ranges,
        output_names=['swelling'],  # Analyze effect on swelling
        sim_time=7200000.0,         # 83.3 days (shorter for demonstration)
        t_eval_points=100,
        num_levels=10,              # Discretization levels
        delta=None                  # Auto-compute step size
    )

    print(f"\nAnalyzer configuration:")
    print(f"  - Number of parameters: {analyzer.get_n_parameters()}")
    print(f"  - Simulation time: {analyzer.sim_time:.1f}s ({analyzer.sim_time/86400:.2f} days)")
    print(f"  - Discretization levels: {analyzer.num_levels}")
    print(f"  - Delta (step size): {analyzer.delta:.3f}")
    print(f"  - Output metric: swelling (%)")

    print_section_header("STEP 2: Run Morris Screening")

    # Number of trajectories (more = better accuracy, but more expensive)
    n_trajectories = 20

    print(f"\nNumber of trajectories: {n_trajectories}")
    print(f"Total simulations: {n_trajectories * (analyzer.get_n_parameters() + 1)}")
    print("\nGenerating random trajectories and computing elementary effects...\n")

    # Run the analysis
    results = analyzer.run_morris_analysis(
        n_trajectories=n_trajectories,
        verbose=True,
        random_state=42  # For reproducibility
    )

    print_section_header("STEP 3: Analyze Results")

    print("\nMorris Screening Results (ranked by μ*):")
    print("-" * 70)
    print(f"{'Parameter':<25} {'μ*':<10} {'μ':<10} {'σ':<10} {'Type':<15}")
    print("-" * 70)

    # Sort results by mu_star (descending)
    ranking = results.get_ranking('swelling')

    for param_name, mu_star in ranking:
        param_idx = results.parameter_names.index(param_name)
        mu = results.mu[param_idx]
        sigma = results.sigma[param_idx]

        # Classify parameter influence
        if mu_star > 1.0:
            influence = "Very High"
        elif mu_star > 0.5:
            influence = "High"
        elif mu_star > 0.1:
            influence = "Moderate"
        else:
            influence = "Low"

        # Classify nonlinearity/interactions
        if sigma > mu_star:
            behavior = "Strongly nonlinear/interacting"
        elif sigma > mu_star / 2:
            behavior = "Moderately nonlinear"
        else:
            behavior = "Approximately linear"

        print(f"{param_name:<25} {mu_star:>9.3f} {mu:>9.3f} {sigma:>9.3f} {influence:<15}")

    print("\nInterpretation:")
    print("  - μ* (mu_star): Mean absolute effect - measures overall influence")
    print("  - μ (mu): Mean effect - can cancel out if effects have opposite signs")
    print("  - σ (sigma): Standard deviation - high σ indicates nonlinearity/interactions")
    print("  - Parameters with high μ* and high σ are important and nonlinear")

    print_section_header("STEP 4: Visualize Results")

    # Create Morris screening plot (μ* vs σ)
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 1. Classic Morris plot: μ* vs σ
    ax1 = fig.add_subplot(gs[0, 0])

    colors = plt.cm.viridis(np.linspace(0, 1, len(results.parameter_names)))
    for i, param_name in enumerate(results.parameter_names):
        ax1.scatter(results.sigma[i], results.mu_star[i],
                   s=200, c=[colors[i]], alpha=0.7, edgecolors='black', linewidth=1.5)
        ax1.annotate(param_name, (results.sigma[i], results.mu_star[i]),
                    fontsize=9, ha='left', va='bottom')

    ax1.set_xlabel('σ (sigma) - Standard Deviation', fontsize=11, fontweight='bold')
    ax1.set_ylabel('μ* (mu_star) - Mean Absolute Effect', fontsize=11, fontweight='bold')
    ax1.set_title('Morris Screening Plot\n(μ* vs σ)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Add quadrant lines
    mean_mu_star = np.mean(results.mu_star)
    mean_sigma = np.mean(results.sigma)
    ax1.axhline(y=mean_mu_star, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axvline(x=mean_sigma, color='red', linestyle='--', linewidth=1, alpha=0.5)

    # 2. Parameter ranking by μ*
    ax2 = fig.add_subplot(gs[0, 1])

    sorted_indices = np.argsort(results.mu_star)[::-1]
    sorted_names = [results.parameter_names[i] for i in sorted_indices]
    sorted_mu_star = results.mu_star[sorted_indices]

    bars = ax2.barh(sorted_names, sorted_mu_star, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('μ* (mu_star)', fontsize=11, fontweight='bold')
    ax2.set_title('Parameter Ranking by Influence', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, sorted_mu_star)):
        ax2.text(val, i, f' {val:.3f}', va='center', fontsize=9, fontweight='bold')

    # 3. μ vs μ* plot (sign and magnitude)
    ax3 = fig.add_subplot(gs[1, 0])

    for i, param_name in enumerate(results.parameter_names):
        ax3.scatter(results.mu[i], results.mu_star[i],
                   s=200, c=[colors[i]], alpha=0.7, edgecolors='black', linewidth=1.5)
        ax3.annotate(param_name, (results.mu[i], results.mu_star[i]),
                    fontsize=9, ha='left', va='bottom')

    ax3.set_xlabel('μ (mu) - Mean Effect', fontsize=11, fontweight='bold')
    ax3.set_ylabel('μ* (mu_star) - Mean Absolute Effect', fontsize=11, fontweight='bold')
    ax3.set_title('Effect Magnitude vs Direction\n(μ vs μ*)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # 4. Elementary effects distribution (box plot)
    ax4 = fig.add_subplot(gs[1, 1])

    # Get elementary effects for swelling
    ee_swelling = results.elementary_effects['swelling']

    # Create box plot
    bp = ax4.boxplot([ee_swelling[i, :] for i in range(len(results.parameter_names))],
                     labels=results.parameter_names,
                     patch_artist=True,
                     vert=False)

    # Color the boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax4.set_xlabel('Elementary Effect', fontsize=11, fontweight='bold')
    ax4.set_title('Distribution of Elementary Effects', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')
    ax4.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # Save figure
    output_filename = 'morris_sensitivity_analysis.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_filename}")
    plt.show()

    return results


def run_custom_morris_example():
    """
    Demonstrate custom Morris analysis with specific parameters.

    This example shows how to configure the Morris method for specific
    use cases and interpret the results.
    """

    print_section_header("BONUS: Custom Morris Analysis")

    print("\nDefining custom parameter ranges...")
    print("Focusing on key parameters affecting swelling...\n")

    # Select a subset of key parameters
    custom_params = [
        ParameterRange(
            name='temperature',
            min_value=600.0,
            max_value=800.0,
            nominal_value=700.0,
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
            name='surface_energy',
            min_value=0.4,
            max_value=0.6,
            nominal_value=0.5,
            distribution='uniform'
        ),
        ParameterRange(
            name='Fnb',
            min_value=5e-6,
            max_value=5e-5,
            nominal_value=1e-5,
            distribution='loguniform'
        )
    ]

    # Create analyzer with custom configuration
    analyzer = MorrisAnalyzer(
        parameter_ranges=custom_params,
        output_names=['swelling', 'max_swelling'],
        sim_time=7200000.0,
        t_eval_points=100,
        num_levels=8,  # Fewer levels for faster computation
        delta=None
    )

    print(f"Custom Morris configuration:")
    print(f"  - Parameters: {analyzer.get_n_parameters()}")
    print(f"  - Levels: {analyzer.num_levels}")
    print(f"  - Outputs: {analyzer.output_names}")
    print()

    # Run analysis with fewer trajectories for demo
    print("Running Morris analysis with reduced trajectories...")
    results = analyzer.run_morris_analysis(
        n_trajectories=10,
        verbose=True,
        random_state=42
    )

    # Interpret results
    print_section_header("Interpretation Guide")

    print("\n1. Identifying Influential Parameters:")
    print("   - High μ*: Parameter has strong overall effect on output")
    print("   - High μ* + Low σ: Important but approximately linear")
    print("   - High μ* + High σ: Important with strong nonlinear/interaction effects")

    print("\n2. Parameter Behavior Classification:")
    ranking = results.get_ranking('swelling')
    for param_name, mu_star in ranking[:3]:  # Top 3
        param_idx = results.parameter_names.index(param_name)
        mu = results.mu[param_idx]
        sigma = results.sigma[param_idx]

        print(f"\n   {param_name}:")
        print(f"     - Influence (μ*): {mu_star:.3f} - {'HIGH' if mu_star > 0.5 else 'MODERATE' if mu_star > 0.1 else 'LOW'}")
        print(f"     - Direction (μ): {mu:+.3f} - {'Positive effect' if mu > 0 else 'Negative effect'}")
        print(f"     - Nonlinearity (σ): {sigma:.3f} - {'HIGH' if sigma > mu_star/2 else 'LOW'}")

        if abs(mu) < mu_star / 2:
            print(f"     → Effects change sign across parameter space (complex behavior)")

    print("\n3. Recommendations:")
    print("   - Focus calibration efforts on high μ* parameters")
    print("   - For high σ parameters, consider interaction effects")
    print("   - Low μ* parameters can potentially be fixed at nominal values")

    return results


def main():
    """Main function to run Morris sensitivity analysis examples"""

    print("\n" + "=" * 70)
    print("  MORRIS ELEMENTARY EFFECTS SCREENING TUTORIAL")
    print("=" * 70)
    print("\nThis tutorial demonstrates global sensitivity screening using the")
    print("Morris elementary effects method for the gas swelling model.\n")

    # Run basic example
    print("PART 1: Basic Morris Screening")
    print("Running comprehensive Morris analysis on all key parameters...\n")
    results1 = run_basic_morris_example()

    # Ask if user wants to continue
    print("\n" + "-" * 70)
    response = input("\nWould you like to see the custom analysis example? (y/n): ")

    if response.lower() == 'y':
        results2 = run_custom_morris_example()

    print_section_header("Tutorial Complete!")

    print("\nKey Takeaways:")
    print("  1. Morris screening efficiently identifies influential parameters")
    print("  2. μ* measures overall influence (magnitude of effects)")
    print("  3. μ measures the direction of effects (can cancel out)")
    print("  4. σ indicates nonlinearity and parameter interactions")
    print("  5. High μ* + high σ = important and complex parameter")

    print("\nWhen to use Morris vs other methods:")
    print("  - Morris: Initial screening, many parameters, limited budget")
    print("  - Sobol: Detailed quantitative analysis, fewer parameters")
    print("  - OAT: Quick local analysis around nominal values")

    print("\nNext Steps:")
    print("  - Use results to prioritize calibration efforts")
    print("  - Fix low-influence parameters at nominal values")
    print("  - Apply Sobol analysis to high-μ* parameters for detailed study")
    print("  - Investigate high-σ parameters for interaction effects")

    print("\nFor more information, see:")
    print("  - examples/sensitivity_oat_example.py (local sensitivity)")
    print("  - examples/sensitivity_sobol_example.py (variance-based analysis)")
    print("  - docs/sensitivity_analysis_guide.md (detailed guide)")
    print("\n")


if __name__ == "__main__":
    main()
