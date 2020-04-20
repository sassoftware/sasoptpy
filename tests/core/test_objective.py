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

import unittest
from inspect import cleandoc

import sasoptpy as so


class TestObjective(unittest.TestCase):
    """
    Unit tests for :class:`sasoptpy.Objective` objects
    """

    @classmethod
    def setUpClass(cls):
        cls.model = so.Model(name='test_objective')
        cls.x = cls.model.add_variable(name='x')

    def test_init(self):
        x = TestObjective.x
        all_params = so.Objective(x ** 2 + 2 * x - 1, name='all_params',
                                  sense=so.MIN)
        self.assertEqual(str(all_params), "(x) ** (2) + 2 * x - 1")

        no_sense = so.Objective(2 * x, name='no_sense')
        self.assertEqual(no_sense.get_sense(), so.MIN)

    def test_model_init(self):
        m = TestObjective.model
        x = TestObjective.x

        obj = m.set_objective(2 * x - x ** 3, sense=so.MIN, name='new_obj')
        self.assertEqual(str(m.get_objective()), "2 * x - ((x) ** (3))")

    def test_defn(self):
        x = TestObjective.x
        def_obj = so.Objective(4 * x - x, name='objdef', sense=so.MAX)
        self.assertEqual(so.to_definition(def_obj),
                         "max objdef = 3 * x;")

    def test_sense(self):
        m = TestObjective.model
        x = TestObjective.x

        m.set_objective(3 * x, name='obj1')
        self.assertEqual(m.get_objective().get_sense(), so.MIN)
        m.get_objective().set_sense(so.MAX)
        self.assertEqual(m.get_objective().get_sense(), so.MAX)

    def test_in_container(self):
        from sasoptpy.actions import for_loop, solve

        with so.Workspace('w') as w:
            x = so.Variable(name='x', lb=0.5, vartype=so.INT, init=2)
            o = so.Objective(x**2, name='obj', sense=so.MIN)
            m = so.Model(name='model1')
            m.include(x, o)
            m.solve(options={'with': 'milp', 'relaxint': True}, primalin=True)
        self.assertEqual(so.to_optmodel(w), cleandoc('''
            proc optmodel;
               var x integer >= 0.5 init 2;
               min obj = (x) ^ (2);
               problem model1 include x obj;
               use problem model1;
               solve with milp relaxint / primalin;
            quit;'''))

    def test_value(self):
        x = TestObjective.x
        all_params = so.Objective(x ** 2 + 2 * x - 1, name='all_params',
                                  sense=so.MIN)
        x.set_value(2)
        self.assertEqual(all_params.get_value(), 7)

        y = so.Variable(name='y')
        y._abstract = True
        new_obj = so.Objective(y ** 2 - 1, name='new_obj')
        self.assertRaises(ValueError, new_obj.get_value)


    @classmethod
    def tearDownClass(self):
        so.reset()


