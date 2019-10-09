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
Unit tests for workspaces.
"""

import unittest
import warnings
from inspect import cleandoc

import sasoptpy as so


class TestWorkspace(unittest.TestCase):

    def setUp(self):
        so.reset()

    def test_vg_in_session(self):
        with so.Workspace('w') as w:
            x = so.VariableGroup(4, name='x')
            x[2].set_bounds(lb=1)
            x[3].set_init(5)
        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                var x {{0,1,2,3}};
                x[3] = 5;
                x[2].lb = 1;
            quit;'''))
