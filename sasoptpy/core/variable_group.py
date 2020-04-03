
from collections import OrderedDict
from itertools import product
from math import inf
import warnings
from multiprocessing import Pool

import sasoptpy
from sasoptpy.libs import (pd, np)
from sasoptpy.core import (Expression, Variable, Group)


class VariableGroup(Group):
    """
    Creates a group of :class:`Variable` objects

    Parameters
    ----------
    argv : list, dict, int, :class:`pandas.Index`
        Loop index for variable group
    name : string, optional
        Name (prefix) of the variables
    vartype : string, optional
        Type of variables, `BIN`, `INT`, or `CONT`
    lb : list, dict, :class:`pandas.Series`, optional
        Lower bounds of variables
    ub : list, dict, :class:`pandas.Series`, optional
        Upper bounds of variables
    init : float, optional
        Initial values of variables

    Examples
    --------

    >>> PERIODS = ['Period1', 'Period2', 'Period3']
    >>> production = so.VariableGroup(PERIODS, vartype=so.INT,
                                      name='production', lb=10)
    >>> print(production)
    Variable Group (production) [
      [Period1: production['Period1']]
      [Period2: production['Period2']]
      [Period3: production['Period3']]
    ]

    >>> x = so.VariableGroup(4, vartype=so.BIN, name='x')
    >>> print(x)
    Variable Group (x) [
      [0: x[0]]
      [1: x[1]]
      [2: x[2]]
      [3: x[3]]
    ]

    >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z')
    >>> print(z)
    Variable Group (z) [
      [(0, 'a'): z[0, 'a']]
      [(0, 'b'): z[0, 'b']]
      [(0, 'c'): z[0, 'c']]
      [(1, 'a'): z[1, 'a']]
      [(1, 'b'): z[1, 'b']]
      [(1, 'c'): z[1, 'c']]
    ]
    >>> print(repr(z))
    sasoptpy.VariableGroup([0, 1], ['a', 'b', 'c'], name='z')

    Notes
    -----
    * When working with a single model, use the
      :func:`sasoptpy.Model.add_variables` method.
    * If a variable group object is created, it can be added to a model using
      the :func:`sasoptpy.Model.include` method.
    * An individual variable inside the group can be accessed using indices.

      >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
      >>> print(repr(z[0, 'a']))
      sasoptpy.Variable(name='z_0_a', lb=0, ub=10, vartype='CONT')

    See also
    --------
    :func:`sasoptpy.Model.add_variables`
    :func:`sasoptpy.Model.include`

    """

    @sasoptpy.class_containable
    def __init__(self, *argv, name, vartype=None, lb=None,
                 ub=None, init=None):
        if len(argv) == 0:
            raise ValueError('An iterable object or None should be given as '
                             'the first parameter')
        super().__init__(name=name)
        self._vardict = OrderedDict()
        self._shadows = OrderedDict()
        self._keyset = []
        self._abstract = False
        self._lb = None
        self._ub = None

        if vartype is None:
            vartype = sasoptpy.CONT

        self._init = init
        self._type = vartype

        if name is None:
            name = sasoptpy.util.get_next_name()

        self._recursive_add_vars(*argv, name=name,
                                 vartype=vartype, lb=lb, ub=ub, init=init,
                                 vardict=self._vardict)
        self.filter_unique_keys()

        lb, ub = sasoptpy.core.util.get_default_bounds_if_none(vartype, lb, ub)

        self.set_bounds(lb=lb, ub=ub, members=False)
        self._objorder = sasoptpy.util.get_creation_id()

        for arg in argv:

            if isinstance(arg, int):
                self._keyset.append(
                    sasoptpy.util.package_utils._extract_argument_as_list(arg))
            else:
                self._keyset.append(
                    sasoptpy.util.package_utils._extract_argument_as_list(arg))
                if not self._abstract and sasoptpy.util.is_set_abstract(arg):
                    self._abstract = True
                    for _, v in self._vardict.items():
                        v._abstract = True

        self._set_var_info()

    def _process_single_var(self, varkey):

        # for varkey in allcombs:
        current_keys = tuple(k for k in varkey)
        is_shadow = any(sasoptpy.abstract.util.is_abstract(i) for i in varkey)
        varname = sasoptpy.core.util.get_name_from_keys(self.get_name(),
                                                        current_keys)
        self._register_keys(current_keys)

        varlb = sasoptpy.util.extract_list_value(current_keys, self._lb)
        varub = sasoptpy.util.extract_list_value(current_keys, self._ub)
        varin = sasoptpy.util.extract_list_value(current_keys, self._init)

        self.add_member(key=current_keys, name=varname, vartype=self._type,
                        lb=varlb, ub=varub, init=varin, shadow=is_shadow)


    def get_name(self):
        """
        Returns the name of the variable group

        Returns
        -------
        name : string
            Name of the variable group

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> var1 = m.add_variables(4, name='x')
        >>> print(var1.get_name())
        x
        """
        return self._name

    def add_member(self, key, name=None, vartype=None, lb=None,
                   ub=None, init=None, shadow=False):
        """
        (Experimental) Adds a new member to Variable Group
        Notes
        -----
        - This method is mainly intended for internal use.
        """

        key = sasoptpy.util.pack_to_tuple(key)

        if lb is None:
            lb = sasoptpy.util.extract_list_value(key, self._lb)
        if ub is None:
            ub = sasoptpy.util.extract_list_value(key, self._ub)
        if init is None:
            init = sasoptpy.util.extract_list_value(key, self._init)
        if vartype is None:
            vartype = self._type

        if shadow is True:
            variable_class = sasoptpy.abstract.ShadowVariable
            dict_to_add = self._shadows
        else:
            variable_class = Variable
            dict_to_add = self._vardict

        if name is None:
            name = sasoptpy.core.util.get_name_from_keys(self.get_name(), key)
        new_var = variable_class(name=name, lb=lb, ub=ub, init=init,
                                 vartype=vartype)
        dict_to_add[key] = new_var
        new_var.set_parent(self)
        return new_var

    def include_member(self, key, var):
        if sasoptpy.core.util.is_variable(var):
            key = sasoptpy.util.pack_to_tuple(key)
            self._vardict[key] = var

    def set_abstract(self, abstract=True):
        self._abstract = abstract

    def _recursive_add_vars(self, *argv, name, vartype, lb, ub, init,
                            vardict, vkeys=(), shadow=False):

        from sasoptpy.util.package_utils import _extract_argument_as_list

        next_arg = _extract_argument_as_list(argv[0])

        for _, i in enumerate(next_arg):
            if isinstance(i, tuple):
                current_keys = vkeys + i
            else:
                current_keys = vkeys + (i,)

            if sasoptpy.abstract.util.is_abstract(i):
                shadow = True

            if len(argv) == 1:
                varname = sasoptpy.core.util.get_name_from_keys(
                    name, current_keys)

                self._register_keys(current_keys)

                varlb = sasoptpy.util.extract_list_value(current_keys, lb)
                varub = sasoptpy.util.extract_list_value(current_keys, ub)
                varin = sasoptpy.util.extract_list_value(current_keys, init)

                self.add_member(key=current_keys, name=varname, vartype=vartype,
                                lb=varlb, ub=varub, init=varin, shadow=shadow)

            else:
                self._recursive_add_vars(*argv[1:], vardict=vardict,
                                         vkeys=current_keys,
                                         name=name, vartype=vartype,
                                         lb=lb, ub=ub, init=init,
                                         shadow=shadow)

    def _set_var_info(self):
        for i in self._vardict:
            self._vardict[i]._set_info(parent=self, key=i)

    def __getitem__(self, key):
        """
        Overloaded method to access individual variables

        Parameters
        ----------
        key : tuple, string or int
            Key of the variable

        Returns
        -------
        ref : :class:`Variable` or list
            Reference to a single Variable or a list of Variable objects

        """
        if self._abstract or sasoptpy.util.is_key_abstract(key) or sasoptpy.core.util.is_expression(key):
            tuple_key = sasoptpy.util.pack_to_tuple(key)
            tuple_key = tuple(i for i in sasoptpy.util.flatten_tuple(tuple_key))
            if tuple_key in self._vardict:
                return self._vardict[tuple_key]
            elif tuple_key in self._shadows:
                return self._shadows[tuple_key]
            else:
                shadow = sasoptpy.abstract.ShadowVariable(self.get_name())
                shadow.set_group_key(self, tuple_key)
                self._shadows[tuple_key] = shadow
                return shadow

        k = sasoptpy.util.pack_to_tuple(key)
        if k in self._vardict:
            return self._vardict[k]
        else:
            indices_to_filter = []
            filter_values = {}
            list_of_variables = []
            for i, _ in enumerate(k):
                if k[i] != '*':
                    indices_to_filter.append(i)
                    filter_values[i] = sasoptpy.util.pack_to_list(k[i])
            for v in self._vardict:
                eligible = True
                for f in indices_to_filter:
                    if v[f] not in filter_values[f]:
                        eligible = False
                if eligible:
                    list_of_variables.append(self._vardict[v])
            if not list_of_variables:
                warnings.warn('Requested variable group is empty:' +
                              ' {}[{}] ({})'.
                              format(self.get_name(), key, type(key)),
                              RuntimeWarning, stacklevel=2)

            if len(list_of_variables) == 0:
                return None
            return list_of_variables

    def __setitem__(self, key, value):
        v = self[key]
        v.set_value(value)
        sasoptpy.abstract.Assignment(v, value)

    def __iter__(self):
        """
        Yields an iterable list of variables inside the variable group

        Returns
        -------
        i : list
            Iterable list of Variable objects
        """
        for v in self._vardict.values():
            yield v

    def _defn(self):
        """
        Returns string to be used in OPTMODEL definition
        """
        name = self.get_name()
        s = 'var {}'.format(name)
        s += ' {'
        for i in self._keyset:
            ind_list = []
            for j in i:
                ind_list.append(
                    sasoptpy.util.package_utils._to_optmodel_quoted_string(j))
            s += '{{{}}}, '.format(','.join(ind_list))
        s = s[:-2]
        s += '} '

        # Grab features
        CONT = sasoptpy.CONT
        BIN = sasoptpy.BIN
        INT = sasoptpy.INT
        if self._type != CONT:
            if self._type == BIN:
                s += 'binary '
            if self._type == INT:
                s += 'integer '

        if sasoptpy.core.util.is_valid_lb(self._lb, self._type):
            s += '>= {} '.format(self._lb)
        if sasoptpy.core.util.is_valid_ub(self._ub, self._type):
            s += '<= {} '.format(self._ub)
        if sasoptpy.core.util.is_valid_init(self._init, self._type):
            s += 'init {} '.format(self._init)

        s = s.rstrip()
        s += ';'

        return(s)

    def _expr(self):
        return self.get_name()

    def _member_defn(self):
        dependents = []
        for v in self.get_members().values():
            dependents.extend(self.get_different_attributes(v))
        defn = sasoptpy.util.get_attribute_definitions(dependents)
        return defn

    def get_members(self):
        """
        Returns a dictionary of members
        """
        return self._vardict

    def get_shadow_members(self):
        return self._shadows

    def get_attributes(self):
        """
        Returns an ordered dictionary of main attributes

        Returns
        --------
        attributes : OrderedDict
            The dictionary consists of `init`, `lb`, and `ub` attributes

        """
        attributes = OrderedDict()
        attributes['init'] = self._init
        attributes['lb'] = self._lb
        attributes['ub'] = self._ub
        return attributes

    def get_type(self):
        """
        Returns the type of variable

        Possible values are:

        * sasoptpy.CONT
        * sasoptpy.INT
        * sasoptpy.BIN

        Examples
        --------

        >>> z = so.VariableGroup(3, name='z', vartype=so.INT)
        >>> z.get_type()
        'INT'

        """
        return self._type

    def get_different_attributes(self, var):
        var_attr = var.get_attributes()
        group_attr = self.get_attributes()

        different_attrs = []
        for key, var_value in var_attr.items():
            if var_value is not None:
                group_value = group_attr.get(key, None)

                def is_equal_to_default(v, k):
                    return v == sasoptpy.core.util.get_default_value(
                        self.get_type(), k)

                if group_value is None and is_equal_to_default(var_value, key):
                    continue

                if sasoptpy.util.is_comparable(group_value) and var_value != group_value:
                    different_attrs.append(
                        {'ref': var, 'key': key, 'value': var_value})
                elif not sasoptpy.util.is_comparable(group_value):
                    different_attrs.append(
                        {'ref': var, 'key': key, 'value': var_value})

        return different_attrs

    def sum(self, *argv):
        """
        Quick sum method for the variable groups

        Parameters
        ----------
        argv : Arguments
            List of indices for the sum

        Returns
        -------
        r : :class:`Expression`
            Expression that represents the sum of all variables in the group

        Examples
        --------

        >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
        >>> e1 = z.sum('*', '*')
        >>> print(e1)
        z[1, 'c']  +  z[1, 'a']  +  z[1, 'b']  +  z[0, 'a']  +  z[0, 'b']  +
        z[0, 'c']
        >>> e2 = z.sum('*', 'a')
        >>> print(e2)
         z[1, 'a']  +  z[0, 'a']
        >>> e3 = z.sum('*', ['a', 'b'])
        >>> print(e3)
         z[1, 'a']  +  z[0, 'b']  +  z[1, 'b']  +  z[0, 'a']

        """
        if self._abstract:
            r = Expression()
            symbolic_sum = False
            ind_set = list()
            iter_key = list()
            for i, a in enumerate(argv):
                if isinstance(a, str) and a == '*':
                    sub_list = list()
                    for j in self._keyset[i]:
                        if sasoptpy.abstract.util.is_abstract_set(j):
                            si = sasoptpy.abstract.SetIterator(j)
                            iter_key.append(si)
                            ind_set.append(si)
                            symbolic_sum = True
                        else:
                            #ind_set.append(j)
                            sub_list.append(j)
                    if sub_list:
                        ind_set.append(sub_list)
                else:
                    if hasattr(a, '__iter__'):
                        ind_set.append(a)
                    else:
                        ind_set.append([a])
            combs = product(*ind_set)
            for i in combs:
                var_key = sasoptpy.util.pack_to_tuple(i)
                r = r.add(self[var_key], 1)
            if symbolic_sum:
                #r = r.add(self[tuple(ind_set)])
                r._operator = 'sum'
                r._iterkey = iter_key
            return r
        else:
            r = Expression()
            r.set_temporary()
            feas_set = []
            for i, a in enumerate(argv):
                if a == '*':
                    feas_set.append(self._groups[i])
                elif hasattr(a, "__iter__") and not isinstance(a, str):
                    feas_set.append(a)
                else:
                    feas_set.append([a])
            combs = product(*feas_set)
            for i in combs:
                var_key = sasoptpy.util.pack_to_tuple(i)
                if var_key in self._vardict:
                    r.add(self._vardict[var_key], 1)
            r.set_permanent()
            return r

    def mult(self, vector):
        """
        Quick multiplication method for the variable groups

        Parameters
        ----------
        vector : list, dictionary, :class:`pandas.Series`,\
                 or :class:`pandas.DataFrame`
            Vector to be multiplied with the variable group

        Returns
        -------
        r : :class:`Expression`
            An expression that is the product of the variable group with the
            specified vector

        Examples
        --------

        Multiplying with a list

        >>> x = so.VariableGroup(4, vartype=so.BIN, name='x')
        >>> e1 = x.mult([1, 5, 6, 10])
        >>> print(e1)
         10.0 * x[3]  +  6.0 * x[2]  +  x[0]  +  5.0 * x[1]

        Multiplying with a dictionary

        >>> y = so.VariableGroup([0, 1], ['a', 'b'], name='y', lb=0, ub=10)
        >>> dvals = {(0, 'a'): 1, (0, 'b'): 2, (1, 'a'): -1, (1, 'b'): 5}
        >>> e2 = y.mult(dvals)
        >>> print(e2)
         2.0 * y[0, 'b']  -  y[1, 'a']  +  y[0, 'a']  +  5.0 * y[1, 'b']

        Multiplying with a pandas.Series object

        >>> u = so.VariableGroup(['a', 'b', 'c', 'd'], name='u')
        >>> ps = pd.Series([0.1, 1.5, -0.2, 0.3], index=['a', 'b', 'c', 'd'])
        >>> e3 = u.mult(ps)
        >>> print(e3)
         1.5 * u['b']  +  0.1 * u['a']  -  0.2 * u['c']  +  0.3 * u['d']

        Multiplying with a pandas.DataFrame object

        >>> data = np.random.rand(3, 3)
        >>> df = pd.DataFrame(data, columns=['a', 'b', 'c'])
        >>> print(df)
        NOTE: Initialized model model1
                  a         b         c
        0  0.966524  0.237081  0.944630
        1  0.821356  0.074753  0.345596
        2  0.065229  0.037212  0.136644
        >>> y = m.add_variables(3, ['a', 'b', 'c'], name='y')
        >>> e = y.mult(df)
        >>> print(e)
        0.9665237354418064 * y[0, 'a']  +  0.23708064143289442 * y[0, 'b']  +
        0.944629500537536 * y[0, 'c']  +  0.8213562592159828 * y[1, 'a']  +
        0.07475256894157478 * y[1, 'b']  +  0.3455957019116668 * y[1, 'c']  +
        0.06522945752546017 * y[2, 'a']  +  0.03721153533250843 * y[2, 'b']  +
        0.13664422498043194 * y[2, 'c']

        """

        r = Expression()
        if isinstance(vector, list) or isinstance(vector, np.ndarray):
            for i, key in enumerate(vector):
                var = self._vardict[i, ]
                r._linCoef[var.get_name()] = {'ref': var, 'val': vector[i]}
        elif isinstance(vector, pd.Series):
            for key in vector.index:
                k = sasoptpy.util.pack_to_tuple(key)
                var = self._vardict[k]
                r._linCoef[var.get_name()] = {'ref': var, 'val': vector[key]}
        elif isinstance(vector, pd.DataFrame):
            vectorflat = sasoptpy.util.flatten_frame(vector)
            for key in vectorflat.index:
                k = sasoptpy.util.pack_to_tuple(key)
                var = self._vardict[k]
                r._linCoef[var.get_name()] = {'ref': var, 'val': vectorflat[key]}
        else:
            for i, key in enumerate(vector):
                if isinstance(key, tuple):
                    k = key
                else:
                    k = (key,)
                var = self._vardict[k]
                try:
                    r._linCoef[var.get_name()] = {'ref': var, 'val': vector[i]}
                except KeyError:
                    r._linCoef[var.get_name()] = {'ref': var, 'val': vector[key]}

        return r

    def set_init(self, init):
        """
        Specifies or updates the initial values

        Parameters
        ----------
        init : float, list, dict, :class:`pandas.Series`
            Initial value of the variables

        Examples
        --------

        >>> m = so.Model(name='m')
        >>> y = m.add_variables(3, name='y')
        >>> print(y._defn())
        var y {{0,1,2}};
        >>> y.set_init(5)
        >>> print(y._defn())
        var y {{0,1,2}} init 5;

        """
        self._init = init
        for v in self._vardict:
            inval = sasoptpy.util.extract_list_value(v, init)
            self._vardict[v].set_init(inval)
        for v in self._shadows:
            self._shadows[v].set_init(init)

    def set_bounds(self, lb=None, ub=None, members=True):
        """
        Specifies or updates bounds for the variable group

        Parameters
        ----------
        lb : float, :class:`pandas.Series`, optional
            Lower bound
        ub : float, :class:`pandas.Series`, optional
            Upper bound

        Examples
        --------

        >>> z = so.VariableGroup(2, ['a', 'b', 'c'], name='z', lb=0, ub=10)
        >>> print(repr(z[0, 'a']))
        sasoptpy.Variable(name='z_0_a', lb=0, ub=10, vartype='CONT')
        >>> z.set_bounds(lb=3, ub=5)
        >>> print(repr(z[0, 'a']))
        sasoptpy.Variable(name='z_0_a', lb=3, ub=5, vartype='CONT')

        >>> u = so.VariableGroup(['a', 'b', 'c', 'd'], name='u')
        >>> lb_vals = pd.Series([1, 4, 0, -1], index=['a', 'b', 'c', 'd'])
        >>> u.set_bounds(lb=lb_vals)
        >>> print(repr(u['b']))
        sasoptpy.Variable(name='u_b', lb=4, ub=inf, vartype='CONT')

        """

        if lb is not None:
            self._lb = sasoptpy.core.util.get_group_bound(lb)
        if ub is not None:
            self._ub = sasoptpy.core.util.get_group_bound(ub)

        if members:
            for v in self._vardict:
                varlb = sasoptpy.util.extract_list_value(v, lb)
                if lb is not None:
                    self[v].set_bounds(lb=varlb)
                varub = sasoptpy.util.extract_list_value(v, ub)
                if ub is not None:
                    self[v].set_bounds(ub=varub)

    def set_member_value(self, key, value):
        pass

    def get_member_by_name(self, name):
        keys = sasoptpy.abstract.util.get_key_from_name(name)
        return self[keys]

    def __str__(self):
        """
        Generates a representation string
        """
        s = 'Variable Group ({}) [\n'.format(self.get_name())
        for k in self._vardict:
            v = self._vardict[k]
            s += '  [{}: {}]\n'.format(sasoptpy.util.get_first_member(k), v)
        s += ']'
        return s

    def __repr__(self):
        """
        Returns a string representation of the object.
        """
        s = 'sasoptpy.VariableGroup('
        keylen = max(map(len, self._vardict))
        for i in range(keylen):
            ls = []
            for k in self._vardict:
                if k[i] not in ls:
                    ls.append(k[i])
            s += '{}, '.format(ls)
        s += 'name=\'{}\')'.format(self.get_name())
        return s
