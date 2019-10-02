
from .set_iterator import SetIterator, SetIteratorGroup
import sasoptpy


class Set:
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

    @sasoptpy.class_containable
    def __init__(self, name, init=None, value=None, settype=None):
        self._name = name
        if name is not None:
            self._objorder = sasoptpy.util.get_creation_id()
        if init:
            if isinstance(init, range):
                newinit = str(init.start) + '..' + str(init.stop)
                if init.step != 1:
                    newinit = ' by ' + init.step
                init = newinit
            else:
                pass
        self._init = init
        self._value = value
        if settype is None:
            settype = ['num']
        self._type = sasoptpy.util.pack_to_list(settype)
        self._colname = sasoptpy.util.pack_to_list(name)
        self._iterators = []

    @classmethod
    def from_object(cls, obj):
        return Set(name=None, value=obj)

    def get_name(self):
        return self._name

    def __iter__(self):
        if len(self._type) > 1:
            s = SetIteratorGroup(self, datatype=self._type)
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
        s += self.get_name()
        if self._init is not None:
            s += ' init ' + sasoptpy.util.package_utils._to_sas_string(self._init) #str(self._init)
        elif self._value is not None:
            s += ' = ' + sasoptpy.util.package_utils._to_sas_string(self._value)
        s += ';'
        return(s)

    def __hash__(self):
        return hash(self.get_name())

    def __eq__(self, other):
        if isinstance(other, Set):
            return self.get_name() == other.get_name()
        else:
            return False

    def __contains__(self, item):
        from .util import is_conditional_value
        if is_conditional_value(item):
            return item.__contains__(self)
        else:
            raise RuntimeError('Cannot verify if value is in abstract set')

    def __str__(self):
        s = self.get_name()
        return('{}'.format(s))

    def __repr__(self):
        s = 'sasoptpy.abstract.Set(name={}, settype={})'.format(
            self.get_name(), self._type)
        return(s)

    def _expr(self):
        if self.get_name() is not None:
            return self.get_name()
        else:
            return sasoptpy.to_expression(self._value)

    def value(self):
        return self._value

