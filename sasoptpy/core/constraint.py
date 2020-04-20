#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import sasoptpy
from sasoptpy.core import Expression


class Constraint(Expression):
    """
    Creates a linear or quadratic constraint for optimization models

    Constraints should be created by adding logical relations to
    :class:`Expression` objects.

    Parameters
    ----------
    exp : :class:`Expression`
        A logical expression that forms the constraint
    direction : string, optional
        Direction of the logical expression

        Possible values are

        - `E` for equality (=) constraints
        - `L` for less than or euqal to (<=) constraints
        - `G` for greater than or equal to (>=) constraints

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

    * A constraint can be generated in two different ways:

      - Using the :func:`sasoptpy.Model.add_constraint` method

         >>> m = so.Model(name='m')
         >>> c1 = m.add_constraint(3 * x - 5 * y <= 10, name='c1')
         >>> print(repr(c1))
         sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

      - Using the constructor

         >>> c1 = sasoptpy.Constraint(3 * x - 5 * y <= 10, name='c1')
         >>> print(repr(c1))
         sasoptpy.Constraint( -  5.0 * y  +  3.0 * x  <=  10, name='c1')

    * The same constraint can be included into other models using the
      :func:`Model.include` method.

    See also
    --------
    :func:`sasoptpy.Model.add_constraint`
    """

    @sasoptpy.class_containable
    def __init__(self, exp, direction=None, name=None, crange=None, condition=None):
        super().__init__(name=name)
        if name is not None:
            self._objorder = sasoptpy.util.get_creation_id()

        if exp._name is None:
            self._linCoef = exp.get_member_dict()
        else:
            self._copy_coef(exp)

        if direction is None:
            self._direction = exp._direction
        else:
            self._direction = direction

        if crange is not None:
            self._range = crange
        else:
            self._range = exp._range

        self.add_conditions(condition)

        if sasoptpy.conditions:
            self.add_conditions(sasoptpy.conditions)

        self._key = None
        self._parent = None
        self._block = None
        self._temp = False
        self._shadow = False

    def get_parent_reference(self):
        return self._parent, self._key

    def update_var_coef(self, var, value):
        """
        Updates the coefficient of a variable inside the constraint

        Parameters
        ----------
        var : :class:`Variable`
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
        varname = var.get_name()
        if varname in self._linCoef:
            self._linCoef[varname]['val'] = value
        else:
            self._linCoef[varname] = {'ref': var, 'val': value}

    def set_rhs(self, value):
        """
        Changes the constant value (right-hand side) of a constraint

        Parameters
        ----------
        value : float
            New right-hand side value for the constraint

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
            Direction of the constraint

            Possible values are

            - `E` for equality (=) constraints
            - `L` for less than or euqal to (<=) constraints
            - `G` for greater than or equal to (>=) constraints

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
            raise ValueError(
                'Not a valid constraint direction {}'.format(direction))

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
            When set to `True`, includes constant values to the value of the
            constraint. Default is `False`.

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

    def get_dual(self):
        """
        Returns the dual value if exists

        Returns
        -------
        dual : float
            Dual value of the constraint

        """
        return self._dual

    def add_conditions(self, conditions):
        if conditions is not None:
            for i in conditions:
                self.sym.add_condition(i)

    def _set_info(self, parent, key, shadow=False):
        self._parent = parent
        self._key = key
        self._shadow = shadow

    def __and__(self, other):
        r = sasoptpy.abstract.Condition(left=self, c_type='and', right=other)
        return r

    def __or__(self, other):
        r = sasoptpy.abstract.Condition(left=self, c_type='or', right=other)
        return r

    def __bool__(self):
        if sasoptpy.conditions is not None:
           sasoptpy.conditions.append(self)
        return True

    def __eq__(self, other):
        return id(self) == id(other)

    def _cond_expr(self):
        return self._get_constraint_expr()

    def _get_optmodel_name(self):
        if self._parent is not None:
            return self.get_parent_reference()[0].get_name() + \
                   sasoptpy.util.package_utils._to_optmodel_loop(
                           self._key, self)
        else:
            return self._name

    def _get_definition_tag(self):
        if self._parent is None:
            return 'con {} : '.format(self.get_name())
        return ''

    def get_range_expr(self):
        if self._range != 0:
            return '{} <= '.format(
                sasoptpy.util.get_in_digit_format(
                    -self.get_member_value('CONST')
                )
            )
        return ''

    def get_right_sign(self):
        if self._range != 0 and self._direction == 'E':
            return ' {} '.format(sasoptpy.util.get_direction_str('L'))
        else:
            return ' {} '.format(
            sasoptpy.util.get_direction_str(self._direction))

    def _expr(self):
        return self._get_constraint_expr()

    def _get_constraint_expr(self):
        left_expr = self.get_range_expr()
        expr = super()._expr()
        right_sign = self.get_right_sign()
        constant_side = '{}'.format(
            sasoptpy.util.get_in_digit_format(
                -self.get_member_value('CONST') + self._range))
        return left_expr + expr + right_sign + constant_side

    def _get_name_list(self):
        from sasoptpy.util.package_utils import \
            get_subindices, get_subindices_optmodel_format, \
            get_iterators, get_iterators_optmodel_format, _insert_brackets

        if self._key:
            group_types = self._parent.get_group_types()
            abstract_keys = [i[1] for i in enumerate(self._key)
                             if group_types[i[0]] == sasoptpy.ABSTRACT]
            concrete_keys = [i[1] for i in enumerate(self._key)
                             if group_types[i[0]] == sasoptpy.CONCRETE]

            parent_name = self._parent.get_name()
            iterators_exp = get_iterators_optmodel_format(abstract_keys)
            subindex_exp = get_subindices_optmodel_format(concrete_keys)
            con_name = _insert_brackets(parent_name + subindex_exp, tuple(abstract_keys))
            if iterators_exp == '':
                return [con_name]
            else:
                return [iterators_exp + ' ' + con_name]
        else:
            return [self._name]

    def _defn(self):
        s = self._get_definition_tag()
        s += self._get_constraint_expr()
        if self._parent is None:
            s += ';'
        return s

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
        elif self._direction == 'NE':
            s += ' ne '
        else:
            try:
                s += ' ' + sasoptpy._relation_dict[self._direction] + ' '
            except:
                raise ValueError('Constraint has no direction')
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
