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


class TestExpression(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.Expression` objects
    """

    def setUp(self):
        pass

    def test_constructor(self):
        def unknown_expression_type():
            e = so.Expression(exp='abc')
        self.assertRaises(TypeError, unknown_expression_type)

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
        new_name = e.set_name('new_name')
        self.assertEqual(new_name, 'new_name')
        f = so.Expression(2*x + y)
        new_name = f.set_name('f')
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
        g = so.expr_sum(z[i] for i in setI) + 5
        g_exp = g._expr()
        self.assertEqual(g_exp, 'sum {i in I} (z[i]) + 5')

    def test_repr(self):
        x = so.Variable(name='x')
        e = x ** 2 + 3 * x - 5
        exp_repr = repr(e)
        self.assertEqual(exp_repr, 'sasoptpy.Expression(exp = (x) ** (2) + 3 * x - 5, name=None)')
        e.set_permanent()
        e.set_name('e')
        exp_repr = repr(e)
        self.assertEqual(exp_repr, 'sasoptpy.Expression(exp = (x) ** (2) + 3 * x - 5, name=\'e\')')

    def test_string(self):
        x = so.Variable(name='x')
        e = 2 * x + 3 ** x + 10
        self.assertEqual(str(e), '2 * x + (3) ** (x) + 10')

        import sasoptpy.abstract.math as sm
        e = sm.abs(x) + sm.min(x, 2, sm.sqrt(x))
        self.assertEqual(str(e), 'abs(x) + min(x , 2, sqrt(x))')

        from sasoptpy.abstract import Set
        setI = Set(name='setI')
        y = so.VariableGroup(setI, name='y')
        e = - so.expr_sum(y[i] * i for i in setI)
        self.assertEqual(str(e), '- (sum(y[i] * i for i in setI))')

        e = 2 * x ** y[0]
        self.assertEqual(str(e), '2 * ((x) ** (y[0]))')

    def test_addition(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')

        exp1 = so.Expression(x+y, name='exp1')
        exp2 = 2 * x - y
        exp3 = exp1 + exp2
        self.assertEqual(str(exp3), '3 * x')

        import sasoptpy.abstract.math as sm
        exp4 = sm.min(x, y, sm.sqrt(x * y)) + 4
        self.assertEqual(str(exp4), 'min(x , y, sqrt(x * y)) + 4')

        def unknown_addition_type():
            exp5 = x + y + [3, 4]
        self.assertRaises(TypeError, unknown_addition_type)

    def test_multiplication(self):
        K = [1, 2, 'a']
        L = so.abstract.Set(name='L')

        x = so.Variable(name='x')
        y = so.Variable(name='y')
        z = so.VariableGroup(K, name='z')
        u = so.VariableGroup(L, name='u')

        exp1 = (x + y + 5) * (2 * x - 4 * y - 10)
        self.assertEqual(str(exp1), '2 * x * x - 2 * x * y - 4 * y * y - 30 * y - 50')

        exp2 = (x + y + 5) * 0 + x
        self.assertEqual(str(exp2), 'x')

        def unknown_multiplication_type():
            exp3 = x * ['a']
        self.assertRaises(TypeError, unknown_multiplication_type)

    def test_division(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')

        exp1 = x/2
        self.assertEqual(str(exp1), '0.5 * x')

        exp2 = x/y
        self.assertEqual(str(exp2), '(x) / (y)')

        import sasoptpy.abstract.math as sm
        exp3 = x**2 / (3*y) + 0 / sm.abs(x)
        self.assertEqual(str(exp3), '((x) ** (2)) / (3 * y) + (0) / (abs(x))')

        def division_by_zero():
            exp4 = x / 0
        self.assertWarns(RuntimeWarning, division_by_zero)

        def unknown_division_type():
           exp5 = x / 'a'
        self.assertRaises(TypeError, unknown_division_type)

    def test_power(self):
        x = so.Variable(name='x')
        e1 = x ** 2 + x ** 3
        self.assertEqual(so.to_expression(e1),
                         '(x) ^ (2) + (x) ^ (3)')

    def test_truediv(self):
        x = so.Variable(name='x')
        e1 = x / (2 + x) + x / (3 + x)
        self.assertEqual(so.to_expression(e1),
                         '(x) / (x + 2) + (x) / (x + 3)')

    def test_is_linear(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')

        exp1 = x
        self.assertTrue(exp1._is_linear())

        exp2 = 2 * x + 3 * y
        self.assertTrue(exp2._is_linear())

        exp3 = 5 * x * y
        self.assertFalse(exp3._is_linear())

        import sasoptpy.abstract.math as sm
        exp4 = sm.max(x, y) + 5
        self.assertFalse(exp4._is_linear())

        exp5 = x ** 2
        self.assertFalse(exp5._is_linear())

    def test_relational(self):
        x = so.Variable(name='x')
        e = 2 * x + 5

        f = e <= 2
        self.assertTrue(type(f) == so.Constraint)

        f = e >= 0
        self.assertTrue(type(f) == so.Constraint)

        f = e == 5
        self.assertTrue(type(f) == so.Constraint)

        f = 2 >= e
        self.assertTrue(type(f) == so.Constraint)

        f = 0 <= e
        self.assertTrue(type(f) == so.Constraint)

    def test_get_constant(self):
        x = so.Variable(name='x')

        e = 2 * x
        self.assertEqual(e.get_constant(), 0)

        e = 2 * x + 5
        self.assertEqual(e.get_constant(), 5)

    def tearDown(self):
        so.reset()
