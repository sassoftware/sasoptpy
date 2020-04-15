#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
SAS Optimization Interface for Python (sasoptpy)
************************************************

This file includes static methods and imports.

"""

from sasoptpy.libs import *
import sasoptpy.util

from sasoptpy.util import (
    quick_sum, expr_sum, reset, reset, reset_globals,
    flatten_frame, get_value_table,
    get_solution_table, dict_to_frame, exp_range,
    to_expression, to_definition, to_optmodel, is_linear,
    load_package_globals)

from sasoptpy.structure import (containable, class_containable, set_container)

from sasoptpy.core.expression import Expression
from sasoptpy.core import (Variable, VariableGroup, Constraint, ConstraintGroup,
                           Model, Objective, Auxiliary, Symbol)

from sasoptpy.abstract import (Set, InlineSet, Parameter, ImplicitVar,
                               ParameterGroup, SetIterator,
                               SetIteratorGroup, LiteralStatement)

load_package_globals()

import sasoptpy.config
from sasoptpy.config import Config, _load_default_config
_load_default_config()

statement_dictionary = dict()
container = None
from sasoptpy.util import load_function_containers
load_function_containers()
conditions = None
from sasoptpy.actions import register_actions
register_actions()


import sasoptpy.interface
sasoptpy.mediators = dict()
from sasoptpy.util import load_default_mediators
load_default_mediators()


from sasoptpy.session import Workspace

name = "sasoptpy"
from sasoptpy.version import __version__
