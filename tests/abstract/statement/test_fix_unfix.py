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
Unit test for fix/unfix statements.
"""

import os
import sys
import unittest
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../..')))
from util import assert_equal_wo_temps

from sasoptpy.actions import fix, unfix

class TestFix(unittest.TestCase):
    """
    Unit tests for FIX and UNFIX statements
    """

    def setUp(self):
        so.reset()

    def test_regular_fix(self):

        from sasoptpy.actions import solve

        with so.Workspace('w') as w:
            x = so.Variable(name='x')
            fix(x, 1)
            solve()
            unfix(x)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               fix x=1;
               solve;
               unfix x;
            quit;'''))

    def test_with_multiple_ops(self):

        from sasoptpy.actions import solve, cofor_loop

        with so.Workspace('w') as w:
            x = so.VariableGroup(4, name='x')
            for i in cofor_loop(range(4)):
                fix((x[0], i), (x[1], 1))
                solve()
                unfix(x[0], (x[1], 2))

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x {{0,1,2,3}};
               cofor {TEMP1 in 0..3} do;
                  fix x[0]=TEMP1 x[1]=1;
                  solve;
                  unfix x[0] x[1]=2;
               end;
            quit;'''))
