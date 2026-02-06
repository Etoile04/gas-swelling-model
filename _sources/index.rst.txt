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

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api
   validation_guide
   sensitivity_analysis_guide

Overview
========

The Gas Swelling Model solves a system of 10 coupled ordinary differential
equations (ODEs) describing:

* Gas atom concentration in bulk matrix and at phase boundaries
* Cavity/bubble concentration and gas atoms per cavity
* Vacancy and interstitial concentrations
* Swelling rate calculations based on cavity volume fraction

Key Features
------------

* **State Vector**: 10 coupled ODEs for comprehensive physics modeling
* **Gas Pressure**: Ideal gas law or modified Van der Waals EOS
* **Cavity Radius**: Mechanical equilibrium between gas pressure and surface tension
* **Swelling Rate**: Total volume fraction occupied by cavities
* **Critical Radius**: Distinguishes gas-driven vs bias-driven void growth

Quick Start
-----------

To run a default simulation::

    from modelrk23 import GasSwellingModel
    from parameters import create_default_parameters

    # Create model with default parameters
    mat_params, sim_params = create_default_parameters()
    model = GasSwellingModel(mat_params, sim_params)

    # Solve for 100 days of irradiation
    import numpy as np
    sim_time = 100 * 24 * 3600  # 100 days in seconds
    time_points = np.linspace(0, sim_time, 1000)

    result = model.solve((0, sim_time), time_points)

    # Access results
    swelling = result['swelling']  # Volume fraction vs time
    radius = result['Rcb']  # Bubble radius vs time


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
