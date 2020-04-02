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
Unit test for abstract assignments.
"""

import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc
from sasoptpy.actions import read_data

from tests.swat_config import create_cas_connection


class TestAssignment(unittest.TestCase):
    """
    Unit tests for assignment statements
    """

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
        from swat import CAS, SWATError
        try:
            cls.conn = create_cas_connection()
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            cls.conn.close()

    def test_bound_assignment(self):

        with so.Workspace('test_regular_assignment') as w:

            p = so.Parameter(name='p', init=2)
            x = so.VariableGroup(5, lb=1, name='x')
            x[0].set_bounds(lb=3)
            x[1].set_bounds(lb=p)
            p.set_value(4)
            x[2].set_bounds(lb=p, ub=p)
            x[3].set_bounds(ub=5)
            x[4].set_bounds(lb=1, ub=4)

        self.assertEqual(so.to_optmodel(w), cleandoc("""
            proc optmodel;
               num p init 2;
               var x {{0,1,2,3,4}} >= 1;
               x[0].lb = 3;
               x[1].lb = p;
               p = 4;
               fix x[2]=p;
               x[3].ub = 5;
               x[4].lb = 1;
               x[4].ub = 4;
            quit;
            """))

    def test_assignment_append(self):
        x = so.Variable(name='x')
        r = so.abstract.Assignment(x, 5)
        self.assertEqual(so.to_definition(r), 'x = 5;')
        y = so.Variable(name='y')
        r.append(identifier=y)
        self.assertEqual(so.to_definition(r), 'y = 5;')
        r.append(expression=10)
        self.assertEqual(so.to_definition(r), 'y = 10;')
        r.append(keyword='fix')
        self.assertEqual(so.to_definition(r), 'fix y = 10;')

    def test_fix_value(self):
        from sasoptpy.actions import fix
        with so.Workspace('w') as w:
            e = so.Parameter(name='e', value=4)
            x = so.VariableGroup(5, name='x')
            fix(x[0], 0)
            fix(x[1], e*2)
        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               num e = 4;
               var x {{0,1,2,3,4}};
               fix x[0]=0;
               fix x[1]=2 * e;
            quit;'''))
