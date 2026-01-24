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


def main():
    """
    Main test execution function.

    Runs all end-to-end tests and reports results.
    """
    print("=" * 70)
    print("Gas Swelling CLI - End-to-End Test")
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

    # Test 2-5: Run simulations with different output formats
    for output_format in TEST_FORMATS:
        print("\n" + "=" * 70)
        print(f"Test: {output_format.upper()} Output Format")
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

        results["tests"].append((f"{output_format.upper()} Output", test_passed))

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
