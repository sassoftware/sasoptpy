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
Unit tests for core classes.
"""

import unittest
import sasoptpy as so
from sasoptpy._libs import pd


class TestConstraintGroup(unittest.TestCase):

    def setUp(self):
        pass

    def test_constructor(self):
        I = [1, 2, 3]
        x = so.VariableGroup(I, name='x')
        cg = so.ConstraintGroup((x[i] <= 3 for i in I), name='bound_con')
        self.assertEqual(
            repr(cg),
            "sasoptpy.ConstraintGroup([x[1] <=  3, x[2] <=  3, x[3] <=  3], name='bound_con')")

    def test_name(self):
        x = so.VariableGroup(2, name='x')
        c1 = so.ConstraintGroup((2 * x[i] <= 5 for i in range(2)), name='ubcon')
        self.assertEqual(c1.get_name(), 'ubcon')

    def test_recursive_generation(self):
        G1 = [1, 2]
        G2 = ['a', 'b']
        x = so.VariableGroup(G1, G2, name='x')
        cg = so.ConstraintGroup((x[i, j] >= 1 for i in G1 for j in G2),
                                name='two_indices')
        self.assertEqual(
            repr(cg),
            "sasoptpy.ConstraintGroup([x[1, a] >=  1, x[1, b] >=  1, x[2, a] >=  1, x[2, b] >=  1], name='two_indices')"
        )

        c1 = x[1, 'a'] >= 4
        c2 = x[1, 'b'] <= 6
        cg2 = so.ConstraintGroup([c1, c2], name='list_cons')
        self.assertEqual(
            repr(cg2),
            "sasoptpy.ConstraintGroup([x[1, a] >=  4, x[1, b] <=  6], name='list_cons')"
        )

        def test_type_error():
            cg3 = so.ConstraintGroup({'a': x[1, 'a'] <= 5}, name='errcon')
        self.assertRaises(TypeError, test_type_error)

    def test_expression_mode(self):
        x = so.VariableGroup(2, name='x')
        cg = so.ConstraintGroup((x[i] >= 1 for i in range(2)), name='lbcon')
        exps = cg.get_expressions()
        x_i = exps.loc[0, 'lbcon'].values[0]
        self.assertEqual(x_i.get_value(), 0)

    def test_get_item(self):
        x = so.VariableGroup(2, name='x')
        cg1 = so.ConstraintGroup((x[i] >= 3 for i in range(2)), name='c1')
        self.assertEqual(type(cg1[0]), so.Constraint)

        so.reset()
        I = so.abstract.Set(name='I')
        y = so.VariableGroup(I, name='y')
        cg2 = so.ConstraintGroup((y[i] >= 3 for i in I), name='c2')
        for i in I:
            self.assertEqual(cg2[i]._get_constraint_expr(), "y[o4] >= 3")
        self.assertEqual(cg2[0], None)

    def test_iter(self):
        x = so.VariableGroup(3, name='x')
        cg = so.ConstraintGroup((x[i] >= i for i in range(3)), name='cg')
        for i, con in enumerate(cg):
            self.assertEqual(str(con), "x[{}] >=  {}".format(i, i))

    def test_definition(self):
        x = so.VariableGroup(3, name='x')
        cg = so.ConstraintGroup((x[i] >= 1 for i in range(3)), name='cg')
        self.assertEqual(
            cg._defn(),
            "con cg_0 : x[0] >= 1;\ncon cg_1 : x[1] >= 1;\ncon cg_2 : x[2] >= 1;\n")

    def test_str(self):
        x = so.VariableGroup(3, name='x')
        cg = so.ConstraintGroup((x[i] <= i-1 for i in range(3)), name='cg')
        cg_str = str(cg)
        self.assertEqual(
            cg_str,
            """Constraint Group (cg) [
  [0: x[0] <=  -1]
  [1: x[1] <=  0]
  [2: x[2] <=  1]
]"""
        )

    def tearDown(self):
        so.reset()
