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
Unit test for structures
"""

import unittest
import sasoptpy as so


class TestStructure(unittest.TestCase):

    def setUp(self):
        so.reset()

    def test_not_implemented(self):
        c = so.statement_dictionary
        so.statement_dictionary = dict()
        from sasoptpy.actions import read_data

        def throw_not_implemented():
            with so.Workspace('w') as w:
                read_data(table='table', index='idx')

        self.assertRaises(NotImplementedError, throw_not_implemented)
        so.util.package_utils.load_function_containers()
