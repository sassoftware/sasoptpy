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
Unit tests for COFOR loops.
"""

import os
import sys
import unittest
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../..')))
from util import assert_equal_wo_temps

from sasoptpy.actions import for_loop, cofor_loop, fix, solve, put_item


class TestCoforLoop(unittest.TestCase):
    """
    Unit tests for concurrent for (COFOR) statements
    """

    def setUp(self):
        so.reset()

    def test_simple_example(self):
        with so.Workspace('w') as w:
            x = so.VariableGroup(6, name='x', lb=0)
            so.Objective(
                so.expr_sum(x[i] for i in range(6)), name='z', sense=so.MIN)
            a1 = so.Constraint(x[1] + x[2] + x[3] <= 4, name='a1')

            for i in cofor_loop(so.exp_range(3, 6)):
                fix(x[1], i)
                solve()
                put_item(i, x[1], so.Symbol('_solution_status_'), names=True)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x {{0,1,2,3,4,5}} >= 0;
               min z = x[0] + x[1] + x[2] + x[3] + x[4] + x[5];
               con a1 : x[1] + x[2] + x[3] <= 4;
               cofor {TEMP1 in 3..5} do;
                  fix x[1]=TEMP1;
                  solve;
                  put TEMP1= x[1]= _solution_status_=;
               end;
            quit;'''))
