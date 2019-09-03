
from collections import OrderedDict
import sasoptpy


class SetIterator(sasoptpy.Expression):
    """
    Creates an iterator object for a given Set

    Parameters
    ----------
    initset : Set
        Set to be iterated on
    name : string, optional
        Name of the iterator
    datatype : string, optional
        Type of the iterator

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

    def __init__(self, initset, name=None, datatype=None):
        if name is None:
            name = sasoptpy.util.get_next_name()
        super().__init__(name=name)
        self.set_member(key=name, ref=self, val=1.0)
        self._set = initset
        if datatype is None:
            datatype = sasoptpy.NUM
        self._type = datatype
        self._conditions = []

    def set_name(self, name):
        self._name = name

    def get_type(self):
        return self._type

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
        s = '{} in {}'.format(self._name, sasoptpy.to_expression(self._set))
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

    def _get_for_expr(self):
        return 'for {} in {}'.format(self._expr(), self._set._name)

    def _expr(self):
        return str(self)

    def __str__(self):
        return self._name

    def __repr__(self):
        s = 'sasoptpy.SetIterator({}, name=\'{}\')'.format(self._set, self._name)
        return s


class SetIteratorGroup(OrderedDict):

    def __init__(self, initset, datatype=None, names=None):
        super()
        self._set = initset
        self._init_members(names, datatype)

    def _init_members(self, names, datatype):
        if names is not None:
            for i, name in enumerate(names):
                dt = datatype[i] if datatype is not None else None
                it = SetIterator(None, name=name, datatype=dt)
                self.append(it)

    def append(self, object):
        name = object.get_name()
        self[name] = object

    def _get_for_expr(self):
        return 'for ({}) in {}'.format(self._expr(), self._set._name)

    def _expr(self):
        return ', '.join(str(i) for i in self.values())

    def _defn(self):
        comb = '<' + ', '.join(str(i) for i in self.values()) + '>'
        s = '{} in {}'.format(comb, sasoptpy.to_expression(self._set))

    def __iter__(self):
        for i in self.values():
            yield i

    def __repr__(self):
        return 'sasoptpy.SetIteratorGroup({}, datatype=[{}], names=[{}])'.format(
            self._set,
            ','.join('\'' + i.get_type() + '\'' for i in self.values()),
            ', '.join('\'' + i.get_name() + '\'' for i in self.values())
        )

    def __str__(self):
        s = ', '.join(str(i) for i in self.values())
        return '(' + s + ')'
