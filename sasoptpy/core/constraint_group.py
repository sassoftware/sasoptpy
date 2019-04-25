
from collections import OrderedDict
from types import GeneratorType

import sasoptpy


class ConstraintGroup:
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

    def __init__(self, argv, name):
        self._condict = OrderedDict()
        self._conlist = []
        if type(argv) == list or type(argv) == GeneratorType:
            self._recursive_add_cons(argv, name=name, condict=self._condict,
                                     conlist=self._conlist)
        if name is not None:
            name = sasoptpy.util.assign_name(name, 'con')
            self._name = name
            self._objorder = sasoptpy.util.register_globally(name, self)
        else:
            self._name = None
        self._shadows = dict()

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

    def _recursive_add_cons(self, argv, name, condict, conlist, ckeys=()):
        conctr = 0

        if sasoptpy.transfer_allowed:
            argv.gi_frame.f_globals.update(sasoptpy._transfer)

        for idx, c in enumerate(argv):
            if type(argv) == list:
                newkeys = ckeys + (idx,)
            elif type(argv) == GeneratorType:
                newkeys = ()
                if argv.gi_code.co_nlocals == 1:
                    vnames = argv.gi_code.co_cellvars
                else:
                    vnames = argv.gi_code.co_varnames
                vdict = argv.gi_frame.f_locals
                for ky in vnames:
                    if ky != '.0':
                        newkeys = newkeys + (vdict[ky],)
            else:
                print('ERROR: Unknown argument type for constraint generation', type(argv))
                return None
            keylist = sasoptpy.core.util._to_iterator_expression(newkeys)
            conname = '{}[{}]'.format(name, ','.join(keylist))
            conname = sasoptpy.util.assign_name(conname, 'con')
            newcon = sasoptpy.Constraint(exp=c, name=conname, crange=c._range)
            condict[newkeys] = newcon
            conlist.append(newkeys)
            conctr += 1
        self._set_con_info()

    def get_expressions(self, rhs=False):
        """
        Returns constraints as a list of expressions

        Parameters
        ----------
        rhs : boolean, optional
            Whether to pass the constant part (rhs) of the constraint or not

        Returns
        -------
        df : :class:`pandas.DataFrame`
            Returns a DataFrame consisting of constraints as expressions

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
        cd_df = sasoptpy.utils.dict_to_frame(cd, cols=[self._name])
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
        item : Constraint
            Reference to the constraint
        """
        if isinstance(key, sasoptpy.data.SetIterator):
            tuple_key = sasoptpy.utils.tuple_pack(key)
            tuple_key = tuple(i for i in sasoptpy.utils.flatten_tuple(tuple_key))
            if tuple_key in self._condict:
                return self._condict[tuple_key]
            elif tuple_key in self._shadows:
                return self._condict[tuple_key]
            else:
                k = list(self._condict)[0]
                c = self._condict[k]
                cname = self._name
                cname = cname.replace(' ', '')
                shadow = Constraint(exp=c, direction=c._direction, name=cname, crange=c._range)
                self._shadows[tuple_key] = shadow
                return shadow
        else:
            key = sasoptpy.utils.tuple_pack(key)
            return self._condict.get(key)

    def __iter__(self):
        for i in self._conlist:
            yield self._condict[i]

    def _set_con_info(self):
        for i in self._condict:
            self._condict[i]._set_info(parent=self, key=i)

    def _get_keys(self):
        return list(self._condict)[0]

    def _defn(self, tabs=''):
        s = ''
        for key_ in self._conlist:
            s += tabs + 'con {}'.format(self._name)
            keys = sasoptpy.util._to_optmodel_loop(key_)
            s += keys
            s += ' : ' + self._condict[key_]._defn()
            s += ';\n'
        return s

    def __str__(self):
        """
        Generates a representation string
        """
        s = 'Constraint Group ({}) [\n'.format(self._name)
        for k in sorted(self._condict):
            v = self._condict[k]
            s += '  [{}: {}]\n'.format(sasoptpy.utils.tuple_unpack(k),
                                       v)
        s += ']'
        return s

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        s = 'sasoptpy.ConstraintGroup(['
        for i in self._condict:
            s += '{}, '.format(str(self._condict[i]))
        s += '], '
        s += 'name=\'{}\')'.format(self._name)
        return s