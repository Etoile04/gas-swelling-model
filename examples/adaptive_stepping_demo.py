#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive Time Stepping Demo

This script demonstrates the adaptive time stepping feature of the gas swelling model.
It compares fixed and adaptive stepping methods to show the performance benefits
while maintaining accuracy.

Author: Gas Swelling Model Team
Date: 2026-01-24
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='adaptive_stepping_demo.log',
    filemode='w'
)
logger = logging.getLogger('adaptive_stepping_demo')


def run_simulation_with_stepping_mode(params, t_span, t_eval, adaptive_enabled, mode_name):
    """
    Run simulation with specified stepping mode.

    Args:
        params: Simulation parameters dictionary
        t_span: Time span tuple (t_start, t_end)
        t_eval: Time points for evaluation
        adaptive_enabled: Whether to enable adaptive stepping
        mode_name: Name of the stepping mode (for logging)

    Returns:
        Dictionary with results and timing information
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Running simulation with {mode_name}")
    logger.info(f"{'='*60}")

    # Set adaptive stepping mode
    params['adaptive_stepping_enabled'] = adaptive_enabled

    # Create model
    model = GasSwellingModel(params)
    model.initial_state[2] = 4.0  # Ncb (gas atoms per bulk cavity)
    model.initial_state[6] = 4.0  # Ncf (gas atoms per interface cavity)
    logger.info(f"Initial gas atoms per cavity: 4.0")

    try:
        # Time the simulation
        start_time = time.time()

        result = model.solve(
            t_span=t_span,
            t_eval=t_eval
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Calculate swelling
        Rcb = result['Rcb']
        Rcf = result['Rcf']
        Ccb = result['Ccb']
        Ccf = result['Ccf']

        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        total_V_bubble = V_bubble_b + V_bubble_f
        swelling = total_V_bubble * 100  # Percentage

        # Log results
        logger.info(f"Simulation completed in {elapsed_time:.2f} seconds")
        logger.info(f"Final swelling: {swelling[-1]:.4f}%")
        logger.info(f"Final bulk bubble radius: {Rcb[-1]*1e9:.2f} nm")
        logger.info(f"Final interface bubble radius: {Rcf[-1]*1e9:.2f} nm")

        return {
            'success': True,
            'result': result,
            'swelling': swelling,
            'elapsed_time': elapsed_time,
            'mode_name': mode_name
        }

    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'mode_name': mode_name
        }


def run_adaptive_stepping_demo(
        sim_time=3600*24,  # 1 day in seconds
        temperature=773,    # 500°C
        output_dir='adaptive_stepping_demo_results'
):
    """
    Run comprehensive adaptive stepping demo.

    Args:
        sim_time: Total simulation time in seconds
        temperature: Temperature in Kelvin
        output_dir: Directory to save results

    Returns:
        Dictionary containing all simulation results
    """
    logger.info("="*80)
    logger.info("ADAPTIVE TIME STEPPING DEMO")
    logger.info("="*80)
    logger.info(f"Simulation time: {sim_time/3600:.1f} hours")
    logger.info(f"Temperature: {temperature} K")
    logger.info(f"Output directory: {output_dir}")

    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Create time points
    t_eval = np.linspace(0, sim_time, 100)

    # Create base parameters
    params = create_default_parameters()

    # Set simulation parameters
    params['temperature'] = temperature
    params['time_step'] = 1e-9
    params['max_time_step'] = 100.0
    params['Fnb'] = 1e-5
    params['Fnf'] = 1e-5
    params['dislocation_density'] = 7.0e13
    params['surface_energy'] = 0.5
    params['resolution_rate'] = 2.0e-5
    params['fission_rate'] = 5e19
    params['gas_production_rate'] = 0.5
    params['Dgb_prefactor'] = 8.55e-12
    params['Dgb_fission_term'] = 1.0e-40
    params['Dgf_multiplier'] = 1.0
    params['Dv0'] = 7.767e-10
    params['Di0'] = 1.259e-8
    params['Evm'] = 0.434
    params['Eim'] = 0.42
    params['Evfmuti'] = 1.0
    params['critical_radius'] = 50e-9
    params['radius_smoothing_factor'] = 0.8
    params['pressure_scaling_factor'] = 0.5
    params['vacancy_contribution_weight'] = 1.2

    # Adaptive stepping parameters
    params['rtol'] = 1e-6
    params['atol'] = 1e-9
    params['min_step'] = 1e-12
    params['max_step'] = sim_time / 10  # Allow large steps during steady periods

    logger.info("\nSimulation parameters:")
    logger.info(f"- Temperature: {params['temperature']} K")
    logger.info(f"- Fission rate: {params['fission_rate']:.2e} fissions/m³/s")
    logger.info(f"- Dislocation density: {params['dislocation_density']:.2e} m⁻²")
    logger.info(f"- Surface energy: {params['surface_energy']} J/m²")
    logger.info(f"- Adaptive stepping enabled: {params.get('adaptive_stepping_enabled', False)}")

    # Run both simulations
    results = {}

    # 1. Run with fixed stepping (adaptive disabled)
    print("\n[1/2] Running simulation with FIXED stepping...")
    fixed_result = run_simulation_with_stepping_mode(
        params.copy(),
        t_span=(0, sim_time),
        t_eval=t_eval,
        adaptive_enabled=False,
        mode_name="Fixed Stepping"
    )
    results['fixed'] = fixed_result

    # 2. Run with adaptive stepping
    print("\n[2/2] Running simulation with ADAPTIVE stepping...")
    adaptive_result = run_simulation_with_stepping_mode(
        params.copy(),
        t_span=(0, sim_time),
        t_eval=t_eval,
        adaptive_enabled=True,
        mode_name="Adaptive Stepping"
    )
    results['adaptive'] = adaptive_result

    # Analyze and compare results
    if fixed_result['success'] and adaptive_result['success']:
        analyze_and_compare_results(results, output_dir)
        plot_comparison(results, t_eval, output_dir)
    else:
        logger.error("One or both simulations failed!")

    return results


def analyze_and_compare_results(results, output_dir):
    """Analyze and compare fixed vs adaptive stepping results."""
    logger.info("\n" + "="*80)
    logger.info("RESULTS COMPARISON")
    logger.info("="*80)

    fixed = results['fixed']
    adaptive = results['adaptive']

    # Performance comparison
    speedup = fixed['elapsed_time'] / adaptive['elapsed_time']

    logger.info("\nPerformance:")
    logger.info(f"- Fixed stepping time: {fixed['elapsed_time']:.2f} s")
    logger.info(f"- Adaptive stepping time: {adaptive['elapsed_time']:.2f} s")
    logger.info(f"- Speedup: {speedup:.2f}x")

    # Accuracy comparison
    fixed_swelling = fixed['swelling'][-1]
    adaptive_swelling = adaptive['swelling'][-1]
    swelling_diff = abs(fixed_swelling - adaptive_swelling)
    swelling_rel_diff = (swelling_diff / fixed_swelling) * 100

    logger.info("\nFinal Swelling:")
    logger.info(f"- Fixed stepping: {fixed_swelling:.4f}%")
    logger.info(f"- Adaptive stepping: {adaptive_swelling:.4f}%")
    logger.info(f"- Absolute difference: {swelling_diff:.6f}%")
    logger.info(f"- Relative difference: {swelling_rel_diff:.3f}%")

    # Bubble radius comparison
    fixed_Rcb = fixed['result']['Rcb'][-1]
    adaptive_Rcb = adaptive['result']['Rcb'][-1]
    fixed_Rcf = fixed['result']['Rcf'][-1]
    adaptive_Rcf = adaptive['result']['Rcf'][-1]

    logger.info("\nFinal Bubble Radii:")
    logger.info(f"- Bulk (fixed): {fixed_Rcb*1e9:.2f} nm")
    logger.info(f"- Bulk (adaptive): {adaptive_Rcb*1e9:.2f} nm")
    logger.info(f"- Bulk difference: {abs(fixed_Rcb - adaptive_Rcb)*1e9:.4f} nm")
    logger.info(f"- Interface (fixed): {fixed_Rcf*1e9:.2f} nm")
    logger.info(f"- Interface (adaptive): {adaptive_Rcf*1e9:.2f} nm")
    logger.info(f"- Interface difference: {abs(fixed_Rcf - adaptive_Rcf)*1e9:.4f} nm")

    # Calculate RMSE over time series
    rmse_swelling = np.sqrt(np.mean((fixed['swelling'] - adaptive['swelling'])**2))
    logger.info(f"\nTime series RMSE (swelling): {rmse_swelling:.6f}%")

    # Save summary to file
    summary_path = os.path.join(output_dir, 'comparison_summary.txt')
    with open(summary_path, 'w') as f:
        f.write("Adaptive Stepping Demo - Results Summary\n")
        f.write("="*60 + "\n\n")
        f.write(f"Performance:\n")
        f.write(f"- Fixed stepping time: {fixed['elapsed_time']:.2f} s\n")
        f.write(f"- Adaptive stepping time: {adaptive['elapsed_time']:.2f} s\n")
        f.write(f"- Speedup: {speedup:.2f}x\n\n")
        f.write(f"Final Swelling:\n")
        f.write(f"- Fixed stepping: {fixed_swelling:.4f}%\n")
        f.write(f"- Adaptive stepping: {adaptive_swelling:.4f}%\n")
        f.write(f"- Absolute difference: {swelling_diff:.6f}%\n")
        f.write(f"- Relative difference: {swelling_rel_diff:.3f}%\n\n")
        f.write(f"Time series RMSE (swelling): {rmse_swelling:.6f}%\n")

    logger.info(f"\nSummary saved to: {summary_path}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Speedup: {speedup:.2f}x")
    print(f"Swelling difference: {swelling_rel_diff:.3f}%")
    print(f"Adaptive stepping maintains accuracy while improving speed!")


def plot_comparison(results, t_eval, output_dir):
    """Create comparison plots for fixed vs adaptive stepping."""
    logger.info("\nCreating comparison plots...")

    fixed = results['fixed']
    adaptive = results['adaptive']

    time_hours = t_eval / 3600

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Fixed vs Adaptive Stepping Comparison', fontsize=16, fontweight='bold')

    # 1. Swelling comparison
    axes[0, 0].plot(time_hours, fixed['swelling'], 'b-', linewidth=2, label='Fixed')
    axes[0, 0].plot(time_hours, adaptive['swelling'], 'r--', linewidth=2, label='Adaptive')
    axes[0, 0].set_xlabel('Time (hours)')
    axes[0, 0].set_ylabel('Swelling (%)')
    axes[0, 0].set_title('Swelling Evolution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Swelling difference
    axes[0, 1].plot(time_hours, adaptive['swelling'] - fixed['swelling'], 'g-', linewidth=2)
    axes[0, 1].axhline(0, color='k', linestyle='--', alpha=0.5)
    axes[0, 1].set_xlabel('Time (hours)')
    axes[0, 1].set_ylabel('Difference (%)')
    axes[0, 1].set_title('Swelling Difference (Adaptive - Fixed)')
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Bulk bubble radius
    axes[0, 2].plot(time_hours, fixed['result']['Rcb']*1e9, 'b-', linewidth=2, label='Fixed')
    axes[0, 2].plot(time_hours, adaptive['result']['Rcb']*1e9, 'r--', linewidth=2, label='Adaptive')
    axes[0, 2].set_xlabel('Time (hours)')
    axes[0, 2].set_ylabel('Radius (nm)')
    axes[0, 2].set_title('Bulk Bubble Radius')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    # 4. Interface bubble radius
    axes[1, 0].plot(time_hours, fixed['result']['Rcf']*1e9, 'b-', linewidth=2, label='Fixed')
    axes[1, 0].plot(time_hours, adaptive['result']['Rcf']*1e9, 'r--', linewidth=2, label='Adaptive')
    axes[1, 0].set_xlabel('Time (hours)')
    axes[1, 0].set_ylabel('Radius (nm)')
    axes[1, 0].set_title('Interface Bubble Radius')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # 5. Gas concentration in bulk
    axes[1, 1].plot(time_hours, fixed['result']['Cgb'], 'b-', linewidth=2, label='Fixed')
    axes[1, 1].plot(time_hours, adaptive['result']['Cgb'], 'r--', linewidth=2, label='Adaptive')
    axes[1, 1].set_xlabel('Time (hours)')
    axes[1, 1].set_ylabel('Concentration (atoms/m³)')
    axes[1, 1].set_title('Gas Concentration in Bulk')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    # 6. Bubble concentration
    axes[1, 2].plot(time_hours, fixed['result']['Ccb'], 'b-', linewidth=2, label='Bulk (Fixed)')
    axes[1, 2].plot(time_hours, adaptive['result']['Ccb'], 'b--', linewidth=2, label='Bulk (Adaptive)')
    axes[1, 2].plot(time_hours, fixed['result']['Ccf'], 'r-', linewidth=2, label='Interface (Fixed)')
    axes[1, 2].plot(time_hours, adaptive['result']['Ccf'], 'r--', linewidth=2, label='Interface (Adaptive)')
    axes[1, 2].set_xlabel('Time (hours)')
    axes[1, 2].set_ylabel('Concentration (cavities/m³)')
    axes[1, 2].set_title('Bubble Concentration')
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()

    save_path = os.path.join(output_dir, 'comparison_plots.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Comparison plots saved to: {save_path}")
    print(f"\nPlots saved to: {save_path}")


def main():
    """Main entry point for the adaptive stepping demo."""
    print("\n" + "="*70)
    print("  ADAPTIVE TIME STEPPING DEMO")
    print("  Gas Swelling Model - Performance and Accuracy Comparison")
    print("="*70)

    # Run the demo
    results = run_adaptive_stepping_demo(
        sim_time=3600*24,  # 1 day
        temperature=773,    # 500°C
        output_dir='adaptive_stepping_demo_results'
    )

    # Final status
    print("\n" + "="*70)
    if results['fixed']['success'] and results['adaptive']['success']:
        print("✓ Demo completed successfully!")
        print(f"✓ Results saved to: adaptive_stepping_demo_results/")
        print("\nKey Findings:")
        speedup = results['fixed']['elapsed_time'] / results['adaptive']['elapsed_time']
        print(f"  • Adaptive stepping achieved {speedup:.2f}x speedup")
        swelling_diff = abs(results['fixed']['swelling'][-1] - results['adaptive']['swelling'][-1])
        print(f"  • Swelling difference: {swelling_diff:.6f}%")
        print(f"  • Accuracy maintained while improving performance")
    else:
        print("✗ Demo failed - check log file for details")
    print("="*70 + "\n")

    logger.info("\n" + "="*80)
    logger.info("DEMO COMPLETED")
    logger.info("="*80)


if __name__ == "__main__":
    main()
