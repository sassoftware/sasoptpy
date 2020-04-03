
from collections import OrderedDict
import sasoptpy
from .condition import Conditional, Condition

class SetIterator(sasoptpy.Expression):
    """
    Creates an iterator object for a given Set

    Parameters
    ----------
    initset : :class:`Set`
        Set to be iterated on
    name : string, optional
        Name of the iterator
    datatype : string, optional
        Type of the iterator

    Notes
    -----

    - :class:`abstract.SetIterator` objects are created automatically when
      iterating over a :class:`abstract.Set` object

    Examples
    --------

    >>> S = so.Set(name='S')
    >>> for i in S:
    ...     print(i.get_name(), type(i))
    o19 <class 'sasoptpy.abstract.set_iterator.SetIterator'>

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
        self.sym = Conditional(self)

    def get_set(self):
        return self._set

    def get_type(self):
        return self._type

    def __hash__(self):
        return hash('{}'.format(id(self)))

    def _get_for_expr(self):
        return '{} in {}'.format(self._expr(),
                                 sasoptpy.to_expression(self._set))

    def _expr(self):
        return self.get_name()

    def __str__(self):
        return self._name

    def _defn(self):
        return self._get_for_expr()

    def __repr__(self):
        s = 'sasoptpy.SetIterator({}, name=\'{}\')'.format(self._set, self.get_name())
        return s

    # def _cond_expr(self):
    #     return '<' + self._expr() + '>'

    def __lt__(self, other):
        return Condition(self, '<', other)

    def __gt__(self, other):
        return Condition(self, '>', other)

    def __le__(self, other):
        return Condition(self, '<=', other)

    def __ge__(self, other):
        return Condition(self, '>=', other)

    def __eq__(self, other):
        return Condition(self, 'EQ', other)

    def __ne__(self, other):
        return Condition(self, 'NE', other)


class SetIteratorGroup(OrderedDict, sasoptpy.Expression):
    """
    Creates a group of set iterator objects for multi-dimensional sets

    Parameters
    ----------
    initset : :class:`Set`
        Set to be iterated on
    names : string, optional
        Names of the iterators
    datatype : string, optional
        Types of the iterators

    Examples
    --------

    >>> T = so.Set(name='T', settype=[so.STR, so.NUM])
    >>> for j in T:
    ...     print(j.get_name(), type(j))
    ...     for k in j:
    ...         print(k.get_name(), type(k))
    o5 <class 'sasoptpy.abstract.set_iterator.SetIteratorGroup'>
    o6 <class 'sasoptpy.abstract.set_iterator.SetIterator'>
    o8 <class 'sasoptpy.abstract.set_iterator.SetIterator'>

    """

    def __init__(self, initset, datatype=None, names=None):
        super(SetIteratorGroup, self).__init__()
        self._objorder = sasoptpy.util.get_creation_id()
        self._name = sasoptpy.util.get_next_name()
        self._set = initset
        self._init_members(names, datatype)
        self.sym = sasoptpy.abstract.Conditional(self)

    def _init_members(self, names, datatype):
        if names is not None:
            for i, name in enumerate(names):
                dt = datatype[i] if datatype is not None else None
                it = SetIterator(None, name=name, datatype=dt)
                self.append(it)
        else:
            for i in datatype:
                it = SetIterator(None, datatype=i)
                self.append(it)

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            if isinstance(key, int):
                return list(self.values())[key]

    def get_name(self):
        return self._name

    def append(self, object):
        name = object.get_name()
        self[name] = object

    def _get_for_expr(self):
        #return '<{}> in {}'.format(self._expr(), self._set._name)
        comb = '<' + ', '.join(str(i) for i in self.values()) + '>'
        s = '{} in {}'.format(comb, sasoptpy.to_expression(self._set))
        return s

    def _expr(self):
        return ', '.join(str(i) for i in self.values())

    def _defn(self):
        return self._get_for_expr()


    def __iter__(self):
        for i in self.values():
            yield i

    def __repr__(self):
        return 'sasoptpy.SetIteratorGroup({}, datatype=[{}], names=[{}])'.format(
            self._set,
            ', '.join('\'' + i.get_type() + '\'' for i in self.values()),
            ', '.join('\'' + i.get_name() + '\'' for i in self.values())
        )

    def __str__(self):
        s = ', '.join(str(i) for i in self.values())
        return '(' + s + ')'

    def __hash__(self):
        hashstr = ','.join(str(id(i)) for i in self.values())
        return hash(hashstr)
