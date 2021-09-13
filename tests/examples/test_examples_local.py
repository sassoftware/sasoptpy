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

import unittest
import os
import sasoptpy
import saspy
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../../examples/client_side')))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../../examples/server_side')))


class TestExamplesLocal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = None
        try:
            cls.conn = None
            if os.name == 'nt':
                cls.conn = saspy.SASsession(cfgname='winlocal')
            else:
                cfg_file = os.path.join(current_dir, 'saspy_config.py')
                cls.conn = saspy.SASsession(cfgfile=cfg_file)
            print('Connected to SAS')
            cls.conn.upload_frame = TestExamplesLocal.sas_upload
        except TypeError:
            raise unittest.SkipTest('Environment variable may not be defined')

    @classmethod
    def tearDownClass(cls):
        cls.conn.endsas()

    @classmethod
    def sas_upload(cls, data, casout):
        if isinstance(casout, str):
            name = casout
        else:
            name = casout.get('name')
        TestExamplesLocal.conn.df2sd(data, table=name)
        return name

    def setUp(self):
        sasoptpy.config['max_digits'] = 12
        self.digits = 5

    def tearDown(self):
        sasoptpy.reset()

    def run_instance(self, test, **kwargs):
        t0 = time.time()
        if kwargs:
            val = test(TestExamplesLocal.conn, **kwargs)
        else:
            val = test(TestExamplesLocal.conn)
        if isinstance(val, tuple):
            print(test.__globals__['__file__'], val[0], time.time() - t0)
        else:
            print(test.__globals__['__file__'], val, time.time()-t0)
        return val

    def test_all(self):
        problem_list = [
            {'problem': 'food_manufacture_1', 'obj': 107842.5925925926, 'digits': self.digits},
            {'problem': 'food_manufacture_2', 'obj': 100278.7, 'digits': 1},
            {'problem': 'factory_planning_1', 'obj': 93715.17857142858, 'digits': self.digits},
            {'problem': 'factory_planning_2', 'obj': 108855.0, 'digits': 1},
            {'problem': 'manpower_planning', 'obj': 498677.2853185597, 'digits': self.digits},
            {'problem': 'refinery_optimization', 'obj': 211365.134768933, 'digits': self.digits, 'limit_names': True},
            {'problem': 'mining_optimization', 'obj': 146.86, 'digits': 2},
            {'problem': 'farm_planning', 'obj': 121719.17286133641, 'digits': self.digits},
            {'problem': 'economic_planning', 'obj': 2450.026622821294, 'digits': self.digits},
            {'problem': 'decentralization', 'obj': 14.9, 'digits': self.digits},
            {'problem': 'sas_kidney_exchange', 'obj': 17.11135898487, 'digits': self.digits, 'wrap_lines': True},
            {'problem': 'sas_optimal_wedding', 'obj': 13.0, 'digits': self.digits},
            {'problem': 'curve_fitting', 'obj': 1.475, 'digits': self.digits},
            {'problem': 'nonlinear_1', 'obj': 3.951157967716, 'digits': self.digits},
            {'problem': 'nonlinear_2', 'obj': -999.0, 'digits': self.digits},
            {'problem': 'least_squares', 'obj': 7.186296783293, 'digits': self.digits},
            # {'problem': 'efficiency_analysis', 'obj': 0.867320, 'digits': self.digits, 'get_tables': True},
        ]
        for p in problem_list:
            example = __import__(p['problem'])
            test = example.test
            kwargs = {}
            if p.get('wrap_lines'):
                kwargs['wrap_lines'] = True
            if p.get('limit_names'):
                kwargs['limit_names'] = True
            obj = self.run_instance(
                test,
                **kwargs
                )
            self.assertAlmostEqual(obj, p['obj'], p['digits'])
