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


from types import GeneratorType

import sasoptpy.components
import sasoptpy.utils


class Parameter:
    '''
    Represents sets inside PROC OPTMODEL
    '''

    def __init__(self, name, keys=None, order=1, init=None, p_type=None):
        self._name = sasoptpy.utils.check_name(name, 'param')
        self._objorder = sasoptpy.utils.register_name(self._name, self)
        self._keys = keys if keys is not None else ()
        self._keysize = len(self._keys)
        self._order = order
        self._init = init
        self._source = None
        self._keyset = None
        self._colname = name
        self._index = None
        self._shadows = {}
        self._type = 'num' if p_type is None else p_type

    def __getitem__(self, key):
        if key in self._shadows:
            return self._shadows[key]
        else:
            pv = ParameterValue(self, key)
            self._shadows[key] = pv
            return pv

    def __setitem__(self, key, item):
        pv = self[key]
        pv._assign = item

    def _set_loop(self, source, keyset, colname=None, index=None):
        self._source = source
        self._keyset = keyset
        self._colname = colname
        self._index = index

    def _expr(self):
        return self._name

    def _defn(self, tabs=None):
        if tabs is None:
            tabs = ''
        if self._keys == ():
            if self._init:
                s = tabs + '{} {} = {}'.format(self._type, self._name,
                                               self._init)
            else:
                s = tabs + '{} {}'.format(self._type, self._name)
        else:
            s = tabs + '{} {} {{'.format(self._type, self._name)
            for k in self._keys:
                s += '{}, '.format(k._name)
            s = s[:-2]
            s += '}'
            if self._init is not None:
                s += ' init {} '.format(self._init)
        s += ';'

        for key in self._shadows:
            sh = self._shadows[key]
            if sh._assign is not None:
                s += '\n'
                has_iterators = False
                iter_list = []
                for i in key:
                    if isinstance(i, SetIterator):
                        has_iterators = True
                        iter_list.append(i._defn())
                if has_iterators:
                    forcond = 'for {'
                    forcond += ', '.join(iter_list)
                    forcond += '} '
                else:
                    forcond = ''
                s += tabs + forcond + str(sh) + ' = ' + str(sh._assign) + ';'

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
            s += '{}={}'.format(self._name, self._colname)
        else:
            s += '{}'.format(self._name)

        return(s)

    def set_init(self, val):
        self._init = val

    def __str__(self):
        return self._name


class ParameterValue(sasoptpy.components.Expression):

    def __init__(self, param, key=None, prefix='', postfix=''):
        super().__init__()
        # pvname = sasoptpy.utils._to_bracket(param._name, key)
        self._name = param._name
        tkey = sasoptpy.utils.tuple_pack(key)
        self._key = tkey
        self._abstract = True
        self._prefix = prefix
        self._postfix = postfix
        self._linCoef[str(self)] = {'ref': self,
                                    'val': 1.0}
        self._ref = param
        self._assign = None

    def set_init(self, val):
        if self._key == ('',):
            self._ref.set_init(val)

    def _tag_constraint(self, *argv):
        pass

    def __repr__(self):
        st = 'sasoptpy.ParameterValue(name=\'{}\', key=[{}])'.format(
            self._name, str(self._key))
        return st

    def __str__(self):
        if len(self._key) == 1:
            if isinstance(self._key[0], str):
                if self._key[0] == '':
                    return self._prefix +\
                           self._name +\
                           self._postfix
        return self._prefix +\
            sasoptpy.utils._to_bracket(self._name, self._key) +\
            self._postfix

    def _expr(self):
        return str(self)


class Set(sasoptpy.components.Expression):
    '''
    Represents index sets inside PROC OPTMODEL
    '''

    def __init__(self, name, init=None, settype=['num']):
        super().__init__()
        self._name = sasoptpy.utils.check_name(name, 'set')
        self._objorder = sasoptpy.utils.register_name(self._name, self)
        if init:
            if isinstance(init, range):
                newinit = str(init.start) + '..' + str(init.stop)
                if init.step != 1:
                    newinit = ' by ' + init.step
                init = newinit
            elif isinstance(init, list):
                init = '[' + ' '.join([str(i) for i in init]) + ']'
        self._init = init
        self._type = sasoptpy.utils.list_pack(settype)
        self._colname = sasoptpy.utils.list_pack(name)
        self._iterators = []
        self._abstract = True
        self._linCoef[str(self)] = {'ref': self,
                                    'val': 1.0}

    def __iter__(self):
        if len(self._type) > 1:
            s = SetIterator(self, datatype=self._type, multi_index=True)
            self._iterators.append(s)
            return iter([s])
        else:
            s = SetIterator(self)
            self._iterators.append(s)
            return iter([s])

    def _defn(self):
        s = 'set '
        if len(self._type) == 1 and self._type[0] == 'num':
            s += ''
        else:
            s += '<' + ', '.join(self._type) + '> '
        s += self._name
        if self._init is not None:
            s += ' = ' + str(self._init)
        s += ';'
        return(s)

    def __hash__(self):
        return hash((self._name))

    def __eq__(self, other):
        if isinstance(other, Set):
            return (self._name) == (other._name)
        else:
            return False

    def __contains__(self, item):
        print('Containts is called: {}'.format(item))
        return True

    def __str__(self):
        s = self._name
        return(s)

    def __repr__(self):
        s = 'sasoptpy.data.Set(name={}, settype={})'.format(
            self._name, self._type)
        return(s)

    def _expr(self):
        return self._name


class SetIterator(sasoptpy.components.Expression):

    def __init__(self, initset, conditions=None, datatype='num',
                 group={'order': 1, 'outof': 1, 'id': 0}, multi_index=False
                 ):
        # TODO use self._name = initset._colname
        super().__init__()
        self._name = sasoptpy.utils.check_name(None, 'i')
        self._linCoef[self._name] = {'ref': self,
                                     'val': 1.0}
        self._set = initset
        self._type = sasoptpy.utils.list_pack(datatype)
        self._children = []
        if len(self._type) > 1 or multi_index:
            for i, ty in enumerate(self._type):
                sc = SetIterator(
                    self, conditions=None, datatype=ty,
                    group={'order': i, 'outof': len(self._type),
                           'id': id(self)}, multi_index=False)
                self._children.append(sc)
        self._order = group['order']
        self._outof = group['outof']
        self._group = group['id']
        self._multi = multi_index
        self._conditions = conditions if conditions else []

    def __hash__(self):
        return hash('{}'.format(id(self)))

    def __add_condition(self, operation, key):
        c = {'type': operation, 'key': key}
        self._conditions.append(c)

    def __contains__(self, key):
        self.__add_condition('IN', key)
        return True

    def __eq__(self, key):
        self.__add_condition('=', key)  # or 'EQ'
        return True

    def __le__(self, key):
        self.__add_condition('<=', key)  # or 'LE'
        return True

    def __lt__(self, key):
        self.__add_condition('<', key)
        return True

    def __ge__(self, key):
        self.__add_condition('>=', key)  # or 'GE'
        return True

    def __gt__(self, key):
        self.__add_condition('>', key)
        return True

    def __ne__(self, key):
        self.__add_condition('NE', key)  # or 'NE'
        return True

    def __and__(self, key):
        self.__add_condition('AND', key)

    def __or__(self, key):
        self.__add_condition('OR', key)

    def _defn(self, cond=0):
        if self._multi:
            comb = '<' + ', '.join(str(i) for i in self._children) + '>'
            s = '{} in {}'.format(comb, self._set._name)
        else:
            s = '{} in {}'.format(self._name, self._set._name)
        if cond and len(self._conditions) > 0:
            s += ':'
            s += self._to_conditions()
        return(s)

    def _to_conditions(self):
        s = ''
        conds = []
        if len(self._conditions) > 0:
            for i in self._conditions:
                c_cond = '{} {} '.format(self._name, i['type'])
                if type(i['key']) == str:
                    c_cond += '\'{}\''.format(i['key'])
                else:
                    c_cond += '{}'.format(i['key'])
                conds.append(c_cond)

            s = ' and '.join(conds)
        else:
            s = ''
        return s

    def _expr(self):
        if self._multi:
            return ', '.join(str(i) for i in self._children)
        return str(self)

    def __str__(self):
        if self._multi:
            print('WARNING: str is called for a multi-index set iterator.')
        return self._name

    def __repr__(self):
        s = 'sasoptpy.data.SetIterator(name={}, initset={}, conditions=['.\
            format(self._name, self._set._name)
        for i in self._conditions:
            s += '{{\'type\': \'{}\', \'key\': \'{}\'}}, '.format(
                i['type'], i['key'])
        s += "], datatype={}, group={{'order': {}, 'outof': {}, 'id': {}}}, multi_index={})".format(
            self._type, self._order, self._outof, self._group, self._multi)
        return(s)


class ExpressionDict:

    def __init__(self, name=None):
        name = sasoptpy.utils.check_name(name, 'impvar')
        self._name = name
        self._objorder = sasoptpy.utils.register_name(name, self)
        self._dict = dict()
        self._conditions = []
        self._shadows = dict()
        self._abstract = False

    def __setitem__(self, key, value):
        key = sasoptpy.utils.tuple_pack(key)
        try:
            if value._name is None:
                value._name = self._name
            if isinstance(value, Parameter):
                self._dict[key] = ParameterValue(value, key)
            elif isinstance(value, sasoptpy.components.Expression):
                self._dict[key] = value
                if value._abstract:
                    self._abstract = True
            else:
                self._dict[key] = value
        except AttributeError:
            self._dict[key] = value

    def __getitem__(self, key):
        key = sasoptpy.utils.tuple_pack(key)
        if key in self._dict:
            return self._dict[key]
        elif key in self._shadows:
            return self._shadows[key]
        else:
            if self._abstract and len(self._dict) <= 1:
                tuple_key = sasoptpy.utils.tuple_pack(key)
                pv = ParameterValue(self, tuple_key)
                self._shadows[key] = pv
                return pv
            else:
                return None

    def _defn(self):
        # Do not return a definition if it is a local dictionary
        s = ''
        if len(self._dict) == 1:
            s = 'impvar {} '.format(self._name)
            if ('',) not in self._dict:
                s += '{'
                key = self._get_only_key()
                s += ', '.join([i._defn() for i in list(key)])
                s += '} = '
            else:
                key = self._get_only_key()
                s += '= '
            item = self._dict[key]
            if isinstance(item, ParameterValue):
                s += self._dict[key]._ref._expr()
            else:
                s += self._dict[key]._expr()
            s += ';'
        #======================================================================
        # else:
        #     s = ''
        #     for key, val in self._dict.items():
        #         ref = self._name + sasoptpy.utils._to_optmodel_loop(key)
        #         s += 'impvar {}'.format(ref)
        #         s += ' = ' + (val._expr()
        #                       if hasattr(val, '_expr') else str(val)) + ';\n'
        #======================================================================
        return s

    def _get_only_key(self):
        return list(self._dict.keys())[0]

    def __str__(self):
        return self._name

    def __repr__(self):
        s = 'sasoptpy.ExpressionDict(name=\'{}\', '.format(self._name)
        if len(self._dict) == 1:
            key = self._get_only_key()
            s += 'expr=('
            try:
                s += self._dict[key]._ref._expr()
            except AttributeError:
                s += str(self._dict[key])
            if ('',) not in self._dict:
                s += ' ' + ' '.join(['for ' + i._defn() for i in list(key)])
            s += ')'
        s += ')'
        return s


class ImplicitVar(ExpressionDict):

    def __init__(self, argv=None, name=None):
        super().__init__(name=name)
        if argv:
            if type(argv) == GeneratorType:
                for arg in argv:
                    keynames = ()
                    keyrefs = ()
                    if argv.gi_code.co_nlocals == 1:
                        itlist = argv.gi_code.co_cellvars
                    else:
                        itlist = argv.gi_code.co_varnames
                    localdict = argv.gi_frame.f_locals
                    for i in itlist:
                        if i != '.0':
                            keynames += (i,)
                    for i in keynames:
                        keyrefs += (localdict[i],)
                    self[keyrefs] = arg
            elif (type(argv) == sasoptpy.components.Expression and
                  argv._abstract):
                self[''] = argv
                self['']._objorder = self._objorder
            elif type(argv) == sasoptpy.components.Expression:
                self[''] = argv
                self['']._objorder = self._objorder
            else:
                print('ERROR: Unrecognized type for ImplicitVar argument: {}'.
                      format(type(argv)))


class Statement:

    def __init__(self, statement, after_solve=False):
        self.statement = statement
        self._name = sasoptpy.utils.check_name(None, None)
        self._objorder = sasoptpy.utils.register_name(self._name, self)
        self._after = after_solve

    def _defn(self):
        return self.statement
