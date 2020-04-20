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
Test for parameter class
"""

import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
from util import assert_equal_wo_temps

class TestParameter(unittest.TestCase):

    def setUp(self):
        so.reset()

    def test_regular_parameter(self):

        with so.Workspace('w') as w:
            p = so.Parameter(name='p', init=3)
            p.set_value(5)

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num p init 3;
               p = 5;
            quit;'''))

    def test_parameter_group(self):

        from sasoptpy.actions import for_loop, condition

        with so.Workspace('w') as w:
            p = so.ParameterGroup(so.exp_range(1, 6), name='p', init=3)
            p[0].set_value(3)
            S = so.Set(name='S', value=so.exp_range(1, 6))
            for i in for_loop(S):
                p[i].set_value(1)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num p {1..5} init 3;
               p[0] = 3;
               set S = 1..5;
               for {TEMP1 in S} do;
                  p[TEMP1] = 1;
               end;
            quit;'''))

    def test_value(self):

        p = so.Parameter(name='p', value=5)
        self.assertEqual(p.get_value(), 5)
