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

from tests.swat_config import create_cas_connection


class TestWorkspace(unittest.TestCase):
    """
    Unit tests for the :class:`sasoptpy.Workspace` objects
    """

    @classmethod
    def setUpClass(cls):
        so.reset()
        cls.conn = None
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
            t = so.VariableGroup(2, name='t')
            u = so.VariableGroup(2, name='t')

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
        def warn_duplicate_vg():
            w.get_variable('t')
        self.assertWarns(UserWarning, warn_duplicate_vg)
        w.set_variable_value('z[0]', 1)
        self.assertEqual(z[0].get_value(), 1)
        self.assertEqual(w.get_variable('a'), None)

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

    def test_ws_parsing(self):
        if TestWorkspace.conn is None:
            self.skipTest('CAS session is not available')

        from sasoptpy.actions import solve, drop, print_item
        from math import inf

        with so.Workspace('test_ws_parsing', session=TestWorkspace.conn)\
                as w:
            x = so.Variable(name='x')
            y = so.Variable(name='y', vartype=so.INT, lb=-inf)
            o = so.Objective(x**2-4*x+4, sense=so.MIN, name='obj')
            c1 = so.Constraint(x <= 1, name='c1')
            c2 = so.Constraint(x == 3*y, name='c2')
            s1 = solve(options={'with': so.BLACKBOX})
            p1 = print_item(x)
            drop(c1)
            s2 = so.LiteralStatement('solve with blackbox;')
            p2 = so.LiteralStatement('print y;')

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               var y integer;
               min obj = (x) ^ (2) - 4 * x + 4;
               con c1 : x <= 1;
               con c2 : x - 3 * y = 0;
               solve with blackbox;
               print x;
               drop c1;
               solve with blackbox;
               print y;
            quit;'''))

        w.submit()
        self.assertEqual(x.get_value(), 3)
        self.assertEqual(s1.get_problem_summary().to_string(), cleandoc('''
                                            Value
            Label                                
            Objective Sense          Minimization
            Objective Function                obj
            Objective Type              Quadratic
                                                 
            Number of Variables                 2
            Bounded Above                       0
            Bounded Below                       0
            Bounded Below and Above             0
            Free                                2
            Fixed                               0
            Binary                              0
            Integer                             1
                                                 
            Number of Constraints               2
            Linear LE (<=)                      1
            Linear EQ (=)                       1
            Linear GE (>=)                      0
            Linear Range                        0
                                                 
            Constraint Coefficients             3'''))
        self.assertEqual(p1.get_response().to_string(), cleandoc('''
                 x
            0  0.0'''))
        self.assertEqual(p2.get_response().to_string(), cleandoc('''
                 y
            0  1.0'''))


    def test_multithread_workspace(self):

        import time
        from threading import Thread

        def create_workspace(i):

            with so.Workspace(f'w{i}') as w:
                self.assertEqual(so.container, w)
                print('Start workspace: {}'.format(w.name))
                time.sleep(1)

            print('Exit workspace: {}'.format(w.name))
            return i

        threads = []
        for j in [1, 2, 3]:
            t = Thread(target=create_workspace, args=(j,))
            threads.append(t)
            t.start()

        for thread in threads:
            thread.join()

        print(threads)
