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
SAS Viya Optimization Modeling for Python (sasoptpy)
****************************************************

This file includes static methods and imports.

"""

# Package config

# Imports
from sasoptpy._libs import *
import sasoptpy.util
sasoptpy.util.load_package_globals()

from sasoptpy.util import (
    quick_sum, reset, reset, reset_globals, read_frame, flatten_frame,
    get_solution_table, dict_to_frame, read_table, exp_range)

from sasoptpy.structure import (inside_container, containable)

from sasoptpy.core import Expression
from sasoptpy.core import (Variable, VariableGroup, Constraint, ConstraintGroup, Model)

import sasoptpy.abstract
from sasoptpy.abstract import (Parameter, ImplicitVar)

import sasoptpy.config
sasoptpy.config._load_default_config()
sasoptpy.util.load_function_containers()


#from sasoptpy.utils import load_package_globals
#load_package_globals()

#from sasoptpy.utils import *
#from sasoptpy.model import *
#from sasoptpy.components import *
#from sasoptpy.data import *

# Optional items
#  sasoptpy.math
#  sasoptpy.api

name = "sasoptpy"
__version__ = '1.0.0.dev0'
