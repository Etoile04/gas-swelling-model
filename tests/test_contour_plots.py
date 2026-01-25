"""
Unit tests for contour_plots module

Tests all contour plotting functions including:
- plot_temperature_contour
- plot_2d_parameter_sweep
- plot_swelling_heatmap
"""

import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
from pathlib import Path
import warnings

from gas_swelling.visualization.contour_plots import (
    plot_temperature_contour,
    plot_2d_parameter_sweep,
    plot_swelling_heatmap
)


@pytest.fixture
def sample_contour_data():
    """Create sample contour data for testing"""
    np.random.seed(42)  # For reproducibility
    temperatures = np.linspace(600, 900, 20)
    burnups = np.linspace(0, 5, 20)

    # Create realistic swelling data with temperature dependence
    T, B = np.meshgrid(temperatures, burnups, indexing='ij')
    # Simulate swelling: peaks around 750K, increases with burnup
    swelling = 3.0 * np.exp(-((T - 750)**2) / (2 * 50**2)) * (1 + B * 0.2)

    return temperatures, burnups, swelling


@pytest.fixture
def sample_2d_param_data():
    """Create sample 2D parameter sweep data"""
    np.random.seed(42)
    param1 = np.logspace(12, 15, 15)  # Dislocation density (wider range for log scale test)
    param2 = np.linspace(600, 800, 15)  # Temperature

    # Create output data
    P1, P2 = np.meshgrid(param1, param2, indexing='ij')
    output = 2.5 * (P2 / 800) * np.log10(P1 / 1e12)

    return param1, param2, output


@pytest.fixture
def sample_heatmap_data():
    """Create sample heatmap data"""
    np.random.seed(42)
    temperatures = np.linspace(600, 900, 25)
    times = np.linspace(0, 100, 25)

    T, Time = np.meshgrid(temperatures, times, indexing='ij')
    # Simulate swelling evolution
    swelling = 2.0 * (Time / 100) * np.exp(-((T - 750)**2) / (2 * 60**2))

    return temperatures, times, swelling


class TestPlotTemperatureContour:
    """Test plot_temperature_contour function"""

    def test_plot_creates_figure(self, sample_contour_data):
        """Test that function creates a valid figure"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            save_path=None
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_with_custom_labels(self, sample_contour_data):
        """Test plotting with custom labels"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            xlabel='Time (days)',
            ylabel='Temperature (K)',
            title='Custom Title',
            colorbar_label='Swelling %',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_different_colormaps(self, sample_contour_data):
        """Test plotting with different colormaps"""
        temperatures, burnups, swelling = sample_contour_data
        cmaps = ['viridis', 'plasma', 'coolwarm', 'RdYlBu_r', 'YlOrRd']

        for cmap in cmaps:
            fig = plot_temperature_contour(
                temperatures, burnups, swelling,
                cmap=cmap,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_with_contour_lines(self, sample_contour_data):
        """Test plotting with contour lines enabled"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            show_contour_lines=True,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_without_contour_lines(self, sample_contour_data):
        """Test plotting without contour lines"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            show_contour_lines=False,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_contour_levels(self, sample_contour_data):
        """Test plotting with custom contour levels"""
        temperatures, burnups, swelling = sample_contour_data
        levels = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            contour_levels=levels,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_figsize(self, sample_contour_data):
        """Test plotting with custom figure size"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            figsize=(12, 10),
            save_path=None
        )
        assert fig is not None
        size = fig.get_size_inches()
        assert abs(size[0] - 12) < 0.1
        assert abs(size[1] - 10) < 0.1
        plt.close(fig)

    def test_plot_different_styles(self, sample_contour_data):
        """Test plotting with different styles"""
        temperatures, burnups, swelling = sample_contour_data
        styles = ['default', 'presentation', 'poster', 'grayscale']

        for style in styles:
            fig = plot_temperature_contour(
                temperatures, burnups, swelling,
                style=style,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_custom_dpi(self, sample_contour_data):
        """Test plotting with custom DPI"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            dpi=150,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_with_axis_limits(self, sample_contour_data):
        """Test plotting with custom axis limits"""
        temperatures, burnups, swelling = sample_contour_data
        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            xlim=(0, 6),
            ylim=(550, 950),
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_invalid_1d_temperature(self, sample_contour_data):
        """Test that 2D temperature array raises ValueError"""
        _, burnups, swelling = sample_contour_data
        temperatures_2d = np.random.rand(10, 10)

        with pytest.raises(ValueError, match="must be 1D arrays"):
            plot_temperature_contour(
                temperatures_2d, burnups, swelling,
                save_path=None
            )

    def test_plot_invalid_1d_x_param(self, sample_contour_data):
        """Test that 2D x_param array raises ValueError"""
        temperatures, _, swelling = sample_contour_data
        x_param_2d = np.random.rand(10, 10)

        with pytest.raises(ValueError, match="must be 1D arrays"):
            plot_temperature_contour(
                temperatures, x_param_2d, swelling,
                save_path=None
            )

    def test_plot_invalid_2d_swelling_data(self, sample_contour_data):
        """Test that 1D swelling data raises ValueError"""
        temperatures, burnups, _ = sample_contour_data
        swelling_1d = np.random.rand(20)

        with pytest.raises(ValueError, match="must be a 2D array"):
            plot_temperature_contour(
                temperatures, burnups, swelling_1d,
                save_path=None
            )

    def test_plot_incompatible_shapes(self, sample_contour_data):
        """Test that incompatible shapes raise ValueError"""
        temperatures, burnups, _ = sample_contour_data
        swelling_wrong = np.random.rand(15, 15)  # Wrong shape

        with pytest.raises(ValueError, match="incompatible"):
            plot_temperature_contour(
                temperatures, burnups, swelling_wrong,
                save_path=None
            )

    def test_plot_save_to_file(self, sample_contour_data, tmp_path):
        """Test saving plot to file"""
        temperatures, burnups, swelling = sample_contour_data
        save_path = tmp_path / "test_contour.png"

        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            save_path=str(save_path),
            dpi=150
        )
        assert save_path.exists()
        plt.close(fig)

    def test_plot_figsize_verification(self, sample_contour_data):
        """Test that figure size is correctly applied"""
        temperatures, burnups, swelling = sample_contour_data
        custom_size = (10, 8)

        fig = plot_temperature_contour(
            temperatures, burnups, swelling,
            figsize=custom_size,
            save_path=None
        )

        actual_size = fig.get_size_inches()
        assert abs(actual_size[0] - custom_size[0]) < 0.1
        assert abs(actual_size[1] - custom_size[1]) < 0.1
        plt.close(fig)


class TestPlot2DParameterSweep:
    """Test plot_2d_parameter_sweep function"""

    def test_plot_creates_figure(self, sample_2d_param_data):
        """Test that function creates a valid figure"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            save_path=None
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_with_custom_names(self, sample_2d_param_data):
        """Test plotting with custom parameter names"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            param1_name='Dislocation Density',
            param2_name='Temperature',
            output_name='Swelling',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_with_units(self, sample_2d_param_data):
        """Test plotting with custom units"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            param1_unit='m^-2',
            param2_unit='K',
            output_unit='%',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_different_colormaps(self, sample_2d_param_data):
        """Test plotting with different colormaps"""
        param1, param2, output = sample_2d_param_data
        cmaps = ['viridis', 'plasma', 'coolwarm', 'inferno']

        for cmap in cmaps:
            fig = plot_2d_parameter_sweep(
                param1, param2, output,
                cmap=cmap,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_with_contour_lines(self, sample_2d_param_data):
        """Test plotting with contour lines enabled"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            show_contour_lines=True,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_without_contour_lines(self, sample_2d_param_data):
        """Test plotting without contour lines"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            show_contour_lines=False,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_contour_levels(self, sample_2d_param_data):
        """Test plotting with custom contour levels"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            contour_levels=10,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_figsize(self, sample_2d_param_data):
        """Test plotting with custom figure size"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            figsize=(11, 9),
            save_path=None
        )
        assert fig is not None
        size = fig.get_size_inches()
        assert abs(size[0] - 11) < 0.1
        assert abs(size[1] - 9) < 0.1
        plt.close(fig)

    def test_plot_different_styles(self, sample_2d_param_data):
        """Test plotting with different styles"""
        param1, param2, output = sample_2d_param_data
        styles = ['default', 'presentation', 'poster', 'grayscale']

        for style in styles:
            fig = plot_2d_parameter_sweep(
                param1, param2, output,
                style=style,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_log_scale_detection(self, sample_2d_param_data):
        """Test that log scale is applied for wide parameter ranges"""
        param1, param2, output = sample_2d_param_data
        # param1 spans >2 orders of magnitude (1e13 to 1e15)
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            save_path=None
        )

        # Check if x-axis is log scale
        ax = fig.axes[0]
        assert ax.get_xscale() == 'log'
        plt.close(fig)

    def test_plot_linear_scale_small_range(self):
        """Test that linear scale is used for small parameter ranges"""
        param1 = np.linspace(1, 10, 15)  # Small range
        param2 = np.linspace(600, 800, 15)
        P1, P2 = np.meshgrid(param1, param2, indexing='ij')
        output = P2 / 800

        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            save_path=None
        )

        # Check if x-axis is linear scale
        ax = fig.axes[0]
        assert ax.get_xscale() == 'linear'
        plt.close(fig)

    def test_plot_with_axis_limits(self, sample_2d_param_data):
        """Test plotting with custom axis limits"""
        param1, param2, output = sample_2d_param_data
        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            xlim=(1e13, 1e16),
            ylim=(550, 850),
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_invalid_1d_param1(self, sample_2d_param_data):
        """Test that 2D param1 array raises ValueError"""
        _, param2, output = sample_2d_param_data
        param1_2d = np.random.rand(10, 10)

        with pytest.raises(ValueError, match="must be 1D arrays"):
            plot_2d_parameter_sweep(
                param1_2d, param2, output,
                save_path=None
            )

    def test_plot_invalid_1d_param2(self, sample_2d_param_data):
        """Test that 2D param2 array raises ValueError"""
        param1, _, output = sample_2d_param_data
        param2_2d = np.random.rand(10, 10)

        with pytest.raises(ValueError, match="must be 1D arrays"):
            plot_2d_parameter_sweep(
                param1, param2_2d, output,
                save_path=None
            )

    def test_plot_invalid_2d_output(self, sample_2d_param_data):
        """Test that 1D output array raises ValueError"""
        param1, param2, _ = sample_2d_param_data
        output_1d = np.random.rand(15)

        with pytest.raises(ValueError, match="must be a 2D array"):
            plot_2d_parameter_sweep(
                param1, param2, output_1d,
                save_path=None
            )

    def test_plot_incompatible_shapes(self, sample_2d_param_data):
        """Test that incompatible shapes raise ValueError"""
        param1, param2, _ = sample_2d_param_data
        output_wrong = np.random.rand(10, 10)  # Wrong shape

        with pytest.raises(ValueError, match="incompatible"):
            plot_2d_parameter_sweep(
                param1, param2, output_wrong,
                save_path=None
            )

    def test_plot_save_to_file(self, sample_2d_param_data, tmp_path):
        """Test saving plot to file"""
        param1, param2, output = sample_2d_param_data
        save_path = tmp_path / "test_2d_sweep.png"

        fig = plot_2d_parameter_sweep(
            param1, param2, output,
            save_path=str(save_path),
            dpi=150
        )
        assert save_path.exists()
        plt.close(fig)


class TestPlotSwellingHeatmap:
    """Test plot_swelling_heatmap function"""

    def test_plot_creates_figure(self, sample_heatmap_data):
        """Test that function creates a valid figure"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            save_path=None
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_with_custom_param_name(self, sample_heatmap_data):
        """Test plotting with custom parameter name"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            param_name='Time',
            param_unit='days',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_different_colormaps(self, sample_heatmap_data):
        """Test plotting with different colormaps"""
        temperatures, times, swelling = sample_heatmap_data
        cmaps = ['YlOrRd', 'viridis', 'plasma', 'coolwarm', 'inferno']

        for cmap in cmaps:
            fig = plot_swelling_heatmap(
                temperatures, times, swelling,
                cmap=cmap,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_with_colorbar(self, sample_heatmap_data):
        """Test plotting with colorbar enabled"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            show_colorbar=True,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_without_colorbar(self, sample_heatmap_data):
        """Test plotting without colorbar"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            show_colorbar=False,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_vertical_colorbar(self, sample_heatmap_data):
        """Test plotting with vertical colorbar"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            show_colorbar=True,
            colorbar_orientation='vertical',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_horizontal_colorbar(self, sample_heatmap_data):
        """Test plotting with horizontal colorbar"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            show_colorbar=True,
            colorbar_orientation='horizontal',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_with_contour_lines(self, sample_heatmap_data):
        """Test plotting with contour lines enabled"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            show_contour_lines=True,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_without_contour_lines(self, sample_heatmap_data):
        """Test plotting without contour lines"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            show_contour_lines=False,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_contour_levels(self, sample_heatmap_data):
        """Test plotting with custom contour levels"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            contour_levels=12,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_figsize(self, sample_heatmap_data):
        """Test plotting with custom figure size"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            figsize=(14, 10),
            save_path=None
        )
        assert fig is not None
        size = fig.get_size_inches()
        assert abs(size[0] - 14) < 0.1
        assert abs(size[1] - 10) < 0.1
        plt.close(fig)

    def test_plot_different_styles(self, sample_heatmap_data):
        """Test plotting with different styles"""
        temperatures, times, swelling = sample_heatmap_data
        styles = ['default', 'presentation', 'poster', 'grayscale']

        for style in styles:
            fig = plot_swelling_heatmap(
                temperatures, times, swelling,
                style=style,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_annotate_values_small_grid(self):
        """Test annotating values on small grid"""
        temperatures = np.linspace(600, 800, 5)  # Small grid
        times = np.linspace(0, 10, 5)
        T, Time = np.meshgrid(temperatures, times, indexing='ij')
        swelling = T / 800

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fig = plot_swelling_heatmap(
                temperatures, times, swelling,
                annotate_values=True,
                save_path=None
            )
            # Should not warn for small grid
            assert len(w) == 0 or "too large" not in str(w[0].message).lower()

        assert fig is not None
        plt.close(fig)

    def test_plot_annotate_values_large_grid(self):
        """Test that large grid annotation produces warning"""
        temperatures = np.linspace(600, 800, 20)  # Large grid
        times = np.linspace(0, 10, 20)
        T, Time = np.meshgrid(temperatures, times, indexing='ij')
        swelling = T / 800

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fig = plot_swelling_heatmap(
                temperatures, times, swelling,
                annotate_values=True,
                save_path=None
            )
            # Should warn about large grid
            assert len(w) > 0
            assert "too large" in str(w[0].message).lower()

        assert fig is not None
        plt.close(fig)

    def test_plot_custom_annotation_format(self):
        """Test plotting with custom annotation format"""
        temperatures = np.linspace(600, 800, 5)
        times = np.linspace(0, 10, 5)
        T, Time = np.meshgrid(temperatures, times, indexing='ij')
        swelling = T / 800

        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            annotate_values=True,
            annotation_format='%.1f',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_with_axis_limits(self, sample_heatmap_data):
        """Test plotting with custom axis limits"""
        temperatures, times, swelling = sample_heatmap_data
        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            xlim=(0, 110),
            ylim=(550, 950),
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_invalid_1d_temperatures(self, sample_heatmap_data):
        """Test that 2D temperatures array raises ValueError"""
        _, times, swelling = sample_heatmap_data
        temperatures_2d = np.random.rand(10, 10)

        with pytest.raises(ValueError, match="must be 1D arrays"):
            plot_swelling_heatmap(
                temperatures_2d, times, swelling,
                save_path=None
            )

    def test_plot_invalid_1d_param_values(self, sample_heatmap_data):
        """Test that 2D param_values array raises ValueError"""
        temperatures, _, swelling = sample_heatmap_data
        times_2d = np.random.rand(10, 10)

        with pytest.raises(ValueError, match="must be 1D arrays"):
            plot_swelling_heatmap(
                temperatures, times_2d, swelling,
                save_path=None
            )

    def test_plot_invalid_2d_swelling(self, sample_heatmap_data):
        """Test that 1D swelling array raises ValueError"""
        temperatures, times, _ = sample_heatmap_data
        swelling_1d = np.random.rand(25)

        with pytest.raises(ValueError, match="must be a 2D array"):
            plot_swelling_heatmap(
                temperatures, times, swelling_1d,
                save_path=None
            )

    def test_plot_incompatible_shapes(self, sample_heatmap_data):
        """Test that incompatible shapes raise ValueError"""
        temperatures, times, _ = sample_heatmap_data
        swelling_wrong = np.random.rand(20, 20)  # Wrong shape

        with pytest.raises(ValueError, match="incompatible"):
            plot_swelling_heatmap(
                temperatures, times, swelling_wrong,
                save_path=None
            )

    def test_plot_save_to_file(self, sample_heatmap_data, tmp_path):
        """Test saving plot to file"""
        temperatures, times, swelling = sample_heatmap_data
        save_path = tmp_path / "test_heatmap.png"

        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            save_path=str(save_path),
            dpi=150
        )
        assert save_path.exists()
        plt.close(fig)

    def test_plot_figsize_verification(self, sample_heatmap_data):
        """Test that figure size is correctly applied"""
        temperatures, times, swelling = sample_heatmap_data
        custom_size = (12, 8)

        fig = plot_swelling_heatmap(
            temperatures, times, swelling,
            figsize=custom_size,
            save_path=None
        )

        actual_size = fig.get_size_inches()
        assert abs(actual_size[0] - custom_size[0]) < 0.1
        assert abs(actual_size[1] - custom_size[1]) < 0.1
        plt.close(fig)


class TestIntegration:
    """Integration tests for contour plots"""

    def test_all_functions_with_same_data(self, sample_contour_data):
        """Test that all plotting functions work with similar data"""
        temperatures, burnups, swelling = sample_contour_data

        fig1 = plot_temperature_contour(
            temperatures, burnups, swelling,
            save_path=None
        )
        fig2 = plot_2d_parameter_sweep(
            temperatures, burnups, swelling,
            save_path=None
        )
        fig3 = plot_swelling_heatmap(
            temperatures, burnups, swelling,
            save_path=None
        )

        assert fig1 is not None
        assert fig2 is not None
        assert fig3 is not None

        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)

    def test_different_colormaps_consistency(self, sample_contour_data):
        """Test that all colormaps work across all functions"""
        temperatures, burnups, swelling = sample_contour_data
        cmaps = ['viridis', 'plasma', 'coolwarm']

        for cmap in cmaps:
            fig1 = plot_temperature_contour(
                temperatures, burnups, swelling,
                cmap=cmap,
                save_path=None
            )
            fig2 = plot_2d_parameter_sweep(
                temperatures, burnups, swelling,
                cmap=cmap,
                save_path=None
            )
            fig3 = plot_swelling_heatmap(
                temperatures, burnups, swelling,
                cmap=cmap,
                save_path=None
            )

            assert fig1 is not None
            assert fig2 is not None
            assert fig3 is not None

            plt.close(fig1)
            plt.close(fig2)
            plt.close(fig3)

    def test_all_styles_consistency(self, sample_contour_data):
        """Test that all styles work across all functions"""
        temperatures, burnups, swelling = sample_contour_data
        styles = ['default', 'presentation', 'poster']

        for style in styles:
            fig1 = plot_temperature_contour(
                temperatures, burnups, swelling,
                style=style,
                save_path=None
            )
            fig2 = plot_2d_parameter_sweep(
                temperatures, burnups, swelling,
                style=style,
                save_path=None
            )
            fig3 = plot_swelling_heatmap(
                temperatures, burnups, swelling,
                style=style,
                save_path=None
            )

            assert fig1 is not None
            assert fig2 is not None
            assert fig3 is not None

            plt.close(fig1)
            plt.close(fig2)
            plt.close(fig3)

    def test_contour_lines_toggle_consistency(self, sample_contour_data):
        """Test that contour lines toggle works across functions"""
        temperatures, burnups, swelling = sample_contour_data

        for show_lines in [True, False]:
            fig1 = plot_temperature_contour(
                temperatures, burnups, swelling,
                show_contour_lines=show_lines,
                save_path=None
            )
            fig2 = plot_2d_parameter_sweep(
                temperatures, burnups, swelling,
                show_contour_lines=show_lines,
                save_path=None
            )
            fig3 = plot_swelling_heatmap(
                temperatures, burnups, swelling,
                show_contour_lines=show_lines,
                save_path=None
            )

            assert fig1 is not None
            assert fig2 is not None
            assert fig3 is not None

            plt.close(fig1)
            plt.close(fig2)
            plt.close(fig3)

    def test_custom_figsize_consistency(self, sample_contour_data):
        """Test that custom figsize works across all functions"""
        temperatures, burnups, swelling = sample_contour_data
        custom_sizes = [(10, 8), (12, 10), (14, 12)]

        for size in custom_sizes:
            fig1 = plot_temperature_contour(
                temperatures, burnups, swelling,
                figsize=size,
                save_path=None
            )
            fig2 = plot_2d_parameter_sweep(
                temperatures, burnups, swelling,
                figsize=size,
                save_path=None
            )
            fig3 = plot_swelling_heatmap(
                temperatures, burnups, swelling,
                figsize=size,
                save_path=None
            )

            assert fig1 is not None
            assert fig2 is not None
            assert fig3 is not None

            # Verify sizes
            assert abs(fig1.get_size_inches()[0] - size[0]) < 0.1
            assert abs(fig2.get_size_inches()[0] - size[0]) < 0.1
            assert abs(fig3.get_size_inches()[0] - size[0]) < 0.1

            plt.close(fig1)
            plt.close(fig2)
            plt.close(fig3)

    def test_edge_case_minimum_data(self):
        """Test with minimum acceptable data size"""
        temperatures = np.array([600, 700, 800])
        burnups = np.array([0, 1, 2])
        swelling = np.array([
            [0.5, 1.0, 1.5],
            [1.0, 2.0, 3.0],
            [0.8, 1.5, 2.5]
        ])

        fig1 = plot_temperature_contour(
            temperatures, burnups, swelling,
            save_path=None
        )
        fig2 = plot_2d_parameter_sweep(
            temperatures, burnups, swelling,
            save_path=None
        )
        fig3 = plot_swelling_heatmap(
            temperatures, burnups, swelling,
            save_path=None
        )

        assert fig1 is not None
        assert fig2 is not None
        assert fig3 is not None

        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
