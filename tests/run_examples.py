import unittest
import os
import sasoptpy
import sys


class NullWriter:

    def write(self, str): pass

    def flush(self): pass


class TestExamples(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from swat import CAS
        cls.conn = CAS(os.environ.get('CASHOST'),
                       int(os.environ.get('CASPORT')),
                       authinfo=os.environ.get('AUTHINFO'))
        cls.defstdout = sys.stdout

    def tearDown(self):
        sasoptpy.reset_globals()

    def run_test(self, test):
        sys.stdout = NullWriter()
        val = test(TestExamples.conn)
        sys.stdout = TestExamples.defstdout
        print(test.__globals__['__file__'])
        print(val)
        return val

    def test_fm1(self):
        from examples.food_manufacture_1 import test
        obj = self.run_test(test)
        self.assertEqual(obj, 107842.592593)

    def test_fm2(self):
        from examples.food_manufacture_2 import test
        obj = self.run_test(test)
        self.assertEqual(obj, 100278.703704)

    def test_fp1(self):
        from examples.factory_planning_1 import test
        obj = self.run_test(test)
        self.assertEqual(obj, 93715.178571)

    def test_fp2(self):
        from examples.factory_planning_2 import test
        obj = self.run_test(test)
        self.assertEqual(obj, 108855.009314)

    def test_mp(self):
        from examples.manpower_planning import test
        obj = self.run_test(test)
        self.assertEqual(obj, 498677.285319)

    def test_ro(self):
        from examples.refinery_optimization import test
        obj = self.run_test(test)
        self.assertEqual(obj, 211365.134769)

    def test_mo(self):
        from examples.mining_optimization import test
        obj = self.run_test(test)
        self.assertEqual(obj, 146.861979)

    def test_farmp(self):
        from examples.farm_planning import test
        obj = self.run_test(test)
        self.assertEqual(obj, 121719.172861)

    def test_econ(self):
        from examples.economic_planning import test
        obj = self.run_test(test)
        self.assertEqual(obj, 2450.026623)

    def test_decentral(self):
        from examples.decentralization import test
        obj = self.run_test(test)
        self.assertEqual(obj, 14.9)

    def test_kidney_exchange(self):
        from examples.sas_kidney_exchange import test
        obj = self.run_test(test)
        self.assertEqual(obj, 17.111359)

    def test_optimal_wedding(self):
        from examples.sas_optimal_wedding import test
        obj = self.run_test(test)
        self.assertEqual(obj, 6.0)


if __name__ == '__main__':
    # Default
    unittest.main(exit=False)
    # Frame method
    # Change 4th argument (frame) to True
    def_opts = sasoptpy.Model.solve.__defaults__
    sasoptpy.Model.solve.__defaults__ = (None, True, None, True, False, True, False, None, None)
    unittest.main()
