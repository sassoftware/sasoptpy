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


class TestConstraint(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.Constraint` objects
    """

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