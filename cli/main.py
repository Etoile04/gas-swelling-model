"""
Main CLI Entry Point

This module provides the main command-line interface using the click library.
It implements commands for running simulations, managing configurations, and
handling output.

The main command is 'run' which executes a gas swelling simulation using
a configuration file.
"""

import click
import sys
import os
import numpy as np

# Add parent directory to path to import model and parameters
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.config import load_config, validate_params
from cli.progress import create_progress_tracker
from cli.output import export_csv, export_json, export_hdf5, export_matlab

__version__ = "0.1.0"


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Gas Swelling Simulation CLI

    A command-line interface for running gas swelling simulations
    without editing Python code.

    \b
    Examples:
        gas-swelling run config.yaml
        gas-swelling run config.yaml --output-dir results/ --format json
    """
    pass


@cli.command()
@click.argument('config', type=click.Path())
@click.option(
    '--output-dir',
    type=click.Path(),
    default='output',
    help='Output directory for results (default: output)'
)
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['csv', 'json', 'hdf5', 'matlab'], case_sensitive=False),
    default='csv',
    help='Output format (default: csv)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def run(config, output_dir, output_format, verbose):
    """
    Run a gas swelling simulation using a YAML configuration file.

    CONFIG: Path to the YAML configuration file

    \b
    Example:
        gas-swelling run config.yaml --output-dir results/ --format json
    """
    try:
        # Validate that config file exists before loading
        if not os.path.exists(config):
            click.echo(f"Error: Configuration file not found: {config}", err=True)
            sys.exit(1)

        # Load configuration from YAML file
        if verbose:
            click.echo(f"Loading configuration from: {config}")
        params = load_config(config)

        # Validate parameters
        if verbose:
            click.echo("Validating parameters...")
        validate_params(params)

        # Import model here to avoid early import failures
        try:
            from modelrk23 import GasSwellingModel
        except ImportError as e:
            click.echo(f"Error: Cannot import GasSwellingModel: {e}", err=True)
            click.echo("Make sure you're running from the project root directory.", err=True)
            sys.exit(1)

        # Create model instance
        if verbose:
            click.echo(f"Creating model with temperature: {params.get('temperature', 'N/A')} K")
            click.echo(f"  Fission rate: {params.get('fission_rate', 'N/A')} fissions/m³/s")
            click.echo(f"  Max time: {params.get('max_time', 'N/A')} s")

        model = GasSwellingModel(params)

        # Determine simulation time
        sim_time = params.get('max_time', 8.64e6)  # Default: 100 days

        # Set up time evaluation points
        t_eval = np.linspace(0, sim_time, 100)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Run simulation
        if verbose:
            click.echo("Starting simulation...")
        else:
            click.echo("Running simulation...")

        # Create progress tracker
        progress_tracker = create_progress_tracker(
            total_steps=100,  # Approximate number of evaluation points
            verbose=verbose,
            desc="Simulating"
        )

        # Get callback for progress tracking
        callback = progress_tracker.get_callback()

        try:
            # Run simulation with progress callback
            result = model.solve(
                t_span=(0, sim_time),
                t_eval=t_eval,
                callback=callback
            )
        finally:
            # Always close progress tracker
            progress_tracker.close()

        # Calculate and display results
        Rcb = result['Rcb']
        Rcf = result['Rcf']
        Ccb = result['Ccb']
        Ccf = result['Ccf']

        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        total_V_bubble = V_bubble_b + V_bubble_f
        swelling = total_V_bubble * 100  # Percentage

        # Display summary
        click.echo(f"\nSimulation completed successfully!")
        click.echo(f"Final time: {result['time'][-1]:.2e} s")
        click.echo(f"Final bulk bubble radius: {Rcb[-1]*1e9:.4f} nm")
        click.echo(f"Final boundary bubble radius: {Rcf[-1]*1e9:.4f} nm")
        click.echo(f"Final swelling: {swelling[-1]:.6f}%")

        # Save results to output file
        config_name = os.path.splitext(os.path.basename(config))[0]
        output_filename = f"{config_name}_results.{output_format}"
        output_path = os.path.join(output_dir, output_filename)

        # Prepare results data
        results_data = {
            'time': result['time'],
            'Cgb': result['Cgb'],
            'Ccb': result['Ccb'],
            'Ncb': result['Ncb'],
            'cvb': result['cvb'],
            'cib': result['cib'],
            'Cgf': result['Cgf'],
            'Ccf': result['Ccf'],
            'Ncf': result['Ncf'],
            'cvf': result['cvf'],
            'cif': result['cif'],
            'Rcb': Rcb,
            'Rcf': Rcf,
            'swelling': swelling
        }

        # Add metadata
        metadata = {
            'config_file': config,
            'temperature': params.get('temperature', 'N/A'),
            'fission_rate': params.get('fission_rate', 'N/A'),
            'max_time': params.get('max_time', 'N/A'),
            'eos_model': params.get('eos_model', 'N/A')
        }

        # Export based on format
        try:
            if output_format == 'csv':
                export_csv(results_data, output_path)
            elif output_format == 'json':
                export_json(results_data, output_path, metadata)
            elif output_format == 'hdf5':
                export_hdf5(results_data, output_path, metadata)
            elif output_format == 'matlab':
                export_matlab(results_data, output_path, metadata)

            click.echo(f"\nResults saved to: {output_path}")
            if verbose:
                click.echo(f"  Format: {output_format}")
                click.echo(f"  Data points: {len(result['time'])}")

        except Exception as e:
            click.echo(f"Error saving results: {e}", err=True)
            sys.exit(1)

        sys.exit(0)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except (ValueError, TypeError) as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Simulation error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()
