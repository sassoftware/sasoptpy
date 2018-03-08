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

'''
Set includes :class:`Set` class and implementations for server-side data
operations

'''


import sasoptpy.components
import sasoptpy.utils
#import pandas as pd

#==============================================================================
# class Statement:
# 
#     def _to_optmodel(self):
#         index = self._keys[0]
#         s = 'read data {} into {}=[{}] '.format(
#             self._name, index._name, index._colname)
#         if self._keysize > 1:
#             col = self._keys[1]
#             s += '{{j in {}}} <{}[{},j]=col(j)> '.format(
#                 col._name, self._name, index._colname)
#         s += ';'
#         return s
#==============================================================================

class Parameter:
    '''
    Represents set inside PROC OPTMODEL
    '''

    def __init__(self, name, keys, order=1):
        self._name = name
        self._keys = keys
        self._keysize = len(keys)
        self._order = order
        self._source = None
        self._keyset = None
        self._colname = name
        self._index = None
        self._shadows = {}

    def __getitem__(self, key):
        refname = sasoptpy.utils._to_bracket(self._name, key)
        if refname in self._shadows:
            return self._shadows[refname]
        else:
            pv = ParameterValue(refname)
            self._shadows[refname] = pv
            return pv

    def _set_loop(self, source, keyset, colname=None, index=None):
        self._source = source
        self._keyset = keyset
        self._colname = colname
        self._index = index

    def _to_optmodel(self):
        s = 'num {} {{'.format(self._name)
        for k in self._keyset:
            s += '{}, '.format(k._name)
        s = s[:-2]
        s += '};'
        return(s)

    def _to_read_data(self):
        if self._source is None:
            print('ERROR: Parameter {} is not declared!'.format(self._name))
            return ''
        s = ''
        if self._index:
            tablekeys = []
            jkeys = []
            keyctr = 1
            s += '{'
            for k in self._index:
                if k not in self._keyset:
                    key = 'j{}'.format(keyctr)
                    tablekeys.append(key)
                    jkeys.append(key)
                    s += '{} in {},'.format(key, k._name)
                else:
                    tablekeys.append(k._colname)
            s = s[:-1]
            s += '} '
            s += '<{}['.format(self._name)
            for j in tablekeys:
                s += '{},'.format(j)
            s = s[:-1]
            s += ']=col('
            for j in jkeys:
                s += '{},'.format(j)
            s = s[:-1]
            s += ')> '
        elif self._colname is not None and self._colname != self._name:
            s += '{}={} '.format(self._name, self._colname)
        else:
            s += '{} '.format(self._name)

        return(s)


class ParameterValue(sasoptpy.components.Expression):

    def __init__(self, paramkey):
        super().__init__()
        self._name = paramkey
        self._linCoef[paramkey] = {'ref': self,
                                   'val': 1.0}

    def __repr__(self):
        st = 'sasoptpy.ParameterValue(name=\'{}\')'.format(self._name)
        return st

    def __str__(self):
        return self._name


class Set:
    '''
    Represents index sets inside PROC OPTMODEL
    '''

    def __init__(self, name, settype='num'):
        self._name = name
        self._type = settype
        self._colname = name

    def __iter__(self):
        return iter([self._name])

    def _to_optmodel(self):
        s = 'set '
        if self._type == 'str':
            s += '<str> '
        s += self._name
        s += ';'
        return(s)

    def __hash__(self):
        return hash((self._name))

    def __eq__(self, other):
        if isinstance(other, Set):
            return (self._name) == (other._name)
        else:
            return False

    def __str__(self):
        s = self._name
        return(s)

    def __repr__(self):
        s = 'sasoptpy.data.Set(name={}, settype={})'.format(
            self._name, self._type)
        return(s)
