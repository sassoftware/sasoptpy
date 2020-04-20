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
Unit tests for math functions.
"""

import unittest
import warnings
from inspect import cleandoc

import sasoptpy as so
import sasoptpy.abstract.math as sm
import math


class TestAbstractMath(unittest.TestCase):
    """
    Unit tests for mathematical functions
    """

    def setUp(self):
        so.reset()

    def test_warn(self):
        def regular_import():
            import sasoptpy.math
        self.assertWarns(DeprecationWarning, regular_import)

    def test_functions(self):
        x = so.Variable(name='x')
        x.set_value(2)

        def check_value(expression, value, exp_str):
            self.assertEqual(expression.get_value(), value)
            self.assertEqual(so.to_expression(expression), exp_str)

        check_value(sm.abs(-x), 2, 'abs(- x)')
        check_value(sm.log(x/2), 0, 'log(0.5 * x)')
        check_value(sm.log2(2*x), 2, 'log2(2 * x)')
        check_value(sm.log10(5*x), 1, 'log10(5 * x)')
        check_value(sm.exp(x), math.exp(2), 'exp(x)')
        check_value(sm.sqrt(x**2), 2, 'sqrt((x) ^ (2))')
        check_value(sm.mod(5*x, 3), 1, 'mod(5 * x , 3)')
        check_value(sm.int(x+0.5), 2, 'int(x + 0.5)')
        check_value(sm.sign(-2 * x), -1, 'sign(- 2 * x)')
        check_value(sm.tan(x), math.tan(2), 'tan(x)')
        check_value(sm.sinh(x), math.sinh(2), 'sinh(x)')
        check_value(sm.cosh(x), math.cosh(2), 'cosh(x)')
        check_value(sm.tanh(x), math.tanh(2), 'tanh(x)')
