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
        val = test(TestExamplesLocal.conn, **kwargs)
        if isinstance(val, tuple):
            print(test.__globals__['__file__'], val[0], time.time() - t0)
        else:
            print(test.__globals__['__file__'], val, time.time()-t0)
        return val

    def test_fm1(self):
        from food_manufacture_1 import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 107842.5925925926, self.digits)

    def test_fm2(self):
        from food_manufacture_2 import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 100278.7, 1)

    def test_fp1(self):
        from factory_planning_1 import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 93715.17857142858, self.digits)

    def test_fp2(self):
        from factory_planning_2 import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 108855.0, 1)

    def test_mp(self):
        from manpower_planning import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 498677.2853185597, self.digits)

    def test_ro(self):
        from refinery_optimization import test
        obj = self.run_instance(test, limit_names=True)
        self.assertAlmostEqual(obj, 211365.134768933, self.digits)

    def test_mo(self):
        from mining_optimization import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 146.86, 2)

    def test_farmp(self):
        from farm_planning import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 121719.17286133641, self.digits)

    def test_econ(self):
        from economic_planning import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 2450.026622821294, self.digits)

    def test_decentral(self):
        from decentralization import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 14.9, self.digits)

    def test_kidney_exchange(self):
        from sas_kidney_exchange import test
        try:
            obj = self.run_instance(test)
        except RuntimeError:
            obj = self.run_instance(test, wrap_lines=True)
        self.assertAlmostEqual(obj, 17.11135898487, self.digits)

    def test_optimal_wedding(self):
        from sas_optimal_wedding import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 13.0, self.digits)

    def test_curve_fitting(self):
        from curve_fitting import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 1.475, self.digits)

    def test_nl1(self):
        from nonlinear_1 import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 3.951157967716, self.digits)

    def test_nl2(self):
        from nonlinear_2 import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, -999.0, self.digits)

    def test_least_squares(self):
        from least_squares import test
        obj = self.run_instance(test)
        self.assertAlmostEqual(obj, 7.186296783293, self.digits)

    def test_efficiency_analysis(self):
        from efficiency_analysis import test
        obj, ed = self.run_instance(test, get_tables=True)
        en = ed.set_index('garage_name').loc['Woking', 'efficiency_number']
        self.assertAlmostEqual(en, 0.867320, self.digits)
