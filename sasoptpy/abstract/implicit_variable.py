
from collections import OrderedDict
from types import GeneratorType

import sasoptpy
import sasoptpy.abstract
from .util import is_abstract
from sasoptpy.core.util import (is_expression)
from sasoptpy.util import to_expression, wrap_expression


class ImplicitVar:
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
    (sasoptpy.abstract.SetIterator(name=i_1, ...),) x + i_1 * y[i_1]

    """

    @sasoptpy.class_containable
    def __init__(self, argv, name=None):
        self._name = name
        self._objorder = sasoptpy.util.get_creation_id()
        self._dict = OrderedDict()
        self._conditions = []
        self._shadows = OrderedDict()
        if argv is not None:
            # Generator type - multi
            if type(argv) == GeneratorType:
                for arg in argv:
                    keynames = ()
                    keyrefs = ()
                    if argv.gi_code.co_nlocals == 1:
                        itlist = argv.gi_code.co_cellvars
                    else:
                        itlist = argv.gi_code.co_cellvars + argv.gi_code.co_varnames
                    localdict = argv.gi_frame.f_locals
                    for i in itlist:
                        if i != '.0':
                            keynames += (i,)
                    for i in keynames:
                        keyrefs += (localdict[i],)
                    self[keyrefs] = wrap_expression(arg)
            elif is_expression(argv):
                exp = wrap_expression(argv)
                exp.set_name(name)
                self[''] = exp
                self['']._objorder = self._objorder
            else:
                exp = sasoptpy.Expression.to_expression(argv)
                exp.set_name(name)
                self[''] = exp
                self['']._objorder = self._objorder

    def _expr(self):
        return self.get_name()

    def _defn(self):
        member_defn = []
        for i in self._dict.values():
            member_defn.append('impvar {} = {};'.format(
                i.get_name_with_keys(name=self.get_name()),
                to_expression(i)))
        s = '\n'.join(member_defn)
        return s

    def __setitem__(self, key, value):
        key = sasoptpy.util.pack_to_tuple(key)
        value.set_permanent()
        value._iterkey = key
        self._dict[key] = value

    def __getitem__(self, key):
        key = sasoptpy.util.pack_to_tuple(key)
        if key in self._dict:
            return self._dict[key]
        elif key in self._shadows:
            return self._shadows[key]
        else:
            tuple_key = sasoptpy.util.pack_to_tuple(key)
            pv = sasoptpy.abstract.ParameterValue(self, tuple_key)
            self._shadows[key] = pv
            return pv

    def get_name(self):
        return self._name

    def get_dict(self):
        return self._dict

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

    def __str__(self):
        return self._name





