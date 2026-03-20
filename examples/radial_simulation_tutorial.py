#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radial Simulation Tutorial for Gas Swelling Model
===================================================

This tutorial demonstrates how to run 1D radial simulations of fission gas
bubble evolution in nuclear fuel materials using the RadialGasSwellingModel.

What this model does:
- Extends the 0D model to capture spatial variations across the fuel pellet radius
- Uses a fast node-wise solve by default, with an optional fully coupled mode
- Calculates radial profiles of swelling, temperature, gas pressure, and more
- Simulates realistic conditions with temperature gradients and flux depression

Physics background:
- In real fuel pins, temperature varies from centerline to surface
- Fission rate can vary due to flux depression effects
- Gas atoms diffuse radially, creating spatial variations in bubble growth
- The 1D radial model captures these important spatial effects

Key differences from 0D model:
- Uses RadialMesh for spatial discretization (multiple nodes across radius)
- Each node has its own temperature and fission rate
- Optional fully coupled mode includes explicit radial diffusion between nodes
- Results are radial profiles instead of single values

Author: Gas Swelling Model Team
"""

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.radial_model import RadialGasSwellingModel
from gas_swelling.models.radial_mesh import RadialMesh
from gas_swelling.params.parameters import create_default_parameters
from gas_swelling.visualization.radial_plots import RadialProfilePlotter, create_radial_plotter

# Set up matplotlib for better plotting
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_radial_mesh_example():
    """
    Demonstrate how to create a radial mesh.

    The radial mesh defines the spatial discretization across the fuel pellet.
    """
    print_section_header("STEP 1: Create Radial Mesh")

    # Create a basic cylindrical mesh
    mesh = RadialMesh(
        n_nodes=10,           # Number of radial nodes
        radius=0.003,         # Fuel pellet radius (3 mm)
        geometry='cylindrical',
        spacing='uniform'     # Evenly spaced nodes
    )

    print(f"Created radial mesh:")
    print(f"  Number of nodes: {mesh.n_nodes}")
    print(f"  Pellet radius: {mesh.radius*1000:.2f} mm")
    print(f"  Geometry: {mesh.geometry}")
    print(f"  Spacing type: uniform")

    print("\nNode positions:")
    for i, r in enumerate(mesh.nodes):
        r_mm = r * 1000  # Convert to mm
        print(f"  Node {i:2d}: r = {r_mm:6.3f} mm")

    return mesh


def run_basic_radial_simulation():
    """
    Run a basic radial gas swelling simulation with uniform temperature.

    This is the simplest way to get started with radial simulations.
    """
    print_section_header("STEP 2: Basic Radial Simulation")

    # Create default parameters
    params = create_default_parameters()

    print(f"Simulation parameters:")
    print(f"  Temperature: {params['temperature']} K (uniform)")
    print(f"  Fission rate: {params['fission_rate']:.2e} fissions/(m³·s)")
    print(f"  Pellet radius: 3.0 mm")
    print(f"  Radial solver mode: {params['radial_solver_mode']}")

    print_section_header("STEP 3: Create Radial Model")

    # Create radial model with 10 nodes
    model = RadialGasSwellingModel(
        params=params,
        n_nodes=10,
        radius=0.003,
        geometry='cylindrical'
    )

    print(f"Model created: {model}")
    print(f"  Number of radial nodes: {model.n_nodes}")
    print(f"  State variables per node: 17")
    print(f"  Total state variables: {len(model.initial_state)}")
    print(f"  Solve mode: {model.params['radial_solver_mode']}")

    print_section_header("STEP 4: Set Up Simulation Time")

    # Simulate 100 days of irradiation
    simulation_time_days = 100
    simulation_time_seconds = simulation_time_days * 24 * 3600

    print(f"Simulation time: {simulation_time_days} days ({simulation_time_seconds:.2e} seconds)")

    # Create time points
    num_time_points = 100
    t_eval = np.linspace(0, simulation_time_seconds, num_time_points)
    print(f"Number of output time points: {num_time_points}")

    print_section_header("STEP 5: Run the Simulation")

    print("Solving the radial model...")
    print("(Default mode uses a fast node-wise backend.)")
    print("(Set params['radial_solver_mode'] = 'coupled' to enable the original coupled solve.)")

    # Solve the system
    result = model.solve(
        t_span=(0, simulation_time_seconds),
        t_eval=t_eval
    )

    print("Simulation completed successfully!")

    print_section_header("STEP 6: Examine Radial Results")

    # The result dictionary contains radial profiles for each variable
    print("\nResult structure:")
    print(f"  Time points: {len(result['time'])}")
    print(f"  Radial nodes: {model.n_nodes}")

    # Each variable has shape (n_time, n_nodes)
    print("\nVariable shapes (time_points × n_nodes):")
    for key in ['swelling', 'Rcb', 'Cgb', 'released_gas']:
        if key in result:
            print(f"  {key}: {result[key].shape}")

    print_section_header("STEP 7: Analyze Radial Profiles")

    # Get final radial profiles
    time_days = result['time'] / (24 * 3600)
    final_swelling = result['swelling'][-1, :]  # Shape: (n_nodes,)

    print("\nFinal swelling radial profile:")
    print(f"  {'Radius (mm)':<12} {'Swelling (%)':<15}")
    print("-" * 30)
    for i, r in enumerate(model.mesh.nodes):
        r_mm = r * 1000
        swell_pct = final_swelling[i]
        print(f"  {r_mm:6.3f}      {swell_pct:10.4f}%")

    # Calculate average swelling
    avg_swelling = np.mean(final_swelling)
    centerline_swelling = final_swelling[0]
    surface_swelling = final_swelling[-1]

    print(f"\nSwelling summary:")
    print(f"  Centerline swelling: {centerline_swelling:.4f}%")
    print(f"  Surface swelling: {surface_swelling:.4f}%")
    print(f"  Average swelling: {avg_swelling:.4f}%")

    return model, result


def visualize_radial_results(model, result):
    """
    Visualize radial profiles using the RadialProfilePlotter.
    """
    print_section_header("STEP 8: Visualize Radial Profiles")

    # Create a plotter
    plotter = RadialProfilePlotter(
        radius_unit='mm',
        length_unit='nm',
        time_unit='days'
    )

    # Load results
    plotter.load_radial_result(result, model.mesh, model.params)

    print("Creating radial profile visualization...")

    # Create the main plot with 4 subplots
    fig = plotter.plot()

    # Save the figure
    output_filename = 'radial_simulation_profile.png'
    plotter.save_and_close(fig, output_filename)
    print(f"Radial profile plot saved to: {output_filename}")

    # Plot swelling evolution over time at different radial positions
    print("\nCreating swelling evolution plot...")

    fig2, ax = plt.subplots(figsize=(10, 6))

    time_days = result['time'] / (24 * 3600)

    # Plot swelling at centerline, mid-radius, and surface
    centerline_idx = 0
    mid_idx = model.n_nodes // 2
    surface_idx = model.n_nodes - 1

    ax.plot(time_days, result['swelling'][:, centerline_idx],
            label='Centerline', linewidth=2)
    ax.plot(time_days, result['swelling'][:, mid_idx],
            label=f'Mid-radius (r={model.mesh.nodes[mid_idx]*1000:.2f} mm)', linewidth=2)
    ax.plot(time_days, result['swelling'][:, surface_idx],
            label='Surface', linewidth=2)

    ax.set_xlabel('Time (days)')
    ax.set_ylabel('Swelling (%)')
    ax.set_title('Swelling Evolution at Different Radial Positions')
    ax.legend()
    ax.grid(True, alpha=0.3)

    output_filename2 = 'radial_swelling_evolution.png'
    plt.savefig(output_filename2, dpi=300, bbox_inches='tight')
    print(f"Swelling evolution plot saved to: {output_filename2}")
    plt.close(fig2)


def run_temperature_profile_example():
    """
    Demonstrate radial simulation with a temperature gradient.
    """
    print_section_header("BONUS: Temperature Gradient Example")

    # Create parameters
    params = create_default_parameters()
    params['temperature'] = 773.15  # Base temperature 500°C

    print("\nComparing uniform vs parabolic temperature profiles...")

    results_list = []

    # Case 1: Uniform temperature
    print("\n1. Running with uniform temperature...")
    model_uniform = RadialGasSwellingModel(
        params=params,
        n_nodes=10,
        temperature_profile='uniform'  # All nodes same temperature
    )

    sim_time = 100 * 24 * 3600  # 100 days
    t_eval = np.linspace(0, sim_time, 50)

    result_uniform = model_uniform.solve(t_span=(0, sim_time), t_eval=t_eval)
    results_list.append(('uniform', model_uniform, result_uniform))

    T_uniform = model_uniform.temperature
    print(f"   Temperature range: {T_uniform[0]:.0f} - {T_uniform[-1]:.0f} K")
    print(f"   Final centerline swelling: {result_uniform['swelling'][-1, 0]:.4f}%")

    # Case 2: Parabolic temperature profile
    print("\n2. Running with parabolic temperature profile...")
    model_parabolic = RadialGasSwellingModel(
        params=params,
        n_nodes=10,
        temperature_profile='parabolic'  # Center hotter than surface
    )

    result_parabolic = model_parabolic.solve(t_span=(0, sim_time), t_eval=t_eval)
    results_list.append(('parabolic', model_parabolic, result_parabolic))

    T_para = model_parabolic.temperature
    print(f"   Temperature range: {T_para[0]:.0f} - {T_para[-1]:.0f} K")
    print(f"   Final centerline swelling: {result_parabolic['swelling'][-1, 0]:.4f}%")

    # Visualize comparison
    print("\nCreating temperature profile comparison plot...")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    radius = model_uniform.mesh.nodes * 1000  # Convert to mm

    # Plot temperature profiles
    axes[0].plot(radius, T_uniform, 'o-', label='Uniform', linewidth=2, markersize=6)
    axes[0].plot(radius, T_para, 's-', label='Parabolic', linewidth=2, markersize=6)
    axes[0].set_xlabel('Radius (mm)')
    axes[0].set_ylabel('Temperature (K)')
    axes[0].set_title('Temperature Profile Comparison')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot final swelling profiles
    axes[1].plot(radius, result_uniform['swelling'][-1, :],
                'o-', label='Uniform T', linewidth=2, markersize=6)
    axes[1].plot(radius, result_parabolic['swelling'][-1, :],
                's-', label='Parabolic T', linewidth=2, markersize=6)
    axes[1].set_xlabel('Radius (mm)')
    axes[1].set_ylabel('Swelling (%)')
    axes[1].set_title('Final Swelling Profile Comparison')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    output_filename = 'radial_temperature_comparison.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nTemperature comparison plot saved to: {output_filename}")
    plt.close(fig)


def run_user_defined_profile_example():
    """
    Demonstrate radial simulation with user-defined temperature profile.
    """
    print_section_header("BONUS: User-Defined Temperature Profile")

    # Create parameters
    params = create_default_parameters()

    # Define a custom temperature profile
    # For example, higher temperature at center, decreasing toward surface
    n_nodes = 10
    custom_temps = np.linspace(900, 650, n_nodes)  # 900K at center, 650K at surface

    print(f"\nUser-defined temperature profile:")
    print(f"  Centerline (node 0): {custom_temps[0]:.0f} K")
    print(f"  Surface (node {n_nodes-1}): {custom_temps[-1]:.0f} K")

    # Create model with user profile
    model = RadialGasSwellingModel(
        params=params,
        n_nodes=n_nodes,
        temperature_profile='user',
        temperature_data=custom_temps
    )

    print(f"\nCreated model with custom temperature profile")

    # Run simulation
    sim_time = 50 * 24 * 3600  # 50 days
    t_eval = np.linspace(0, sim_time, 50)

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

    print(f"Simulation completed")
    print(f"  Final centerline swelling: {result['swelling'][-1, 0]:.4f}%")
    print(f"  Final surface swelling: {result['swelling'][-1, -1]:.4f}%")


def main():
    """Main function to run the radial simulation tutorial"""

    parser = argparse.ArgumentParser(
        description='Radial Gas Swelling Simulation Tutorial'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Set up model without running full simulation'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  RADIAL GAS SWELLING MODEL - TUTORIAL")
    print("=" * 70)
    print("\nWelcome! This tutorial will guide you through running radial")
    print("gas swelling simulations with spatial discretization.")
    print("\nKey features of the radial model:")
    print("  - Spatial discretization across fuel pellet radius")
    print("  - Fast node-wise solve is the default execution mode")
    print("  - Original fully coupled radial ODE solve remains available")
    print("  - Temperature gradients affect swelling distribution")
    print("  - Coupled mode includes explicit radial diffusion between nodes")
    print()

    if args.dry_run:
        print("\n" + "-" * 70)
        print("DRY RUN MODE: Setting up model without full simulation")
        print("-" * 70)

        # Create mesh
        mesh = create_radial_mesh_example()

        # Create model
        params = create_default_parameters()
        model = RadialGasSwellingModel(params, n_nodes=10)

        print(f"\nModel created successfully: {model}")
        print("\nDry run complete. Model is ready for simulation.")
        return

    # Run basic radial simulation
    mesh = create_radial_mesh_example()
    model, result = run_basic_radial_simulation()

    # Visualize results
    visualize_radial_results(model, result)

    # Offer additional examples
    print("\n" + "-" * 70)
    response = input("\nWould you like to see the temperature gradient example? (y/n): ")

    if response.lower() == 'y':
        run_temperature_profile_example()

    print("\n" + "-" * 70)
    response = input("\nWould you like to see the user-defined profile example? (y/n): ")

    if response.lower() == 'y':
        run_user_defined_profile_example()

    print_section_header("Tutorial Complete!")
    print("\nCongratulations! You've explored the radial gas swelling model.")
    print("\nKey takeaways:")
    print("  - Radial mesh discretizes the fuel pellet spatially")
    print("  - Temperature profiles affect swelling distribution")
    print("  - Use RadialProfilePlotter for visualization")
    print("  - Compare uniform vs non-uniform conditions")
    print("\nNext steps:")
    print("  - Try different mesh resolutions (n_nodes parameter)")
    print("  - Experiment with flux depression (flux_depression=True)")
    print("  - Study slab geometry vs cylindrical geometry")
    print("  - Analyze radial profiles of gas pressure, bubble radius, etc.")
    print("\nFor more information, see the documentation in the docs/ directory.")
    print("\n")


if __name__ == "__main__":
    main()
