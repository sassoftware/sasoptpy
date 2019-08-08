import sasoptpy
from sasoptpy.util import to_expression
from .set import Set


class AbstractRange(Set):

    def __init__(self, start, end, step=1):
        super().__init__(name=None)
        self._start = start
        self._end = end
        self._step = step

    def _expr(self):
        if self._step == 1:
            return '{}..{}'.format(to_expression(self._start).replace(' ', ''),
                                   to_expression(self._end).replace(' ', ''))
        else:
            return '{}..{} by {}'.format(
                to_expression(self._start),
                to_expression(self._end),
                to_expression(self._step)
            )

    def _defn(self):
        pass

    def __str__(self):
        return self._expr()
