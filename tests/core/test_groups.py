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


class TestVariableGroup(unittest.TestCase):

    def setUp(self):
        pass

    def test_constructor(self):
        idx = [1,2,3]
        v = so.VariableGroup(idx, name=None)
        self.assertEqual(repr(v),
                         "sasoptpy.VariableGroup([1, 2, 3], name='vg_1')")

        u = so.VariableGroup(5, name='u')
        self.assertEqual(repr(u),
                         "sasoptpy.VariableGroup([0, 1, 2, 3, 4], name='u')")

    def test_get_name(self):
        # Test regular name
        u = so.VariableGroup(4, name='myvargroup')
        self.assertEqual(u.get_name(), 'myvargroup')

        # Test default name
        v = so.VariableGroup(5, name=None)
        self.assertEqual(v.get_name(), 'vg_1')

    def test_abstract(self):
        u = so.VariableGroup(4, name='u')
        self.assertFalse(u._abstract)
        u.set_abstract(True)
        self.assertTrue(u._abstract)

        from sasoptpy.abstract.data import Set
        I = Set(name='I')
        v = so.VariableGroup(I, name='v')
        self.assertTrue(v._abstract)
        v.set_abstract(False)
        self.assertFalse(v._abstract)

    def tearDown(self):
        so.reset()


