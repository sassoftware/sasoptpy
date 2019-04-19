

from abc import ABC, abstractmethod

class Shadow(ABC):

    def __init__(self):
        return

    @abstractmethod
    def _expr(self):
        pass


class ShadowVariable(Shadow, Variable):

    def __init__(self):
        super(Variable, self).__init__()
        print(self._linCoef)

    def _expr(self):
        return self._name


class ShadowConstraint(Shadow, Constraint):

    def __init__(self):
        super(Constraint, self).__init__()

    def _expr(self):
        return self._name
