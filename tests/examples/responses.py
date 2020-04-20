"""
This file keeps a copy of expected responses to unit tests.
"""

from inspect import cleandoc
import os
current_dir = os.path.dirname(os.path.abspath(__file__))


def read_file(problem):
    file_path = os.path.join(current_dir, 'responses/{}.sas'.format(problem))
    return open(file_path, 'r').read()


# Food Manufacture 1
fm1 = [
    read_file('food_manufacture_1_0'),
    read_file('food_manufacture_1_1'),
    read_file('food_manufacture_1_2'),
    read_file('food_manufacture_1_3')
]

# Food Manufacture 2
fm2 = [
    read_file('food_manufacture_2')
]

# Factory Planning 1
fp1 = [
    read_file('factory_planning_1')
]

# Factory Planning 2
fp2 = [
    read_file('factory_planning_2')
]

# Manpower Planning
mp = [
    read_file('manpower_planning_0'),
    read_file('manpower_planning_1')
]

# Refinery Optimization
ro = [
    read_file('refinery_optimization')
]

# Mining Optimization
mo = [
    read_file('mining_optimization')
]

# Farm Planning
farmp = [
    read_file('farm_planning')
]

# Economic Planning
econ = [
    read_file('economic_planning_0'),
    read_file('economic_planning_1'),
    read_file('economic_planning_2'),
    read_file('economic_planning_3')
]

# Decentralization
dc = [
    read_file('decentralization_0'),
    read_file('decentralization_1')
]

# Optimal Wedding
ow = [
    read_file('sas_optimal_wedding')
]

# Kidney Exchange
kx = [
    read_file('sas_kidney_exchange_0'),
    read_file('sas_kidney_exchange_1')
]

# Multiobjective
multiobj = [
    read_file('multiobjective')
]

# Curve Fitting
cf = [
    read_file('curve_fitting_0'),
    read_file('curve_fitting_1'),
    read_file('curve_fitting_2'),
    read_file('curve_fitting_3')
]

# Nonlinear 1
nl1 = [
    read_file('nonlinear_1')
]

# Nonlinear 2
nl2 = [
    read_file('nonlinear_2_0'),
    read_file('nonlinear_2_1')
]

least_squares = [
    read_file('least_squares')
]

efficiency_analysis = [
    read_file('efficiency_analysis')
]
