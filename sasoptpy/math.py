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
Math includes the definition of mathematical operations

"""

import math
import sasoptpy.utils


func_equivalent = {
    'abs': abs,
    'log': math.log,
    'log2': math.log2,
    'log10': math.log10,
    'exp': math.exp,
    'sqrt': math.sqrt,
    'mod': lambda x,y: divmod(x,y)[1],
    'int': int,
    'sign': lambda x: math.copysign(1, x),
    'max': max,
    'min': min,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan
}


def math_func(exp, op, *args):
    """
    Function wrapper for math functions

    Parameters
    ----------
    exp : Expression
        Expression where the math func will be applied
    op : string
        String representation of the math function
    args : float, optional
        Additional arguments
    """
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
def abs(exp):
    """
    Absolute value function
    """
    return math_func(exp, 'abs')


def log(exp):
    """
    Natural logarithm function
    """
    return math_func(exp, 'log')


def log2(exp):
    """
    Logarithm function to the base 2
    """
    return math_func(exp, 'log2')


def log10(exp):
    """
    Logarithm function to the base 10
    """
    return math_func(exp, 'log10')


def exp(exp):
    """
    Exponential function
    """
    return math_func(exp, 'exp')


def sqrt(exp):
    """
    Square root function
    """
    return math_func(exp, 'sqrt')


def mod(exp, divisor):
    """
    Modulo function

    Parameters
    ----------
    exp : Expression
        Dividend
    divisor : Expression
        Divisor
    """
    return math_func(exp, 'mod', divisor)


def int(exp):
    """
    Integer value function
    """
    return math_func(exp, 'int')


def sign(exp):
    """
    Sign value function
    """
    return math_func(exp, 'sign')


# Descriptive functions
def max(exp, *args):
    """
    Largest value function
    """
    return math_func(exp, 'max', *args)


def min(exp, *args):
    """
    Smallest value function
    """
    return math_func(exp, 'min', *args)


# Trigonometric functions
def sin(exp):
    """
    Sine function
    """
    return math_func(exp, 'sin')


def cos(exp):
    """
    Cosine function
    """
    return math_func(exp, 'cos')


def tan(exp):
    """
    Tangent function
    """
    return math_func(exp, 'tan')
