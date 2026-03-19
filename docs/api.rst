API Reference
=============

This page contains the API reference documentation for the Gas Swelling Model.

.. toctree::
   :maxdepth: 4

Model Classes
-------------

Main Model
^^^^^^^^^^

.. autoclass:: gas_swelling.models.modelrk23.GasSwellingModel
   :members:
   :undoc-members:
   :show-inheritance:

Refactored Model
^^^^^^^^^^^^^^^^

.. autoclass:: gas_swelling.models.refactored_model.RefactoredGasSwellingModel
   :members:
   :undoc-members:
   :show-inheritance:

Radial Model
^^^^^^^^^^^^

``RadialGasSwellingModel`` now supports two execution modes through
``params['radial_solver_mode']``:

- ``'decoupled'``: default fast path that advances each radial node with the
  validated 0D backend and reassembles the radial profiles.
- ``'coupled'``: original fully coupled radial ODE solve with explicit
  inter-node transport terms.

.. autoclass:: gas_swelling.models.radial_model.RadialGasSwellingModel
   :members:
   :undoc-members:
   :show-inheritance:

Parameter Classes
-----------------

.. autoclass:: gas_swelling.params.parameters.MaterialParameters
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: gas_swelling.params.parameters.SimulationParameters
   :members:
   :undoc-members:
   :show-inheritance:

Parameter Creation Functions
------------------------------

.. autofunction:: gas_swelling.params.parameters.create_default_parameters

Solvers
-------

.. autoclass:: gas_swelling.solvers.rk23_solver.RK23Solver
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: gas_swelling.solvers.euler_solver.EulerSolver
   :members:
   :undoc-members:
   :show-inheritance:

Analysis
--------

.. autoclass:: gas_swelling.analysis.sensitivity.SensitivityAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:

Validation
----------

.. automodule:: gas_swelling.validation.metrics
   :members:

.. automodule:: gas_swelling.validation.datasets
   :members:
