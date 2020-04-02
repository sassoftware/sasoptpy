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
Unit tests for FOR loops.
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

from sasoptpy.actions import for_loop


class TestForLoop(unittest.TestCase):
    """
    Unit tests for FOR statements
    """

    def setUp(self):
        so.reset()

    def testRegularWorkspace(self):

        from sasoptpy.actions import for_loop, solve, set_value, set_objective, print_item

        with so.Workspace('ex_9_1_matirx_sqrt', session=None) as w:

            so.LiteralStatement('call streaminit(1);')

            n = so.Parameter(name='n', value=5)
            rn = so.Set(name='RN', value=so.exp_range(1, n))
            A = so.ParameterGroup(rn, rn, name='A', value="10-20*rand('UNIFORM')")
            P = so.ParameterGroup(rn, rn, name='P')

            for i in for_loop(rn):
                for j in for_loop(so.exp_range(i, n)):
                    set_value(P[i, j], so.expr_sum(A[i, k] * A[j, k] for k in rn))

            q = so.VariableGroup(rn, rn, name='q')
            set_value(q[1, 1], 1)
            set_objective(
                so.expr_sum((
                    so.expr_sum(q[k, i] * q[k, j] for k in so.exp_range(1, i)) +
                    so.expr_sum(q[i, k] * q[k, j] for k in so.exp_range(i+1, j)) +
                    so.expr_sum(q[i, k] * q[j, k] for k in so.exp_range(j+1, n)) -
                    P[i, j]
                )**2 for i in rn for j in so.exp_range(i, n))
                , name='r', sense=so.MIN)

            solve()
            print_item(P)
            print_item(q)

        assert_equal_wo_temps(
            self, so.to_optmodel(w),
            cleandoc(
                '''
                proc optmodel;
                   call streaminit(1);
                   num n = 5;
                   set RN = 1..n;
                   num A {RN, RN} = 10-20*rand('UNIFORM');
                   num P {RN, RN};
                   for {TEMP1 in RN} do;
                      for {TEMP2 in TEMP1..n} do;
                         P[TEMP1, TEMP2] = sum {k in RN} (A[TEMP1, k] * A[TEMP2, k]);
                      end;
                   end;
                   var q {{RN}, {RN}};
                   q[1, 1] = 1;
                   MIN r = sum {i in RN, j in i..n} ((sum {k in 1..i} (q[k, i] * q[k, j]) + sum {k in i+1..j} (q[i, k] * q[k, j]) + sum {k in j+1..n} (q[i, k] * q[j, k]) - P[i, j]) ^ (2));
                   solve;
                   print P;
                   print q;
                quit;
                '''))

    def test_basic(self):

        from sasoptpy.actions import put_item

        with so.Workspace('w') as w:
            for i in for_loop(range(1, 3)):
                for j in for_loop(['a', 'b']):
                    put_item(i, j)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc("""
            proc optmodel;
               for {TEMP1 in 1..2} do;
                  for {TEMP2 in {'a','b'}} do;
                     put TEMP1 TEMP2;
                  end;
               end;
            quit;"""))

    def test_with_assignment(self):
        with so.Workspace('w') as w:
            r = so.exp_range(1, 11)
            x = so.VariableGroup(r, name='x')
            for i in for_loop(r):
                x[i] = 1

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc("""
            proc optmodel;
               var x {{1,2,3,4,5,6,7,8,9,10}};
               for {TEMP1 in 1..10} do;
                  x[TEMP1] = 1;
               end;
            quit;"""))

    def test_with_predefined_set(self):
        with so.Workspace('w') as w:
            cn = so.Set(name='C', value=['a', 'b', 'c'])
            for i in for_loop(cn):
                so.actions.put_item(i)

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc("""
            proc optmodel;
               set C = {'a','b','c'};
               for {TEMP1 in C} do;
                  put TEMP1;
               end;
            quit;"""))

    def test_with_create_data(self):
        from sasoptpy.actions import create_data, read_data
        from sasoptpy.util import concat, iterate
        with so.Workspace('w') as w:
            m = so.Set(name='m', value=range(1, 4))
            rev = so.VariableGroup(range(1, 13), name='revenue')
            read_data(
                table='revdata',
                index={'key': so.N},
                columns=[
                    {'column': 'rev', 'target': rev}
                ]
            )
            month = so.SetIterator(None, name='month')
            for q in for_loop(so.exp_range(1, 5)):
                create_data(
                    table=concat('qtr', q),
                    index={'key': [month], 'set': m},
                    columns=[
                        {'expression': rev[month+(q-1)*3]}
                    ]
                )

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc("""
            proc optmodel;
               set m = 1..3;
               var revenue {{1,2,3,4,5,6,7,8,9,10,11,12}};
               read data revdata into [_N_] revenue=rev;
               for {TEMP1 in 1..4} do;
                  create data ('qtr' || TEMP1) from [month] = {m} revenue[month + 3.0 * TEMP1 - 3];
               end;
            quit;"""))


    def test_multiple_set_loop(self):

        with so.Workspace('w') as w:
            r = so.Set(name='R', value=range(1, 11))
            c = so.Set(name='C', value=range(1, 6))
            a = so.ParameterGroup(r, c, name='A', ptype=so.number)
            for (i, j) in for_loop(r, c):
                a[i, j] = 1

        assert_equal_wo_temps(self, so.to_optmodel(w), cleandoc('''
            proc optmodel;
               set R = 1..10;
               set C = 1..5;
               num A {R, C};
               for {TEMP1 in R, TEMP2 in C} do;
                  A[TEMP1, TEMP2] = 1;
               end;
            quit;'''))
