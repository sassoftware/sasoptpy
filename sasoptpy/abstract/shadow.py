
import sasoptpy
from sasoptpy.core import Variable, Constraint
from abc import ABC, abstractmethod

class Shadow(ABC):

    def __init__(self):
        self._abstract = True
        self._shadow = True

    @abstractmethod
    def _expr(self):
        pass


class ShadowVariable(Shadow, Variable):

    def __init__(self, name, **kwargs):
        Variable.__init__(self, name=name, internal=True)
        Shadow.__init__(self)

    def _initialize_self_coef(self):
        self.set_member(key=self._name + str(id(self)), ref=self, val=1)

    def set_group_key(self, vg, key):
        self._parent = vg
        self._iterkey = key
        if not sasoptpy.abstract.util.is_key_abstract(key):
            self._abstract = False

    def _expr(self):
        keylist = sasoptpy.util.package_utils._to_iterator_expression(
            self._iterkey)
        key = ', '.join(keylist)
        self_expr = '{}[{}]'.format(self._name, key)
        return self_expr

class ShadowConstraint(Shadow, Constraint):

    def __init__(self):
        super(Constraint, self).__init__()

    def _expr(self):
        return self._name
