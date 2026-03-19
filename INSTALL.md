# Installation Guide

This guide provides step-by-step instructions for installing the Gas Swelling Model package using pip, conda, or from source.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [Method 1: Install with pip](#method-1-install-with-pip)
  - [Method 2: Install with conda](#method-2-install-with-conda)
  - [Method 3: Build from Source](#method-3-build-from-source)
- [Verifying Installation](#verifying-installation)
- [Optional Dependencies](#optional-dependencies)
- [Building Documentation](#building-documentation)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Python Version
- **Minimum**: Python 3.8
- **Recommended**: Python 3.10 or 3.11
- **Tested on**: Python 3.8, 3.9, 3.10, 3.11, 3.12

### Operating Systems
- Linux (Ubuntu, CentOS, Rocky Linux, etc.)
- macOS (10.15+)
- Windows (10/11 with WSL2 recommended)

### Hardware Requirements
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk Space**: 500 MB for package installation
- **CPU**: Any modern x86-64 processor (ARM support experimental)

---

## Installation Methods

### Method 1: Install with pip

This is the **recommended** installation method for most users.

#### Prerequisites

Ensure you have Python 3.8+ installed:

```bash
python --version
# or
python3 --version
```

#### Standard Installation

Install the latest stable version from PyPI (when published):

```bash
pip install gas-swelling-model
```

#### Installation with Plotting Support

For plotting and visualization features, install with optional dependencies:

```bash
pip install gas-swelling-model[plotting]
```

#### Development Installation

If you want to modify the code or contribute:

```bash
# Clone the repository
git clone https://github.com/yourusername/gas-swelling-model.git
cd gas-swelling-model

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

#### User-Only Installation

If you don't have administrative privileges:

```bash
pip install --user gas-swelling-model
```

**Note**: Make sure `~/.local/bin` is in your `PATH`:

```bash
export PATH=$HOME/.local/bin:$PATH
```

---

### Method 2: Install with conda

If you use Anaconda or Miniconda, you can install the package in a conda environment.

#### Step 1: Create a New Environment (Recommended)

```bash
conda create -n gas-swelling python=3.11
conda activate gas-swelling
```

#### Step 2: Install Dependencies

```bash
conda install -c conda-forge numpy scipy
```

#### Step 3: Install Optional Plotting Dependencies

```bash
conda install -c conda-forge matplotlib
```

#### Step 4: Install the Package

```bash
# Install from PyPI with pip
pip install gas-swelling-model

# OR install from local directory
cd /path/to/gas-swelling-model
pip install .
```

#### Complete conda Installation Script

```bash
#!/bin/bash
# Create and setup environment
conda create -n gas-swelling python=3.11 -y
conda activate gas-swelling
conda install -c conda-forge numpy scipy matplotlib -y
pip install gas-swelling-model
```

---

### Method 3: Build from Source

Build the package from source for development or customized installations.

#### Prerequisites

Install build dependencies:

```bash
# Using pip
pip install build twine

# Using conda
conda install -c conda-forge build
```

#### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/gas-swelling-model.git
cd gas-swelling-model
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n gas-swelling python=3.11
conda activate gas-swelling
```

#### Step 3: Install Build Dependencies

```bash
pip install setuptools wheel build
```

#### Step 4: Build and Install

```bash
# Build the package
python -m build

# Install from built wheel
pip install dist/gas_swelling_model-*.whl

# OR install in editable mode for development
pip install -e .
```

#### Step 5: Verify Installation

```bash
python -c "import gas_swelling; print(gas_swelling.__version__)"
```

#### Building Distribution Packages

To create distributable packages:

```bash
# Build source distribution and wheel
python -m build

# Output files:
# - dist/gas_swelling_model-0.1.0.tar.gz   (source distribution)
# - dist/gas_swelling_model-0.1.0-py3-none-any.whl  (wheel)
```

---

## Verifying Installation

After installation, verify that the package is working correctly.

### Quick Verification

```bash
# Check package installation
pip show gas-swelling-model

# Test import
python -c "from gas_swelling import GasSwellingModel; print('Installation successful!')"
```

### Run Test Simulation

Create a test script `test_installation.py`:

```python
#!/usr/bin/env python
"""Test script to verify installation"""

from gas_swelling import GasSwellingModel
from gas_swelling.params import create_default_parameters

# Create parameters
params = create_default_parameters()

# Initialize model
model = GasSwellingModel(params)

# Run short simulation
print("Running test simulation...")
result = model.solve(t_span=(0, 1e6), t_eval=None)  # 1 second simulation

# Check results
if result['success']:
    print("✓ Installation successful!")
    print(f"  Time steps: {len(result['t'])}")
    print(f"  Final swelling: {result['swelling'][-1]:.2e}")
else:
    print("✗ Installation test failed")
    exit(1)
```

Run the test:

```bash
python test_installation.py
```

### Expected Output

```
Running test simulation...
✓ Installation successful!
  Time steps: 100
  Final swelling: 1.23e-04
```

---

## Optional Dependencies

### Plotting Dependencies

For visualization and plotting capabilities:

```bash
# Using pip
pip install matplotlib>=3.3.0

# Using conda
conda install -c conda-forge matplotlib
```

### Development Dependencies

For running tests and contributing:

```bash
# Using pip
pip install gas-swelling-model[dev]

# Or install individually
pip install pytest pytest-cov build twine
```

### Safe Local Test Runner

The repo includes a helper script for local test runs:

```bash
./scripts/test_safe.sh tests/test_import.py
./.venv/bin/python scripts/test_safe.py tests/test_import.py
./.venv/bin/python scripts/test_safe.py --timeout 300 -- tests/test_import.py
```

It adds a default timeout, sets writable cache directories for plotting-related
imports, and terminates the whole pytest process tree if the run times out.
Use `test_safe.py` when you want the same cross-platform entry point as CI.

### Documentation Dependencies

For local Sphinx builds:

```bash
./.venv/bin/python -m pip install -r docs/requirements.txt
```

### All Optional Dependencies

```bash
# Install everything
pip install gas-swelling-model[all]
```

---

## Building Documentation

The repository includes a Sphinx documentation site under `docs/`.

### Recommended Commands

```bash
# Install docs dependencies into the repo virtualenv
./.venv/bin/python -m pip install -r docs/requirements.txt

# Fast smoke build (no HTML output, checks links/parsing)
make -C docs dummy-offline

# Full offline HTML build
make -C docs html-offline
```

### Output Location

The generated HTML site is written to:

```text
docs/_build/html/
```

Open `docs/_build/html/index.html` in a browser after the build finishes.

### Why the Offline Target Is Recommended

- It uses the repo virtualenv by default through `docs/Makefile`
- It avoids external intersphinx fetches, which helps in restricted or offline environments
- It sets writable cache directories for Matplotlib/font handling during the build

### Direct Python Alternative

If you prefer not to use `make`, the equivalent command is:

```bash
SPHINX_OFFLINE=1 MPLCONFIGDIR=/tmp/mplconfig XDG_CACHE_HOME=/tmp/xdg-cache \
./.venv/bin/python -m sphinx -b html docs docs/_build/html
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Python Version Not Supported

**Error**: `Python 3.7 is not supported`

**Solution**:
```bash
# Install Python 3.8+
# Using conda:
conda install python=3.11

# Or download from python.org
```

#### Issue 2: Permission Denied

**Error**: `[Errno 13] Permission denied`

**Solution**:
```bash
# Use user installation
pip install --user gas-swelling-model

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install gas-swelling-model
```

#### Issue 3: numpy/scipy Import Errors

**Error**: `ImportError: numpy.core.multiarray failed to import`

**Solution**:
```bash
# Uninstall and reinstall with correct versions
pip uninstall numpy scipy
pip install numpy>=1.20.0 scipy>=1.7.0
```

#### Issue 4: Build from Source Fails

**Error**: `error: Microsoft Visual C++ 14.0 is required`

**Solution (Windows)**:
```bash
# Install Microsoft C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or use pre-built wheels
pip install --only-binary :all: gas-swelling-model
```

#### Issue 5: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'gas_swelling'`

**Solution**:
```bash
# Verify installation
pip list | grep gas-swelling-model

# Reinstall if needed
pip install --force-reinstall gas-swelling-model

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Issue 6: Conda Environment Conflicts

**Error**: `UnsatisfiableError: The following specifications were found to be in conflict`

**Solution**:
```bash
# Create fresh environment
conda create -n gas-swelling --force
conda activate gas-swelling
conda install -c conda-forge numpy scipy matplotlib python=3.11
pip install gas-swelling-model
```

### Getting Help

If you encounter issues not covered here:

1. **Check the documentation**: [README.md](README.md)
2. **Search existing issues**: [GitHub Issues](https://github.com/yourusername/gas-swelling-model/issues)
3. **Create a new issue**: Include your OS, Python version, and full error message
4. **Discussion forum**: Ask questions in GitHub Discussions

### Debug Mode

Enable verbose output for debugging:

```bash
# Install with verbose output
pip install -v gas-swelling-model

# Run Python with debug info
python -v test_installation.py
```

---

## Next Steps

After successful installation, choose your learning path:

### Quickstart Options

**🚀 Streamlined Quickstart** (Recommended for new users)
- Read [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- Run [examples/quickstart_simple.py](examples/quickstart_simple.py) - Minimal working example

**📚 Comprehensive Tutorial** (For in-depth understanding)
- Run [examples/quickstart_tutorial.py](examples/quickstart_tutorial.py) - Detailed walkthrough
- Explore the `notebooks/` directory - Interactive Jupyter notebooks
- Consult the [Parameter Reference](docs/parameter_reference.md) - All parameters explained
- Review the [Repository Guide](docs/guides/repository_guide.md) - Structure, workflows, and entry points

---

## Uninstallation

To remove the package:

```bash
pip uninstall gas-swelling-model
```

To remove conda environment:

```bash
conda deactivate
conda env remove -n gas-swelling
```

---

## Installation Script Examples

### Automated Installation Script (Linux/macOS)

Save as `install.sh`:

```bash
#!/bin/bash
set -e

echo "Installing Gas Swelling Model..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
python3 -m venv gas-swelling-env
source gas-swelling-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install package
pip install gas-swelling-model[plotting]

# Verify installation
python -c "from gas_swelling import GasSwellingModel; print('✓ Installation successful!')"

echo "Installation complete. Activate with: source gas-swelling-env/bin/activate"
```

Run with:

```bash
chmod +x install.sh
./install.sh
```

### Windows PowerShell Installation Script

Save as `install.ps1`:

```powershell
Write-Host "Installing Gas Swelling Model..." -ForegroundColor Green

# Check Python version
$pythonVersion = python --version
Write-Host "Found $pythonVersion"

# Create virtual environment
python -m venv gas-swelling-env
.\gas-swelling-env\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install package
pip install gas-swelling-model[plotting]

# Verify installation
python -c "from gas_swelling import GasSwellingModel; print('Installation successful!')"

Write-Host "Installation complete. Activate with: .\gas-swelling-env\Scripts\Activate.ps1" -ForegroundColor Green
```

---

For more information, visit the [project repository](https://github.com/yourusername/gas-swelling-model).
