import sasoptpy
from sasoptpy.core import Expression


class Objective(Expression):
    """
    Objective represents expressions with sense and used as target value in
    optimization

    Parameters
    ----------
    exp : :class:`Expression`
        Objective as an expression
    name : string
        Unique name of the expression
    sense : string, optional
        Direction of the objective, sasoptpy.MIN (default) or sasoptpy.MAX

    Examples
    --------

    >>> m = so.Model(name='test_objective')
    >>> x = m.add_variable(name='x')
    >>> obj = m.set_objective(2 * x - x ** 3, sense=so.MIN, name='new_obj')
    >>> str(m.get_objective())
    2 * x - (x) ** (3)
    >>> type(obj)
    sasoptpy.Objective

    """

    @sasoptpy.class_containable
    def __init__(self, exp, name, sense=None, **kwargs):
        super().__init__(exp=exp, name=name)
        if sense is None:
            sense = sasoptpy.MIN
        self._sense = sense
        self._default = kwargs.get('default', False)

    def _defn(self):
        return self._sense.lower() + ' ' + \
               self.get_name() + ' = ' + self._expr() + ';'

    def is_default(self):
        return self._default

    def get_sense(self):
        """
        Returns the objective sense (direction)
        """
        return self._sense

    def set_sense(self, sense):
        """
        Specifies the objective sense (direction)

        Parameters
        ----------
        sense : string
            sasoptpy.MIN or sasoptpy.MAX
        """
        self._sense = sense
