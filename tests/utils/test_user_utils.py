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
import unittest
import pandas as pd
import sasoptpy as so
from sasoptpy import to_expression as exp

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
from util import assert_equal_wo_temps


class TestUserUtils(unittest.TestCase):

    def setUp(self):
        so.reset()

    def test_concat(self):
        x = so.Variable(name='x')
        e1 = 'col'
        S = so.Set(name='S')
        e2 = so.SetIterator(S, name='i')
        r = so.util.concat(e1, e2)
        self.assertEqual(exp(r), '\'col\' || i')

    def test_exp_range(self):
        self.assertEqual(so.exp_range(1,5), range(1,5))
        t = so.exp_range(1, so.N)
        self.assertEqual(exp(t), '1.._N_')

    def test_get_value_table(self):

        self.assertEqual(so.get_value_table(), None)

        S = ['a', 'b', 'c']
        x = so.VariableGroup(S, name='x')
        x['a'].set_value(1)
        x['b'].set_value(3)
        x['c'].set_value(10)
        self.assertEqual(so.get_value_table(x).to_string(),
            cleandoc('''
                x
            a   1
            b   3
            c  10
            '''))

        c = so.ConstraintGroup((2 * x[i] >= 1 for i in S), name='c')
        self.assertEqual(so.get_value_table(c).to_string(), cleandoc(
            '''
                c
            a   2
            b   6
            c  20
            '''))

        df = pd.DataFrame([['a', 1, 2], ['b', 3, 4]],
                          columns=['var', 'lb', 'ub']).set_index(['var'])
        self.assertEqual(so.get_value_table(df).to_string(), cleandoc(
            '''
                lb ub
            var      
            a    1  2
            b    3  4
            '''))

        self.assertEqual(so.get_value_table(x, c).to_string(), cleandoc(
            '''
                x   c
            a   1   2
            b   3   6
            c  10  20
            '''
        ))

        self.assertEqual(so.get_value_table(df, df).to_string(), cleandoc(
            '''
                lb ub lb ub
            var            
            a    1  2  1  2
            b    3  4  3  4
            '''
        ))

        T = so.Set(name='T')
        y = so.VariableGroup(T, name='y')
        y[0].set_value(10)
        y[1].set_value(5)
        self.assertEqual(so.get_value_table(y).to_string(), cleandoc(
            '''
                y
            0  10
            1   5
            '''))

        z = so.ImplicitVar((2 * x[i] - 5 for i in S), name='z')
        self.assertEqual(so.get_value_table(z).to_string(), cleandoc(
            '''
                z
            a  -3
            b   1
            c  15
            '''
        ))

        e = so.Expression(x['a'] + 5 - y[0], name='e')
        self.assertEqual(so.get_value_table(e).to_string(), cleandoc(
            '''
               e
            - -4
            '''
        ))

    def test_submit(self):
        w = so.Workspace('w')
        def get_error_submit():
            w.submit()
        self.assertRaises(RuntimeError, get_error_submit)

        m = so.Model(name='m')
        def get_error_solve():
            m.solve()
        self.assertRaises(RuntimeError, get_error_solve)

    def test_expr_sum(self):
        S = ['a', 'b', 'c']
        x = so.VariableGroup(S, name='x')
        e = so.expr_sum(x[i] for i in S)

        T = so.Set(name='T')
        U = so.Set(name='U')
        y = so.VariableGroup(T, U, name='y')
        c = so.ConstraintGroup(
            (so.expr_sum(y[i, j] for i in T) <= 5 for j in U),
            name='c')
        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o10 in U} : sum {i in T} (y[i, o10]) <= 5;')

        e = so.expr_sum(y[i, 5] for i in T)
        assert_equal_wo_temps(self, exp(e), 'sum {i in T} (y[i, 5])')


    def test_reset_globals(self):
        def warn_reset_globals():
            so.reset_globals()
        self.assertWarns(DeprecationWarning, warn_reset_globals)

    def test_reset(self):
        x = so.Variable(name='x')
        self.assertGreater(so.itemid, 0)
        so.reset()
        self.assertEqual(so.itemid, 0)

    def test_dict_to_frame_and_flatten(self):
        d = {'coal': {'period1': 1, 'period2': 5, 'period3': 7},
           'steel': {'period1': 8, 'period2': 4, 'period3': 3},
           'copper': {'period1': 5, 'period2': 7, 'period3': 9}}
        df = so.dict_to_frame(d)
        self.assertEqual(df.to_string(), cleandoc(
            '''
                    period1  period2  period3
            coal          1        5        7
            steel         8        4        3
            copper        5        7        9
            '''))

        ff = so.flatten_frame(df)
        self.assertEqual(ff.to_string(), cleandoc(
            '''
            (coal, period1)      1
            (coal, period2)      5
            (coal, period3)      7
            (steel, period1)     8
            (steel, period2)     4
            (steel, period3)     3
            (copper, period1)    5
            (copper, period2)    7
            (copper, period3)    9
            '''))
        ffs = so.flatten_frame(df, swap=True)
        self.assertEqual(ffs.to_string(), cleandoc(
            '''
            (period1, coal)      1
            (period2, coal)      5
            (period3, coal)      7
            (period1, steel)     8
            (period2, steel)     4
            (period3, steel)     3
            (period1, copper)    5
            (period2, copper)    7
            (period3, copper)    9
            '''))


