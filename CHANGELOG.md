## [0.3.0] - 2026-03-19

### ✨ New Features

#### 1D Radial Model
- **RadialGasSwellingModel**: New 1D spatial discretization model for capturing radial variations across fuel pellet
- **Dual solver modes**: `decoupled` (default, fast node-wise solve) and `coupled` (full ODE system)
- **Radial mesh**: Configurable number of nodes with proper boundary conditions
- **Temperature profiles**: Support for radially-varying temperature and fission rate

#### Reduced-Order Models
- **QSSAGasSwellingModel**: Quasi-steady-state approximation for faster simulations
- **HybridQSSAGasSwellingModel**: Hybrid approach balancing speed and accuracy
- **Model backend selection**: New `model_backend` parameter ('full', 'qssa', 'hybrid_qssa')

#### Testing Infrastructure
- **Safe test runner**: `scripts/test_safe.py` with timeout handling and process tree cleanup
- **Robust CI**: Improved GitHub Actions workflows with proper error handling

### 📚 Documentation

#### New Tutorials
- **30-Minute Quickstart**: Comprehensive hands-on tutorial
- **Rate Theory Fundamentals**: Plain-language introduction to core concepts
- **Model Equations Explained**: Paper-level variable mapping

#### New Guides
- **Interpreting Results**: Complete guide to all 17 output variables
- **Plot Gallery**: 16+ ready-to-use plotting code snippets
- **Troubleshooting**: Solutions for 31+ common issues
- **Repository Guide**: Quick navigation for new users

#### Learning Resources
- **Learning Paths**: Structured curriculum for different user types
- **Jupyter Notebooks**: 6 interactive notebooks for exploration
  - Basic Simulation Walkthrough
  - Parameter Sweep Studies
  - Gas Distribution Analysis
  - Experimental Data Comparison
  - Custom Material Composition
  - Advanced Analysis Techniques

### 🔧 Improvements
- **17-state ODE system**: Full implementation tracking gas, cavities, defects, and sink strengths
- **CLAUDE.md**: Updated with accurate commands and architecture details
- **Build artifacts**: Removed `docs/_build/` from git tracking
- **Code organization**: Cleaner module structure with physics, ode, solvers separation

### 🗑️ Removed
- Deprecated CLI module
- Temporary verification scripts
- Obsolete test files

---

## [1.0.0] - 2026-01-24

### ✨ New Features
- **Parallel Processing**: Implemented multiprocessing pool wrapper and joblib parallel backend for concurrent simulation execution with configurable n_jobs parameter
- **Export Formats**: Added CSV export with proper formatting and metadata, plus NetCDF export for complex multi-dimensional datasets
- **Parameter Sampling Methods**: Implemented three sampling strategies - grid-based (cartesian product), Latin Hypercube Sampling (LHS), and sparse grid sampling for advanced use cases
- **Progress Tracking**: Added tqdm integration with time estimation for long-running simulations
- **Parameter Validation**: Added configuration parameter validation with helpful error messages

### 📚 Documentation
- **Installation Guide**: Created comprehensive INSTALL.md with setup instructions
- **Quick Start Tutorial**: Added beginner-friendly tutorial script (examples/quickstart_tutorial.py)
- **Parameter Reference**: Created detailed parameter documentation (docs/parameter_reference.md)
- **Examples Guide**: Created examples/README.md with overview of all available examples
- **Jupyter Notebook**: Added interactive Temperature_Sweep_Example.ipynb
- **API Documentation**: Added comprehensive docstrings and usage examples to public APIs
- **Theory Documentation**: Completed documentation of defect kinetics equations
- **Completion Summary**: Added completion summary documentation

### 🔧 Improvements
- **Result Aggregation**: Implemented result storage system converting results to pandas DataFrame
- **Example Usage**: Created demonstration script showing multi-parameter sweep with caching and parallelization
- **End-to-end Verification**: Completed full multi-parameter sweep validation

### 🐛 Bug Fixes
- **Documentation Links**: Restored correct README.md with proper documentation links after rebase

### 📝 Project Management
- Updated plan and progress files to completed status
- Documented subtask completion in build-progress.txt