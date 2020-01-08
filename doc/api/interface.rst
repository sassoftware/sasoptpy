
Interface
=========

.. currentmodule:: sasoptpy.interface

CAS (Viya)
~~~~~~~~~~

.. autosummary::
   :toctree: generated/
   :template: autosummary/class_without_autosummary.rst

   CASMediator

Model
-----

.. autosummary::
   :toctree: generated/

   CASMediator.solve
   CASMediator.tune
   CASMediator.tune_problem
   CASMediator.solve_with_mps
   CASMediator.solve_with_optmodel
   CASMediator.parse_cas_solution
   CASMediator.parse_cas_table
   CASMediator.set_variable_values
   CASMediator.set_constraint_values
   CASMediator.set_model_objective_value
   CASMediator.set_variable_init_values
   CASMediator.upload_user_blocks
   CASMediator.upload_model


Workspace
---------

.. autosummary::
   :toctree: generated/

   CASMediator.submit
   CASMediator.submit_optmodel_code
   CASMediator.parse_cas_workspace_response
   CASMediator.set_workspace_variable_values


SAS
~~~

.. autosummary::
   :toctree: generated/
   :template: autosummary/class_without_autosummary.rst

   SASMediator

Model
-----

.. autosummary::
   :toctree: generated/

   SASMediator.solve
   SASMediator.solve_with_mps
   SASMediator.solve_with_optmodel
   SASMediator.parse_sas_mps_solution
   SASMediator.parse_sas_solution
   SASMediator.parse_sas_table
   SASMediator.convert_to_original
   SASMediator.perform_postsolve_operations


Workspace
---------

.. autosummary::
   :toctree: generated/

   SASMediator.submit
   SASMediator.submit_optmodel_code
   SASMediator.parse_sas_workspace_response
   SASMediator.set_workspace_variable_values
