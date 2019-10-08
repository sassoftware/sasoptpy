import sasoptpy
from sasoptpy.core import Expression


class Objective(Expression):
    """
    """

    @sasoptpy.class_containable
    def __init__(self, exp, name, sense=None):
        super().__init__(exp=exp, name=name)
        if sense is None:
            sense = sasoptpy.MIN
        self._sense = sense

    def _defn(self):
        return self._sense.lower() + ' ' + \
               self.get_name() + ' = ' + self._expr() + ';'

    def get_sense(self):
        return self._sense

    def set_sense(self, sense):
        self._sense = sense
