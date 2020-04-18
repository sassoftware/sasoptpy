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

from inspect import cleandoc
import os
import unittest
import warnings

from swat import CAS, SWATError

import sasoptpy as so

from tests.swat_config import create_cas_connection


class TestOPTMODEL(unittest.TestCase):
    """
    Unit tests for the CAS interface
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

    def test_variable_group_assignments(self):

        from sasoptpy.actions import read_data

        if TestOPTMODEL.conn is None:
            self.skipTest('CAS Session is not available')

        import pandas as pd
        df = pd.DataFrame([
            ['a', 'b', 1],
            ['c', 'd,e', 2],
            ['f,g', 'g,h,i', 3]
        ], columns=['k1', 'k2', 'v'])


        m = so.Model(name='m', session=TestOPTMODEL.conn)
        setK1 = df['k1'].tolist()
        setK2 = df['k2'].tolist()

        x = m.add_variables(setK1, setK2, name='x')
        m.add_constraints((x[i, j] >= 1 for i in setK1 for j in setK2), name='c')
        m.set_objective(so.expr_sum(x[i, j] for i in setK1 for j in setK2), name='obj', sense=so.minimize)
        m.solve(verbose=True)
        self.assertEqual(str(m.get_solution()), cleandoc('''
            Selected Rows from Table SOLUTION

                 i               var  value             lb             ub   rc
            0  1.0            x[a,b]    1.0 -1.797693e+308  1.797693e+308  0.0
            1  2.0        x[a,'d,e']    1.0 -1.797693e+308  1.797693e+308  0.0
            2  3.0      x[a,'g,h,i']    1.0 -1.797693e+308  1.797693e+308  0.0
            3  4.0            x[c,b]    1.0 -1.797693e+308  1.797693e+308  0.0
            4  5.0        x[c,'d,e']    1.0 -1.797693e+308  1.797693e+308  0.0
            5  6.0      x[c,'g,h,i']    1.0 -1.797693e+308  1.797693e+308  0.0
            6  7.0        x['f,g',b]    1.0 -1.797693e+308  1.797693e+308  0.0
            7  8.0    x['f,g','d,e']    1.0 -1.797693e+308  1.797693e+308  0.0
            8  9.0  x['f,g','g,h,i']    1.0 -1.797693e+308  1.797693e+308  0.0'''))

        so.config['generic_naming'] = True
        self.assertEqual(m.to_optmodel(), cleandoc('''
            proc optmodel;
               var x {{'a','c','f,g'}, {'b','d,e','g,h,i'}};
               x['a', 'b'] = 1.0;
               x['a', 'd,e'] = 1.0;
               x['a', 'g,h,i'] = 1.0;
               x['c', 'b'] = 1.0;
               x['c', 'd,e'] = 1.0;
               x['c', 'g,h,i'] = 1.0;
               x['f,g', 'b'] = 1.0;
               x['f,g', 'd,e'] = 1.0;
               x['f,g', 'g,h,i'] = 1.0;
               con c_0 : x['a', 'b'] >= 1;
               con c_1 : x['a', 'd,e'] >= 1;
               con c_2 : x['a', 'g,h,i'] >= 1;
               con c_3 : x['c', 'b'] >= 1;
               con c_4 : x['c', 'd,e'] >= 1;
               con c_5 : x['c', 'g,h,i'] >= 1;
               con c_6 : x['f,g', 'b'] >= 1;
               con c_7 : x['f,g', 'd,e'] >= 1;
               con c_8 : x['f,g', 'g,h,i'] >= 1;
               min obj = x['a', 'b'] + x['a', 'd,e'] + x['a', 'g,h,i'] + x['c', 'b'] + x['c', 'd,e'] + x['c', 'g,h,i'] + x['f,g', 'b'] + x['f,g', 'd,e'] + x['f,g', 'g,h,i'];
               solve;
            quit;'''))

