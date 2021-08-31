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
Unit tests for bug-fixes and patch releases.
"""

import unittest
import sasoptpy as so
from inspect import cleandoc


class TestPatches(unittest.TestCase):
    """
    Unit tests for patches
    """

    def setUp(self):
        so.reset()

    def test_multi_iterators(self):

        def get_nearby(v):
            return (v-1, v+1)

        G = list(range(5))

        m = so.Model(name='test_multi_iter')
        x = m.add_variables(G, name='x', ub=10)
        m.set_objective(so.expr_sum(x[i] for i in G), name='obj',
                        sense=so.maximize)

        m.add_constraints(
            (so.expr_sum(x[k] for k in range(j) if k != i) >= x[i] -1
             for i in G for j in get_nearby(i) if j >=0 and j<=4),
            name='c1'
        )

        for i in G:
            for j in get_nearby(i):
                if j>=0 and j<=4:
                    m.add_constraint(so.expr_sum(x[k] for k in range(j) if k!=i) >= x[i]-1, name=so.util.get_next_name())

        m.add_constraints(
            (so.expr_sum(x[k] for k in range(j)) >= x[i] - 1
             for i in range(5) for j in get_nearby(i) if j >= 0 and j <= 4),
            name='c2'
        )

        self.assertEqual(so.to_optmodel(m), cleandoc('''
            proc optmodel;
               var x {{0,1,2,3,4}} <= 10;
               max obj = x[0] + x[1] + x[2] + x[3] + x[4];
               con c1_0_1 : - x[0] >= -1;
               con c1_1_0 : - x[1] >= -1;
               con c1_1_2 : x[0] - x[1] >= -1;
               con c1_2_1 : x[0] - x[2] >= -1;
               con c1_2_3 : x[0] + x[1] - x[2] >= -1;
               con c1_3_2 : x[0] + x[1] - x[3] >= -1;
               con c1_3_4 : x[0] + x[1] + x[2] - x[3] >= -1;
               con c1_4_3 : x[0] + x[1] + x[2] - x[4] >= -1;
               con o37 : - x[0] >= -1;
               con o40 : - x[1] >= -1;
               con o43 : x[0] - x[1] >= -1;
               con o46 : x[0] - x[2] >= -1;
               con o49 : x[0] + x[1] - x[2] >= -1;
               con o52 : x[0] + x[1] - x[3] >= -1;
               con o55 : x[0] + x[1] + x[2] - x[3] >= -1;
               con o58 : x[0] + x[1] + x[2] - x[4] >= -1;
               con c2_0_1 : 1 >= -1;
               con c2_1_0 : - x[1] >= -1;
               con c2_1_2 : x[0] >= -1;
               con c2_2_1 : x[0] - x[2] >= -1;
               con c2_2_3 : x[0] + x[1] >= -1;
               con c2_3_2 : x[0] + x[1] - x[3] >= -1;
               con c2_3_4 : x[0] + x[1] + x[2] >= -1;
               con c2_4_3 : x[0] + x[1] + x[2] - x[4] >= -1;
               solve;
            quit;'''))
