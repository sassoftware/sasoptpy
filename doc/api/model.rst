
Model
=====

.. currentmodule:: sasoptpy

Constructor
~~~~~~~~~~~

.. autosummary::
   :toctree: generated/
   :template: autosummary/class_without_autosummary.rst

   Model

Components
~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Model.get_name

   Model.set_session
   Model.get_session
   Model.get_session_type

   Model.set_objective
   Model.append_objective
   Model.get_objective
   Model.get_all_objectives

   Model.add_variable
   Model.add_variables
   Model.add_implicit_variable
   Model.get_variable
   Model.get_variables
   Model.get_grouped_variables
   Model.get_implicit_variables
   Model.get_variable_coef
   Model.drop_variable
   Model.drop_variables

   Model.add_constraint
   Model.add_constraints
   Model.get_constraint
   Model.get_constraints
   Model.get_grouped_constraints
   Model.drop_constraint
   Model.drop_constraints

   Model.add_set
   Model.add_parameter
   Model.add_statement
   Model.get_sets
   Model.get_parameters
   Model.get_statements

   Model.include

Solver calls
~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Model.solve
   Model.tune_parameters

   Model.get_solution
   Model.get_variable_value
   Model.get_objective_value
   Model.get_solution_summary
   Model.get_problem_summary
   Model.get_tuner_results

   Model.print_solution
   Model.clear_solution

Export
~~~~~~

.. autosummary::
   :toctree: generated/

   Model.to_mps
   Model.to_optmodel


Internal functions
~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Model._is_linear

Deprecated
~~~~~~~~~~

.. deprecated:: 1.0.0

Following method(s) are deprecated and will be removed in future minor updates.

.. autosummary::
   :toctree: generated/

   Model.to_frame
