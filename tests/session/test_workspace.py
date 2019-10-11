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

import os
import unittest
import warnings
from inspect import cleandoc

from swat import CAS, SWATError
import sasoptpy as so


class TestWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
        try:
            cls.conn = CAS(os.environ.get('CASHOST'),
                           int(os.environ.get('CASPORT')),
                           authinfo=os.environ.get('AUTHINFO'))
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)

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

    def test_attributes(self):
        with so.Workspace('w') as w:
            S = so.Set(name='S')
            x = so.Variable(name='x')
            y = so.VariableGroup(4, name='y')
            z = so.VariableGroup(S, name='z')
            d = so.Variable(name='d')
            e = so.Variable(name='d')

        self.assertIn('Workspace[ID', str(w))
        self.assertEqual('sasoptpy.Workspace(w)', repr(w))
        w.set_session(None)
        self.assertEqual(w.get_session(), None)
        self.assertIs(x, w.get_variable('x'))
        self.assertIs(y, w.get_variable('y'))
        self.assertIs(z[0], w.get_variable('z[0]'))
        def warn_duplicate():
            w.get_variable('d')
        self.assertWarns(UserWarning, warn_duplicate)
        w.set_variable_value('z[0]', 1)
        self.assertEqual(z[0].get_value(), 1)

    def test_var_values(self):
        if TestWorkspace.conn is None:
            self.skipTest('CAS session is not available')

        from sasoptpy.actions import solve

        with so.Workspace('test_var_vals', session=TestWorkspace.conn) as w:
            S = so.Set(name='S', value=[1, 2, 3])
            x = so.Variable(name='x', lb=1, ub=4)
            y = so.VariableGroup(S, name='y', ub=7)
            z = so.VariableGroup(2, name='z', ub=2)
            o = so.Objective(x+y[1]+y[2]+y[3]+z[0], name='obj', sense=so.MAX)
            solve()

        w.submit(verbose=True)
        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
                set S = {1,2,3};
                var x >= 1 <= 4;
                var y {{S}} <= 7;
                var z {{0,1}} <= 2;
                max obj = x + y[1] + y[2] + y[3] + z[0];
                solve;
            quit;'''))
        self.assertEqual(x.get_value(), 4)
        self.assertEqual(y[1].get_value(), 7)
        self.assertEqual(z[0].get_value(), 2)
