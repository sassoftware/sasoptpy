import sasoptpy
from sasoptpy.libs import pd
from abc import ABC, abstractmethod
from collections import OrderedDict


class Group(ABC):

    def __init__(self, name):
        self._name = name
        self._groups = OrderedDict()

    def get_name(self):
        return self._name

    def _register_keys(self, keys):
        for j, k in enumerate(keys):
            try:
                self._groups[j].append(k)
            except KeyError:
                self._groups[j] = [k]

    def filter_unique_keys(self):
        for i in self._groups:
            self._groups[i] = list(OrderedDict.fromkeys(self._groups[i]))

    def get_group_types(self):
        group_types = []
        for i in self._groups.values():
            if any([sasoptpy.abstract.is_key_abstract(j) for j in i]):
                group_types.append(sasoptpy.ABSTRACT)
            else:
                group_types.append(sasoptpy.CONCRETE)
        return group_types

    @abstractmethod
    def get_members(self):
        """
        Each Group object should provide a way to access its members as an
        OrderedDict
        """
