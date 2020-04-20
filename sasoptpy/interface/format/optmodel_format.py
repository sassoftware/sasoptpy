
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
    multi_obj = False

    # Based on creation order
    s = ''
    if header:
        s = 'proc optmodel;\n'
    body = ''

    all_components_dict = {
        **model._setDict,
        **model._parameterDict,
        **model._statementDict,
        **model._variableDict,
        **model._impvarDict,
        **model._constraintDict,
        **model._objectiveDict,
    }

    all_components = list(all_components_dict.values()) + [model._objective]

    sorted_comp = sorted(all_components, key=lambda i: i._objorder)
    for cm in sorted_comp:
        if (sasoptpy.core.util.is_regular_component(cm)):
            body += cm._defn() + '\n'
            if hasattr(cm, '_member_defn'):
                mdefn = cm._member_defn()
                if mdefn != '':
                    body += mdefn + '\n'

    dropped_comps = ' '.join(list(model._get_dropped_vars().keys()) +
                             list(model._get_dropped_cons().keys()))
    if dropped_comps != '':
        body += mdefn + 'drop ' + dropped_comps + ';\n'

    # Solve block
    if solve:
        body += 'solve'
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
                        multi_obj = True
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
                body += ' ' + ' '.join(pre_opts)
            if pos_opts != '':
                body += ' / ' + ' '.join(pos_opts)
        body += ';\n'

    # Output ODS tables
    if ods:
        body += 'ods output PrintTable=primal_out;\n'

    if parse_results:
        body += 'create data solution from [i]= {1.._NVAR_} var=_VAR_.name value=_VAR_ lb=_VAR_.lb ub=_VAR_.ub rc=_VAR_.rc;\n'

    if ods:
        body += 'ods output PrintTable=dual_out;\n'

    if parse_results:
        body += 'create data dual from [j] = {1.._NCON_} con=_CON_.name value=_CON_.body dual=_CON_.dual;\n'

    if multi_obj:
        body += 'create data allsols from [s]=(1.._NVAR_) name=_VAR_[s].name {j in 1.._NSOL_} <col(\'sol_\'||j)=_VAR_[s].sol[j]>;\n'

    # After-solve statements
    for i in model._postSolveDict.values():
        body += i._defn() + '\n'

    s += sasoptpy.util.addSpaces(body, 3)

    if header:
        s += 'quit;'
    return(s)


def to_optmodel_for_session(workspace, **kwargs):

    header = kwargs.get('header', True)
    parse = kwargs.get('parse', False)
    ods = kwargs.get('ods', False)


    s = ''

    if header:
        s += 'proc optmodel;\n'

    allcomp = workspace.get_elements()

    memberdefs = []
    for cm in allcomp:
        if (sasoptpy.core.util.is_regular_component(cm)):
            component_defn = cm._defn()
            if hasattr(cm, '_member_defn'):
                mdefn = cm._member_defn()
                if mdefn != '':
                    component_defn += '\n' + mdefn
            memberdefs.append(component_defn)

    memberdefs = '\n'.join(memberdefs)
    s += sasoptpy.util.addSpaces(memberdefs, 3)

    if parse:
        parse_str = '\ncreate data solution from [i]= {1.._NVAR_} var=_VAR_.name value=_VAR_ lb=_VAR_.lb ub=_VAR_.ub rc=_VAR_.rc;\n'
        parse_str += 'create data dual from [j] = {1.._NCON_} con=_CON_.name value=_CON_.body dual=_CON_.dual;'
        s += sasoptpy.util.addSpaces(parse_str, 3)

    if header:
        s += '\nquit;'
    return s
