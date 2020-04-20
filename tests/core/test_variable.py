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


class TestVariable(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.Variable` objects
    """

    def setUp(self):
        pass

    def test_repr(self):
        x = so.Variable(name='x')
        self.assertEqual(repr(x), "sasoptpy.Variable(name='x', vartype='CONT')")

        y = so.Variable(name='y', lb=1, ub=10, init=3)
        self.assertEqual(repr(y), "sasoptpy.Variable(name='y', lb=1, ub=10, init=3, vartype='CONT')")

        I = so.Set(name='I')
        z = so.VariableGroup(I, name='z')
        self.assertEqual(repr(z[0]), "sasoptpy.Variable(name='z[0]', vartype='CONT')")

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
