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
import sasoptpy.util


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
    'tan': math.tan,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh
}


def math_func(exp, op, *args):
    """
    Function wrapper for math functions

    Parameters
    ----------
    exp : :class:`Expression`
        Expression where the math function will be applied
    op : string
        String representation of the math function
    args : float, optional
        Additional arguments
    """
    exp = sasoptpy.util.get_mutable(exp)
    exp._operator = op
    for arg in args:
        exp._arguments.append(arg)
    r = sasoptpy.util.wrap_expression(exp)
    return r


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
    Logarithm function in base 2
    """
    return math_func(exp, 'log2')


def log10(exp):
    """
    Logarithm function in base 10
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
    exp : :class:`Expression`
        Dividend
    divisor : :class:`Expression`
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


def sinh(exp):
    """
    Hyperbolic sine function
    """
    return math_func(exp, 'sinh')


def cosh(exp):
    """
    Hyperbolic cosine function
    """
    return math_func(exp, 'cosh')


def tanh(exp):
    """
    Hyperbolic tangent function
    """
    return math_func(exp, 'tanh')

