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
Unit test for If-Else-Switch statements.
"""

import os
import sys
import unittest
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../..')))
from util import assert_equal_wo_temps

from sasoptpy.actions import if_condition, switch_conditions

class TestIfElse(unittest.TestCase):
    """
    Unit tests for IF/ELSE and SWITCH statements
    """

    def setUp(self):
        so.reset()

    def test_regular_if_else(self):
        with so.Workspace('w') as w:
            x = so.Variable(name='x')
            x.set_value(0.5)
            def func1():
                x.set_value(1)
            def func2():
                x.set_value(0)
            if_condition(x > 1e-6, func1, func2)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               x = 0.5;
               if x > 1e-06 then do;
                  x = 1;
               end;
               else do;
                  x = 0;
               end;
            quit;'''))

    def test_regular_switch(self):
        with so.Workspace('w') as w:
            x = so.Variable(name='x')
            p = so.Parameter(name='p')
            x.set_value(2.5)
            def func1():
                p.set_value(1)
            def func2():
                p.set_value(2)
            def func3():
                p.set_value(3)
            def func4():
                p.set_value(0)

            switch_conditions(x < 1, func1, x < 2, func2, x < 3, func3, func4)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               num p;
               x = 2.5;
               if x < 1 then do;
                  p = 1;
               end;
               else if x < 2 then do;
                  p = 2;
               end;
               else if x < 3 then do;
                  p = 3;
               end;
               else do;
                  p = 0;
               end;
            quit;'''))

    def test_combined_condition(self):
        with so.Workspace('w') as w:
            p = so.Parameter(name='p')
            def case1():
                p.set_value(10)
            def case2():
                p.set_value(20)
            r = so.Parameter(name='r', value=10)
            if_condition((r < 5) | (r > 10), case1, case2)

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num p;
               num r = 10;
               if (r < 5) or (r > 10) then do;
                  p = 10;
               end;
               else do;
                  p = 20;
               end;
            quit;'''))
