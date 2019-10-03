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
Unit tests for core classes.
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


class TestForLoop(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

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
                    set_value(P[i, j], so.quick_sum(A[i, k] * A[j, k] for k in rn))

            q = so.VariableGroup(rn, rn, name='q')
            set_value(q[1, 1], 1)
            set_objective(
                so.quick_sum((
                    so.quick_sum(q[k, i] * q[k, j] for k in so.exp_range(1, i)) +
                    so.quick_sum(q[i, k] * q[k, j] for k in so.exp_range(i+1, j)) +
                    so.quick_sum(q[i, k] * q[j, k] for k in so.exp_range(j+1, n)) -
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
                    for {o7 in RN} do;
                        for {o10 in o7..n} do;
                            P[o7, o10] = sum {k in RN} (A[o7, k] * A[o10, k]);
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
