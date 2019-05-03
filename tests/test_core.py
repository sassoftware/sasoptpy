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

import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import unittest
import sasoptpy as so


class TestExpression(unittest.TestCase):

    def setUp(self):
        pass

    def test_constructor(self):
        def wrong_expression_type():
            e = so.Expression(exp='abc')
        self.assertRaises(TypeError, wrong_expression_type)

    def test_get_value(self):
        import sasoptpy.abstract.math as sm
        x = so.Variable(name='x')
        x.set_value(7)
        e = sm.sin(2)**sm.sqrt(9) + sm.min(x, 5, 10)
        v = e.get_value()
        self.assertAlmostEqual(v, 5.751826, places=5)

    def test_dual(self):
        x = so.Variable(name='x')
        x._dual = 0
        self.assertEqual(x.get_dual(), 0)

    def test_rename(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')
        e = so.Expression(x + 2*x*y, name='nonlinear_exp')
        new_name = e.set_name()
        self.assertEqual(new_name, 'nonlinear_exp')
        f = so.Expression(2*x + y)
        new_name = f.set_name()
        self.assertIsNotNone(new_name)
        new_name = e.set_name('e')
        self.assertEqual(new_name, 'e')
        get_name = e.get_name()
        self.assertEqual(get_name, 'e')

    def test_expr_string(self):
        import sasoptpy.abstract.math as sm
        x = so.Variable(name='x')
        y = so.Variable(name='y')
        e = sm.abs(x) + 2 *y + sm.min(x, y)
        e_exp = e._expr()
        self.assertEqual(e_exp, 'abs(x) + 2 * y + min(x , y)')

        setI = so.abstract.Set(name='I')
        z = so.VariableGroup(setI, name='z')
        g = so.quick_sum(z[i] for i in setI) + 5
        g_exp = g._expr()
        self.assertEqual(g_exp, 'sum {i_1 in I}(z[i_1]) + 5')

    def test_repr(self):
        x = so.Variable(name='x')
        e = x ** 2 + 3 * x - 5
        exp_repr = repr(e)
        self.assertEqual(exp_repr, 'sasoptpy.Expression(exp = (x) ** (2) + 3 * x - 5, name=None)')
        e.set_permanent('e')
        exp_repr = repr(e)
        self.assertEqual(exp_repr, 'sasoptpy.Expression(exp = (x) ** (2) + 3 * x - 5, name=\'e\')')

    def tearDown(self):
        so.reset()


if __name__ == '__main__':
    unittest.main()

