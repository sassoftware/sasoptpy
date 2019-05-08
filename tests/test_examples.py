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
import sys
import time


class NullWriter:

    def write(self, text): pass

    def flush(self): pass


class TestExamples(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from swat import CAS, SWATError
        try:
            cls.conn = CAS(os.environ.get('CASHOST'),
                           int(os.environ.get('CASPORT')),
                           authinfo=os.environ.get('AUTHINFO'))
            cls.defstdout = sys.stdout
        except SWATError:
            print()
            raise unittest.SkipTest('Cannot establish CAS connection. ' \
                  + 'Check your environment variables ' \
                  + '(CASHOST, CASPORT, AUTHINFO)')
        except TypeError:
            raise unittest.SkipTest('CASPORT environment variable is not'
                                    'defined')


    def setUp(self):
        sasoptpy.config['max_digits'] = 12
        self.digits = 6

    def tearDown(self):
        sasoptpy.reset()

    def run_test(self, test):
        sys.stdout = NullWriter()
        t0 = time.time()
        val = test(TestExamples.conn)
        sys.stdout = TestExamples.defstdout
        print(test.__globals__['__file__'], val, time.time()-t0)
        return val

    def test_fm1(self):
        from examples.food_manufacture_1 import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 107842.5925925926, self.digits)

    def test_fm2(self):
        from examples.food_manufacture_2 import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 100278.7037037037, self.digits)

    def test_fp1(self):
        from examples.factory_planning_1 import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 93715.17857142858, self.digits)

    def test_fp2(self):
        from examples.factory_planning_2 import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 108855.00772495591, self.digits)

    def test_mp(self):
        from examples.manpower_planning import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 498677.2853185597, self.digits)

    def test_ro(self):
        from examples.refinery_optimization import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 211365.134768933, self.digits)

    def test_mo(self):
        from examples.mining_optimization import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 146.861980777726, self.digits)

    def test_farmp(self):
        from examples.farm_planning import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 121719.17286133641, self.digits)

    def test_econ(self):
        from examples.economic_planning import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 2450.026622821294, self.digits)

    def test_decentral(self):
        from examples.decentralization import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 14.9, self.digits)

    def test_kidney_exchange(self):
        from examples.sas_kidney_exchange import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 17.11135898487, self.digits)

    def test_optimal_wedding(self):
        from examples.sas_optimal_wedding import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 13.0, self.digits)

    def test_curve_fitting(self):
        from examples.curve_fitting import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 1.475, self.digits)

    def test_nl1(self):
        from examples.nonlinear_1 import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, 3.951157967716, self.digits)

    def test_nl2(self):
        from examples.nonlinear_2 import test
        obj = self.run_test(test)
        self.assertAlmostEqual(obj, -999.0, self.digits)


if __name__ == '__main__':
    # Default
    unittest.main(exit=False)
    # Frame method
    # Change 4th argument (frame) to True
    def_opts = sasoptpy.Model.solve.__defaults__
    sasoptpy.Model.solve.__defaults__ = (
        None, True, None, True, False, True, False, None, None, False)
    unittest.main()
