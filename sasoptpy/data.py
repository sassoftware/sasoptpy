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
Set includes :class:`Set` class and implementations for server-side data
operations

"""


from collections import OrderedDict
from types import GeneratorType

import sasoptpy.components
import sasoptpy.utils


class Parameter:
    """
    Creates a parameter to be represented inside PROC OPTMODEL

    Parameters
    ----------
    name : string
        Name of the parameter
    keys : list, optional
        List of :class:`Set` to be used as keys for multi-index parameters
    init : Expression, optional
        Initial value expression of the parameter
    p_type : string, optional
        Type of the parameter, 'num' or 'str'

    Examples
    --------

    >>> p = so.Parameter('p', init=x + 2*y)
    >>> print(p._defn())
    num p = x + 2 * y;

    >>> I = so.Set('I')
    >>> r = so.Parameter('r', keys=I, p_type='str')
    >>> print(r._defn())
    str r {I};

    See also
    --------
    :func:`read_table`, :meth:`Model.read_table`

    """

    def __init__(self, name, keys=None, order=1, init=None, value=None, p_type=None):
        self._name = sasoptpy.utils.check_name(name, 'param')
        self._objorder = sasoptpy.utils.register_name(self._name, self)
        self._keys = keys if keys is not None else ()
        self._keysize = len(self._keys)
        self._order = order
        self._init = init
        self._value = value
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
            if self._init is not None:
                s = tabs + '{} {} init {}'.format(self._type, self._name,
                                               sasoptpy.utils._to_sas_string(self._init))
            elif self._value is not None:
                s = tabs + '{} {} = {}'.format(self._type, self._name,
                                               sasoptpy.utils._to_sas_string(self._value))
            else:
                s = tabs + '{} {}'.format(self._type, self._name)
        else:
            s = tabs + '{} {} {{'.format(self._type, self._name)
            for k in self._keys:
                s += '{}, '.format(k._name)
            s = s[:-2]
            s += '}'
            if self._init is not None:
                s += ' init {} '.format(sasoptpy.utils._to_sas_string(self._init))
            elif self._value is not None:
                s += ' = {} '.format(sasoptpy.utils._to_sas_string(self._value))
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
                if type(k) == GeneratorType:
                    for i in k:
                        key = 'jj{}'.format(keyctr)
                        keyctr += 1
                        tablekeys.append(key)
                        jkeys.append(key)
                        s += '{} in {}'.format(key, i._set._name)
                elif k not in self._keyset:
                    key = 'j{}'.format(keyctr)
                    tablekeys.append(key)
                    jkeys.append(key)
                    s += '{} in {},'.format(key, k._name)
                elif hasattr(k, '_colname'):
                    if isinstance(k._colname, list):
                        for i in k._colname:
                            tablekeys.append(i)
                    else:
                        tablekeys.append(k._colname)
                else:
                    tablekeys.append(k)
            s += '} '
            s += '<{}['.format(self._name)
            s += ','.join([format(i) for i in tablekeys])
            s += ']=col('
            if self._colname:
                if callable(self._colname):
                    s += self._colname(*jkeys) + '||'
                else:
                    s += '"{}"||'.format(self._colname)
            s += ','.join([format(i) for i in jkeys])
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

    def get_value(self):
        if self._keysize == 0:
            if self._value is not None:
                return self._value
            elif self._init is not None:
                return self._init
            else:
                return None
        else:
            return None


class ParameterValue(sasoptpy.components.Expression):
    """
    Represents a single value of a parameter

    Parameters
    ----------
    param : Parameter
        Parameter that the value belongs to
    key : tuple, optional
        Key of the parameter value in the multi-index parameter
    prefix : string
        Prefix of the parameter
    suffix : string
        Suffix of the parameter, such as ``.lb`` and ``.ub``

    Notes
    -----

    - Parameter values are mainly used in abstract expressions
    """

    def __init__(self, param, key=None, prefix='', suffix=''):
        super().__init__()
        # pvname = sasoptpy.utils._to_bracket(param._name, key)
        self._name = param._name
        tkey = sasoptpy.utils.tuple_pack(key)
        self._key = tkey
        self._abstract = True
        self._prefix = prefix
        self._suffix = suffix
        self._linCoef[str(self)] = {'ref': self,
                                    'val': 1.0}
        self._ref = param
        self._assign = None

    def set_init(self, val):
        """
        Sets the initial value of the parameter

        Parameters
        ----------
        val : Expression
            Initial value

        Examples
        --------

        >>> p = so.Parameter(name='p')
        >>> print(p._defn())
        num p;
        >>> p.set_init(10)
        >>> print(p._defn())
        num p = 10;

        Notes
        -----
        - This method is only available for parameters without index/key.

        """
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
                           self._suffix
        return self._prefix +\
            sasoptpy.utils._to_bracket(self._name, self._key) +\
            self._suffix

    def _expr(self):
        return str(self)

    def get_value(self):
        if self._key == ('',):
            return self._ref.get_value()
        else:
            return None


class Set(sasoptpy.components.Expression):
    """
    Creates an index set to be represented inside PROC OPTMODEL

    Parameters
    ----------
    name : string
        Name of the parameter
    init : Expression, optional
        Initial value expression of the parameter
    settype : list, optional
        List of types for the set, consisting of 'num' and 'str' values

    Examples
    --------

    >>> I = so.Set('I')
    >>> print(I._defn())
    set I;

    >>> J = so.Set('J', settype=['num', 'str'])
    >>> print(J._defn())
    set <num, str> J;

    >>> N = so.Parameter(name='N', init=5)
    >>> K = so.Set('K', init=so.exp_range(1,N))
    >>> print(K._defn())
    set K = 1..N;

    """

    def __init__(self, name, init=None, value=None, settype=['num']):
        super().__init__()
        self._name = sasoptpy.utils.check_name(name, 'set')
        self._objorder = sasoptpy.utils.register_name(self._name, self)
        if init:
            if isinstance(init, range):
                newinit = str(init.start) + '..' + str(init.stop)
                if init.step != 1:
                    newinit = ' by ' + init.step
                init = newinit
            #elif isinstance(init, list):
            #    init = '[' + ' '.join([str(i) for i in init]) + ']'
            else:
                pass
        self._init = init
        self._value = value
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
            s += ' init ' + sasoptpy.utils._to_sas_string(self._init) #str(self._init)
        elif self._value is not None:
            s += ' = ' + sasoptpy.utils._to_sas_string(self._value)
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

    def value(self):
        return self._value

class SetIterator(sasoptpy.components.Expression):
    """
    Creates an iterator object for a given Set

    Parameters
    ----------
    initset : Set
        Set to be iterated on
    conditions : list, optional
        List of conditions on the iterator
    datatype : string, optional
        Type of the iterator
    group : dict, optional
        Dictionary representing the order of iterator inside multi-index sets
    multi_index : boolean, optional
        Switch for representing multi-index iterators

    Notes
    -----

    - SetIterator objects are automatically created when looping over a
      :class:`Set`.
    - This class is mainly intended for internal use.
    - The ``group`` parameter consists of following keys

      - **order** : int
        Order of the parameter inside the group
      - **outof** : int
        Total number of indices inside the group
      - **id** : int
        ID number assigned to group by Python

    """

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
    """
    Creates a dictionary of :class:`Expression` objects

    Parameters
    ----------
    name : string
        Name of the object

    Examples
    --------

    >>> e[0] = x + 2*y
    >>> e[1] = 2*x + y**2
    >>> print(e.get_keys())
    >>> for i in e:
    >>>     print(i, e[i])
    (0,) x + 2 * y
    (1,) 2 * x + (y) ** (2)


    Notes
    -----
    - ExpressionDict is the underlying class for :class:`ImplicitVar`.
    - It behaves as a regular dictionary for client-side models.
    """

    def __init__(self, name=None):
        name = sasoptpy.utils.check_name(name, 'impvar')
        self._name = name
        self._objorder = sasoptpy.utils.register_name(name, self)
        self._dict = OrderedDict()
        self._conditions = []
        self._shadows = OrderedDict()
        self._abstract = False

    def __setitem__(self, key, value):
        key = sasoptpy.utils.tuple_pack(key)

        # Set name for named types
        ntypes = [Parameter, sasoptpy.components.Expression]
        if any(isinstance(value, i) for i in ntypes) and value._name is None:
            value._name = self._name

        # Add the dictionary value
        if isinstance(value, Parameter):
            self._dict[key] = ParameterValue(value, key)
        elif isinstance(value, sasoptpy.components.Expression):
            self._dict[key] = value
            if value._abstract:
                self._abstract = True
        else:
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

    def get_keys(self):
        """
        Returns the dictionary keys

        Returns
        -------
        d : dict_keys
            Dictionary keys stored in the object
        """
        return self._dict.keys()

    def __iter__(self):
        return self._dict.__iter__()

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
    """
    Creates an implicit variable

    Parameters
    ----------
    argv : Generator, optional
        Generator object for the implicit variable
    name : string, optional
        Name of the implicit variable

    Notes
    -----

    - If the loop inside generator is over an abstract object, a definition
      for the object will be created inside :meth:`Model.to_optmodel` method.

    Examples
    --------

    Regular Implicit Variable

    >>> I = range(5)
    >>> x = so.Variable(name='x')
    >>> y = so.VariableGroup(I, name='y')
    >>> z = so.ImplicitVar((x + i * y[i] for i in I), name='z')
    >>> for i in z:
    >>>     print(i, z[i])
    (0,) x
    (1,) x + y[1]
    (2,) x + 2 * y[2]
    (3,) x + 3 * y[3]
    (4,) x + 4 * y[4]

    Abstract Implicit Variable

    >>> I = so.Set(name='I')
    >>> x = so.Variable(name='x')
    >>> y = so.VariableGroup(I, name='y')
    >>> z = so.ImplicitVar((x + i * y[i] for i in I), name='z')
    >>> print(z._defn())
    impvar z {i_1 in I} = x + i_1 * y[i_1];
    >>> for i in z:
    >>>     print(i, z[i])
    (sasoptpy.data.SetIterator(name=i_1, ...),) x + i_1 * y[i_1]

    """

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
