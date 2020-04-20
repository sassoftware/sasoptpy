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
Unit tests for set iterators.
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

from tests.swat_config import create_cas_connection


class TestSetIterator(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.abstract.SetIterator` objects
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

    def test_set_iterator_init(self):
        S = so.Set(name='S')
        i = so.SetIterator(S, name='i')

        self.assertEqual(i.get_name(), 'i')
        self.assertEqual(i.get_type(), so.NUM)

        for j in S:
            assert_equal_wo_temps(self, j._get_for_expr(), 'o1 in S')
            assert_equal_wo_temps(
                self, repr(j),
                'sasoptpy.SetIterator(S, name=\'o1\')'
            )

    def test_set_iterator_as_exp(self):
        S = so.Set(name='S')
        x = so.VariableGroup(S, name='x')
        for i in S:
            e = i + x[0]
            assert_equal_wo_temps(self, so.to_expression(e), 'o1 + x[0]')
            assert_equal_wo_temps(self, so.to_definition(i), 'o1 in S')

    def test_set_iterator_condition(self):

        from sasoptpy.actions import condition

        S = so.Set(name='S')
        P = so.Set(name='P')
        x = so.VariableGroup(S, name='x')

        # GT
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(2*i > 1):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: 2.0 * o4 > 1} : o4 * x[o4] <= 5;')

        # GE
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(2 * i >= 1):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: 2.0 * o4 >= 1} : o4 * x[o4] <= 5;')

        # LT
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(2 * i < 1):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: 2.0 * o4 < 1} : o4 * x[o4] <= 5;')

        # LE
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(2 * i <= 1):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: 2.0 * o4 <= 1} : o4 * x[o4] <= 5;')

        # EQ
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(2 * i == 1):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: 2.0 * o4 = 1} : o4 * x[o4] <= 5;')

        # NE
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(2 * i != 1):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: 2.0 * o4 ne 1} : o4 * x[o4] <= 5;')

        # IN
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            with condition(i.sym in P):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o4 in S: o4 IN P} : o4 * x[o4] <= 5;')

        # Alternatively:
        # assert_equal_wo_temps(
        #     self, so.to_definition(c),
        #     'con c {o4 in S: <o4> IN P} : o4 * x[o4] <= 5;')

        # AND, OR, Multi Statement
        c = so.ConstraintGroup(None, name='c')
        for i in S:
            e1 = 2 * i != 1
            e2 = i ** 2 <= 3
            e3 = 3 * i >= 9
            e4 = i != 0
            with condition(((e1) & (e2) | (e3)) & (e4)):
                c[i] = i * x[i] <= 5

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c {o34 in S: ((((2.0 * o34 ne 1) and ((o34) ^ (2) <= 3)) or (3.0 * o34 >= 9)) and (o34 NE 0))} : o34 * x[o34] <= 5;'
        )

    def test_set_iterator_group(self):

        S = so.Set(name='S', settype=[so.STR, so.NUM])
        x = so.VariableGroup(S, name='x')
        p = so.ParameterGroup(S, name='p')
        c = so.ConstraintGroup(None, name='c')
        d = so.ConstraintGroup(None, name='d')
        for k in S:
            (i, j) = k
            c[k] = so.Constraint(x[i, j] + 5 <= 3*i - 2*j)
            for t in range(3):
                d[k, t] = so.Constraint(x[i, t] <= 4 * j)

        assert_equal_wo_temps(
            self, so.to_definition(c),
            'con c_o7 {<o8, o10> in S} : x[o8, o10] - 3.0 * o8 + 2.0 * o10 <= -5;')
        assert_equal_wo_temps(
            self, so.to_definition(d),
            cleandoc('''
                con d_o7_0 {<o8, o10> in S} : x[o8, 0] - 4.0 * o10 <= 0;
                con d_o7_1 {<o8, o10> in S} : x[o8, 1] - 4.0 * o10 <= 0;
                con d_o7_2 {<o8, o10> in S} : x[o8, 2] - 4.0 * o10 <= 0;
            ''')
        )

    def test_set_iterator_in_iterate(self):

        with so.Workspace('test_set_iter_in_iterate') as w:
            S = so.Set(name='S', settype=[so.NUM, so.NUM])
            W = so.Set(name='W', settype=so.NUM)
            p = so.ParameterGroup(S, W, name='p')
            x = so.VariableGroup(S, name='x')

            from sasoptpy.actions import read_data
            from sasoptpy.util import iterate

            with iterate(S, name=['pos1', 'pos2']) as keys:
                r = read_data(
                    table='cas_table_1',
                    index={
                        'target': S,
                        'key': keys
                    }
                )
                with iterate(W, name='d') as d:
                    r.append({
                        'index': d,
                        'target': p[keys['pos1'], keys['pos2'], d],
                        'column': d
                    })

                assert_equal_wo_temps(self, so.to_definition(keys),
                                      '<pos1, pos2> in S')
                self.assertEqual(repr(keys), cleandoc('''
                    sasoptpy.SetIteratorGroup(S, datatype=['num', 'num'], names=['pos1', 'pos2'])
                '''))
                self.assertEqual(so.to_expression(keys), 'pos1, pos2')
                self.assertEqual(str(keys), '(pos1, pos2)')


        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set <num, num> S;
               set W;
               num p {S, W};
               var x {{S}};
               read data cas_table_1 into S=[pos1 pos2] {d in W} < p[pos1, pos2, d]=col(d) >;
            quit;
            '''))

    def test_definition_multi(self):
        regset = so.Set(name='regset')
        multiset = so.Set(name='multiset', settype=[so.string, so.number])
        mt = so.VariableGroup(5, name='mt')
        e = so.expr_sum(mt[k] for k in regset)
        self.assertEqual(so.to_expression(e), "sum {k in regset} (mt[k])")
        e = so.expr_sum(mt[k] for k in multiset)
        assert_equal_wo_temps(self, so.to_expression(e),
                              "sum {<o1, o2> in multiset} (mt[o1, o2])")

    def tearDown(self):
        pass
