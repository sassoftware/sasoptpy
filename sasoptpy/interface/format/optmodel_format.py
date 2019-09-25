
from math import inf

import numpy as np
import pandas as pd

import sasoptpy

def to_optmodel(caller, **kwargs):
    if sasoptpy.util.is_model(caller):
        return to_optmodel_for_solve(caller, **kwargs)
    elif sasoptpy.util.is_workspace(caller):
        return to_optmodel_for_session(caller, **kwargs)


def to_optmodel_for_solve(model, **kwargs):
    solve_option_keys = ('with', 'obj', 'objective', 'noobj', 'noobjective', 'relaxint', 'primalin')

    header = kwargs.get('header', True)
    ods = kwargs.get('ods', False)
    solve = kwargs.get('solve', True)
    options = kwargs.get('options', dict())
    primalin = kwargs.get('primalin', False)
    parse_results = kwargs.get('parse', False)

    # Based on creation order
    s = ''
    if header:
        s = 'proc optmodel;\n'
    allcomp = (
        model._sets +
        model._parameters +
        model._statements +
        model._vargroups +
        model._variables +
        model._impvars +
        model._congroups +
        model._constraints +
        [model._objective] +
        model._multiobjs
        )
    sorted_comp = sorted(allcomp, key=lambda i: i._objorder)
    for cm in sorted_comp:
        if (sasoptpy.core.util.is_regular_component(cm)):
            s += cm._defn() + '\n'
            if hasattr(cm, '_member_defn'):
                mdefn = cm._member_defn()
                if mdefn != '':
                    s += mdefn + '\n'

    # Solve block
    if solve:
        s += 'solve'
        pre_opts = []
        pos_opts = []

        if primalin:
            options['primalin'] = True

        if options:
            for key, value in options.items():
                if key in solve_option_keys:
                    if key == 'with':
                        pre_opts.append('with ' + options['with'])
                    elif key == 'relaxint' and options[key] is True:
                        pre_opts.append('relaxint')
                    elif key == 'obj' or key == 'objectives':
                        pre_opts.append('obj ({})'.format(' '.join(i.get_name() for i in options[key])))
                    elif key == 'primalin' and options[key] is True:
                        pos_opts.append('primalin')
                        primalin_set = True
                else:
                    if type(value) is dict:
                        pos_opts.append('{}=('.format(key) + ','.join(
                            '{}={}'.format(i, j)
                            for i, j in value.items()) + ')')
                    else:
                        pos_opts.append('{}={}'.format(key, value))

            if pre_opts != '':
                s += ' ' + ' '.join(pre_opts)
            if pos_opts != '':
                s += ' / ' + ' '.join(pos_opts)
        s += ';\n'

    # Output ODS tables
    if ods:
        s += 'ods output PrintTable=primal_out;\n'

    if parse_results:
        s += 'create data solution from [i]= {1.._NVAR_} var=_VAR_.name value=_VAR_ lb=_VAR_.lb ub=_VAR_.ub rc=_VAR_.rc;\n'

    if ods:
        s += 'ods output PrintTable=dual_out;\n'

    if parse_results:
        s += 'create data dual from [j] = {1.._NCON_} con=_CON_.name value=_CON_.body dual=_CON_.dual;\n'

    # After-solve statements
    for i in model._postsolve_statements:
        s += i._defn() + '\n'

    if header:
        s += 'quit;'
    return(s)


def to_optmodel_for_session(workspace, **kwargs):

    header = kwargs.get('header', True)
    s = ''

    if header:
        s += 'proc optmodel;\n'

    allcomp = workspace.get_elements()

    memberdefs = ''
    for cm in allcomp:
        if (sasoptpy.core.util.is_regular_component(cm)):
            memberdefs += cm._defn() + '\n'
            if hasattr(cm, '_member_defn'):
                mdefn = cm._member_defn()
                if mdefn != '':
                    memberdefs += mdefn + '\n'

    s += sasoptpy.util.addSpaces(memberdefs, 4)

    if header:
        s += 'quit;'
    return s