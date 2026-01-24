"""
Command-line interface for gas swelling model sensitivity analysis.

This module provides a CLI for running sensitivity analysis, parameter studies,
and uncertainty quantification on the gas swelling model.
"""

import argparse
import json
import sys
from typing import Optional, List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters
    ----------
    args : list, optional
        Command-line arguments to parse. If None, uses sys.argv[1:].

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog='gas-swelling-model',
        description='Command-line interface for gas swelling model sensitivity analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run one-at-a-time sensitivity analysis
  python -m gas_swelling.analysis.cli oat --parameter temperature --min 600 --max 900

  # Run Morris screening analysis
  python -m gas_swelling.analysis.cli morris --num-trajectories 10

  # List available parameters
  python -m gas_swelling.analysis.cli list-params

For more information, see: https://github.com/yourusername/gas-swelling-model
        """
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Analysis command to run',
        metavar='COMMAND'
    )

    # One-at-a-time (OAT) sensitivity analysis
    oat_parser = subparsers.add_parser(
        'oat',
        help='One-at-a-time sensitivity analysis',
        description='Perform one-at-a-time sensitivity analysis by varying parameters individually'
    )
    oat_parser.add_argument(
        '--parameter',
        type=str,
        help='Parameter name to analyze (if not specified, varies all parameters)'
    )
    oat_parser.add_argument(
        '--min',
        type=float,
        help='Minimum value for parameter (overrides default range)'
    )
    oat_parser.add_argument(
        '--max',
        type=float,
        help='Maximum value for parameter (overrides default range)'
    )
    oat_parser.add_argument(
        '--num-points',
        type=int,
        default=10,
        help='Number of parameter values to test (default: 10)'
    )
    oat_parser.add_argument(
        '--output',
        type=str,
        help='Output file path for results (JSON format)'
    )
    oat_parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate sensitivity plots'
    )

    # Morris screening
    morris_parser = subparsers.add_parser(
        'morris',
        help='Morris screening analysis',
        description='Perform Morris screening for global sensitivity analysis'
    )
    morris_parser.add_argument(
        '--num-trajectories',
        type=int,
        default=10,
        help='Number of trajectories to generate (default: 10)'
    )
    morris_parser.add_argument(
        '--output',
        type=str,
        help='Output file path for results (JSON format)'
    )

    # Sobol analysis
    sobol_parser = subparsers.add_parser(
        'sobol',
        help='Sobol variance-based sensitivity analysis',
        description='Perform Sobol sensitivity analysis for variance decomposition'
    )
    sobol_parser.add_argument(
        '--num-samples',
        type=int,
        default=1000,
        help='Number of samples to generate (default: 1000)'
    )
    sobol_parser.add_argument(
        '--output',
        type=str,
        help='Output file path for results (JSON format)'
    )

    # List parameters
    list_parser = subparsers.add_parser(
        'list-params',
        help='List available model parameters',
        description='List all parameters available for sensitivity analysis'
    )
    list_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show parameter ranges and descriptions'
    )

    # Batch study runner
    batch_parser = subparsers.add_parser(
        'batch',
        help='Batch study runner with parallel execution',
        description='Run multiple sensitivity analysis studies in parallel'
    )
    batch_parser.add_argument(
        '--method',
        type=str,
        choices=['oat', 'morris', 'sobol'],
        default='oat',
        help='Sensitivity analysis method to use (default: oat)'
    )
    batch_parser.add_argument(
        '--parameters',
        type=str,
        help='Comma-separated list of parameters to analyze (e.g., temperature,fission_rate)'
    )
    batch_parser.add_argument(
        '--n-samples',
        type=int,
        default=10,
        help='Number of samples per study (default: 10)'
    )
    batch_parser.add_argument(
        '--n-jobs',
        type=int,
        default=1,
        help='Number of parallel jobs to run (default: 1)'
    )
    batch_parser.add_argument(
        '--num-points',
        type=int,
        default=10,
        help='Number of parameter values for OAT analysis (default: 10)'
    )
    batch_parser.add_argument(
        '--num-trajectories',
        type=int,
        default=10,
        help='Number of trajectories for Morris analysis (default: 10)'
    )
    batch_parser.add_argument(
        '--output',
        type=str,
        help='Output file path for results (JSON format)'
    )
    batch_parser.add_argument(
        '--random-state',
        type=int,
        help='Random seed for reproducibility'
    )

    # Global options
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args(args)


def cmd_list_params(args: argparse.Namespace) -> int:
    """
    List available model parameters.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Lazy import to avoid numpy dependency for basic CLI commands
        from .sensitivity import create_default_parameter_ranges
        param_ranges = create_default_parameter_ranges()

        if args.detailed:
            print("Available Model Parameters for Sensitivity Analysis")
            print("=" * 60)
            for range_info in sorted(param_ranges, key=lambda x: x.name):
                print(f"\n{range_info.name}:")
                print(f"  Range: [{range_info.min_value:.2e}, {range_info.max_value:.2e}]")
                if hasattr(range_info, 'description') and range_info.description:
                    print(f"  Description: {range_info.description}")
        else:
            print("Available parameters:")
            for range_info in sorted(param_ranges, key=lambda x: x.name):
                print(f"  - {range_info.name}")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_oat(args: argparse.Namespace) -> int:
    """
    Run one-at-a-time sensitivity analysis.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    try:
        print("Running one-at-a-time sensitivity analysis...")
        print(f"  Number of points: {args.num_points}")

        if args.parameter:
            print(f"  Parameter: {args.parameter}")
            if args.min is not None:
                print(f"  Min: {args.min}")
            if args.max is not None:
                print(f"  Max: {args.max}")
        else:
            print("  Parameters: all")

        # TODO: Implement actual OAT analysis
        # This is a placeholder that demonstrates the CLI structure
        print("\nNote: OAT analysis implementation is in progress.")
        print("The full implementation will:")
        print("  1. Load model parameters")
        print("  2. Run simulations at specified parameter values")
        print("  3. Calculate sensitivity metrics")
        print("  4. Generate plots if --plot is specified")
        print("  5. Save results to --output if specified")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_morris(args: argparse.Namespace) -> int:
    """
    Run Morris screening analysis.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    try:
        print("Running Morris screening analysis...")
        print(f"  Number of trajectories: {args.num_trajectories}")

        # TODO: Implement actual Morris analysis
        print("\nNote: Morris analysis implementation is in progress.")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_sobol(args: argparse.Namespace) -> int:
    """
    Run Sobol sensitivity analysis.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    try:
        print("Running Sobol sensitivity analysis...")
        print(f"  Number of samples: {args.num_samples}")

        # TODO: Implement actual Sobol analysis
        print("\nNote: Sobol analysis implementation is in progress.")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _run_single_oat_study(
    parameter_name: str,
    parameter_ranges: List,
    num_points: int,
    random_state: Optional[int] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run a single OAT study for a parameter.

    Parameters
    ----------
    parameter_name : str
        Name of parameter to analyze
    parameter_ranges : List
        List of ParameterRange objects
    num_points : int
        Number of parameter values to test
    random_state : int, optional
        Random seed for reproducibility
    verbose : bool
        Whether to print progress

    Returns
    -------
    Dict[str, Any]
        Study results dictionary
    """
    from .sensitivity import OATAnalyzer, ParameterRange

    # Find the parameter range for this parameter
    param_range = None
    for pr in parameter_ranges:
        if pr.name == parameter_name:
            param_range = pr
            break

    if param_range is None:
        raise ValueError(f"Parameter '{parameter_name}' not found in ranges")

    # Create analyzer with single parameter
    analyzer = OATAnalyzer(
        parameter_ranges=[param_range],
        sim_time=7200000.0,
        t_eval_points=100
    )

    # Run OAT analysis
    percent_variations = np.linspace(-20, 20, num_points).tolist()
    results = analyzer.run_oat_analysis(
        percent_variations=percent_variations,
        verbose=verbose
    )

    # Convert results to dictionary
    if results and len(results) > 0:
        result = results[0]
        return {
            'parameter_name': parameter_name,
            'nominal_value': float(result.nominal_value),
            'variations': [float(v) for v in result.variations],
            'outputs': {k: v.tolist() for k, v in result.outputs.items()},
            'sensitivities': result.sensitivities,
            'baseline_outputs': result.baseline_outputs
        }
    else:
        return {
            'parameter_name': parameter_name,
            'error': 'No results generated'
        }


def _run_single_morris_study(
    parameter_names: List[str],
    parameter_ranges: List,
    n_trajectories: int,
    random_state: Optional[int] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run a single Morris study for multiple parameters.

    Parameters
    ----------
    parameter_names : List[str]
        Names of parameters to analyze
    parameter_ranges : List
        List of ParameterRange objects
    n_trajectories : int
        Number of trajectories to generate
    random_state : int, optional
        Random seed for reproducibility
    verbose : bool
        Whether to print progress

    Returns
    -------
    Dict[str, Any]
        Study results dictionary
    """
    from .sensitivity import MorrisAnalyzer, ParameterRange

    # Filter parameter ranges to only those requested
    filtered_ranges = [pr for pr in parameter_ranges if pr.name in parameter_names]

    if not filtered_ranges:
        raise ValueError(f"None of the parameters {parameter_names} found in ranges")

    # Create analyzer
    analyzer = MorrisAnalyzer(
        parameter_ranges=filtered_ranges,
        sim_time=7200000.0,
        t_eval_points=100
    )

    # Run Morris analysis
    result = analyzer.run_morris_analysis(
        n_trajectories=n_trajectories,
        verbose=verbose,
        random_state=random_state
    )

    return result.to_dict()


def _run_single_sobol_study(
    parameter_names: List[str],
    parameter_ranges: List,
    n_samples: int,
    random_state: Optional[int] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run a single Sobol study for multiple parameters.

    Parameters
    ----------
    parameter_names : List[str]
        Names of parameters to analyze
    parameter_ranges : List
        List of ParameterRange objects
    n_samples : int
        Number of samples to generate
    random_state : int, optional
        Random seed for reproducibility
    verbose : bool
        Whether to print progress

    Returns
    -------
    Dict[str, Any]
        Study results dictionary
    """
    from .sensitivity import SobolAnalyzer, ParameterRange

    # Filter parameter ranges to only those requested
    filtered_ranges = [pr for pr in parameter_ranges if pr.name in parameter_names]

    if not filtered_ranges:
        raise ValueError(f"None of the parameters {parameter_names} found in ranges")

    # Create analyzer
    analyzer = SobolAnalyzer(
        parameter_ranges=filtered_ranges,
        sim_time=7200000.0,
        t_eval_points=100
    )

    # Run Sobol analysis
    result = analyzer.run_sobol_analysis(
        n_samples=n_samples,
        verbose=verbose,
        random_state=random_state
    )

    return result.to_dict()


def cmd_batch(args: argparse.Namespace) -> int:
    """
    Run batch sensitivity analysis studies with parallel execution.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Import sensitivity analysis modules
        from .sensitivity import create_default_parameter_ranges

        print("Running batch sensitivity analysis...")
        print(f"  Method: {args.method}")
        print(f"  Parallel jobs: {args.n_jobs}")

        # Get parameter ranges
        param_ranges = create_default_parameter_ranges()

        # Parse parameters to analyze
        if args.parameters:
            parameters = [p.strip() for p in args.parameters.split(',')]
            # Validate parameters exist
            available_params = {pr.name for pr in param_ranges}
            invalid_params = set(parameters) - available_params
            if invalid_params:
                print(f"Error: Unknown parameters: {invalid_params}", file=sys.stderr)
                print(f"Available parameters: {', '.join(sorted(available_params))}", file=sys.stderr)
                return 1
        else:
            # Use all parameters
            parameters = [pr.name for pr in param_ranges]

        print(f"  Parameters: {', '.join(parameters)}")
        print(f"  Number of parameters: {len(parameters)}")
        print()

        # Prepare studies based on method
        studies = []

        if args.method == 'oat':
            print(f"Running OAT analysis with {args.n_jobs} parallel jobs...")
            # Create one study per parameter
            for param_name in parameters:
                study = {
                    'type': 'oat',
                    'parameter_name': param_name,
                    'parameter_ranges': param_ranges,
                    'num_points': args.num_points,
                    'random_state': args.random_state,
                    'verbose': args.n_jobs == 1  # Only verbose if single job
                }
                studies.append(study)

        elif args.method == 'morris':
            print(f"Running Morris screening with {args.n_jobs} parallel jobs...")
            # For Morris, we run a single study with all parameters
            # But if n_jobs > 1, we split trajectories across jobs
            trajectories_per_job = max(1, args.num_trajectories // args.n_jobs)
            remaining = args.num_trajectories % args.n_jobs

            for i in range(args.n_jobs):
                n_traj = trajectories_per_job + (1 if i < remaining else 0)
                if n_traj > 0:
                    study = {
                        'type': 'morris',
                        'parameter_names': parameters,
                        'parameter_ranges': param_ranges,
                        'n_trajectories': n_traj,
                        'random_state': args.random_state + i if args.random_state else None,
                        'verbose': False
                    }
                    studies.append(study)

        elif args.method == 'sobol':
            print(f"Running Sobol analysis with {args.n_jobs} parallel jobs...")
            # For Sobol, we run a single study with all parameters
            # But if n_jobs > 1, we split samples across jobs
            samples_per_job = max(1, args.n_samples // args.n_jobs)
            remaining = args.n_samples % args.n_jobs

            for i in range(args.n_jobs):
                n_samp = samples_per_job + (1 if i < remaining else 0)
                if n_samp > 0:
                    study = {
                        'type': 'sobol',
                        'parameter_names': parameters,
                        'parameter_ranges': param_ranges,
                        'n_samples': n_samp,
                        'random_state': args.random_state + i if args.random_state else None,
                        'verbose': False
                    }
                    studies.append(study)

        print(f"  Total studies to run: {len(studies)}")
        print()

        # Run studies in parallel
        results = []

        if args.n_jobs == 1:
            # Sequential execution
            print("Running studies sequentially...")
            for i, study in enumerate(studies, 1):
                print(f"  Study {i}/{len(studies)}...", end=' ')
                sys.stdout.flush()

                try:
                    if study['type'] == 'oat':
                        result = _run_single_oat_study(
                            study['parameter_name'],
                            study['parameter_ranges'],
                            study['num_points'],
                            study['random_state'],
                            study['verbose']
                        )
                    elif study['type'] == 'morris':
                        result = _run_single_morris_study(
                            study['parameter_names'],
                            study['parameter_ranges'],
                            study['n_trajectories'],
                            study['random_state'],
                            study['verbose']
                        )
                    elif study['type'] == 'sobol':
                        result = _run_single_sobol_study(
                            study['parameter_names'],
                            study['parameter_ranges'],
                            study['n_samples'],
                            study['random_state'],
                            study['verbose']
                        )
                    else:
                        raise ValueError(f"Unknown study type: {study['type']}")

                    results.append(result)
                    print("Done")

                except Exception as e:
                    print(f"Failed: {e}")
                    results.append({'error': str(e)})

        else:
            # Parallel execution
            print(f"Running studies in parallel with {args.n_jobs} workers...")
            with ProcessPoolExecutor(max_workers=args.n_jobs) as executor:
                # Submit all studies
                futures = {}
                for i, study in enumerate(studies):
                    if study['type'] == 'oat':
                        future = executor.submit(
                            _run_single_oat_study,
                            study['parameter_name'],
                            study['parameter_ranges'],
                            study['num_points'],
                            study['random_state'],
                            study['verbose']
                        )
                    elif study['type'] == 'morris':
                        future = executor.submit(
                            _run_single_morris_study,
                            study['parameter_names'],
                            study['parameter_ranges'],
                            study['n_trajectories'],
                            study['random_state'],
                            study['verbose']
                        )
                    elif study['type'] == 'sobol':
                        future = executor.submit(
                            _run_single_sobol_study,
                            study['parameter_names'],
                            study['parameter_ranges'],
                            study['n_samples'],
                            study['random_state'],
                            study['verbose']
                        )
                    else:
                        continue

                    futures[future] = i

                # Collect results as they complete
                completed = 0
                for future in as_completed(futures):
                    study_idx = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        print(f"  Study {study_idx + 1}/{len(studies)} completed")
                    except Exception as e:
                        print(f"  Study {study_idx + 1}/{len(studies)} failed: {e}")
                        results.append({'error': str(e)})

                    completed += 1

        print()
        print(f"Batch analysis complete! Completed {len([r for r in results if 'error' not in r])}/{len(studies)} studies")

        # Save results if output file specified
        if args.output:
            output_data = {
                'method': args.method,
                'parameters': parameters,
                'n_studies': len(studies),
                'n_successful': len([r for r in results if 'error' not in r]),
                'results': results
            }

            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)

            print(f"Results saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Parameters
    ----------
    args : list, optional
        Command-line arguments to parse. If None, uses sys.argv[1:].

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    parsed_args = parse_args(args)

    if parsed_args.verbose:
        print(f"Gas Swelling Model CLI v0.1.0")
        print(f"Command: {parsed_args.command}")
        print()

    # Dispatch to appropriate command handler
    if parsed_args.command == 'list-params':
        return cmd_list_params(parsed_args)
    elif parsed_args.command == 'oat':
        return cmd_oat(parsed_args)
    elif parsed_args.command == 'morris':
        return cmd_morris(parsed_args)
    elif parsed_args.command == 'sobol':
        return cmd_sobol(parsed_args)
    elif parsed_args.command == 'batch':
        return cmd_batch(parsed_args)
    else:
        # No command specified, show help
        print("Error: No command specified", file=sys.stderr)
        parse_args(['--help'])
        return 1


if __name__ == '__main__':
    sys.exit(main())
