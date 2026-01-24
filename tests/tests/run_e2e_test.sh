#!/bin/bash
# End-to-End Test Runner for Visualization Module
# This script runs comprehensive tests of all plotting functions

set -e  # Exit on error

echo "=========================================="
echo "  Gas Swelling Visualization E2E Test"
echo "=========================================="

# Check Python environment
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found"
    exit 1
fi

echo "Using: $PYTHON"
$PYTHON --version

# Check dependencies
echo ""
echo "Checking dependencies..."
$PYTHON -c "import numpy; print('  ✓ numpy')"
$PYTHON -c "import scipy; print('  ✓ scipy')"
$PYTHON -c "import matplotlib; print('  ✓ matplotlib')"

# Run the test
echo ""
echo "Running end-to-end test..."
echo ""

# Run with default options (quick mode, no temperature sweep)
$PYTHON tests/test_visualization_e2e.py --quick --no-sweep

echo ""
echo "=========================================="
echo "  Test Complete"
echo "=========================================="
