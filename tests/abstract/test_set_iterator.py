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


class TestSetIterator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        so.reset()
        from swat import CAS, SWATError
        try:
            cls.conn = CAS(os.environ.get('CASHOST'),
                           int(os.environ.get('CASPORT')),
                           authinfo=os.environ.get('AUTHINFO'))
        except SWATError:
            warnings.warn('CAS connection is not available', RuntimeWarning)
        except TypeError:
            warnings.warn('CAS variables are not available', RuntimeWarning)

    def test_set_iterator_init(self):
        S = so.Set(name='S')
        i = so.SetIterator(S, name='i')

        self.assertEqual(i.get_name(), 'i')
        self.assertEqual(i.get_type(), so.NUM)
        self.assertEqual(so.to_definition(i), 'i in S')

        for j in S:
            assert_equal_wo_temps(self, so.to_definition(j), 'o1 in S')

    def test_set_iterator_as_exp(self):
        S = so.Set(name='S')
        x = so.VariableGroup(S, name='x')
        for i in S:
            e = i + x[0]
            assert_equal_wo_temps(self, so.to_expression(e), 'o1 + x[0]')

    # def test_set_iterator_compare(self):
    #     S = so.Set(name='S')
    #     for i in S:
    #         for j in S:
    #             print(i==j)
    #             self.assertNotEqual(i, j)

    def test_set_iterator_condition(self):

        S = so.Set(name='S')
        x = so.VariableGroup(S, name='x')
        #c = so.ConstraintGroup((i * x[i] <= 5 for i in S if value(i) > 1), name='c')

        #print(so.to_definition(c))
        #print(so.to_optmodel(ws))


    def tearDown(self):
        pass
