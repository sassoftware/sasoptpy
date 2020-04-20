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
Unit test for configurations
"""

import unittest
import sasoptpy as so


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.define_problem()

    def define_problem(self):
        self.model = so.Model(name='model_test_config')
        self.var = self.model.add_variable(name='x')
        self.con = self.model.add_constraint(
            10 / 3 * self.var + 1e-20 * self.var ** 2 <= 30 + 1e-11,
            name='c')
        self.target_config = 'max_digits'
        self.expected_response = {
            2: "con c : 3.33 * x + 0.0 * ((x) ^ (2)) <= 30.0;",
            3: "con c : 3.333 * x + 0.0 * ((x) ^ (2)) <= 30.0;",
            None: "con c : 3.3333333333333335 * x + 1e-20 * ((x) ^ (2)) <= 30.00000000001;"
        }
        self.new_config_key = 'new_config'
        self.new_config_value = 20

    def measure_function(self):
        return self.con._defn()

    def test_default_configs(self):
        self.assertEqual(set(so.default_config_keys), set(so.config.keys))

    def test_config_constructor(self):
        for i in self.expected_response.keys():
            so.config = so.Config(self.target_config, i)
            actual_response = self.measure_function()
            self.assertEqual(actual_response, self.expected_response[i])

    def test_override_config(self):
        for i in self.expected_response.keys():
            so.config[self.target_config] = i
            actual_response = self.measure_function()
            self.assertEqual(actual_response, self.expected_response[i])

    def test_delete_overridden(self):
        original_value = so.config[self.target_config]
        so.config[self.target_config] = original_value + 1
        del so.config[self.target_config]
        self.assertEqual(so.config[self.target_config], original_value)

    def test_config_reset(self):
        original_value = so.config[self.target_config]
        so.config[self.target_config] = original_value + 1
        so.config.reset()
        self.assertEqual(so.config[self.target_config], original_value)

    def test_add_delete_config(self):
        so.config[self.new_config_key] = self.new_config_value
        self.assertEqual(so.config[self.new_config_key], self.new_config_value)
        del so.config[self.new_config_key]
        self.assertEqual(so.config[self.new_config_key], None)

    def test_delete_key_exception(self):
        def delete_nonexistent_key():
            del so.config['nonexistent_key']
        self.assertRaises(KeyError, delete_nonexistent_key)

    def test_config_iter(self):
        list_of_keys_via_iter = set()
        list_of_keys_via_keys = set()

        for i in so.config:
            list_of_keys_via_iter.add(i)
        for i in so.config.keys:
            list_of_keys_via_keys.add(i)

        self.assertEqual(list_of_keys_via_iter, list_of_keys_via_keys)

    def tearDown(self):
        so.reset()
