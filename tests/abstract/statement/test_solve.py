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
Unit test for solve statements.
"""

import os
import sys
import unittest
import warnings
import sasoptpy as so
from inspect import cleandoc

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../..')))
from util import assert_equal_wo_temps

from sasoptpy.actions import solve, print_item

from tests.swat_config import create_cas_connection



class TestSolve(unittest.TestCase):
    """
    Unit tests for SOLVE statements
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

    def setUp(self):
        so.reset()

    def test_regular_solve(self):
        with so.Workspace('w') as w:
            x = so.Variable(name='x', lb=1, ub=10)
            o = so.Objective(2*x, sense=so.maximize, name='obj')
            s = solve()
            p = print_item(x)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x >= 1 <= 10;
               max obj = 2 * x;
               solve;
               print x;
            quit;'''))

        if TestSolve.conn:
            w.set_session(TestSolve.conn)
            w.submit()
            self.assertEqual(str(p.get_response()), cleandoc('''
                  x
            0  10.0'''))
            self.assertEqual(str(s.get_response()['Problem Summary']), cleandoc('''
                Problem Summary
                
                                                Value
                Label                                
                Objective Sense          Maximization
                Objective Function                obj
                Objective Type                 Linear
                                                     
                Number of Variables                 1
                Bounded Above                       0
                Bounded Below                       0
                Bounded Below and Above             1
                Free                                0
                Fixed                               0
                                                     
                Number of Constraints               0
                                                     
                Constraint Coefficients             0'''))

    def test_with_model(self):

        def produce_order_error():
            with so.Workspace('w') as w:
                m = so.Model(name='m')
                x = so.Variable(name='x')
                m.solve()
                m.include(x)
                m.solve()

        self.assertRaises(ReferenceError, produce_order_error)

        so.reset()
        with so.Workspace('w') as w:
            x = so.Variable(name='x')
            m = so.Model(name='m')
            m.include(x)
            m.solve()

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x;
               problem m include x;
               use problem m;
               solve;
            quit;'''))

    def test_with_options(self):
        with so.Workspace('w') as w:
            solve()
            solve(options={'with': 'milp'})
            solve(options={'with': 'milp'}, primalin=True)
            solve(options={'with': 'milp', 'presolver': None, 'feastol': 1e-6,
                           'logfreq': 2, 'maxsols': 3, 'scale': 'automatic',
                           'restarts': None, 'cutmir': 'aggressive'})

        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               solve;
               solve with milp;
               solve with milp / primalin;
               solve with milp / presolver=None feastol=1e-06 logfreq=2 maxsols=3 scale=automatic restarts=None cutmir=aggressive;
            quit;'''))


    def test_warning_without_abstract(self):

        def solve_without_abstract():
            m = so.Model(name='m1')
            x = m.add_variable(name='x')
            m.set_objective(2*x, name='o')
            solve()

        self.assertWarns(UserWarning, solve_without_abstract)
