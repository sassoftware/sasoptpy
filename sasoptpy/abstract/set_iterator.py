import sasoptpy


class SetIterator(sasoptpy.Expression):
    """
    Creates an iterator object for a given Set

    Parameters
    ----------
    initset : Set
        Set to be iterated on
    conditions : list, optional
        List of conditions on the iterator
    datatype : string, optional
        Type of the iterator
    group : dict, optional
        Dictionary representing the order of iterator inside multi-index sets
    multi_index : boolean, optional
        Switch for representing multi-index iterators

    Notes
    -----

    - SetIterator objects are automatically created when looping over a
      :class:`Set`.
    - This class is mainly intended for internal use.
    - The ``group`` parameter consists of following keys

      - **order** : int
        Order of the parameter inside the group
      - **outof** : int
        Total number of indices inside the group
      - **id** : int
        ID number assigned to group by Python

    """

    def __init__(self, initset, name=None, conditions=None, datatype='num',
                 group={'order': 1, 'outof': 1, 'id': 0}, multi_index=False
                 ):
        # TODO use self._name = initset._colname
        if name is None:
            name = sasoptpy.util.get_next_name()
        super().__init__(name=name)
        self._linCoef[self._name] = {'ref': self,
                                     'val': 1.0}
        self._set = initset
        self._type = sasoptpy.util.pack_to_list(datatype)
        self._children = []
        if len(self._type) > 1 or multi_index:
            for i, ty in enumerate(self._type):
                sc = SetIterator(
                    self, conditions=None, datatype=ty,
                    group={'order': i, 'outof': len(self._type),
                           'id': id(self)}, multi_index=False)
                self._children.append(sc)
        self._order = group['order']
        self._outof = group['outof']
        self._group = group['id']
        self._multi = multi_index
        self._conditions = conditions if conditions else []

    def set_name(self, name):
        self._name = name

    def __hash__(self):
        return hash('{}'.format(id(self)))

    def __add_condition(self, operation, key):
        c = {'type': operation, 'key': key}
        self._conditions.append(c)

    def __contains__(self, key):
        self.__add_condition('IN', key)
        return True

    def __eq__(self, key):
        self.__add_condition('=', key)  # or 'EQ'
        return True

    def __le__(self, key):
        self.__add_condition('<=', key)  # or 'LE'
        return True

    def __lt__(self, key):
        self.__add_condition('<', key)
        return True

    def __ge__(self, key):
        self.__add_condition('>=', key)  # or 'GE'
        return True

    def __gt__(self, key):
        self.__add_condition('>', key)
        return True

    def __ne__(self, key):
        self.__add_condition('NE', key)  # or 'NE'
        return True

    def __and__(self, key):
        self.__add_condition('AND', key)

    def __or__(self, key):
        self.__add_condition('OR', key)

    def _defn(self, cond=0):
        if self._multi:
            comb = '<' + ', '.join(str(i) for i in self._children) + '>'
            s = '{} in {}'.format(comb, sasoptpy.to_expression(self._set))
        else:
            s = '{} in {}'.format(self._name, sasoptpy.to_expression(self._set))
        if cond and len(self._conditions) > 0:
            s += ':'
            s += self._to_conditions()
        return(s)

    def _to_conditions(self):
        s = ''
        conds = []
        if len(self._conditions) > 0:
            for i in self._conditions:
                c_cond = '{} {} '.format(self._name, i['type'])
                if type(i['key']) == str:
                    c_cond += '\'{}\''.format(i['key'])
                else:
                    c_cond += '{}'.format(i['key'])
                conds.append(c_cond)

            s = ' and '.join(conds)
        else:
            s = ''
        return s

    def _get_for_expr(self):
        if self._multi:
            return 'for ({}) in {}'.format(self._expr(), self._set._name)
        else:
            return 'for {} in {}'.format(self._expr(), self._set._name)

    def _expr(self):
        if self._multi:
            return ', '.join(str(i) for i in self._children)
        return str(self)

    def __str__(self):
        if self._multi:
            print('WARNING: str is called for a multi-index set iterator.')
        return self._name

    def __repr__(self):
        s = 'sasoptpy.abstract.SetIterator(name={}, initset={}, conditions=['.\
            format(self._name, self._set._name)
        for i in self._conditions:
            s += '{{\'type\': \'{}\', \'key\': \'{}\'}}, '.format(
                i['type'], i['key'])
        s += "], datatype={}, group={{'order': {}, 'outof': {}, 'id': {}}}, multi_index={})".format(
            self._type, self._order, self._outof, self._group, self._multi)
        return(s)