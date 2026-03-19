.. Gas Swelling Model documentation master file, created by sphinx-quickstart.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gas Swelling Model's documentation!
==============================================

This is the scientific documentation for the Gas Swelling Model, a computational
tool for simulating fission gas bubble evolution and void swelling behavior in
irradiated metallic fuels (U-Zr and U-Pu-Zr alloys).

The model implements rate theory equations based on the theoretical framework
from "Kinetics of fission-gas-bubble-nucleated void swelling of the alpha-uranium
phase of irradiated U-Zr and U-Pu-Zr fuel."

If you are new to the repository, start with the repository guide before diving
into the deeper tutorials. It is the best entry point for understanding where
the package code lives, which example to run first, and which module to read
for each feature area.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api
   1d_radial_model
   tutorials/30minute_quickstart
   guides/repository_guide
   tutorials/rate_theory_fundamentals
   tutorials/model_equations_explained
   learning_paths
   guides/interpreting_results
   guides/plot_gallery
   guides/troubleshooting
   parameter_reference
   sensitivity_analysis_guide
   validation_guide
   adaptive_stepping

Overview
========

The Gas Swelling Model package combines the original rate-theory formulation
with the current packaged implementation, including the main 0D model, reduced-
order backends, and the 1D radial model.

The repository covers:

* Gas atom concentration in bulk matrix and at phase boundaries
* Cavity/bubble concentration and gas atoms per cavity
* Vacancy and interstitial behavior
* Swelling calculations and post-processing
* Reduced-order variants and radial workflows

Key Features
------------

* **Package-first API**: main imports come from ``gas_swelling``
* **Model Variants**: ``full``, ``qssa``, and ``hybrid_qssa`` backends
* **Radial Support**: 1D radial model with default ``decoupled`` execution mode
* **Validation & Analysis**: experimental datasets, plotting, and sensitivity analysis
* **Testing**: a large local pytest suite covering physics, numerics, plotting, and docs

Quick Start
-----------

To run a default simulation::

    from gas_swelling import GasSwellingModel, create_default_parameters

    # Create model with default parameters
    params = create_default_parameters()
    model = GasSwellingModel(params)

    # Solve with the packaged interface
    result = model.solve()

    # Access results
    swelling = result['swelling']
    radius = result['Rcb']


Mathematical Framework
======================

The model implements the following key equations:

**Gas Transport** (Eqs. 1-8)
    Diffusion, nucleation, and cavity growth mechanisms

**Defect Kinetics** (Eqs. 17-20)
    Vacancy/interstitial production, recombination, and sink annihilation

**Cavity Growth** (Eq. 14)
    Bias-driven vacancy influx vs thermal emission

**Gas Release** (Eqs. 9-12)
    Interconnectivity threshold and release fraction

**Swelling Calculation**

The swelling rate is calculated as the volume fraction occupied by cavities:

.. math::

    V_{bubble} = \frac{4}{3}\pi R^3 \times C_c

where :math:`R` is the cavity radius and :math:`C_c` is the cavity concentration.

For detailed mathematical derivations and equation references, see the
:doc:`api` documentation.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
