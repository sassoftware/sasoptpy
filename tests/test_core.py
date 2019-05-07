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
        e = - so.quick_sum(y[i] * i for i in setI)
        self.assertEqual(str(e), '- sum(y[i_1] * i_1 for i_1 in setI)')

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


    def tearDown(self):
        so.reset()



class TestVariable(unittest.TestCase):

    def setUp(self):
        pass

    def test_repr(self):
        x = so.Variable(name='x')
        self.assertEqual(repr(x), "sasoptpy.Variable(name='x',  vartype='CONT')")

        y = so.Variable(name='y', lb=1, ub=10, init=3)
        self.assertEqual(repr(y), "sasoptpy.Variable(name='y', lb=1, ub=10, init=3,  vartype='CONT')")

        I = so.abstract.data.Set(name='I')
        z = so.VariableGroup(I, name='z')
        self.assertEqual(repr(z[0]), "sasoptpy.Variable(name='z', abstract=True, shadow=True,  vartype='CONT')")

    def test_string(self):
        x = so.VariableGroup([1,2,3], name='x')
        self.assertEqual(str(x[1]), "x[1]")

    def test_definition(self):
        x = so.Variable(name='x')
        self.assertEqual(x._defn(), "var x;")

        y = so.Variable(name='y', lb=1, ub=10, init=3, vartype=so.INT)
        self.assertEqual(y._defn(), "var y integer >= 1 <= 10 init 3;")

        z = so.Variable(name='z', ub=0.5, vartype=so.BIN)
        self.assertEqual(z._defn(), "var z binary <= 0.5;")

    def tearDown(self):
        so.reset()


class TestConstraint(unittest.TestCase):

    def setUp(self):
        pass

    def test_constructor(self):
        x = so.Variable(name='x')
        c2 = 3 * x + x ** 2 >= 10
        c3 = so.Constraint(exp=c2, name='c3')
        self.assertEqual(str(c3), "3 * x + (x) ** (2) >=  10")

        def no_direction():
            c4 = so.Constraint(2 * x, name='c4')
        self.assertRaises(AttributeError, no_direction)

        c5 = so.Constraint(c3, name='c5')
        self.assertEqual(str(c5), "3 * x + (x) ** (2) >=  10")

    def test_update_var_coef(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')
        c1 = so.Constraint(2 * x + 3 * y <= 20, name='c1')

        c1.update_var_coef(x, 5)
        self.assertEqual(str(c1), '5 * x + 3 * y <=  20')

        z = so.Variable(name='z')
        c1.update_var_coef(z, 10)
        self.assertEqual(str(c1), '5 * x + 3 * y + 10 * z <=  20')

    def test_change_direction(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')
        c1 = so.Constraint(2 * x + 3 * y <= 20, name='c1')

        c1.set_direction('G')
        self.assertEqual(str(c1), '2 * x + 3 * y >=  20')

        def unknown_direction():
            c1.set_direction('X')
        self.assertRaises(ValueError, unknown_direction)

    def test_get_value(self):
        x = so.Variable(name='x')
        y = so.Variable(name='y')
        c1 = so.Constraint(2 * x + 3 * y <= 20, name='c1')

        x.set_value(4)
        y.set_value(3)

        self.assertEqual(c1.get_value(), 17)
        self.assertEqual(c1.get_value(rhs=True), -3)

    def test_definition(self):
        x = so.Variable(name='x')
        c1 = so.Constraint(3 * x == [5, 10], name='c1')
        self.assertEqual(c1._defn(), 'con c1 : 5 <= 3 * x <= 10;')

        c2 = so.Constraint(5 * x == 15, name='c2')
        self.assertEqual(c2._defn(), 'con c2 : 5 * x = 15;')

        c3 = so.Constraint(10 * x >= 5, name='c3')
        self.assertEqual(c3._defn(), 'con c3 : 10 * x >= 5;')

        def unknown_direction():
            c3._direction = 'X'
            c3d = c3._defn()
        self.assertRaises(ValueError, unknown_direction)

    def test_str(self):
        x = so.Variable(name='x')
        c1 = 2 * x <= 5
        self.assertEqual(str(c1), "2 * x <=  5")

        c2 = 2 * x >= 5
        self.assertEqual(str(c2), "2 * x >=  5")

        c3 = 2 * x == 5
        self.assertEqual(str(c3), "2 * x ==  5")

        c4 = 2 * x == [5, 10]
        self.assertEqual(str(c4), "2 * x ==  [5, 10]")

        def unknown_direction():
            c4._direction = 'X'
            c4s = str(c4)
        self.assertRaises(ValueError, unknown_direction)

    def test_repr(self):
        x = so.Variable(name='x')

        c1 = so.Constraint(2 * x <= 5, name='c1')
        self.assertEqual(repr(c1), "sasoptpy.Constraint(2 * x <=  5, name='c1')")

        c2 = 2 * x <= 5
        self.assertEqual(repr(c2), "sasoptpy.Constraint(2 * x <=  5, name=None)")

    def tearDown(self):
        so.reset()


if __name__ == '__main__':
    unittest.main()

