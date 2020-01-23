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

from math import inf

import sasoptpy


class Config:
    """
    Option manager for sasoptpy
    """

    def __init__(self, *args):
        self.defaults = _get_default_config()
        self.overridden = dict()

        if len(args) > 1 and len(args) % 2 != 1:
            keys = args[::2]
            values = args[1::2]
            self.overridden = dict(zip(keys, values))

    def __getitem__(self, key):
        if key in self.overridden:
            return self.overridden[key]
        return self.defaults.get(key, None)

    def __setitem__(self, key, value):
        self.overridden[key] = value

    def __delitem__(self, key):
        if key in self.overridden:
            del self.overridden[key]
        else:
            raise KeyError('ERROR: Invalid config key: {}'.format(key))

    @property
    def keys(self):
        dicts = [self.defaults, self.overridden]
        merged_keys = set().union(*dicts)
        return list(merged_keys)

    def __iter__(self):
        for key in self.keys:
            yield key

    def reset(self):
        self.overridden = dict()


def _get_default_config():
    config = dict()
    config['verbosity'] = 3
    config['max_digits'] = 12
    config['print_digits'] = 6
    config['valid_outcomes'] = ['OPTIMAL', 'ABSFCONV', 'BEST_FEASIBLE']
    config['default_sense'] = sasoptpy.MIN
    config['submit_realtime'] = True
    config['default_bounds'] = {
        sasoptpy.CONT: {'lb': -inf, 'ub': inf},
        sasoptpy.INT: {'lb': -inf, 'ub': inf},
        sasoptpy.BIN: {'lb': 0, 'ub': 1}
    }

    return config


def _load_default_config():
    sasoptpy.config = Config()
    sasoptpy.default_config_keys = sasoptpy.config.keys
