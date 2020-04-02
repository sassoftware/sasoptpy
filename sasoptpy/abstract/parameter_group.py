
from collections import OrderedDict

from .parameter import Parameter

import sasoptpy

class ParameterGroup:
    """
    Represents a group of input parameters

    Parameters
    ----------
    index_key : iterable
        Index key of the group members
    name : string
        Name of the parameter group
    ptype : string, optional
        Type of the parameters. Possible values are `sasoptpy.STR` and
        `sasoptpy.NUM`
    value : float, optional
        Value of the parameter
    init : float, optional
        Initial value of the parameter

    Examples
    --------

    >>> from sasoptpy.actions import for_loop
    >>> with so.Workspace('w') as w:
    ...    p = so.ParameterGroup(so.exp_range(1, 6), name='p', init=3)
    ...    p[0].set_value(3)
    ...    S = so.Set(name='S', value=so.exp_range(1, 6))
    ...    for i in for_loop(S):
    ...        p[i].set_value(1)
    ...
    >>> print(so.to_optmodel(w))
    proc optmodel;
       num p {1..5} init 3;
       p[0] = 3;
       set S = 1..5;
       for {o13 in S} do;
          p[o13] = 1;
       end;
    quit;

    """

    @sasoptpy.class_containable
    def __init__(self, *index_key, name, init=None, value=None, ptype=None):
        self._key = list(index_key)
        self._name = name
        self._init = init
        self._value = value
        if ptype is None:
            ptype = sasoptpy.NUM
        self._ptype = ptype
        self._objorder = sasoptpy.util.get_creation_id()
        self._shadows = OrderedDict()

    def get_name(self):
        return self._name

    def get_element_name(self, key):
        keyname = sasoptpy.util.package_utils._to_sas_string(key)
        return '{}[{}]'.format(self.get_name(), keyname)

    def __getitem__(self, key):
        if key in self._shadows:
            return self._shadows[key]
        else:
            try:
                keys = ', '.join(i._expr()
                                 if hasattr(i, '_expr') else str(i) for i in
                                 key)
            except TypeError:
                keys = str(key)
            temp_name = '{}[{}]'.format(self.get_name(), keys)
            pv = Parameter(name=temp_name, internal=True)
            pv.set_parent(self, key=key)
            self._shadows[key] = pv
            return pv

    def __setitem__(self, key, value):
        k = self[key]
        k.set_value(value)
        sasoptpy.abstract.Assignment(self._shadows[key], value)

    def get_type_name_str(self):
        return '{} {}'.format(self._ptype, self.get_name())

    def get_iterator_str(self):
        key_defs = []
        for k in self._key:
            if sasoptpy.abstract.is_key_abstract(k):
                key_defs.append(k._defn())
            else:
                key_defs.append(sasoptpy.to_expression(k))
        return ' {{{}}}'.format(', '.join(key_defs))

    def get_value_init_str(self):
        if self._init is not None:
            return ' init {}'.format(self._init)
        elif self._value is not None:
            return ' = {}'.format(self._value)
        return ''

    def _defn(self):
        type_name_str = self.get_type_name_str()
        iterator_str = self.get_iterator_str()
        value_init_str = self.get_value_init_str()
        s = type_name_str + iterator_str + value_init_str
        s += ';'
        return s

    def _expr(self):
        return self.get_name()
