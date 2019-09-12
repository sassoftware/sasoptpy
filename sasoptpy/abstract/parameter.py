
import sasoptpy
from sasoptpy.core import Expression

class Parameter(Expression):

    @sasoptpy.class_containable
    def __init__(self, name, ptype=None, value=None, init=None, **kwargs):
        super().__init__(name=name)
        if name is None:
            name = sasoptpy.util.get_next_name()
        self._name = name
        if ptype is None:
            ptype = sasoptpy.NUM
        self._type = ptype
        self._fix_value = value
        self._init = init
        self._parent = None
        self._initialize_self_coef()
        self._abstract = True

    def set_parent(self, parent, key):
        self._parent = parent
        self._key = key

    def _initialize_self_coef(self):
        self.set_member(key=self._name, ref=self, val=1)

    def set_init(self, value):
        self._init = value

    @sasoptpy.containable
    def set_value(self, value):
        self._fix_value = value

    def _expr(self):
        if self._parent:
            return self._parent.get_element_name(self._key)
        return self._name

    def _defn(self):
        if self._parent:
            return None
        else:
            s = '{} {}'.format(self._type, self._name)
            if self._init:
                s += ' init {}'.format(self._init)
            elif self._fix_value:
                s += ' = {}'.format(self._fix_value)
            s += ';'
            return s

    def __str__(self):
        return self._name
