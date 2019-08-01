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
import sasoptpy as so
from inspect import cleandoc


class TestReadData(unittest.TestCase):

    def setUp(self):
        pass


    def test_read_regular_existing(self):

        with so.Workspace('test_workspace') as ws:

            ITEMS = so.abstract.Set(name='ITEMS')
            value = so.abstract.ParameterGroup(ITEMS, name='value', init=0)
            get = ws.add_variables(ITEMS, name='get', vartype=so.INT, lb=0)

            ws.read_data(
                table="values",
                index={'target': ITEMS, 'column': None},
                columns=[{'column': value}])

            ws.solve(options={'with': so.LSO, 'maxgen': 10})

        optmodel_code = so.to_optmodel(ws)
        self.assertEqual(optmodel_code, cleandoc("""
        proc optmodel;
            set ITEMS;
            num value{ITEMS} init 0;
            var get {{ITEMS}} integer >= 0;
            read data values into ITEMS value;
            solve with lso / maxgen=10;
        quit;
        """))


    def tearDown(self):
        pass
