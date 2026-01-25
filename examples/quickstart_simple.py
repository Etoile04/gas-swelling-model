#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start Simple - Fast Tutorial
===================================

A fast, minimal tutorial to get you running quickly.
Demonstrates basic gas swelling simulation.

Note: Runtime can vary from 3-10 minutes depending on your system
due to the computational complexity of solving stiff ODE systems.
The simulation uses minimal parameters (5 days, 5 time points) for
speed while still demonstrating key features.

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Configure matplotlib
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def main():
    """Run a quick gas swelling simulation"""

    print("\n" + "=" * 60)
    print("  GAS SWELLING MODEL - QUICK START (FAST)")
    print("=" * 60)

    # Step 1: Create parameters with defaults
    print("\n[1/4] Creating model with default parameters...")
    params = create_default_parameters()
    print(f"  Temperature: {params['temperature']} K")
    print(f"  Fission rate: {params['fission_rate']:.2e} fissions/(m³·s)")

    # Step 2: Create model
    print("\n[2/4] Initializing model...")
    model = GasSwellingModel(params)
    print(f"  Model tracks {len(model.initial_state)} state variables")

    # Step 3: Set up simulation (shorter for speed)
    print("\n[3/4] Setting up simulation...")
    sim_time_days = 5  # Very short simulation for speed
    sim_time = sim_time_days * 24 * 3600
    t_eval = np.linspace(0, sim_time, 5)  # Minimal time points
    print(f"  Simulation time: {sim_time_days} days")
    print(f"  Time points: {len(t_eval)}")

    # Step 4: Run simulation
    print("\n[4/4] Running simulation...")
    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
    print("  ✓ Simulation complete!")

    # Display results
    time_days = result['time'] / (24 * 3600)

    # Calculate key metrics
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    print("\n" + "-" * 60)
    print("RESULTS:")
    print("-" * 60)
    print(f"  Final bulk bubble radius: {result['Rcb'][-1]*1e9:.2f} nm")
    print(f"  Final boundary bubble radius: {result['Rcf'][-1]*1e9:.2f} nm")
    print(f"  Final swelling: {swelling[-1]:.4f}%")
    print(f"  Gas released: {result['released_gas'][-1]:.2e} atoms/m³")

    # Create simplified plot (3 panels instead of 6)
    print("\nCreating visualization...")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Gas Swelling Simulation (Fast Results)', fontsize=14, fontweight='bold')

    # Panel 1: Bubble radius
    axes[0, 0].plot(time_days, result['Rcb'] * 1e9, label='Bulk', linewidth=2)
    axes[0, 0].plot(time_days, result['Rcf'] * 1e9, label='Boundary', linewidth=2)
    axes[0, 0].set_xlabel('Time (days)')
    axes[0, 0].set_ylabel('Radius (nm)')
    axes[0, 0].set_title('Bubble Radius')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Panel 2: Swelling
    axes[0, 1].plot(time_days, swelling, color='red', linewidth=2)
    axes[0, 1].set_xlabel('Time (days)')
    axes[0, 1].set_ylabel('Swelling (%)')
    axes[0, 1].set_title('Fuel Swelling')
    axes[0, 1].grid(True, alpha=0.3)

    # Panel 3: Gas atoms per bubble
    axes[1, 0].plot(time_days, result['Ncb'], label='Bulk', linewidth=2)
    axes[1, 0].plot(time_days, result['Ncf'], label='Boundary', linewidth=2)
    axes[1, 0].set_xlabel('Time (days)')
    axes[1, 0].set_ylabel('Gas atoms per bubble')
    axes[1, 0].set_title('Gas in Bubbles')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Panel 4: Bubble concentration
    axes[1, 1].semilogy(time_days, result['Ccb'], label='Bulk', linewidth=2)
    axes[1, 1].semilogy(time_days, result['Ccf'], label='Boundary', linewidth=2)
    axes[1, 1].set_xlabel('Time (days)')
    axes[1, 1].set_ylabel('Concentration (m⁻³)')
    axes[1, 1].set_title('Bubble Concentration')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    output_file = 'quickstart_simple_results.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✓ Plot saved to: {output_file}")

    print("\n" + "=" * 60)
    print("SUCCESS! Simulation completed")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Try quickstart_tutorial.py for detailed explanations")
    print("  - Modify parameters and experiment")
    print("  - Check docs/ for more examples\n")

    return result


if __name__ == "__main__":
    main()
