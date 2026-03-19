#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start Tutorial for Gas Swelling Model
===========================================

This tutorial demonstrates how to run a basic simulation of fission gas
bubble evolution in nuclear fuel materials.

What this model does:
- Simulates the formation and growth of gas bubbles in irradiated fuel
- Tracks gas atoms, vacancies, and bubble evolution over time
- Calculates swelling (volume expansion) due to bubble formation

Physics background:
- During nuclear fission, gas atoms (Xe, Kr) are produced
- These gas atoms diffuse through the fuel material
- They can nucleate bubbles or accumulate at existing bubbles
- Bubbles grow by absorbing gas atoms and vacancies
- This causes the fuel to swell (expand)

Author: Gas Swelling Model Team
"""

import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# Set up matplotlib for better plotting
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_basic_simulation():
    """
    Run a basic gas swelling simulation with default parameters.

    This is the simplest way to get started - just use the default
    parameters and run the model!
    """

    print_section_header("STEP 1: Create Default Parameters")

    # The model comes with reasonable default parameters
    # You can inspect and modify these as needed
    params = create_default_parameters()

    # Let's see what the main parameters are
    print(f"Temperature: {params['temperature']} K")
    print(f"Fission rate: {params['fission_rate']:.2e} fissions/(m³·s)")
    print(f"Dislocation density: {params['dislocation_density']:.2e} m⁻²")
    print(f"Surface energy: {params['surface_energy']} J/m²")

    print("\nThese parameters represent typical reactor conditions.")

    print_section_header("STEP 2: Create the Model")

    # Create a model instance with our parameters
    model = GasSwellingModel(params)

    print("Model created successfully!")
    print(f"The model tracks {len(model.initial_state)} state variables:")
    print("  1. Gas atoms in bulk matrix")
    print("  2. Gas atoms at phase boundaries")
    print("  3. Bubble concentration in bulk")
    print("  4. Bubble concentration at boundaries")
    print("  5. Gas atoms per bulk bubble")
    print("  6. Gas atoms per boundary bubble")
    print("  7. Vacancy concentration in bulk")
    print("  8. Vacancy concentration at boundaries")
    print("  9. Interstitial concentration in bulk")
    print(" 10. Interstitial concentration at boundaries")

    print_section_header("STEP 3: Set Up Simulation Time")

    # Simulate 100 days of irradiation
    simulation_time_days = 100
    simulation_time_seconds = simulation_time_days * 24 * 3600

    print(f"Simulation time: {simulation_time_days} days ({simulation_time_seconds:.2e} seconds)")

    # Create time points where we want to evaluate the solution
    # The solver will adaptively choose intermediate time steps
    num_time_points = 100
    t_eval = np.linspace(0, simulation_time_seconds, num_time_points)

    print(f"Number of output time points: {num_time_points}")

    print_section_header("STEP 4: Run the Simulation")

    print("Solving the system of differential equations...")
    print("(This may take a moment...)")

    # Solve the system of ODEs
    result = model.solve(
        t_span=(0, simulation_time_seconds),  # Time range
        t_eval=t_eval                         # Evaluation points
    )

    print("Simulation completed successfully!")

    print_section_header("STEP 5: Examine the Results")

    # The result dictionary contains all state variables over time
    print("\nKey results at the end of simulation:")

    # Convert time to days for easier interpretation
    time_days = result['time'] / (24 * 3600)

    # Final bubble radii
    final_Rcb = result['Rcb'][-1] * 1e9  # Convert to nm
    final_Rcf = result['Rcf'][-1] * 1e9  # Convert to nm
    print(f"  Final bulk bubble radius: {final_Rcb:.2f} nm")
    print(f"  Final boundary bubble radius: {final_Rcf:.2f} nm")

    # Calculate final swelling
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb'][-1]**3 * result['Ccb'][-1]
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf'][-1]**3 * result['Ccf'][-1]
    total_V_bubble = V_bubble_b + V_bubble_f
    final_swelling = total_V_bubble * 100  # Convert to percent

    print(f"  Final swelling: {final_swelling:.4f}%")

    # Gas distribution
    gas_in_bulk = result['Cgb'][-1]
    gas_in_boundaries = result['Cgf'][-1]
    gas_in_bulk_bubbles = result['Ccb'][-1] * result['Ncb'][-1]
    gas_in_boundary_bubbles = result['Ccf'][-1] * result['Ncf'][-1]
    gas_released = result['released_gas'][-1]

    total_gas = (gas_in_bulk + gas_in_boundaries +
                 gas_in_bulk_bubbles + gas_in_boundary_bubbles + gas_released)

    if total_gas > 0:
        print(f"\n  Gas distribution:")
        print(f"    In bulk matrix: {gas_in_bulk/total_gas*100:.1f}%")
        print(f"    In boundaries: {gas_in_boundaries/total_gas*100:.1f}%")
        print(f"    In bulk bubbles: {gas_in_bulk_bubbles/total_gas*100:.1f}%")
        print(f"    In boundary bubbles: {gas_in_boundary_bubbles/total_gas*100:.1f}%")
        print(f"    Released: {gas_released/total_gas*100:.1f}%")

    print_section_header("STEP 6: Visualize the Results")

    # Create a multi-panel plot
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Gas Swelling Simulation Results', fontsize=14, fontweight='bold')

    # 1. Bubble radius evolution
    axes[0, 0].plot(time_days, result['Rcb'] * 1e9, label='Bulk bubbles', linewidth=2)
    axes[0, 0].plot(time_days, result['Rcf'] * 1e9, label='Boundary bubbles', linewidth=2)
    axes[0, 0].set_xlabel('Time (days)')
    axes[0, 0].set_ylabel('Bubble radius (nm)')
    axes[0, 0].set_title('Bubble Radius Evolution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Swelling evolution
    # Calculate swelling over time
    V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
    V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
    swelling = (V_bubble_b + V_bubble_f) * 100

    axes[0, 1].plot(time_days, swelling, linewidth=2, color='red')
    axes[0, 1].set_xlabel('Time (days)')
    axes[0, 1].set_ylabel('Swelling (%)')
    axes[0, 1].set_title('Fuel Swelling Evolution')
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Bubble concentration evolution
    axes[0, 2].semilogy(time_days, result['Ccb'], label='Bulk bubbles', linewidth=2)
    axes[0, 2].semilogy(time_days, result['Ccf'], label='Boundary bubbles', linewidth=2)
    axes[0, 2].set_xlabel('Time (days)')
    axes[0, 2].set_ylabel('Bubble concentration (m⁻³)')
    axes[0, 2].set_title('Bubble Concentration')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    # 4. Gas atoms per bubble
    axes[1, 0].plot(time_days, result['Ncb'], label='Bulk bubbles', linewidth=2)
    axes[1, 0].plot(time_days, result['Ncf'], label='Boundary bubbles', linewidth=2)
    axes[1, 0].set_xlabel('Time (days)')
    axes[1, 0].set_ylabel('Gas atoms per bubble')
    axes[1, 0].set_title('Gas Accumulation in Bubbles')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # 5. Gas concentration in matrix
    axes[1, 1].plot(time_days, result['Cgb'], label='Bulk matrix', linewidth=2)
    axes[1, 1].plot(time_days, result['Cgf'], label='Boundaries', linewidth=2)
    axes[1, 1].set_xlabel('Time (days)')
    axes[1, 1].set_ylabel('Gas concentration (atoms/m³)')
    axes[1, 1].set_title('Gas in Solution')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    # 6. Gas release
    axes[1, 2].plot(time_days, result['released_gas'], linewidth=2, color='purple')
    axes[1, 2].set_xlabel('Time (days)')
    axes[1, 2].set_ylabel('Released gas (atoms/m³)')
    axes[1, 2].set_title('Cumulative Gas Release')
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()

    # Save the figure
    output_filename = 'quickstart_results.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_filename}")

    # Also display it if running interactively
    plt.show()

    return result


def run_temperature_comparison():
    """
    Compare swelling at different temperatures.

    This demonstrates how to modify parameters and run multiple simulations.
    """

    print_section_header("BONUS: Temperature Comparison Study")

    temperatures = [600, 700, 800, 900]  # Kelvin
    print(f"\nComparing swelling at temperatures: {temperatures} K")

    results_list = []

    for temp in temperatures:
        print(f"\nRunning simulation at {temp} K...")

        # Create parameters and modify temperature
        params = create_default_parameters()
        params['temperature'] = temp

        # Create model and run
        model = GasSwellingModel(params)

        sim_time = 100 * 24 * 3600  # 100 days
        t_eval = np.linspace(0, sim_time, 100)

        result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

        # Calculate swelling
        V_bubble_b = (4.0/3.0) * np.pi * result['Rcb']**3 * result['Ccb']
        V_bubble_f = (4.0/3.0) * np.pi * result['Rcf']**3 * result['Ccf']
        swelling = (V_bubble_b + V_bubble_f) * 100

        results_list.append({
            'temperature': temp,
            'time_days': result['time'] / (24 * 3600),
            'swelling': swelling
        })

        print(f"  Final swelling: {swelling[-1]:.4f}%")

    # Plot comparison
    plt.figure(figsize=(10, 6))

    for result in results_list:
        plt.plot(result['time_days'], result['swelling'],
                label=f"{result['temperature']} K", linewidth=2)

    plt.xlabel('Time (days)')
    plt.ylabel('Swelling (%)')
    plt.title('Effect of Temperature on Fuel Swelling')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_filename = 'quickstart_temperature_comparison.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nTemperature comparison plot saved to: {output_filename}")
    plt.show()


def main():
    """Main function to run the quick start tutorial"""

    print("\n" + "=" * 70)
    print("  GAS SWELLING MODEL - QUICK START TUTORIAL")
    print("=" * 70)
    print("\nWelcome! This tutorial will guide you through running your first")
    print("gas swelling simulation. Let's get started!\n")

    # Run the basic simulation
    result = run_basic_simulation()

    # Offer to run temperature comparison
    print("\n" + "-" * 70)
    response = input("\nWould you like to see a temperature comparison study? (y/n): ")

    if response.lower() == 'y':
        run_temperature_comparison()

    print_section_header("Tutorial Complete!")
    print("\nCongratulations! You've run your first gas swelling simulations.")
    print("\nNext steps:")
    print("  - Explore different parameters (temperature, fission rate, etc.)")
    print("  - Check out the Jupyter notebook examples for interactive analysis")
    print("  - Read the parameter reference guide for detailed parameter info")
    print("  - Look at the advanced examples for temperature sweeps and more")
    print("\nFor more information, see the documentation in the docs/ directory.")
    print("\n")


if __name__ == "__main__":
    main()
