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
Math includes the definition of mathematical operations

'''

import sasoptpy.utils


def math_func(exp, op, *args):
    try:
        exp = sasoptpy.utils.get_mutable(exp)
        exp._operator = op
        for arg in args:
            exp._arguments.append(arg)
        r = sasoptpy.utils.wrap(exp)
        return r
    except AttributeError:
        pass


# Basic functions
def abs(exp): return math_func(exp, 'abs')
def mod(exp): return math_func(exp, 'mod')
def log(exp): return math_func(exp, 'log')
def log2(exp): return math_func(exp, 'log2')
def log10(exp): return math_func(exp, 'log10')
def exp(exp): return math_func(exp, 'exp')
def sqrt(exp): return math_func(exp, 'sqrt')
def mod(exp, divisor): return math_func(exp, 'mod', divisor)
def int(exp): return math_func(exp, 'int')
def sign(exp): return math_func(exp, 'sign')


# Descriptive functions
def max(exp, *args): return math_func(exp, 'max', *args)
def min(exp, *args): return math_func(exp, 'min', *args)


# Trigonometric functions
def sin(exp): return math_func(exp, 'sin')
def cos(exp): return math_func(exp, 'cos')
def tan(exp): return math_func(exp, 'tan')

