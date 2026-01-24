API Reference
=============

This page contains the API reference documentation for the Gas Swelling Model.

.. toctree::
   :maxdepth: 4

Model Classes
-------------

Main Model
^^^^^^^^^^

.. autoclass:: modelrk23.GasSwellingModel
   :members:
   :undoc-members:
   :show-inheritance:

Euler Method Model
^^^^^^^^^^^^^^^^^^

.. autoclass:: modelrk23.EulerGasSwellingModel
   :members:
   :undoc-members:
   :show-inheritance:

Parameter Classes
-----------------

.. autoclass:: parameters.MaterialParameters
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: parameters.SimulationParameters
   :members:
   :undoc-members:
   :show-inheritance:

Parameter Creation Functions
------------------------------

.. autofunction:: parameters.create_default_parameters

Test and Analysis Classes
--------------------------

Study Classes
^^^^^^^^^^^^^

.. autoclass:: test4_run_rk23.UraniumSwellingStudy
   :members:
   :undoc-members:
   :show-inheritance:

Test Runner Functions
^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: test4_run_rk23.run_test4
.. autofunction:: test4_run_rk23.run_temperature_sweep
.. autofunction:: test4_run_rk23.run_comparison_study

Analysis Functions
^^^^^^^^^^^^^^^^^^

.. autofunction:: test4_run_rk23.plot_swelling_vs_temperature
.. autofunction:: test4_run_rk23.plot_bubble_radius_evolution
.. autofunction:: test4_run_rk23.plot_gas_release_fraction
.. autofunction:: test4_run_rk23.compare_with_experimental_data
