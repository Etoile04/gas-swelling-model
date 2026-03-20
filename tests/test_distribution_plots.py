"""
Unit tests for distribution_plots module

Tests all distribution plotting functions including:
- plot_bubble_size_distribution
- plot_bubble_radius_distribution
- plot_gas_distribution_histogram
"""

import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
from pathlib import Path

from gas_swelling import GasSwellingModel, create_default_parameters
from gas_swelling.visualization.distribution_plots import (
    plot_bubble_size_distribution,
    plot_bubble_radius_distribution,
    plot_gas_distribution_histogram,
    _get_time_index
)


@pytest.fixture
def mock_result():
    """Create minimal mock result data for fast testing"""
    t = np.linspace(0, 100, 50)
    return {
        'time': t,
        'Rcb': np.linspace(1e-9, 5e-9, 50),  # Bulk radius (m)
        'Rcf': np.linspace(2e-9, 8e-9, 50),  # Interface radius (m)
        'Ccb': np.linspace(1e20, 5e20, 50),  # Bulk concentration
        'Ccf': np.linspace(1e21, 8e21, 50),  # Interface concentration
        'Ncb': np.linspace(100, 500, 50),    # Gas atoms per bulk bubble
        'Ncf': np.linspace(200, 800, 50),    # Gas atoms per interface bubble
    }


@pytest.fixture(scope="module")
def sample_result():
    """Create sample simulation result data for testing (cached at module level)"""
    params = create_default_parameters()
    model = GasSwellingModel(params)

    sim_time = 3 * 24 * 3600  # 3 days in seconds (reduced for faster tests)
    t_eval = np.linspace(0, sim_time, 30)  # Fewer points for faster tests

    result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
    return result


@pytest.fixture
def sample_params():
    """Create sample parameters for testing"""
    return create_default_parameters()


class TestGetTimeIndex:
    """Test the _get_time_index helper function"""

    def test_time_index_start(self, mock_result):
        """Test getting index for 'start' time point"""
        idx = _get_time_index(mock_result, 'start')
        assert idx == 0

    def test_time_index_end(self, mock_result):
        """Test getting index for 'end' time point"""
        idx = _get_time_index(mock_result, 'end')
        assert idx == len(mock_result['time']) - 1

    def test_time_index_peak(self, mock_result):
        """Test getting index for 'peak' time point"""
        idx = _get_time_index(mock_result, 'peak')
        assert isinstance(idx, (int, np.integer))
        assert 0 <= idx < len(mock_result['time'])

    def test_time_index_integer(self, mock_result):
        """Test getting index with integer value"""
        idx = _get_time_index(mock_result, 25)
        assert idx == 25

    def test_time_index_float(self, mock_result):
        """Test getting index with float time value"""
        # Use a time value from the middle of the simulation
        target_time = mock_result['time'][25]
        idx = _get_time_index(mock_result, target_time)
        assert idx == 25

    def test_time_index_invalid_string(self, mock_result):
        """Test that invalid string raises ValueError"""
        with pytest.raises(ValueError, match="Invalid time_point string"):
            _get_time_index(mock_result, 'invalid')

    def test_time_index_out_of_range(self, mock_result):
        """Test that out of range index raises ValueError"""
        with pytest.raises(ValueError, match="out of range"):
            _get_time_index(mock_result, 999999)

    def test_time_index_invalid_type(self, mock_result):
        """Test that invalid type raises ValueError"""
        with pytest.raises(ValueError, match="Invalid time_point type"):
            _get_time_index(mock_result, [1, 2, 3])


class TestBubbleSizeDistribution:
    """Test plot_bubble_size_distribution function"""

    def test_plot_creates_figure(self, mock_result, sample_params):
        """Test that function creates a valid figure"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            plot_type='histogram',  # Use histogram only (no KDE which needs multiple points)
            bins=20,
            save_path=None
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_with_histogram_only(self, mock_result, sample_params):
        """Test plotting histogram only"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            plot_type='histogram', bins=20,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    @pytest.mark.skip(reason="KDE requires multiple data points - use real simulation data")
    def test_plot_with_kde_only(self, mock_result, sample_params):
        """Test plotting KDE only"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            plot_type='kde', bins=20,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    @pytest.mark.skip(reason="KDE requires multiple data points - use real simulation data")
    def test_plot_with_both(self, mock_result, sample_params):
        """Test plotting both histogram and KDE"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            plot_type='both', bins=20,
            save_path=None
        )
        assert fig is not None
        # Should have 2 subplots for 'both'
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_plot_different_time_points(self, mock_result, sample_params):
        """Test plotting at different time points"""
        time_points = ['start', 'end', 'peak', 0, 25]

        for tp in time_points:
            fig = plot_bubble_size_distribution(
                mock_result,
                sample_params,
                time_point=tp, bins=20,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_different_length_units(self, mock_result, sample_params):
        """Test plotting with different length units"""
        units = ['m', 'mm', 'um', 'nm']

        for unit in units:
            fig = plot_bubble_size_distribution(
                mock_result,
                sample_params,
                length_unit=unit, bins=20,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_custom_bins(self, mock_result, sample_params):
        """Test plotting with custom bins"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            bins=20,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_bandwidth(self, mock_result, sample_params):
        """Test plotting with custom bandwidth"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            bandwidth=0.5,
            plot_type='kde', bins=20,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_figsize(self, mock_result, sample_params):
        """Test plotting with custom figure size"""
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params,
            figsize=(8, 6),
            save_path=None
        )
        assert fig is not None
        size = fig.get_size_inches()
        assert abs(size[0] - 8) < 0.1
        assert abs(size[1] - 6) < 0.1
        plt.close(fig)

    def test_plot_different_styles(self, mock_result, sample_params):
        """Test plotting with different styles"""
        styles = ['default', 'presentation', 'poster']

        for style in styles:
            fig = plot_bubble_size_distribution(
                mock_result,
                sample_params,
                style=style, bins=20,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_missing_required_keys(self, sample_params):
        """Test that missing required keys raises ValueError"""
        invalid_result = {'time': np.array([0, 1, 2])}
        with pytest.raises(ValueError):
            plot_bubble_size_distribution(
                invalid_result,
                sample_params, bins=20,
                save_path=None
            )

    def test_plot_save_to_file(self, mock_result, sample_params, tmp_path):
        """Test saving plot to file"""
        save_path = tmp_path / "test_bubble_size.png"
        fig = plot_bubble_size_distribution(
            mock_result,
            sample_params, bins=20,
            save_path=str(save_path),
            dpi=150
        )
        assert save_path.exists()
        plt.close(fig)


class TestBubbleRadiusDistribution:
    """Test plot_bubble_radius_distribution function"""

    def test_plot_creates_figure(self, mock_result, sample_params):
        """Test that function creates a valid figure"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            save_path=None
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_histogram_type(self, mock_result, sample_params):
        """Test histogram plot type"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            plot_type='histogram',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_box_type(self, mock_result, sample_params):
        """Test box plot type"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            plot_type='box',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_timeline_type(self, mock_result, sample_params):
        """Test timeline plot type"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            plot_type='timeline',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_bulk_region(self, mock_result, sample_params):
        """Test plotting bulk region only"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            region='bulk',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_interface_region(self, mock_result, sample_params):
        """Test plotting interface region only"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            region='interface',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_both_regions(self, mock_result, sample_params):
        """Test plotting both regions"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            region='both',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_invalid_region(self, mock_result, sample_params):
        """Test that invalid region raises ValueError"""
        with pytest.raises(ValueError, match="Invalid region"):
            plot_bubble_radius_distribution(
                mock_result,
                sample_params,
                region='invalid',
                save_path=None
            )

    def test_plot_multiple_time_points(self, mock_result, sample_params):
        """Test plotting at multiple time points"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            time_points=[0, 50, 99],
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_time_point_strings(self, mock_result, sample_params):
        """Test plotting with time point strings"""
        for tp in ['start', 'end', 'peak']:
            fig = plot_bubble_radius_distribution(
                mock_result,
                sample_params,
                time_points=tp,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_different_length_units(self, mock_result, sample_params):
        """Test plotting with different length units"""
        units = ['m', 'mm', 'um', 'nm']

        for unit in units:
            fig = plot_bubble_radius_distribution(
                mock_result,
                sample_params,
                length_unit=unit,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_custom_bins(self, mock_result, sample_params):
        """Test plotting with custom bins"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            bins=30,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_figsize(self, mock_result, sample_params):
        """Test plotting with custom figure size"""
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            figsize=(12, 8),
            save_path=None
        )
        assert fig is not None
        size = fig.get_size_inches()
        assert abs(size[0] - 12) < 0.1
        assert abs(size[1] - 8) < 0.1
        plt.close(fig)

    def test_plot_different_styles(self, mock_result, sample_params):
        """Test plotting with different styles"""
        styles = ['default', 'presentation', 'poster']

        for style in styles:
            fig = plot_bubble_radius_distribution(
                mock_result,
                sample_params,
                style=style,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_invalid_plot_type(self, mock_result, sample_params):
        """Test that invalid plot type raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported plot_type"):
            plot_bubble_radius_distribution(
                mock_result,
                sample_params,
                plot_type='invalid',
                save_path=None
            )

    def test_plot_save_to_file(self, mock_result, sample_params, tmp_path):
        """Test saving plot to file"""
        save_path = tmp_path / "test_radius_dist.png"
        fig = plot_bubble_radius_distribution(
            mock_result,
            sample_params,
            save_path=str(save_path),
            dpi=150
        )
        assert save_path.exists()
        plt.close(fig)


class TestGasDistributionHistogram:
    """Test plot_gas_distribution_histogram function"""

    def test_plot_creates_figure(self, mock_result, sample_params):
        """Test that function creates a valid figure"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            save_path=None
        )
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_histogram_type(self, mock_result, sample_params):
        """Test histogram plot type"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            plot_type='histogram',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_comparison_type(self, mock_result, sample_params):
        """Test comparison plot type"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            plot_type='comparison',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_evolution_type(self, mock_result, sample_params):
        """Test evolution plot type"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            plot_type='evolution',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_bulk_region(self, mock_result, sample_params):
        """Test plotting bulk region only"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            region='bulk',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_interface_region(self, mock_result, sample_params):
        """Test plotting interface region only"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            region='interface',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_both_regions(self, mock_result, sample_params):
        """Test plotting both regions"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            region='both',
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_different_time_points(self, mock_result, sample_params):
        """Test plotting at different time points"""
        time_points = ['start', 'end', 'peak', 0, 25]

        for tp in time_points:
            fig = plot_gas_distribution_histogram(
                mock_result,
                sample_params,
                time_point=tp,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_custom_bins(self, mock_result, sample_params):
        """Test plotting with custom bins"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            bins=25,
            save_path=None
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_custom_figsize(self, mock_result, sample_params):
        """Test plotting with custom figure size"""
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            figsize=(10, 7),
            save_path=None
        )
        assert fig is not None
        size = fig.get_size_inches()
        assert abs(size[0] - 10) < 0.1
        assert abs(size[1] - 7) < 0.1
        plt.close(fig)

    def test_plot_different_styles(self, mock_result, sample_params):
        """Test plotting with different styles"""
        styles = ['default', 'presentation', 'poster']

        for style in styles:
            fig = plot_gas_distribution_histogram(
                mock_result,
                sample_params,
                style=style,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_invalid_plot_type(self, mock_result, sample_params):
        """Test that invalid plot type raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported plot_type"):
            plot_gas_distribution_histogram(
                mock_result,
                sample_params,
                plot_type='invalid',
                save_path=None
            )

    def test_plot_evolution_with_different_regions(self, mock_result, sample_params):
        """Test evolution plot type with different regions"""
        for region in ['bulk', 'interface', 'both']:
            fig = plot_gas_distribution_histogram(
                mock_result,
                sample_params,
                plot_type='evolution',
                region=region,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_comparison_with_different_regions(self, mock_result, sample_params):
        """Test comparison plot type with different regions"""
        for region in ['bulk', 'interface', 'both']:
            fig = plot_gas_distribution_histogram(
                mock_result,
                sample_params,
                plot_type='comparison',
                region=region,
                save_path=None
            )
            assert fig is not None
            plt.close(fig)

    def test_plot_save_to_file(self, mock_result, sample_params, tmp_path):
        """Test saving plot to file"""
        save_path = tmp_path / "test_gas_dist.png"
        fig = plot_gas_distribution_histogram(
            mock_result,
            sample_params,
            save_path=str(save_path),
            dpi=150
        )
        assert save_path.exists()
        plt.close(fig)


class TestIntegration:
    """Integration tests for distribution plots"""

    def test_all_functions_with_same_data(self, mock_result, sample_params):
        """Test that all plotting functions work with the same data"""
        functions = [
            lambda: plot_bubble_size_distribution(mock_result, sample_params, bins=20, save_path=None),
            lambda: plot_bubble_radius_distribution(mock_result, sample_params, save_path=None),
            lambda: plot_gas_distribution_histogram(mock_result, sample_params, save_path=None)
        ]

        for func in functions:
            fig = func()
            assert fig is not None
            plt.close(fig)

    def test_different_time_points_consistency(self, mock_result, sample_params):
        """Test that plots at different time points all work"""
        time_points = ['start', 'end', 'peak']

        for tp in time_points:
            fig1 = plot_bubble_size_distribution(
                mock_result, sample_params, time_point=tp, bins=20, save_path=None
            )
            fig2 = plot_bubble_radius_distribution(
                mock_result, sample_params, time_points=tp, save_path=None
            )
            fig3 = plot_gas_distribution_histogram(
                mock_result, sample_params, time_point=tp, save_path=None
            )

            assert fig1 is not None
            assert fig2 is not None
            assert fig3 is not None

            plt.close(fig1)
            plt.close(fig2)
            plt.close(fig3)

    def test_all_units_consistency(self, mock_result, sample_params):
        """Test that all length units work across functions"""
        units = ['m', 'mm', 'um', 'nm']

        for unit in units:
            fig1 = plot_bubble_size_distribution(
                mock_result, sample_params, length_unit=unit, bins=20, save_path=None
            )
            fig2 = plot_bubble_radius_distribution(
                mock_result, sample_params, length_unit=unit, save_path=None
            )

            assert fig1 is not None
            assert fig2 is not None

            plt.close(fig1)
            plt.close(fig2)
