#!/usr/bin/env python
"""
End-to-End CLI Test

This script performs comprehensive testing of the gas-swelling CLI tool,
including:
- Running simulations from CLI with all output formats
- Verifying output files are created
- Verifying progress bar appears
- Verifying exit codes
- Verifying output files contain valid data
- Error handling tests (invalid config, missing files, invalid parameters, etc.)

Based on patterns from test4_run_rk23.py
"""

import subprocess
import os
import sys
import json
import csv
import h5py
import numpy as np
from pathlib import Path

# Test configuration
TEST_CONFIG = "examples/config_example.yaml"
TEST_OUTPUT_DIR = "test_e2e_output"
TEST_FORMATS = ["csv", "json", "hdf5", "matlab"]

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str) -> None:
    """Print info message in yellow."""
    print(f"{YELLOW}ℹ {message}{RESET}")


def check_cli_installed() -> bool:
    """
    Check if gas-swelling CLI is installed.

    Returns:
        True if CLI is installed, False otherwise
    """
    print_info("Checking if gas-swelling CLI is installed...")
    try:
        result = subprocess.run(
            ["gas-swelling", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "Commands:" in result.stdout:
            print_success("gas-swelling CLI is installed")
            return True
        else:
            print_error("gas-swelling CLI not found")
            print_info("Install with: pip install -e .")
            return False
    except FileNotFoundError:
        print_error("gas-swelling command not found")
        print_info("Install with: pip install -e .")
        return False
    except Exception as e:
        print_error(f"Error checking CLI: {e}")
        return False


def run_simulation(output_format: str, verbose: bool = True) -> dict:
    """
    Run a simulation using the CLI.

    Args:
        output_format: Output format (csv, json, hdf5, matlab)
        verbose: Whether to use verbose flag

    Returns:
        Dictionary with exit_code, stdout, stderr
    """
    print_info(f"\nRunning simulation with {output_format.upper()} output format...")

    # Build command
    cmd = [
        "gas-swelling", "run",
        TEST_CONFIG,
        "--output-dir", TEST_OUTPUT_DIR,
        "--format", output_format
    ]

    if verbose:
        cmd.append("--verbose")

    # Run command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }

    except subprocess.TimeoutExpired:
        print_error("Simulation timed out after 5 minutes")
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Timeout",
            "success": False
        }
    except Exception as e:
        print_error(f"Error running simulation: {e}")
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }


def verify_output_file(output_format: str) -> bool:
    """
    Verify that the output file was created and contains valid data.

    Args:
        output_format: Output format to verify

    Returns:
        True if file is valid, False otherwise
    """
    print_info(f"Verifying {output_format.upper()} output file...")

    # Determine file path
    config_name = Path(TEST_CONFIG).stem
    output_file = os.path.join(TEST_OUTPUT_DIR, f"{config_name}_results.{output_format}")

    # Check if file exists
    if not os.path.exists(output_file):
        print_error(f"Output file not found: {output_file}")
        return False

    print_success(f"Output file created: {output_file}")

    # Verify file content based on format
    try:
        if output_format == "csv":
            return verify_csv_file(output_file)
        elif output_format == "json":
            return verify_json_file(output_file)
        elif output_format == "hdf5":
            return verify_hdf5_file(output_file)
        elif output_format == "matlab":
            return verify_matlab_file(output_file)
        else:
            print_error(f"Unknown format: {output_format}")
            return False

    except Exception as e:
        print_error(f"Error verifying {output_format} file: {e}")
        return False


def verify_csv_file(filepath: str) -> bool:
    """
    Verify CSV file contains valid data.

    Args:
        filepath: Path to CSV file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Check required columns
            required_cols = ['time', 'Rcb', 'Rcf', 'swelling']
            if not all(col in reader.fieldnames for col in required_cols):
                print_error(f"CSV missing required columns: {required_cols}")
                return False

            # Check data rows
            if len(rows) < 2:
                print_error("CSV has insufficient data rows")
                return False

            # Verify data can be parsed as floats
            try:
                time_val = float(rows[0]['time'])
                rcb_val = float(rows[0]['Rcb'])
                swelling_val = float(rows[0]['swelling'])
            except (ValueError, KeyError) as e:
                print_error(f"CSV data parsing failed: {e}")
                return False

            print_success(f"CSV file valid with {len(rows)} data rows")
            return True

    except Exception as e:
        print_error(f"Error reading CSV: {e}")
        return False


def verify_json_file(filepath: str) -> bool:
    """
    Verify JSON file contains valid data.

    Args:
        filepath: Path to JSON file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Check structure
        if 'results' not in data or 'metadata' not in data:
            print_error("JSON missing 'results' or 'metadata' keys")
            return False

        results = data['results']
        metadata = data['metadata']

        # Check required fields
        required_fields = ['time', 'Rcb', 'Rcf', 'swelling']
        if not all(field in results for field in required_fields):
            print_error(f"JSON results missing required fields: {required_fields}")
            return False

        # Verify data is list/array
        if not isinstance(results['time'], list):
            print_error("JSON 'time' field is not a list")
            return False

        if len(results['time']) < 2:
            print_error("JSON has insufficient data points")
            return False

        # Check metadata
        if 'temperature' not in metadata:
            print_error("JSON metadata missing 'temperature'")
            return False

        print_success(f"JSON file valid with {len(results['time'])} data points")
        return True

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        print_error(f"Error reading JSON: {e}")
        return False


def verify_hdf5_file(filepath: str) -> bool:
    """
    Verify HDF5 file contains valid data.

    Args:
        filepath: Path to HDF5 file

    Returns:
        True if valid, False otherwise
    """
    try:
        with h5py.File(filepath, 'r') as f:
            # Check required datasets
            required_datasets = ['time', 'Rcb', 'Rcf', 'swelling']
            missing = [ds for ds in required_datasets if ds not in f]

            if missing:
                print_error(f"HDF5 missing required datasets: {missing}")
                return False

            # Verify dataset sizes
            time_len = len(f['time'])
            if time_len < 2:
                print_error("HDF5 has insufficient data points")
                return False

            # Check all datasets have same length
            for ds in required_datasets:
                if len(f[ds]) != time_len:
                    print_error(f"HDF5 dataset '{ds}' has inconsistent length")
                    return False

            print_success(f"HDF5 file valid with {time_len} data points")
            return True

    except Exception as e:
        print_error(f"Error reading HDF5: {e}")
        return False


def verify_matlab_file(filepath: str) -> bool:
    """
    Verify MATLAB file contains valid data.

    Args:
        filepath: Path to MATLAB .mat file

    Returns:
        True if valid, False otherwise
    """
    try:
        from scipy.io import loadmat

        data = loadmat(filepath)

        # Check required variables
        required_vars = ['time', 'Rcb', 'Rcf', 'swelling']
        missing = [var for var in required_vars if var not in data]

        if missing:
            print_error(f"MATLAB file missing required variables: {missing}")
            return False

        # Verify data sizes
        time_len = len(data['time'].flatten())
        if time_len < 2:
            print_error("MATLAB file has insufficient data points")
            return False

        print_success(f"MATLAB file valid with {time_len} data points")
        return True

    except Exception as e:
        print_error(f"Error reading MATLAB file: {e}")
        return False


def verify_progress_bar(output: str) -> bool:
    """
    Verify that progress bar appeared in output.

    Args:
        output: stdout from CLI run

    Returns:
        True if progress indicators found, False otherwise
    """
    print_info("Checking for progress indicators...")

    # Check for various progress indicators
    progress_indicators = [
        "Simulating",
        "%",
        "Running simulation"
    ]

    has_progress = any(indicator in output for indicator in progress_indicators)

    if has_progress:
        print_success("Progress indicators found in output")
    else:
        print_error("No progress indicators found in output")

    return has_progress


def cleanup_test_files() -> None:
    """Clean up test output directory."""
    print_info("Cleaning up test files...")
    try:
        import shutil
        if os.path.exists(TEST_OUTPUT_DIR):
            shutil.rmtree(TEST_OUTPUT_DIR)
            print_success("Test output directory cleaned")
    except Exception as e:
        print_error(f"Error cleaning up: {e}")


def test_help_command() -> bool:
    """
    Test the --help command.

    Returns:
        True if help displays correctly, False otherwise
    """
    print_info("Testing --help command...")

    try:
        result = subprocess.run(
            ["gas-swelling", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print_error("Help command returned non-zero exit code")
            return False

        # Check for expected help content
        expected_content = ["Usage:", "Commands:", "run", "Options:"]
        missing = [content for content in expected_content if content not in result.stdout]

        if missing:
            print_error(f"Help output missing: {missing}")
            return False

        print_success("Help command displays correctly")
        return True

    except Exception as e:
        print_error(f"Error testing help command: {e}")
        return False


def test_run_help() -> bool:
    """
    Test the 'run --help' command.

    Returns:
        True if run help displays correctly, False otherwise
    """
    print_info("Testing 'run --help' command...")

    try:
        result = subprocess.run(
            ["gas-swelling", "run", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print_error("Run help command returned non-zero exit code")
            return False

        # Check for expected options in help
        expected_options = ["--output-dir", "--format", "--verbose", "-v"]
        missing = [opt for opt in expected_options if opt not in result.stdout]

        if missing:
            print_error(f"Run help missing options: {missing}")
            return False

        print_success("Run help displays all options correctly")
        return True

    except Exception as e:
        print_error(f"Error testing run help: {e}")
        return False


def test_output_dir_option() -> bool:
    """
    Test the --output-dir option with various directory paths.

    Returns:
        True if output-dir option works correctly, False otherwise
    """
    print_info("Testing --output-dir option...")

    test_dirs = [
        "test_output_custom",
        "test_output/nested/path",
        "test_output_with_spaces"
    ]

    for test_dir in test_dirs:
        print_info(f"  Testing output directory: {test_dir}")

        # Build command
        cmd = [
            "gas-swelling", "run",
            TEST_CONFIG,
            "--output-dir", test_dir,
            "--format", "csv"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print_error(f"Failed with output-dir={test_dir}")
                print(f"STDERR: {result.stderr}")
                return False

            # Check if output file was created in the specified directory
            config_name = Path(TEST_CONFIG).stem
            expected_file = os.path.join(test_dir, f"{config_name}_results.csv")

            if not os.path.exists(expected_file):
                print_error(f"Output file not created in {test_dir}")
                return False

            print_success(f"Output directory {test_dir} works correctly")

            # Clean up
            import shutil
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)

        except Exception as e:
            print_error(f"Error with output-dir={test_dir}: {e}")
            return False

    return True


def test_verbose_flag() -> bool:
    """
    Test the --verbose flag.

    Returns:
        True if verbose flag works correctly, False otherwise
    """
    print_info("Testing --verbose flag...")

    # Test with verbose flag
    cmd_verbose = [
        "gas-swelling", "run",
        TEST_CONFIG,
        "--output-dir", TEST_OUTPUT_DIR,
        "--format", "csv",
        "--verbose"
    ]

    # Test without verbose flag
    cmd_quiet = [
        "gas-swelling", "run",
        TEST_CONFIG,
        "--output-dir", TEST_OUTPUT_DIR,
        "--format", "csv"
    ]

    try:
        result_verbose = subprocess.run(
            cmd_verbose,
            capture_output=True,
            text=True,
            timeout=300
        )

        result_quiet = subprocess.run(
            cmd_quiet,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result_verbose.returncode != 0 or result_quiet.returncode != 0:
            print_error("Simulation failed with/without verbose flag")
            return False

        # Check that verbose output contains more information
        verbose_lines = len(result_verbose.stdout.split('\n'))
        quiet_lines = len(result_quiet.stdout.split('\n'))

        # Verbose output should generally be longer or contain specific keywords
        verbose_keywords = ["Loading configuration", "Validating parameters", "Creating model"]
        has_verbose_info = any(keyword in result_verbose.stdout for keyword in verbose_keywords)

        if not has_verbose_info:
            print_error("Verbose output doesn't contain expected information")
            return False

        print_success(f"Verbose flag works correctly (verbose: {verbose_lines} lines, quiet: {quiet_lines} lines)")
        return True

    except Exception as e:
        print_error(f"Error testing verbose flag: {e}")
        return False


def test_format_option() -> bool:
    """
    Test the --format option with all valid formats.

    Returns:
        True if all format options work correctly, False otherwise
    """
    print_info("Testing --format option...")

    for fmt in TEST_FORMATS:
        print_info(f"  Testing format: {fmt}")

        cmd = [
            "gas-swelling", "run",
            TEST_CONFIG,
            "--output-dir", TEST_OUTPUT_DIR,
            "--format", fmt
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print_error(f"Failed with format={fmt}")
                print(f"STDERR: {result.stderr}")
                return False

            # Verify output file exists
            if not verify_output_file(fmt):
                return False

        except Exception as e:
            print_error(f"Error with format={fmt}: {e}")
            return False

    print_success("All format options work correctly")
    return True


def test_invalid_format() -> bool:
    """
    Test that invalid format options are properly rejected.

    Returns:
        True if invalid formats are rejected, False otherwise
    """
    print_info("Testing invalid format option...")

    cmd = [
        "gas-swelling", "run",
        TEST_CONFIG,
        "--output-dir", TEST_OUTPUT_DIR,
        "--format", "invalid_format"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with invalid format
        if result.returncode == 0:
            print_error("Invalid format was accepted (should have failed)")
            return False

        # Check error message mentions invalid choice
        if "Invalid value" in result.stderr or "invalid choice" in result.stderr.lower():
            print_success("Invalid format properly rejected")
            return True
        else:
            print_error(f"Unexpected error message: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error testing invalid format: {e}")
        return False


def test_missing_config() -> bool:
    """
    Test behavior when config file is missing.

    Returns:
        True if missing config is handled correctly, False otherwise
    """
    print_info("Testing missing config file...")

    cmd = [
        "gas-swelling", "run",
        "nonexistent_config.yaml",
        "--output-dir", TEST_OUTPUT_DIR
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail
        if result.returncode == 0:
            print_error("Missing config was accepted (should have failed)")
            return False

        # Check error message
        if "not found" in result.stderr.lower() or "no such file" in result.stderr.lower():
            print_success("Missing config properly handled")
            return True
        else:
            print_error(f"Unexpected error message: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error testing missing config: {e}")
        return False


def test_option_combinations() -> bool:
    """
    Test various combinations of options.

    Returns:
        True if all combinations work correctly, False otherwise
    """
    print_info("Testing option combinations...")

    combinations = [
        {"format": "json", "verbose": True},
        {"format": "hdf5", "verbose": False},
        {"format": "csv", "verbose": True},
    ]

    for i, combo in enumerate(combinations, 1):
        print_info(f"  Testing combination {i}: format={combo['format']}, verbose={combo['verbose']}")

        cmd = [
            "gas-swelling", "run",
            TEST_CONFIG,
            "--output-dir", TEST_OUTPUT_DIR,
            "--format", combo["format"]
        ]

        if combo["verbose"]:
            cmd.append("--verbose")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print_error(f"Combination {i} failed")
                print(f"STDERR: {result.stderr}")
                return False

            # Verify output file
            if not verify_output_file(combo["format"]):
                return False

        except Exception as e:
            print_error(f"Error with combination {i}: {e}")
            return False

    print_success("All option combinations work correctly")
    return True


def test_invalid_yaml_syntax() -> bool:
    """
    Test behavior when config file has invalid YAML syntax.

    Returns:
        True if invalid YAML is properly rejected, False otherwise
    """
    print_info("Testing invalid YAML syntax...")

    # Create a temporary config file with invalid YAML
    invalid_yaml_config = "test_invalid_yaml.yaml"
    try:
        with open(invalid_yaml_config, 'w') as f:
            f.write("""
temperature: 773.0
fission_rate: 5e19
max_time: 8640000
invalid_yaml: [unclosed bracket
""")

        cmd = [
            "gas-swelling", "run",
            invalid_yaml_config,
            "--output-dir", TEST_OUTPUT_DIR
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail
        if result.returncode == 0:
            print_error("Invalid YAML was accepted (should have failed)")
            return False

        # Check for YAML error indication
        error_output = result.stderr.lower() + result.stdout.lower()
        if "yaml" in error_output or "syntax" in error_output or "parse" in error_output:
            print_success("Invalid YAML properly rejected")
            return True
        else:
            print_error(f"Unexpected error message: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error testing invalid YAML: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(invalid_yaml_config):
            os.remove(invalid_yaml_config)


def test_invalid_parameter_values() -> bool:
    """
    Test behavior when config file has invalid parameter values.

    Returns:
        True if invalid parameters are properly rejected, False otherwise
    """
    print_info("Testing invalid parameter values...")

    test_cases = [
        {
            "name": "negative_temperature",
            "content": "temperature: -100.0\nfission_rate: 5e19\n",
            "error_indicator": "below minimum"
        },
        {
            "name": "temperature_too_high",
            "content": "temperature: 10000.0\nfission_rate: 5e19\n",
            "error_indicator": "exceeds maximum"
        },
        {
            "name": "negative_fission_rate",
            "content": "temperature: 773.0\nfission_rate: -1e10\n",
            "error_indicator": "below minimum"
        },
        {
            "name": "invalid_eos_model",
            "content": "temperature: 773.0\nfission_rate: 5e19\neos_model: invalid_model\n",
            "error_indicator": "not allowed"
        },
        {
            "name": "wrong_type_temperature",
            "content": "temperature: \"not_a_number\"\nfission_rate: 5e19\n",
            "error_indicator": "incorrect type"
        },
    ]

    for test_case in test_cases:
        print_info(f"  Testing: {test_case['name']}")

        invalid_config = f"test_invalid_{test_case['name']}.yaml"
        try:
            # Create config with invalid parameter
            with open(invalid_config, 'w') as f:
                f.write(test_case['content'])

            cmd = [
                "gas-swelling", "run",
                invalid_config,
                "--output-dir", TEST_OUTPUT_DIR
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should fail
            if result.returncode == 0:
                print_error(f"Invalid parameter '{test_case['name']}' was accepted")
                return False

            # Check for appropriate error message
            error_output = result.stderr.lower() + result.stdout.lower()
            if test_case['error_indicator'] in error_output:
                print_success(f"Parameter '{test_case['name']}' properly rejected")
            else:
                print_error(f"Expected error indicator '{test_case['error_indicator']}' not found")
                print(f"STDERR: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error testing {test_case['name']}: {e}")
            return False
        finally:
            # Clean up
            if os.path.exists(invalid_config):
                os.remove(invalid_config)

    return True


def test_missing_required_parameters() -> bool:
    """
    Test behavior when config file is missing required parameters.

    Returns:
        True if missing parameters are properly detected, False otherwise
    """
    print_info("Testing missing required parameters...")

    test_cases = [
        {
            "name": "missing_temperature",
            "content": "fission_rate: 5e19\n",
            "missing_param": "temperature"
        },
        {
            "name": "missing_fission_rate",
            "content": "temperature: 773.0\n",
            "missing_param": "fission_rate"
        },
        {
            "name": "empty_config",
            "content": "{}",
            "missing_param": "temperature"
        },
    ]

    for test_case in test_cases:
        print_info(f"  Testing: {test_case['name']}")

        invalid_config = f"test_missing_{test_case['name']}.yaml"
        try:
            # Create config missing required parameters
            with open(invalid_config, 'w') as f:
                f.write(test_case['content'])

            cmd = [
                "gas-swelling", "run",
                invalid_config,
                "--output-dir", TEST_OUTPUT_DIR
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should fail
            if result.returncode == 0:
                print_error(f"Missing parameter '{test_case['name']}' was accepted")
                return False

            # Check for missing parameter error
            error_output = result.stderr.lower() + result.stdout.lower()
            if "missing" in error_output and test_case['missing_param'] in error_output:
                print_success(f"Missing parameter '{test_case['missing_param']}' properly detected")
            else:
                print_error(f"Expected missing parameter error not found")
                print(f"STDERR: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error testing {test_case['name']}: {e}")
            return False
        finally:
            # Clean up
            if os.path.exists(invalid_config):
                os.remove(invalid_config)

    return True


def test_invalid_command() -> bool:
    """
    Test behavior when invalid command is provided.

    Returns:
        True if invalid command is properly rejected, False otherwise
    """
    print_info("Testing invalid command...")

    cmd = [
        "gas-swelling", "invalid_command",
        TEST_CONFIG
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail
        if result.returncode == 0:
            print_error("Invalid command was accepted (should have failed)")
            return False

        # Check for error message
        error_output = result.stderr.lower() + result.stdout.lower()
        if "invalid" in error_output or "not found" in error_output or "no such command" in error_output:
            print_success("Invalid command properly rejected")
            return True
        else:
            print_error(f"Unexpected error message: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error testing invalid command: {e}")
        return False


def test_missing_arguments() -> bool:
    """
    Test behavior when required arguments are missing.

    Returns:
        True if missing arguments are properly detected, False otherwise
    """
    print_info("Testing missing arguments...")

    # Test 1: Missing config file argument for 'run' command
    print_info("  Testing: missing config argument")
    cmd = ["gas-swelling", "run"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail
        if result.returncode == 0:
            print_error("Missing config argument was accepted")
            return False

        # Check for missing argument error
        error_output = result.stderr.lower() + result.stdout.lower()
        if "missing" in error_output or "required" in error_output or "argument" in error_output:
            print_success("Missing argument properly detected")
        else:
            print_error(f"Expected missing argument error not found")
            print(f"STDERR: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Error testing missing arguments: {e}")
        return False

    return True


def test_parameter_relationships() -> bool:
    """
    Test validation of logical parameter relationships.

    Returns:
        True if invalid parameter relationships are detected, False otherwise
    """
    print_info("Testing parameter relationship validation...")

    test_cases = [
        {
            "name": "time_step_gt_max_time_step",
            "content": "temperature: 773.0\nfission_rate: 5e19\ntime_step: 100.0\nmax_time_step: 10.0\n",
            "error_indicator": "time_step"
        },
        {
            "name": "time_step_gt_max_time",
            "content": "temperature: 773.0\nfission_rate: 5e19\ntime_step: 1e7\nmax_time: 1e6\n",
            "error_indicator": "time_step"
        },
    ]

    for test_case in test_cases:
        print_info(f"  Testing: {test_case['name']}")

        invalid_config = f"test_relation_{test_case['name']}.yaml"
        try:
            # Create config with invalid parameter relationship
            with open(invalid_config, 'w') as f:
                f.write(test_case['content'])

            cmd = [
                "gas-swelling", "run",
                invalid_config,
                "--output-dir", TEST_OUTPUT_DIR
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should fail
            if result.returncode == 0:
                print_error(f"Invalid relationship '{test_case['name']}' was accepted")
                return False

            # Check for appropriate error message
            error_output = result.stderr.lower() + result.stdout.lower()
            if test_case['error_indicator'] in error_output:
                print_success(f"Invalid relationship '{test_case['name']}' properly detected")
            else:
                print_error(f"Expected error indicator '{test_case['error_indicator']}' not found")
                print(f"STDERR: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error testing {test_case['name']}: {e}")
            return False
        finally:
            # Clean up
            if os.path.exists(invalid_config):
                os.remove(invalid_config)

    return True


def main():
    """
    Main test execution function.

    Runs all end-to-end tests and reports results.
    """
    print("=" * 70)
    print("Gas Swelling CLI - End-to-End Test Suite")
    print("=" * 70)

    # Track test results
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }

    # Test 1: Check CLI installation
    print("\n" + "=" * 70)
    print("Test 1: CLI Installation Check")
    print("=" * 70)

    if not check_cli_installed():
        print_error("CLI not installed. Exiting.")
        sys.exit(1)

    results["passed"] += 1
    results["tests"].append(("CLI Installation", True))

    # Create test output directory
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    # Test 2: Help command
    print("\n" + "=" * 70)
    print("Test 2: Help Command")
    print("=" * 70)

    test_passed = test_help_command()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Help Command", test_passed))

    # Test 3: Run help
    print("\n" + "=" * 70)
    print("Test 3: Run Help")
    print("=" * 70)

    test_passed = test_run_help()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Run Help", test_passed))

    # Test 4: Output directory option
    print("\n" + "=" * 70)
    print("Test 4: --output-dir Option")
    print("=" * 70)

    test_passed = test_output_dir_option()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("--output-dir Option", test_passed))

    # Test 5: Verbose flag
    print("\n" + "=" * 70)
    print("Test 5: --verbose Flag")
    print("=" * 70)

    test_passed = test_verbose_flag()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("--verbose Flag", test_passed))

    # Test 6: Format option
    print("\n" + "=" * 70)
    print("Test 6: --format Option")
    print("=" * 70)

    test_passed = test_format_option()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("--format Option", test_passed))

    # Test 7: Invalid format
    print("\n" + "=" * 70)
    print("Test 7: Invalid Format Handling")
    print("=" * 70)

    test_passed = test_invalid_format()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Invalid Format", test_passed))

    # Test 8: Missing config
    print("\n" + "=" * 70)
    print("Test 8: Missing Config Handling")
    print("=" * 70)

    test_passed = test_missing_config()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Missing Config", test_passed))

    # Test 9: Option combinations
    print("\n" + "=" * 70)
    print("Test 9: Option Combinations")
    print("=" * 70)

    test_passed = test_option_combinations()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Option Combinations", test_passed))

    # Test 10: Invalid YAML syntax
    print("\n" + "=" * 70)
    print("Test 10: Invalid YAML Syntax")
    print("=" * 70)

    test_passed = test_invalid_yaml_syntax()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Invalid YAML Syntax", test_passed))

    # Test 11: Invalid parameter values
    print("\n" + "=" * 70)
    print("Test 11: Invalid Parameter Values")
    print("=" * 70)

    test_passed = test_invalid_parameter_values()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Invalid Parameter Values", test_passed))

    # Test 12: Missing required parameters
    print("\n" + "=" * 70)
    print("Test 12: Missing Required Parameters")
    print("=" * 70)

    test_passed = test_missing_required_parameters()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Missing Required Parameters", test_passed))

    # Test 13: Invalid command
    print("\n" + "=" * 70)
    print("Test 13: Invalid Command")
    print("=" * 70)

    test_passed = test_invalid_command()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Invalid Command", test_passed))

    # Test 14: Missing arguments
    print("\n" + "=" * 70)
    print("Test 14: Missing Arguments")
    print("=" * 70)

    test_passed = test_missing_arguments()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Missing Arguments", test_passed))

    # Test 15: Parameter relationships
    print("\n" + "=" * 70)
    print("Test 15: Parameter Relationships")
    print("=" * 70)

    test_passed = test_parameter_relationships()
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append(("Parameter Relationships", test_passed))

    # Test 16-19: Run simulations with different output formats (legacy tests)
    for output_format in TEST_FORMATS:
        print("\n" + "=" * 70)
        print(f"Test: {output_format.upper()} Output Format (Full Simulation)")
        print("=" * 70)

        # Run simulation
        sim_result = run_simulation(output_format, verbose=True)

        # Verify exit code
        exit_code_ok = sim_result["exit_code"] == 0
        if exit_code_ok:
            print_success(f"Exit code is 0 (success)")
        else:
            print_error(f"Exit code is {sim_result['exit_code']} (expected 0)")
            print(f"STDOUT: {sim_result['stdout']}")
            print(f"STDERR: {sim_result['stderr']}")

        # Verify output file
        output_ok = verify_output_file(output_format)

        # Verify progress bar (only check first format)
        progress_ok = True
        if output_format == TEST_FORMATS[0]:
            progress_ok = verify_progress_bar(sim_result["stdout"])

        # Record results
        test_passed = exit_code_ok and output_ok and progress_ok
        if test_passed:
            results["passed"] += 1
            print_success(f"{output_format.upper()} format test PASSED")
        else:
            results["failed"] += 1
            print_error(f"{output_format.upper()} format test FAILED")

        results["tests"].append((f"{output_format.upper()} Full Simulation", test_passed))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    total = results["passed"] + results["failed"]
    print(f"Total tests: {total}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")

    # Detailed results
    print("\nDetailed Results:")
    for test_name, passed in results["tests"]:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {test_name}: {status}")

    # Exit with appropriate code
    if results["failed"] > 0:
        print("\n" + RED + "Some tests FAILED" + RESET)
        cleanup_test_files()
        sys.exit(1)
    else:
        print("\n" + GREEN + "All tests PASSED!" + RESET)
        cleanup_test_files()
        sys.exit(0)


if __name__ == "__main__":
    main()
