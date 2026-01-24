#!/usr/bin/env python3
"""
Test script for error handling and exit codes in the gas-swelling CLI.

This script verifies that the CLI returns appropriate exit codes for various
error conditions, which is important for automation and scripting.
"""

import subprocess
import sys
import os


def run_command(cmd):
    """Run a command and return the exit code and output."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_error_scenarios():
    """Test various error scenarios and verify exit codes."""
    python = sys.executable
    tests = []

    # Test 1: Nonexistent configuration file
    print("Test 1: Nonexistent configuration file")
    exit_code, stdout, stderr = run_command(
        f"{python} -m cli run nonexistent.yaml"
    )
    print(f"  Exit code: {exit_code}")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "not found" in stdout.lower() or "not found" in stderr.lower()
    print("  ✓ PASSED\n")

    # Test 2: Invalid parameter value (temperature below minimum)
    print("Test 2: Invalid parameter value")
    exit_code, stdout, stderr = run_command(
        f"{python} -m cli run /tmp/test_invalid_temp.yaml"
    )
    print(f"  Exit code: {exit_code}")
    # Create test file with invalid temperature
    with open('/tmp/test_invalid_temp.yaml', 'w') as f:
        f.write("temperature: -100\n")
    exit_code, stdout, stderr = run_command(
        f"{python} -m cli run /tmp/test_invalid_temp.yaml"
    )
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "below minimum" in stdout or "below minimum" in stderr
    print("  ✓ PASSED\n")

    # Test 3: Invalid YAML syntax
    print("Test 3: Invalid YAML syntax")
    with open('/tmp/test_bad_yaml.yaml', 'w') as f:
        f.write("invalid: [yaml\n")
    exit_code, stdout, stderr = run_command(
        f"{python} -m cli run /tmp/test_bad_yaml.yaml"
    )
    print(f"  Exit code: {exit_code}")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert ("yaml" in stdout.lower() or "yaml" in stderr.lower() or
            "parsing" in stdout.lower() or "parsing" in stderr.lower())
    print("  ✓ PASSED\n")

    # Test 4: Valid configuration (should succeed)
    print("Test 4: Valid configuration (should succeed)")
    if os.path.exists("examples/config_example.yaml"):
        exit_code, stdout, stderr = run_command(
            f"{python} -m cli run examples/config_example.yaml --output-dir /tmp/test_error_output"
        )
        print(f"  Exit code: {exit_code}")
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
        assert "successfully" in stdout.lower() or "successfully" in stderr.lower()
        print("  ✓ PASSED\n")
    else:
        print("  ⊘ SKIPPED (examples/config_example.yaml not found)\n")

    # Test 5: Empty configuration (should use defaults and succeed)
    print("Test 5: Empty configuration with defaults")
    with open('/tmp/test_empty.yaml', 'w') as f:
        f.write("# Empty config file\n")
    exit_code, stdout, stderr = run_command(
        f"{python} -m cli run /tmp/test_empty.yaml --output-dir /tmp/test_error_output"
    )
    print(f"  Exit code: {exit_code}")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    assert "successfully" in stdout.lower() or "successfully" in stderr.lower()
    print("  ✓ PASSED\n")

    # Test 6: Invalid format option (Click validation)
    print("Test 6: Invalid format option")
    if os.path.exists("examples/config_example.yaml"):
        exit_code, stdout, stderr = run_command(
            f"{python} -m cli run examples/config_example.yaml --format invalid"
        )
        print(f"  Exit code: {exit_code}")
        # This is a Click validation error, which returns exit code 2
        # The important thing is it's a non-zero exit code indicating failure
        assert exit_code != 0, f"Expected non-zero exit code, got {exit_code}"
        assert "invalid" in stdout.lower() or "invalid" in stderr.lower()
        print("  ✓ PASSED (non-zero exit code for invalid option)\n")
    else:
        print("  ⊘ SKIPPED (examples/config_example.yaml not found)\n")

    print("=" * 60)
    print("All error handling tests passed! ✓")
    print("=" * 60)
    print("\nSummary:")
    print("  - Exit code 0: Success")
    print("  - Exit code 1: Error (file not found, invalid parameters, etc.)")
    print("  - Non-zero exit codes: All error conditions")
    print("\nThe CLI properly indicates success/failure for automation.")


if __name__ == "__main__":
    test_error_scenarios()
