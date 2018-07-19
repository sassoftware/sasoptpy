
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

   Model.set_session
   Model.add_constraint
   Model.add_constraints
   Model.add_variable
   Model.add_variables
   Model.add_implicit_variable
   Model.add_set
   Model.add_parameter
   Model.add_statement
   Model.set_objective
   Model.set_coef

   Model.drop_constraint
   Model.drop_constraints
   Model.drop_variable
   Model.drop_variables

   Model.get_constraint
   Model.get_constraints
   Model.get_variable
   Model.get_variables
   Model.get_objective
   Model.get_variable_coef

   Model.read_data
   Model.read_table

   Model.include

Solver calls
~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Model.solve
   Model.solve_on_cas
   Model.solve_on_mva
   Model.get_solution
   Model.get_variable_value
   Model.get_objective_value
   Model.get_solution_summary
   Model.get_problem_summary
   Model.print_solution
   Model.upload_user_blocks

Export
~~~~~~

.. autosummary::
   :toctree: generated/

   Model.to_frame
   Model.to_optmodel

Internal functions
~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated/

   Model.upload_model
   Model.test_session
   Model._defn
   Model._expr
   Model._is_linear
   Model.__repr__
   Model.__str__

