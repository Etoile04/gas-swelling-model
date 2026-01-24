"""Test script to verify temperature sweep visualization works correctly."""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from gas_swelling.visualization.parameter_sweeps import plot_temperature_sweep

def test_basic_temperature_sweep():
    """Test basic temperature sweep plot."""
    # Create sample data
    temperatures = np.array([600, 650, 700, 750, 800, 850, 900])
    swellings = np.array([0.5, 1.2, 2.1, 1.8, 1.0, 0.6, 0.3])

    # Create plot
    fig = plot_temperature_sweep(
        temperatures,
        swellings,
        save_path='test_temperature_sweep.png',
        title='Swelling vs Temperature - Test'
    )

    print("✓ Basic temperature sweep plot created successfully")
    plt.close(fig)

def test_custom_styling():
    """Test temperature sweep with custom styling."""
    temperatures = np.array([600, 650, 700, 750, 800])
    swellings = np.array([0.5, 1.2, 2.1, 1.8, 1.0])

    fig = plot_temperature_sweep(
        temperatures,
        swellings,
        color='red',
        marker='s',
        linewidth=3,
        xlabel='Temperature (K)',
        ylabel='Swelling (%)',
        title='Custom Styled Temperature Sweep'
    )

    print("✓ Custom styled temperature sweep plot created successfully")
    plt.close(fig)

def test_error_handling():
    """Test error handling for mismatched array lengths."""
    try:
        temperatures = np.array([600, 650, 700])
        swellings = np.array([0.5, 1.2])  # Different length
        fig = plot_temperature_sweep(temperatures, swellings)
        print("✗ Should have raised ValueError for mismatched lengths")
    except ValueError as e:
        print(f"✓ Error handling works: {e}")

if __name__ == '__main__':
    print("Testing temperature sweep visualization...")
    test_basic_temperature_sweep()
    test_custom_styling()
    test_error_handling()
    print("\nAll tests passed! ✓")
