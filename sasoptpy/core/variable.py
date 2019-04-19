



class Variable(Expression):
    """
    Creates an optimization variable to be used inside models

    Parameters
    ----------
    name : string
        Name of the variable
    vartype : string, optional
        Type of the variable
    lb : float, optional
        Lower bound of the variable
    ub : float, optional
        Upper bound of the variable
    init : float, optional
        Initial value of the variable
    abstract : boolean, optional
        Indicator of whether the variable is abstract or not
    shadow : boolean, optional
        Indicator of whether the variable is shadow or not\
        Used for internal purposes

    Examples
    --------

    >>> x = so.Variable(name='x', lb=0, ub=20, vartype=so.CONT)
    >>> print(repr(x))
    sasoptpy.Variable(name='x', lb=0, ub=20, vartype='CONT')

    >>> y = so.Variable(name='y', init=1, vartype=so.INT)
    >>> print(repr(y))
    sasoptpy.Variable(name='y', lb=0, ub=inf, init=1, vartype='INT')

    See also
    --------
    :func:`sasoptpy.Model.add_variable`

    """

    def __init__(self, name, vartype=None, lb=-inf, ub=inf,
                 init=None, abstract=False, shadow=False, key=None):
        super().__init__()
        if vartype is None:
            vartype = sasoptpy.CONT
        if not shadow:
            name = sasoptpy.utils.check_name(name, 'var')
        self._name = name
        self._type = vartype
        if lb is None:
            lb = -inf
        if ub is None:
            ub = inf
        self._lb = lb
        self._ub = ub
        self._init = init
        if self._init is not None:
            self._value = self._init
        if vartype == sasoptpy.BIN:
            self._lb = max(self._lb, 0)
            self._ub = min(self._ub, 1)
        if shadow:
            self._linCoef[name + str(id(self))] = {'ref': self, 'val': 1}
        else:
            self._linCoef[name] = {'ref': self, 'val': 1}
            self._objorder = sasoptpy.utils.register_name(name, self)
        self._key = key
        self._parent = None
        self._temp = False
        self._abstract = abstract
        self._shadow = shadow

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    @sasoptpy.structures.containable
    def set_bounds(self, *, lb=None, ub=None):
        """
        Changes bounds on a variable

        Parameters
        ----------
        lb : float
            Lower bound of the variable
        ub : float
            Upper bound of the variable

        Examples
        --------

        >>> x = so.Variable(name='x', lb=0, ub=20)
        >>> print(repr(x))
        sasoptpy.Variable(name='x', lb=0, ub=20, vartype='CONT')
        >>> x.set_bounds(lb=5, ub=15)
        >>> print(repr(x))
        sasoptpy.Variable(name='x', lb=5, ub=15, vartype='CONT')

        """
        if lb is not None:
            self._lb = lb
        if ub is not None:
            self._ub = ub

    def set_init(self, init=None):
        """
        Changes initial value of a variable

        Parameters
        ----------
        init : float or None
            Initial value of the variable

        Examples
        --------

        >>> x = so.Variable(name='x')
        >>> x.set_init(5)

        >>> y = so.Variable(name='y', init=3)
        >>> y.set_init()

        """
        self._init = init

    def get_value(self):
        """
        Returns value of a variable
        """
        return self._value

    def set_value(self, value):
        """
        Sets the value of a variable
        """
        self._value = value

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        st = 'sasoptpy.Variable(name=\'{}\', '.format(self._name)
        if self._lb is not 0:
            st += 'lb={}, '.format(self._lb)
        if self._ub is not inf:
            st += 'ub={}, '.format(self._ub)
        if self._init is not None:
            st += 'init={}, '.format(self._init)
        if self._abstract:
            st += 'abstract=True, '
        if self._shadow:
            st += 'shadow=True, '
        st += ' vartype=\'{}\')'.format(self._type)
        return st

    def __str__(self):
        """
        Generates a representation string
        """
        if self._parent is not None and self._key is not None:
            keylist = [i._expr() if isinstance(i, Expression)
                       else str(i) for i in self._key]
            key = ', '.join(keylist)
            return ('{}[{}]'.format(self._parent._name, key))
        if self._shadow and self._iterkey:
            keylist = [i._expr() if isinstance(i, Expression)
                       else str(i) for i in self._iterkey]
            key = ', '.join(keylist)
            return('{}[{}]'.format(self._name, key))
        return('{}'.format(self._name))

    def _expr(self):
        if self._parent is not None and self._key is not None:
            keylist = sasoptpy.utils._to_iterator_expression(self._key)
            key = ', '.join(keylist)
            return ('{}[{}]'.format(self._parent._name, key))
        if self._shadow and self._iterkey:
            keylist = sasoptpy.utils._to_iterator_expression(self._iterkey)
            key = ', '.join(keylist)
            return('{}[{}]'.format(self._name, key))
        return('{}'.format(self._name))

    def _defn(self):
        s = 'var {}'.format(self._name)
        BIN = sasoptpy.BIN
        CONT = sasoptpy.CONT
        if self._type != CONT:
            if self._type == BIN:
                s += ' binary'
            else:
                s += ' integer'
        if self._lb != -inf:
            if not (self._lb == 0 and self._type == BIN):
                s += ' >= {}'.format(self._lb)
        if self._ub != inf:
            if not (self._ub == 1 and self._type == BIN):
                s += ' <= {}'.format(self._ub)
        if self._init is not None:
            s += ' init {}'.format(self._init)
        s += ';'
        return(s)