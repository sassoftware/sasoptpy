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
Unit test for drop statements.
"""

import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../..')))
from util import assert_equal_wo_temps

class TestDropRestore(unittest.TestCase):
    """
    Unit tests for DROP and RESTORE statements
    """

    def setUp(self):
        so.reset()

    def test_regular_drop(self):

        import sasoptpy.abstract.math as sm
        from sasoptpy.actions import solve, drop

        with so.Workspace('w') as w:
            x = so.Variable(name='x', lb=1)
            y = so.Variable(name='y', lb=0)
            c = so.Constraint(sm.sqrt(x) >= 5, name='c')
            o = so.Objective(x + y, sense=so.MIN, name='obj')
            s = solve()
            drop(c)
            o2 = so.Objective(x, sense=so.MIN, name='obj2')
            s2 = solve()

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x >= 1;
               var y >= 0;
               con c : sqrt(x) >= 5;
               min obj = x + y;
               solve;
               drop c;
               min obj2 = x;
               solve;
            quit;'''))

    def test_multiple_and_mixed_drop(self):

        from sasoptpy.actions import solve, drop
        with so.Workspace('w') as w:
            x = so.Variable(name='x')
            o = so.Objective(x**2, sense=so.MIN, name='obj')
            c1 = so.Constraint(x >= 5, name='c1')
            c2 = so.ConstraintGroup((x**i >= 1+i for i in range(3)), name='c2')
            c3 = so.ConstraintGroup((x >= i for i in range(2)), name='c3')
            S = so.Set(name='S', value=range(1, 5))
            y = so.VariableGroup(S, name='y')
            d = so.ConstraintGroup((y[i] >= i+j for i in S for j in range(2)),
                                   name='d')
            solve()
            drop(c1, c2[1], c3)
            solve()
            drop(d[2,0])
            solve()
            drop(d)
            solve()

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               min obj = (x) ^ (2);
               con c1 : x >= 5;
               con c2_0 : (x) ^ (0) >= 1;
               con c2_1 : (x) ^ (1) >= 2;
               con c2_2 : (x) ^ (2) >= 3;
               con c3_0 : x >= 0;
               con c3_1 : x >= 1;
               set S = 1..4;
               var y {{S}};
               con d_0 {TEMP1 in S} : y[TEMP1] - TEMP1 >= 0;
               con d_1 {TEMP1 in S} : y[TEMP1] - TEMP1 >= 1;
               solve;
               drop c1 c2_1 c3_0 c3_1;
               solve;
               drop d_0[2];
               solve;
               drop {TEMP1 in S} d_0[TEMP1] {TEMP1 in S} d_1[TEMP1];
               solve;
            quit;'''))

    def test_drop_in_model(self):

        m = so.Model(name='m')
        x = m.add_variables(3, name='x')
        c = m.add_constraints((x[i] <= i**2 for i in range(3)), name='c')
        self.assertEqual(so.to_optmodel(m), cleandoc('''
            proc optmodel;
               min m_obj = 0;
               var x {{0,1,2}};
               con c_0 : x[0] <= 0;
               con c_1 : x[1] <= 1;
               con c_2 : x[2] <= 4;
               solve;
            quit;'''))
        m.drop_constraint(c[0])
        self.assertEqual(so.to_optmodel(m), cleandoc('''
            proc optmodel;
               min m_obj = 0;
               var x {{0,1,2}};
               con c_0 : x[0] <= 0;
               con c_1 : x[1] <= 1;
               con c_2 : x[2] <= 4;
               drop c_0;
               solve;
            quit;'''))

    def test_simple_drop_restore(self):
        from sasoptpy.actions import drop, restore, solve, set_objective
        with so.Workspace('w') as w:
            x = so.Variable(name='x', lb=-1)
            set_objective(x**3, name='xcube', sense=so.minimize)
            c = so.Constraint(x >= 1, name='xbound')
            solve()
            drop(c)
            solve()
            restore(c)
            solve()

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x >= -1;
               MIN xcube = (x) ^ (3);
               con xbound : x >= 1;
               solve;
               drop xbound;
               solve;
               restore xbound;
               solve;
            quit;'''))
