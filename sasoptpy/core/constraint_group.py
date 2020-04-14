
from collections import OrderedDict
from types import GeneratorType

import sasoptpy
from sasoptpy.libs import pd
from sasoptpy.core import Group


class ConstraintGroup(Group):
    """
    Creates a group of :class:`Constraint` objects

    Parameters
    ----------
    argv : Generator-type object
        A Python generator that includes :class:`Expression` objects
    name : string, optional
        Name (prefix) of the constraints

    Examples
    --------

    >>> var_ind = ['a', 'b', 'c', 'd']
    >>> u = so.VariableGroup(var_ind, name='u')
    >>> t = so.Variable(name='t')
    >>> cg = so.ConstraintGroup((u[i] + 2 * t <= 5 for i in var_ind), name='cg')
    >>> print(cg)
    Constraint Group (cg) [
      [a:  2.0 * t  +  u['a']  <=  5]
      [b:  u['b']  +  2.0 * t  <=  5]
      [c:  2.0 * t  +  u['c']  <=  5]
      [d:  2.0 * t  +  u['d']  <=  5]
    ]

    >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
    >>> cg2 = so.ConstraintGroup((2 * z[i, j] + 3 * z[i-1, j] >= 2 for i in
                                  [1] for j in ['a', 'b', 'c']), name='cg2')
    >>> print(cg2)
    Constraint Group (cg2) [
      [(1, 'a'):  3.0 * z[0, 'a']  +  2.0 * z[1, 'a']  >=  2]
      [(1, 'b'):  2.0 * z[1, 'b']  +  3.0 * z[0, 'b']  >=  2]
      [(1, 'c'):  2.0 * z[1, 'c']  +  3.0 * z[0, 'c']  >=  2]
    ]

    Notes
    -----
    Use :func:`sasoptpy.Model.add_constraints` when working with a single
    model.

    See also
    --------
    :func:`sasoptpy.Model.add_constraints`
    :func:`sasoptpy.Model.include`

    """

    @sasoptpy.class_containable
    def __init__(self, argv, name):
        super().__init__(name=name)
        self._condict = OrderedDict()
        self._shadows = OrderedDict()
        if type(argv) == list or type(argv) == GeneratorType:
            self._recursive_add_cons(argv, name=name, condict=self._condict)
            self.filter_unique_keys()
        elif argv is None:
            # Empty CG
            self._initialized = False
        else:
            raise(TypeError, "Invalid iterator type for constraint group")

        self._objorder = sasoptpy.util.get_creation_id()

    def get_name(self):
        """
        Returns the name of the constraint group

        Returns
        -------
        name : string
            Name of the constraint group

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> x = m.add_variable(name='x')
        >>> indices = ['a', 'b', 'c']
        >>> y = m.add_variables(indices, name='y')
        >>> c1 = m.add_constraints((x + y[i] <= 4 for i in indices),
                                   name='con1')
        >>> print(c1.get_name())
        con1
        """
        return self._name

    def _get_name_list(self):
        def_names = []
        for i in self._condict.values():
            def_names.extend(i._get_name_list())
        return def_names

    def _recursive_add_cons(self, argv, name, condict, ckeys=()):
        conctr = 0

        for (idx, c) in enumerate(argv):

            if not sasoptpy.core.util.is_constraint(c):
                raise ValueError(
                    'Cannot create constraint from {}'.format(type(c)))

            if type(argv) == list:
                new_keys = ckeys + (idx,)
            elif type(argv) == GeneratorType:
                new_keys = sasoptpy.core.util.get_generator_names(argv)

            key_list = sasoptpy.core.util._to_safe_iterator_expression(new_keys)
            con_name = '{}[{}]'.format(name, ','.join(key_list))
            new_con = sasoptpy.Constraint(exp=c, name=con_name, crange=c._range)
            self[new_keys] = new_con
            conctr += 1

    def get_expressions(self, rhs=False):
        """
        Returns constraints as a list of expressions

        Parameters
        ----------
        rhs : boolean, optional
            When set to `True`, passes the the constant part (rhs) of the
            constraint

        Returns
        -------
        df : :class:`pandas.DataFrame`
            Returns a DataFrame that consists of constraints as expressions

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> var_ind = ['a', 'b', 'c', 'd']
        >>> u = m.add_variables(var_ind, name='u')
        >>> t = m.add_variable(name='t')
        >>> cg = so.ConstraintGroup((u[i] + 2 * t <= 5 for i in var_ind),
                                    name='cg')
        >>> ce = cg.get_expressions()
        >>> print(ce)
                     cg
        a  u[a] + 2 * t
        b  u[b] + 2 * t
        c  u[c] + 2 * t
        d  u[d] + 2 * t
        >>> ce_rhs = cg.get_expressions(rhs=True)
        >>> print(ce_rhs)
                         cg
        a  u[a] + 2 * t - 5
        b  u[b] + 2 * t - 5
        c  u[c] + 2 * t - 5
        d  u[d] + 2 * t - 5

        """
        cd = OrderedDict()
        for i in self._condict:
            cd[i] = self._condict[i].copy()
            if rhs is False:
                cd[i]._linCoef['CONST']['val'] = 0
        cd_df = sasoptpy.util.dict_to_frame(cd, cols=[self._name])
        return cd_df

    def __getitem__(self, key):
        """
        Overloaded method to access individual constraints

        Parameters
        ----------
        key : string or int
            Key of the constraint

        Returns
        -------
        item : :class:`Constraint`
            Reference to the constraint
        """
        key = sasoptpy.util.pack_to_tuple(key)
        if key in self._condict:
            return self._condict[key]

        if key in self._shadows:
            return self._shadows[key]

        return self._get_shadow_if_abstract(key)

    def _get_shadow_if_abstract(self, keys):
        for i, k in enumerate(keys):
            group = self._groups[i]
            if any([sasoptpy.util.is_key_abstract(j) for j in group]):
                continue
            else:
                if k not in group:
                    return None
        # If it reached this part, it is a feasible request
        return self._create_shadow(keys)

    def __setitem__(self, key, value):
        tupled_key = sasoptpy.util.pack_to_tuple(key)
        self._condict[tupled_key] = value
        self._register_keys(tupled_key)
        value._set_info(parent=self, key=tupled_key)

    def _create_shadow(self, key):
        if len(self._condict) == 0:
            return None
        else:
            k = list(self._condict)[0]
            c = self._condict[k]
            cname = self.get_name()
            cname = cname.replace(' ', '')
            shadow = sasoptpy.Constraint(exp=c, direction=c._direction,
                                         name=cname, crange=c._range)
            self._shadows[key] = shadow
            shadow._set_info(parent=self, key=key, shadow=True)
            return shadow

    def __iter__(self):
        for i in self._condict.values():
            yield i
    #
    # def _set_con_info(self):
    #     for i in self._condict:
    #         self._condict[i]._set_info(parent=self, key=i)

    def get_members(self):
        """
        Returns a dictionary of members
        """
        return self._condict

    def get_member_by_name(self, name):
        keys = sasoptpy.abstract.util.get_key_from_name(name)
        return self[keys]

    def get_shadow_members(self):
        return self._shadows

    def get_all_keys(self):
        """
        Returns a list of all keys (indices) in the group
        """
        return list(self._condict.keys()) + list(self._shadows.keys())

    def _defn(self):
        from sasoptpy.util.package_utils import _to_optmodel_loop
        groups = []
        for key_ in self._condict:
            current_constraint = self._condict[key_]
            con_name = self.get_name() + _to_optmodel_loop(key_, current_constraint)
            group_str = 'con {}'.format(con_name)
            group_str += ' : ' + self._condict[key_]._defn()
            group_str += ';'
            groups.append(group_str)
        return '\n'.join(groups)

    def _expr(self):
        return self.get_name()

    def __str__(self):
        """
        Generates a representation string
        """
        s = 'Constraint Group ({}) [\n'.format(self.get_name())
        for k in sorted(self._condict):
            v = self._condict[k]
            s += '  [{}: {}]\n'.format(sasoptpy.util.get_first_member(k), v)
        s += ']'
        return s

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        s = 'sasoptpy.ConstraintGroup(['
        s += ', '.join(str(self._condict[i]) for i in self._condict)
        s += '], '
        s += 'name=\'{}\')'.format(self.get_name())
        return s
