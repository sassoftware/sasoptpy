
from .set_iterator import SetIterator, SetIteratorGroup
from .statement.statement_base import Statement
import sasoptpy
from types import GeneratorType


class Set:
    """
    Creates an index set to be represented inside PROC OPTMODEL

    Parameters
    ----------
    name : string
        Name of the parameter
    init : :class:`Expression`, optional
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

    def __contains__(self, item):
        from .util import is_conditional_value
        if is_conditional_value(item):
            return item.is_in(self)
        else:
            raise RuntimeError('Cannot verify if value is in abstract set')

    def __str__(self):
        s = self.get_name()
        return('{}'.format(s))

    def __repr__(self):
        s = 'sasoptpy.abstract.Set(name={}, settype={}'.format(
            self.get_name(), self._type)
        if self._init:
            s += ', init={}'.format(self._init)
        if self._value:
            s += ', value={}'.format(self._value)
        s += ')'
        return(s)

    def _expr(self):
        if self.get_name() is not None:
            return self.get_name()
        else:
            return sasoptpy.to_expression(self._value)


class InlineSet(Statement):

    def __init__(self, func):
        super().__init__()
        self.sym = sasoptpy.abstract.Conditional(self)
        with sasoptpy.set_container(self, conditions=True):
            res = func()
            for m in res:
                if isinstance(m, tuple):
                    for j in m:
                        self.append(j)
                else:
                    self.append(m)

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        pass

    def _expr(self):
        member_defs = ', '.join(sasoptpy.to_definition(i) for i in self.elements)
        conditions = self.sym.get_conditions_str()
        if conditions != '':
            return f'{{{member_defs}: {conditions}}}'
        else:
            return f'{{{member_defs}}}'

    def __repr__(self):
        s = 'sasoptpy.InlineSet('
        try:
            s += self._expr()
        except:
            s += f'id={id(self)}'
        s += '}'
        return s
