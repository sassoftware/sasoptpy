


class Constraint(Expression):
    """
    Creates a linear or quadratic constraint for optimization models

    Constraints should be created by adding logical relations to
    :class:`Expression` objects.

    Parameters
    ----------
    exp : Expression
        A logical expression that forms the constraint
    direction : string
        Direction of the logical expression, 'E' (=), 'L' (<=) or 'G' (>=)
    name : string, optional
        Name of the constraint object
    crange : float, optional
        Range for ranged constraints

    Examples
    --------

    >>> x = so.Variable(name='x')
    >>> y = so.Variable(name='y')
    >>> c1 = so.Constraint( 3 * x - 5 * y <= 10, name='c1')
    >>> print(repr(c1))
    sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

    >>> c2 = so.Constraint( - x + 2 * y - 5, direction='L', name='c2')
    sasoptpy.Constraint( -  x  +  2.0 * y  <=  5, name='c2')

    Notes
    -----

    * A constraint can be generated in multiple ways:

      1. Using the :func:`sasoptpy.Model.add_constraint` method

         >>> m = so.Model(name='m')
         >>> c1 = m.add_constraint(3 * x - 5 * y <= 10, name='c1')
         >>> print(repr(c1))
         sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

      2. Using the constructor

         >>> c1 = sasoptpy.Constraint(3 * x - 5 * y <= 10, name='c1')
         >>> print(repr(c1))
         sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

    * The same constraint can be included into other models using the
      :func:`Model.include` method.

    See also
    --------
    :func:`sasoptpy.Model.add_constraint`
    """

    def __init__(self, exp, direction=None, name=None, crange=0):
        super().__init__()
        if name is not None:
            name = sasoptpy.utils.check_name(name, 'con')
            self._name = name
            self._objorder = sasoptpy.utils.register_name(name, self)
        else:
            self._name = None
        if exp._name is None:
            self._linCoef = exp._linCoef
        else:
            for m in exp._linCoef:
                self._linCoef[m] = dict(exp._linCoef[m])
        if direction is None:
            self._direction = exp._direction
        else:
            self._direction = direction
        self._range = crange
        self._key = None
        self._parent = None
        self._block = None
        self._temp = False

    def __and__(self, other):
        print('Called!')
        print(self)
        print(other)
        return self

    def update_var_coef(self, var, value):
        """
        Updates the coefficient of a variable inside the constraint

        Parameters
        ----------
        var : Variable
            Variable to be updated
        value : float
            Coefficient of the variable in the constraint

        Examples
        --------

        >>> c1 = so.Constraint(exp=3 * x - 5 * y <= 10, name='c1')
        >>> print(repr(c1))
        sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')
        >>> c1.update_var_coef(x, -1)
        >>> print(repr(c1))
        sasoptpy.Constraint( -  5.0 * y  -  x  <=  10, name='c1')

        See also
        --------
        :func:`sasoptpy.Model.set_coef`

        """
        varname = var._name
        if varname in self._linCoef:
            self._linCoef[varname]['val'] = value
        else:
            self._linCoef[varname] = {'ref': var, 'val': value}

    def set_rhs(self, value):
        """
        Changes the RHS of a constraint

        Parameters
        ----------
        value : float
            New RHS value for the constraint

        Examples
        --------

        >>> x = m.add_variable(name='x')
        >>> y = m.add_variable(name='y')
        >>> c = m.add_constraint(x + 3*y <= 10, name='con_1')
        >>> print(c)
        x  +  3.0 * y  <=  10
        >>> c.set_rhs(5)
        >>> print(c)
        x  +  3.0 * y  <=  5

        """
        self._linCoef['CONST']['val'] = -value

    def set_direction(self, direction):
        """
        Changes the direction of a constraint

        Parameters
        ----------
        direction : string
            Direction of the constraint, 'E', 'L', or 'G' for equal to,
            less than or equal to, and greater than or equal to, respectively

        Examples
        --------

        >>> c1 = so.Constraint(exp=3 * x - 5 * y <= 10, name='c1')
        >>> print(repr(c1))
        sasoptpy.Constraint( 3.0 * x  -  5.0 * y  <=  10, name='c1')
        >>> c1.set_direction('G')
        >>> print(repr(c1))
        sasoptpy.Constraint( 3.0 * x  -  5.0 * y  >=  10, name='c1')

        """
        if direction in ['E', 'L', 'G']:
            self._direction = direction
        else:
            print('WARNING: Cannot change constraint direction {} {}'.format(
                self._name, direction))

    def set_block(self, block_number):
        """
        Sets the decomposition block number for a constraint

        Parameters
        ----------
        block_number : int
            Block number of the constraint

        Examples
        --------

        >>> c1 = m.add_constraints((x + 2 * y[i] <= 5 for i in NODES),
                                   name='c1')
        >>> for i in NODES:
              c1[i].set_block(i)

        """
        self._block = block_number

    def get_value(self, rhs=False):
        """
        Returns the current value of the constraint

        Parameters
        ----------
        rhs : boolean, optional
            Whether constant values (RHS) will be included in the value or not.
            Default is false

        Examples
        --------

        >>> x = so.Variable(name='x', init=2)
        >>> c = so.Constraint(x ** 2 + 2 * x <= 15, name='c')
        >>> print(c.get_value())
        8
        >>> print(c.get_value(rhs=True))
        -7

        """
        v = super().get_value()
        if rhs:
            return v
        else:
            v -= self._linCoef['CONST']['val']
            return v

    def _set_info(self, parent, key):
        self._parent = parent
        self._key = key

    def _defn(self):
        s = ''
        if self._parent is None:
            s = 'con {} : '.format(self._name)
        if self._range != 0:
            s += '{} <= '.format(sasoptpy.utils.get_in_digit_format(- self._linCoef['CONST']['val']))
        s += super()._expr()
        if self._direction == 'E' and self._range == 0:
            s += ' = '
        elif self._direction == 'L':
            s += ' <= '
        elif self._direction == 'G':
            s += ' >= '
        elif self._direction == 'E' and self._range != 0:
            s += ' <= '
        else:
            raise Exception('Constraint has no direction!')
        s += '{}'.format(sasoptpy.utils.get_in_digit_format(- self._linCoef['CONST']['val'] + self._range))
        if self._parent is None:
            s += ';'
            # Currently we switch to frame when blocks are set
            # if self._block:
            #     s += '\n'
            #     s += self._name + '.block = ' + str(self._block) + ';'
        return(s)

    def __str__(self):
        """
        Generates a representation string
        """
        s = super().__str__()
        if self._direction == 'E':
            s += ' == '
        elif self._direction == 'L':
            s += ' <= '
        elif self._direction == 'G':
            s += ' >= '
        else:
            raise Exception('Constraint has no direction!')
        if self._range == 0:
            s += ' {}'.format(- self._linCoef['CONST']['val'])
        else:
            s += ' [{}, {}]'.format(- self._linCoef['CONST']['val'],
                                    - self._linCoef['CONST']['val'] +
                                    self._range)
        return s

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        if self._name is not None:
            st = 'sasoptpy.Constraint({}, name=\'{}\')'
            s = st.format(str(self), self._name)
        else:
            st = 'sasoptpy.Constraint({}, name=None)'
            s = st.format(str(self))
        return s