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

from difflib import SequenceMatcher
import inspect
import unittest

import sasoptpy as so
from sasoptpy.core.util import *


def match_ratio(a, b):
    seq = SequenceMatcher(None, a, b)
    return seq.ratio()


class TestUtil(unittest.TestCase):
    """
    Unit tests for core utility functions
    """

    @classmethod
    def setUpClass(cls):
        cls.x = x = so.Variable(name='x')
        cls.e = so.Expression(2 * x, name='e')
        cls.c = so.Constraint(4 * x**2 <= 10, name='c')
        cls.I = I = so.abstract.Set(name='I')
        cls.a = so.VariableGroup(I, name='a')
        cls.S1 = S1 = so.abstract.Set(name='S1')
        cls.S2 = S2 = so.abstract.Set(name='S2', settype='str')
        cls.S3 = S3 = so.abstract.Set(name='S3')
        cls.p = so.abstract.ParameterGroup(S1, name='p')
        cls.y = so.VariableGroup(S1, S2, S3, name='y')

    def test_expression(self):
        self.assertTrue(is_expression(TestUtil.e))
        self.assertTrue(is_expression(TestUtil.x))
        self.assertTrue(is_expression(TestUtil.c))

    def test_variable(self):
        self.assertFalse(is_variable(TestUtil.e))
        self.assertTrue(is_variable(TestUtil.x))
        self.assertFalse(is_variable(TestUtil.c))

    def test_constraint(self):
        self.assertTrue(is_constraint(TestUtil.c))
        self.assertFalse(is_constraint(TestUtil.e))

    def test_abstract(self):
        self.assertTrue(is_abstract(TestUtil.a))
        self.assertFalse(is_abstract(TestUtil.x))

    def test_itearor_expression(self):
        so.reset()
        S1 = TestUtil.S1
        S2 = TestUtil.S2
        S3 = TestUtil.S3
        p = TestUtil.p
        y = TestUtil.y
        c = so.ConstraintGroup((y[i, 'a', 1] + p[i] <= 5 for i in S1),
                               name='it_exp')
        self.assertEqual(so.to_definition(c),
                         "con it_exp {{o{i} in S1}} : "
                         "y[o{i}, 'a', 1] + p[o{i}] <= 5;".format(i=1))

    def test_safe_iterator_expression(self):
        S1 = TestUtil.S1
        S2 = ['a', 'b c', 'd']
        S3 = [1, 2, 3]
        y = TestUtil.y
        c = so.ConstraintGroup((y [i, j, k] <= 5 for i in S1 for j in S2 for k in S3),
                               name='safe_it_exp')
        self.assertEqual(so.to_definition(c), inspect.cleandoc(
            """
            con safe_it_exp_a_1 {o1 in S1} : y[o1, 'a', 1] <= 5;
            con safe_it_exp_a_2 {o1 in S1} : y[o1, 'a', 2] <= 5;
            con safe_it_exp_a_3 {o1 in S1} : y[o1, 'a', 3] <= 5;
            con safe_it_exp_b_c_1 {o1 in S1} : y[o1, 'b c', 1] <= 5;
            con safe_it_exp_b_c_2 {o1 in S1} : y[o1, 'b c', 2] <= 5;
            con safe_it_exp_b_c_3 {o1 in S1} : y[o1, 'b c', 3] <= 5;
            con safe_it_exp_d_1 {o1 in S1} : y[o1, 'd', 1] <= 5;
            con safe_it_exp_d_2 {o1 in S1} : y[o1, 'd', 2] <= 5;
            con safe_it_exp_d_3 {o1 in S1} : y[o1, 'd', 3] <= 5;
            """
        ))

    def test_evaluate(self):
        x = TestUtil.x
        import sasoptpy.abstract.math as sm
        import math

        e1 = x * x + x - 5
        e2 = 2 * x ** 2 - 10
        e3 = 2 / x + 5 + sm.sin(x)

        x.set_value(3)
        self.assertEqual(e1.get_value(), 7)
        self.assertEqual(e2.get_value(), 8)
        self.assertEqual(e3.get_value(), 17/3 + math.sin(3))
        x.set_value(4)
        self.assertEqual(e1.get_value(), 15)
        self.assertEqual(e2.get_value(), 22)
        self.assertEqual(e3.get_value(), 5.5 + math.sin(4))

        def division_by_zero():
            x.set_value(0)
            e3.get_value()
        self.assertRaises(ZeroDivisionError, division_by_zero)

        x.set_value(2)
        e4 = x ** (sm.sin(x)) - 1
        self.assertEqual(e4.get_value(), 2 ** math.sin(2) - 1)

    def test_expression_to_constraint(self):
        x = TestUtil.x
        e1 = 4 * x - 10

        c = so.core.util.expression_to_constraint(e1, 'E', [2, 10])
        self.assertTrue(so.to_definition(c), "con None : 12 <= 4 * x <= 20;")

        c = so.core.util.expression_to_constraint(x, 'G', 10)
        self.assertEqual(so.to_definition(c), "con None : x >= 10;")

        c = so.core.util.expression_to_constraint(2 * x, 'L', 3 * x)
        self.assertEqual(so.to_definition(c), "con None : - x <= 0;")

        c = so.core.util.expression_to_constraint(x, 'G', 0)
        self.assertEqual(so.to_definition(c), "con None : x >= 0;")

        import sasoptpy.abstract.math as sm
        c = so.core.util.expression_to_constraint(sm.sin(x), 'L', 1)
        self.assertEqual(so.to_definition(c), "con None : sin(x) <= 1;")

        y = TestUtil.y
        S1 = TestUtil.S1
        e1 = so.expr_sum(y[i, 'a', 1] for i in S1)
        c = so.core.util.expression_to_constraint(e1, 'G', 5)
        self.assertEqual(so.to_definition(c), "con None : sum {i in S1} "
                                              "(y[i, 'a', 1]) >= 5;")

    def tearDown(self):
        so.reset()

    @classmethod
    def tearDownClass(self):
        so.reset()


